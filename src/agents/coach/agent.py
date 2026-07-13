"""CoachAgent — rule-based dialogue analysis and feedback generator.

Analyses a completed Session against the Scenario's script_text,
scores across six dimensions, and produces sandwich-format feedback
with optional script citations (RAG placeholder).
"""

from __future__ import annotations

import logging
import re
from typing import ClassVar

from core.entities import Evaluation, Scenario, Session
from core.exceptions import CoachError

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_SCORE_MAX = 100.0
_SCORE_MIN = 0.0

# Thresholds for scoring tiers
_THRESHOLD_HIGH = 0.7
_THRESHOLD_MEDIUM = 0.4
_THRESHOLD_LOW = 0.2

# Minimum transcript entries for meaningful analysis
_MIN_TRANSCRIPT_LENGTH = 2

# Gaming detection thresholds
_GAMING_MIN_MESSAGES = 3
_GAMING_MAX_SHORT_LEN = 15

# Feedback thresholds
_FB_LOW = 30
_FB_MEDIUM = 50
_FB_HIGH = 70
_FB_TOP = 80

# ── Linguistic markers ─────────────────────────────────────────────────

_POSITIVE_TONE_MARKERS: set[str] = {
    "thank you", "thanks", "please", "appreciate", "welcome",
    "pleasure", "happy", "glad", "great", "excellent", "wonderful",
    "absolutely", "certainly", "of course", "my pleasure",
    "you're welcome", "happy to help", "lovely", "fantastic",
    "marvellous", "splendid", "perfect",
}

_NEGATIVE_TONE_MARKERS: set[str] = {
    "whatever", "not my problem", "can't you", "don't care",
    "what do you want", "just", "fine", "whatever you say",
    "calm down", "relax", "you people", "you always",
}

_EMPATHY_MARKERS: set[str] = {
    "understand", "sorry", "apologise", "apologize",
    "appreciate", "hear you", "frustrat", "upset",
    "concern", "patience", "understand how you feel",
    "i can imagine", "that must be", "i hear you",
    "i see why", "valid point", "i appreciate",
}

_OBJECTION_ADDRESS_MARKERS: set[str] = {
    "understand", "sorry", "apologise", "apologize",
    "solution", "offer", "help", "fix", "resolve",
    "alternative", "option", "suggest", "recommend",
    "explain", "clarify", "let me", "i can",
    "what i can do", "here's what", "how about",
}

_STOP_WORDS: set[str] = {
    "a", "an", "the", "is", "it", "at", "on", "in", "of", "to",
    "for", "and", "or", "but", "so", "if", "be", "are", "was",
    "were", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "not", "no", "this", "that", "these", "those",
    "i", "me", "my", "we", "our", "you", "your", "he", "she",
    "they", "them", "their",
}


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from script text."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def _count_markers(text: str, markers: set[str]) -> int:
    """Count occurrences of any marker phrase in text."""
    lower = text.lower()
    return sum(1 for m in markers if m in lower)


def _get_operator_turns(session: Session) -> list[str]:
    """Extract operator speech turns from transcript."""
    return [
        t.text for t in session.transcript
        if t.speaker == "operator"
    ]


def _get_client_turns(session: Session) -> list[str]:
    """Extract client speech turns from transcript."""
    return [
        t.text for t in session.transcript
        if t.speaker == "client"
    ]


def _clamp(value: float, minimum: float = _SCORE_MIN,
           maximum: float = _SCORE_MAX) -> float:
    """Clamp a value to [minimum, maximum]."""
    return max(minimum, min(maximum, value))


# ── CoachAgent ─────────────────────────────────────────────────────────


class CoachAgent:
    """Rule-based dialogue evaluator with sandwich feedback generation.

    Analyses operator performance against script criteria across six
    scoring dimensions. RAG integration is available as a future
    enhancement for citation-backed validation.
    """

    _script_keywords: ClassVar[set[str] | None] = None

    # ── Protocol method ─────────────────────────────────────────────────

    async def evaluate_session(
        self, session: Session, scenario: Scenario
    ) -> Evaluation:
        """Analyse a completed session and produce an evaluation.

        Steps:
          1. Compute sub-scores for each dimension.
          2. Generate sandwich-format feedback text.
          3. Return a populated Evaluation entity.
        """
        self._validate(session, scenario)

        operator_msgs = _get_operator_turns(session)
        client_msgs = _get_client_turns(session)
        all_text = " ".join(operator_msgs)

        # Early exit for empty transcript
        if not operator_msgs:
            praise = (
                "The session was completed but no operator speech was recorded."
            )
            growth = (
                "The session transcript appears to be empty. "
                "A meaningful conversation is essential for evaluation. "
                "Please complete a full simulation with multiple exchanges "
                "to receive detailed feedback."
            )
            closing = (
                "Start a new session and practise walking through the "
                "script step by step."
            )
            return Evaluation(
                session_id=session.id,
                user_id=session.user_id,
                overall_score=0.0,
                script_adherence=0.0,
                tone_score=0.0,
                empathy_score=0.0,
                objection_handling=0.0,
                completeness_score=0.0,
                praise_text=praise,
                growth_text=growth,
                closing_text=closing,
            )

        script_adherence = self._score_script_adherence(
            operator_msgs, scenario
        )
        tone_score = self._score_tone(all_text)
        empathy_score = self._score_empathy(all_text)
        objection_handling = self._score_objection_handling(
            operator_msgs, client_msgs
        )
        completeness_score = self._score_completeness(
            operator_msgs, scenario
        )
        overall_score = self._compute_overall([
            script_adherence,
            tone_score,
            empathy_score,
            objection_handling,
            completeness_score,
        ])

        gaming_detected = self._detect_gaming(operator_msgs)

        praise, growth, closing = self._generate_feedback(
            scenario=scenario,
            script_adherence=script_adherence,
            tone_score=tone_score,
            empathy_score=empathy_score,
            objection_handling=objection_handling,
            completeness_score=completeness_score,
            overall_score=overall_score,
            gaming_detected=gaming_detected,
        )

        evaluation = Evaluation(
            session_id=session.id,
            user_id=session.user_id,
            overall_score=overall_score,
            script_adherence=script_adherence,
            tone_score=tone_score,
            empathy_score=empathy_score,
            objection_handling=objection_handling,
            completeness_score=completeness_score,
            praise_text=praise,
            growth_text=growth,
            closing_text=closing,
            gaming_detected=gaming_detected,
        )

        logger.info(
            "Coach evaluated session %s overall=%.1f",
            session.id, overall_score,
        )
        return evaluation

    # ── Validation ──────────────────────────────────────────────────────

    def _validate(
        self, session: Session, scenario: Scenario
    ) -> None:
        """Validate inputs before evaluation."""
        if session.user_id is None:
            msg = "Session missing user_id"
            raise CoachError(msg)
        if not scenario.script_text:
            msg = "Scenario missing script_text"
            raise CoachError(msg)

    # ── Scoring helpers ─────────────────────────────────────────────────

    def _score_script_adherence(
        self, operator_msgs: list[str], scenario: Scenario,
    ) -> float:
        """Score how well the operator followed the script.

        Extracts keywords from the scenario's script_text and checks
        how many appear in operator messages.
        """
        keywords = _extract_keywords(scenario.script_text)
        if not keywords:
            return 50.0  # neutral fallback

        all_operator_text = " ".join(operator_msgs).lower()
        found = sum(1 for kw in keywords if kw in all_operator_text)
        ratio = found / len(keywords)
        return _clamp(ratio * _SCORE_MAX)

    def _score_tone(self, text: str) -> float:
        """Score operator's tone based on positive vs negative markers."""
        if not text.strip():
            return 0.0

        positive = _count_markers(text, _POSITIVE_TONE_MARKERS)
        negative = _count_markers(text, _NEGATIVE_TONE_MARKERS)

        total = positive + negative
        if total == 0:
            return 50.0  # neutral — no clear tone markers

        ratio = positive / total
        return _clamp(ratio * _SCORE_MAX)

    def _score_empathy(self, text: str) -> float:
        """Score empathy based on empathy marker frequency."""
        if not text.strip():
            return 0.0

        empathy_count = _count_markers(text, _EMPATHY_MARKERS)
        word_count = len(text.split())

        if word_count == 0:
            return 0.0

        # Scale: 1 empathy marker per ~15 words → high score
        density = empathy_count / (word_count / 15.0)
        return _clamp(density * _SCORE_MAX * 0.8)

    def _score_objection_handling(
        self, operator_msgs: list[str], client_msgs: list[str],
    ) -> float:
        """Score how well the operator handled client objections.

        Looks for client turns expressing negative sentiment, then
        checks if the following operator turn addresses it.
        """
        if not client_msgs:
            return _SCORE_MAX  # no objections to handle

        addressed = 0
        total_objections = 0

        # Pair client turns with subsequent operator turns
        for i, client_msg in enumerate(client_msgs):
            if _count_markers(client_msg, _EMPATHY_MARKERS) > 0:
                continue  # not an objection

            # Check if this client turn is the last one
            obj_keywords = {"no", "not", "but", "won't", "can't",
                            "doesn't", "don't", "wrong", "bad",
                            "terrible", "hate", "problem", "issue"}
            if not any(kw in client_msg.lower() for kw in obj_keywords):
                continue

            total_objections += 1

            # Find the next operator turn for this client message
            op_msg = operator_msgs[i] if i < len(operator_msgs) else ""

            if op_msg and _count_markers(op_msg, _OBJECTION_ADDRESS_MARKERS) > 0:
                addressed += 1

        if total_objections == 0:
            return _SCORE_MAX  # no objections — perfect

        ratio = addressed / total_objections
        return _clamp(ratio * _SCORE_MAX)

    def _score_completeness(
        self, operator_msgs: list[str], scenario: Scenario,
    ) -> float:
        """Score call completeness based on transcript length and coverage.

        Checks:
          - Minimum viable operator turns (4+)
          - Stage coverage derived from keyword presence
        """
        if not operator_msgs:
            return 0.0

        turn_count = len(operator_msgs)
        max_turns_points = min(turn_count / 8.0, 1.0) * 50.0

        # Stage coverage via script keyword presence
        keywords = _extract_keywords(scenario.script_text)
        if keywords:
            all_text = " ".join(operator_msgs).lower()
            # Split keywords into thirds: greeting, middle, closing
            third = max(len(keywords) // 3, 1)
            greeting_kw = set(keywords[:third])
            middle_kw = set(keywords[third:2 * third])
            closing_kw = set(keywords[2 * third:])

            stages_covered = 0
            if any(kw in all_text for kw in greeting_kw):
                stages_covered += 1
            if any(kw in all_text for kw in middle_kw):
                stages_covered += 1
            if any(kw in all_text for kw in closing_kw):
                stages_covered += 1

            stage_points = (stages_covered / 3.0) * 50.0
        else:
            stage_points = 25.0

        return _clamp(max_turns_points + stage_points)

    def _compute_overall(self, scores: list[float]) -> float:
        """Weighted average of sub-scores."""
        if not scores:
            return 0.0
        return _clamp(sum(scores) / len(scores))

    def _detect_gaming(self, operator_msgs: list[str]) -> bool:
        """Detect potential gaming behaviour.

        Checks for:
          - All messages extremely short (< 10 chars)
          - Near-identical repetition
        """
        if len(operator_msgs) < _GAMING_MIN_MESSAGES:
            return False

        # Check for uniformly short messages
        short_count = sum(
            1 for m in operator_msgs if len(m.strip()) < _GAMING_MAX_SHORT_LEN
        )
        if short_count == len(operator_msgs):
            return True

        # Check for repetition
        unique = len({
            m.strip().lower()[:_GAMING_MAX_SHORT_LEN]
            for m in operator_msgs[-_GAMING_MIN_MESSAGES:]
        })
        return unique <= 1

    # ── Feedback generation ─────────────────────────────────────────────

    def _generate_feedback(  # noqa: PLR0913
        self,
        scenario: Scenario,
        script_adherence: float,
        tone_score: float,
        empathy_score: float,
        objection_handling: float,
        completeness_score: float,
        overall_score: float,
        gaming_detected: bool,  # noqa: FBT001
    ) -> tuple[str, str, str]:
        """Generate sandwich-format feedback: praise → growth → closing."""
        scores = {
            "script adherence": script_adherence,
            "tone": tone_score,
            "empathy": empathy_score,
            "objection handling": objection_handling,
            "completeness": completeness_score,
        }

        sorted_dims = sorted(scores.items(), key=lambda x: -x[1])
        best_dim, best_score = sorted_dims[0]
        worst_dim, worst_score = sorted_dims[-1]

        # ── Praise ──────────────────────────────────────────────────
        if overall_score >= _FB_TOP:
            praise = (
                f"Excellent work on this {scenario.name} scenario! "
                f"Your strongest area was **{best_dim}** "
                f"(score: {best_score:.0f}/100). "
                "You demonstrated good control of the conversation."
            )
        elif overall_score >= _FB_MEDIUM:
            praise = (
                f"Good effort on the {scenario.name} scenario. "
                f"Your best area was **{best_dim}** "
                f"(score: {best_score:.0f}/100). "
                "Keep building on this strength."
            )
        else:
            praise = (
                f"You completed the {scenario.name} scenario. "
                f"Your strongest area was **{best_dim}** "
                f"(score: {best_score:.0f}/100). "
                "There is room for improvement across all dimensions."
            )

        # ── Growth (empty transcript special case) ──────────────────
        completeness_score_actual = scores.get("completeness", 0)
        if completeness_score_actual == 0 and overall_score < _FB_LOW:
            growth = (
                "The session transcript appears to be empty. "
                "A meaningful conversation is essential for evaluation. "
                "Please complete a full simulation with multiple exchanges "
                "to receive detailed feedback."
            )
        elif gaming_detected:
            growth = (
                "⚠️ **Gaming detected**: Your responses appear repetitive "
                "or too short. Focus on providing meaningful, varied "
                "responses that address the customer's needs."
            )
        elif worst_score >= _FB_HIGH:
            growth = (
                f"Good overall performance! To take it further, "
                f"focus on **{worst_dim}** (score: {worst_score:.0f}/100) — "
                "there's still room to polish this area. "
                f"Tip: Review the script for '{scenario.script_ref}' "
                "and practise the steps you found challenging."
            )
        else:
            growth = (
                f"Area for improvement: **{worst_dim}** "
                f"(score: {worst_score:.0f}/100). "
                f"According to the script '{scenario.script_ref}', "
                "focus on addressing each customer concern thoroughly. "
                "Try using empathetic language and offering clear solutions."
            )

        # ── Closing ──────────────────────────────────────────────────
        if overall_score >= _FB_TOP:
            closing = (
                "Keep up the great work! You're on track to master "
                "this scenario. Practice with different psychotypes "
                "to build confidence across all customer types."
            )
        elif overall_score >= _FB_MEDIUM:
            closing = (
                "You're making solid progress. Continue practising, "
                "especially on the areas highlighted above. "
                "Every session builds your skills!"
            )
        else:
            closing = (
                "Don't be discouraged — this is a learning process. "
                "Review the script carefully and try again. "
                "With practice, you'll see steady improvement!"
            )

        return praise, growth, closing
