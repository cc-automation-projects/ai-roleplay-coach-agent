from uuid import uuid4

import pytest
from pydantic import ValidationError

from core.entities import Evaluation, Scenario, User, XPTransaction
from core.entities.session import Session, TranscriptEntry
from core.entities.xp import XPReason


def test_username_too_short():
    with pytest.raises(ValidationError):
        User(
            username="ab",  # min length 3
            hashed_password="",
            email="test@test.com",
            name="Test",
        )


def test_username_invalid_chars():
    with pytest.raises(ValidationError):
        User(
            username="user name!",  # only alnum + underscore
            hashed_password="",
            email="test@test.com",
            name="Test",
        )


def test_evaluation_score_out_of_range():
    with pytest.raises(ValidationError):
        Evaluation(
            session_id=uuid4(),
            user_id=uuid4(),
            overall_score=150.0,  # max 100
            script_adherence=50.0,
            tone_score=50.0,
            empathy_score=50.0,
            objection_handling=50.0,
            completeness_score=50.0,
        )


def test_scenario_name_empty():
    with pytest.raises(ValidationError):
        Scenario(
            name="",
            description="desc",
            script_ref="ref",
            script_text="text",
        )


def test_xp_transaction_negative_amount_allowed():
    # XPTransaction permits negative amounts (penalties)
    txn = XPTransaction(
        user_id=uuid4(),
        amount=-10,
        reason=XPReason.SESSION_COMPLETED,
    )
    assert txn.amount == -10


def test_transcript_trimmed_to_100():
    entries = [TranscriptEntry(speaker="operator", text=f"msg{i}") for i in range(120)]
    session = Session(user_id=uuid4(), scenario_id=uuid4(), transcript=entries)
    assert len(session.transcript) == 100
