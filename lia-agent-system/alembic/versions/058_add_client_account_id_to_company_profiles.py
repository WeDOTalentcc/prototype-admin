"""Add client_account_id FK to company_profiles for multi-tenancy linking.

Links CompanyProfile to ClientAccount, enabling tenant resolution:
WorkOS org -> ClientAccount -> CompanyProfile.
"""

revision = '058'
down_revision = '057'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade():
    op.execute("""
        ALTER TABLE company_profiles
        ADD COLUMN IF NOT EXISTS client_account_id UUID
        REFERENCES client_accounts(id) ON DELETE SET NULL
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_company_profiles_client_account_id
        ON company_profiles (client_account_id)
        WHERE client_account_id IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_company_profiles_client_account_id
        ON company_profiles (client_account_id)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_company_profiles_client_account_id")
    op.execute("DROP INDEX IF EXISTS uq_company_profiles_client_account_id")
    op.execute("ALTER TABLE company_profiles DROP COLUMN IF EXISTS client_account_id")
