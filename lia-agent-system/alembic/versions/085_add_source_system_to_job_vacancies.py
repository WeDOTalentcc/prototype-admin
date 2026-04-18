"""Task #435 — add a dedicated source_system column to job_vacancies.

Revision ID: 085_add_source_system_to_job_vacancies
Revises: 084_add_actor_user_id_to_audit_logs
Create Date: 2026-04-18

Contexto
--------
Antes desta migration, "esta vaga veio de um ATS externo?" era inferido por
heuristica em ``additional_data`` (chaves ``imported_from_ats``, ``source``,
``external_system_id``...). Conforme novas integracoes ATS sao adicionadas,
essa inferencia fica fragil e o badge "ATS" no painel de Vagas pode ficar
inconsistente.

Esta migration adiciona uma coluna estruturada ``source_system`` (String(50),
indexada, nullable) em ``job_vacancies`` e faz backfill com base na
heuristica atual:

- linha com ``additional_data.source`` em {gupy, pandape, merge, kenoby,
  solides, abler, greenhouse} -> usa o slug correspondente.
- linha com ``additional_data.imported_from_ats == true`` ou
  ``external_system_id``/``ats_external_id`` preenchidos sem slug conhecido
  -> usa ``ats_other``.
- linha com ``additional_data.source == 'fast_track'`` -> ``lia_fast_track``.
- demais linhas permanecem ``NULL`` (legado / criado manualmente; a
  detecao no backend continua caindo no fallback heuristico).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "085_add_source_system_to_job_vacancies"
down_revision = "084_add_actor_user_id_to_audit_logs"
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
    if not _table_exists(conn, "job_vacancies"):
        return

    if not _column_exists(conn, "job_vacancies", "source_system"):
        op.add_column(
            "job_vacancies",
            sa.Column("source_system", sa.String(length=50), nullable=True),
        )

    if not _index_exists(conn, "ix_job_vacancies_source_system"):
        op.create_index(
            "ix_job_vacancies_source_system",
            "job_vacancies",
            ["source_system"],
        )

    # Backfill from additional_data heuristic. Only touch rows where
    # source_system is NULL so re-running the migration is a no-op.
    # 1) Known ATS slug embedded in additional_data.source/origin/import_source.
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET source_system = LOWER(
                   COALESCE(
                       additional_data->>'source',
                       additional_data->>'origin',
                       additional_data->>'import_source'
                   )
               )
         WHERE source_system IS NULL
           AND additional_data IS NOT NULL
           AND LOWER(
                   COALESCE(
                       additional_data->>'source',
                       additional_data->>'origin',
                       additional_data->>'import_source',
                       ''
                   )
               ) IN ('gupy', 'pandape', 'merge', 'kenoby', 'solides',
                     'abler', 'greenhouse')
        """
    ))

    # 2) fast_track shim used by the LIA fast-track endpoint.
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET source_system = 'lia_fast_track'
         WHERE source_system IS NULL
           AND additional_data IS NOT NULL
           AND LOWER(COALESCE(additional_data->>'source', '')) = 'fast_track'
        """
    ))

    # 3) Generic ATS markers without a recognised slug.
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET source_system = 'ats_other'
         WHERE source_system IS NULL
           AND additional_data IS NOT NULL
           AND (
                (additional_data::jsonb ? 'imported_from_ats' AND
                 (additional_data->>'imported_from_ats')::text IN ('true', 'True'))
                OR additional_data::jsonb ? 'external_system_id'
                OR additional_data::jsonb ? 'ats_external_id'
           )
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, "ix_job_vacancies_source_system"):
        op.drop_index("ix_job_vacancies_source_system", table_name="job_vacancies")
    if _column_exists(conn, "job_vacancies", "source_system"):
        op.drop_column("job_vacancies", "source_system")
