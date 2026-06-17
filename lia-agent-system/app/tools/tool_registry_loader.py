"""
YAML Tool Registry Loader — Sprint G5.

Provides declarative metadata for tools via YAML.
Handlers remain in Python; YAML covers:
  - name, description, allowed_agents, scope, version

Usage:
    from app.tools.tool_registry_loader import (
        load_tool_metadata,
        export_registry_to_yaml,
        validate_registry_against_yaml,
    )

Portabilidade: loader é stateless e pode ser usado em qualquer runtime Python.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

_DEFAULT_YAML_PATH = Path(__file__).parent / "tool_registry_metadata.yaml"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_tool_metadata(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Load tool metadata from YAML file.

    Returns a dict keyed by tool name:
        {
            "search_salary_benchmark": {
                "description": "...",
                "allowed_agents": [...],
                "scope": "JOB_TABLE",
                "version": "1.0",
                "parameters": {...},
            },
            ...
        }
    """
    if not _YAML_AVAILABLE:
        logger.warning("PyYAML not installed; returning empty metadata")
        return {}

    target = path or _DEFAULT_YAML_PATH
    if not target.exists():
        logger.warning(f"Tool metadata YAML not found at {target}")
        return {}

    with target.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    tools_list: list[dict[str, Any]] = data.get("tools", [])
    return {t["name"]: t for t in tools_list if "name" in t}


def export_registry_to_yaml(
    registry_tools: list[Any],
    path: Path | None = None,
) -> str:
    """
    Serialize ToolDefinition objects to YAML string (and optionally write to file).

    Args:
        registry_tools: list of ToolDefinition objects from tool_registry.
        path: if provided, write to this file.

    Returns:
        YAML string.
    """
    if not _YAML_AVAILABLE:
        raise RuntimeError("PyYAML is required for YAML export. Install with: pip install pyyaml")

    serialized = []
    for tool in registry_tools:
        entry: dict[str, Any] = {
            "name": tool.name,
            "description": tool.description,
            "allowed_agents": tool.allowed_agents,
            "parameters": tool.parameters_schema,
        }
        serialized.append(entry)

    document = {"tools": serialized}
    yaml_str = yaml.dump(document, allow_unicode=True, sort_keys=False, default_flow_style=False)

    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml_str, encoding="utf-8")
        logger.info(f"Exported {len(serialized)} tools to {path}")

    return yaml_str


def validate_registry_against_yaml(
    registry_tools: list[Any],
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Validate registered tools against the YAML metadata snapshot.

    Returns a report dict:
        {
            "ok": bool,
            "missing_in_yaml": [tool_names],   # in registry but not in yaml
            "missing_in_registry": [names],    # in yaml but not registered
            "description_mismatches": [...],   # description differs
        }
    """
    metadata = load_tool_metadata(path)
    registered_names = {t.name for t in registry_tools}
    yaml_names = set(metadata.keys())

    missing_in_yaml = sorted(registered_names - yaml_names)
    missing_in_registry = sorted(yaml_names - registered_names)

    description_mismatches: list[dict[str, str]] = []
    for tool in registry_tools:
        if tool.name in metadata:
            yaml_desc = metadata[tool.name].get("description", "")
            if yaml_desc and yaml_desc.strip() != tool.description.strip():
                description_mismatches.append({
                    "tool": tool.name,
                    "registry": tool.description[:80],
                    "yaml": yaml_desc[:80],
                })

    missing_returns = [name for name, meta in metadata.items() if "returns" not in meta]

    ok = not missing_in_yaml and not missing_in_registry and not description_mismatches  # missing_returns is a warning only
    report = {
        "ok": ok,
        "registered_count": len(registered_names),
        "yaml_count": len(yaml_names),
        "missing_in_yaml": missing_in_yaml,
        "missing_in_registry": missing_in_registry,
        "description_mismatches": description_mismatches,
        "missing_returns": missing_returns,
    }
    if missing_returns:
        report["warnings"] = report.get("warnings", []) + [
            f"Tools missing returns: {missing_returns}"
        ]

    if not ok:
        logger.warning(f"Tool registry YAML validation issues: {report}")
    else:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Tool registry YAML validation OK — {len(registered_names)} tools")

    return report
