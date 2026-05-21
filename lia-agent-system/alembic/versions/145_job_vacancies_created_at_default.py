"""Sprint O.2: job_vacancies.created_at + updated_at server defaults + backfill NULLs.

Revision ID: 145_job_vacancies_created_at_default
Revises: 144_t20_audit_demographic_proxies
Create Date: 2026-05-21

Root cause: api_client.py:_create_job_local INSERT omits created_at/updated_at columns,
and DB schema lacks DEFAULT CURRENT_TIMESTAMP. Result: 4 vacancies from Sprint M/N
validation runs have created_at = NULL, breaking ORDER BY created_at DESC, time-based
filters, and audit timeline UI.

Fix (defense-in-depth, Option C):
1. ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP (DB-side safety net)
2. ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP (idem)
3. Backfill 4 NULL rows from Sprint M/N with COALESCE(updated_at, NOW())
4. Companion fix in api_client.py to explicitly pass both timestamps (belt-and-suspenders)

Sentinel: tests/wizard/test_api_client_created_at.py asserts DEFAULT presence
+ INSERT statement includes both columns (no regression).
"""
from alembic import op
import sqlalchemy as sa


revision = "145_job_vacancies_created_at_default"
down_revision = "144_t20_audit_demographic_proxies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add DB-side DEFAULT (idempotent — no-op if already set)
    op.alter_column(
        "job_vacancies",
        "created_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "job_vacancies",
        "updated_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )

    # 2. Backfill the 4 Sprint M/N NULL rows.
    #    Strategy: COALESCE(updated_at, NOW()) — preserves real timeline when updated_at exists,
    #    otherwise NOW() (only row 713f23ef has both NULL — E2E test row, NOW() is fine).
    op.execute(
        """
        UPDATE job_vacancies
        SET created_at = COALESCE(updated_at, NOW())
        WHERE created_at IS NULL
        """
    )

    # 3. Also backfill any NULL updated_at (only row 713f23ef applies)
    op.execute(
        """
        UPDATE job_vacancies
        SET updated_at = COALESCE(created_at, NOW())
        WHERE updated_at IS NULL
        """
    )


def downgrade() -> None:
    op.alter_column("job_vacancies", "created_at", server_default=None)
    op.alter_column("job_vacancies", "updated_at", server_default=None)
