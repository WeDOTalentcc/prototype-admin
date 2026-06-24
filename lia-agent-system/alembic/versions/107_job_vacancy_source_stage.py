"""Add source + wizard_stage columns to job_vacancies (Phase 4H).

Bug 7 fix (post-mortem 2026-05-02) — distinguish vagas created by:
  - wizard (source='wizard')      ← canonical JobCreationGraph flow
  - ATS bulk import (source='ats_import')  ← /api/v1/jobs/bulk-import
  - external sync (source='ats_external')  ← future ATS sync (Gupy, Greenhouse)
  - manual REST  (source='manual')          ← direct POST /api/v1/jobs

Plus wizard_stage to persist current LangGraph node (intake, jd_enrichment,
bigfive, salary, competency, wsi_questions, eligibility, review, published,
calibration, handoff). Without this column, wizard_stage lives only in
LangGraph checkpointer state — invisible to FE filtering / badges.

Harness:
  GUIDE = canonical column on job_vacancies (single source of truth) —
          avoids JOIN with imported_job_descriptions in FE list query.
  SENSOR = tests/integration/test_job_source_default.py asserts every
           insert path sets source explicitly (no NULL). Migration 107
           adds NOT NULL with server_default='wizard' as safety net.
  FAIL-OPEN: existing rows backfilled with 'wizard' (no breaking change).
  FAIL-CLOSED: new INSERTs MUST set source — db enforces NOT NULL.

Down revision: 106_sprint_b_learning_tables.
"""
revision = "107_job_vacancy_source_stage"
# down_revision adapted for fix/remediation-unified base.
# In the original branch (feat/ats-bulk-import-phase-4h-4i), this pointed to
# 106_sprint_b_learning_tables. That branch had migrations 105 (merge heads)
# and 106 (Sprint B tables) that do NOT exist on fix/remediation-unified.
# Adapted to skip directly to 104 (the latest existing pre-107 migration here).
down_revision = "72bb11ddbbaa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    import sqlalchemy as sa

    # ── 1. job_vacancies.source ─────────────────────────────────────────
    # NOT NULL with server_default='wizard' — backfills existing rows
    # safely. Every new caller MUST set source explicitly (tests enforce).
    op.add_column(
        "job_vacancies",
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'wizard'"),
        ),
    )
    op.create_index(
        "ix_job_vacancies_company_source",
        "job_vacancies",
        ["company_id", "source"],
    )

    # ── 2. job_vacancies.wizard_stage ───────────────────────────────────
    # Nullable — non-wizard sources (ats_import, manual) leave it NULL.
    # Wizard syncs this from LangGraph state on each node transition.
    op.add_column(
        "job_vacancies",
        sa.Column(
            "wizard_stage",
            sa.String(50),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_job_vacancies_wizard_stage",
        "job_vacancies",
        ["wizard_stage"],
    )


def downgrade() -> None:
    from alembic import op

    op.drop_index("ix_job_vacancies_wizard_stage", table_name="job_vacancies")
    op.drop_column("job_vacancies", "wizard_stage")

    op.drop_index("ix_job_vacancies_company_source", table_name="job_vacancies")
    op.drop_column("job_vacancies", "source")
