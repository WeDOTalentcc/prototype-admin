"""Extend company_benefits with structured schema fields.

Revision ID: 099_extend_company_benefits_schema
Revises: 098_create_offer_proposals_table
Create Date: 2026-04-21

Aligns `company_benefits` with the rich schema already used by the
front-end (percentage_value, value_details, seniority_levels,
waiting_period_days, is_mandatory, is_discount, provider). Idempotent —
only adds columns that are missing so environments bootstrapped via
``Base.metadata.create_all`` stay healthy.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "099_extend_company_benefits_schema"
down_revision = "098_create_offer_proposals_table"
branch_labels = None
depends_on = None


_NEW_COLUMNS = [
    ("provider", sa.Column("provider", sa.String(length=255), nullable=True)),
    ("percentage_value", sa.Column("percentage_value", sa.Float(), nullable=True)),
    ("value_details", sa.Column("value_details", sa.Text(), nullable=True)),
    ("seniority_levels", sa.Column("seniority_levels", JSONB(), nullable=True)),
    (
        "waiting_period_days",
        sa.Column(
            "waiting_period_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    ),
    (
        "is_mandatory",
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    ),
    (
        "is_discount",
        sa.Column(
            "is_discount",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "company_benefits" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("company_benefits")}
    for name, column in _NEW_COLUMNS:
        if name not in existing:
            op.add_column("company_benefits", column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "company_benefits" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("company_benefits")}
    for name, _ in reversed(_NEW_COLUMNS):
        if name in existing:
            try:
                op.drop_column("company_benefits", name)
            except Exception:
                pass
