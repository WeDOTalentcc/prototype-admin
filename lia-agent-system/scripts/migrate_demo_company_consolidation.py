"""Idempotent re-runner for Demo Company consolidation (Task #969 / T-C).

Background
----------
Alembic migration ``080_migrate_demo_company_to_uuid`` originally
re-pointed every ``demo_company`` slug reference to the canonical UUID
``00000000-0000-4000-a000-000000000001`` and deleted the slug row from
``companies``. After that, ``app/core/database.py::ensure_default_company``
silently re-inserted the slug row on every backend boot
(canonical-fix anti-pattern #7 — migration inline at runtime), so
the ``demo_company`` row reappeared with no tenant data attached but
visible in `SELECT ... FROM companies`. Task #969 fixes the source
(``ensure_default_company`` now upserts the canonical UUID instead) and
this script re-runs the consolidation idempotently for any environment
that already accumulated the duplicate.

Behaviour
---------
1. Re-point every string-typed ``company_id``/``tenant_id`` column whose
   value equals ``demo_company`` to the canonical UUID.
2. Refresh column DEFAULT clauses still pinned to the legacy literal.
3. Assert no leftover references, then DELETE the legacy
   ``companies`` row.
4. Upsert the canonical Demo Company row with rich values
   (``scripts.seeds.demo_company``).
5. Print a per-table report: ``{table.column: rows_migrated}``.

The script is fully idempotent: running it on a clean DB is a no-op
(Step 1 finds zero rows, Step 3 finds zero leftovers, Step 4 upserts
the same values).

Usage::

    cd lia-agent-system
    python -m scripts.migrate_demo_company_consolidation

Exit codes::

    0 — consolidation succeeded (or DB was already clean)
    1 — leftover legacy references after rewrite (manual cleanup needed)
    2 — DB unreachable / unexpected SQL error (see logs)
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from sqlalchemy import text

logger = logging.getLogger("migrate_demo_company_consolidation")

LEGACY_DEMO_ID = "demo_company"
CANONICAL_DEMO_UUID = "00000000-0000-4000-a000-000000000001"
STRING_TYPES = ("character varying", "varchar", "text", "character")
CYCLIC_STRING_COMPANY_FKS = [
    ("company_modules", "fk_company_modules_credit_accounts"),
]


async def _string_company_id_columns(conn) -> list[tuple[str, str]]:
    rows = await conn.execute(text(
        "SELECT table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema='public' "
        "  AND column_name IN ('company_id','tenant_id')"
    ))
    out: list[tuple[str, str]] = []
    for table_name, column_name, data_type in rows.fetchall():
        if table_name == "companies":
            continue
        if data_type and data_type.lower() in STRING_TYPES:
            out.append((table_name, column_name))
    return out


async def _constraint_exists(conn, table: str, constraint: str) -> bool:
    res = await conn.execute(text(
        "SELECT EXISTS ("
        " SELECT 1 FROM pg_constraint c "
        " JOIN pg_class cl ON cl.oid = c.conrelid "
        " JOIN pg_namespace n ON n.oid = cl.relnamespace "
        " WHERE n.nspname='public' AND cl.relname=:t AND c.conname=:c)"
    ), {"t": table, "c": constraint})
    return bool(res.scalar())


async def consolidate(conn) -> dict[str, Any]:
    """Run the full consolidation. Returns a structured report."""
    report: dict[str, Any] = {
        "rewrites": {},        # {f"{table}.{column}": rowcount}
        "defaults_updated": [],  # [(table, column)]
        "leftovers": [],       # [(table, column, count)] — non-empty = abort
        "legacy_row_deleted": False,
        "seeded_canonical": False,
    }

    # ---- Step 1: defer cyclic FKs that span string company_ids ----
    deferred: list[tuple[str, str]] = []
    for table_name, constraint_name in CYCLIC_STRING_COMPANY_FKS:
        if await _constraint_exists(conn, table_name, constraint_name):
            await conn.execute(text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" DEFERRABLE'
            ))
            deferred.append((table_name, constraint_name))
    if deferred:
        await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

    # ---- Step 2: rewrite all string company_id/tenant_id values ----
    for table_name, column_name in await _string_company_id_columns(conn):
        result = await conn.execute(text(
            f"UPDATE {table_name} SET {column_name} = :new "
            f"WHERE {column_name} = :old"
        ), {"new": CANONICAL_DEMO_UUID, "old": LEGACY_DEMO_ID})
        if result.rowcount:
            report["rewrites"][f"{table_name}.{column_name}"] = result.rowcount

    # ---- Step 3: restore FK deferrability ----
    if deferred:
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        for table_name, constraint_name in deferred:
            await conn.execute(text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER CONSTRAINT "{constraint_name}" NOT DEFERRABLE'
            ))

    # ---- Step 4: refresh DEFAULT clauses pinned to legacy literal ----
    defaults = await conn.execute(text(
        "SELECT table_name, column_name "
        "FROM information_schema.columns "
        "WHERE table_schema='public' "
        "  AND column_name IN ('company_id','tenant_id') "
        "  AND column_default IS NOT NULL "
        "  AND column_default LIKE '%demo_company%'"
    ))
    for table_name, column_name in defaults.fetchall():
        await conn.execute(text(
            f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
            f"SET DEFAULT '{CANONICAL_DEMO_UUID}'"
        ))
        report["defaults_updated"].append((table_name, column_name))

    # ---- Step 5: assert no leftovers, then delete legacy row ----
    for table_name, column_name in await _string_company_id_columns(conn):
        leftover = await conn.execute(text(
            f"SELECT COUNT(*) FROM {table_name} "
            f"WHERE {column_name} = :old"
        ), {"old": LEGACY_DEMO_ID})
        count = leftover.scalar() or 0
        if count:
            report["leftovers"].append((table_name, column_name, count))

    if report["leftovers"]:
        return report  # caller will abort before deletion

    deleted = await conn.execute(text(
        "DELETE FROM companies WHERE id = :id"
    ), {"id": LEGACY_DEMO_ID})
    report["legacy_row_deleted"] = bool(deleted.rowcount)

    # ---- Step 6: upsert canonical Demo Company with rich values ----
    from scripts.seeds.demo_company import seed_demo_company
    await seed_demo_company(conn)
    report["seeded_canonical"] = True

    return report


def _format_report(report: dict[str, Any]) -> str:
    lines = ["[consolidation] report:"]
    if report["rewrites"]:
        for key, count in sorted(report["rewrites"].items()):
            lines.append(f"  rewrite {key}: {count} rows")
    else:
        lines.append("  rewrite: 0 rows (db already clean)")
    if report["defaults_updated"]:
        for table_name, column_name in report["defaults_updated"]:
            lines.append(f"  default refreshed: {table_name}.{column_name}")
    if report["leftovers"]:
        lines.append("  LEFTOVER LEGACY REFERENCES (abort, no deletion):")
        for table_name, column_name, count in report["leftovers"]:
            lines.append(f"    {table_name}.{column_name}: {count} rows")
    lines.append(f"  legacy companies row deleted: {report['legacy_row_deleted']}")
    lines.append(f"  canonical demo seeded: {report['seeded_canonical']}")
    return "\n".join(lines)


async def _main() -> int:
    from app.core.database import engine

    async with engine.begin() as conn:
        try:
            report = await consolidate(conn)
        except Exception as exc:
            # pii-logs ok: nome de tabela/coluna nao e PII per LGPD Art.5 V.
            logger.exception("[consolidation] aborted: %s", exc)
            return 2

    logger.info(_format_report(report))

    if report["leftovers"]:
        logger.error(
            "[consolidation] leftover references blocked the deletion of "
            "the legacy companies row. Reconcile manually and re-run."
        )
        return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(asyncio.run(_main()))
