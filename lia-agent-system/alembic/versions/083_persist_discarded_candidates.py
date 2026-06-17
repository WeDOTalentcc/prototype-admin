"""Task #403 — persist discarded candidates alongside each search execution.

Revision ID: 083_persist_discarded_candidates
Revises: 082_add_candidate_company_id
Create Date: 2026-04-17

Contexto
--------
Antes desta migration, a lista de candidatos descartados pelo enriquecimento
(Apify) ficava apenas no estado React do frontend (``searchResults.filteredCandidates``).
Refresh ou re-execução da busca apagava o histórico — o usuário perdia os
perfis que foram filtrados por falta de email/telefone.

Esta migration adiciona a coluna ``discarded_candidates`` (JSONB) à tabela
``candidate_searches``. Cada linha de ``CandidateSearch`` (que já é o registro
de histórico de busca por usuário) passa a guardar a lista leve de descartados
serializada — dados suficientes para o frontend re-exibir e exportar.

Não há TTL dedicado: o registro vive sob o mesmo ciclo de vida do histórico
de buscas (``candidate_searches``), que já é a fonte canônica e cuja retenção
é gerenciada por políticas existentes.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "083_persist_discarded_candidates"
down_revision = "082_add_candidate_company_id"
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


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "candidate_searches"):
        return
    if _column_exists(conn, "candidate_searches", "discarded_candidates"):
        return
    op.add_column(
        "candidate_searches",
        sa.Column(
            "discarded_candidates",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "candidate_searches", "discarded_candidates"):
        op.drop_column("candidate_searches", "discarded_candidates")
