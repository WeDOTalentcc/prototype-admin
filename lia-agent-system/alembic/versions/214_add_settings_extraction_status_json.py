"""Add settings_extraction_status_json to onboarding_agent_state.

Closes the persistence gap where OnboardingSession.settings_extraction_status_json
was set in memory but never saved to DB — extraction state was lost on page reload.

Sprint 2 BE-3 (2026-05-27)
"""
from alembic import op
import sqlalchemy as sa

revision = "214"
down_revision = "213_sync_trigger_types_canonical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "onboarding_agent_state",
        sa.Column("settings_extraction_status_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("onboarding_agent_state", "settings_extraction_status_json")
