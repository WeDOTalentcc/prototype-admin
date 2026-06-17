"""add company_hiring_policies.policy_instructions (P3b)

Free-text recruiter instructions per policy concept (screening_criteria,
diversity_inclusion_guidelines, data_retention_candidate_policy, etc.). These
are PROMPT HINTS injected into the LIA system prompt — deliberately SEPARATE
from the 5 typed gate blocks (pipeline/scheduling/communication/screening/
automation_rules) so free text can never corrupt a typed gate (safety
invariant from the P0 anti-corruption work).

Revision ID: 231
Revises: 230
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision = "231"
down_revision = "230"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "company_hiring_policies",
        sa.Column(
            "policy_instructions",
            sa.JSON,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("company_hiring_policies", "policy_instructions")
