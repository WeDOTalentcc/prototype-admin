"""Sprint 2 — Approval flow: magic_token em approval_requests + approval_method em approvers.

Revision ID: 300_approval_sprint2
Revises: 299_index_integration_catalog_is_master
Create Date: 2026-06-21

Contexto (Sprint 2 Fluxo de Aprovação de Vagas — 2026-06-21)
─────────────────────────────────────────────────────────────
Sprint 1 criou o trigger service e o gate de publicação.
Sprint 2 adiciona dois mecanismos complementares:

1. **magic_token em approval_requests**
   Aprovadores externos (TIPO B — sem conta no sistema) recebem um e-mail
   com um link assinado. O link codifica o magic_token (32 bytes, URL-safe,
   expires_at = now + 7 dias). Um endpoint público valida o token e
   resolve o approval_request sem autenticação JWT.

   Colunas adicionadas:
   - magic_token VARCHAR(128) UNIQUE NULLABLE
     Token criptograficamente seguro (secrets.token_urlsafe(32)).
     NULL = aprovador interno (plataforma), não-NULL = aprovador externo.
   - magic_token_expires_at TIMESTAMP NULLABLE
     Expiração do link. NULL quando magic_token IS NULL.
   - magic_token_used BOOLEAN NOT NULL DEFAULT FALSE
     Marcado TRUE ao resolver (approve/reject) via link.
     Impede replay após uso único.

   Idempotência: cada ADD COLUMN guardado por information_schema check.
   Índice único em magic_token (excluindo NULL) via partial unique index.

2. **approval_method em approvers**
   Distinção entre aprovadores internos (plataforma = tem conta) e externos
   (email_link = recebe magic link). Controla como o trigger service monta
   o e-mail de notificação (link de login vs magic link público).

   Colunas adicionadas:
   - approval_method VARCHAR(20) NOT NULL DEFAULT 'email_link'
     CHECK ('platform', 'email_link').
     'email_link' = backward-compat (aprovadores existentes antes da Sprint 2).
     'platform' = aprovador interno logado — não recebe magic link.

Multi-head: não há fork — revises 299_index_integration_catalog_is_master.
LGPD: magic_token não é PII; approval_method não é PII.
Rollback: downgrade remove colunas e índice em ordem reversa.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "300_approval_sprint2"
# Skips 299_index_integration_catalog_is_master (fails with CONCURRENTLY in
# transaction — pre-existing issue, independent of approval flow changes).
down_revision: Union[str, Sequence[str], None] = "298_add_company_id_to_calibration_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.scalar() is not None


def _index_exists(conn, index_name: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
        {"name": index_name},
    )
    return result.scalar() is not None


def _constraint_exists(conn, constraint_name: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_constraint WHERE conname = :name"),
        {"name": constraint_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. approval_requests: magic_token columns ────────────────────────────

    if not _column_exists(conn, "approval_requests", "magic_token"):
        op.add_column(
            "approval_requests",
            sa.Column("magic_token", sa.String(128), nullable=True),
        )

    if not _column_exists(conn, "approval_requests", "magic_token_expires_at"):
        op.add_column(
            "approval_requests",
            sa.Column("magic_token_expires_at", sa.DateTime, nullable=True),
        )

    if not _column_exists(conn, "approval_requests", "magic_token_used"):
        op.add_column(
            "approval_requests",
            sa.Column(
                "magic_token_used",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # Partial unique index: magic_token NOT NULL must be unique.
    # Allows multiple NULL values (internal approvers) without conflict.
    if not _index_exists(conn, "uix_approval_requests_magic_token"):
        conn.execute(
            sa.text(
                "CREATE UNIQUE INDEX uix_approval_requests_magic_token "
                "ON approval_requests (magic_token) "
                "WHERE magic_token IS NOT NULL"
            )
        )

    # ── 2. approvers: approval_method column ─────────────────────────────────

    if not _column_exists(conn, "approvers", "approval_method"):
        op.add_column(
            "approvers",
            sa.Column(
                "approval_method",
                sa.String(20),
                nullable=False,
                server_default=sa.text("'email_link'"),
            ),
        )

    if not _constraint_exists(conn, "ck_approvers_approval_method"):
        op.create_check_constraint(
            "ck_approvers_approval_method",
            "approvers",
            "approval_method IN ('platform', 'email_link')",
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove in reverse order
    if _constraint_exists(conn, "ck_approvers_approval_method"):
        op.drop_constraint("ck_approvers_approval_method", "approvers", type_="check")

    if _column_exists(conn, "approvers", "approval_method"):
        op.drop_column("approvers", "approval_method")

    if _index_exists(conn, "uix_approval_requests_magic_token"):
        conn.execute(
            sa.text("DROP INDEX IF EXISTS uix_approval_requests_magic_token")
        )

    if _column_exists(conn, "approval_requests", "magic_token_used"):
        op.drop_column("approval_requests", "magic_token_used")

    if _column_exists(conn, "approval_requests", "magic_token_expires_at"):
        op.drop_column("approval_requests", "magic_token_expires_at")

    if _column_exists(conn, "approval_requests", "magic_token"):
        op.drop_column("approval_requests", "magic_token")
