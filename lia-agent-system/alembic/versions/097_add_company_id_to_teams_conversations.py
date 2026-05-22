"""P0-1 — Multi-tenant fix: add company_id to teams_conversations.

Revision ID: 097_add_company_id_to_teams_conversations
Revises: 096_align_self_scheduling_links_table
Create Date: 2026-04-26

Contexto
--------
Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-1) identificou
que `teams_orchestrator_bridge._resolve_company_id` lia
`TeamsConversation.company_id`, mas o modelo nao tinha essa coluna.
`getattr(row, "company_id", None)` mascarava o erro silently — toda mensagem
do Teams chegava no orchestrator com `company_id=None`, quebrando isolamento
multi-tenant downstream (RAG, fairness, audit, drift).

Esta revisao:
  1. Adiciona `company_id VARCHAR(255) NULL` em `teams_conversations` (mesmo
     pattern de `users.company_id`).
  2. Cria index para perf de queries multi-tenant lookup.
  3. Backfill best-effort via `user_aad_object_id` -> `users.azure_ad_object_id`
     -> `users.company_id`. Linhas orfaos (sem User correspondente) ficam NULL
     e serao resolvidas em runtime pelo bridge fallback (lookup direto).

Nao define NOT NULL nesta migration: registros pre-existentes podem nao ter
`aad_object_id` (registros antigos de dev) — bridge tolera None com warning.
Migration futura pode definir NOT NULL apos cleanup de orfaos.

Reversibilidade
---------------
`downgrade()` dropa o index e a coluna. Idempotente: usa IF EXISTS / IF NOT EXISTS.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "097_add_company_id_to_teams_conversations"
down_revision = "096_align_self_scheduling_links_table"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c)"
    ), {"t": table, "c": column}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "teams_conversations"):
        # Tabela ainda nao foi criada (provavel em DB virgem); a column sera
        # adicionada quando ORM criar a tabela. Nada a fazer.
        return

    # 1. Adiciona coluna company_id (idempotente)
    if not _column_exists(conn, "teams_conversations", "company_id"):
        op.execute(sa.text(
            "ALTER TABLE teams_conversations ADD COLUMN company_id VARCHAR(255)"
        ))

    # 2. Cria index (idempotente)
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_teams_conversations_company_id "
        "ON teams_conversations (company_id)"
    ))

    # 3. Backfill best-effort via aad_object_id -> users.company_id
    #    Cobre apenas linhas com user_aad_object_id setado e User correspondente.
    #    CANONICAL-FIX-EXEMPT: ambos azure_ad_object_id e user_aad_object_id sao VARCHAR (Azure AD GUIDs como string). Same-type join seguro sem cast.
    if _table_exists(conn, "users"):
        op.execute(sa.text("""
            UPDATE teams_conversations tc
            SET company_id = u.company_id
            FROM users u
            WHERE tc.company_id IS NULL
              AND tc.user_aad_object_id IS NOT NULL
              AND u.azure_ad_object_id = tc.user_aad_object_id
              AND u.company_id IS NOT NULL
        """))

    # 4. Comentario na coluna para futuros desenvolvedores
    op.execute(sa.text(
        "COMMENT ON COLUMN teams_conversations.company_id IS "
        "'Multi-tenant boundary populated from User.company_id via aad_object_id lookup. "
        "Fix P0-1 (auditoria 2026-04-26).'"
    ))


def downgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "teams_conversations"):
        return

    op.execute(sa.text(
        "DROP INDEX IF EXISTS ix_teams_conversations_company_id"
    ))

    if _column_exists(conn, "teams_conversations", "company_id"):
        op.execute(sa.text(
            "ALTER TABLE teams_conversations DROP COLUMN company_id"
        ))
