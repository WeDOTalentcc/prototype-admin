"""Task #366 — promote actor_user_id to a structured column on audit_logs.

Revision ID: 084_add_actor_user_id_to_audit_logs
Revises: 083_persist_discarded_candidates
Create Date: 2026-04-17

Contexto
--------
Antes desta migration, o id do usuario que disparou uma decisao auditavel
(por exemplo: o gestor editando uma politica de contratacao) era guardado
dentro do array de texto livre ``reasoning`` (ex.: ``"actor_user_id=user-42"``).
Isso impedia filtrar/relatorar entradas de auditoria por usuario sem fazer
parse do JSON.

Esta migration adiciona a coluna ``actor_user_id`` (String, indexada) na
tabela ``audit_logs`` para que callers como o ``PolicySetupAgent`` e o
endpoint de bulk_actions persistam o id em um campo estruturado.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "084_add_actor_user_id_to_audit_logs"
down_revision = "083_persist_discarded_candidates"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c)"
    ), {"t": table, "c": column}).scalar())


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _index_exists(conn, index_name: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes "
        "WHERE schemaname = 'public' AND indexname = :n)"
    ), {"n": index_name}).scalar())


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "audit_logs"):
        return
    if not _column_exists(conn, "audit_logs", "actor_user_id"):
        op.add_column(
            "audit_logs",
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        )
    if not _index_exists(conn, "ix_audit_logs_actor_user_id"):
        op.create_index(
            "ix_audit_logs_actor_user_id",
            "audit_logs",
            ["actor_user_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, "ix_audit_logs_actor_user_id"):
        op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    if _column_exists(conn, "audit_logs", "actor_user_id"):
        op.drop_column("audit_logs", "actor_user_id")
