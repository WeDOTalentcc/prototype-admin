"""
react_agent_registry — YAML-driven flat agent registry for lia_agents_core.

Moved/recreated as a shim after I3c cleanup. Original module was removed but
several consumers (tests + app.core.agent_registry_watcher) still import it.

API:
    _flat_registry    — dict[str, dict]  (module-level, mutable for tests)
    reload_from_yaml  — load YAML file and register enabled agents
    is_registered     — check if agent name is in registry
    get               — retrieve entry by name
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Module-level registry — mutable so tests can call .clear() for isolation
_flat_registry: dict[str, dict[str, Any]] = {}


def reload_from_yaml(yaml_path: str) -> list[str]:
    """Load agents from a YAML file and register enabled ones.

    Args:
        yaml_path: Path to a YAML file with an ``agents`` list.

    Returns:
        List of names of successfully registered (enabled) agents.
        Returns [] on file-not-found or YAML parse error (fail-open).
    """
    import os

    if not os.path.exists(yaml_path):
        logger.warning("[react_agent_registry] YAML not found: %s — returning []", yaml_path)
        return []

    try:
        import yaml  # type: ignore[import]
        with open(yaml_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("[react_agent_registry] Failed to load %s: %s", yaml_path, exc)
        return []

    agents = data.get("agents", [])
    if not isinstance(agents, list):
        logger.warning("[react_agent_registry] 'agents' key is not a list in %s", yaml_path)
        return []

    loaded: list[str] = []
    for entry in agents:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        if entry.get("enabled", True):  # enabled defaults to True if omitted
            _flat_registry[name] = entry
            loaded.append(name)

    logger.info("[react_agent_registry] Loaded %d agents from %s", len(loaded), yaml_path)
    return loaded


def is_registered(name: str) -> bool:
    """Return True if *name* is in the flat registry."""
    return name in _flat_registry


def get(name: str) -> dict[str, Any] | None:
    """Return the registry entry for *name*, or None if not registered."""
    return _flat_registry.get(name)
