"""SessionService — orchestrates the simulation lifecycle.

Coordinates the Simulator and Coach agents through the
start → turn → finish lifecycle of a single training session.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.entities import Session, SessionCreate, SessionStatus, TranscriptEntry
from core.exceptions import BusinessRuleViolationError, NotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from core.entities import Evaluation
    from core.interfaces.agents import CoachAgent, SimulatorAgent
    from core.interfaces.repositories import (
        EvaluationRepository,
        ScenarioRepository,
        SessionRepository,
        UserRepository,
    )

_NOT_FOUND_SCENARIO = "Scenario"
_NOT_FOUND_SESSION = "Session"
_NOT_FOUND_USER = "User"

logger = logging.getLogger(__name__)


class SessionService:
    """Orchestrates a single simulation session end-to-end."""

    def __init__(  # noqa: PLR0913
        self,
        session_repo: SessionRepository,
        scenario_repo: ScenarioRepository,
        simulator: SimulatorAgent,
        coach: CoachAgent,
        user_repo: UserRepository | None = None,
        eval_repo: EvaluationRepository | None = None,
    ) -> None:
        self._session_repo = session_repo
        self._scenario_repo = scenario_repo
        self._simulator = simulator
        self._coach = coach
        self._user_repo = user_repo
        self._eval_repo = eval_repo

    async def start_session(
        self,
        user_id: UUID,
        scenario_id: UUID,
    ) -> Session:
        """Start a new simulation session.

        1. Load the scenario.
        2. Ask the Simulator for an initial greeting and psychotype.
        3. Persist the session in IN_PROGRESS state.

        Returns the created session.
        """
        if self._user_repo is not None:
            user = await self._user_repo.get_by_id(user_id)
            if user is None:
                raise NotFoundError(_NOT_FOUND_USER, str(user_id))

        scenario = await self._scenario_repo.get_by_id(scenario_id)
        if scenario is None:
            raise NotFoundError(_NOT_FOUND_SCENARIO, str(scenario_id))

        greeting, psychotype = await self._simulator.start_dialogue(scenario)

        return await self._session_repo.create(
            SessionCreate(
                user_id=user_id,
                scenario_id=scenario_id,
                status=SessionStatus.IN_PROGRESS,
                difficulty_at_start=scenario.difficulty,
                psychotype_at_start=psychotype,
                script_text_at_start=scenario.script_text,
                transcript=[
                    TranscriptEntry(speaker="client", text=greeting),
                ],
            )
        )

    async def process_turn(
        self,
        session_id: UUID,
        operator_text: str,
    ) -> TranscriptEntry:
        """Process a single operator turn.

        1. Load and validate the session is in progress.
        2. Append the operator message to the transcript.
        3. Ask the Simulator for a client response.
        4. Append the client response and persist.

        Returns the client's response transcript entry.
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(_NOT_FOUND_SESSION, str(session_id))
        if session.status != SessionStatus.IN_PROGRESS:
            msg = (
                f"Session {session_id} is {session.status.value}, not in progress"
            )
            raise BusinessRuleViolationError(msg)

        # Append operator turn
        session.append_transcript_entry(speaker="operator", text=operator_text)

        # Generate and append client response
        client_text = await self._simulator.generate_response(session)
        session.append_transcript_entry(speaker="client", text=client_text)

        await self._session_repo.update(session)

        return session.transcript[-1]

    async def finish_session(self, session_id: UUID) -> Session:
        """Finish a session.

        1. Load the session and its scenario.
        2. Mark the session as completed.
        3. Persist and return the updated session.

        NOTE: Evaluation is produced separately via the Coach agent;
              this method only terminates the session.
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(_NOT_FOUND_SESSION, str(session_id))

        session.status = SessionStatus.COMPLETED
        return await self._session_repo.update(session)

    async def get_session(self, session_id: UUID) -> Session:
        """Retrieve a session by ID."""
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(_NOT_FOUND_SESSION, str(session_id))
        return session

    async def evaluate_session(self, session_id: UUID) -> Evaluation:
        """Run the Coach evaluation on a completed session and persist it.

        Returns the persisted evaluation (with ID and timestamps).
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(_NOT_FOUND_SESSION, str(session_id))

        scenario = await self._scenario_repo.get_by_id(session.scenario_id)
        if scenario is None:
            raise NotFoundError(_NOT_FOUND_SCENARIO, str(session.scenario_id))

        evaluation = await self._coach.evaluate_session(session, scenario)

        # Persist the evaluation if we have an eval repo wired
        if self._eval_repo is not None:
            evaluation = await self._eval_repo.create(evaluation)

        return evaluation
