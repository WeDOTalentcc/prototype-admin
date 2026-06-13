"""273 — create role_scope_filters table

Revision ID: 273_create_role_scope_filters
Revises: 272_add_correlation_id_observability
Create Date: 2026-06-13

Sprint C — RBAC declarativo.
Permissões vivem na tabela role_scope_filters, não no código de endpoint.
Harness: Guide computacional consultado pelo ScopeFilterService em runtime.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "273_create_role_scope_filters"
down_revision = "272_add_correlation_id_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_scope_filters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(80), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("conditions", JSONB, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("role", "resource", "action", name="uq_role_resource_action"),
    )
    op.create_index("ix_rsf_role_resource", "role_scope_filters", ["role", "resource"])
    op.create_index("ix_rsf_allowed", "role_scope_filters", ["allowed"])


def downgrade() -> None:
    op.drop_index("ix_rsf_allowed")
    op.drop_index("ix_rsf_role_resource")
    op.drop_table("role_scope_filters")
