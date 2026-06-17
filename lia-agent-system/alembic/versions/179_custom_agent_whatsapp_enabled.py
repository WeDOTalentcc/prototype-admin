"""T5a UX Transformação 5 — add whatsapp_enabled flag to custom_agents

Revision ID: 179_custom_agent_whatsapp_enabled
Revises: 178_tenant_llm_config_region
Create Date: 2026-05-23

T5a: Per-agent WhatsApp flag (default OFF). Espelha o pattern de
voice_enabled (177_custom_agent_voice_enabled) — cliente controla via UI
no AgentCard se este agente custom pode operar via canal WhatsApp como
canal de execução (não apenas como canal de notificação outbound).

Defense-in-depth:
1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explícito por endpoint.
3. ``CustomAgent.whatsapp_enabled`` (per-agent toggle) — cliente UI flag.
4. ``WhatsAppProviderFactory.get_provider`` → Meta ou Twilio configurados.
5. ``CustomAgentRuntime._invoke_whatsapp`` → gates internos (PII, fairness).

Tests: tests/contract/test_whatsapp_agent_plugin.py
       tests/contract/test_agent_studio_whatsapp_endpoints.py
Refs: T5a (UX_AUDIT_ESTUDIO_AGENTES_2026-05-21.md §4.5)
      Sprint 3.5 (channel='whatsapp') + Sprint 3.7 (voice_enabled pattern)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "179_custom_agent_whatsapp_enabled"
down_revision = "178_tenant_llm_config_region"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent (espelha pattern 177): IF NOT EXISTS para resiliência em
    # casos de re-run + bypass psycopg2 sync que possa ter sido feito antes
    # do alembic conseguir rodar (audit harness pattern).
    op.execute(
        """
        ALTER TABLE custom_agents
            ADD COLUMN IF NOT EXISTS whatsapp_enabled BOOLEAN NOT NULL DEFAULT FALSE
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE custom_agents
            DROP COLUMN IF EXISTS whatsapp_enabled
        """
    )
