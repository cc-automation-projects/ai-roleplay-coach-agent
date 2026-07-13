"""Tests for CoachAgent — rule-based dialogue analysis and feedback."""

from uuid import uuid4

import pytest

from agents.coach.agent import CoachAgent
from core.entities import (
    DifficultyLevel,
    Psychotype,
    Scenario,
    Session,
    SessionStatus,
)


class TestCoachAgent:
    """CoachAgent: evaluate_session — scoring, analysis, sandwich feedback."""

    @pytest.fixture
    def scenario(self) -> Scenario:
        return Scenario(
            name="Billing issue",
            description="Customer with billing dispute",
            script_ref="s-002",
            script_text=(
                "Greet the customer warmly. "
                "Identify the billing issue by asking open-ended questions. "
                "Empathize with the customer's frustration. "
                "Explain the charges clearly. "
                "Offer a solution or adjustment. "
                "Confirm the customer is satisfied. "
                "Close the call professionally."
            ),
            psychotype=Psychotype.AGGRESSIVE,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )

    @pytest.fixture
    def coach(self) -> CoachAgent:
        return CoachAgent()

    # ── Basic smoke ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_evaluate_session_returns_evaluation(
        self, coach, scenario
    ):
        """Returns an Evaluation with all required fields."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Hello!")
        session.append_transcript_entry("client", "I have a problem!")
        session.append_transcript_entry("operator", "How can I help?")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.session_id == session.id
        assert eval_result.user_id == session.user_id
        assert 0.0 <= eval_result.overall_score <= 100.0
        assert eval_result.praise_text
        assert eval_result.growth_text
        assert eval_result.closing_text

    # ── Script adherence ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_script_adherence_good_operator(self, coach, scenario):
        """Operator who follows script keywords gets high adherence."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        # Operator messages include script keywords directly
        session.append_transcript_entry(
            "operator", "Hello, welcome! Let me greet you warmly."
        )
        session.append_transcript_entry("client", "I'm angry about my bill!")
        session.append_transcript_entry(
            "operator",
            "Let me identify the billing issue. Are you asking about charges?",
        )
        session.append_transcript_entry("client", "Yes, it's too high!")
        session.append_transcript_entry(
            "operator",
            "I understand your frustration. Let me empathize with your concern "
            "and explain the charges clearly.",
        )
        session.append_transcript_entry("client", "OK.")
        session.append_transcript_entry(
            "operator",
            "Let me offer a solution — I can adjust this for you. "
            "Would that satisfy your needs?",
        )
        session.append_transcript_entry("client", "Yes, that works.")
        session.append_transcript_entry(
            "operator",
            "Great! Let me confirm you are satisfied. "
            "I'm happy we could close this professionally.",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.script_adherence >= 50.0

    @pytest.mark.asyncio
    async def test_script_adherence_poor_operator(self, coach, scenario):
        """Operator who ignores script keywords gets low adherence."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Yeah?")
        session.append_transcript_entry("client", "My bill is wrong!")
        session.append_transcript_entry("operator", "Not my problem.")
        session.append_transcript_entry("client", "What?")
        session.append_transcript_entry("operator", "Pay it or don't.")
        session.append_transcript_entry("client", "Fine.")
        session.append_transcript_entry("operator", "Bye.")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.script_adherence <= 40.0

    # ── Tone analysis ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_tone_polite_operator_high_score(self, coach, scenario):
        """Polite, professional language yields high tone score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry(
            "operator", "Good morning, thank you for calling. How may I assist you?"
        )
        session.append_transcript_entry("client", "I have a complaint.")
        session.append_transcript_entry(
            "operator",
            "I sincerely apologise for the inconvenience. Please allow me to help.",
        )
        session.append_transcript_entry("client", "OK.")
        session.append_transcript_entry(
            "operator",
            "Thank you for your patience. Is there anything else I can do for you?",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.tone_score >= 70.0

    @pytest.mark.asyncio
    async def test_tone_rude_operator_low_score(self, coach, scenario):
        """Rude or dismissive language yields low tone score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "What do you want?")
        session.append_transcript_entry("client", "I need help.")
        session.append_transcript_entry("operator", "Can't you read the FAQ?")
        session.append_transcript_entry("client", "No.")
        session.append_transcript_entry("operator", "Fine, what's the account number?")
        session.append_transcript_entry("client", "12345.")
        session.append_transcript_entry("operator", "Whatever. Done.")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.tone_score <= 50.0

    # ── Empathy detection ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_empathy_detected(self, coach, scenario):
        """Empathetic language detected → high empathy score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry(
            "operator",
            "I completely understand why you're upset. That must be frustrating.",
        )
        session.append_transcript_entry("client", "It is!")
        session.append_transcript_entry(
            "operator",
            "I hear you, and I'm sorry for the trouble. Let me make this right.",
        )
        session.append_transcript_entry("client", "OK.")
        session.append_transcript_entry(
            "operator",
            "I appreciate your understanding. You've been very patient.",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.empathy_score >= 60.0

    @pytest.mark.asyncio
    async def test_empathy_missing(self, coach, scenario):
        """No empathetic language → low empathy score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Next.")
        session.append_transcript_entry("client", "I'm upset!")
        session.append_transcript_entry("operator", "Give me your details.")
        session.append_transcript_entry("client", "Here.")
        session.append_transcript_entry("operator", "Done. Next call.")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.empathy_score <= 40.0

    # ── Objection handling ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_objection_handling_good(self, coach, scenario):
        """Operator who addresses objections gets high score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Hello, how can I help?")
        session.append_transcript_entry("client", "Your service is terrible!")
        session.append_transcript_entry(
            "operator",
            "I understand you feel that way. Let me explain what happened and how we can fix it.",
        )
        session.append_transcript_entry(
            "client", "I don't think you can help."
        )
        session.append_transcript_entry(
            "operator",
            "I appreciate your concern. Here's what I can offer as a solution.",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.objection_handling >= 60.0

    @pytest.mark.asyncio
    async def test_objection_handling_poor(self, coach, scenario):
        """Operator who ignores objections gets low score."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Hello.")
        session.append_transcript_entry("client", "I hate this company!")
        session.append_transcript_entry(
            "operator", "That's not a question. Do you have an account number?"
        )
        session.append_transcript_entry("client", "You're not listening!")
        session.append_transcript_entry("operator", "I need your account number.")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.objection_handling <= 50.0

    # ── Completeness ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_completeness_full_coverage(self, coach, scenario):
        """Operator who covers all script steps gets high completeness."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        # Cover greeting, identification, empathy, explanation, solution, confirmation, closing
        session.append_transcript_entry("operator", "Welcome! How can I help?")
        session.append_transcript_entry("client", "My bill is wrong!")
        session.append_transcript_entry(
            "operator",
            "Let me ask you a few questions to understand the issue better.",
        )
        session.append_transcript_entry("client", "I was overcharged.")
        session.append_transcript_entry(
            "operator",
            "I understand why that's frustrating. I'm sorry about that.",
        )
        session.append_transcript_entry("client", "Fix it!")
        session.append_transcript_entry(
            "operator",
            "Let me explain the charges. You were billed for premium features.",
        )
        session.append_transcript_entry("client", "I didn't order those.")
        session.append_transcript_entry(
            "operator",
            "I can offer a full adjustment. Would that work for you?",
        )
        session.append_transcript_entry("client", "Yes.")
        session.append_transcript_entry(
            "operator",
            "Great! Are you satisfied with this resolution?",
        )
        session.append_transcript_entry("client", "Yes, thank you.")
        session.append_transcript_entry(
            "operator",
            "Thank you for your time. Have a wonderful day!",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.completeness_score >= 70.0

    # ── Feedback format ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_sandwich_feedback_format(self, coach, scenario):
        """Feedback follows sandwich structure: praise → growth → closing."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Hello, how can I help?")
        session.append_transcript_entry("client", "I need assistance.")
        session.append_transcript_entry(
            "operator", "Sure, let me help you with that."
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.praise_text
        assert eval_result.growth_text
        assert eval_result.closing_text
        assert len(eval_result.praise_text) > 10
        assert len(eval_result.growth_text) > 10
        assert len(eval_result.closing_text) > 10

    # ── Edge cases ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_empty_transcript(self, coach, scenario):
        """Empty transcript yields minimal scores and appropriate feedback."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.overall_score <= 30.0
        assert eval_result.completeness_score == 0.0

    @pytest.mark.asyncio
    async def test_short_transcript(self, coach, scenario):
        """Very short transcript yields low completeness."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry("operator", "Hi.")
        session.append_transcript_entry("client", "Hello.")
        session.append_transcript_entry("operator", "Bye.")

        eval_result = await coach.evaluate_session(session, scenario)

        assert eval_result.completeness_score <= 40.0

    @pytest.mark.asyncio
    async def test_neutral_scoring_balance(self, coach, scenario):
        """Neutral operator scores around 30-90 across dimensions."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        session.append_transcript_entry(
            "operator", "Hello, welcome! How can I assist you today?"
        )
        session.append_transcript_entry("client", "I have a billing problem.")
        session.append_transcript_entry(
            "operator",
            "Sure, let me identify the issue. Can I have your details "
            "so I can explain the charges?",
        )
        session.append_transcript_entry("client", "Sure, here you go.")
        session.append_transcript_entry(
            "operator",
            "I see the problem. Let me offer a solution that works for you.",
        )
        session.append_transcript_entry("client", "That works.")
        session.append_transcript_entry(
            "operator",
            "Great, I'm glad we could resolve this professionally.",
        )
        session.append_transcript_entry("client", "No.")
        session.append_transcript_entry(
            "operator",
            "Thanks for your time then. Bye.",
        )

        eval_result = await coach.evaluate_session(session, scenario)

        # Mid-range check: scores should be reasonable, not all extremes
        assert 20.0 <= eval_result.script_adherence <= 95.0
        assert 20.0 <= eval_result.completeness_score <= 95.0
        # tone can be 100 for a polite operator with no negative markers
        assert eval_result.tone_score >= 20.0
