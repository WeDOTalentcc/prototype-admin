"""
P0.c — Sanitize corrupted CompanyHiringPolicy gate slots (audit 2026-06-01).

Root cause: the narrative Políticas UI wrote free-text strings ("Sim"/"Não"/
prose) into TYPED gate slots (bool/int) of the 5 JSON blocks, via a write path
that did not validate types (fixed in P0.a). Consumers read raw values where
the string "Não" is Python-truthy -> automations silently turned ON. This script
normalizes EXISTING rows: any bool/int gate slot holding a non-bool/non-int value
is coerced via the canonical ``coerce_bool``/``coerce_int`` helpers (P0.b).

Idempotent: re-running after a clean pass finds nothing. Non-destructive: writes
a timestamped JSON backup of every changed row's blocks BEFORE applying.

Expected types are derived from BLOCK_SCHEMAS (single source of truth) — not a
hand-maintained list — so this stays in lockstep with the Pydantic contract.

## Run

    # Dry-run (default — reports, writes nothing):
    python3 scripts/sanitize_hiring_policy_corruption.py

    # Apply (writes backup file, then normalizes + commits):
    python3 scripts/sanitize_hiring_policy_corruption.py --apply
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger("sanitize_hiring_policy")

_BACKUP_DIR = os.path.join(_PROJECT_ROOT, ".policy_sanitize_backups")


def _detect_fixes_for_block(schema, block_name: str, block_data: dict) -> list[dict]:
    """Return list of {key, before, after, kind} for type-mismatched gate slots."""
    from app.shared.policy_helper import coerce_bool, coerce_int

    fixes: list[dict] = []
    if not isinstance(block_data, dict):
        return fixes
    for key, value in block_data.items():
        field = schema.model_fields.get(key)
        if field is None:
            continue  # unknown/legacy key — leave untouched (P0.a forbids new ones)
        ann = field.annotation
        if ann is bool and not isinstance(value, bool):
            fixes.append({"key": key, "before": value, "after": coerce_bool(value), "kind": "bool"})
        elif ann is int and (not isinstance(value, int) or isinstance(value, bool)):
            fixes.append({"key": key, "before": value, "after": coerce_int(value), "kind": "int"})
    return fixes


async def main(apply: bool = False) -> dict:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.schemas.company_hiring_policy import BLOCK_SCHEMAS
    from lia_models.company_hiring_policy import CompanyHiringPolicy

    summary: dict = {"checked": 0, "corrupted_rows": 0, "fixes": 0, "apply": apply, "details": [], "errors": []}
    backups: list[dict] = []

    async with AsyncSessionLocal() as db:
        rows = list((await db.execute(select(CompanyHiringPolicy))).scalars().all())
        summary["checked"] = len(rows)

        for policy in rows:
            row_fixes: dict[str, list[dict]] = {}
            original_blocks: dict[str, dict] = {}
            try:
                for block_name, schema in BLOCK_SCHEMAS.items():
                    block_data = getattr(policy, block_name, None) or {}
                    fixes = _detect_fixes_for_block(schema, block_name, block_data)
                    if fixes:
                        row_fixes[block_name] = fixes
                        original_blocks[block_name] = dict(block_data)

                if not row_fixes:
                    continue

                summary["corrupted_rows"] += 1
                summary["fixes"] += sum(len(f) for f in row_fixes.values())
                summary["details"].append({"company_id": policy.company_id, "fixes": row_fixes})

                if apply:
                    backups.append({"company_id": policy.company_id, "blocks": original_blocks})
                    for block_name, fixes in row_fixes.items():
                        new_block = dict(getattr(policy, block_name) or {})
                        for f in fixes:
                            new_block[f["key"]] = f["after"]
                        # T-1169: NOVO dict — Column(JSON) puro não rastreia mutação in-place.
                        setattr(policy, block_name, new_block)
            except Exception as exc:  # noqa: BLE001 — fault-isolated per row
                summary["errors"].append({"company_id": getattr(policy, "company_id", "?"), "error": str(exc)[:200]})
                logger.warning("row %s failed: %s", getattr(policy, "company_id", "?"), exc)

        if apply and backups:
            os.makedirs(_BACKUP_DIR, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup_path = os.path.join(_BACKUP_DIR, f"policy_backup_{stamp}.json")
            with open(backup_path, "w", encoding="utf-8") as fh:
                json.dump(backups, fh, ensure_ascii=False, indent=2, default=str)
            summary["backup_path"] = backup_path
            await db.commit()
            logger.info("Applied %d fixes across %d rows. Backup: %s",
                        summary["fixes"], summary["corrupted_rows"], backup_path)
        elif apply:
            logger.info("Nothing to fix — DB already clean.")

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    apply = "--apply" in sys.argv
    result = asyncio.run(main(apply=apply))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    sys.exit(1 if result["errors"] else 0)
