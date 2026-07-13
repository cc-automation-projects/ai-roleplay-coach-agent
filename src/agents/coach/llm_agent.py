"""LLMCoachAgent — LLM-powered dialogue evaluation with rule-based fallback.

Uses an LLMProvider to analyse a completed Session against the Scenario's
script_text, scoring across six dimensions and generating sandwich-format
feedback. If the LLM call fails (invalid JSON, exception, timeout) the
evaluation is delegated to the rule-based CoachAgent.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from core.entities import Evaluation
from core.interfaces.llm_provider import LLMMessage

if TYPE_CHECKING:
    from agents.coach.agent import CoachAgent
    from core.entities import Scenario, Session
    from core.interfaces.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_SCORE_MIN = 0.0
_SCORE_MAX = 100.0
_MAX_TRANSCRIPT_TOKENS = 3000  # rough char estimate for context limit
_DEFAULT_TEMPERATURE = 0.3
_DEFAULT_MAX_TOKENS = 1024

_SYSTEM_PROMPT = """\
You are a call centre coach expert. Analyse the operator's dialogue \
with a customer and return a JSON object with scores and feedback.

Scoring dimensions (each 0-100):
- script_adherence: how well the operator followed the script (keywords, structure)
- tone_score: politeness, professionalism, and positive language
- empathy_score: understanding and acknowledging the customer's feelings
- objection_handling: how well the operator addressed customer objections and concerns
- completeness_score: call completeness (greeting, middle, closing stages)
- overall_score: weighted overall performance

Also include:
- praise_text: what the operator did well (1-2 sentences, in Russian)
- growth_text: what can be improved (1-2 sentences, in Russian)
- closing_text: encouragement or next steps (1 sentence, in Russian)
- gaming_detected: whether the operator appears to be gaming the system (true/false)

Return ONLY valid JSON, no markdown formatting, no additional text.
"""


def _clamp(value: float, minimum: float = _SCORE_MIN, maximum: float = _SCORE_MAX) -> float:
    """Clamp a value to [minimum, maximum]."""
    return max(minimum, min(maximum, value))


def _parse_json_response(raw: str) -> dict[str, Any] | None:
    """Parse JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM JSON response: %s", exc)
        return None
    else:
        if isinstance(data, dict):
            return data
        logger.warning("LLM returned non-dict JSON: %s", type(data).__name__)
        return None


def _extract_score(data: dict[str, Any], key: str, default: float = 50.0) -> float:
    """Extract and clamp a score from parsed JSON data."""
    raw = data.get(key, default)
    try:
        return _clamp(float(raw))
    except (TypeError, ValueError):
        logger.warning("Invalid score for %s=%r, using default=%.1f", key, raw, default)
        return default


def _extract_text(data: dict[str, Any], key: str, default: str = "") -> str:
    """Extract text (feedback) from parsed JSON data."""
    raw = data.get(key, default)
    if isinstance(raw, str):
        return raw.strip()
    return default


def _extract_bool(data: dict[str, Any], key: str, default: bool = False) -> bool:  # noqa: FBT001, FBT002
    """Extract boolean flag from parsed JSON data."""
    raw = data.get(key, default)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.lower() in ("true", "yes", "1")
    return default


def _build_user_prompt(scenario: Scenario, session: Session) -> str:
    """Build the user prompt with scenario context and transcript."""
    lines = [f"Scenario: {scenario.name}"]
    if scenario.script_ref:
        lines.append(f"Script reference: {scenario.script_ref}")
    lines.append(f"Script text: {scenario.script_text or '(empty)'}")
    lines.append("")
    lines.append("Transcript:")
    lines.extend(
        f"  [{entry.timestamp}] {entry.speaker}: {entry.text}"
        for entry in session.transcript
    )

    # Truncate if too long (rough heuristic: ~4 chars per token)
    full = "\n".join(lines)
    if len(full) > _MAX_TRANSCRIPT_TOKENS * 4:
        logger.info(
            "Transcript too long (%d chars), truncating to last %d chars",
            len(full), _MAX_TRANSCRIPT_TOKENS * 4,
        )
        # Keep the scenario info (first ~500 chars) + last N chars of transcript
        scenario_part = lines[:3]
        transcript_start = len("\n".join(scenario_part))
        keep_chars = _MAX_TRANSCRIPT_TOKENS * 4 - transcript_start
        full = "\n".join(scenario_part) + "\n... (truncated) ...\n" + full[-max(keep_chars, 0):]

    return full


# ── LLMCoachAgent ──────────────────────────────────────────────────────


class LLMCoachAgent:
    """LLM-powered dialogue evaluator with rule-based fallback.

    Uses an LLM for semantic analysis of the dialogue. If the LLM is
    unavailable or returns invalid output, evaluation falls back to the
    rule-based CoachAgent.
    """

    def __init__(
        self,
        llm: LLMProvider,
        rule_based: CoachAgent,
    ) -> None:
        self._llm = llm
        self._rule_based = rule_based

    async def evaluate_session(
        self, session: Session, scenario: Scenario,
    ) -> Evaluation:
        """Analyse a completed session using LLM.

        Delegates to _llm_evaluate which calls llm.generate(). If the LLM
        returns invalid/unparseable JSON, falls back to the rule-based agent.
        LLM transport exceptions (timeout, connection) propagate to the
        caller (adapter) for CircuitBreaker handling.
        """
        return await self._llm_evaluate(session, scenario)

    async def _llm_evaluate(
        self, session: Session, scenario: Scenario,
    ) -> Evaluation:
        """Core LLM evaluation logic."""
        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=_build_user_prompt(scenario, session)),
        ]

        raw = await self._llm.generate(
            messages=messages,
            temperature=_DEFAULT_TEMPERATURE,
            max_tokens=_DEFAULT_MAX_TOKENS,
        )

        logger.debug("LLM raw response (%d chars): %s", len(raw), raw[:200])

        parsed = _parse_json_response(raw)
        if parsed is None:
            logger.warning("LLM response unparseable, falling back to rule-based")
            return await self._rule_based.evaluate_session(session, scenario)

        # Extract scores with clamping
        evaluation = Evaluation(
            session_id=session.id,
            user_id=session.user_id,
            overall_score=_extract_score(parsed, "overall_score"),
            script_adherence=_extract_score(parsed, "script_adherence"),
            tone_score=_extract_score(parsed, "tone_score"),
            empathy_score=_extract_score(parsed, "empathy_score"),
            objection_handling=_extract_score(parsed, "objection_handling"),
            completeness_score=_extract_score(parsed, "completeness_score"),
            praise_text=_extract_text(parsed, "praise_text"),
            growth_text=_extract_text(parsed, "growth_text"),
            closing_text=_extract_text(parsed, "closing_text"),
            gaming_detected=_extract_bool(parsed, "gaming_detected"),
        )

        logger.info(
            "LLM Coach evaluated session %s overall=%.1f",
            session.id, evaluation.overall_score,
        )
        return evaluation
