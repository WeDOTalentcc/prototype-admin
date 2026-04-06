# LIA-T07 — GlobalToolRegistry: acesso cross-domain a ferramentas com permissões read-only
# OWASP LLM06: Excessive Agency — GlobalToolRegistry limita escopo de ferramentas
# acessíveis por domínios externos, prevenindo side effects não autorizados.
#
# Task #125: Added tenant-aware tool filtering via declarative YAML permissions.

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ToolPermission(StrEnum):
    READ_ONLY = "read_only"     # Can only retrieve data
    READ_WRITE = "read_write"   # Can retrieve and modify
    ADMIN = "admin"             # Full access including delete


@dataclass
class ToolRegistration:
    tool: BaseTool
    domain: str
    permission: ToolPermission = ToolPermission.READ_ONLY
    description: str = ""
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


class GlobalToolRegistry:
    """Cross-domain tool registry with permission model.

    Domains can register their tools with a permission level.
    Other domains can discover and use tools, but external access
    is limited to READ_ONLY unless explicitly granted.

    LIA-T07: Previne Excessive Agency (OWASP LLM06) restringindo
    quais ferramentas podem ser acessadas cross-domain.

    Task #125: list_tools_for_scope() and get_tool_in_scope() add
    tenant-aware filtering via ToolPermissionsLoader (declarative YAML).
    """

    _instance: GlobalToolRegistry | None = None

    def __init__(self) -> None:
        self._registry: dict[str, ToolRegistration] = {}

    @classmethod
    def get_instance(cls) -> GlobalToolRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        tool: BaseTool,
        domain: str,
        permission: ToolPermission = ToolPermission.READ_ONLY,
        tags: list[str] | None = None,
    ) -> None:
        """Register a tool from a domain."""
        key = f"{domain}.{tool.name}"
        self._registry[key] = ToolRegistration(
            tool=tool,
            domain=domain,
            permission=permission,
            description=tool.description,
            tags=tags or [],
        )
        logger.debug(
            "[GlobalToolRegistry] Registered %s (%s) from domain %s",
            tool.name, permission.value, domain,
        )

    def get_tool(
        self,
        tool_name: str,
        requesting_domain: str,
        max_permission: ToolPermission = ToolPermission.READ_ONLY,
    ) -> BaseTool | None:
        """Get a tool by name, filtered by permission level.

        External domains can only access READ_ONLY tools by default.
        """
        for key, reg in self._registry.items():
            if not key.endswith(f".{tool_name}"):
                continue
            if not reg.enabled:
                continue
            if reg.domain == requesting_domain:
                return reg.tool
            if reg.permission == ToolPermission.READ_ONLY:
                return reg.tool
            if (
                reg.permission == ToolPermission.READ_WRITE
                and max_permission in (ToolPermission.READ_WRITE, ToolPermission.ADMIN)
            ):
                return reg.tool
            logger.warning(
                "[GlobalToolRegistry] Access denied: domain '%s' requested '%s' (permission=%s)",
                requesting_domain, tool_name, reg.permission.value,
            )
            return None
        return None

    def list_tools(
        self,
        requesting_domain: str,
        max_permission: ToolPermission = ToolPermission.READ_ONLY,
        tags: list[str] | None = None,
    ) -> list[BaseTool]:
        """List all accessible tools for a domain, optionally filtered by tags."""
        accessible = []
        for key, reg in self._registry.items():
            if not reg.enabled:
                continue
            if reg.domain != requesting_domain:
                if reg.permission != ToolPermission.READ_ONLY:
                    if not (
                        reg.permission == ToolPermission.READ_WRITE
                        and max_permission != ToolPermission.READ_ONLY
                    ):
                        continue
            if tags and not any(t in reg.tags for t in tags):
                continue
            accessible.append(reg.tool)
        return accessible

    def list_tools_for_scope(
        self,
        requesting_domain: str,
        scope: str,
        tenant_id: str | None = None,
        max_permission: ToolPermission = ToolPermission.READ_ONLY,
        tags: list[str] | None = None,
    ) -> list[BaseTool]:
        """
        List tools accessible to a domain AND allowed in the given scope for a tenant.

        Combines cross-domain permission checks with declarative scope permissions
        from ToolPermissionsLoader (tool_permissions.yaml).

        Args:
            requesting_domain: The domain requesting tool access.
            scope: Prompt scope string (talent_funnel, job_table, in_job, global).
            tenant_id: Tenant identifier for per-tenant scope overrides.
            max_permission: Maximum cross-domain permission level to allow.
            tags: Optional tag filter applied after scope filtering.

        Returns:
            List of BaseTool objects that pass both cross-domain and scope checks.
        """
        try:
            from app.tools.tool_permissions_loader import get_tools_for_scope
            scope_allowed: set[str] = get_tools_for_scope(scope, "all", tenant_id=tenant_id)
        except Exception as exc:
            logger.error(
                "[GlobalToolRegistry] SECURITY: Could not load scope permissions for "
                "scope=%s tenant=%s: %s — denying all tools (fail-closed)",
                scope, tenant_id, exc,
            )
            return []

        accessible = []
        for key, reg in self._registry.items():
            if not reg.enabled:
                continue

            # Scope filter from declarative YAML
            if scope_allowed is not None and reg.tool.name not in scope_allowed:
                continue

            # Cross-domain permission check
            if reg.domain != requesting_domain:
                if reg.permission != ToolPermission.READ_ONLY:
                    if not (
                        reg.permission == ToolPermission.READ_WRITE
                        and max_permission != ToolPermission.READ_ONLY
                    ):
                        continue

            if tags and not any(t in reg.tags for t in tags):
                continue

            accessible.append(reg.tool)

        return accessible

    def get_tool_in_scope(
        self,
        tool_name: str,
        requesting_domain: str,
        scope: str,
        tenant_id: str | None = None,
        max_permission: ToolPermission = ToolPermission.READ_ONLY,
    ) -> BaseTool | None:
        """
        Get a tool only if it passes both cross-domain permission AND scope checks.

        Args:
            tool_name: Name of the requested tool.
            requesting_domain: Domain making the request.
            scope: Prompt scope string.
            tenant_id: Tenant identifier for per-tenant overrides.
            max_permission: Maximum cross-domain permission.

        Returns:
            BaseTool if allowed, None otherwise.
        """
        try:
            from app.tools.tool_permissions_loader import is_tool_allowed
            if not is_tool_allowed(tool_name, scope, tenant_id=tenant_id):
                logger.warning(
                    "[GlobalToolRegistry] Scope denied: tool '%s' not in scope '%s' for tenant=%s",
                    tool_name, scope, tenant_id,
                )
                return None
        except Exception as exc:
            logger.error(
                "[GlobalToolRegistry] SECURITY: Scope check failed for tool '%s' "
                "scope=%s tenant=%s: %s — denying access (fail-closed)",
                tool_name, scope, tenant_id, exc,
            )
            return None

        return self.get_tool(tool_name, requesting_domain, max_permission)

    def disable_tool(self, domain: str, tool_name: str) -> bool:
        """Disable a tool (e.g., during compliance review)."""
        key = f"{domain}.{tool_name}"
        if key in self._registry:
            self._registry[key].enabled = False
            logger.info("[GlobalToolRegistry] Tool %s.%s disabled", domain, tool_name)
            return True
        return False

    def get_registry_summary(self) -> dict[str, Any]:
        """Returns summary of registered tools for observability."""
        by_domain: dict[str, list[str]] = {}
        for key, reg in self._registry.items():
            by_domain.setdefault(reg.domain, []).append(
                f"{reg.tool.name}({reg.permission.value})"
            )
        return {
            "total_tools": len(self._registry),
            "domains": list(by_domain.keys()),
            "by_domain": by_domain,
        }


# Module-level singleton accessor
def get_registry() -> GlobalToolRegistry:
    return GlobalToolRegistry.get_instance()
