"""SimulatorAgent — LangGraph-powered client simulator.

Generates client responses based on psychotype, dialogue stage,
and optional RAG context. Maintains per-session state for DDA
(Dynamic Difficulty Adjustment) and Anti-Gaming.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.entities import DifficultyLevel, Psychotype, Scenario, Session
from core.exceptions import BusinessRuleViolationError

if TYPE_CHECKING:
    from uuid import UUID

if TYPE_CHECKING:
    from infrastructure.qdrant.rag_service import RAGService

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_STAGE_TURN_GREETING = 1
_STAGE_TURN_NEED_ID = 3
_STAGE_TURN_OBJECTION = 6
_STAGE_TURN_CLOSING = 7
_DDA_STREAK_THRESHOLD = 2
_ANTI_GAMING_MIN_REPETITIONS = 3
_ANTI_GAMING_TRIGGER_COUNT = 2
_MAX_OPERATOR_TURNS = 10

# ── Stage names ────────────────────────────────────────────────────────

STAGE_GREETING = "greeting"
STAGE_NEED_ID = "need_identification"
STAGE_OBJECTION = "objection_handling"
STAGE_CLOSING = "closing"
STAGE_END = "end"

# ── Template responses per psychotype ──────────────────────────────────

_GREETINGS: dict[Psychotype, list[str]] = {
    Psychotype.AGGRESSIVE: [
        "Hello? I've been waiting forever! Are you going to help me or not?",
        "Finally! I need to speak with someone competent right now!",
        "Look, I've called three times already. Fix my problem NOW!",
    ],
    Psychotype.CONFUSED: [
        "Um, hello? I hope I'm calling the right department...",
        "Hi there. I'm a bit lost, I got this letter and I don't understand it.",
        "Hello? I'm not sure if you can help me, but I'll try to explain...",
    ],
    Psychotype.TECHNICALLY_INEPT: [
        "Hello? My computer is doing something weird again!",
        "Hi, I can't log in! It says something about a password but I never changed it!",
        "Hello? I got an email but I clicked on it and now everything looks different!",
    ],
    Psychotype.FRAUDSTER: [
        "Good day. I'm calling on behalf of Mr. Petrov regarding his account.",
        "Hello, I need to verify some account details for a family member.",
        "Hi, I'm helping my elderly neighbour with his banking. Can you assist?",
    ],
    Psychotype.NEUTRAL: [
        "Hello, I'd like some help with your service please.",
        "Hi there, I have a question about my account if you have a moment.",
        "Hello, can you help me with an issue I'm having?",
    ],
}

_NEED_ID_RESPONSES: dict[Psychotype, list[str]] = {
    Psychotype.AGGRESSIVE: [
        "The problem is obvious! You people charged me twice! Fix it!",
        "I shouldn't have to explain this. It's YOUR mistake!",
        "Are you stupid or what? I just said, I got overcharged!",
    ],
    Psychotype.CONFUSED: [
        "Well, I got a letter saying I owe money but I don't understand why...",
        "I think there's a mistake somewhere, but I'm not sure where.",
        "Hmm, let me check my papers... I'm not very good with these things.",
    ],
    Psychotype.TECHNICALLY_INEPT: [
        "Every time I try to pay, it says 'error' and I don't know what to do!",
        "The website asked me to verify something but I don't remember my details.",
        "I think I clicked something I shouldn't have. Now everything is messed up!",
    ],
    Psychotype.FRAUDSTER: [
        "We just need a small change to the contact details. Very simple.",
        "I need to check the transaction history for the last few months.",
        "My associate needs access to the account. Can you add him as a manager?",
    ],
    Psychotype.NEUTRAL: [
        "I noticed a charge on my bill that I don't recognise.",
        "I'd like to update my contact information if possible.",
        "I have a question about the terms of my agreement.",
    ],
}

_OBJECTION_RESPONSES: dict[Psychotype, list[str]] = {
    Psychotype.AGGRESSIVE: [
        "That's not good enough! I want a manager right now!",
        "You're not listening! I already told you I tried that!",
        "This is ridiculous! You have no idea what you're doing!",
        "I demand to speak to someone who actually knows the rules!",
    ],
    Psychotype.CONFUSED: [
        "But I don't understand... the letter says something different.",
        "Are you sure? I'm afraid of making things worse by doing that.",
        "I don't know... that sounds complicated. Can you just fix it for me?",
    ],
    Psychotype.TECHNICALLY_INEPT: [
        "I can't do that! I don't even know where that button is!",
        "That's not what I asked. I just want things to work like before!",
        "I tried that! Nothing happened! Wait, what button did you say?",
    ],
    Psychotype.FRAUDSTER: [
        "That's not convenient. Can't you just bypass that step?",
        "I don't have that information with me. Can't you just use what's on file?",
        "Surely for a long-standing customer you can make an exception?",
    ],
    Psychotype.NEUTRAL: [
        "I see, but that doesn't quite solve my problem. What else can you suggest?",
        "I understand what you're saying, but I was hoping for a different solution.",
        "Is that really the only option available?",
    ],
}

_CLOSING_RESPONSES: dict[Psychotype, list[str]] = {
    Psychotype.AGGRESSIVE: [
        "About time! Just make sure it doesn't happen again.",
        "Fine. But I'll be checking my account, and if there's another mistake...",
        "Finally, someone who can actually solve problems. Send me the confirmation.",
    ],
    Psychotype.CONFUSED: [
        "OK, thank you. I hope I did everything right. Please send me an email confirmation.",
        "Thanks for your help. I'll try what you suggested. Sorry for taking so much time.",
        "Alright, I think I understand now. Can you repeat the steps one more time?",
    ],
    Psychotype.TECHNICALLY_INEPT: [
        "OK, I'll try that. But if something goes wrong, I'm calling back!",
        "Thanks. Can you send me step-by-step instructions? I'll forget otherwise.",
        "Alright, I think I can manage that. Maybe. Thanks I guess.",
    ],
    Psychotype.FRAUDSTER: [
        "Very well. I'll expect the confirmation shortly. Good day.",
        "Thank you for your assistance. My associate will be in touch.",
        "Perfect. I'll let my colleague know the changes have been made.",
    ],
    Psychotype.NEUTRAL: [
        "Thank you for your help. I'll follow your suggestions.",
        "Great, thanks for resolving this. Have a good day.",
        "Appreciate your assistance. I'll wait for the confirmation email.",
    ],
}

# ── Per-session state ──────────────────────────────────────────────────


@dataclass
class SimulatorSessionState:
    """Internal state for a single simulation session."""

    session_id: UUID
    scenario_id: UUID
    psychotype: Psychotype
    difficulty: DifficultyLevel
    stage: str = STAGE_GREETING
    dda_level: int = 0
    operator_success_streak: int = 0
    last_operator_messages: list[str] = field(default_factory=list)
    repetition_count: int = 0
    used_greeting: str = ""
    has_responded: bool = False


# ── SimulatorAgent ─────────────────────────────────────────────────────


class SimulatorAgent:
    """Rule-based client simulator with DDA and Anti-Gaming.

    Wraps template responses per psychotype/dialogue-stage and
    tracks per-session internal state. RAG integration optional.
    """

    def __init__(self, rag_service: RAGService | None = None) -> None:
        self._rag = rag_service
        self._sessions: dict[UUID, SimulatorSessionState] = {}

    # ── Protocol methods ───────────────────────────────────────────────

    async def start_dialogue(
        self, scenario: Scenario
    ) -> tuple[str, Psychotype]:
        """Start a dialogue: return greeting and selected psychotype.

        Internal state is created lazily on the first generate_response call
        so the caller can use the session id as the lookup key.
        """
        psychotype = scenario.psychotype
        greeting = random.choice(_GREETINGS[psychotype])  # noqa: S311

        logger.info(
            "Simulator started dialogue psychotype=%s greeting=%r",
            psychotype.value,
            greeting[:50],
        )
        return greeting, psychotype

    async def generate_response(self, session: Session) -> str:
        """Generate the client's next response based on transcript.

        Determines the current stage, applies DDA and Anti-Gaming,
        and returns an appropriate template response.
        """
        state = self._get_or_create_state(session)

        _validate_turn_order(session)
        last_op_msg = session.transcript[-1].text if session.transcript else ""
        state.last_operator_messages.append(last_op_msg)

        # Update stage based on turn count and transcript
        self._update_stage(state, session)

        # Generate response for current stage
        response = self._generate_stage_response(state)

        # Apply DDA (add extra intensity for successful operators)
        response = self._apply_dda(state, response)

        # Apply Anti-Gaming (detect and counter repetition)
        response = self._apply_anti_gaming(state, response)

        state.has_responded = True
        logger.debug(
            "Simulator response stage=%s response=%r",
            state.stage,
            response[:60],
        )
        return response

    async def should_end(self, session: Session) -> bool:
        """Check if the dialogue should end."""
        state = self._get_or_create_state(session)
        return self._check_end_condition(state, session)

    # ── Public helpers ─────────────────────────────────────────────────

    def get_state(
        self, session_id: UUID
    ) -> SimulatorSessionState | None:
        """Return internal simulator state for a session."""
        return self._sessions.get(session_id)

    def reset_session(self, session_id: UUID) -> None:
        """Clear internal state for a session."""
        self._sessions.pop(session_id, None)

    # ── Internal helpers ───────────────────────────────────────────────

    def _get_or_create_state(
        self, session: Session
    ) -> SimulatorSessionState:
        """Get existing state or create a best-effort one from session."""
        sid = session.id
        if sid in self._sessions:
            return self._sessions[sid]

        # Fallback: create state from session data
        psychotype = (
            session.psychotype_at_start or Psychotype.NEUTRAL
        )
        difficulty = (
            session.difficulty_at_start or DifficultyLevel.BEGINNER
        )
        state = SimulatorSessionState(
            session_id=sid,
            scenario_id=session.scenario_id,
            psychotype=psychotype,
            difficulty=difficulty,
        )
        self._sessions[sid] = state
        return state

    def _update_stage(
        self, state: SimulatorSessionState, session: Session
    ) -> None:
        """Determine current stage from transcript length and content."""
        operator_turns = sum(
            1 for t in session.transcript if t.speaker == "operator"
        )

        if operator_turns <= _STAGE_TURN_GREETING:
            state.stage = STAGE_GREETING
        elif operator_turns <= _STAGE_TURN_NEED_ID:
            state.stage = STAGE_NEED_ID
        elif operator_turns <= _STAGE_TURN_OBJECTION:
            state.stage = STAGE_OBJECTION
        elif operator_turns >= _STAGE_TURN_CLOSING:
            state.stage = STAGE_CLOSING

    def _generate_stage_response(self, state: SimulatorSessionState) -> str:
        """Pick a response for the current stage based on psychotype."""
        responses_by_stage = {
            STAGE_GREETING: _GREETINGS,
            STAGE_NEED_ID: _NEED_ID_RESPONSES,
            STAGE_OBJECTION: _OBJECTION_RESPONSES,
            STAGE_CLOSING: _CLOSING_RESPONSES,
        }

        pool = responses_by_stage.get(state.stage, _NEED_ID_RESPONSES)
        psych_pool = pool.get(state.psychotype, pool[Psychotype.NEUTRAL])

        # Avoid repeating the exact last response
        if (
            state.last_operator_messages
            and len(psych_pool) > 1
        ):
            last = state.last_operator_messages[-1]
            candidates = [r for r in psych_pool if r != last]
            if candidates:
                return random.choice(candidates)  # noqa: S311

        return random.choice(psych_pool)  # noqa: S311

    def _apply_dda(
        self, state: SimulatorSessionState, response: str
    ) -> str:
        """Apply Dynamic Difficulty Adjustment.

        Incrementally increases response intensity when operator
        demonstrates consistent success.
        """
        if state.operator_success_streak >= _DDA_STREAK_THRESHOLD:
            # Intensify by adding aggressive prefix
            intensifiers = [
                "",
                " Look, I've been patient but ",
                " I'm losing my patience here! ",
                " THIS IS UNACCEPTABLE! ",
            ]
            idx = min(state.dda_level, len(intensifiers) - 1)
            if idx > 0 and not response.startswith(intensifiers[idx].strip()):
                response = intensifiers[idx] + response.lower()

        return response

    def _apply_anti_gaming(
        self, state: SimulatorSessionState, response: str
    ) -> str:
        """Apply Anti-Gaming countermeasures.

        Detects repetitive operator patterns and varies response
        unpredictably.
        """
        msgs = state.last_operator_messages

        # Check for repetitive patterns (3+ near-identical messages)
        if len(msgs) >= _ANTI_GAMING_MIN_REPETITIONS:
            unique = len({
                m.strip().lower()[:_ANTI_GAMING_MIN_REPETITIONS * 10]
                for m in msgs[-_ANTI_GAMING_MIN_REPETITIONS:]
            })
            if unique <= 1:
                state.repetition_count += 1
                # Counter: change stage unpredictably
                response = (
                    "That's what you said before! Stop repeating yourself "
                    "and give me a proper answer!"
                )

        # If repetitive pattern detected, sprinkle extra objections
        if state.repetition_count >= _ANTI_GAMING_TRIGGER_COUNT:
            extra_objections = [
                "You're clearly not listening! I want a different agent!",
                "This is going nowhere. Escalate this right now!",
            ]
            response = random.choice(extra_objections)  # noqa: S311

        return response

    def _check_end_condition(
        self, state: SimulatorSessionState, session: Session
    ) -> bool:
        """Check termination conditions."""
        operator_turns = sum(
            1 for t in session.transcript if t.speaker == "operator"
        )

        if operator_turns >= _MAX_OPERATOR_TURNS:
            return True

        return state.stage == STAGE_CLOSING and state.has_responded


_ERR_NO_OPERATOR_TURN = "Cannot generate response: no operator turn in transcript"
_ERR_LAST_NOT_OPERATOR = (
    "Cannot generate response: last turn is not from operator"
)


def _validate_turn_order(session: Session) -> None:
    """Validate that the last turn is from the operator.

    Allow a single client greeting (post-creation) so standalone
    simulator endpoints can generate the first client response.
    """
    if not session.transcript:
        raise BusinessRuleViolationError(_ERR_NO_OPERATOR_TURN)
    last = session.transcript[-1]
    if last.speaker != "operator":
        if len(session.transcript) == 1 and last.speaker == "client":
            return
        raise BusinessRuleViolationError(_ERR_LAST_NOT_OPERATOR)
