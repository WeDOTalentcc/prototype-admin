"""Task #511 — addendum: FK wsi_responses.session_id -> wsi_sessions.id.

Revision ID: 092_wsi_responses_session_fk
Revises: 091_add_wsi_responses_audit_trail
Create Date: 2026-04-18

Contexto
--------
Code review da Task #511 apontou que `wsi_responses.session_id` ficou como
`VARCHAR(255)` sem FK para `wsi_sessions.id` — quebra a integridade da trilha
de auditoria (linhas órfãs após delete da sessão; tipo divergente do parent).

Esta revisão:
  1. Converte `wsi_responses.session_id` para UUID (cast seguro pois UUIDs já
     são gravados como strings válidas).
  2. Adiciona FK `wsi_responses.session_id -> wsi_sessions.id` ON DELETE CASCADE.

Reversibilidade
---------------
`downgrade()` remove a FK e converte de volta para VARCHAR(255). Idempotente.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "092_wsi_responses_session_fk"
down_revision = "091_add_wsi_responses_audit_trail"
branch_labels = None
depends_on = None


_FK_NAME = "fk_wsi_responses_session"


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _constraint_exists(conn, name: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_schema = 'public' AND constraint_name = :n)"
    ), {"n": name}).scalar())


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "wsi_responses"):
        return

    # 0. Round 3 — preflight: detecta valores não-UUID antes do CAST.
    # Sem isso, o ALTER TABLE abaixo abortaria com erro genérico do Postgres
    # em deploy. Falhamos cedo com mensagem acionável.
    invalid = conn.execute(sa.text(
        "SELECT COUNT(*) FROM wsi_responses "
        "WHERE session_id !~ "
        "'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        "[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'"
    )).scalar()
    if invalid and int(invalid) > 0:
        raise RuntimeError(
            f"Migration 092 abortada: {invalid} linha(s) em wsi_responses "
            "com session_id inválido (não-UUID). Limpe ou normalize antes "
            "de aplicar (ver runbook EU-AI-Act #511)."
        )

    # 1. Cast VARCHAR -> UUID. USING garante que a conversão use o valor existente.
    op.execute(sa.text(
        "ALTER TABLE wsi_responses "
        "ALTER COLUMN session_id TYPE UUID USING session_id::uuid"
    ))

    # 2. FK com ON DELETE CASCADE (audit trail acompanha a sessão).
    if not _constraint_exists(conn, _FK_NAME):
        op.execute(sa.text(
            f"ALTER TABLE wsi_responses "
            f"ADD CONSTRAINT {_FK_NAME} "
            f"FOREIGN KEY (session_id) REFERENCES wsi_sessions(id) ON DELETE CASCADE"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "wsi_responses"):
        return

    if _constraint_exists(conn, _FK_NAME):
        op.execute(sa.text(
            f"ALTER TABLE wsi_responses DROP CONSTRAINT {_FK_NAME}"
        ))

    op.execute(sa.text(
        "ALTER TABLE wsi_responses "
        "ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text"
    ))
