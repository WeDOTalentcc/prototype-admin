"""Add audit_execution_metadata table

Revision ID: 025_add_agent_execution_metadata
Revises: 024_add_disabled_eligibility_question_ids
Create Date: 2026-03-07

Tabela de metadados leves de execuções de agentes IA.
- Metadados aqui (rápido, indexável) → consultas de dashboard e investigação inicial
- Payload completo (prompts, respostas, tool I/O) → storage de objeto (path em storage_path)

Compliance: LGPD Art. 18, EU AI Act, SOX — auditabilidade de decisões de IA.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "025_add_agent_execution_metadata"
down_revision = "024_add_disabled_eligibility_question_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_execution_metadata",
        sa.Column("execution_id", sa.String(255), primary_key=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("domain", sa.String(100), nullable=True),
        sa.Column("agent_type", sa.String(50), nullable=True),   # "react" | "graph"
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("duration_ms", sa.Float, nullable=True),
        sa.Column("nodes_visited", JSONB, nullable=True, server_default="'[]'::jsonb"),
        sa.Column("tools_used", JSONB, nullable=True, server_default="'[]'::jsonb"),
        sa.Column("success", sa.Boolean, nullable=True, server_default="true"),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )

    op.create_index(
        "ix_audit_exec_company_id",
        "audit_execution_metadata",
        ["company_id"],
    )
    op.create_index(
        "ix_audit_exec_session_id",
        "audit_execution_metadata",
        ["session_id"],
    )
    op.create_index(
        "ix_audit_exec_domain",
        "audit_execution_metadata",
        ["domain"],
    )
    op.create_index(
        "ix_audit_exec_company_timestamp",
        "audit_execution_metadata",
        ["company_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_exec_company_timestamp", table_name="audit_execution_metadata")
    op.drop_index("ix_audit_exec_domain", table_name="audit_execution_metadata")
    op.drop_index("ix_audit_exec_session_id", table_name="audit_execution_metadata")
    op.drop_index("ix_audit_exec_company_id", table_name="audit_execution_metadata")
    op.drop_table("audit_execution_metadata")
