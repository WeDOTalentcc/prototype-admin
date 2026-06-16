"""281 — merge branches: 275_add_tier_policies + 280_add_correlation_id_lgpd_tables

Revision ID: 281_merge_tier_policies_branch
Revises: 275_add_tier_policies, 280_add_correlation_id_lgpd_tables
Create Date: 2026-06-14

Merge migration — consolida branch 275_add_tier_policies com 280.
Nenhuma alteracao de schema.
"""
from alembic import op

revision = "281_merge_tier_policies_branch"
down_revision = (
    "275_add_tier_policies",
    "280_add_correlation_id_lgpd_tables",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
