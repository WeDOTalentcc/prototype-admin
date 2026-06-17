"""
One-time data migration — Task #353.

Copies any per-tenant `llm_provider` / `llm_fallback_order` entries from
`app/tools/tool_permissions.yaml` into the `tenant_llm_configs` database
table, in line with ADR-016. Idempotent: re-running on a clean YAML is a
no-op; existing DB rows are preserved (only missing rows are inserted,
and only `primary_provider` / `fallback_order` are filled in — provider
API keys / routing are untouched).

Usage:
    python -m scripts.migrate_yaml_llm_to_db
    python -m scripts.migrate_yaml_llm_to_db --dry-run
    python -m scripts.migrate_yaml_llm_to_db --yaml /path/to/tool_permissions.yaml
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger("migrate_yaml_llm_to_db")


def _load_yaml_tenants(yaml_path: Path) -> dict[str, dict]:
    import yaml

    if not yaml_path.exists():
        logger.warning("YAML file not found: %s", yaml_path)
        return {}
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    tenants = raw.get("tenants") or {}
    out: dict[str, dict] = {}
    for tenant_id, cfg in tenants.items():
        if not isinstance(cfg, dict):
            continue
        provider = cfg.get("llm_provider")
        fallback = cfg.get("llm_fallback_order")
        if provider or fallback:
            out[tenant_id] = {
                "primary_provider": provider or "gemini",
                "fallback_order": list(fallback) if fallback else [
                    "gemini",
                    "claude",
                    "openai",
                ],
            }
    return out


async def _migrate(
    yaml_path: Path, dry_run: bool, created_by: str
) -> tuple[int, int, int]:
    """Returns (found, inserted, skipped_existing)."""
    tenants = _load_yaml_tenants(yaml_path)
    if not tenants:
        logger.info("No per-tenant LLM entries found in %s — nothing to do.", yaml_path)
        return 0, 0, 0

    logger.info("Found %d tenant entries in YAML.", len(tenants))

    if dry_run:
        for tid, cfg in tenants.items():
            logger.info(
                "[dry-run] would upsert tenant=%s provider=%s fallback=%s",
                tid,
                cfg["primary_provider"],
                cfg["fallback_order"],
            )
        return len(tenants), 0, 0

    # Imports kept lazy so --dry-run works without a configured DB.
    from lia_config.database import AsyncSessionLocal
    from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository

    inserted = 0
    skipped = 0
    async with AsyncSessionLocal() as session:
        repo = LlmConfigRepository(session)
        for tenant_id, cfg in tenants.items():
            existing = await repo.get_by_company_id(tenant_id)
            if existing:
                logger.info(
                    "Skipping tenant=%s — already has a tenant_llm_configs row.",
                    tenant_id,
                )
                skipped += 1
                continue
            await repo.upsert(
                company_id=tenant_id,
                primary_provider=cfg["primary_provider"],
                fallback_order=cfg["fallback_order"],
                providers_dict={},
                routing={},
                created_by=created_by,
            )
            inserted += 1
        await session.commit()
    return len(tenants), inserted, skipped


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    default_yaml = (
        Path(__file__).resolve().parent.parent
        / "app"
        / "tools"
        / "tool_permissions.yaml"
    )
    parser.add_argument("--yaml", type=Path, default=default_yaml)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--created-by", default="migrate_yaml_llm_to_db")
    args = parser.parse_args()

    found, inserted, skipped = asyncio.run(
        _migrate(args.yaml, args.dry_run, args.created_by)
    )
    logger.info(
        "Done. found=%d inserted=%d skipped_existing=%d", found, inserted, skipped
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
