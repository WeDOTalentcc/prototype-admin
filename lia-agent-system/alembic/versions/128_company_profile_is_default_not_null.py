"""Backfill + NOT NULL on company_profiles.is_default.

Revision ID: 128_company_profile_is_default_not_null
Revises: 127_enrich_companies_schema
Create Date: 2026-05-12

Background
----------
Task #1016 / PR-B. The ORM model declared
``company_profiles.is_default = Column(Boolean, default=False)`` (no
``nullable=False`` and no ``server_default``), and ``CompanyProfileResponse``
declared ``is_default: bool`` (non-nullable). Legacy rows in production
landed with ``NULL`` because raw INSERTs (seed scripts, ad-hoc fixes,
historical PATCHes) never set the column.

Effect: ``GET /api/v1/company/profile`` returned 500
``ResponseValidationError: Input should be a valid boolean`` immediately
after every successful save — the frontend interpreted the 500 as
"save falhou" even though the PATCH itself had already persisted.

Fix (DB-first, validated by the audit doc):

1. Backfill existing NULLs with ``false``.
2. Set ``DEFAULT false`` so future raw INSERTs cannot reintroduce NULL.
3. ``ALTER COLUMN ... SET NOT NULL`` so the database enforces the
   contract the model + response schema already assumed.

Idempotent and safe to re-run. The only failure mode would be a NULL
sneaking in between step 1 and step 3 under heavy write load — extremely
unlikely for ``company_profiles`` (dozens of rows / tenant) and the
``DEFAULT false`` from step 2 plugs even that gap.
"""
from alembic import op
import sqlalchemy as sa


revision = "128_company_profile_is_default_not_null"
down_revision = "127_enrich_companies_schema"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t)"
    ), {"t": table}).scalar())


def _column_is_nullable(conn, table: str, column: str) -> bool | None:
    row = conn.execute(sa.text(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).scalar()
    if row is None:
        return None
    return str(row).upper() == "YES"


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "company_profiles"):
        return

    # Step 1 — backfill existing NULLs.
    conn.execute(sa.text(
        "UPDATE company_profiles SET is_default = false WHERE is_default IS NULL"
    ))

    # Step 2 — install DEFAULT false (idempotent).
    conn.execute(sa.text(
        "ALTER TABLE company_profiles ALTER COLUMN is_default SET DEFAULT false"
    ))

    # Step 3 — enforce NOT NULL (idempotent: only flip when still nullable).
    nullable = _column_is_nullable(conn, "company_profiles", "is_default")
    if nullable is True:
        conn.execute(sa.text(
            "ALTER TABLE company_profiles ALTER COLUMN is_default SET NOT NULL"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "company_profiles"):
        return

    # Reverse step 3, keep DEFAULT (harmless and matches model intent).
    nullable = _column_is_nullable(conn, "company_profiles", "is_default")
    if nullable is False:
        conn.execute(sa.text(
            "ALTER TABLE company_profiles ALTER COLUMN is_default DROP NOT NULL"
        ))
