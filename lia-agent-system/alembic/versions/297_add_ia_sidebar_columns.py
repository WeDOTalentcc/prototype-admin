"""Migration 297: add IA Sidebar session management columns to conversations.

Revision ID: 297_add_ia_sidebar_columns
Revises: 296_add_screening_config_defaults
Create Date: 2026-06-19

Adds:
  - is_pinned BOOL DEFAULT FALSE — recruiter can pin sessions
  - domain_tag VARCHAR(50) — auto-inferred category (Vagas/Candidatos/Relatórios/Configurações/Geral)
  - note TEXT NULLABLE — recruiter note shown as yellow callout in chat
  - unread_count INT DEFAULT 0 — badge count for Brain icon
  - composite index (company_id, user_id, is_active) for list query perf
  - also upgrades company_id index to composite (company_id, is_active)

company_id column was added nullable in migration 108. NOT NULL deferred until
all legacy anonymous conversations are confirmed backfilled (separate migration).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "297_add_ia_sidebar_columns"
down_revision = "296_add_screening_config_defaults"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def _index_exists(conn, index_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :n"
    ), {"n": index_name})
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()

    if not _column_exists(conn, "conversations", "is_pinned"):
        op.add_column("conversations", sa.Column("is_pinned", sa.Boolean(), server_default=sa.false(), nullable=False))

    if not _column_exists(conn, "conversations", "domain_tag"):
        op.add_column("conversations", sa.Column("domain_tag", sa.String(50), nullable=True))

    if not _column_exists(conn, "conversations", "note"):
        op.add_column("conversations", sa.Column("note", sa.Text(), nullable=True))

    if not _column_exists(conn, "conversations", "unread_count"):
        op.add_column("conversations", sa.Column("unread_count", sa.Integer(), server_default="0", nullable=False))

    # Composite index for IASidebar list query (company_id, user_id, is_active)
    if not _index_exists(conn, "ix_conversations_company_user_active"):
        op.create_index(
            "ix_conversations_company_user_active",
            "conversations",
            ["company_id", "user_id", "is_active"],
        )

    # Index for pinned sessions lookup
    if not _index_exists(conn, "ix_conversations_company_pinned"):
        op.create_index(
            "ix_conversations_company_pinned",
            "conversations",
            ["company_id", "is_pinned"],
            postgresql_where=sa.text("is_pinned = TRUE"),
        )


def downgrade():
    conn = op.get_bind()

    if _index_exists(conn, "ix_conversations_company_pinned"):
        op.drop_index("ix_conversations_company_pinned", "conversations")

    if _index_exists(conn, "ix_conversations_company_user_active"):
        op.drop_index("ix_conversations_company_user_active", "conversations")

    if _column_exists(conn, "conversations", "unread_count"):
        op.drop_column("conversations", "unread_count")

    if _column_exists(conn, "conversations", "note"):
        op.drop_column("conversations", "note")

    if _column_exists(conn, "conversations", "domain_tag"):
        op.drop_column("conversations", "domain_tag")

    if _column_exists(conn, "conversations", "is_pinned"):
        op.drop_column("conversations", "is_pinned")
