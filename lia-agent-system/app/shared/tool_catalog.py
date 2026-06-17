"""Catálogo canônico de tools — fonte única de METADATA (Fase 1 reconciliação).

DERIVADO dos domain registries (Sistema B) + overlay de `scope` do
`tool_registry_metadata.yaml` (Sistema A). NUNCA hand-maintained (anti-drift):
quem é dono do metadata de execução é o ToolDefinition do registry de origem;
este catálogo só UNIFICA + acrescenta o `scope` (PromptScope) por contexto.

Fase 1: escopo inicial = 5 registries provados (jobs/talent/kanban/wizard/
workforce — os que o recruiter_copilot já importa). Fases seguintes expandem
_CANONICAL_SOURCES para os demais domínios (communication, analytics, ...).

Proveniência honesta: scope vindo do YAML-A => scope_inferred=False; senão
default GLOBAL + scope_inferred=True (não fabrica scope).
"""
from __future__ import annotations

import functools
import importlib
import pathlib

from pydantic import BaseModel, ConfigDict, Field


class ToolMeta(BaseModel):
    """Metadata canônica unificada de uma tool (1 por nome)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    domain: str
    scope: str = "GLOBAL"  # PromptScope: TALENT_FUNNEL|JOB_TABLE|IN_JOB|GLOBAL
    scope_inferred: bool = True  # True = não veio do YAML-A (honesto)
    permission: str = "read"  # read|write (derivado de side_effects)
    requires_company_id: bool = True
    touches_pii: bool = False
    affects_candidate_decision: bool = False
    requires_human_review: bool = False
    version: str = "1.0"
    source_registries: list[str] = Field(default_factory=list)


# registry_key -> (módulo, função get_*_tools). Fase 1 = núcleo provado.
_CANONICAL_SOURCES: dict[str, tuple[str, str]] = {
    "jobs_mgmt": (
        "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry",
        "get_jobs_mgmt_tools",
    ),
    "talent": (
        "app.domains.recruiter_assistant.agents.talent_tool_registry",
        "get_talent_tools",
    ),
    "kanban": (
        "app.domains.recruiter_assistant.agents.kanban_tool_registry",
        "get_kanban_tools",
    ),
    "wizard": (
        "app.domains.job_management.agents.wizard_tool_registry",
        "get_wizard_tools",
    ),
    "workforce": (
        "app.domains.workforce.agents.workforce_tool_registry",
        "get_workforce_tools",
    ),
    "analytics": ("app.domains.analytics.agents.analytics_tool_registry", "get_analytics_tools"),
    "ats_integration": ("app.domains.ats_integration.agents.ats_integration_tool_registry", "get_ats_integration_tools"),
    "automation": ("app.domains.automation.agents.automation_tool_registry", "get_automation_tools"),
    "communication": ("app.domains.communication.agents.communication_tool_registry", "get_communication_tools"),
    "company_settings": ("app.domains.company_settings.agents.company_tool_registry", "get_company_settings_tools"),
    "policy": ("app.domains.hiring_policy.agents.policy_tool_registry", "get_policy_tools"),
    "sourcing": ("app.domains.sourcing.agents.sourcing_tool_registry", "get_sourcing_tools"),
    "talent_pool": ("app.domains.talent_pool.agents.talent_pool_tool_registry", "get_talent_pool_tools"),
    "ui": ("app.domains.recruiter_assistant.agents.ui_tool_registry", "get_ui_tools"),
    # cv_screening_pipeline: read tools from pipeline_tool_registry (view_screening_results, etc.)
    # Separado de cv_screening (candidate mutation tools) para dedup por nome.
    "cv_screening_pipeline": (
        "app.domains.cv_screening.agents.pipeline_tool_registry",
        "get_pipeline_tools",
    ),
    # interview_scheduling: agendamento de entrevistas (schedule_interview, check_interviewer_availability)
    "interview_scheduling": (
        "app.domains.interview_scheduling.agents.interview_scheduling_tool_registry",
        "get_interview_scheduling_tools",
    ),
    # autonomous REMOVIDO (P2-3, 2026-06-15): diretório app/domains/autonomous/ NÃO existe.
    # Mantê-lo causava ModuleNotFoundError silencioso em toda carga do catálogo.
    # Sensor: tests/contract/test_federation_spec_completeness.py::test_autonomous_not_in_canonical_sources
}


@functools.lru_cache(maxsize=1)
def _scope_overlay() -> dict[str, str]:
    """name -> scope, lido do tool_registry_metadata.yaml (Sistema A)."""
    import yaml

    app_dir = pathlib.Path(__file__).resolve().parent.parent  # .../app
    yaml_path = app_dir / "tools" / "tool_registry_metadata.yaml"
    if not yaml_path.exists():
        return {}
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    overlay: dict[str, str] = {}
    for tool in data.get("tools", []) or []:
        name = tool.get("name")
        scope = tool.get("scope")
        if name and scope:
            overlay[str(name)] = str(scope)
    return overlay


def _load_sources() -> dict[str, list]:
    """Importa cada registry de _CANONICAL_SOURCES defensivamente.

    Falha de um registry NAO derruba o catalogo (degrada + loga; o sensor
    test_todas_fontes_canonicas_carregam pega regressao). Retorna
    {key: [ToolDefinition]}.
    """
    import logging

    log = logging.getLogger(__name__)
    out: dict[str, list] = {}
    for key, (mod_path, fn_name) in _CANONICAL_SOURCES.items():
        try:
            module = importlib.import_module(mod_path)
            out[key] = list(getattr(module, fn_name)())
        except Exception as exc:
            log.warning("[tool_catalog] fonte %r falhou ao carregar: %s", key, exc)
    return out


def build_tool_catalog() -> dict[str, ToolMeta]:
    """Produtor único: deriva ToolMeta de todos os _CANONICAL_SOURCES.

    Dedup por nome; nomes em >1 registry acumulam em source_registries
    (detecção de colisão — Fase 5 resolve).
    """
    overlay = _scope_overlay()
    out: dict[str, ToolMeta] = {}
    for key, tools in _load_sources().items():
        for td in tools:
            existing = out.get(td.name)
            if existing is not None:
                if key not in existing.source_registries:
                    existing.source_registries.append(key)
                continue
            scope = overlay.get(td.name)
            out[td.name] = ToolMeta(
                name=td.name,
                domain=str(getattr(td, "owner_team", "") or key),
                scope=scope or "GLOBAL",
                scope_inferred=scope is None,
                permission="write"
            if "write" in (getattr(td, "side_effects", None) or [])
            else "read",
                requires_company_id=bool(getattr(td, "requires_company_id", True)),
                touches_pii=bool(getattr(td, "touches_pii", False)),
                affects_candidate_decision=bool(
                    getattr(td, "affects_candidate_decision", False)
                ),
                requires_human_review=bool(
                    getattr(td, "requires_human_review", False)
                ),
                version=str(getattr(td, "version", "1.0")),
                source_registries=[key],
            )
    return out


def get_tools_for_scope(scope: str) -> list[str]:
    """Nomes de tools BOUNDED para o scope (DELEGA ao scope_config, fonte unica) + GLOBAL.

    Fix 2026-06-06: a versao anterior filtrava por ToolMeta.scope do catalogo, mas
    166 de 179 tools defaultam a scope GLOBAL (scope_inferred) + havia case mismatch
    (lowercase vs UPPERCASE) e retornava ~166 (NAO estreitava = anti-pattern). O scope
    bounded vem do YAML de permissoes via app.tools.scope_config (talent_funnel=26,
    job_table=19, in_job=26, global=10). Uma fonte da verdade; GLOBAL sempre incluido.
    """
    from app.tools.scope_config import get_tools_for_scope as _bounded
    _sc = str(scope).lower()
    return sorted(set(_bounded(_sc)) | set(_bounded("global")))


# Fase 2 consolidacao: escopo DERIVADO do registry de origem (anti-drift).
# A ToolDefinition real NAO carrega scope (so owner_team='backend'); e os YAMLs
# de scope (scope_config / tool_registry_metadata) divergiram dos 179 nomes
# reais -> filtrar por eles dava 1-6 tools/escopo (bug live 2026-06-06: federado
# primario SEM busca, nao achava Felipe Almeida que existe). Fonte unica =
# registry de origem (_load_sources ja agrupa por key). Cada key alimenta 1+
# escopos; GLOBAL = essenciais transversais (reads).
_REGISTRY_SCOPE: dict[str, set[str]] = {
    "talent": {"talent_funnel"},
    "sourcing": {"talent_funnel"},
    "talent_pool": {"talent_funnel"},
    # ui: apply_table_state so faz sentido onde ha ponte FE (Funil/candidates).
    # open_ui esta em _GLOBAL_ESSENTIALS (sempre disponivel, todos os escopos).
    "ui": {"talent_funnel", "job_table", "in_job"},
    "communication": {"talent_funnel", "in_job"},
    "kanban": {"in_job"},
    "jobs_mgmt": {"job_table"},
    "analytics": {"job_table"},
    "workforce": {"job_table", "global"},
    # cv_screening_pipeline: view_screening_results disponível em in_job e talent_funnel
    "cv_screening_pipeline": {"in_job", "talent_funnel"},
    # interview_scheduling: agendar entrevista disponivel em in_job
    "interview_scheduling": {"in_job", "talent_funnel"},
    # wizard: roda como state machine SEPARADA (pre-router) -- federado nao usa.
    # company_settings / policy / automation / ats_integration:
    # fora do escopo inicial (decisao #3 -- expandir PromptScope quando preciso).
}

# Reads transversais SEMPRE disponiveis (inclusive no fallback GLOBAL): o
# federado primario precisa achar/listar/ver candidato e vaga em QUALQUER turno,
# mesmo sem contexto de pagina. So READS (sem mutacao) -> seguro no fallback.
# Nomes confirmados reais nos registries (talent / jobs_mgmt / kanban).
_GLOBAL_ESSENTIALS: set[str] = {
    "search_candidates",
    "list_candidates",
    "view_candidate_profile",
    "compare_candidates",
    "rank_candidates",
    "list_jobs",
    "view_job_details",
    "get_portfolio_metrics",
    "get_pipeline_summary",
    "list_stage_candidates",
    # UI capability universal (self-gated: capability_map + HITL): abrir modal/
    # navegar de qualquer surface. apply_table_state NAO entra aqui (surface-
    # specific: so no escopo talent_funnel via _REGISTRY_SCOPE).
    "open_ui",
}


def get_scoped_tool_definitions(scope: str) -> list:
    """ToolDefinitions para o agente federado carregar ~20-50 tools/turno (em vez
    das 179). DERIVA o escopo do registry de ORIGEM (_REGISTRY_SCOPE, anti-drift)
    + _GLOBAL_ESSENTIALS (reads transversais sempre presentes). Dedup por nome
    (1o registry vence -- dominio canonico antes do autonomous). Fase 2 do plano
    de consolidacao (agente federado unico).

    NAO usa mais o scope-set YAML (scope_config) -- ele divergiu dos nomes reais
    e dava 1-6 tools/escopo (bug live 2026-06-06). Sensor end-to-end:
    tests/contract/test_scoped_tool_definitions_coverage.py.

    Retorna objetos ToolDefinition (o caller converte via
    tool_definition_to_langchain_tool). Defensivo: usa o que _load_sources carregou.
    """
    scope_str = (scope.value if hasattr(scope, "value") else str(scope)).strip().lower()
    wanted_keys = {k for k, scopes in _REGISTRY_SCOPE.items() if scope_str in scopes}
    by_name: dict[str, object] = {}
    for key, defs in _load_sources().items():
        registry_in_scope = key in wanted_keys
        for td in defs:
            nm = getattr(td, "name", None)
            if not nm or nm in by_name:
                continue
            if registry_in_scope or nm in _GLOBAL_ESSENTIALS:
                by_name[nm] = td
    # Fase C.2 (2026-06-09): Studio scope extension — first-party agents contribute
    # tools for covered scopes.  Sync check (get_studio_covered_scopes) is fast (set
    # lookup from static config, no DB); async cache build only when scope matches.
    # Fail-open: any error from the extension leaves base scoped tools intact.
    # NOTE: this is SYNC — get_scoped_tool_definitions is called from a sync context
    # (_resolve_scoped_tool_defs in recruiter_copilot_react_agent.py).  We use the
    # already-built cache snapshot (None = not yet populated = skip silently).
    try:
        from app.orchestrator.studio_scope_extension import (
            get_studio_covered_scopes,
            get_studio_scope_cache_snapshot,
        )
        if scope_str in get_studio_covered_scopes():
            _snapshot = get_studio_scope_cache_snapshot()
            if _snapshot is not None:
                _studio_tool_names = _snapshot.get(scope_str, [])
                _all_tool_defs = None  # built lazily below if needed
                for _tool_name in _studio_tool_names:
                    if _tool_name in by_name:
                        continue  # existing registry wins (canonical first)
                    # Look up full ToolDefinition from loaded sources by name.
                    # Scan once and build a name→def reverse map if we have any miss.
                    if _all_tool_defs is None:
                        _all_tool_defs = {
                            getattr(td, "name", None): td
                            for defs in _load_sources().values()
                            for td in defs
                        }
                    _td = _all_tool_defs.get(_tool_name)
                    if _td is not None:
                        by_name[_tool_name] = _td
    except Exception:
        import logging as _log
        _log.getLogger(__name__).debug(
            "[tool_catalog] Studio scope extension skipped for scope=%s", scope_str,
            exc_info=True,
        )
    return list(by_name.values())
