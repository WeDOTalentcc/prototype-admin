"""
Tool Permissions Loader — Task #125.

Loads declarative tool scope permissions from YAML.
Supports global defaults with per-tenant overrides.

Replaces hardcoded Set[str] in scope_config.py with:
  - File-based config (tool_permissions.yaml)
  - Per-tenant customisation without code changes
  - Fallback chain: tenant override → global default → empty set

OWASP LLM06: Least-privilege tool access enforced via declarative config.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

_DEFAULT_PERMISSIONS_PATH = Path(__file__).parent / "tool_permissions.yaml"

VALID_SCOPES = {"talent_funnel", "job_table", "in_job", "global", "universal"}
VALID_TOOL_TYPES = {"query", "action", "all"}


class ToolPermissionsConfig:
    """
    Immutable snapshot of tool permissions for a given tenant.

    Built by ToolPermissionsLoader and cached per (tenant_id, yaml_path).
    """

    def __init__(
        self,
        tenant_id: str | None,
        scopes: dict[str, dict[str, set[str]]],
        llm_provider: str,
        llm_fallback_order: list[str],
        restricted_tools: set[str] | None = None,
    ) -> None:
        self._tenant_id = tenant_id
        self._scopes = scopes
        self._llm_provider = llm_provider
        self._llm_fallback_order = llm_fallback_order
        self._restricted_tools = restricted_tools or set()

    @property
    def tenant_id(self) -> str | None:
        return self._tenant_id

    @property
    def llm_provider(self) -> str:
        return self._llm_provider

    @property
    def llm_fallback_order(self) -> list[str]:
        return list(self._llm_fallback_order)

    def get_tools(self, scope: str, tool_type: str = "all") -> set[str]:
        """
        Return the allowed tool names for the given scope and type.

        Args:
            scope: One of talent_funnel, job_table, in_job, global.
            tool_type: "query", "action", or "all". Unknown values fall back to "all".

        Returns:
            Frozenset-like Set[str] — never mutate the returned object.
        """
        scope_lower = scope.lower()
        if scope_lower not in self._scopes:
            return set()

        scope_data = self._scopes[scope_lower]

        if tool_type == "all":
            combined = scope_data.get("query", set()) | scope_data.get("action", set())
            return set(combined)
        if tool_type not in ("query", "action"):
            # Unknown tool_type: fall back to "all"
            combined = scope_data.get("query", set()) | scope_data.get("action", set())
            return set(combined)
        # Return a copy to prevent callers from mutating cached internal state
        return set(scope_data.get(tool_type, set()))

    @property
    def restricted_tools(self) -> set[str]:
        """Return the set of tools that require explicit user confirmation."""
        return set(self._restricted_tools)

    def is_restricted(self, tool_name: str) -> bool:
        """Check if a tool requires explicit user confirmation (OWASP LLM06)."""
        return tool_name in self._restricted_tools

    def is_tool_allowed(self, tool_name: str, scope: str) -> bool:
        return tool_name in self.get_tools(scope, "all")

    def filter_tools(self, tools: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
        """Filter a list of tool definition dicts to those allowed in scope."""
        allowed = self.get_tools(scope, "all")
        return [t for t in tools if t.get("name") in allowed]

    def __repr__(self) -> str:
        return (
            f"<ToolPermissionsConfig tenant={self._tenant_id!r} "
            f"provider={self._llm_provider!r}>"
        )


class ToolPermissionsLoader:
    """
    Loads tool permissions from YAML and builds ToolPermissionsConfig objects.

    Singleton pattern with an in-memory cache keyed by (tenant_id, path).
    Call invalidate_cache() to reload config (e.g., in tests or hot-reload).
    """

    _instance: ToolPermissionsLoader | None = None
    _raw_config: dict[str, Any] | None = None
    _config_path: Path | None = None

    def __init__(self, path: Path | None = None) -> None:
        resolved = path or _DEFAULT_PERMISSIONS_PATH
        if self._config_path != resolved or self._raw_config is None:
            self.__class__._config_path = resolved
            self.__class__._raw_config = self._load_yaml(resolved)

    @classmethod
    def get_instance(cls, path: Path | None = None) -> ToolPermissionsLoader:
        if cls._instance is None:
            cls._instance = cls(path)
        return cls._instance

    @classmethod
    def invalidate_cache(cls) -> None:
        """Reset loaded config and cached per-tenant objects. Useful for tests."""
        cls._instance = None
        cls._raw_config = None
        cls._config_path = None
        _build_tenant_config.cache_clear()
        logger.debug("[ToolPermissionsLoader] Cache invalidated")

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not _YAML_AVAILABLE:
            logger.warning("[ToolPermissionsLoader] PyYAML not available; using empty config")
            return {}
        if not path.exists():
            logger.warning("[ToolPermissionsLoader] permissions file not found: %s", path)
            return {}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        logger.debug("[ToolPermissionsLoader] Loaded %s", path)
        return data

    def get_config(self, tenant_id: str | None = None) -> ToolPermissionsConfig:
        """
        Return the ToolPermissionsConfig for the given tenant (or global defaults).

        Results are cached via lru_cache on the module-level helper.
        """
        raw = self._raw_config or {}
        return _build_tenant_config(tenant_id, _freeze(raw))


_DICT_MARKER = "__dict__"
_LIST_MARKER = "__list__"


def _freeze(d: Any) -> Any:
    """Make a nested dict/list/set hashable for lru_cache.

    Uses type markers to distinguish dicts from lists on unfreeze.
    """
    if isinstance(d, dict):
        return (_DICT_MARKER, tuple(sorted((k, _freeze(v)) for k, v in d.items())))
    if isinstance(d, (list, set)):
        return (_LIST_MARKER, tuple(_freeze(i) for i in d))
    return d


@lru_cache(maxsize=256)
def _build_tenant_config(
    tenant_id: str | None,
    frozen_raw: Any,
) -> ToolPermissionsConfig:
    """Build and cache a ToolPermissionsConfig from frozen raw YAML data."""
    raw = _unfreeze(frozen_raw) or {}
    global_cfg = raw.get("global", {})
    global_scopes_raw = global_cfg.get("scopes", {})
    global_provider = global_cfg.get("llm_provider", "gemini")
    global_fallback = list(global_cfg.get("llm_fallback_order", ["claude", "gemini", "openai"]))

    # Build global scope sets
    scopes: dict[str, dict[str, set[str]]] = {}
    for scope_name, type_map in global_scopes_raw.items():
        scopes[scope_name] = {
            "query": set(type_map.get("query", [])),
            "action": set(type_map.get("action", [])),
        }

    provider = global_provider
    fallback_order = global_fallback

    # Apply per-tenant overrides if tenant_id is provided
    if tenant_id:
        tenants_cfg = raw.get("tenants", {}) or {}
        tenant_cfg = tenants_cfg.get(tenant_id, {})

        if tenant_cfg:
            provider = tenant_cfg.get("llm_provider", provider)
            fallback_order = list(tenant_cfg.get("llm_fallback_order", fallback_order))

            overrides = tenant_cfg.get("overrides", {}) or {}
            for scope_name, override in overrides.items():
                if scope_name not in scopes:
                    scopes[scope_name] = {"query": set(), "action": set()}

                if "add_query" in override:
                    scopes[scope_name]["query"].update(override["add_query"])
                if "add_action" in override:
                    scopes[scope_name]["action"].update(override["add_action"])
                if "remove" in override:
                    remove_set = set(override["remove"])
                    scopes[scope_name]["query"] -= remove_set
                    scopes[scope_name]["action"] -= remove_set

    # Load restricted tools list (OWASP LLM06 enforcement)
    restricted_tools = set(global_cfg.get("restricted_tools", []))

    return ToolPermissionsConfig(
        tenant_id=tenant_id,
        scopes=scopes,
        llm_provider=provider,
        llm_fallback_order=fallback_order,
        restricted_tools=restricted_tools,
    )


def _unfreeze(d: Any) -> Any:
    """Reverse _freeze() back to dict/list."""
    if isinstance(d, tuple) and len(d) == 2 and d[0] in (_DICT_MARKER, _LIST_MARKER):
        marker, payload = d
        if marker == _DICT_MARKER:
            return {k: _unfreeze(v) for k, v in payload}
        if marker == _LIST_MARKER:
            return [_unfreeze(i) for i in payload]
    return d


# ---------------------------------------------------------------------------
# Convenience module-level functions
# ---------------------------------------------------------------------------

def get_permissions(tenant_id: str | None = None) -> ToolPermissionsConfig:
    """
    Return ToolPermissionsConfig for the given tenant (or global defaults).

    This is the primary entry point for all permission checks.
    """
    return ToolPermissionsLoader.get_instance().get_config(tenant_id)


def get_tools_for_scope(
    scope: str,
    tool_type: str = "all",
    tenant_id: str | None = None,
) -> set[str]:
    """Convenience wrapper — returns allowed tool names for scope."""
    return get_permissions(tenant_id).get_tools(scope, tool_type)


def is_tool_allowed(
    tool_name: str,
    scope: str,
    tenant_id: str | None = None,
) -> bool:
    """Convenience wrapper — check single tool permission."""
    return get_permissions(tenant_id).is_tool_allowed(tool_name, scope)
