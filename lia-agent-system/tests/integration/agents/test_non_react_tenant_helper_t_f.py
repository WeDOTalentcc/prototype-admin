"""T-F + T-G regression — `resolve_tenant_snippet_for_non_react` canonical
allowlist for NON-ReAct callsites of ``SystemPromptBuilder.build``.

Causa raiz endereçada (auditoria T-F + T-G — Task #978):
    Após T-D/T-E (16 ReActAgents canônicos), o bug "LIA pergunta company_id
    no chat" voltou pela TERCEIRA vez porque rotas non-ReAct continuavam a
    chamar ``SystemPromptBuilder.build()`` direto, lendo
    ``ctx.get("tenant_context_snippet", "")`` sem o contrato de fail-closed
    do ``TenantAwareAgentMixin``. T-F endereçou os 2 callsites mais críticos
    (``fallback_react_service.py`` + ``orchestrator.py`` V1). T-G (Task #978)
    fechou a porta para a 4a recorrência: enumera **todos** os módulos que
    chamam ``SystemPromptBuilder.build`` com ``tenant_context_snippet`` e os
    classifica em uma de duas listas canônicas:

      * ``MUST_USE_HELPER`` — DEVEM importar ``resolve_tenant_snippet_for_non_react``.
      * ``OUT_OF_SCOPE_DOCUMENTED`` — NÃO usam o helper por motivo escrito
        e auditável (ReActAgent coberto pelo mixin, runtime de Agent Studio
        com arquitetura própria, etc.).

    A sentinela ``test_no_unaudited_system_prompt_builder_callsite`` quebra
    o build se um terceiro caminho non-ReAct passar ``tenant_context_snippet``
    sem aparecer em nenhuma das duas listas — forçando o autor do PR a
    classificar conscientemente.
"""
from __future__ import annotations

import os
import re

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


# ----------------------------------------------------------------------
# T-G (Task #978) — Inventário canônico de callsites NON-ReAct
# ----------------------------------------------------------------------
# DEVEM usar ``resolve_tenant_snippet_for_non_react``. Se o módulo deixa
# de importar/usar o helper, ``test_must_use_helper_modules_import_helper``
# quebra. Se um módulo NOVO chamar ``SystemPromptBuilder.build`` com
# ``tenant_context_snippet`` sem aparecer aqui nem em
# ``OUT_OF_SCOPE_DOCUMENTED``, ``test_no_unaudited_system_prompt_builder_callsite``
# quebra — forçando o autor do PR a classificar.
MUST_USE_HELPER: dict[str, str] = {
    "app/orchestrator/services/fallback_react_service.py": (
        "Fallback do CascadedRouter quando nenhum ReActAgent atende a intent "
        "(T-F R2)."
    ),
    "app/orchestrator/orchestrator.py": (
        "Orchestrator V1 deprecated mas ainda exposto via "
        "/api/orchestrator_routes.py (T-F R3)."
    ),
    "app/api/v1/chat.py": (
        "SSE direto (LIA-P05 desligado): _sse_event_generator chama "
        "SystemPromptBuilder.build com tenant_context_snippet — T-G migra "
        "a resolução para o helper canônico."
    ),
    "app/api/v1/lia_assistant/conversational.py": (
        "_build_conversational_prompt (chat conversacional do wizard) "
        "passa tenant_context_snippet — T-G migra para o helper."
    ),
    "app/domains/registry.py": (
        "_YamlDomainProxy.get_system_prompt (proxy para domains definidos via "
        "YAML, NON-ReAct) — T-G migra para o helper."
    ),
}

# NÃO usam o helper por motivo auditável. Cada entrada exige justificativa
# escrita; sem isso o autor do PR provavelmente NÃO refletiu sobre o impacto.
OUT_OF_SCOPE_DOCUMENTED: dict[str, str] = {
    "app/domains/candidate_self_service/agents/candidate_react_agent.py": (
        "É um ReActAgent canônico (T-D inventory, 16 agentes). O override de "
        "_get_system_prompt aqui existe pela Audit N (Sprint 2 Phase 3.1 P0) "
        "para não vazar a persona recruiter para candidatos — o snippet de "
        "tenant flui via TenantAwareAgentMixin async (_process_langgraph), "
        "não pelo path sync. Coberto por T-D + T-E contracts 1+2."
    ),
    "app/domains/agent_studio/custom_agent_runtime.py": (
        "Runtime de custom agents do Agent Studio — arquitetura separada "
        "explicitamente fora do escopo T-D/T-F (ver replit.md → "
        "TenantAwareAgent Roll-out, caso especial #5). Custom agents têm "
        "ciclo próprio de validação de tenant via AgentTemplate.permissions."
    ),
}


def test_must_use_helper_modules_import_helper():
    """Cada módulo em ``MUST_USE_HELPER`` DEVE importar/chamar o helper."""
    failures: list[str] = []
    for rel_path, motivo in MUST_USE_HELPER.items():
        src = _read_source(rel_path)
        if "resolve_tenant_snippet_for_non_react" not in src:
            failures.append(f"{rel_path}: {motivo}")
    assert not failures, (
        "Os módulos abaixo estão em MUST_USE_HELPER mas NÃO chamam "
        "resolve_tenant_snippet_for_non_react. Origem: 3a recorrência do bug "
        "'LIA pergunta company_id no chat'. Migrar para o helper canônico ou "
        "mover para OUT_OF_SCOPE_DOCUMENTED com motivo escrito.\n\n"
        + "\n".join(failures)
    )


def test_must_use_and_out_of_scope_lists_are_disjoint():
    """Sanidade: nenhum módulo aparece nas duas listas."""
    overlap = set(MUST_USE_HELPER.keys()) & set(OUT_OF_SCOPE_DOCUMENTED.keys())
    assert not overlap, (
        "Módulos não podem estar em MUST_USE_HELPER e OUT_OF_SCOPE_DOCUMENTED "
        f"ao mesmo tempo: {sorted(overlap)}"
    )


def test_out_of_scope_modules_have_non_empty_motivation():
    """Sanidade: justificativa não pode ser vazia/placeholder."""
    bad = [p for p, motivo in OUT_OF_SCOPE_DOCUMENTED.items() if len(motivo.strip()) < 40]
    assert not bad, (
        "OUT_OF_SCOPE_DOCUMENTED exige motivo escrito (>=40 chars) para evitar "
        f"placeholders tipo 'TODO' / 'fix later'. Faltam motivos em: {bad}"
    )


# ----------------------------------------------------------------------
# Sentinela canônica (T-G) — terceiro callsite NON-ReAct sem classificação
# quebra o build
# ----------------------------------------------------------------------
# Estratégia: varremos `app/` em busca de qualquer módulo que chame
# ``SystemPromptBuilder.build(`` E passe o kwarg ``tenant_context_snippet=``
# no MESMO arquivo. Se o caminho não estiver explicitamente classificado em
# uma das duas listas acima, falha.
_BUILD_RE = re.compile(r"SystemPromptBuilder\.build\s*\(")
_TENANT_KW_RE = re.compile(r"tenant_context_snippet\s*=")


def _walk_app_python_files() -> list[str]:
    app_root = os.path.join(_REPO_ROOT, "app")
    rels: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(app_root):
        for fn in filenames:
            if fn.endswith(".py"):
                abs_path = os.path.join(dirpath, fn)
                rels.append(os.path.relpath(abs_path, _REPO_ROOT))
    return rels


def test_no_unaudited_system_prompt_builder_callsite():
    """Sentinela T-G: terceiro callsite NON-ReAct sem classificação quebra build.

    Se alguém adicionar um novo lugar que chama
    ``SystemPromptBuilder.build(... tenant_context_snippet=...)`` sem incluir
    o caminho em ``MUST_USE_HELPER`` ou ``OUT_OF_SCOPE_DOCUMENTED``, este
    teste falha — forçando classificação consciente.

    Por que essa defesa existe: o bug "LIA pergunta company_id no chat" caiu
    3 vezes seguidas (T-A, T-D, T-F) porque novos callsites apareciam sem
    serem auditados. T-G fecha a porta com inventário + sentinela.
    """
    classified = set(MUST_USE_HELPER.keys()) | set(OUT_OF_SCOPE_DOCUMENTED.keys())
    # Normaliza pra sep do SO (Windows safe — repo Python fica em Linux/CI mas
    # devs locais podem rodar em macOS/Windows).
    classified_norm = {p.replace("/", os.sep) for p in classified}

    self_path = os.path.relpath(os.path.abspath(__file__), _REPO_ROOT)

    unclassified: list[str] = []
    for rel in _walk_app_python_files():
        # Skip o próprio helper (define a função, não a usa) e os testes.
        if rel.endswith("tenant_aware_agent.py"):
            continue
        if rel == self_path:
            continue
        try:
            src = _read_source(rel)
        except Exception:
            continue
        if not _BUILD_RE.search(src):
            continue
        if not _TENANT_KW_RE.search(src):
            # Chama build mas não passa tenant_context_snippet — fora do escopo
            # do bug "LIA pergunta company_id".
            continue
        if rel in classified_norm:
            continue
        unclassified.append(rel)

    assert not unclassified, (
        "Novos callsites de SystemPromptBuilder.build com tenant_context_snippet "
        "foram detectados SEM classificação canônica (T-G / Task #978).\n\n"
        "Adicione cada caminho abaixo em UMA das duas listas em "
        "tests/integration/agents/test_non_react_tenant_helper_t_f.py:\n"
        "  * MUST_USE_HELPER     — se o módulo deve passar pelo helper "
        "resolve_tenant_snippet_for_non_react (caminho NON-ReAct).\n"
        "  * OUT_OF_SCOPE_DOCUMENTED — se há motivo auditável para NÃO usar "
        "o helper (ex: ReActAgent coberto pelo mixin T-D, runtime de custom "
        "agents do Agent Studio).\n\n"
        "Origem: bug 'LIA pergunta company_id no chat' caiu 3x — sem allowlist "
        "canônica, a 4a recorrência é só questão de tempo.\n\n"
        f"Caminhos não classificados:\n  - " + "\n  - ".join(sorted(unclassified))
    )
