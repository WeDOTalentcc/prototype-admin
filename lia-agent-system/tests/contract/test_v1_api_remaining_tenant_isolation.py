"""v1 API remaining endpoints — cross-tenant query filter contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram filtros
``Model.company_id == company_id`` em endpoints v1 que faziam queries inline
sem multi-tenancy enforcement.

Cobertura:
1. agent_quality.get_evaluation_detail — AgentQualityEvaluation filtra company_id
2. ai_transparency list query — AutomatedDecisionExplanation dynamic builder
   tem TENANT-EXEMPT marker (conditions[0] já é company_id).

Estratégia: source-level AST inspection — não httpx (sem fixtures de DB).

Referência: ADR-001 + REGRA ZERO + HARDENING_PLAN B.1.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path_rel: str) -> str:
    return (REPO_ROOT / path_rel).read_text(encoding="utf-8")


def _count_company_id_filters(source: str, model_name: str) -> int:
    pattern = rf"{re.escape(model_name)}\.company_id\s*=="
    return len(re.findall(pattern, source))


# ── agent_quality ────────────────────────────────────────────────────────────


def test_agent_quality_get_evaluation_detail_filters_by_company() -> None:
    """get_evaluation_detail MUST filter AgentQualityEvaluation.company_id
    (REGRA ZERO — sem filtro, qualquer recruiter lia avaliação de outro
    tenant via /agent-quality/{evaluation_id})."""
    source = _read("app/api/v1/agent_quality.py")
    assert _count_company_id_filters(source, "AgentQualityEvaluation") >= 1, (
        "agent_quality.get_evaluation_detail falta "
        "AgentQualityEvaluation.company_id filter"
    )


def test_agent_quality_get_evaluation_detail_handler_filters_explicitly() -> None:
    """The dedicated get_evaluation_detail handler MUST contain the literal
    ``AgentQualityEvaluation.company_id == company_id`` filter. The previous
    code claimed the sensor was a false positive while in fact the WHERE
    clause had only ``id == evaluation_id`` — a real cross-tenant leak.

    Lock the filter so a future refactor cannot silently remove it."""
    source = _read("app/api/v1/agent_quality.py")
    # Locate the specific handler block
    handler_start = source.find("async def get_evaluation_detail(")
    assert handler_start >= 0
    next_def = source.find("async def ", handler_start + 1)
    if next_def < 0:
        next_def = len(source)
    handler_body = source[handler_start:next_def]
    assert "AgentQualityEvaluation.company_id == company_id" in handler_body, (
        "get_evaluation_detail handler precisa do filter literal "
        "'AgentQualityEvaluation.company_id == company_id' no select."
    )


# ── ai_transparency ─────────────────────────────────────────────────────────


def test_ai_transparency_dynamic_builder_has_exempt_marker() -> None:
    """ai_transparency list endpoint uses dynamic ``conditions`` list whose
    first element is ``AutomatedDecisionExplanation.company_id == company_uuid``
    (composed near top of handler). Both count + list queries need
    TENANT-EXEMPT markers in window since AST sensor cannot trace dynamic
    builders."""
    source = _read("app/api/v1/ai_transparency.py")
    # Marker must be present
    assert source.count("TENANT-EXEMPT") >= 2, (
        "ai_transparency precisa de TENANT-EXEMPT markers no count + list "
        "queries que usam and_(*conditions)"
    )
    # The actual conditions[0] must still be the company_id filter
    assert _count_company_id_filters(source, "AutomatedDecisionExplanation") >= 1, (
        "AutomatedDecisionExplanation.company_id condition foi removida — "
        "marker EXEMPT sem o filter underlying é vazamento real."
    )
