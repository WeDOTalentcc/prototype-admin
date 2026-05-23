"""
Auditor profundo: cruza Domain Actions ↔ Tools ↔ Handlers ↔ Router.

Objetivo: produzir inventário completo do que a LIA REALMENTE consegue executar
quando o recrutador faz uma solicitação no chat unificado, e identificar gaps:
  - Tools registradas mas inalcançáveis (sem action ou keyword)
  - Actions sem tool nem handler
  - Mapeamentos quebrados (action -> tool inexistente)
  - Handlers que falham ao importar
  - Agent-types no AGENT_TYPE_TO_DOMAIN apontando para domínios não registrados
  - Domain dirs que NÃO estão registrados
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import traceback
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://stub:stub@localhost/stub")
os.environ.setdefault("LIA_SKIP_DB", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Domínios que executam actions via state-machine intent routing
# (process_intent + _route_by_stage), em vez de _ACTION_TOOL_MAP / handler_map.
# Para esses, a ausência de mapeamento explícito NÃO é um gap.
_INTENT_ROUTED_DOMAINS: set[str] = {"job_creation"}


REPORT: dict = {
    "registered_domains": {},
    "domain_dirs_unregistered": [],
    "agent_type_mapping": {},
    "agent_types_pointing_to_unknown_domain": [],
    "gaps_by_domain": {},
    "global_summary": {},
}


def _safe_import(modpath: str):
    try:
        return importlib.import_module(modpath), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _list_domain_dirs() -> list[str]:
    base = ROOT / "app" / "domains"
    return sorted(
        d.name for d in base.iterdir()
        if d.is_dir() and not d.name.startswith("_") and d.name != "modules"
    )


def _force_register_all_domains():
    """Importa todos os domain.py para acionar @register_domain."""
    base = ROOT / "app" / "domains"
    failures = {}
    for d in base.iterdir():
        if not d.is_dir() or d.name.startswith("_") or d.name == "modules":
            continue
        domain_module = f"app.domains.{d.name}.domain"
        if not (d / "domain.py").exists():
            continue
        _, err = _safe_import(domain_module)
        if err:
            failures[d.name] = err
    return failures


def audit():
    print("=" * 80)
    print("LIA — Auditoria profunda do chat unificado")
    print("=" * 80)

    domain_dirs = _list_domain_dirs()
    REPORT["domain_dirs_total"] = len(domain_dirs)

    print(f"\n[1/6] Importando {len(domain_dirs)} domain dirs para acionar registry…")
    import_failures = _force_register_all_domains()
    REPORT["domain_import_failures"] = import_failures
    print(f"      Falhas de import: {len(import_failures)}")
    for name, err in list(import_failures.items())[:10]:
        print(f"        - {name}: {err[:140]}")

    print("\n[2/6] Carregando registry…")
    from app.domains.registry import DomainRegistry, _DOMAIN_REGISTRY
    registry = DomainRegistry()
    registered = sorted(str(k) for k in _DOMAIN_REGISTRY.keys() if isinstance(k, str))
    print(f"      Registered: {len(registered)} → {registered}")

    REPORT["domain_dirs_unregistered"] = sorted(
        set(domain_dirs)
        - {n for n in registered}
        - {"DOMAIN_CATALOG.md", "compliance_base.py"}
    )

    print("\n[3/6] Carregando mapping AGENT_TYPE_TO_DOMAIN…")
    from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, DEFAULT_DOMAIN
    REPORT["agent_type_mapping"] = dict(AGENT_TYPE_TO_DOMAIN)
    REPORT["default_domain"] = DEFAULT_DOMAIN
    unknown_targets = sorted({
        target for target in AGENT_TYPE_TO_DOMAIN.values() if target not in registered
    })
    REPORT["agent_types_pointing_to_unknown_domain"] = unknown_targets
    print(f"      Agent-types no mapping: {len(AGENT_TYPE_TO_DOMAIN)}")
    print(f"      Apontando para domínio NÃO registrado: {len(unknown_targets)}")
    for t in unknown_targets:
        sources = [k for k, v in AGENT_TYPE_TO_DOMAIN.items() if v == t]
        print(f"        - target='{t}' chamado por: {sources}")

    print("\n[4/6] Auditoria por domínio (actions, tools, handlers, mapping)…")
    for did in registered:
        info = _audit_domain(did, registry)
        REPORT["registered_domains"][did] = info
        gaps = info["gaps"]
        if any(gaps.values()):
            print(f"\n  ⚠️  {did}")
            for k, v in gaps.items():
                if v:
                    print(f"        {k}: {v if isinstance(v, int) else len(v)}")
        else:
            print(f"  ✅ {did}  ({info['action_count']} actions, {info['tool_count']} tools)")

    print("\n[5/6] Computing global summary…")
    REPORT["global_summary"] = _compute_summary()

    print("\n[6/6] Gravando relatórios…")
    out_json = ROOT / "docs" / "chat_capabilities_audit.json"
    out_json.write_text(json.dumps(REPORT, indent=2, default=str, ensure_ascii=False))
    print(f"      → {out_json}")
    return REPORT


def _audit_domain(did: str, registry) -> dict:
    info = {
        "class": None, "action_count": 0, "tool_count": 0,
        "actions": [], "tools": [], "action_tool_map": {},
        "gaps": {
            "action_tool_map_broken": [],
            "tools_orphaned_no_action": [],
            "actions_without_tool_or_handler": [],
            "handlers_failing_import": [],
        },
        "errors": [],
    }
    try:
        instance = registry.get_instance(did)
        if not instance:
            info["errors"].append("registry.get_instance returned None")
            return info
        info["class"] = type(instance).__name__
        actions = instance.get_allowed_actions() or []
        info["actions"] = [a.action_id for a in actions]
        info["action_count"] = len(actions)
    except Exception as e:
        info["errors"].append(f"get_allowed_actions: {e}")
        return info

    tools_mod, err = _safe_import(f"app.domains.{did}.tools")
    tools_list = []
    if tools_mod is not None:
        for attr in ("SOURCING_TOOLS", f"{did.upper()}_TOOLS", "TOOLS"):
            if hasattr(tools_mod, attr):
                t = getattr(tools_mod, attr)
                if isinstance(t, list):
                    tools_list = t
                    break
        if not tools_list:
            for name in dir(tools_mod):
                if name.endswith("_TOOLS") and isinstance(getattr(tools_mod, name), list):
                    tools_list = getattr(tools_mod, name)
                    break

    info["tools"] = [t.get("tool_id", t.get("name", "?")) for t in tools_list]
    info["tool_count"] = len(tools_list)

    domain_mod, _ = _safe_import(f"app.domains.{did}.domain")
    atm = getattr(domain_mod, "_ACTION_TOOL_MAP", None) if domain_mod else None
    if atm:
        info["action_tool_map"] = dict(atm)
        tool_ids = {t.get("tool_id") for t in tools_list}
        for action_id, tool_id in atm.items():
            if tool_id not in tool_ids:
                info["gaps"]["action_tool_map_broken"].append(
                    {"action": action_id, "missing_tool": tool_id}
                )

    if tools_list:
        mapped_tools = set(info["action_tool_map"].values())
        for t in tools_list:
            tid = t.get("tool_id")
            if tid not in mapped_tools:
                info["gaps"]["tools_orphaned_no_action"].append(tid)

    if domain_mod and did not in _INTENT_ROUTED_DOMAINS:
        domain_src = (ROOT / "app" / "domains" / did / "domain.py").read_text(errors="ignore")
        action_handler_keys = set()
        if "handler_map = {" in domain_src or "handler_map={" in domain_src:
            import re
            for m in re.finditer(r'"([a-z_]+)"\s*:\s*self\._handle', domain_src):
                action_handler_keys.add(m.group(1))
        mapped_actions = set(info["action_tool_map"].keys())
        for a in info["actions"]:
            if a not in mapped_actions and a not in action_handler_keys:
                info["gaps"]["actions_without_tool_or_handler"].append(a)
    elif did in _INTENT_ROUTED_DOMAINS:
        info["intent_routed"] = True

    for t in tools_list:
        handler = t.get("handler")
        if handler and isinstance(handler, str) and "." in handler:
            # Use the same progressive resolver as the runtime tool registry
            # and the unified-chat smoke gate, so all three agree.
            try:
                from app.shared.tool_handler import resolve_handler_path
                obj = resolve_handler_path(handler)
                if not callable(obj):
                    info["gaps"]["handlers_failing_import"].append(
                        {"tool_id": t.get("tool_id"), "handler": handler, "error": "resolved object is not callable"}
                    )
            except Exception as exc:
                info["gaps"]["handlers_failing_import"].append(
                    {"tool_id": t.get("tool_id"), "handler": handler, "error": f"{type(exc).__name__}: {exc}"[:160]}
                )

    return info


def _compute_summary() -> dict:
    s = {
        "total_registered": len(REPORT["registered_domains"]),
        "total_actions": 0,
        "total_tools": 0,
        "domains_with_gaps": 0,
        "broken_mappings": 0,
        "orphan_tools": 0,
        "actions_no_handler": 0,
        "broken_handlers": 0,
    }
    for did, info in REPORT["registered_domains"].items():
        s["total_actions"] += info["action_count"]
        s["total_tools"] += info["tool_count"]
        gaps = info["gaps"]
        if any(gaps.values()):
            s["domains_with_gaps"] += 1
        s["broken_mappings"] += len(gaps["action_tool_map_broken"])
        s["orphan_tools"] += len(gaps["tools_orphaned_no_action"])
        s["actions_no_handler"] += len(gaps["actions_without_tool_or_handler"])
        s["broken_handlers"] += len(gaps["handlers_failing_import"])
    return s


if __name__ == "__main__":
    try:
        audit()
        print("\n" + "=" * 80)
        print("Resumo global:", json.dumps(REPORT["global_summary"], indent=2))
    except Exception:
        traceback.print_exc()
        sys.exit(1)
