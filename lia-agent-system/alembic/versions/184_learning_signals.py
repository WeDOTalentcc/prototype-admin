"""W3-021 · learning_signals table (LearningSignalRepository persistence)

Revision ID: 184_learning_signals
Revises: 183_custom_agent_channel_columns
Create Date: 2026-05-23

W3-021 do MASTER_PLAN.md de remediação enterprise.
Tests: tests/unit/test_w3021_learning_signal_repository.py
Sensor: scripts/check_learning_signal_wired.py

Cria tabela `learning_signals` para persistir corrections capturadas via
`CorrectionCaptureService.record_correction`. Anteriormente os signals
eram apenas logged (TODO ml-team, ISSUE-P3-05 deferred). Agora persistem
em DB para consumo posterior por `FewShotEvolutionService`.

Multi-tenancy fail-closed via `company_id NOT NULL`. RLS aplicado em
migration separada (alinhado pattern 123_rls_t5_learning_ml).

Schema:
- id UUID PK
- company_id VARCHAR(64) NOT NULL — tenant isolation
- user_id VARCHAR(64) NOT NULL — quem deu o correction
- conversation_id VARCHAR(64) — sessão LIA chat (opcional)
- domain VARCHAR(100) — automation, cv_screening, etc (mapeia pra YAML)
- original_response TEXT NOT NULL — resposta IA antes
- corrected_response TEXT NOT NULL — resposta humano sugeriu
- feedback_type VARCHAR(40) — "correction" | "thumbs_down" | "explicit_correction"
- confidence_at_generation REAL — score IA antes do correction
- metadata JSONB — extensible (intent, model_used, etc)
- consumed_for_fewshot BOOLEAN default false — flag fanout pra evolution service
- consumed_at TIMESTAMPTZ — quando virou few-shot
- created_at TIMESTAMPTZ default now()

Indexes:
- (company_id, created_at DESC) — leitura per-tenant recent
- (domain, consumed_for_fewshot) — fanout para evolution service
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "184_learning_signals"
down_revision = "183_custom_agent_channel_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("conversation_id", sa.String(64), nullable=True),
        sa.Column("domain", sa.String(100), nullable=True),
        sa.Column("original_response", sa.Text, nullable=False),
        sa.Column("corrected_response", sa.Text, nullable=False),
        sa.Column("feedback_type", sa.String(40), nullable=False),
        sa.Column("confidence_at_generation", sa.Float, nullable=True),
        sa.Column("signal_metadata", postgresql.JSONB, nullable=True),
        sa.Column("consumed_for_fewshot", sa.Boolean, nullable=False,
                  server_default=sa.false()),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_learning_signals_company_created",
        "learning_signals",
        ["company_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_learning_signals_domain_consumed",
        "learning_signals",
        ["domain", "consumed_for_fewshot"],
    )


def downgrade():
    op.drop_index("ix_learning_signals_domain_consumed", table_name="learning_signals")
    op.drop_index("ix_learning_signals_company_created", table_name="learning_signals")
    op.drop_table("learning_signals")
