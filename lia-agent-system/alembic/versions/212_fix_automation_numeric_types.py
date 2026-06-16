"""Fix automation numeric column types: String -> Integer/Float.

Revision ID: 212_fix_automation_numeric_types
Revises: 211
Create Date: 2026-05-26

Bug context (AUTOMATIONS_BACKEND_AUDIT.md):
    Several "numeric" columns in the automation models were declared as
    String(10) (e.g. ``cooldown_minutes``, ``execution_count``,
    ``confidence_threshold``, ``execution_time_ms``, ``confidence_score``).
    This made arithmetic and comparison operations (``WHERE cooldown_minutes > 30``)
    compare lexically rather than numerically, producing wrong results and
    silently corrupting analytics.

Safety:
    - We never DROP data.
    - ALTER COLUMN ... USING falls back to the column default when the
      stored string is non-numeric, so dirty rows (e.g. empty strings)
      don't abort the migration.
    - Downgrade restores VARCHAR(10) by stringifying numeric values.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "212_fix_automation_numeric_types"
down_revision = "211"
branch_labels = None
depends_on = None


# (table, column, new_type, default_sql, nullable)
INT_COLS = [
    ("communication_automations", "cooldown_minutes", "INTEGER", "0", False),
    ("communication_automations", "execution_count", "INTEGER", "0", False),
    ("automation_execution_logs", "execution_time_ms", "INTEGER", None, True),
]
FLOAT_COLS = [
    ("ai_suggestions", "confidence_score", "DOUBLE PRECISION", None, True),
    ("stage_automation_rules", "confidence_threshold", "DOUBLE PRECISION", "0.8", False),
]


def _alter_to_numeric(table: str, col: str, new_type: str, default_sql: str | None, nullable: bool) -> None:
    """Cast a TEXT/VARCHAR column to a numeric type, defaulting bad data."""
    # Coalesce NULL/empty/non-numeric strings to the default (or NULL if no default).
    fallback = default_sql if default_sql is not None else "NULL"
    using_expr = (
        f"CASE "
        f"WHEN {col} IS NULL THEN {fallback} "
        f"WHEN btrim({col}) = '' THEN {fallback} "
        # ~ matches POSIX regex; accepts int or float (no scientific notation needed here).
        f"WHEN btrim({col}) ~ '^-?[0-9]+(\\.[0-9]+)?$' THEN btrim({col})::{new_type} "
        f"ELSE {fallback} "
        f"END"
    )
    # Drop old (string) default first — Postgres can't auto-cast a text default to numeric.
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")
    op.execute(
        f"ALTER TABLE {table} "
        f"ALTER COLUMN {col} TYPE {new_type} USING ({using_expr})"
    )
    # Defaults are stored as strings in the column metadata; reset them.
    if default_sql is not None:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT {default_sql}")
    else:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")

    if nullable:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL")
    else:
        # Backfill any remaining NULL just in case before enforcing NOT NULL.
        op.execute(f"UPDATE {table} SET {col} = {default_sql} WHERE {col} IS NULL")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL")


def _alter_to_varchar(table: str, col: str, default_str: str | None, nullable: bool) -> None:
    """Reverse: numeric -> VARCHAR(10), stringifying the value."""
    using_expr = f"CASE WHEN {col} IS NULL THEN NULL ELSE {col}::text END"
    # Drop numeric default first — Postgres can't auto-cast it to VARCHAR.
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")
    op.execute(
        f"ALTER TABLE {table} "
        f"ALTER COLUMN {col} TYPE VARCHAR(10) USING ({using_expr})"
    )
    if default_str is not None:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT '{default_str}'")
    else:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")

    if nullable:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL")
    else:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL")


def upgrade() -> None:
    for table, col, new_type, default_sql, nullable in INT_COLS + FLOAT_COLS:
        _alter_to_numeric(table, col, new_type, default_sql, nullable)


def downgrade() -> None:
    # Reverse in opposite order; original String(10) with string defaults.
    reverse_int = [(t, c, d, n) for t, c, _, d, n in INT_COLS]
    reverse_float = [(t, c, d, n) for t, c, _, d, n in FLOAT_COLS]
    for table, col, default_sql, nullable in reverse_float + reverse_int:
        default_str = default_sql if default_sql is not None else None
        _alter_to_varchar(table, col, default_str, nullable)
