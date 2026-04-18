"""Task #429 — add Job Readiness Hub columns to job_vacancies.

Revision ID: 086_add_job_readiness_columns
Revises: 085_add_source_system_to_job_vacancies
Create Date: 2026-04-18

Adds 4 columns and backfills `readiness_stage` from existing JD content.

Stages (string enum, kept as VARCHAR for forward-compat / easy backfill):
    importada, sem_jd, jd_rascunho, jd_enriquecido,
    perguntas_triagem, pronta_disparo, em_triagem
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "086_add_job_readiness_columns"
down_revision = "085_add_source_system_to_job_vacancies"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c)"
    ), {"t": table, "c": column}).scalar())


def _index_exists(conn, index_name: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes "
        "WHERE schemaname = 'public' AND indexname = :n)"
    ), {"n": index_name}).scalar())


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "job_vacancies"):
        return

    if not _column_exists(conn, "job_vacancies", "readiness_stage"):
        op.add_column(
            "job_vacancies",
            sa.Column("readiness_stage", sa.String(length=40), nullable=True),
        )
    if not _column_exists(conn, "job_vacancies", "readiness_blockers"):
        op.add_column(
            "job_vacancies",
            sa.Column("readiness_blockers", sa.JSON(), nullable=True),
        )
    if not _column_exists(conn, "job_vacancies", "last_readiness_event_at"):
        op.add_column(
            "job_vacancies",
            sa.Column("last_readiness_event_at", sa.DateTime(), nullable=True),
        )
    if not _column_exists(conn, "job_vacancies", "assigned_audience_policy"):
        op.add_column(
            "job_vacancies",
            sa.Column("assigned_audience_policy", sa.String(length=40), nullable=True),
        )

    if not _index_exists(conn, "ix_job_vacancies_readiness_stage"):
        op.create_index(
            "ix_job_vacancies_readiness_stage",
            "job_vacancies",
            ["readiness_stage"],
        )

    # ── Backfill ────────────────────────────────────────────────────────────
    # Idempotent: only touch rows where readiness_stage IS NULL.
    #
    # Rules (most-advanced wins):
    # 1. screening_config has status active/started -> em_triagem
    #    (also stamp every screening_question with approved=true so the
    #    classifier won't bounce them back to perguntas_triagem on re-classify)
    # 2. screening_questions non-empty AND every question already approved
    #    -> pronta_disparo
    # 3. screening_questions non-empty BUT not all approved -> perguntas_triagem
    # 4. enriched_jd present -> jd_enriquecido (recruiter still validates)
    # 5. description non-empty (a JD exists, no enrichment) -> jd_rascunho
    # 6. source_system NOT NULL and no description -> sem_jd (came from ATS)
    # 7. otherwise -> importada
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'em_triagem',
               screening_questions = (
                 SELECT COALESCE(jsonb_agg(
                   CASE
                     WHEN jsonb_typeof(elem) = 'object'
                       THEN elem || jsonb_build_object('approved', true)
                     ELSE jsonb_build_object('question', elem, 'approved', true)
                   END
                 ), '[]'::jsonb)
                 FROM jsonb_array_elements(COALESCE(screening_questions::jsonb, '[]'::jsonb)) AS elem
               )
         WHERE readiness_stage IS NULL
           AND screening_config IS NOT NULL
           AND LOWER(COALESCE(screening_config->'status'->>'screening_status', '')) IN ('active', 'paused', 'completed')
        """
    ))
    # All questions already flagged approved=true → pronta_disparo
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'pronta_disparo'
         WHERE readiness_stage IS NULL
           AND screening_questions IS NOT NULL
           AND jsonb_array_length(COALESCE(screening_questions::jsonb, '[]'::jsonb)) > 0
           AND NOT EXISTS (
             SELECT 1
               FROM jsonb_array_elements(COALESCE(screening_questions::jsonb, '[]'::jsonb)) AS elem
              WHERE jsonb_typeof(elem) <> 'object'
                 OR COALESCE((elem->>'approved')::boolean, false) = false
           )
        """
    ))
    # Otherwise (questions exist but not all approved) → perguntas_triagem
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'perguntas_triagem'
         WHERE readiness_stage IS NULL
           AND screening_questions IS NOT NULL
           AND jsonb_array_length(COALESCE(screening_questions::jsonb, '[]'::jsonb)) > 0
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'jd_enriquecido'
         WHERE readiness_stage IS NULL
           AND enriched_jd IS NOT NULL
           AND enriched_jd::text <> 'null'
           AND enriched_jd::text <> '{}'
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'jd_rascunho'
         WHERE readiness_stage IS NULL
           AND description IS NOT NULL
           AND length(trim(description)) > 0
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'sem_jd'
         WHERE readiness_stage IS NULL
           AND source_system IS NOT NULL
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE job_vacancies
           SET readiness_stage = 'importada'
         WHERE readiness_stage IS NULL
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, "ix_job_vacancies_readiness_stage"):
        op.drop_index("ix_job_vacancies_readiness_stage", table_name="job_vacancies")
    for col in (
        "assigned_audience_policy",
        "last_readiness_event_at",
        "readiness_blockers",
        "readiness_stage",
    ):
        if _column_exists(conn, "job_vacancies", col):
            op.drop_column("job_vacancies", col)
