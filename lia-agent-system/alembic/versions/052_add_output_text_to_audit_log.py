"""Add output_text and input_text to audit_logs for conversational auditing

Revision ID: 052
Revises: 051
Create Date: 2026-04-04

WHY: O modelo audit_log atual rastreia apenas decisões estruturadas (score, reasoning,
     criteria_used). A saída textual da LIA para o recrutador nunca é armazenada,
     impossibilitando auditoria completa conforme EU AI Act Art. 13 (transparency)
     e LGPD Art. 18 (direito de explicação).

CAMPOS ADICIONADOS:
  input_text    → mensagem do recrutador que gerou a resposta
  output_text   → resposta textual da LIA (o que o recrutador viu)
  fairness_flags → lista de alertas soft gerados pelo FairnessGuard (JSON)
  agent_used    → qual domínio/agente respondeu (sourcing, pipeline, wsi, etc.)
  session_id    → ID da sessão de chat para correlacionar com MemoryResolver

ATENÇÃO: nullable=True em todos — registros legados não têm esses campos.
"""
import sqlalchemy as sa
from alembic import op

revision = '052'
down_revision = '051'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("input_text", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("output_text", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("fairness_flags", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("agent_used", sa.String(255), nullable=True))
    op.add_column("audit_logs", sa.Column("session_id", sa.String(255), nullable=True))

    # Index para busca por session_id (debug de conversas específicas)
    op.create_index(
        "ix_audit_logs_session_id",
        "audit_logs",
        ["session_id"],
    )
    # Index composto para relatórios de compliance por empresa + data
    op.create_index(
        "ix_audit_logs_company_created",
        "audit_logs",
        ["company_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_company_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_session_id", table_name="audit_logs")
    op.drop_column("audit_logs", "session_id")
    op.drop_column("audit_logs", "agent_used")
    op.drop_column("audit_logs", "fairness_flags")
    op.drop_column("audit_logs", "output_text")
    op.drop_column("audit_logs", "input_text")
