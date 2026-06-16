"""Task #419 — backfill actor_user_id on historical audit_logs rows.

Revision ID: 087_backfill_actor_user_id_audit_logs
Revises: 086_add_job_readiness_columns
Create Date: 2026-04-18

Contexto
--------
Migration 084 adicionou a coluna estruturada ``actor_user_id`` em
``audit_logs``. Linhas novas (Policy edits, bulk_actions, chat) ja gravam
o id no campo dedicado, porem as linhas historicas continuam carregando
o id apenas dentro do array de texto livre ``reasoning`` no formato
``"actor_user_id=user-42"``. Enquanto esses registros nao forem migrados,
relatorios de admin filtrados por usuario (``GET /admin/audit/decisions``)
deixam de fora as decisoes antigas.

Estrategia
----------
1. Para cada linha com ``actor_user_id IS NULL`` cujo ``reasoning`` contem
   um elemento prefixado por ``actor_user_id=``, extrair o valor com regex
   e gravar no novo campo.
2. ``reasoning`` e armazenado como JSON. Convertemos para ``jsonb`` so
   para usar ``jsonb_array_elements_text``; rows cujo JSON nao seja um
   array (ou seja NULL) sao tratadas como ``'[]'::jsonb`` via ``CASE``
   *dentro* da chamada lateral, evitando o erro
   ``cannot extract elements from a scalar/object`` que aconteceria se
   o filtro fosse colocado apenas no ``WHERE`` (a expansao lateral roda
   antes do filtro).
3. A migration e idempotente: rodar de novo nao altera linhas que ja
   tem ``actor_user_id`` preenchido (filtro ``actor_user_id IS NULL``)
   e nao quebra se a coluna ou tabela nao existirem ainda.
4. Sem ``downgrade`` destrutivo: o reverse limpa apenas linhas cujo
   reasoning ainda contem o token ``actor_user_id=`` (sinalizando que
   o valor veio do backfill), mantendo intactas as linhas onde o caller
   ja gravou o id de forma estruturada desde o inicio.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "087_backfill_actor_user_id_audit_logs"
down_revision = "086_add_job_readiness_columns"
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


_BACKFILL_SQL = sa.text("""
    UPDATE audit_logs AS a
    SET actor_user_id = sub.uid
    FROM (
        SELECT
            al.id AS row_id,
            (regexp_match(elem, '^actor_user_id=(.+)$'))[1] AS uid
        FROM audit_logs AS al
        CROSS JOIN LATERAL jsonb_array_elements_text(
            CASE
                WHEN al.reasoning IS NOT NULL
                 AND jsonb_typeof(al.reasoning::jsonb) = 'array'
                THEN al.reasoning::jsonb
                ELSE '[]'::jsonb
            END
        ) AS elem
        WHERE al.actor_user_id IS NULL
          AND elem LIKE 'actor_user_id=%'
    ) AS sub
    WHERE a.id = sub.row_id
      AND a.actor_user_id IS NULL
      AND sub.uid IS NOT NULL
      AND length(trim(sub.uid)) > 0
""")


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "audit_logs"):
        return
    if not _column_exists(conn, "audit_logs", "actor_user_id"):
        # Migration 084 nao rodou ainda — nada a fazer.
        return
    if not _column_exists(conn, "audit_logs", "reasoning"):
        return

    result = conn.execute(_BACKFILL_SQL)
    if result.rowcount:
        print(
            f"[087] audit_logs.actor_user_id: backfilled {result.rowcount} "
            f"rows from reasoning[]"
        )


def downgrade() -> None:
    # Limpa apenas linhas cujo reasoning ainda carrega o token legado, ou
    # seja, aquelas que receberam o valor via backfill. Linhas em que o
    # caller ja persistiu actor_user_id de forma estruturada permanecem
    # intactas.
    conn = op.get_bind()
    if not _table_exists(conn, "audit_logs"):
        return
    if not _column_exists(conn, "audit_logs", "actor_user_id"):
        return

    # Tighter than "any row whose reasoning still mentions actor_user_id=":
    # we only null the column when the structured value actually equals the
    # token in reasoning. That way a caller that legitimately persists both
    # the structured field and the legacy text token (post-084) is not
    # accidentally cleared on downgrade.
    conn.execute(sa.text("""
        UPDATE audit_logs AS a
        SET actor_user_id = NULL
        WHERE a.actor_user_id IS NOT NULL
          AND a.reasoning IS NOT NULL
          AND jsonb_typeof(a.reasoning::jsonb) = 'array'
          AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements_text(a.reasoning::jsonb) AS elem
              WHERE elem = 'actor_user_id=' || a.actor_user_id
          )
    """))
