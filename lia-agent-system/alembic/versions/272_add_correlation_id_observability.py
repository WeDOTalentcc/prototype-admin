"""272 — add correlation_id to observability tables

Revision ID: 272_add_correlation_id_observability
Revises: 271_merge_all_orphaned_heads
Create Date: 2026-06-13

Sprint A — rastreabilidade cross-domain.
Adiciona correlation_id como coluna nullable indexed nas tabelas de audit/observability.
Permite rastrear um request HTTP end-to-end: handler -> audit_log -> agent_run -> eventos.
"""
from alembic import op
import sqlalchemy as sa

revision = "272_add_correlation_id_observability"
down_revision = "271_merge_all_orphaned_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # audit_logs — tabela principal de decisoes de IA
    op.execute("""
        ALTER TABLE audit_logs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_logs_correlation_id
        ON audit_logs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # agent_execution_logs — execucoes de agentes
    op.execute("""
        ALTER TABLE agent_execution_logs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_agent_exec_logs_correlation_id
        ON agent_execution_logs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # pool_agent_runs — execucoes de agentes de talent pool
    op.execute("""
        ALTER TABLE pool_agent_runs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_pool_agent_runs_correlation_id
        ON pool_agent_runs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # automation_execution_logs — automacoes disparadas por eventos
    op.execute("""
        ALTER TABLE automation_execution_logs
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_automation_exec_logs_correlation_id
        ON automation_execution_logs(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # fairness_policy_violations ja tem correlation_id (migration 266)
    # sox_audit_logs ja tem request_id (equivalente)
    # ai_inference_logs: sem escritores ativos confirmados — diferir


def downgrade() -> None:
    for table, idx in [
        ("audit_logs", "ix_audit_logs_correlation_id"),
        ("agent_execution_logs", "ix_agent_exec_logs_correlation_id"),
        ("pool_agent_runs", "ix_pool_agent_runs_correlation_id"),
        ("automation_execution_logs", "ix_automation_exec_logs_correlation_id"),
    ]:
        op.execute(f"DROP INDEX IF EXISTS {idx}")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS correlation_id")
