"""
Studio scope extension for the federated agent scope resolver.
Extends the base scope with tools from first-party Studio agents.

HOT FILE NOTE: scope_config.py (app/tools/scope_config.py) is NOT modified
beyond a single import line added at the bottom.
This module owns ALL Studio→scope integration logic.

Domain→PromptScope mapping:
  - first-party Studio agents declare `domains` (e.g. ["talent_analysis",
    "skill_gap"]) that overlap with existing PromptScope concepts.
  - This module maps those Studio domains to the canonical PromptScope
    values so that get_tools_for_scope/get_scoped_tool_definitions
    can transparently include Studio tools.
  - TENANT-FREE: first_party agents have company_id=None — intentional.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Module-level import so patch("...studio_scope_extension.CustomAgentRepository")
# works in tests. Circular import check: custom_agent_repository → lia_models only;
# does NOT import from app.orchestrator → safe.
from app.domains.agent_studio.repositories.custom_agent_repository import (  # noqa: E402
    CustomAgentRepository,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Studio domain → PromptScope mapping (canonical, single source of truth).
# Studio "domains" are finer-grained than PromptScope — many map to the
# same scope.  A Studio domain NOT listed here is treated as "global"
# (tools added to all scopes, safe conservative default).
# ---------------------------------------------------------------------------
_STUDIO_DOMAIN_TO_SCOPE: dict[str, str] = {
    # TalentIntelAgent domains
    "talent_analysis": "talent_funnel",
    "skill_gap": "talent_funnel",
    "candidate_nurture": "talent_funnel",
    # Both talent_funnel and job_table make sense; prefer job_table for planning
    "market_intelligence": "job_table",
    "workforce_planning": "job_table",
    # InterviewAnalysisAgent domains
    "interview_analysis": "in_job",
    "bias_detection": "in_job",
    "interview_feedback": "in_job",
}

# Cache: scope_str → sorted list of tool names contributed by Studio agents.
# None = not yet built (lazy). Cleared on any first-party update.
# TENANT-FREE: first_party agents are global — cache is shared across tenants.
_STUDIO_SCOPE_CACHE: dict[str, list[str]] | None = None
_CACHE_LOCK = asyncio.Lock()


async def get_studio_tools_for_scope(
    scope: str,
    db: "AsyncSession",
) -> list[str]:
    """
    Returns allowed_tools contributed by first-party Studio agents for scope.

    TENANT-FREE: first_party agents have company_id=None — global by design.
    Fail-open: returns [] on any error so the base scope is unaffected.
    """
    global _STUDIO_SCOPE_CACHE
    try:
        if _STUDIO_SCOPE_CACHE is None:
            async with _CACHE_LOCK:
                if _STUDIO_SCOPE_CACHE is None:
                    _STUDIO_SCOPE_CACHE = await _build_scope_cache(db)
        scope_str = (scope.value if hasattr(scope, "value") else str(scope)).strip().lower()
        return list(_STUDIO_SCOPE_CACHE.get(scope_str, []))
    except Exception as exc:
        logger.warning("[studio_scope_extension] get_studio_tools_for_scope(%s) failed: %s", scope, exc)
        return []


async def _build_scope_cache(db: "AsyncSession") -> dict[str, list[str]]:
    """Build scope→tools mapping from ALL active first-party Studio agents.

    # TENANT-FREE: querying first_party agents (company_id=None) — not a bug.
    """
    repo = CustomAgentRepository(db)
    agents = await repo.list_first_party_agents()

    cache: dict[str, list[str]] = {}
    for agent in agents:
        if not agent.domains:
            continue
        for studio_domain in agent.domains:
            scope_key = _STUDIO_DOMAIN_TO_SCOPE.get(str(studio_domain), "global")
            if scope_key not in cache:
                cache[scope_key] = []
            for tool in agent.allowed_tools or []:
                tool_name = str(tool)
                if tool_name not in cache[scope_key]:
                    cache[scope_key].append(tool_name)
    # Sort for deterministic ordering
    return {k: sorted(v) for k, v in cache.items()}


def invalidate_studio_scope_cache() -> None:
    """Call this when any first-party CustomAgent manifest is updated."""
    global _STUDIO_SCOPE_CACHE
    _STUDIO_SCOPE_CACHE = None
    logger.debug("[studio_scope_extension] Studio scope cache invalidated")


def get_studio_covered_domains() -> set[str]:
    """Returns the set of Studio domain names mapped (from the static config).

    Available without a DB session — safe to call synchronously anywhere.
    """
    return set(_STUDIO_DOMAIN_TO_SCOPE.keys())


def get_studio_covered_scopes() -> set[str]:
    """Returns PromptScope values that Studio agents contribute tools to.

    Derived from the static domain→scope map; independent of live DB state.
    Use this for fast checks before hitting the async cache.
    """
    return set(_STUDIO_DOMAIN_TO_SCOPE.values())


def get_studio_scope_cache_snapshot() -> dict[str, list[str]] | None:
    """Returns the current cached scope→tools mapping (None if not built).

    Useful for tests and observability — does not trigger a build.
    """
    return _STUDIO_SCOPE_CACHE
