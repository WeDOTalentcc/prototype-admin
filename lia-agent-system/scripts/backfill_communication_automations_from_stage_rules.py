"""
WT-2022 P3.2: Backfill communication_automations from stage_automation_rules legacy.

Script idempotente — pode rodar multiplas vezes sem efeito colateral. Reusa
StageRuleAdapter canonical (`upsert_communication_automation_from_stage_rule`)
para evitar duplicacao de logica e garantir o MESMO contrato de schema bridge
usado em CREATE/UPDATE pelo endpoint UI legacy.

## Match strategy

Mesmo (`company_id`, `trigger_type`, `name`) ja existente em
`communication_automations` -> UPDATE in-place (preserva ID + audit trail).
Sem match -> INSERT.

## Falhas nao-fatais por rule

Cada rule e processada isoladamente; erro em uma nao aborta o batch. Erros
sao acumulados em `summary["errors"]` com `rule_id` + mensagem truncada,
para reconciliacao manual posterior.

## Como rodar

    # Dry-run (so conta, nao escreve):
    python3 scripts/backfill_communication_automations_from_stage_rules.py --dry-run

    # Run real:
    python3 scripts/backfill_communication_automations_from_stage_rules.py

## Esperado em prod

    Backfill result: {
        'checked': <N rules ativas>,
        'synced': <M upserts feitos>,
        'skipped': 0,            # so > 0 em dry-run
        'errors': []
    }

## Reference

- WT-2022 P3.2 — stage_automation_rules -> communication_automations migration
- `app/domains/automation/services/stage_rule_adapter.py` (logica canonical)
- `app/api/v1/automation_rules.py` (UI legacy endpoints que tambem dual-write)
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

# Permitir rodar como `python3 scripts/backfill_*.py` direto do root
# lia-agent-system/ sem precisar de PYTHONPATH externo.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger("backfill_communication_automations")


async def main(dry_run: bool = False) -> dict:
    """Backfill ativo. Retorna summary dict para logs/CI."""
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.stage_rule_adapter import StageRuleAdapter
    from lia_models.automation import StageAutomationRule

    summary: dict = {
        "checked": 0,
        "synced": 0,
        "skipped": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(StageAutomationRule).where(StageAutomationRule.is_active.is_(True))
        )
        rules = list(result.scalars().all())
        summary["checked"] = len(rules)

        logger.info(
            "[WT-2022 P3.2 backfill] %d active stage_automation_rules to process "
            "(dry_run=%s)",
            len(rules),
            dry_run,
        )

        for rule in rules:
            try:
                if dry_run:
                    summary["skipped"] += 1
                    continue
                mirror = await StageRuleAdapter.upsert_communication_automation_from_stage_rule(
                    db, rule
                )
                if mirror is not None:
                    summary["synced"] += 1
                else:
                    # Adapter retornou None — log warning embutido la dentro.
                    summary["errors"].append(
                        {
                            "rule_id": str(rule.id),
                            "error": "adapter returned None (see logs)",
                        }
                    )
            except Exception as exc:  # noqa: BLE001 — fault-isolated per rule
                summary["errors"].append(
                    {"rule_id": str(rule.id), "error": str(exc)[:200]}
                )
                logger.warning(
                    "[WT-2022 P3.2 backfill] rule %s failed: %s",
                    rule.id,
                    exc,
                )

        if not dry_run:
            await db.commit()
            logger.info(
                "[WT-2022 P3.2 backfill] commit done: synced=%d errors=%d",
                summary["synced"],
                len(summary["errors"]),
            )

    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    dry_run = "--dry-run" in sys.argv
    result = asyncio.run(main(dry_run=dry_run))
    print(f"Backfill result: {result}")
    # Exit code 1 se houve erros — sinaliza CI/cron.
    sys.exit(1 if result["errors"] else 0)
