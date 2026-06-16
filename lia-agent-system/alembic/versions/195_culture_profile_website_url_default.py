"""fix(schema): company_culture_profiles.website_url SET DEFAULT ''

Root cause (2026-05-25): website_url = Column(String(500), nullable=False)
declared in the ORM with no Python default= and no server_default=.
Any cold-start INSERT (recruiter manually editing Cultura & EVP fields in
Configurações → Minha Empresa for a company that has never run /analyze)
failed with:
  asyncpg.exceptions.NotNullViolationError: null value in column "website_url"
  of relation "company_culture_profiles" violates not-null constraint

This blocked ALL 11 Cultura & EVP fields from saving for tenants that had
never triggered a culture analysis job (the majority of onboarding tenants).

Approach:
  1. upsert_profile_fields in the repo now calls filtered.setdefault("website_url", "")
     before CREATE (defense in code).
  2. This migration adds the DB-level DEFAULT '' so any future non-ORM inserts
     (direct SQL, test seeds, admin scripts) also work without providing the
     column explicitly.

No data migration needed — existing rows already have a non-null website_url.
"""
from alembic import op
from sqlalchemy import text

revision = "195"
down_revision = "194"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "ALTER COLUMN website_url SET DEFAULT ''"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "ALTER COLUMN website_url DROP DEFAULT"
    ))
