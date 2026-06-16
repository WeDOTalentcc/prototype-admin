"""Add disabled_eligibility_question_ids to job_vacancies for opt-out screening questions.

Revision ID: 024_add_disabled_eligibility_question_ids
Revises: 023_add_stage_entered_at
Create Date: 2026-03-07

Context:
  Company-level screening questions (CompanyScreeningQuestion) are now active by
  default on every job vacancy. Recruiters can disable specific questions per job
  via the screening config UI. This column stores the list of UUIDs (strings) of
  CompanyScreeningQuestion records that have been disabled for a given job.

  Empty array (default) = all company questions are active for this job.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "024_add_disabled_eligibility_question_ids"
down_revision = "023_add_stage_entered_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_vacancies",
        sa.Column(
            "disabled_eligibility_question_ids",
            JSONB,
            nullable=True,
            server_default="'[]'::jsonb",
        ),
    )


def downgrade() -> None:
    op.drop_column("job_vacancies", "disabled_eligibility_question_ids")
