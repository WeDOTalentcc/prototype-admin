"""280 — add correlation_id to LGPD-critical observability tables

Revision ID: 280_add_correlation_id_lgpd_tables
Revises: 279_add_stakeholders_to_job_vacancies
Create Date: 2026-06-13

Sprint G5 — completa rastreabilidade fim-a-fim LGPD Art.37V.
As 3 tabelas abaixo foram EXPLICITAMENTE DEFERIDAS na migration 272 por
ausência de escritores ativos confirmados à época. Sprint G5 confirma que:
  - ai_inference_logs: escrito via observability API + fairness_guard
  - data_access_logs: escrito via AuditService.log_data_access (SOXAuditLog wrapper)
  - automated_decision_explanations: escrito via ai_transparency API + wsi_questions

LGPD Art.37V — audit trail: request → LLM → decisão automatizada.
Permite correlacionar qualquer chamada LLM ou decisão de IA com o
request HTTP que a originou (via X-Correlation-ID / X-Request-ID).
"""
from alembic import op
import sqlalchemy as sa

revision = "280_add_correlation_id_lgpd_tables"
down_revision = "279_add_stakeholders_to_job_vacancies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- ai_inference_logs: logs de chamadas LLM (LGPD Art.37V explainability) --
    op.execute("""
        ALTER TABLE ai_inference_logs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ai_inference_logs_correlation_id
        ON ai_inference_logs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)
    # LGPD Art.37V: rastreabilidade fim-a-fim request → LLM → decisão

    # -- data_access_logs: acesso a dados de candidatos (LGPD Art.37V) --
    op.execute("""
        ALTER TABLE data_access_logs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_data_access_logs_correlation_id
        ON data_access_logs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # -- automated_decision_explanations: decisões automáticas Art.20 LGPD --
    op.execute("""
        ALTER TABLE automated_decision_explanations
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_automated_decision_expl_correlation_id
        ON automated_decision_explanations(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)


def downgrade() -> None:
    for table, idx in [
        ("ai_inference_logs", "ix_ai_inference_logs_correlation_id"),
        ("data_access_logs", "ix_data_access_logs_correlation_id"),
        ("automated_decision_explanations", "ix_automated_decision_expl_correlation_id"),
    ]:
        op.execute(f"DROP INDEX IF EXISTS {idx}")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS correlation_id")
