"""Loader for platform_tools.yaml — single source of truth for Agent Studio registries.

Replaces the 3 Python dicts that lived in custom_agent_runtime.py:
  - PLATFORM_TOOLS_REGISTRY  → get_platform_tools_registry()
  - HITL_REQUIRED_TOOLS      → get_hitl_required_tools()
  - domain_tool_loaders      → get_domain_tool_loaders()

The YAML is loaded once at import time (module-level cache).
"""
from __future__ import annotations

import pathlib
from functools import lru_cache
from typing import Any

import yaml

_CONFIG_PATH = pathlib.Path(__file__).parent / "config" / "platform_tools.yaml"


@lru_cache(maxsize=1)
def _load_yaml() -> dict[str, Any]:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_platform_tools_registry() -> dict[str, str]:
    """Returns {tool_name: "read"|"write"} for all platform tools."""
    data = _load_yaml()
    return {name: spec["access"] for name, spec in data["tools"].items()}


def get_hitl_required_tools() -> frozenset[str]:
    """Returns frozenset of tool names requiring HITL confirmation."""
    data = _load_yaml()
    return frozenset(data.get("hitl_required", []))


def get_domain_tool_loaders() -> dict[str, str]:
    """Returns {domain_name: dotted.import.path} for domain tool registries."""
    data = _load_yaml()
    return {name: spec["loader"] for name, spec in data.get("domains", {}).items()}


def get_available_tool_names() -> list[str]:
    """Returns list of all platform tool names."""
    return list(get_platform_tools_registry().keys())
