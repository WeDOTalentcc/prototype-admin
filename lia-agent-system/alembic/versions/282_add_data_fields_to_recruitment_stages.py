"""282 — add data_fields to recruitment_stages

Revision ID: 281_add_data_fields_to_recruitment_stages
Revises: 280_add_correlation_id_lgpd_tables
Create Date: 2026-06-13

Adiciona coluna JSONB `data_fields` à tabela `recruitment_stages`.

`data_fields` armazena a lista de campos de coleta de dados que devem ser
solicitados ao candidato ao entrar neste estágio do pipeline.

Formato canônico de cada item (StageDataField no FE):
  {
    "id": "<uuid-ou-slug>",
    "displayName": "<nome exibido ao candidato>",
    "category": "basic" | "document" | "financial" | "admissional",
    "required": true | false,
    "auto_collect": true | false
  }

Default: lista vazia [] — sem coleta automática. Estágios existentes não são
afetados; o FE lê `data_fields ?? []` e mostra vazio quando não configurado.

Consumidor principal: JobProcessStageCard.tsx (exibição read-only no editor de
processo seletivo da vaga) — a coleta efetiva via DataRequestVoiceService /
DataRequestWhatsAppService é o próximo passo (Fase 4 data_fields).
"""
from alembic import op
import sqlalchemy as sa

revision = "282_add_data_fields_to_recruitment_stages"
down_revision = "281_merge_tier_policies_branch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE recruitment_stages
        ADD COLUMN IF NOT EXISTS data_fields JSONB NOT NULL DEFAULT '[]'::jsonb
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE recruitment_stages
        DROP COLUMN IF EXISTS data_fields
    """)
