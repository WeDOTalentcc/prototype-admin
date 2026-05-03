"""Cleanup orphaned teams_conversations rows with NULL company_id

Revision ID: 113
Revises: 112
Create Date: 2026-05-03

UC-P2-34 — Migration 097 added company_id to teams_conversations with a
best-effort backfill via user_aad_object_id -> users.azure_ad_object_id.
Rows without a matching User were left NULL intentionally (bridge fallback
tolerates None with a warning).

This follow-up migration:
  1. Second-pass backfill via users.id direct FK (covers rows where
     user_aad_object_id was missing but user_id FK exists).
  2. Logs a WARNING line per orphan that remains NULL so a DBA can review
     before a future NOT NULL constraint is added.

Downgrade: no-op (backfill data is correct; log lines are append-only).
"""
from alembic import op
import sqlalchemy as sa
import logging

logger = logging.getLogger("alembic.env")

revision = "113"
down_revision = "112"
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


def upgrade():
    conn = op.get_bind()

    if not _table_exists(conn, "teams_conversations"):
        logger.info("[113] teams_conversations table not found — skipping")
        return

    if not _column_exists(conn, "teams_conversations", "company_id"):
        logger.warning(
            "[113] company_id column missing from teams_conversations "
            "— run migration 097 first"
        )
        return

    # 1. Second-pass backfill: try to resolve via user_id -> users.id
    #    (covers rows with a user FK but no aad_object_id)
    if _table_exists(conn, "users") and _column_exists(conn, "teams_conversations", "user_id"):
        result = conn.execute(sa.text("""
            UPDATE teams_conversations tc
            SET company_id = u.company_id
            FROM users u
            WHERE tc.company_id IS NULL
              AND tc.user_id IS NOT NULL
              AND tc.user_id::text = u.id::text
              AND u.company_id IS NOT NULL
        """))
        logger.info("[113] Second-pass backfill updated %d rows via user_id FK", result.rowcount)

    # 2. Count remaining orphans and emit WARNING per row so a DBA can act.
    orphan_rows = conn.execute(sa.text(
        "SELECT id FROM teams_conversations WHERE company_id IS NULL"
    )).fetchall()

    if orphan_rows:
        logger.warning(
            "[113] %d teams_conversations rows remain with company_id IS NULL "
            "after second-pass backfill. IDs: %s — "
            "review before adding NOT NULL constraint.",
            len(orphan_rows),
            [str(r[0]) for r in orphan_rows],
        )
    else:
        logger.info("[113] No orphan teams_conversations rows remain.")


def downgrade():
    pass  # Backfill is correct to keep; no structural change to reverse
