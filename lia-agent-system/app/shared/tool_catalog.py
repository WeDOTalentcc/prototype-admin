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


def build_tool_catalog() -> dict[str, ToolMeta]:
    """Produtor único: deriva ToolMeta de todos os _CANONICAL_SOURCES.

    Dedup por nome; nomes em >1 registry acumulam em source_registries
    (detecção de colisão — Fase 5 resolve).
    """
    overlay = _scope_overlay()
    out: dict[str, ToolMeta] = {}
    for key, (mod_path, fn_name) in _CANONICAL_SOURCES.items():
        module = importlib.import_module(mod_path)
        for td in getattr(module, fn_name)():
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
                permission="write" if getattr(td, "side_effects", None) else "read",
                requires_company_id=bool(getattr(td, "requires_company_id", True)),
                touches_pii=bool(getattr(td, "touches_pii", False)),
                version=str(getattr(td, "version", "1.0")),
                source_registries=[key],
            )
    return out


def get_tools_for_scope(scope: str) -> list[str]:
    """Nomes de tools cujo scope == `scope` OU GLOBAL (sempre disponíveis)."""
    cat = build_tool_catalog()
    return [m.name for m in cat.values() if m.scope in (scope, "GLOBAL")]
