"""create compensation_components + history + job_vacancies.variable_compensation

Revision ID: 230
Revises: 229
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "230"
down_revision = "229"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compensation_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="bonus"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("value_type", sa.String(50), server_default="percent"),
        sa.Column("target_pct", sa.Float, nullable=True),
        sa.Column("min_pct", sa.Float, nullable=True),
        sa.Column("max_pct", sa.Float, nullable=True),
        sa.Column("min_amount", sa.Float, nullable=True),
        sa.Column("max_amount", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), server_default="BRL"),
        sa.Column("frequency", sa.String(50), nullable=True),
        sa.Column("trigger", sa.String(50), nullable=True),
        sa.Column("spec", postgresql.JSONB, nullable=True),
        sa.Column("seniority_levels", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("contract_types", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("departments", postgresql.JSONB, nullable=True),
        sa.Column("subsidiaries", postgresql.JSONB, nullable=True),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_highlighted", sa.Boolean, server_default=sa.text("false")),
        sa.Column("order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_compensation_components_company_id", "compensation_components", ["company_id"])

    op.create_table(
        "compensation_component_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "component_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compensation_components.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("changed_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("change_type", sa.String(50), nullable=False),
        sa.Column("previous_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("change_notes", sa.Text, nullable=True),
    )
    op.create_index("ix_comp_component_history_component_id", "compensation_component_history", ["component_id"])
    op.create_index("ix_comp_component_history_company_id", "compensation_component_history", ["company_id"])

    # vaga: coluna estruturada de verbas variaveis (snapshot+ref, mirror benefits)
    op.add_column("job_vacancies", sa.Column("variable_compensation", postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("job_vacancies", "variable_compensation")
    op.drop_index("ix_comp_component_history_company_id", table_name="compensation_component_history")
    op.drop_index("ix_comp_component_history_component_id", table_name="compensation_component_history")
    op.drop_table("compensation_component_history")
    op.drop_index("ix_compensation_components_company_id", table_name="compensation_components")
    op.drop_table("compensation_components")
