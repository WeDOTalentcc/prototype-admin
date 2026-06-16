"""revert in_app_enabled (gap conceitual Workstream A)

Revision ID: 186_revert_in_app_enabled
Revises: 185_voice_wsi_results_canonical
Create Date: 2026-05-23

Decisão Paulo 2026-05-23: in_app_enabled era falso-positivo conceitual.
"Chat web" entre os 4 canais que Paulo quer = chat candidato público
(já existe em /api/v1/triagem/), NÃO chat lateral recrutador interno.

Reverter coluna custom_agents.in_app_enabled — não tem uso real.
voice_enabled, voip_enabled, whatsapp_enabled (canonical reais) mantidos.

ChannelType.IN_APP permanece no enum (pode ter outros usos via
MultiChannelService notifications) mas:
- Column in_app_enabled removida do custom_agents
- channel="in_app" literal removido do CustomAgentRuntime.execute
- REST PATCH /in_app/enabled endpoint removido
- UI toggle removido do AgentCard (3 toggles canonical: WhatsApp + Voice + VoIP)

Refs:
- AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md
- Migration 183 (que adicionou — agora revertida parcialmente, voip_enabled mantém)
"""
from alembic import op


revision = "186_revert_in_app_enabled"
down_revision = "185_voice_wsi_results_canonical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop in_app_enabled column — gap conceitual Workstream A."""
    op.execute("ALTER TABLE custom_agents DROP COLUMN IF EXISTS in_app_enabled")


def downgrade() -> None:
    """Re-add in_app_enabled (rollback path — para auditoria histórica)."""
    op.execute(
        "ALTER TABLE custom_agents "
        "ADD COLUMN IF NOT EXISTS in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE"
    )
