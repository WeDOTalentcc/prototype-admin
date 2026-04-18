"""Task #446 — speed up ATS job re-syncs with a functional index.

Revision ID: 087_index_job_vacancies_external_system_id
Revises: 086_add_job_readiness_columns
Create Date: 2026-04-18

Contexto
--------
``ATSSyncService.upsert_job_vacancy`` precisava encontrar a JobVacancy
correspondente a um ``(company_id, source_system, external_system_id)``
em cada job retornado pelo ATS. Antes desta migration o lookup carregava
toda a janela ``(company_id, source_system)`` em memória e filtrava o
``external_system_id`` em Python — O(N*M) por re-sync.

Esta migration adiciona um índice B-tree funcional sobre

    (company_id, source_system, (additional_data->>'external_system_id'))

para que o filtro SQL (agora usado por ``upsert_job_vacancy``) seja O(1)
por upsert. O índice é parcial (apenas linhas com ``source_system NOT NULL``
e ``additional_data ? 'external_system_id'``) para manter o tamanho enxuto:
linhas criadas manualmente na LIA não precisam dele.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "088_index_job_vacancies_external_system_id"
down_revision = "087_backfill_actor_user_id_audit_logs"
branch_labels = None
depends_on = None


INDEX_NAME = "ix_job_vacancies_company_source_external_id"


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
    if not _table_exists(conn, "job_vacancies"):
        return

    if not _index_exists(conn, INDEX_NAME):
        op.execute(sa.text(
            f"""
            CREATE INDEX {INDEX_NAME}
                ON job_vacancies (
                    company_id,
                    source_system,
                    ((additional_data->>'external_system_id'))
                )
             WHERE source_system IS NOT NULL
               AND additional_data IS NOT NULL
               AND (additional_data->>'external_system_id') IS NOT NULL
            """
        ))


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, INDEX_NAME):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
