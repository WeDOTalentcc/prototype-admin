"""Backfill `wsi_response_analyses.transparency_extras` for legacy rows.

Audit task #534 — A coluna JSONB `transparency_extras` foi introduzida na
task #528 (G23-02 / G23-03) para expor selo de qualidade degradada,
flags estruturadas e breakdown de penalidades/bônus (LGPD Art. 20 / EU
AI Act §13). Análises gravadas antes desse PR ficam com a coluna NULL —
a API serve defaults seguros, mas relatórios históricos não exibem o
breakdown granular nem o banner de qualidade degradada.

Este script percorre todas as análises com `transparency_extras IS NULL`
e recalcula o payload via `calculate_wsi_deterministic` (Camada 1
determinística) usando os campos persistidos (response_text, framework,
expected_signals, scoring_criteria). A Camada 2 (LLM) NÃO é executada —
o backfill marca `is_llm_fallback=True` e adiciona
`layer2_degraded_reason="backfill_legacy_record_layer2_unavailable"`
para que o banner de qualidade degradada apareça e auditores saibam
que o registro foi reconstruído fora do fluxo original.

É idempotente:
  * SELECT filtra por `transparency_extras IS NULL`, então re-executar
    não toca registros já populados.
  * UPDATE usa o `id` da análise individual.
  * Falhas individuais são logadas e não interrompem o lote.

Uso:
    cd lia-agent-system && python scripts/backfill_wsi_transparency_extras.py

Variáveis opcionais:
  BACKFILL_BATCH_SIZE   tamanho do lote por commit (default 200)
  BACKFILL_DRY_RUN      "1" para apenas inspecionar o PRIMEIRO lote sem UPDATE
                        (preview/sample — não percorre a tabela inteira; use
                        sem dry-run para o backfill real)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_transparency_extras")

BACKFILL_REASON = "backfill_legacy_record_layer2_unavailable"


def _category_from_framework(framework: str | None) -> str | None:
    if framework in ("Bloom", "Dreyfus"):
        return "technical"
    if framework in ("CBI", "BigFive"):
        return "behavioral"
    return None


def _coerce_jsonb(value: Any) -> Any:
    """JSONB pode vir como dict/list (driver decode) ou string."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def _build_extras_for_row(row: Any) -> dict[str, Any]:
    """Recalcula `transparency_extras` usando o scorer determinístico."""
    from app.domains.cv_screening.services.wsi_deterministic_scorer import (
        build_transparency_extras_payload,
        calculate_wsi_deterministic,
    )

    framework = row.framework or "CBI"
    derived_category = _category_from_framework(framework)
    question_type = derived_category if derived_category in ("technical", "behavioral") else "technical"

    scoring_criteria = _coerce_jsonb(row.scoring_criteria) or {}
    expected_signals = _coerce_jsonb(row.expected_signals) or []

    bloom_expected = scoring_criteria.get("bloom_expected") if isinstance(scoring_criteria, dict) else None
    dreyfus_expected = scoring_criteria.get("dreyfus_expected") if isinstance(scoring_criteria, dict) else None
    trait_signals_expected = len(expected_signals) if expected_signals else None

    result = calculate_wsi_deterministic(
        response_text=row.response_text or "",
        competency_name=row.competency or "",
        question_framework=framework,
        question_type=question_type,
        bloom_expected=bloom_expected,
        dreyfus_expected=dreyfus_expected,
        trait_signals_expected=trait_signals_expected,
        layer2_signals=None,
    )

    return build_transparency_extras_payload(
        result,
        layer2_degraded_reason=BACKFILL_REASON,
        extra_degraded_reasons=["backfill_recalculated"],
        force_llm_fallback=True,
    )


def _build_select_sql(skip_ids: list[Any]) -> Any:
    """Audit task #534 — exclui IDs já marcados como falha persistente nesta
    execução para evitar loop infinito quando uma janela inteira (>= batch_size)
    contém apenas linhas que sempre falham em ``_build_extras_for_row``."""
    skip_clause = "AND ra.id <> ALL(:skip_ids)" if skip_ids else ""
    return text(
        f"""
        SELECT ra.id, ra.response_text, ra.competency,
               q.framework, q.expected_signals, q.scoring_criteria
        FROM wsi_response_analyses ra
        JOIN wsi_questions q ON q.id = ra.question_id
        JOIN wsi_sessions s ON s.id = ra.session_id
        WHERE ra.transparency_extras IS NULL
          AND (s.status = 'completed' OR s.completed_at IS NOT NULL)
          {skip_clause}
        ORDER BY ra.created_at NULLS LAST, ra.id
        LIMIT :limit
        """
    )

UPDATE_SQL = text(
    """
    UPDATE wsi_response_analyses
    SET transparency_extras = CAST(:extras AS jsonb)
    WHERE id = :id AND transparency_extras IS NULL
    """
)


async def run_backfill(batch_size: int = 200, dry_run: bool = False) -> dict[str, int]:
    from app.core.database import AsyncSessionLocal

    total_seen = 0
    total_updated = 0
    total_failed = 0
    skip_ids: list[Any] = []  # Audit task #534 — quarentena de falhas persistentes.

    while True:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"limit": batch_size}
            if skip_ids:
                params["skip_ids"] = skip_ids
            rows = (
                await session.execute(_build_select_sql(skip_ids), params)
            ).fetchall()
            if not rows:
                break

            updates: list[dict[str, Any]] = []
            for row in rows:
                total_seen += 1
                try:
                    extras = _build_extras_for_row(row)
                    updates.append({"id": row.id, "extras": json.dumps(extras)})
                except Exception as exc:  # noqa: BLE001
                    total_failed += 1
                    skip_ids.append(row.id)
                    logger.exception(
                        "Failed to compute transparency_extras for analysis id=%s: %s",
                        row.id, exc,
                    )

            if dry_run:
                logger.info(
                    "[dry-run] batch ready: would update %d rows (failed=%d)",
                    len(updates), total_failed,
                )
                # Em dry-run não há UPDATE; precisamos sair para não loopar
                # infinitamente sobre o mesmo conjunto de NULLs.
                return {
                    "seen": total_seen,
                    "updated": 0,
                    "failed": total_failed,
                    "dry_run": True,
                }

            batch_updated = 0
            for payload in updates:
                try:
                    result = await session.execute(UPDATE_SQL, payload)
                    # Audit task #534 — métrica precisa: conta apenas linhas
                    # realmente afetadas (rowcount=0 quando o UPDATE bate na
                    # guarda `transparency_extras IS NULL`, evitando inflar o
                    # contador em corridas concorrentes / re-execução parcial).
                    affected = result.rowcount or 0
                    batch_updated += affected
                    if affected == 0:
                        skip_ids.append(payload["id"])
                except Exception as exc:  # noqa: BLE001
                    total_failed += 1
                    skip_ids.append(payload["id"])
                    logger.exception(
                        "UPDATE failed for analysis id=%s: %s", payload["id"], exc,
                    )
            total_updated += batch_updated
            await session.commit()
            logger.info(
                "Batch committed: updated=%d failed=%d (running totals seen=%d updated=%d failed=%d skipped=%d)",
                batch_updated, total_failed, total_seen, total_updated, total_failed, len(skip_ids),
            )

            if len(rows) < batch_size:
                break

    return {
        "seen": total_seen,
        "updated": total_updated,
        "failed": total_failed,
        "dry_run": False,
    }


async def main() -> None:
    batch_size = int(os.environ.get("BACKFILL_BATCH_SIZE", "200"))
    dry_run = os.environ.get("BACKFILL_DRY_RUN") == "1"

    logger.info(
        "Starting transparency_extras backfill (batch_size=%d, dry_run=%s)",
        batch_size, dry_run,
    )
    summary = await run_backfill(batch_size=batch_size, dry_run=dry_run)
    logger.info("Backfill complete: %s", summary)


if __name__ == "__main__":
    asyncio.run(main())
