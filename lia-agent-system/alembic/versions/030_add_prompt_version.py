"""Add prompt_version column to conversation_logs table.

Revision ID: 030_add_prompt_version
Revises: 029_add_conversation_title_index
Create Date: 2026-03-08

Sprint B — PromptVersionRegistry (André P3/R3):
Adiciona coluna prompt_version VARCHAR(16) NULL na tabela conversation_logs
para auditoria do hash SHA-256 (12 chars prefix) do system prompt utilizado
em cada interação.

Permite:
- Rastrear qual versão de prompt gerou cada resposta
- Detectar regressões ao comparar métricas por versão de prompt
- Conformidade SOX/ISO 27001 (rastreabilidade de decisões de IA)
"""
from alembic import op
import sqlalchemy as sa


revision = "030_add_prompt_version"
down_revision = "029_add_conversation_title_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_logs",
        sa.Column("prompt_version", sa.String(16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_logs", "prompt_version")
