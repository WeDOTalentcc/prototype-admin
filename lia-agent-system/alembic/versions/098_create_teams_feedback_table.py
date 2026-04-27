"""P1-7 — Create teams_feedback table for Teams Adaptive Card feedback loop.

Revision ID: 098_create_teams_feedback_table
Revises: 097_add_company_id_to_teams_conversations
Create Date: 2026-04-27

Contexto
--------
Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, P1-7) identificou que
o endpoint /api/v1/teams/feedback apenas logava 👍/👎 dos cards
(comentário literal `# TODO: persist to feedback table for LIA training`).
Sem persistência: sem feedback loop de ML, sem dashboard de qualidade,
sem rastreamento de UX.

Esta revisão cria `teams_feedback` (espelhando o modelo TeamsFeedback em
lia_models.teams), com indexes para queries comuns (per-user, per-company,
per-type, time-windowed).

Reversibilidade
---------------
`downgrade()` dropa a tabela. Idempotente via IF EXISTS.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "098_create_teams_feedback_table"
down_revision = "097_add_company_id_to_teams_conversations"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def upgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "teams_feedback"):
        return

    op.execute(sa.text("""
        CREATE TABLE teams_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            feedback_type VARCHAR(50) NOT NULL,
            feedback_text TEXT,
            user_id VARCHAR(255) NOT NULL,
            company_id VARCHAR(255),
            card_context JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
    # Indexes for typical query patterns
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_teams_feedback_type "
        "ON teams_feedback (feedback_type)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_teams_feedback_user "
        "ON teams_feedback (user_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_teams_feedback_company "
        "ON teams_feedback (company_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_teams_feedback_created_at "
        "ON teams_feedback (created_at)"
    ))
    op.execute(sa.text(
        "COMMENT ON TABLE teams_feedback IS "
        "'User feedback (thumbs up/down) on Teams Adaptive Cards. P1-7 fix.'"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "teams_feedback"):
        op.execute(sa.text("DROP INDEX IF EXISTS ix_teams_feedback_created_at"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_teams_feedback_company"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_teams_feedback_user"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_teams_feedback_type"))
        op.execute(sa.text("DROP TABLE teams_feedback"))
