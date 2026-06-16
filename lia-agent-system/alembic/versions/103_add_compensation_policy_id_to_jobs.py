"""add compensation_policy_id to job_vacancies

Revision ID: 103
Revises: 102
Create Date: 2026-04-30
"""
from alembic import op

revision = "103_add_compensation_policy_id_to_jobs"
down_revision = "102_realign_compensation_policies"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE job_vacancies
        ADD COLUMN IF NOT EXISTS compensation_policy_id UUID
            REFERENCES compensation_policies(id) ON DELETE SET NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_vacancies_compensation_policy_id
            ON job_vacancies(compensation_policy_id);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_job_vacancies_compensation_policy_id;")
    op.execute("ALTER TABLE job_vacancies DROP COLUMN IF EXISTS compensation_policy_id;")
