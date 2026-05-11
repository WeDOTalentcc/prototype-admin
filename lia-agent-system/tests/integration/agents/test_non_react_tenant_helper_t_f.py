"""T-F regression — `resolve_tenant_snippet_for_non_react` no FallbackReActService + Orchestrator V1.

Causa raiz endereçada (auditoria T-F):
    Após T-D/T-E (16 ReActAgents canônicos), o bug "LIA pergunta company_id no
    chat" voltou pela TERCEIRA vez porque DUAS rotas non-ReAct continuavam a
    chamar `SystemPromptBuilder.build()` direto, lendo
    `ctx.get("tenant_context_snippet", "")` sem o contrato de fail-closed do
    `TenantAwareAgentMixin`:

      1. `app/orchestrator/services/fallback_react_service.py` — fallback do
         CascadedRouter quando nenhum ReActAgent atende a intent.
      2. `app/orchestrator/orchestrator.py` — Orchestrator V1 deprecated, mas
         ainda exposto via `/api/orchestrator_routes.py` (legacy route).

    Sem snippet, o prompt renderizado pedia "qual a empresa?" — exatamente o
    sintoma que T-A/T-B/T-D foram criados pra eliminar.

Defesa canônica: helper `resolve_tenant_snippet_for_non_react` em
`app.shared.agents.tenant_aware_agent` que reutiliza a mesma lógica
fail-open/closed + telemetria Prometheus do mixin para callsites sync
non-ReAct. Este teste é a sentinela canônica — se um terceiro callsite
non-ReAct surgir e chamar SystemPromptBuilder.build sem o helper, este teste
NÃO o detecta diretamente, mas as invariantes 1+2+3 abaixo garantem que
qualquer regressão no helper ou nas duas rotas conhecidas quebra o build.
"""
from __future__ import annotations

import os

import pytest

from app.shared.agents.tenant_aware_agent import (
    get_tenant_context_metrics,
    reset_tenant_context_metrics,
    resolve_tenant_snippet_for_non_react,
)
from app.shared.exceptions.tenant_errors import MissingTenantContextError


@pytest.fixture(autouse=True)
def _reset_metrics():
    reset_tenant_context_metrics()
    yield
    reset_tenant_context_metrics()


@pytest.fixture
def _strict_off(monkeypatch):
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "false")
    monkeypatch.setenv("APP_ENV", "development")


@pytest.fixture
def _strict_on(monkeypatch):
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")


# ----------------------------------------------------------------------
# Invariante 1 (POSITIVO) — snippet upstream chega ao prompt
# ----------------------------------------------------------------------
@pytest.mark.parametrize("agent_name", ["fallback_react", "orchestrator_v1"])
def test_upstream_snippet_is_returned_and_metric_hit(_strict_off, agent_name):
    snippet = (
        "Você está assistindo **ACME Tech**, empresa do setor "
        "**Tecnologia** com **3** vagas abertas."
    )
    out = resolve_tenant_snippet_for_non_react(
        {"tenant_context_snippet": snippet, "company_id": "acme"},
        agent_name=agent_name,
    )
    assert out == snippet
    metrics = get_tenant_context_metrics()
    assert metrics[agent_name]["hit"] == 1
    assert metrics[agent_name]["fail_open"] == 0
    assert metrics[agent_name]["fail_closed"] == 0


# ----------------------------------------------------------------------
# Invariante 2 (MISS) — TenantContext sync renderiza
# ----------------------------------------------------------------------
def test_tenant_context_sync_renders_and_caches_snippet(_strict_off):
    class _FakeCtx:
        def to_prompt_snippet(self) -> str:
            return "Você está assistindo **ACME Tech**, setor **Tecnologia**."

    ctx_dict = {"tenant_context": _FakeCtx(), "company_id": "acme"}
    out = resolve_tenant_snippet_for_non_react(ctx_dict, agent_name="fallback_react")
    assert "ACME Tech" in out
    # Cacheado para o próximo callsite na mesma request
    assert ctx_dict["tenant_context_snippet"] == out
    assert get_tenant_context_metrics()["fallback_react"]["miss"] == 1


# ----------------------------------------------------------------------
# Invariante 3 (FAIL-CLOSED) — strict mode rejeita request sem tenant
# ----------------------------------------------------------------------
@pytest.mark.parametrize("agent_name", ["fallback_react", "orchestrator_v1"])
def test_strict_mode_raises_missing_tenant_context_error(_strict_on, agent_name):
    with pytest.raises(MissingTenantContextError) as excinfo:
        resolve_tenant_snippet_for_non_react(
            {"company_id": "acme"},
            agent_name=agent_name,
            company_id_raw="acme",
        )
    details = excinfo.value.details
    assert details["agent"] == agent_name
    assert details["tenant_source"] == "non_react_helper"
    metrics = get_tenant_context_metrics()
    assert metrics[agent_name]["fail_closed"] == 1
    assert metrics[agent_name]["fail_open"] == 0


# ----------------------------------------------------------------------
# Invariante 4 (FAIL-OPEN) — dev mode + sem snippet retorna "" + warning
# ----------------------------------------------------------------------
def test_dev_mode_fail_open_returns_empty_with_metric(_strict_off):
    out = resolve_tenant_snippet_for_non_react(
        {"company_id": "acme"},
        agent_name="fallback_react",
        company_id_raw="acme",
    )
    assert out == ""
    metrics = get_tenant_context_metrics()
    assert metrics["fallback_react"]["fail_open"] == 1


# ----------------------------------------------------------------------
# Invariante 5 (ANTI-PADRÃO) — duas rotas non-ReAct conhecidas usam o helper
# ----------------------------------------------------------------------
# Sentinela: se alguém remover o helper de uma das duas rotas e voltar a
# chamar SystemPromptBuilder.build com `ctx.get("tenant_context_snippet", "")`
# direto, este teste quebra. Inspecionamos o source code estático para evitar
# espelhar a lógica run-time (que dependeria de fixtures de DB pesadas).
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def _read_source(rel_path: str) -> str:
    with open(os.path.join(_REPO_ROOT, rel_path), encoding="utf-8") as fh:
        return fh.read()


def test_fallback_react_service_uses_canonical_helper():
    src = _read_source("app/orchestrator/services/fallback_react_service.py")
    assert "resolve_tenant_snippet_for_non_react" in src, (
        "FallbackReActService DEVE usar resolve_tenant_snippet_for_non_react. "
        "Origem: 3a recorrência do bug 'LIA pergunta company_id no chat' (T-F)."
    )


def test_orchestrator_v1_uses_canonical_helper():
    src = _read_source("app/orchestrator/orchestrator.py")
    assert "resolve_tenant_snippet_for_non_react" in src, (
        "Orchestrator V1 DEVE usar resolve_tenant_snippet_for_non_react. "
        "Origem: 3a recorrência do bug 'LIA pergunta company_id no chat' (T-F)."
    )
