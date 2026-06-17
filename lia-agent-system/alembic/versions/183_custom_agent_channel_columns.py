"""W-Channels-A · custom_agent voip_enabled + in_app_enabled (4-channel canonical)

Revision ID: 183_custom_agent_channel_columns
Revises: 182_deepseek_catalog
Create Date: 2026-05-23

Workstream A — Coerência canais Opção B (decisão Paulo 2026-05-23):

Antes desta migration, custom_agents possuía apenas 2 toggles per-canal:
- voice_enabled (177): cobria PSTN E VoIP indistintamente (acoplamento).
- whatsapp_enabled (179): canal WhatsApp.

Mental model Paulo é de 4 canais independentes:
1. Chat web interno (lateral) — recém renomeado in_app
2. WhatsApp                    — whatsapp_enabled (já existia)
3. Ligação telefônica PSTN     — voice_enabled (agora APENAS PSTN)
4. Voz no navegador (VoIP)     — voip_enabled (NOVO)

Esta migration ADICIONA dois colunas:
- ``voip_enabled`` (default FALSE) — gate canonical pra Twilio VoIP SDK +
  Gemini Live. Não toca voice_enabled existente (forward-compat).
- ``in_app_enabled`` (default TRUE) — chat lateral interno; default true
  preserva comportamento atual (todos os agentes podem ser invocados via
  chat lateral salvo opt-out explícito).

Backward compat:
- voice_enabled mantém valores existentes (não mexemos). Semântica agora
  significa "PSTN only" — quem queria PSTN+VoIP precisa habilitar ambos.
- Sessões/runs já criados continuam funcionando. Runtime trata flags
  ausentes via getattr(default).

Idempotente: ADD COLUMN IF NOT EXISTS / DROP COLUMN IF EXISTS.

Tests: tests/contract/test_channel_coherence_4_channels.py
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "183_custom_agent_channel_columns"
down_revision = "182_deepseek_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE custom_agents "
        "ADD COLUMN IF NOT EXISTS voip_enabled BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE custom_agents "
        "ADD COLUMN IF NOT EXISTS in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE custom_agents DROP COLUMN IF EXISTS voip_enabled")
    op.execute("ALTER TABLE custom_agents DROP COLUMN IF EXISTS in_app_enabled")
