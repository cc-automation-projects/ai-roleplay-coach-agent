"""Tests for SimulatorAgent — LangGraph-powered client simulator."""

from uuid import uuid4

import pytest

from agents.simulator.agent import SimulatorAgent
from core.entities import (
    DifficultyLevel,
    Psychotype,
    Scenario,
    Session,
    SessionStatus,
)
from core.exceptions import BusinessRuleViolationError


class TestSimulatorAgent:
    """SimulatorAgent: start_dialogue, generate_response, should_end."""

    @pytest.fixture
    def scenario(self) -> Scenario:
        return Scenario(
            name="Angry customer",
            description="Aggressive client with billing issue",
            script_ref="s-001",
            script_text=(
                "Operator should greet the customer. "
                "Identify the billing issue. "
                "Handle objections about late fees. "
                "Offer a solution and close."
            ),
            psychotype=Psychotype.AGGRESSIVE,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )

    @pytest.fixture
    def simulator(self) -> SimulatorAgent:
        return SimulatorAgent()

    # ── start_dialogue ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_start_dialogue_returns_greeting_and_psychotype(
        self, simulator, scenario
    ):
        """Returns a non-empty greeting and the scenario's psychotype."""
        greeting, psychotype = await simulator.start_dialogue(scenario)

        assert greeting, "Greeting should not be empty"
        assert psychotype == Psychotype.AGGRESSIVE

    @pytest.mark.asyncio
    async def test_start_dialogue_different_psychotypes(self, simulator):
        """Each psychotype produces a distinct greeting."""
        greetings = set()
        for pt in Psychotype:
            s = Scenario(
                name=f"Test {pt.value}",
                description=f"Test for {pt.value}",
                script_ref="s-001",
                script_text="Test script.",
                psychotype=pt,
            )
            greeting, returned_pt = await simulator.start_dialogue(s)
            assert returned_pt == pt
            greetings.add(greeting)

        assert len(greetings) == len(Psychotype), (
            f"Expected {len(Psychotype)} unique greetings, got {len(greetings)}"
        )

    # ── generate_response ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_generate_response_returns_client_message(
        self, simulator, scenario
    ):
        """Given a session with transcript, returns a client response."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.IN_PROGRESS,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.AGGRESSIVE,
        )
        session.append_transcript_entry(
            "operator", "Hello, thank you for calling. How can I help you today?"
        )

        response = await simulator.generate_response(session)

        assert response, "Response should not be empty"
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_generate_response_requires_operator_turn(self, simulator):
        """Raises error if last turn is not from operator (after greeting)."""
        session = Session(
            id=uuid4(), user_id=uuid4(), scenario_id=uuid4()
        )
        # Single client greeting is allowed (post-creation)
        session.append_transcript_entry("client", "Hello?")
        session.append_transcript_entry("operator", "How can I help?")
        # After the operator responds, the next entry must be operator too
        session.append_transcript_entry("client", "I need help")

        with pytest.raises(BusinessRuleViolationError, match="operator"):
            await simulator.generate_response(session)

    @pytest.mark.asyncio
    async def test_generate_response_tracks_stage(
        self, simulator, scenario
    ):
        """Responses vary by dialogue stage (greeting → need_id → objection → closing)."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.NEUTRAL,
        )

        # Turn 1: operator greets → should be need_id stage response
        session.append_transcript_entry("operator", "Hello!")
        r1 = await simulator.generate_response(session)

        # Turn 2: operator asks question → should be objection stage
        session.append_transcript_entry("operator", "How can I help?")
        r2 = await simulator.generate_response(session)

        # Turn 3: operator handles objection → should progress
        session.append_transcript_entry("operator", "I understand your concern.")
        r3 = await simulator.generate_response(session)

        assert r1
        assert r2
        assert r3
        assert simulator.get_state(session.id) is not None

    # ── should_end ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_should_end_returns_false_for_new_session(
        self, simulator, scenario
    ):
        """Fresh session should not end."""
        session = Session(
            id=uuid4(), user_id=uuid4(), scenario_id=scenario.id
        )
        assert await simulator.should_end(session) is False

    @pytest.mark.asyncio
    async def test_should_end_after_max_turns(self, simulator, scenario):
        """Session with many turns should end."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.IN_PROGRESS,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.NEUTRAL,
        )
        # Simulate many operator+client exchanges
        for i in range(12):
            session.append_transcript_entry("operator", f"Operator message {i}")
            session.append_transcript_entry("client", f"Client message {i}")

        assert await simulator.should_end(session) is True

    @pytest.mark.asyncio
    async def test_should_end_not_too_early(self, simulator, scenario):
        """Short session should not end."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            status=SessionStatus.IN_PROGRESS,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.NEUTRAL,
        )
        session.append_transcript_entry("operator", "Hello")
        session.append_transcript_entry("client", "Hi, I need help")
        session.append_transcript_entry("operator", "Sure, what's the issue?")

        assert await simulator.should_end(session) is False

    # ── get_state / reset_session ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_reset_session(self, simulator, scenario):
        """Reset clears internal state for a session."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=scenario.id,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.NEUTRAL,
        )
        session.append_transcript_entry("operator", "Hello")

        # generate_response creates state lazily
        await simulator.generate_response(session)
        assert simulator.get_state(session.id) is not None

        # Reset clears it
        simulator.reset_session(session.id)
        assert simulator.get_state(session.id) is None
