"""Workstream A 2026-05-23 — add triagem_invite_enabled flag to custom_agents

Revision ID: 188_custom_agent_triagem_invite_enabled
Revises: 187_triagem_resolve_tenant_secdef
Create Date: 2026-05-23

4º toggle per-agent — capability "convite triagem candidato" (default OFF).

Diferente dos canais diretos (voice/voip/whatsapp), triagem_invite é
CAPABILITY: quando ativo, agente pode CRIAR convites de triagem (token
único + URL pública /triagem/{token}) que serão entregues ao candidato
via email/WhatsApp. O canal real de delivery é determinado pelo campo
``invite_channel`` no payload, não pelo toggle.

Pattern espelha Sprint 3.7 W4-1 (voice_enabled) + T5a (whatsapp_enabled)
+ W-Channels-A 2026-05-23 (voip_enabled). Toggle visível ao cliente via
AgentCard; defesa em camadas:

1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explícito por endpoint.
3. CustomAgent.triagem_invite_enabled (per-agent toggle) → cliente UI.
4. TriagemSessionService.create_session → persistência canonical.

Default false — admin precisa habilitar explicitamente per-agent
(consistente com pattern audit canonical LGPD: nenhum side-effect
mass-deliverable sem opt-in explícito).

Tests: tests/contract/test_agent_studio_triagem_invite_endpoints.py
Refs: Workstream A T5 (whatsapp) + Sprint 3.7 W4-1 (voice template)
"""
from alembic import op


# revision identifiers, used by Alembic
revision = "188_custom_agent_triagem_invite_enabled"
down_revision = "187_triagem_resolve_tenant_secdef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE custom_agents
            ADD COLUMN IF NOT EXISTS triagem_invite_enabled BOOLEAN NOT NULL DEFAULT FALSE
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE custom_agents
            DROP COLUMN IF EXISTS triagem_invite_enabled
        """
    )
