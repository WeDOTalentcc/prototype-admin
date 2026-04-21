"""Migrate job_vacancies.benefits from ARRAY(String) to structured JSONB.

Revision ID: 100_job_vacancy_benefits_jsonb
Revises: 099_extend_company_benefits_schema
Create Date: 2026-04-21

Task #765 — the legacy `benefits TEXT[]` column drops every structured
field the SalaryStage wizard exposes (category, value/value_type,
provider, is_highlighted, is_mandatory, …) on save. This migration:

* ALTER COLUMN to JSONB so the structure round-trips intact.
* Backfills each existing string element into the minimal
  ``{"name": <str>, "value_type": "informative"}`` object so the
  read paths can still find a name. Where a `company_benefits` row
  exists for the same company + name (case-insensitive), the richer
  schema (category, value_type, provider, value/percentage_value,
  is_mandatory, is_highlighted) is copied so the wizard immediately
  shows the correct chip on first load.

Idempotent — detects current column type and skips if already JSONB.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "100_job_vacancy_benefits_jsonb"
down_revision = "099_extend_company_benefits_schema"
branch_labels = None
depends_on = None


# Backfill SELECT used to populate benefits_new from the legacy TEXT[]
# column when the company_benefits catalogue exists. Joins each string
# element against company_benefits (case-insensitive name + tenant) so
# the rich schema (category, value_type, provider, value, …) is copied
# whenever a match exists, falling back to the minimal name-only shape
# otherwise. Exposed at module scope so the integration test can replay
# the same SQL inside an UPDATE.
BACKFILL_SELECT_WITH_COMPANY_BENEFITS = """
    SELECT jsonb_agg(
        CASE
            WHEN cb.id IS NOT NULL THEN jsonb_build_object(
                'id', cb.id::text,
                'name', cb.name,
                'description', COALESCE(cb.description, ''),
                'category', cb.category,
                'value_type', COALESCE(cb.value_type, 'informative'),
                'value', cb.value,
                'percentage_value', cb.percentage_value,
                'value_details', cb.value_details,
                'provider', cb.provider,
                'seniority_levels', COALESCE(cb.seniority_levels, '["all"]'::jsonb),
                'waiting_period_days', COALESCE(cb.waiting_period_days, 0),
                'is_mandatory', COALESCE(cb.is_mandatory, false),
                'is_active', COALESCE(cb.is_active, true),
                'is_highlighted', COALESCE(cb.is_highlighted, false),
                'is_discount', COALESCE(cb.is_discount, false)
            )
            ELSE jsonb_build_object(
                'name', name_elem,
                'category', NULL,
                'value_type', 'informative'
            )
        END
        ORDER BY ord
    )
    FROM unnest(job_vacancies.benefits) WITH ORDINALITY AS t(name_elem, ord)
    LEFT JOIN company_benefits cb
           ON cb.company_id = job_vacancies.company_id
          AND lower(cb.name) = lower(name_elem)
"""

# Downgrade backfill — copies just the names from the JSONB array
# into the new TEXT[] column. Empty/missing names are dropped.
DOWNGRADE_BACKFILL_UPDATE = """
    UPDATE job_vacancies
       SET benefits_old = COALESCE(
           ARRAY(
               SELECT COALESCE(elem->>'name', '')
                 FROM jsonb_array_elements(benefits) AS elem
                WHERE COALESCE(elem->>'name', '') <> ''
           ),
           ARRAY[]::TEXT[]
       )
"""


# Same shape but for environments missing the company_benefits table.
BACKFILL_SELECT_WITHOUT_COMPANY_BENEFITS = """
    SELECT jsonb_agg(
        jsonb_build_object(
            'name', name_elem,
            'category', NULL,
            'value_type', 'informative'
        )
        ORDER BY ord
    )
    FROM unnest(job_vacancies.benefits) WITH ORDINALITY AS t(name_elem, ord)
"""


def _benefits_column_type(bind) -> str | None:
    """Return the udt_name (`_text`, `jsonb`, `json`, …) of the
    ``job_vacancies.benefits`` column, or ``None`` when the column /
    table does not exist yet (fresh dev DB)."""
    row = bind.execute(
        sa.text(
            """
            SELECT udt_name
              FROM information_schema.columns
             WHERE table_name = 'job_vacancies'
               AND column_name = 'benefits'
            """
        )
    ).first()
    return row[0] if row else None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "job_vacancies" not in inspector.get_table_names():
        return

    udt = _benefits_column_type(bind)
    if udt is None:
        return  # column missing — let create_all handle it
    if udt in ("jsonb", "json"):
        return  # already migrated

    # company_benefits may not exist on very old envs. Use a NULL-safe
    # lateral join so the migration still succeeds in that case.
    has_company_benefits = "company_benefits" in inspector.get_table_names()

    # Postgres forbids subqueries inside ALTER TABLE ... USING, so we
    # use the canonical add-new / backfill / drop / rename pattern.
    # The SELECTs below are exposed as module-level constants so the
    # integration test can replay the very same backfill SQL.
    if has_company_benefits:
        backfill_select = BACKFILL_SELECT_WITH_COMPANY_BENEFITS
    else:
        backfill_select = BACKFILL_SELECT_WITHOUT_COMPANY_BENEFITS

    op.execute("ALTER TABLE job_vacancies ADD COLUMN benefits_new JSONB")
    op.execute(
        f"""
        UPDATE job_vacancies
           SET benefits_new = COALESCE(({backfill_select}), '[]'::jsonb)
        """
    )
    op.execute("ALTER TABLE job_vacancies DROP COLUMN benefits")
    op.execute("ALTER TABLE job_vacancies RENAME COLUMN benefits_new TO benefits")
    op.execute(
        "ALTER TABLE job_vacancies ALTER COLUMN benefits SET DEFAULT '[]'::jsonb"
    )
    op.execute("UPDATE job_vacancies SET benefits = '[]'::jsonb WHERE benefits IS NULL")
    op.execute("ALTER TABLE job_vacancies ALTER COLUMN benefits SET NOT NULL")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "job_vacancies" not in inspector.get_table_names():
        return

    udt = _benefits_column_type(bind)
    if udt != "jsonb":
        return

    # Lossy downgrade — drops every structured field, keeps the names.
    # Uses the same add-new / backfill / drop / rename pattern as the
    # upgrade because Postgres forbids subqueries in ALTER … USING.
    op.execute("ALTER TABLE job_vacancies ADD COLUMN benefits_old TEXT[]")
    op.execute(DOWNGRADE_BACKFILL_UPDATE)
    op.execute("ALTER TABLE job_vacancies DROP COLUMN benefits")
    op.execute("ALTER TABLE job_vacancies RENAME COLUMN benefits_old TO benefits")
    op.execute(
        "ALTER TABLE job_vacancies ALTER COLUMN benefits SET DEFAULT '{}'::text[]"
    )
