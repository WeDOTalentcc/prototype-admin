"""Add responsibilities ARRAY column to job_vacancies (Task #1166).

Revision ID: 132_job_vacancies_responsibilities
Revises: 131_company_webhook_secrets
Create Date: 2026-05-18

Root cause (T-1166 investigation): ``job_vacancies`` lacked a dedicated
``responsibilities`` column, even though:

* ``imported_job_descriptions.responsibilities`` (ARRAY) already separates
  responsibilities from requirements at JD-upload time, and
* ``IntakeExtractor.JobIntakePayload`` (LLM extractor) emits the 3 fields
  separately (``responsibilities`` / ``technical_skills`` /
  ``behavioral_skills``).

Result: every create path either dropped ``responsibilities`` on the floor or
crammed both into the generic ``requirements`` ARRAY. The frontend then
rendered ``job.requirements`` under the "RESPONSABILIDADES" label
(``SCMSectionContent.tsx:68``) producing the contamination reported by the
user (vaga 200 showed "Python / TypeScript / PostgreSQL" as
*responsibilities*, but those are *requirements*).

This migration is purely additive (nullable, default ``[]``) — no existing
column is touched, no data is migrated. Backfill is a separate one-shot
script (Phase D) that copies from ``imported_job_descriptions.responsibilities``
when ``additional_data->>'imported_jd_id'`` links exist.

Reversible.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "132_job_vacancies_responsibilities"
down_revision = "131_company_webhook_secrets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_vacancies",
        sa.Column(
            "responsibilities",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("job_vacancies", "responsibilities")
