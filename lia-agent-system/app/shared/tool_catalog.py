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
    # autonomous = MENOR prioridade: re-implementa tools de outros dominios
    # (_wrap_auto_*) p/ execucao autonoma. Em colisao de nome, o dominio
    # CANONICO vence (first-wins na ordem). Fase 5 reconciliacao.
    "autonomous": ("app.domains.autonomous.agents.autonomous_tool_registry", "get_autonomous_tools"),
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
