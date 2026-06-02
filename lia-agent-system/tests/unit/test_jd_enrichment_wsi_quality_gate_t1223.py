"""Task #1223 — eval gate determinístico de qualidade WSI da JD enriquecida.

Golden dataset: ``eval/golden/jd_enrichment_wsi_quality.jsonl``. Para cada caso,
roda o enriquecimento REAL (``enrich_job_description``, catálogos locais — sem
DB nem rede) seguido de ``build_wsi_persistence_payload`` e assere:

  * o gate de mínimos (9 técnicas + 5 comportamentais) bate o esperado;
  * cenários que devem enriquecer atingem ``min_wsi_quality_score``.

Gate: TODOS os casos devem passar (pass rate 1.0). Rodável via
``pytest tests/unit/test_jd_enrichment_wsi_quality_gate_t1223.py``.
"""
import json
from pathlib import Path

import pytest

from app.domains.job_management.services.jd_enrichment_service import (
    build_wsi_persistence_payload,
    jd_enrichment_service,
)
from app.schemas.jd_enrichment import EnrichmentRequest

_GOLDEN = (
    Path(__file__).resolve().parents[2]
    / "eval"
    / "golden"
    / "jd_enrichment_wsi_quality.jsonl"
)


def _load_cases() -> list[dict]:
    cases: list[dict] = []
    with _GOLDEN.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def test_golden_file_present_and_nonempty():
    cases = _load_cases()
    assert len(cases) >= 5, "golden dataset deve ter ao menos 5 cenários"


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
async def test_jd_enrichment_wsi_quality_gate(case: dict):
    request = EnrichmentRequest(
        company_id="00000000-0000-4000-a000-000000000001",
        title=case["title"],
        seniority=case.get("seniority"),
        department=case.get("department"),
        detected_responsibilities=case.get("detected_responsibilities", []),
        detected_technical_skills=case.get("detected_technical_skills", []),
        detected_behavioral_competencies=case.get("detected_behavioral_competencies", []),
        raw_input=case.get("raw_input"),
    )

    response = await jd_enrichment_service.enrich_job_description(request, db=None)
    assert response.success and response.enriched_jd is not None, (
        f"[{case['id']}] enriquecimento falhou: {response.error}"
    )

    payload = build_wsi_persistence_payload(
        response.enriched_jd, original_description=case.get("raw_input")
    )

    assert payload["meets_wsi_minimums"] is case["expected_meets_minimums"], (
        f"[{case['id']}] gate de mínimos divergiu: "
        f"tech={len(payload['technical_skills'])}, "
        f"behav={len(payload['behavioral_competencies'])}"
    )

    min_score = case.get("min_wsi_quality_score")
    if case["expected_meets_minimums"] and min_score is not None:
        assert payload["wsi_quality_score"] >= min_score, (
            f"[{case['id']}] qualidade WSI {payload['wsi_quality_score']} "
            f"abaixo do mínimo {min_score}"
        )
