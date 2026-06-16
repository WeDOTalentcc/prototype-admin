"""LLM-as-judge eval for WSI Camada 2 LLM-extractor (audit M01 rev. 18+19).

Carrega `tests/golden/wsi_layer2_extraction_v1.json` (8 casos representativos
cobrindo as dimensões F8.3) e roda o extrator REAL contra cada caso, comparando
com `expected`. Aceite: ≥7/8 casos com score ≥0.85.

Skipped por padrão: requer ANTHROPIC_API_KEY no ambiente. Ativável via
`pytest -m eval --runeval` (ou simplesmente exportando a env var).

Uso CLI standalone:
    cd lia-agent-system && python -m tests.eval.test_wsi_layer2_eval
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from app.domains.cv_screening.services.wsi_service.layer2_extractor import (
    Layer2ExtractionError,
    WSILayer2Extractor,
)
from app.domains.cv_screening.services.wsi_service.models import (
    Layer2Signals,
    WSIQuestion,
)

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "golden" / "wsi_layer2_extraction_v1.json"

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
    reason="Eval requer ANTHROPIC_API_KEY ou OPENAI_API_KEY no ambiente",
)


def _make_question(case_input: dict) -> WSIQuestion:
    return WSIQuestion(
        id=f"eval-{case_input.get('competency','x')}",
        competency=case_input.get("competency", "Liderança"),
        framework=case_input.get("framework", "CBI"),
        question_type="contextual",
        question_text=case_input["question_text"],
        weight=0.20,
        expected_signals=[],
        scoring_criteria={},
    )


def _score_case(actual: Layer2Signals, expected: dict) -> tuple[float, list[str]]:
    """Retorna (score 0..1, lista de mismatches).

    Para cada chave de `expected`:
    - sufixo `_min`/`_max` → check de range
    - confidence_min → assert >= valor
    - bool/string/int direto → match exato
    """
    actual_dict = actual.model_dump()
    checks: list[tuple[str, bool, str]] = []  # (campo, passou, detalhe)

    for key, exp_val in expected.items():
        if key.endswith("_min"):
            field = key[:-4]
            got = actual_dict.get(field)
            ok = got is not None and got >= exp_val
            checks.append((field, ok, f"got={got} expected>={exp_val}"))
        elif key.endswith("_max"):
            field = key[:-4]
            got = actual_dict.get(field)
            ok = got is not None and got <= exp_val
            checks.append((field, ok, f"got={got} expected<={exp_val}"))
        else:
            got = actual_dict.get(key)
            ok = got == exp_val
            checks.append((key, ok, f"got={got!r} expected={exp_val!r}"))

    if not checks:
        return 1.0, []
    passed = sum(1 for _, ok, _ in checks if ok)
    score = passed / len(checks)
    mismatches = [f"{f}: {d}" for f, ok, d in checks if not ok]
    return score, mismatches


async def _run_eval() -> dict:
    """Executa todos os casos e retorna sumário {passing, total, threshold, results}."""
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    threshold = data.get("threshold_score", 0.85)
    threshold_passing = data.get("threshold_passing_cases", 7)

    extractor = WSILayer2Extractor()  # usa llm_service singleton
    results = []
    for case in data["cases"]:
        case_id = case["id"]
        question = _make_question(case["input"])
        try:
            signals = await extractor.extract(question, case["input"]["response_text"])
            score, mismatches = _score_case(signals, case["expected"])
            results.append({
                "id": case_id,
                "score": score,
                "passed": score >= threshold,
                "mismatches": mismatches,
            })
        except Layer2ExtractionError as exc:
            results.append({
                "id": case_id,
                "score": 0.0,
                "passed": False,
                "mismatches": [f"Layer2ExtractionError: {exc}"],
            })

    passing = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passing": passing,
        "threshold": threshold,
        "threshold_passing": threshold_passing,
        "passed_overall": passing >= threshold_passing,
        "results": results,
    }


@pytest.mark.asyncio
@pytest.mark.eval
async def test_wsi_layer2_golden_dataset_meets_threshold():
    """Eval principal — ≥7/8 casos com score ≥0.85."""
    summary = await _run_eval()
    msg = (
        f"\nEval Camada 2: {summary['passing']}/{summary['total']} casos passaram "
        f"(threshold ≥{summary['threshold']:.2f}, mínimo {summary['threshold_passing']}).\n"
        + "\n".join(
            f"  - {r['id']}: score={r['score']:.2f} "
            + ("✅" if r["passed"] else f"❌ {r['mismatches'][:3]}")
            for r in summary["results"]
        )
    )
    print(msg)
    assert summary["passed_overall"], msg


if __name__ == "__main__":
    summary = asyncio.run(_run_eval())
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    raise SystemExit(0 if summary["passed_overall"] else 1)
