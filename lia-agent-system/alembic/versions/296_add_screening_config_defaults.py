"""Migration 296: add screening_config_defaults to company_hiring_policies."""
revision = "296_add_screening_config_defaults"
down_revision = "295"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(
        "company_hiring_policies",
        sa.Column(
            "screening_config_defaults",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("company_hiring_policies", "screening_config_defaults")
