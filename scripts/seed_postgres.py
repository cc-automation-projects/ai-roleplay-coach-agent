#!/usr/bin/env python
"""Seed script: populate PostgreSQL with test users, scenarios, and badges."""

from __future__ import annotations

import asyncio
import logging
import uuid

from core.entities import (
    BadgeCreate,
    DifficultyLevel,
    EvaluationCreate,
    Psychotype,
    ScenarioCreate,
    Session,
    SessionCreate,
    SessionStatus,
    UserCreate,
    UserRole,
    XPReason,
)
from core.entities.xp import XPTransaction as XPDomain
from infrastructure.postgres.database import Database
from infrastructure.postgres.repositories import (
    BadgeRepo,
    EvaluationRepo,
    ScenarioRepo,
    SessionRepo,
    UserRepo,
    XPTransactionRepo,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def main() -> None:
    """Run the seed."""
    db = Database()

    async with db.session() as session:
        user_repo = UserRepo(session)
        scenario_repo = ScenarioRepo(session)
        session_repo = SessionRepo(session)
        evaluation_repo = EvaluationRepo(session)
        badge_repo = BadgeRepo(session)
        xp_repo = XPTransactionRepo(session)

        # --- Users ---
        users_data = [
            UserCreate(
                username="alice",
                hashed_password="",
                email="alice@example.com",
                name="Alice Johnson",
                role=UserRole.OPERATOR,
            ),
            UserCreate(
                username="bob",
                hashed_password="",
                email="bob@example.com",
                name="Bob Smith",
                role=UserRole.OPERATOR,
            ),
            UserCreate(
                username="carol",
                hashed_password="",
                email="carol@example.com",
                name="Carol Davis",
                role=UserRole.TRAINER,
            ),
        ]
        created_users = []
        for ud in users_data:
            user = await user_repo.create(ud)
            created_users.append(user)
            logger.info("Created user: %s (%s)", user.name, user.id)

        # Add XP for operators
        for user in created_users[:2]:
            txn = XPDomain(
                user_id=user.id,
                amount=150,
                reason=XPReason.SESSION_COMPLETED,
                reference_id=uuid.uuid4(),
            )
            await xp_repo.create(txn)
            logger.info("Added XP to user %s — %d XP (reason: %s)", user.id, txn.amount, txn.reason)

        # --- Scenarios ---
        scenarios_data = [
            ScenarioCreate(
                name="Tech Support — Internet Outage",
                description="Customer reporting complete internet outage.",
                script_ref="scripts/tech_support_outage.md",
                script_text=(
                    "You are a Level 1 tech support agent. "
                    "A customer calls because their internet has been down for 3 hours. "
                    "Steps:\n"
                    "1. Acknowledge frustration\n"
                    "2. Verify account details\n"
                    "3. Run remote modem diagnostics\n"
                    "4. Check area outage map\n"
                    "5. If outage confirmed — provide ETA and offer credit\n"
                    "6. If no outage — escalate to Level 2"
                ),
                tags=["tech-support", "internet", "outage"],
                difficulty=DifficultyLevel.BEGINNER,
                psychotype=Psychotype.NEUTRAL,
            ),
            ScenarioCreate(
                name="Billing — Disputed Charge",
                description="Customer disputing a charge on their monthly bill.",
                script_ref="scripts/billing_dispute.md",
                script_text=(
                    "You are a billing specialist. "
                    "A customer claims they were overcharged for a service they didn't order. "
                    "Steps:\n"
                    "1. Listen without interrupting\n"
                    "2. Review billing history\n"
                    "3. Identify the charge and verify service activation\n"
                    "4. If error — apologize and issue credit\n"
                    "5. If valid charge — explain itemized breakdown\n"
                    "6. Offer payment plan if needed"
                ),
                tags=["billing", "dispute", "refund"],
                difficulty=DifficultyLevel.INTERMEDIATE,
                psychotype=Psychotype.CONFUSED,
            ),
            ScenarioCreate(
                name="Retention — Cancel Subscription",
                description="High-value customer threatening to cancel.",
                script_ref="scripts/retention_cancel.md",
                script_text=(
                    "You are a retention specialist. "
                    "A loyal customer of 3 years wants to cancel their premium plan. "
                    "Steps:\n"
                    "1. Empathize with their specific pain point\n"
                    "2. Review account history and identify value\n"
                    "3. Offer targeted retention incentive (discount, feature upgrade)\n"
                    "4. If they accept — confirm terms and thank them\n"
                    "5. If they decline — make one final tailored offer\n"
                    "6. Process cancellation professionally if needed"
                ),
                tags=["retention", "cancellation", "churn"],
                difficulty=DifficultyLevel.ADVANCED,
                psychotype=Psychotype.AGGRESSIVE,
            ),
            ScenarioCreate(
                name="Sales — Upgrade Pitch",
                description="Inbound call — opportunity to upsell customer.",
                script_ref="scripts/sales_upgrade.md",
                script_text=(
                    "You are a sales consultant. "
                    "A customer calls to pay their bill — you identify an upgrade opportunity. "
                    "Steps:\n"
                    "1. Handle the original request efficiently\n"
                    "2. Ask a discovery question about usage\n"
                    "3. Present the upgrade as a solution to their unstated need\n"
                    "4. Handle objection with value proposition\n"
                    "5. Close — offer trial or discount for first month"
                ),
                tags=["sales", "upsell", "upgrade"],
                difficulty=DifficultyLevel.INTERMEDIATE,
                psychotype=Psychotype.NEUTRAL,
            ),
            ScenarioCreate(
                name="Complaint — Executive Escalation",
                description="Furious customer demanding manager after unresolved issue.",
                script_ref="scripts/escalation_complaint.md",
                script_text=(
                    "You are a senior agent handling escalated calls. "
                    "A customer has been transferred to you after 3 failed interactions. "
                    "Steps:\n"
                    "1. Own the issue — do not blame previous agents\n"
                    "2. Summarize the history to show understanding\n"
                    "3. Present one clear solution with timeline\n"
                    "4. Get buy-in with follow-up commitment\n"
                    "5. Offer goodwill gesture before ending the call"
                ),
                tags=["complaint", "escalation", "executive"],
                difficulty=DifficultyLevel.ADVANCED,
                psychotype=Psychotype.AGGRESSIVE,
            ),
        ]
        created_scenarios = []
        for sd in scenarios_data:
            scenario = await scenario_repo.create(sd)
            created_scenarios.append(scenario)
            logger.info("Created scenario: %s (%s)", scenario.name, scenario.id)

        # --- Badges ---
        badges_data = [
            BadgeCreate(
                name="First Call Resolution",
                description="Resolved a customer issue on the first contact.",
                criteria="Complete a session with score > 85 and no escalation.",
                icon_url="/badges/fcr.png",
                xp_reward=100,
            ),
            BadgeCreate(
                name="Empathy Star",
                description="Demonstrated exceptional empathy in a difficult interaction.",
                criteria="Score > 90 on empathy in an advanced scenario.",
                icon_url="/badges/empathy.png",
                xp_reward=75,
            ),
            BadgeCreate(
                name="Billing Whiz",
                description="Mastered billing scenarios with perfect accuracy.",
                criteria="Score > 95 on three billing scenarios.",
                icon_url="/badges/billing.png",
                xp_reward=150,
            ),
        ]
        for bd in badges_data:
            badge = await badge_repo.create(bd)
            logger.info("Created badge: %s (%s)", badge.name, badge.id)

        # --- Sessions + Evaluations ---
        for user in created_users[:2]:
            for scenario in created_scenarios[:2]:
                sess = await session_repo.create(
                    SessionCreate(user_id=user.id, scenario_id=scenario.id)
                )
                # Create evaluation
                ev = await evaluation_repo.create(
                    EvaluationCreate(
                        session_id=sess.id,
                        user_id=user.id,
                        overall_score=78.5,
                        script_adherence=82.0,
                        tone_score=75.0,
                        empathy_score=70.0,
                        objection_handling=80.0,
                        completeness_score=85.0,
                        praise_text="Good script adherence. Kept the conversation on track.",
                        growth_text="Try to show more empathy early in the call.",
                        closing_text="Solid performance overall. Practice active listening.",
                    )
                )
                logger.info("Created evaluation for user %s: score=%.1f", user.id, ev.overall_score)
                # Complete the session
                completed = Session(
                    id=sess.id,
                    user_id=user.id,
                    scenario_id=scenario.id,
                    status=SessionStatus.COMPLETED,
                    transcript=sess.transcript,
                    created_at=sess.created_at,
                    updated_at=sess.updated_at,
                )
                await session_repo.update(completed)
                logger.info("Completed session %s", sess.id)

    logger.info("✅ Seeding complete! 3 users, 5 scenarios, 3 badges, 4 evaluations")


if __name__ == "__main__":
    asyncio.run(main())
