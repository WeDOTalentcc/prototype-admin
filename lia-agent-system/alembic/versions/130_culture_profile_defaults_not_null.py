"""Backfill + DEFAULT + NOT NULL on company_culture_profiles array/score cols.

Revision ID: 130_culture_profile_defaults_not_null
Revises: 129_heal_demo_user_company_id
Create Date: 2026-05-15

Background
----------
Task #1100. ``company_culture_profiles`` declared several columns with a
Python-side ``default=[]`` / ``default=50`` only — no ``server_default`` and
no ``NOT NULL``. Rows written via raw SQL, legacy seed scripts or future
migrations could therefore land with ``NULL`` silently. Task #1098 worked
around the symptom by coercing ``NULL`` → default at response-validation
time in ``app/schemas/company_culture.py`` (since removed in Task #1106
once this migration was confirmed applied across all environments), but
the source of truth — the database — kept accepting garbage.

This migration moves the contract to the database (mirrors the pattern
already used by 128_company_profile_is_default_not_null):

1. Backfill existing NULLs with the canonical default
   (``ARRAY[]::text[]`` for the array columns, ``50`` for the Big Five
   scores).
2. Install ``DEFAULT`` so future raw INSERTs cannot reintroduce NULL.
3. ``ALTER COLUMN ... SET NOT NULL`` so the database enforces it.

Idempotent and safe to re-run.

Columns covered
~~~~~~~~~~~~~~~
Array (text[]) → default ``ARRAY[]::text[]``:
  - values
  - evp_bullets
  - core_competencies
  - analyzed_pages
  - locations
  - tech_stack
  - default_languages

Integer Big Five scores → default ``50``:
  - openness_score
  - conscientiousness_score
  - extraversion_score
  - agreeableness_score
  - stability_score
"""
from alembic import op
import sqlalchemy as sa


revision = "130_culture_profile_defaults_not_null"
down_revision = "129_heal_demo_user_company_id"
branch_labels = None
depends_on = None


_ARRAY_COLUMNS = (
    "values",
    "evp_bullets",
    "core_competencies",
    "analyzed_pages",
    "locations",
    "tech_stack",
    "default_languages",
)

_SCORE_COLUMNS = (
    "openness_score",
    "conscientiousness_score",
    "extraversion_score",
    "agreeableness_score",
    "stability_score",
)


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t)"
    ), {"t": table}).scalar())


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c)"
    ), {"t": table, "c": column}).scalar())


def _column_is_nullable(conn, table: str, column: str) -> bool | None:
    row = conn.execute(sa.text(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).scalar()
    if row is None:
        return None
    return str(row).upper() == "YES"


def _column_data_type(conn, table: str, column: str) -> str | None:
    """Return the canonical Postgres ``data_type`` (e.g. ``ARRAY``, ``jsonb``).

    The live schema has drifted from the SQLAlchemy model for some array
    columns (e.g. ``default_languages`` landed as ``jsonb`` in production
    while the model declares ``ARRAY(String)``). Picking the wrong default
    literal raises ``DatatypeMismatchError``, so we introspect per column.
    """
    row = conn.execute(sa.text(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).scalar()
    if row is None:
        return None
    return str(row).lower()


def _array_default_for(conn, column: str) -> str:
    """Pick a NULL-replacement literal compatible with the live column type."""
    dtype = _column_data_type(conn, "company_culture_profiles", column)
    # Postgres reports JSONB as ``jsonb`` and JSON as ``json``.
    if dtype in {"jsonb", "json"}:
        return "'[]'::jsonb" if dtype == "jsonb" else "'[]'::json"
    # Default to text[] for ARRAY columns and any unexpected type — matches
    # the model declaration ``Column(ARRAY(String), ...)``.
    return "ARRAY[]::text[]"


def _harden(conn, column: str, default_sql: str) -> None:
    if not _column_exists(conn, "company_culture_profiles", column):
        return
    # ``values`` is a SQL reserved word — quote every identifier defensively.
    quoted = f'"{column}"'
    # Step 1 — backfill NULLs.
    conn.execute(sa.text(
        f"UPDATE company_culture_profiles SET {quoted} = {default_sql} "
        f"WHERE {quoted} IS NULL"
    ))
    # Step 2 — install DEFAULT (idempotent).
    conn.execute(sa.text(
        f"ALTER TABLE company_culture_profiles "
        f"ALTER COLUMN {quoted} SET DEFAULT {default_sql}"
    ))
    # Step 3 — flip to NOT NULL only when still nullable.
    nullable = _column_is_nullable(conn, "company_culture_profiles", column)
    if nullable is True:
        conn.execute(sa.text(
            f"ALTER TABLE company_culture_profiles "
            f"ALTER COLUMN {quoted} SET NOT NULL"
        ))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "company_culture_profiles"):
        return

    for col in _ARRAY_COLUMNS:
        _harden(conn, col, _array_default_for(conn, col))

    for col in _SCORE_COLUMNS:
        _harden(conn, col, "50")


def downgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "company_culture_profiles"):
        return

    # Reverse step 3 only; keep DEFAULT (harmless and matches model intent).
    for col in (*_ARRAY_COLUMNS, *_SCORE_COLUMNS):
        if not _column_exists(conn, "company_culture_profiles", col):
            continue
        nullable = _column_is_nullable(conn, "company_culture_profiles", col)
        if nullable is False:
            conn.execute(sa.text(
                f'ALTER TABLE company_culture_profiles '
                f'ALTER COLUMN "{col}" DROP NOT NULL'
            ))
