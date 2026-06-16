"""Sprint 7B-3a Part 1.5 v2 — relaxa sourcing_agent_signals.agent_id NOT NULL → NULLABLE.

Decisão Paulo 2026-05-26 (Opção 2): canonical-only fail-closed (REGRA 4 single source).
- Signals NOVOS escritos pelo orchestrator (Part 2 full) usam custom_agent_id.
- agent_id permanece pra signals históricos pré-Sprint 7A (preserva calibração).
- Tabela vazia em dev — risco zero.

Sprint 8 prevista pra DROP sourcing_agents table inteira (e migration adicional
que vai DROP agent_id column).

Refs:
- AGENT_STUDIO_GAP_ANALYSIS_2026-05-26.md decisões #2 (write policy canonical-only)
- Sprint 7A migration 202 (criou custom_agent_id + assignment_id columns).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "209"
down_revision = "208"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sourcing_agent_signals",
        "agent_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )


def downgrade():
    # Rollback: re-add NOT NULL. Pode falhar se houver rows com agent_id NULL.
    # Em dev tabela está vazia (validado 2026-05-26 Fase A), rollback safe.
    op.alter_column(
        "sourcing_agent_signals",
        "agent_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
