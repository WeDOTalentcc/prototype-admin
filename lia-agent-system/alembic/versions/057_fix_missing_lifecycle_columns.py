"""Fix missing lifecycle columns from migration 056.

Migration 056 was marked as applied but the DDL was never executed.
This corrective migration re-applies the same DDL with IF NOT EXISTS
to ensure all environments have the required columns and indexes.
"""

revision = '057'
down_revision = '056'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS is_hired BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS hired_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS hired_job_id VARCHAR(255) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS hired_job_title VARCHAR(500) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS blacklisted_by VARCHAR(255) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS blacklisted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_is_hired
        ON candidates (is_hired) WHERE is_hired = TRUE
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_is_blacklisted_by
        ON candidates (blacklisted_by) WHERE blacklisted_by IS NOT NULL
    """)

    op.execute("""
        ALTER TABLE vacancy_candidates
        ADD COLUMN IF NOT EXISTS previous_status VARCHAR(50) DEFAULT NULL
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_candidates_is_hired")
    op.execute("DROP INDEX IF EXISTS idx_candidates_is_blacklisted_by")
    op.execute("""
        ALTER TABLE candidates
        DROP COLUMN IF EXISTS is_hired,
        DROP COLUMN IF EXISTS hired_at,
        DROP COLUMN IF EXISTS hired_job_id,
        DROP COLUMN IF EXISTS hired_job_title,
        DROP COLUMN IF EXISTS blacklisted_by,
        DROP COLUMN IF EXISTS blacklisted_at
    """)
    op.execute("ALTER TABLE vacancy_candidates DROP COLUMN IF EXISTS previous_status")
