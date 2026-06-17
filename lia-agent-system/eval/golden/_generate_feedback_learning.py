"""Generate eval/golden/feedback_learning_quality.jsonl programmatically.

Task #1300 — gate dedicado do CICLO DE APRENDIZAGEM de feedback. Espelha o
padrão dos demais geradores (``_generate_tenant_context.py``) e dos gates
``company_settings_prefill`` / ``wizard``.

O dataset é a tríade canônica (positivo / anti-padrão / fairness):
  - POSITIVO  — preferência legítima aprendida DEVE aflorar na sugestão.
  - ANTI-PADRÃO — o ciclo NUNCA pode inventar aprendizado sem base,
    re-sugerir valor rejeitado, nem vazar padrão de outro tenant.
  - FAIRNESS — aprendizado discriminatório (gênero/idade/aparência) é
    SEMPRE recusado; é a mesma barreira do ``FairnessGuard`` que o
    ``learning_loop_service`` aplica antes de persistir.

Backbone estático = determinístico (committed + usado no CI). Augmentação a
partir do banco (feedback ACUMULADO e aprovado pelo FairnessGuard) é opcional
e local:

    # backbone estático (committed / CI):
    python -m eval.golden._generate_feedback_learning

    # backbone + curadoria do banco (local; requer DATABASE_URL):
    python -m eval.golden._generate_feedback_learning --from-db --company-id <uuid>

Saída: ``eval/golden/feedback_learning_quality.jsonl`` (sobrescrito) +
sidecar ``feedback_learning_quality.meta.json``.

Gate:
    python -m eval.eval_runner --gate eval/golden/feedback_learning_quality.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUT_PATH = Path(__file__).parent / "feedback_learning_quality.jsonl"


def _curation_service():
    """Import tardio — mantém a geração estática livre de deps pesadas até ser
    necessário (mesmo espírito de lazy-import dos demais geradores)."""
    # Garante que a raiz do lia-agent-system esteja no path quando rodado como
    # ``python -m eval.golden._generate_feedback_learning`` a partir da raiz.
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from app.shared.learning.learning_golden_curation_service import (
        learning_golden_curation_service,
    )
    return learning_golden_curation_service


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o golden dataset do gate de aprendizagem de feedback (Task #1300)."
    )
    parser.add_argument(
        "--from-db",
        action="store_true",
        help="Augmenta o backbone estático com feedback curado do banco "
        "(FairnessGuard-aprovado). Requer DATABASE_URL e --company-id.",
    )
    parser.add_argument(
        "--company-id",
        default="00000000-0000-4000-a000-000000000001",
        help="Tenant para curadoria do banco (default: Demo Company canônica).",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Confiança/aceitação mínima para um padrão virar caso positivo.",
    )
    args = parser.parse_args()

    svc = _curation_service()

    extra_rows = []
    if args.from_db:
        import asyncio

        async def _load() -> list[dict]:
            from app.core.database import get_async_session_factory

            factory = get_async_session_factory()
            async with factory() as db:
                rows, blocked = await svc.curate_from_db(
                    db, args.company_id, min_confidence=args.min_confidence
                )
                if blocked:
                    print(
                        f"  [curation] FairnessGuard bloqueou {len(blocked)} "
                        f"padrão(ões) — NÃO viraram caso positivo: {blocked}"
                    )
                return rows

        extra_rows = asyncio.run(_load())
        print(f"  [curation] {len(extra_rows)} caso(s) positivo(s) curado(s) do banco.")

    rows = svc.build_dataset(extra_rows=extra_rows)
    out = svc.write_jsonl(OUT_PATH, rows)

    by_contract: dict[str, int] = {}
    for r in rows:
        by_contract[r.get("contract", "?")] = by_contract.get(r.get("contract", "?"), 0) + 1
    print(
        f"wrote {len(rows)} rows to {out} (v{svc.DATASET_VERSION}) — "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_contract.items()))
    )


if __name__ == "__main__":
    main()
