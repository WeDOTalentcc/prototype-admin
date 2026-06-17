"""pii field-level visibility: users.pii_field_visibility + company_hiring_policies.pii_visibility_defaults

Revision ID: 245
Revises: 244
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "245"
down_revision = "244"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("pii_field_visibility", JSONB, nullable=True))
    op.add_column(
        "company_hiring_policies",
        sa.Column("pii_visibility_defaults", JSONB, nullable=True),
    )


def downgrade():
    op.drop_column("company_hiring_policies", "pii_visibility_defaults")
    op.drop_column("users", "pii_field_visibility")
