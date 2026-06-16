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
    """Discover every string column in ``public.*`` that semantically
    references the tenant identifier and is therefore eligible for the
    legacy → canonical rewrite.

    Source set is the UNION of:

    * **FK metadata** (authoritative): every column that has an actual
      ``FOREIGN KEY ... REFERENCES companies(id)`` constraint, regardless
      of column name. This catches non-conventional naming
      (``owner_company_id``, ``parent_tenant``, etc.) flagged by the
      architect review of T-C as previously unmigrated.
    * **Convention fallback**: any column literally named
      ``company_id``/``tenant_id``. Some tables in this repo carry
      "soft" tenant pointers without a declared FK (e.g. denormalised
      analytics tables); without them an upstream rewrite would leave
      orphan ``demo_company`` strings undiscovered.

    Only string-typed columns are returned — UUID-typed FKs are not
    affected by the slug→UUID rewrite.
    """
    fk_rows = await conn.execute(text(
        """
        SELECT  src.relname        AS table_name,
                src_att.attname    AS column_name,
                fmt.data_type      AS data_type
        FROM    pg_constraint c
        JOIN    pg_class       src     ON src.oid = c.conrelid
        JOIN    pg_namespace   src_ns  ON src_ns.oid = src.relnamespace
        JOIN    pg_class       tgt     ON tgt.oid = c.confrelid
        JOIN    pg_namespace   tgt_ns  ON tgt_ns.oid = tgt.relnamespace
        JOIN    pg_attribute   src_att ON src_att.attrelid = src.oid
                                       AND src_att.attnum  = ANY(c.conkey)
        JOIN    pg_attribute   tgt_att ON tgt_att.attrelid = tgt.oid
                                       AND tgt_att.attnum  = ANY(c.confkey)
        JOIN    information_schema.columns fmt
                  ON  fmt.table_schema = src_ns.nspname
                 AND  fmt.table_name   = src.relname
                 AND  fmt.column_name  = src_att.attname
        WHERE   c.contype = 'f'
          AND   tgt_ns.nspname  = 'public'
          AND   src_ns.nspname  = 'public'
          AND   tgt.relname     = 'companies'
          AND   tgt_att.attname = 'id'
        """
    ))
    convention_rows = await conn.execute(text(
        "SELECT table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema='public' "
        "  AND column_name IN ('company_id','tenant_id')"
    ))

    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for table_name, column_name, data_type in (
        list(fk_rows.fetchall()) + list(convention_rows.fetchall())
    ):
        if table_name == "companies":
            continue
        if not data_type or data_type.lower() not in STRING_TYPES:
            continue
        key = (table_name, column_name)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
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
    """Run the full consolidation. Returns a structured report.

    Report shape (acceptance contract for Task #969 / T-C):

    .. code-block:: python

        {
            "tables": {                       # per-table operational metric
                "users.company_id": {
                    "linhas_migradas": 0,    # rows rewritten this run
                    "linhas_orfas": 0,       # leftover legacy refs after rewrite
                },
                ...
            },
            "rewrites": {...},               # legacy alias (kept for back-compat)
            "leftovers": [...],              # legacy alias (kept for back-compat)
            "defaults_updated": [...],
            "fk_targets_companies_id": [...],
            "legacy_row_deleted": bool,
            "seeded_canonical": bool,
        }
    """
    report: dict[str, Any] = {
        "tables": {},          # {f"{table}.{column}": {linhas_migradas, linhas_orfas}}
        "rewrites": {},        # legacy alias kept for callers that already parse it
        "defaults_updated": [],
        "leftovers": [],
        "fk_targets_companies_id": [],
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

    # ---- Step 2: rewrite EVERY string FK column targeting companies.id
    #              plus convention columns (`company_id`/`tenant_id`).
    targets = await _string_company_id_columns(conn)
    for table_name, column_name in targets:
        key = f"{table_name}.{column_name}"
        result = await conn.execute(text(
            f"UPDATE {table_name} SET {column_name} = :new "
            f"WHERE {column_name} = :old"
        ), {"new": CANONICAL_DEMO_UUID, "old": LEGACY_DEMO_ID})
        migrated = int(result.rowcount or 0)
        report["tables"][key] = {
            "linhas_migradas": migrated,
            "linhas_orfas": 0,  # filled in Step 5
        }
        if migrated:
            report["rewrites"][key] = migrated

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
    for table_name, column_name in targets:
        key = f"{table_name}.{column_name}"
        leftover = await conn.execute(text(
            f"SELECT COUNT(*) FROM {table_name} "
            f"WHERE {column_name} = :old"
        ), {"old": LEGACY_DEMO_ID})
        count = int(leftover.scalar() or 0)
        report["tables"].setdefault(key, {"linhas_migradas": 0, "linhas_orfas": 0})
        report["tables"][key]["linhas_orfas"] = count
        if count:
            report["leftovers"].append((table_name, column_name, count))

    # ---- Step 5b: enumerate every FK that targets companies(id), regardless
    # of column name, for operator visibility. Note: as of T-C the
    # rewrite step (Step 2) already covers EVERY string FK to
    # ``companies.id`` (see ``_string_company_id_columns`` — UNION of FK
    # metadata and convention names), so this list now serves as a
    # post-condition audit that any future schema change which adds an
    # FK with a non-conventional column name would surface here.
    fk_rows = await conn.execute(text(
        """
        SELECT  src_ns.nspname || '.' || src.relname AS source_table,
                src_att.attname                       AS source_column
        FROM    pg_constraint c
        JOIN    pg_class       src     ON src.oid = c.conrelid
        JOIN    pg_namespace   src_ns  ON src_ns.oid = src.relnamespace
        JOIN    pg_class       tgt     ON tgt.oid = c.confrelid
        JOIN    pg_namespace   tgt_ns  ON tgt_ns.oid = tgt.relnamespace
        JOIN    pg_attribute   src_att ON src_att.attrelid = src.oid
                                       AND src_att.attnum  = ANY(c.conkey)
        JOIN    pg_attribute   tgt_att ON tgt_att.attrelid = tgt.oid
                                       AND tgt_att.attnum  = ANY(c.confkey)
        WHERE   c.contype = 'f'
          AND   tgt_ns.nspname = 'public'
          AND   tgt.relname    = 'companies'
          AND   tgt_att.attname = 'id'
        ORDER BY source_table, source_column
        """
    ))
    report["fk_targets_companies_id"] = [
        f"{row[0]}.{row[1]}" for row in fk_rows.fetchall()
    ]

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
    tables = report.get("tables") or {}
    total_migrated = sum(t["linhas_migradas"] for t in tables.values())
    total_orphans = sum(t["linhas_orfas"] for t in tables.values())
    lines.append(
        f"  per-table summary: {len(tables)} tracked | "
        f"linhas_migradas={total_migrated} | linhas_orfas={total_orphans}"
    )
    for key in sorted(tables):
        m = tables[key]["linhas_migradas"]
        o = tables[key]["linhas_orfas"]
        # only show rows that actually moved or are dirty — keeps log signal high
        if m or o:
            lines.append(
                f"    {key}: linhas_migradas={m} linhas_orfas={o}"
            )
    if total_migrated == 0 and total_orphans == 0:
        lines.append("  (db already clean — no rewrites, no orphans)")
    if report["defaults_updated"]:
        for table_name, column_name in report["defaults_updated"]:
            lines.append(f"  default refreshed: {table_name}.{column_name}")
    fks = report.get("fk_targets_companies_id") or []
    if fks:
        lines.append(f"  FK targets to companies(id) [{len(fks)} total]:")
        for ref in fks:
            lines.append(f"    {ref}")
    else:
        lines.append("  FK targets to companies(id): none discovered")
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
