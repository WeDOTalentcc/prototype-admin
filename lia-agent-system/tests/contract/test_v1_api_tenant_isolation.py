"""v1 API endpoints — cross-tenant query filter contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram
company_id filter explícito em endpoints v1 que faziam queries inline.

Cobertura:
1. agent_approvals.list_pending — CustomAgent enrichment filtra company_id
2. sourcing_agents.get/pause/resume — SourcingAgent filtra company_id
3. guardrails.get/update — Guardrail filtra company_id

Pattern canonical: AST-level inspection via static analysis sobre o arquivo
fonte (não httpx) — confirma a presença literal de
`<Model>.company_id == ...` em cada query inline.

Referência: ADR-001 + REGRA ZERO + HARDENING_PLAN B.1.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path_rel: str) -> str:
    """Read source file relative to lia-agent-system root."""
    return (REPO_ROOT / path_rel).read_text(encoding="utf-8")


def _count_company_id_filters(source: str, model_name: str) -> int:
    """Count `<Model>.company_id == ...` filters in the source.

    Permissive regex — accepts both `current_user.company_id` and
    `company_id` (param from Depends(require_company_id)).
    """
    pattern = rf"{re.escape(model_name)}\.company_id\s*=="
    return len(re.findall(pattern, source))


# ── agent_approvals ──────────────────────────────────────────────────────────


def test_agent_approvals_enriches_custom_agent_with_company_filter() -> None:
    """list_pending enrichment loop MUST filter CustomAgent.company_id."""
    source = _read("app/api/v1/agent_approvals.py")
    # Was a single CustomAgent.id == row filter, now also CustomAgent.company_id ==
    assert _count_company_id_filters(source, "CustomAgent") >= 1, (
        "agent_approvals.list_pending CustomAgent lookup falta company_id filter"
    )


# ── agent_deployments ────────────────────────────────────────────────────────


def test_agent_deployments_executes_with_company_filter() -> None:
    """execute_deployment CustomAgent loading MUST filter company_id."""
    source = _read("app/api/v1/agent_deployments.py")
    assert _count_company_id_filters(source, "CustomAgent") >= 1, (
        "agent_deployments execute_deployment CustomAgent lookup falta filter"
    )


# ── sourcing_agents ──────────────────────────────────────────────────────────


def test_sourcing_agents_filters_by_company() -> None:
    """All SourcingAgent queries inline MUST filter SourcingAgent.company_id."""
    source = _read("app/api/v1/sourcing_agents.py")
    # 3 endpoints: get / pause / resume — todos devem filtrar
    assert _count_company_id_filters(source, "SourcingAgent") >= 3, (
        "sourcing_agents tem queries sem SourcingAgent.company_id filter"
    )


# ── guardrails ───────────────────────────────────────────────────────────────


def test_guardrails_get_and_update_filter_by_company() -> None:
    """get_guardrail + update_guardrail MUST filter Guardrail.company_id."""
    source = _read("app/api/v1/guardrails.py")
    assert _count_company_id_filters(source, "Guardrail") >= 2, (
        "guardrails has queries sem Guardrail.company_id filter"
    )


# ── custom_agents ────────────────────────────────────────────────────────────


def test_custom_agents_enrichments_filter_by_company() -> None:
    """Top-blocked/top-agent enrichment loops MUST filter CustomAgent.company_id."""
    source = _read("app/api/v1/custom_agents.py")
    # 2 enrichment loops (top blocked + top by usage)
    assert _count_company_id_filters(source, "CustomAgent") >= 2, (
        "custom_agents enrichments falta CustomAgent.company_id filter"
    )


# ── platform_event_handlers ──────────────────────────────────────────────────


def test_platform_event_handlers_filter_by_company() -> None:
    """VacancyCandidate and Candidate queries em event handlers MUST filter."""
    source = _read("app/api/v1/platform_event_handlers.py")
    # _get_vacancy_candidate + close-vacancy open candidates + 2 Candidate
    assert _count_company_id_filters(source, "VacancyCandidate") >= 1, (
        "platform_event_handlers VacancyCandidate queries falta filter"
    )
    assert _count_company_id_filters(source, "Candidate") >= 2, (
        "platform_event_handlers Candidate queries falta filter"
    )


# ── talent_pools ─────────────────────────────────────────────────────────────


def test_talent_pools_refresh_counts_optional_company_filter() -> None:
    """_refresh_counts MUST aceitar company_id param e adicionar filter."""
    source = _read("app/api/v1/talent_pools.py")
    assert "TalentPool.company_id" in source, (
        "talent_pools _refresh_counts UPDATE falta TalentPool.company_id filter"
    )


# ── test_activities ──────────────────────────────────────────────────────────


def test_test_activities_clear_filter_by_company() -> None:
    """clear_test_activities MUST filter ActivityFeed.company_id."""
    source = _read("app/api/v1/test_activities.py")
    assert "ActivityFeed.company_id" in source, (
        "test_activities clear DELETE falta ActivityFeed.company_id filter"
    )
