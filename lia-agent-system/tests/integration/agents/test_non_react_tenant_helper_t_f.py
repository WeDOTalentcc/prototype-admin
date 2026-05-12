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

import ast
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


# ----------------------------------------------------------------------
# T-G (Task #978) — Inventário canônico de callsites NON-ReAct
# ----------------------------------------------------------------------
# DEVEM usar ``resolve_tenant_snippet_for_non_react``. A sentinela AST
# ``test_must_use_helper_modules_pass_tenant_arg_from_resolver`` (Task #979)
# prova **estruturalmente** que cada chamada de ``SystemPromptBuilder.build``
# nesses módulos passa ``tenant_context_snippet=`` derivado do helper canônico
# — substituindo a antiga sentinela por substring, que dava tanto falso
# positivo (nome em comentário) quanto falso negativo (refactors com aliases).
# Se um módulo NOVO chamar ``SystemPromptBuilder.build`` com
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


# ----------------------------------------------------------------------
# AST-based validation (Task #979) — supersedes substring sentinels
# ----------------------------------------------------------------------
# Por que AST e não substring:
#   * Substring dá FALSO POSITIVO: o nome do helper aparecendo num
#     comentário ou import sem uso real "passa" o teste.
#   * Substring dá FALSO NEGATIVO em refactors estruturais legítimos
#     (ex.: renomear o symbol importado via ``as`` ou splitar funções).
# A análise estática garante que o argumento ``tenant_context_snippet=``
# de cada chamada a ``SystemPromptBuilder.build(...)`` provém
# **estruturalmente** do retorno de ``resolve_tenant_snippet_for_non_react(...)``
# — diretamente (assignment local) ou indiretamente (parâmetro de função
# helper cujos call-sites passam o resultado do resolver).
_RESOLVER_NAME = "resolve_tenant_snippet_for_non_react"


def _is_resolver_call(expr: ast.AST) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    if isinstance(func, ast.Name) and func.id == _RESOLVER_NAME:
        return True
    if isinstance(func, ast.Attribute) and func.attr == _RESOLVER_NAME:
        return True
    return False


def _enclosing_func(tree: ast.AST, target: ast.AST) -> ast.AST | None:
    """Smallest FunctionDef/AsyncFunctionDef containing ``target`` by lineno."""
    candidates: list[tuple[int, ast.AST]] = []
    target_line = getattr(target, "lineno", None)
    if target_line is None:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", None) or node.lineno
            if start <= target_line <= end:
                candidates.append((end - start, node))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _iter_scope_statements(func_node: ast.AST):
    """Yield statements that share ``func_node``'s scope.

    Walks into control-flow containers (``If``/``For``/``While``/``Try``/``With``
    etc.) but **stops at scope boundaries** — nested ``FunctionDef``,
    ``AsyncFunctionDef``, ``Lambda``, ``ClassDef`` and comprehensions are
    skipped. This avoids picking variable bindings from a nested helper as if
    they applied to the enclosing function.
    """
    SCOPE_BOUNDARY = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Lambda,
        ast.ClassDef,
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
    )

    def _walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, SCOPE_BOUNDARY):
                # Do not descend — different scope.
                continue
            yield child
            yield from _walk(child)

    yield from _walk(func_node)


def _nearest_prior_assignment_source(
    func_node: ast.AST, name: str, before_lineno: int
) -> ast.AST | None:
    """Most recent RHS expression assigned to ``name`` in ``func_node``'s scope
    that occurs *before* ``before_lineno`` (callsite-relative).

    Scope-aware (does not descend into nested functions/lambdas/classes/
    comprehensions) and order-aware (only considers assignments with
    ``lineno < before_lineno``). This prevents two failure modes flagged in
    code review:
      * picking up an assignment that occurs **after** the
        ``SystemPromptBuilder.build(...)`` call,
      * picking up an assignment from a nested function body.
    """
    source: ast.AST | None = None
    source_lineno = -1
    for node in _iter_scope_statements(func_node):
        node_lineno = getattr(node, "lineno", None)
        if node_lineno is None or node_lineno >= before_lineno:
            continue
        if isinstance(node, ast.Assign):
            assigned = False
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    assigned = True
                elif isinstance(tgt, (ast.Tuple, ast.List)):
                    for elt in tgt.elts:
                        if isinstance(elt, ast.Name) and elt.id == name:
                            assigned = True
            if assigned and node_lineno > source_lineno:
                source = node.value
                source_lineno = node_lineno
        elif isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == name
                and node.value is not None
                and node_lineno > source_lineno
            ):
                source = node.value
                source_lineno = node_lineno
    return source


def _is_param_of(func_node: ast.AST, name: str) -> bool:
    args = func_node.args
    all_args = list(args.args) + list(args.kwonlyargs) + list(args.posonlyargs)
    if args.vararg:
        all_args.append(args.vararg)
    if args.kwarg:
        all_args.append(args.kwarg)
    return any(a.arg == name for a in all_args)


def _find_callers(tree: ast.AST, func_name: str, exclude: ast.AST) -> list[ast.Call]:
    out: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node is not exclude:
            f = node.func
            fname = None
            if isinstance(f, ast.Name):
                fname = f.id
            elif isinstance(f, ast.Attribute):
                fname = f.attr
            if fname == func_name:
                out.append(node)
    return out


def _validate_tenant_arg(
    tree: ast.AST,
    call_node: ast.Call,
    value_node: ast.AST,
    seen: set[str] | None = None,
) -> tuple[bool, str]:
    """Recursively prove ``value_node`` originates from ``_RESOLVER_NAME(...)``.

    Two structural shapes are accepted:
      1. ``X = resolve_tenant_snippet_for_non_react(...)`` then
         ``SystemPromptBuilder.build(..., tenant_context_snippet=X, ...)``
         within the same enclosing function.
      2. ``tenant_context_snippet=PARAM`` where ``PARAM`` is a parameter of
         the enclosing helper function. In that case, every call-site of the
         helper inside the same module must pass that parameter from a
         resolver call (recursive check).
    """
    if seen is None:
        seen = set()

    if not isinstance(value_node, ast.Name):
        kind = type(value_node).__name__
        return False, (
            "tenant_context_snippet deve ser um Name ligado a "
            f"{_RESOLVER_NAME}(...) — recebido: {kind}"
        )

    name = value_node.id
    func = _enclosing_func(tree, call_node)
    if func is None:
        return False, (
            f"chamada a SystemPromptBuilder.build na linha {call_node.lineno} "
            f"está fora de uma função — não foi possível validar '{name}'"
        )

    src_expr = _nearest_prior_assignment_source(
        func, name, before_lineno=call_node.lineno
    )
    if src_expr is not None and _is_resolver_call(src_expr):
        return True, ""

    if _is_param_of(func, name):
        key = f"{func.name}@{func.lineno}"
        if key in seen:
            return True, ""
        seen.add(key)
        callers = _find_callers(tree, func.name, exclude=call_node)
        if not callers:
            return False, (
                f"função '{func.name}' recebe '{name}' como parâmetro mas não "
                "tem call-sites no mesmo módulo — não é possível provar que o "
                f"upstream chama {_RESOLVER_NAME}(...)"
            )
        for caller in callers:
            kw = next((k for k in caller.keywords if k.arg == name), None)
            if kw is None:
                return False, (
                    f"call-site de '{func.name}' na linha {caller.lineno} não "
                    f"passa '{name}=' explicitamente — não é possível provar "
                    f"que o upstream chama {_RESOLVER_NAME}(...)"
                )
            ok, reason = _validate_tenant_arg(tree, caller, kw.value, seen)
            if not ok:
                return False, (
                    f"call-site de '{func.name}' na linha {caller.lineno}: {reason}"
                )
        return True, ""

    if src_expr is not None:
        return False, (
            f"'{name}' em '{func.name}' é atribuído de "
            f"{ast.dump(src_expr)[:120]}... — esperado {_RESOLVER_NAME}(...)"
        )
    return False, (
        f"'{name}' em '{func.name}' não é atribuído de {_RESOLVER_NAME}(...) "
        "nem é parâmetro do enclosing helper — origem não auditável"
    )


def _ast_validate_module(rel_path: str) -> list[str]:
    """Return a list of human-readable failures for ``rel_path``."""
    src = _read_source(rel_path)
    tree = ast.parse(src, filename=rel_path)
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (
            isinstance(f, ast.Attribute)
            and f.attr == "build"
            and isinstance(f.value, ast.Name)
            and f.value.id == "SystemPromptBuilder"
        ):
            continue
        tcs_kw = next(
            (k for k in node.keywords if k.arg == "tenant_context_snippet"),
            None,
        )
        if tcs_kw is None:
            continue
        ok, reason = _validate_tenant_arg(tree, node, tcs_kw.value)
        if not ok:
            failures.append(f"{rel_path}:{node.lineno} — {reason}")
    return failures


def _must_use_helper_paths() -> list[str]:
    return sorted(MUST_USE_HELPER.keys())


def _validate_inline_source(src: str) -> list[str]:
    """Run the AST validator against an inline source string (for unit tests)."""
    tree = ast.parse(src, filename="<inline>")
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (
            isinstance(f, ast.Attribute)
            and f.attr == "build"
            and isinstance(f.value, ast.Name)
            and f.value.id == "SystemPromptBuilder"
        ):
            continue
        tcs_kw = next(
            (k for k in node.keywords if k.arg == "tenant_context_snippet"),
            None,
        )
        if tcs_kw is None:
            continue
        ok, reason = _validate_tenant_arg(tree, node, tcs_kw.value)
        if not ok:
            failures.append(f"line {node.lineno}: {reason}")
    return failures


def test_ast_sentinel_accepts_direct_resolver_assignment():
    """Caso bom: snippet vem de assignment direto do helper."""
    src = (
        "def f(ctx):\n"
        "    snippet = resolve_tenant_snippet_for_non_react(ctx, agent_name='x')\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=snippet)\n"
    )
    assert _validate_inline_source(src) == []


def test_ast_sentinel_accepts_param_with_resolver_upstream():
    """Caso bom: snippet vem de parâmetro cujo call-site usa o helper."""
    src = (
        "def helper(*, tenant_context_snippet=''):\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=tenant_context_snippet)\n"
        "\n"
        "def caller(ctx):\n"
        "    s = resolve_tenant_snippet_for_non_react(ctx, agent_name='x')\n"
        "    return helper(tenant_context_snippet=s)\n"
    )
    assert _validate_inline_source(src) == []


def test_ast_sentinel_rejects_dict_get_anti_pattern():
    """Caso ruim: anti-padrão clássico ``ctx.get('tenant_context_snippet', '')``."""
    src = (
        "def f(ctx):\n"
        "    return SystemPromptBuilder.build(\n"
        "        tenant_context_snippet=ctx.get('tenant_context_snippet', '')\n"
        "    )\n"
    )
    failures = _validate_inline_source(src)
    assert failures, "AST sentinel should reject ctx.get(...) anti-pattern"


def test_ast_sentinel_rejects_string_literal():
    """Caso ruim: string literal hardcoded — origem não auditável."""
    src = (
        "def f():\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet='hardcoded')\n"
    )
    failures = _validate_inline_source(src)
    assert failures


def test_ast_sentinel_rejects_unrelated_assignment():
    """Caso ruim: variável atribuída de outra função — não do helper canônico."""
    src = (
        "def f(ctx):\n"
        "    snippet = some_other_function(ctx)\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=snippet)\n"
    )
    failures = _validate_inline_source(src)
    assert failures


def test_ast_sentinel_rejects_param_with_unrelated_caller():
    """Caso ruim: param passado por caller que NÃO chama o helper canônico."""
    src = (
        "def helper(*, tenant_context_snippet=''):\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=tenant_context_snippet)\n"
        "\n"
        "def caller():\n"
        "    return helper(tenant_context_snippet='oops')\n"
    )
    failures = _validate_inline_source(src)
    assert failures


def test_ast_sentinel_rejects_assignment_after_call():
    """Caso ruim (callsite-relative): assignment do helper só ocorre DEPOIS
    da chamada de ``build`` — ``ast.walk`` ingênuo aceitaria por engano."""
    src = (
        "def f(ctx):\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=snippet)\n"
        "    snippet = resolve_tenant_snippet_for_non_react(ctx, agent_name='x')\n"
    )
    failures = _validate_inline_source(src)
    assert failures, "AST sentinel must require assignment to precede the call"


def test_ast_sentinel_rejects_nested_function_assignment():
    """Caso ruim (scope-aware): assignment do helper está numa função aninhada,
    enquanto o snippet do enclosing vem de um anti-padrão. ``ast.walk`` ingênuo
    cruzaria o boundary de escopo e aceitaria por engano."""
    src = (
        "def f(ctx):\n"
        "    def inner():\n"
        "        snippet = resolve_tenant_snippet_for_non_react(ctx, agent_name='x')\n"
        "        return snippet\n"
        "    snippet = ctx.get('tenant_context_snippet', '')\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=snippet)\n"
    )
    failures = _validate_inline_source(src)
    assert failures, "AST sentinel must not cross nested-function scope boundary"


def test_ast_sentinel_uses_nearest_prior_assignment():
    """Caso bom: múltiplas atribuições — a última anterior à chamada vem do
    helper canônico, então a sentinela aceita."""
    src = (
        "def f(ctx):\n"
        "    snippet = ctx.get('x', '')\n"
        "    snippet = resolve_tenant_snippet_for_non_react(ctx, agent_name='x')\n"
        "    return SystemPromptBuilder.build(tenant_context_snippet=snippet)\n"
    )
    assert _validate_inline_source(src) == []


def test_ast_sentinel_rejects_resolver_only_in_comment():
    """Caso ruim: nome do helper só aparece em comentário/docstring (era o
    falso positivo da sentinela substring)."""
    src = (
        "def f(ctx):\n"
        "    # resolve_tenant_snippet_for_non_react is the canonical helper\n"
        "    '''resolve_tenant_snippet_for_non_react docstring mention.'''\n"
        "    return SystemPromptBuilder.build(\n"
        "        tenant_context_snippet=ctx['tenant_context_snippet']\n"
        "    )\n"
    )
    failures = _validate_inline_source(src)
    assert failures, "AST sentinel deve ignorar menções em comentário/docstring"


@pytest.mark.parametrize("rel_path", _must_use_helper_paths())
def test_must_use_helper_modules_pass_tenant_arg_from_resolver(rel_path):
    """AST sentinel (Task #979): cada call de ``SystemPromptBuilder.build(...)``
    em módulos de ``MUST_USE_HELPER`` deve passar ``tenant_context_snippet``
    estruturalmente derivado de ``resolve_tenant_snippet_for_non_react(...)``.

    Substitui as sentinelas por substring (``test_fallback_react_service_uses_canonical_helper``
    e ``test_orchestrator_v1_uses_canonical_helper``), eliminando falsos
    positivos (nome em comentário/import sem uso) e falsos negativos
    (refactors com aliases ou helpers intermediários).
    """
    failures = _ast_validate_module(rel_path)
    assert not failures, (
        "Validação AST falhou — uma chamada de SystemPromptBuilder.build "
        "passa tenant_context_snippet sem origem auditável em "
        f"resolve_tenant_snippet_for_non_react(...).\n\n"
        "Origem: bug 'LIA pergunta company_id no chat' caiu 3x (T-A, T-D, "
        "T-F). Sentinela AST (Task #979) impede que substring miss/false-"
        "positive disfarce a 4a recorrência.\n\n"
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
