import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    _indexes_up()
    _badge_cols_up()


def _indexes_up() -> None:
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_scid", "sessions", ["scenario_id"])
    op.create_index("ix_eval_session", "evaluations", ["session_id"])
    op.create_index("ix_eval_user", "evaluations", ["user_id"])
    op.create_index("ix_ub_user", "user_badges", ["user_id"])
    op.create_index("ix_ub_badge", "user_badges", ["badge_id"])
    op.create_index("ix_xp_user", "xp_transactions", ["user_id"])
    op.create_index("ix_te_session", "transcript_entries", ["session_id"])


def _badge_cols_up() -> None:
    op.alter_column("badges", "description", type_=sa.String(500), existing_type=sa.Text())
    op.alter_column("badges", "criteria", type_=sa.String(1000), existing_type=sa.Text())
    op.alter_column("badges", "icon_url", type_=sa.String(500), existing_nullable=True)


def downgrade() -> None:
    _badge_cols_down()
    _indexes_down()


def _badge_cols_down() -> None:
    op.alter_column("badges", "icon_url", type_=sa.Text(), existing_type=sa.String(500))
    op.alter_column("badges", "criteria", type_=sa.Text(), existing_type=sa.String(1000))
    op.alter_column("badges", "description", type_=sa.Text(), existing_type=sa.String(500))


def _indexes_down() -> None:
    op.drop_index("ix_te_session", table_name="transcript_entries")
    op.drop_index("ix_xp_user", table_name="xp_transactions")
    op.drop_index("ix_ub_badge", table_name="user_badges")
    op.drop_index("ix_ub_user", table_name="user_badges")
    op.drop_index("ix_eval_user", table_name="evaluations")
    op.drop_index("ix_eval_session", table_name="evaluations")
    op.drop_index("ix_sessions_scid", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
