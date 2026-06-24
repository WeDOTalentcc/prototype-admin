"""Migrate the demo tenant row from legacy 'demo_company' to canonical UUID.

Revision ID: 080_migrate_demo_company_to_uuid
Revises: 079_align_learning_patterns_columns
Create Date: 2026-04-16

Background
----------
Historically the demo tenant lived in the ``companies`` table with the
opaque string id ``'demo_company'`` (see
``database/migrations/007_data_hygiene_company_ids.sql``). JWTs and the
platform seed (``scripts/seed_full_platform.py``) now use the canonical
UUID ``00000000-0000-4000-a000-000000000001`` for the demo tenant. Task
#282 added ``app.core.tenant.normalize_demo_company_id`` to reconcile the
two values at token encode/decode time as a temporary shim.

This migration retires the legacy id by:

1. Inserting a new ``companies`` row with id = canonical UUID.
2. Re-pointing every string-typed ``company_id`` / ``tenant_id`` column
   in the ``public`` schema whose value equals ``'demo_company'`` to the
   canonical UUID. UUID-typed columns cannot hold the legacy literal so
   they are skipped.
3. Updating column ``DEFAULT`` clauses that still reference
   ``'demo_company'`` so future inserts use the canonical UUID.
4. Asserting that no row anywhere still references the legacy id, then
   deleting the legacy ``companies`` row.

Failure mode is fail-fast: if any UPDATE fails (e.g. due to a unique
constraint conflict from a polluted dev database that accumulated
parallel demo datasets) the migration aborts and must be remediated by
hand before retrying.
"""
from alembic import op
import sqlalchemy as sa

revision = "080_migrate_demo_company_to_uuid"
down_revision = "079_sox_audit_company_id"
branch_labels = None
depends_on = None


LEGACY_DEMO_ID = "demo_company"
CANONICAL_DEMO_UUID = "00000000-0000-4000-a000-000000000001"

# String types whose values can equal the legacy 'demo_company' literal.
STRING_TYPES = ("character varying", "varchar", "text", "character")

# The single FK in the schema whose parent and child both hold a string
# ``company_id`` value. Re-pointing the legacy demo id requires updating
# both sides of this cycle within one statement boundary, so it must be
# made deferrable for the duration of the migration. Listed explicitly to
# avoid touching unrelated FKs.
CYCLIC_STRING_COMPANY_FKS = [
    ("company_modules", "fk_company_modules_credit_accounts"),
]


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _string_columns(conn, column_name: str):
    """Return the list of public table names whose ``column_name`` is
    a string type (and could therefore hold the legacy literal)."""
    rows = conn.execute(sa.text(
        "SELECT table_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' AND column_name = :c"
    ), {"c": column_name}).fetchall()
    return [t for (t, dt) in rows if dt and dt.lower() in STRING_TYPES]


def _constraint_exists(conn, table: str, constraint: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS ("
        " SELECT 1 FROM pg_constraint c "
        " JOIN pg_class cl ON cl.oid = c.conrelid "
        " JOIN pg_namespace n ON n.oid = cl.relnamespace "
        " WHERE n.nspname = 'public' AND cl.relname = :t AND c.conname = :c"
        ")"
    ), {"t": table, "c": constraint}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "companies"):
        # Fresh schema that never created the legacy table; nothing to
        # migrate (the bootstrap will use the canonical UUID directly).
        return

    # ------------------------------------------------------------------
    # Step 1: ensure the canonical companies row exists.
    # ------------------------------------------------------------------
    legacy_row = conn.execute(sa.text(
        "SELECT name, display_name, is_active, is_demo "
        "FROM companies WHERE id = :id"
    ), {"id": LEGACY_DEMO_ID}).fetchone()

    if legacy_row is not None:
        conn.execute(sa.text("""
            INSERT INTO companies (id, name, display_name, is_active, is_demo,
                                   created_at, updated_at)
            VALUES (:id, :name, :display_name, :is_active, :is_demo,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                display_name = EXCLUDED.display_name,
                is_active = EXCLUDED.is_active,
                is_demo = EXCLUDED.is_demo,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "id": CANONICAL_DEMO_UUID,
            "name": legacy_row[0] or "Demo Company",
            "display_name": legacy_row[1] or "Demo Company - Development/Testing",
            "is_active": legacy_row[2] if legacy_row[2] is not None else True,
            "is_demo": legacy_row[3] if legacy_row[3] is not None else True,
        })
    else:
        conn.execute(sa.text("""
            INSERT INTO companies (id, name, display_name, is_active, is_demo,
                                   created_at, updated_at)
            VALUES (:id, 'Demo Company', 'Demo Company - Development/Testing',
                    TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """), {"id": CANONICAL_DEMO_UUID})

    # ------------------------------------------------------------------
    # Step 2: re-point every string company_id / tenant_id column.
    #
    # Updates run fail-fast — a UNIQUE-constraint violation from a
    # polluted dev database (where canonical-UUID demo data was seeded
    # alongside the legacy one) will abort the migration so it can be
    # remediated by hand rather than partially applied.
    # ------------------------------------------------------------------
    # The one schema cycle on a string company_id is
    # company_modules.company_id -> credit_accounts.company_id.
    # Both sides must be updated inside the same transaction, so the FK
    # is temporarily marked DEFERRABLE and the check is deferred to
    # commit. Other (UUID-typed) FKs are unaffected by this migration.
    deferred_fks = []
    for table_name, constraint_name in CYCLIC_STRING_COMPANY_FKS:
        if _constraint_exists(conn, table_name, constraint_name):
            conn.execute(sa.text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" DEFERRABLE'
            ))
            deferred_fks.append((table_name, constraint_name))
    if deferred_fks:
        conn.execute(sa.text("SET CONSTRAINTS ALL DEFERRED"))

    total_updated = 0
    for column_name in ("company_id", "tenant_id"):
        for table_name in _string_columns(conn, column_name):
            if table_name == "companies":
                # Parent row is rewritten via INSERT/DELETE, not UPDATE.
                continue
            result = conn.execute(sa.text(
                f"UPDATE {table_name} SET {column_name} = :new "
                f"WHERE {column_name} = :old"
            ), {"new": CANONICAL_DEMO_UUID, "old": LEGACY_DEMO_ID})
            if result.rowcount:
                print(f"[080] {table_name}.{column_name}: updated "
                      f"{result.rowcount} rows from legacy demo id")
                total_updated += result.rowcount

    # Restore deferrability now that all rewrites have happened. The
    # deferred FK check will run at commit and raise if the data is
    # inconsistent.
    if deferred_fks:
        conn.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))
        for table_name, constraint_name in deferred_fks:
            conn.execute(sa.text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" NOT DEFERRABLE'
            ))

    # ------------------------------------------------------------------
    # Step 3: update column DEFAULT clauses still pinned to legacy id.
    # ------------------------------------------------------------------
    defaults = conn.execute(sa.text(
        "SELECT table_name, column_name "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' "
        "  AND column_name IN ('company_id', 'tenant_id') "
        "  AND column_default IS NOT NULL "
        "  AND column_default LIKE '%demo_company%'"
    )).fetchall()
    for table_name, column_name in defaults:
        conn.execute(sa.text(
            f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
            f"SET DEFAULT '{CANONICAL_DEMO_UUID}'"
        ))
        print(f"[080] {table_name}.{column_name}: DEFAULT updated to canonical UUID")

    # ------------------------------------------------------------------
    # Step 4: assert no leftover legacy references, then drop the row.
    # ------------------------------------------------------------------
    leftover_rows = []
    for column_name in ("company_id", "tenant_id"):
        for table_name in _string_columns(conn, column_name):
            if table_name == "companies":
                continue
            count = conn.execute(sa.text(
                f"SELECT COUNT(*) FROM {table_name} "
                f"WHERE {column_name} = :old"
            ), {"old": LEGACY_DEMO_ID}).scalar() or 0
            if count:
                leftover_rows.append((table_name, column_name, count))

    if leftover_rows:
        details = ", ".join(
            f"{t}.{c}={n}" for (t, c, n) in leftover_rows
        )
        raise RuntimeError(
            "[080] Legacy 'demo_company' references remain after rewrite: "
            f"{details}. Refusing to drop legacy companies row; please "
            "reconcile these tables and re-run."
        )

    deleted = conn.execute(sa.text(
        "DELETE FROM companies WHERE id = :id"
    ), {"id": LEGACY_DEMO_ID})
    if deleted.rowcount:
        print(f"[080] companies: removed legacy '{LEGACY_DEMO_ID}' row")

    print(f"[080] Demo tenant migration complete. "
          f"Total tenant-scoped rows re-pointed: {total_updated}.")


def downgrade() -> None:
    """Best-effort rollback to the legacy 'demo_company' string id.

    Provided for completeness; once the canonical UUID is in circulation,
    downgrading will leave JWTs out of sync with the database. Skipped if
    the companies table is absent.
    """
    conn = op.get_bind()
    if not _table_exists(conn, "companies"):
        return

    canonical_row = conn.execute(sa.text(
        "SELECT name, display_name, is_active, is_demo "
        "FROM companies WHERE id = :id"
    ), {"id": CANONICAL_DEMO_UUID}).fetchone()

    if canonical_row is not None:
        conn.execute(sa.text("""
            INSERT INTO companies (id, name, display_name, is_active, is_demo,
                                   created_at, updated_at)
            VALUES (:id, :name, :display_name, :is_active, :is_demo,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
        """), {
            "id": LEGACY_DEMO_ID,
            "name": canonical_row[0] or "Demo Company",
            "display_name": canonical_row[1] or "Demo Company - Development/Testing",
            "is_active": canonical_row[2] if canonical_row[2] is not None else True,
            "is_demo": canonical_row[3] if canonical_row[3] is not None else True,
        })

    deferred_fks = []
    for table_name, constraint_name in CYCLIC_STRING_COMPANY_FKS:
        if _constraint_exists(conn, table_name, constraint_name):
            conn.execute(sa.text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" DEFERRABLE'
            ))
            deferred_fks.append((table_name, constraint_name))
    if deferred_fks:
        conn.execute(sa.text("SET CONSTRAINTS ALL DEFERRED"))

    for column_name in ("company_id", "tenant_id"):
        for table_name in _string_columns(conn, column_name):
            if table_name == "companies":
                continue
            conn.execute(sa.text(
                f"UPDATE {table_name} SET {column_name} = :new "
                f"WHERE {column_name} = :old"
            ), {"new": LEGACY_DEMO_ID, "old": CANONICAL_DEMO_UUID})

    if deferred_fks:
        conn.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))
        for table_name, constraint_name in deferred_fks:
            conn.execute(sa.text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" NOT DEFERRABLE'
            ))

    conn.execute(sa.text(
        "DELETE FROM companies WHERE id = :id"
    ), {"id": CANONICAL_DEMO_UUID})
