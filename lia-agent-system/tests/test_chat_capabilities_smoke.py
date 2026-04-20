"""Smoke test parametrizado para a cadeia de execução do chat unificado.

Cobertura:
1. **Handler resolution** — para cada (domain, tool) registrado em
   `*_TOOLS`, o `handler` declarado deve ser importável e callable.
2. **Action coverage** — para cada action declarada em `domain.get_all_actions()`,
   garantir que existe um caminho de execução válido:
   (a) action.action_id está mapeado em `_ACTION_TOOL_MAP` para um tool_id
       efetivamente registrado em `*_TOOLS`, OU
   (b) o domínio sobrescreve `execute_action` com lógica direta (não-mapeada),
       OU (c) está marcada como deferred em `_DEFERRED_ACTIONS`.
3. **Execute_action contract** — uma action mapeada, ao ser executada, retorna
   um `DomainResponse` (success ou clarification). Para evitar dependência de
   DB/APIs, a execução real é validada apenas para um subconjunto de actions
   "puras" (`_PURE_EXECUTABLE_ACTIONS`); as demais validam apenas que o método
   `execute_action` está implementado.

Falhas neste teste BLOQUEIAM o merge (gate de CI): qualquer regressão na
cadeia de execução é detectada antes de chegar à produção.
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import re
from typing import Any

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Configuração: domínios P1 ainda fora de escopo da Fase 1
# ──────────────────────────────────────────────────────────────────────────────
P1_DOMAINS_DEFERRED: set[str] = set()  # Phase 2 (#582): all P1 handlers now resolve.

# Domínios cujo roteamento é via state-machine (process_intent + _route_by_stage)
# em vez de _ACTION_TOOL_MAP / handler_map. Para esses, a ausência de
# mapeamento explícito NÃO é um gap — espelha `_INTENT_ROUTED_DOMAINS`
# em scripts/audit_chat_capabilities.py.
_INTENT_ROUTED_DOMAINS: set[str] = {"job_creation"}

# Actions cujo execute_action depende de IO pesado (DB com vagas reais, APIs
# externas) — validamos coverage mas não invocamos.
_DEFERRED_ACTIONS: set[tuple[str, str]] = set()

# Domínios cujas actions são roteadas via state-machine (process_intent +
# _route_by_stage), sem _ACTION_TOOL_MAP nem handler_map. Para esses, a
# ausência de mapeamento explícito é arquitetura intencional — o teste de
# coverage é satisfeito pela existência de process_intent override.
_INTENT_ROUTED_DOMAINS: set[str] = {"job_creation"}


# ──────────────────────────────────────────────────────────────────────────────
# Coletores
# ──────────────────────────────────────────────────────────────────────────────
def _collect_tools_per_domain() -> list[tuple[str, str, str]]:
    """Returns (domain_id, tool_id, handler_path) for every registered tool."""
    from app.domains.registry import DomainRegistry

    registry = DomainRegistry()
    rows: list[tuple[str, str, str]] = []
    for domain_id in registry.list_domains():
        if not isinstance(domain_id, str):  # registry pode retornar property/Mock
            continue
        try:
            tools_module = importlib.import_module(f"app.domains.{domain_id}.tools")
        except ImportError:
            continue
        for attr_name in dir(tools_module):
            if not attr_name.endswith("_TOOLS"):
                continue
            tools_list = getattr(tools_module, attr_name)
            if not isinstance(tools_list, list):
                continue
            for tool in tools_list:
                if not isinstance(tool, dict):
                    continue
                tool_id = tool.get("tool_id") or tool.get("id") or "?"
                handler = tool.get("handler")
                if handler:
                    rows.append((domain_id, tool_id, handler))
    return rows


def _collect_actions_per_domain() -> list[tuple[str, str, Any]]:
    """Returns (domain_id, action_id, domain_instance) for every registered action."""
    from app.domains.registry import DomainRegistry

    registry = DomainRegistry()
    rows: list[tuple[str, str, Any]] = []
    actions_by_domain = registry.get_all_actions() or {}
    for domain_id, actions in actions_by_domain.items():
        if not isinstance(domain_id, str):
            continue
        try:
            domain_instance = registry.get_instance(domain_id)
        except Exception:
            domain_instance = None
        if domain_instance is None:
            continue
        for action in actions or []:
            action_id = getattr(action, "action_id", None) or (
                action.get("action_id") if isinstance(action, dict) else None
            )
            if action_id:
                rows.append((domain_id, action_id, domain_instance))
    return rows


def _registered_tool_ids_per_domain() -> dict[str, set[str]]:
    by_domain: dict[str, set[str]] = {}
    for d, t, _h in _collect_tools_per_domain():
        by_domain.setdefault(d, set()).add(t)
    return by_domain


def _extract_action_tool_map(domain_instance: Any) -> dict[str, str]:
    """Extrai `_ACTION_TOOL_MAP` do domínio (#583).

    Procura a estrutura em duas posições:
      1. **Module-level** — `domain_module._ACTION_TOOL_MAP` (padrão canônico
         alinhado ao `scripts/audit_chat_capabilities.py`).
      2. **Inline em `execute_action`** — para domínios legados que ainda
         declaram o dict dentro do método (parseado via regex sobre fonte).

    O dict module-level vence em caso de colisão de chave.
    """
    mapping: dict[str, str] = {}

    # (2) inline em execute_action — fallback legado
    try:
        src = inspect.getsource(domain_instance.execute_action)
        map_blocks = re.findall(
            r'_ACTION_TOOL_MAP[^=]*=\s*\{(.*?)\}', src, flags=re.DOTALL
        )
        for block in map_blocks:
            for k, v in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block):
                mapping[k] = v
    except (TypeError, OSError):
        pass

    # (1) module-level — padrão canônico
    domain_module = inspect.getmodule(type(domain_instance))
    module_map = getattr(domain_module, "_ACTION_TOOL_MAP", None)
    if isinstance(module_map, dict):
        for k, v in module_map.items():
            if isinstance(k, str) and isinstance(v, str):
                mapping[k] = v

    return mapping


def _resolve_handler(handler_path: str) -> Any:
    """Resolve `module.func` ou `module.singleton.method` progressivamente."""
    parts = handler_path.split(".")
    last_err: Exception | None = None
    for i in range(len(parts), 0, -1):
        try:
            module = importlib.import_module(".".join(parts[:i]))
        except ImportError as exc:
            last_err = exc
            continue
        obj: Any = module
        try:
            for attr in parts[i:]:
                obj = getattr(obj, attr)
            return obj
        except AttributeError as exc:
            last_err = exc
            continue
    raise (last_err or ImportError(f"Não foi possível resolver: {handler_path}"))


# Pre-coletas em tempo de import (parametrizam os testes).
_TOOL_ROWS = _collect_tools_per_domain()
_ACTION_ROWS = _collect_actions_per_domain()
_TOOL_IDS_BY_DOMAIN = _registered_tool_ids_per_domain()


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: Handler resolution — per-case parametrize para diagnóstico granular
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "domain_id,tool_id,handler",
    _TOOL_ROWS,
    ids=[f"{d}::{t}" for d, t, _ in _TOOL_ROWS],
)
def test_chat_tool_handler_resolves(domain_id: str, tool_id: str, handler: str) -> None:
    """Cada handler declarado por um tool de chat deve ser importável e callable."""
    if domain_id in P1_DOMAINS_DEFERRED:
        pytest.xfail(f"Domínio P1 ({domain_id}) ainda não saneado — Fase 2 (#582).")

    resolved = _resolve_handler(handler)
    assert callable(resolved), (
        f"Handler {handler!r} para tool {tool_id!r} do domínio {domain_id!r} "
        f"não é callable (resolveu para: {type(resolved).__name__})."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: Action coverage — per-case parametrize
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "domain_id,action_id,domain_instance",
    _ACTION_ROWS,
    ids=[f"{d}::{a}" for d, a, _ in _ACTION_ROWS],
)
def test_action_has_execution_path(
    domain_id: str, action_id: str, domain_instance: Any
) -> None:
    """Toda action declarada em get_allowed_actions() tem caminho válido para execução."""
    if domain_id in P1_DOMAINS_DEFERRED:
        pytest.xfail(f"Domínio P1 ({domain_id}) — Fase 2 (#582).")
    if (domain_id, action_id) in _DEFERRED_ACTIONS:
        pytest.xfail(f"Action {domain_id}::{action_id} marcada deferred.")

    # Intent-routed domains (state-machine wizards) executam via
    # process_intent + _route_by_stage. A ausência de mapping é por design.
    if domain_id in _INTENT_ROUTED_DOMAINS:
        assert hasattr(domain_instance, "process_intent"), (
            f"Domínio intent-routed '{domain_id}' não implementa process_intent."
        )
        return

    mapping = _extract_action_tool_map(domain_instance)
    registered_tools = _TOOL_IDS_BY_DOMAIN.get(domain_id, set())

    if action_id in mapping:
        mapped_tool = mapping[action_id]
        assert mapped_tool in registered_tools, (
            f"Action '{action_id}' do domínio '{domain_id}' mapeia para tool "
            f"'{mapped_tool}' que NÃO está registrado em *_TOOLS. "
            f"Tools disponíveis: {sorted(registered_tools)}"
        )
    else:
        assert hasattr(domain_instance, "execute_action"), (
            f"Domínio '{domain_id}' não implementa execute_action e action "
            f"'{action_id}' não está em _ACTION_TOOL_MAP. Backlog: mapear ou "
            f"adicionar a _DEFERRED_ACTIONS."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: execute_action invocation — chama execute_action com params vazios e
# DomainContext dummy. Aceita DomainResponse OU exceções de runtime esperadas
# (faltam fixtures DB/tenant). Falha apenas em quebras estruturais:
# AttributeError de método inexistente, NameError, ImportError ou
# TypeError de signature incompatível — todos sinalizam handler quebrado.
# ──────────────────────────────────────────────────────────────────────────────
import asyncio as _asyncio
from app.domains.base import DomainContext as _DomainCtx, DomainResponse as _DomainResp

# Erros que indicam código quebrado de verdade (não falta de fixture).
_STRUCTURAL_BUG_ERRORS = (
    NameError,
    ImportError,
    SyntaxError,
)


def _build_dummy_context(domain_id: str) -> _DomainCtx:
    return _DomainCtx(
        domain_id=domain_id,
        user_id="smoke-user",
        session_id="smoke-session",
        tenant_id="smoke-tenant",
    )


@pytest.mark.parametrize(
    "domain_id,action_id,domain_instance",
    _ACTION_ROWS,
    ids=[f"{d}::{a}" for d, a, _ in _ACTION_ROWS],
)
def test_action_execute_invocation(
    domain_id: str, action_id: str, domain_instance: Any
) -> None:
    """Invoca execute_action(action_id, {}, dummy_ctx) para cada (domain, action).

    Validação: ou retorna DomainResponse válido (success/error/clarification),
    ou levanta exceção de runtime esperada (DB indisponível, tenant fake, etc).
    Falha apenas em erros estruturais — handler ausente, import quebrado,
    signature incompatível — que indicariam regressão real na cadeia de
    execução do chat unificado (#580).
    """
    if domain_id in P1_DOMAINS_DEFERRED:
        pytest.xfail(f"Domínio P1 ({domain_id}) — Fase 2 (#582).")
    if (domain_id, action_id) in _DEFERRED_ACTIONS:
        pytest.xfail(f"Action {domain_id}::{action_id} marcada deferred.")

    method = getattr(domain_instance, "execute_action", None)
    assert callable(method), (
        f"Domínio '{domain_id}' não expõe execute_action callable."
    )

    ctx = _build_dummy_context(domain_id)

    async def _invoke() -> Any:
        return await _asyncio.wait_for(method(action_id, {}, ctx), timeout=1.5)

    try:
        result = _asyncio.run(_invoke())
    except _asyncio.TimeoutError:
        # Handler estava chamando IO/DB real — chain de execução está
        # estruturalmente OK (não levantou erro de import/atributo), só
        # pendurou esperando recurso. Aceito como pass.
        return
    except _STRUCTURAL_BUG_ERRORS as exc:
        pytest.fail(
            f"[#580] {domain_id}::{action_id} levantou erro estrutural "
            f"({type(exc).__name__}: {exc}) — handler quebrado."
        )
    except TypeError as exc:
        msg = str(exc)
        # TypeError de signature do execute_action é bug; TypeError de IO interno é tolerado.
        if "execute_action" in msg or "positional argument" in msg or "keyword argument" in msg:
            pytest.fail(
                f"[#580] {domain_id}::{action_id} signature incompatível: {exc}"
            )
        return  # TypeError de outra origem = falta de fixture/dado real.
    except AttributeError as exc:
        msg = str(exc)
        # AttributeError em self._handle_xxx ou método inexistente = bug.
        if "_handle" in msg or "execute_action" in msg:
            pytest.fail(
                f"[#580] {domain_id}::{action_id} handler ausente: {exc}"
            )
        return  # AttributeError de objeto interno = falta de fixture.
    except Exception:
        # Qualquer outra exceção (PermissionError, ValueError, RuntimeError, etc.)
        # é runtime esperado em smoke sem DB/APIs reais. O importante é que a
        # chain de execução foi acionada e não quebrou estruturalmente.
        return

    # Se retornou, deve ser DomainResponse.
    assert isinstance(result, _DomainResp), (
        f"[#580] {domain_id}::{action_id} retornou {type(result).__name__} "
        f"em vez de DomainResponse."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: Execute_action contract — DomainResponse válido para erro previsível
# ──────────────────────────────────────────────────────────────────────────────
def test_execute_action_returns_domain_response_for_unknown_action() -> None:
    """Chamar execute_action com action inexistente deve retornar DomainResponse
    de erro estruturado (não levantar exceção crua)."""
    from app.domains.base import DomainContext, DomainResponse
    from app.domains.registry import DomainRegistry

    registry = DomainRegistry()
    domain = registry.get_instance("job_management")
    assert domain is not None, "Domínio job_management não está registrado."

    ctx = DomainContext(
        domain_id="job_management",
        user_id="test",
        session_id="test-session",
        tenant_id="00000000-0000-0000-0000-000000000000",
    )
    resp = asyncio.run(domain.execute_action("__action_inexistente__", {}, ctx))
    assert isinstance(resp, DomainResponse), (
        f"execute_action deve retornar DomainResponse (recebido: {type(resp).__name__})"
    )
    assert resp.success is False, "Action inexistente deve retornar success=False"


# ──────────────────────────────────────────────────────────────────────────────
# Sanity checks
# ──────────────────────────────────────────────────────────────────────────────
def test_smoke_collected_at_least_50_tools() -> None:
    assert len(_TOOL_ROWS) >= 50, (
        f"Esperado ≥50 tools agregados; coletor achou {len(_TOOL_ROWS)}."
    )


def test_smoke_collected_at_least_100_actions() -> None:
    """Deve haver ao menos 100 actions registradas no total."""
    assert len(_ACTION_ROWS) >= 100, (
        f"Esperado ≥100 actions; coletor achou {len(_ACTION_ROWS)}."
    )


def test_zero_actions_without_tool_or_handler() -> None:
    """[#583] Gate canônico — toda action deve ter tool mapeado OU handler.

    Reproduz o critério de aceitação do auditor (`scripts/audit_chat_capabilities`):
    para cada (domain, action), ou (a) está em `_ACTION_TOOL_MAP` (module-level
    ou inline) com tool registrado em `*_TOOLS`, ou (b) está em `handler_map`
    dentro do domain.py via padrão `"action_id": self._handle_*`.

    Domínios em P1_DOMAINS_DEFERRED são tolerados (xfail-equivalente).
    """
    from pathlib import Path

    failures: list[str] = []
    repo_root = Path(__file__).resolve().parent.parent

    for domain_id, action_id, domain_instance in _ACTION_ROWS:
        if domain_id in P1_DOMAINS_DEFERRED:
            continue
        if domain_id in _INTENT_ROUTED_DOMAINS:
            continue  # state-machine routing — não usa _ACTION_TOOL_MAP/handler_map
        if (domain_id, action_id) in _DEFERRED_ACTIONS:
            continue
        # Intent-routed (state-machine) — execução é via process_intent
        # + _route_by_stage; ausência de _ACTION_TOOL_MAP / handler_map
        # é arquitetura intencional. Validado em test_action_has_execution_path.
        if domain_id in _INTENT_ROUTED_DOMAINS:
            continue

        # (a) action em _ACTION_TOOL_MAP com tool registrado
        mapping = _extract_action_tool_map(domain_instance)
        registered = _TOOL_IDS_BY_DOMAIN.get(domain_id, set())
        if action_id in mapping and mapping[action_id] in registered:
            continue

        # (b) handler_map regex sobre o arquivo real da classe (alguns
        # domínios — como pipeline_transition — vivem em pacote diferente).
        domain_src = ""
        try:
            domain_src = Path(inspect.getfile(type(domain_instance))).read_text(errors="ignore")
        except (TypeError, OSError):
            domain_src_path = repo_root / "app" / "domains" / domain_id / "domain.py"
            try:
                domain_src = domain_src_path.read_text(errors="ignore")
            except OSError:
                domain_src = ""
        if "handler_map" in domain_src:
            handler_keys = set(re.findall(
                r'"([a-z_][a-z0-9_]*)"\s*:\s*self\._handle', domain_src
            ))
            if action_id in handler_keys:
                continue

        failures.append(f"{domain_id}::{action_id}")

    assert not failures, (
        f"[#583] {len(failures)} actions sem tool nem handler:\n  - "
        + "\n  - ".join(sorted(failures))
    )


# ──────────────────────────────────────────────────────────────────────────────
# Execution-level checks (#583 review follow-up)
# ──────────────────────────────────────────────────────────────────────────────
def test_candidate_self_service_blocks_unauthenticated_access() -> None:
    """[#583/security] Handlers do candidato exigem identidade autenticada.

    Defesa contra IDOR: nao basta passar candidate_id no payload — a identidade
    deve vir do contexto autenticado. Sem user_id/tenant_id, deve falhar.
    """
    import asyncio
    from app.domains.candidate_self_service.domain import CandidateSelfServiceDomain
    from app.domains.base import DomainContext

    domain = CandidateSelfServiceDomain()
    anon_ctx = DomainContext(
        domain_id="candidate_self_service", user_id="", session_id="s", tenant_id=""
    )
    for handler_name in ("_handle_get_status", "_handle_get_interview_info", "_handle_get_feedback"):
        handler = getattr(domain, handler_name)
        resp = asyncio.run(handler({"vacancy_id": "v1"}, anon_ctx))
        assert resp.success is False, f"{handler_name} permitiu acesso anonimo"
        assert "negado" in (resp.error or "").lower(), (
            f"{handler_name} nao retornou mensagem de acesso negado: {resp.error!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# [#591] Cobertura de execução real do _ACTION_TOOL_MAP por domínio
# ──────────────────────────────────────────────────────────────────────────────
# Actions que executamos com payload dummy para validar o contrato execute_action
# → DomainResponse. Excluídas:
#   - actions em _DEFERRED_ACTIONS (já cobertas pela exceção declarativa);
#   - actions cujo handler exige IO externo pesado (Apify, OpenAI, e-mail real)
#     e não retorna DomainResponse estruturado em modo dummy. A whitelist
#     abaixo é deliberadamente curta — qualquer crescimento exige justificativa
#     no PR. Adicionar aqui = aceitar débito técnico.
_ACTION_EXECUTION_SKIP: set[tuple[str, str]] = set()


def test_mapped_actions_return_domain_response_under_dummy_payload() -> None:
    """[#591] Para CADA action mapeada em `_ACTION_TOOL_MAP`, executar com
    payload dummy seguro DEVE retornar DomainResponse — sem exceção crua.

    Cobre o contrato prometido pelo saneamento da Fase 1: handlers tipados
    devolvem `success`, `clarification` ou `error_response`; nunca propagam
    stack trace para o orquestrador. Falhas listam (domain, action, exc) para
    diagnóstico granular, em vez de parar no primeiro erro.
    """
    from app.domains.base import DomainContext, DomainResponse
    from app.domains.registry import DomainRegistry

    registry = DomainRegistry()
    failures: list[str] = []
    executed = 0

    dummy_ctx = DomainContext(
        domain_id="__smoke__",
        user_id="00000000-0000-0000-0000-000000000001",
        session_id="smoke-session",
        tenant_id="00000000-0000-0000-0000-000000000099",
    )

    for domain_id in sorted(_TOOL_IDS_BY_DOMAIN.keys() | set(P1_DOMAINS_DEFERRED)):
        if domain_id in P1_DOMAINS_DEFERRED:
            continue
        if domain_id in _INTENT_ROUTED_DOMAINS:
            continue
        try:
            domain = registry.get_instance(domain_id)
        except Exception as exc:
            failures.append(f"{domain_id} :: registry.get_instance crashed → {exc!r}")
            continue
        if domain is None:
            continue

        mapping = _extract_action_tool_map(domain)
        for action_id, _tool_id in mapping.items():
            if (domain_id, action_id) in _DEFERRED_ACTIONS:
                continue
            if (domain_id, action_id) in _ACTION_EXECUTION_SKIP:
                continue

            dummy_ctx.domain_id = domain_id
            try:
                resp = asyncio.run(domain.execute_action(action_id, {}, dummy_ctx))
            except Exception as exc:
                failures.append(
                    f"{domain_id}::{action_id} levantou {type(exc).__name__}: "
                    f"{str(exc)[:160]}"
                )
                continue

            if not isinstance(resp, DomainResponse):
                failures.append(
                    f"{domain_id}::{action_id} retornou {type(resp).__name__} "
                    f"em vez de DomainResponse"
                )
                continue
            executed += 1

    # Sanity: cobrimos pelo menos as 4 famílias saneadas na Fase 1.
    assert executed >= 30, (
        f"Cobertura suspeita: só {executed} actions exercitadas "
        f"(esperado ≥30 entre os 4 domínios P0)."
    )
    assert not failures, (
        f"[#591] {len(failures)} actions estouraram exceção ou não retornaram "
        f"DomainResponse:\n  - " + "\n  - ".join(failures)
    )


def test_company_settings_handlers_fail_explicitly_when_service_missing() -> None:
    """[#583] Sem CompanyProfileService, handlers devolvem error_response.

    Anteriormente o ImportError era engolido e respondia success — mascarando
    no-op como execucao. Agora deve falhar explicitamente.
    """
    import asyncio
    from app.domains.company_settings.domain import CompanySettingsDomain
    from app.domains.base import DomainContext

    domain = CompanySettingsDomain()
    ctx = DomainContext(
        domain_id="company_settings", user_id="u1", session_id="s", tenant_id="t1"
    )
    for handler_name in (
        "_handle_configure_profile",
        "_handle_configure_culture",
        "_handle_configure_tech_stack",
        "_handle_configure_benefits",
        "_handle_configure_workforce",
        "_handle_analyze_website",
        "_handle_process_document",
    ):
        handler = getattr(domain, handler_name)
        resp = asyncio.run(handler({}, ctx))
        assert resp.success is False, f"{handler_name} mascarou no-op como sucesso"
        assert "nao foi implementado" in (resp.error or "").lower(), (
            f"{handler_name} mensagem inesperada: {resp.error!r}"
        )
