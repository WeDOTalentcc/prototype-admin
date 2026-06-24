"""267 — add auto_approve_threshold, review_threshold, sector to company_hiring_policies.screening_rules

Revision ID: 267_add_screening_thresholds_defaults
Revises: 266_create_fairness_policy_tables
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

revision = "267_add_screening_thresholds_defaults"
down_revision = "266_fairness_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill: screening_rules is json type, cast to jsonb for operators
    op.execute(sa.text(
        "UPDATE company_hiring_policies "
        "SET screening_rules = (screening_rules::jsonb || "
        "    \'{\"auto_approve_threshold\": null, \"review_threshold\": null, \"sector\": null}\'::jsonb)::json "
        "WHERE screening_rules IS NOT NULL "
        "  AND NOT (screening_rules::jsonb ? \'auto_approve_threshold\')"
    ))

def downgrade() -> None:
    op.execute(sa.text("""
        UPDATE company_hiring_policies
        SET screening_rules = screening_rules
            - 'auto_approve_threshold'
            - 'review_threshold'
            - 'sector'
        WHERE screening_rules IS NOT NULL
    """))
