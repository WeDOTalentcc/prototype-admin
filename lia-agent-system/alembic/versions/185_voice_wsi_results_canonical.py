"""P0 production fix · voice_wsi_results canonical table

Revision ID: 185_voice_wsi_results_canonical
Revises: 184_learning_signals
Create Date: 2026-05-23

Audit 2026-05-23 (MISSING_TABLES_INVESTIGATION_2026-05-23.md) descobriu que
5 consumers fazem INSERT/DELETE em ``voice_wsi_results`` mas a tabela NUNCA
foi criada. ``_persist_wsi_result`` em ``app/services/voice/wsi_pipeline.py``
tinha try/except mudo (REGRA 4 anti-pattern) que escondia o gap. Scores WSI
Voice silenciosamente perdidos em produção desde release. Webhook OpenMic
respondia 200 OK enquanto persistência falhava.

Consumers (canonical):
- INSERT/UPSERT: ``app/services/voice/wsi_pipeline.py:144`` (hot path,
  OpenMic webhook) — ON CONFLICT (call_id) DO UPDATE.
- DELETE/SELECT: ``app/jobs/tasks/voice_retention.py:214,228`` (cron LGPD
  Art. 16 retention 365d, deleta where created_at < cutoff).
- DELETE: ``app/domains/lgpd/services/lgpd_cleanup_service.py:456,471``
  (cascade LGPD Art. 18 erasure por candidate_id).

Schema canonical inferido do INSERT real em wsi_pipeline.py:144-170:
- candidate_id, job_id, company_id, call_id, source
- final_score, classification, bloom_level, context_score
- transcript_length, created_at, updated_at

Type alignment com sibling ``voice_screening_calls``:
- ``call_id`` VARCHAR (não UUID — OpenMic emite call_id como string)
- ``candidate_id`` VARCHAR (alinha com voice_screening_calls.candidate_id)
- ``company_id``, ``job_id`` VARCHAR (alinha com pattern existing voice_*)
- ``created_at``, ``updated_at`` TIMESTAMP WITHOUT TIME ZONE (alinha sibling)

Constraints:
- ``call_id`` UNIQUE (necessário para ON CONFLICT (call_id) em wsi_pipeline).
- ``company_id`` NOT NULL (multi-tenancy fail-closed canonical).
- ``candidate_id`` nullable (defense para casos onde candidato é deletado mas
  histórico de scoring permanece anonimizado).

Indexes:
- ``ix_voice_wsi_results_company_id`` — multi-tenant query path.
- ``ix_voice_wsi_results_candidate_id`` — LGPD Art. 18 erasure cascade.
- ``ix_voice_wsi_results_job_id`` — analytics per-vaga.
- ``ix_voice_wsi_results_created_at`` — retention 365d cron range scan.
- UNIQUE on ``call_id`` — UPSERT path.

RLS: NÃO habilitado (alinha com sibling voice_screening_calls que também
não tem RLS — multi-tenancy enforced via app layer ContextVar canonical).
Mudar isso requer migration coordenada das outras voice_* tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "185_voice_wsi_results_canonical"
down_revision = "184_learning_signals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "voice_wsi_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Multi-tenancy fail-closed canonical
        sa.Column("company_id", sa.String(64), nullable=False),
        # FK alignment com voice_screening_calls (candidate_id varchar)
        sa.Column("candidate_id", sa.String(255), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True),
        # OpenMic call_id is a string identifier
        sa.Column("call_id", sa.String(255), nullable=False, unique=True),
        # Source canonical: "openmic_voice" (extensible)
        sa.Column("source", sa.String(50), nullable=False, server_default="openmic_voice"),
        # WSI scoring outputs (canonical de wsi_pipeline.py)
        sa.Column("final_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("classification", sa.String(50), nullable=False, server_default="regular"),
        sa.Column("bloom_level", sa.Integer, nullable=False, server_default="0"),
        sa.Column("context_score", sa.Float, nullable=False, server_default="0.0"),
        # Telemetria
        sa.Column("transcript_length", sa.Integer, nullable=True),
        # Timestamps (alinha com sibling voice_screening_calls = sem tz)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=True,
        ),
    )

    # Indexes canonical
    op.create_index(
        "ix_voice_wsi_results_company_id",
        "voice_wsi_results",
        ["company_id"],
    )
    op.create_index(
        "ix_voice_wsi_results_candidate_id",
        "voice_wsi_results",
        ["candidate_id"],
    )
    op.create_index(
        "ix_voice_wsi_results_job_id",
        "voice_wsi_results",
        ["job_id"],
    )
    op.create_index(
        "ix_voice_wsi_results_created_at",
        "voice_wsi_results",
        ["created_at"],
    )


def downgrade():
    op.drop_index("ix_voice_wsi_results_created_at", table_name="voice_wsi_results")
    op.drop_index("ix_voice_wsi_results_job_id", table_name="voice_wsi_results")
    op.drop_index("ix_voice_wsi_results_candidate_id", table_name="voice_wsi_results")
    op.drop_index("ix_voice_wsi_results_company_id", table_name="voice_wsi_results")
    op.drop_table("voice_wsi_results")
