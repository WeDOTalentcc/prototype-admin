"""Sprint 3.7 W4-1 — add voice_enabled flag to custom_agents

Revision ID: 177_custom_agent_voice_enabled
Revises: 176_audit_hash_chain
Create Date: 2026-05-22

Sprint 3.7 W4-1: Per-agent voice flag (default OFF).

Adiciona coluna ``voice_enabled BOOLEAN NOT NULL DEFAULT FALSE`` à tabela
``custom_agents`` para permitir ao cliente final habilitar/desabilitar voz
em cada agente custom do Agent Studio.

Defense-in-depth: este flag soma com o feature flag global
``voice_screening_v2_enabled`` (per-tenant) — ambos precisam estar ON
para que ``CustomAgentRuntime._invoke_voice`` execute. Toggle visível ao
cliente é o ``voice_enabled``; o feature flag continua sob controle WeDOTalent.

Tests: tests/contract/test_agent_studio_voice_endpoints.py
Refs: Sprint 3.5 (channel='voice') + Sprint 3.6 (StudioVoicePlugin)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "177_custom_agent_voice_enabled"
down_revision = "176_audit_hash_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "custom_agents",
        sa.Column(
            "voice_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("custom_agents", "voice_enabled")
