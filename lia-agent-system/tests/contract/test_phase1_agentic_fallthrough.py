"""#3 (2026-06-04): Phase 1 → agentic fall-through para ações prefer-agentic.

Quando o Phase 1 ActionExecutor retorna needs_params para search_candidates, o
orquestrador deve DEFERIR ao agentic loop (LLM extrai o critério do NL e chama a
tool) em vez de perguntar "Quais critérios de busca?". Restrito à allowlist —
ações que legitimamente exigem param (agendar entrevista) NÃO deferem.
"""
from types import SimpleNamespace

from app.orchestrator.execution.main_orchestrator import (
    _defer_needs_params_to_agentic,
    PREFER_AGENTIC_ON_MISSING_PARAMS,
)


def test_search_candidates_needs_params_defers():
    r = SimpleNamespace(needs_params=True, action_type="search_candidates")
    assert _defer_needs_params_to_agentic(r) is True


def test_search_candidates_executed_does_not_defer():
    r = SimpleNamespace(needs_params=False, action_type="search_candidates")
    assert _defer_needs_params_to_agentic(r) is False


def test_other_action_needs_params_does_not_defer():
    # agendar entrevista precisa de data → DEVE perguntar (não defere)
    r = SimpleNamespace(needs_params=True, action_type="schedule_interview")
    assert _defer_needs_params_to_agentic(r) is False


def test_missing_attrs_is_safe():
    assert _defer_needs_params_to_agentic(SimpleNamespace()) is False


def test_allowlist_contains_search_candidates():
    assert "search_candidates" in PREFER_AGENTIC_ON_MISSING_PARAMS
