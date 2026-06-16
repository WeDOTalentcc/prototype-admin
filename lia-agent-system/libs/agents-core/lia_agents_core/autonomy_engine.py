"""
AutonomyEngine — Maps company autonomy_level to dynamic guardrails for ReAct agents.

Loads CompanyHiringPolicy from PostgreSQL and resolves which tools require
user confirmation based on the company's configured automation_rules.autonomy_level.

Autonomy levels:
- "low"    → All destructive tools require confirmation (default)
- "medium" → Only critical tools require confirmation
- "high"   → Only irreversible actions need confirmation
"""
import logging
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from lia_config.database import AsyncSessionLocal
from app.models.company_hiring_policy import CompanyHiringPolicy, AUTOMATION_RULES_DEFAULTS

logger = logging.getLogger(__name__)

GUARDRAILS_BY_LEVEL: Dict[str, List[str]] = {
    "low": [
        "move_candidate",
        "batch_move",
        "reject_candidate",
        "schedule_interview",
        "generate_offer",
        "finalize_hiring",
        "create_job",
        "update_job",
        "delete_job",
        "send_message",
        "bulk_send",
    ],
    "medium": [
        "batch_move",
        "reject_candidate",
        "generate_offer",
        "finalize_hiring",
        "delete_job",
        "bulk_send",
    ],
    "high": [
        "finalize_hiring",
        "delete_job",
    ],
}

CACHE_TTL_SECONDS = 300


class AutonomyEngine:
    """Resolves dynamic guardrails for ReAct agents based on company hiring policy.

    Uses a simple in-memory dict cache with a 5-minute TTL so the database
    is not queried on every agent invocation.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def _load_policy(self, company_id: str) -> Optional[CompanyHiringPolicy]:
        """Load CompanyHiringPolicy from the database, using cache when available.

        Args:
            company_id: The company identifier to look up.

        Returns:
            The CompanyHiringPolicy instance, or None if not found.
        """
        cached = self._cache.get(company_id)
        if cached and (time.time() - cached["ts"]) < CACHE_TTL_SECONDS:
            logger.debug("AutonomyEngine cache hit for company_id=%s", company_id)
            return cached["policy"]

        logger.info("AutonomyEngine loading policy for company_id=%s", company_id)
        # REGRA-4-EXEMPT: fail-closed bootstrap. DB error → policy=None →
        # _get_autonomy_level(None) → "low" (autonomia minima). NAO eh LLM
        # call e nao mascara falha — caller intencionalmente trata None
        # como "deny by default" (canonical defensivo). Logger.exception
        # ja captura stack pra ops. Audit anchor: 2026-05-21 P0.D triage.
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(CompanyHiringPolicy).where(
                        CompanyHiringPolicy.company_id == company_id
                    )
                )
                policy = result.scalar_one_or_none()
        except Exception:
            logger.exception("AutonomyEngine failed to load policy for company_id=%s", company_id)
            policy = None

        self._cache[company_id] = {"policy": policy, "ts": time.time()}
        return policy

    def _get_autonomy_level(self, policy: Optional[CompanyHiringPolicy]) -> str:
        """Extract the autonomy_level string from a policy, defaulting to 'low'.

        Args:
            policy: The hiring policy record (may be None).

        Returns:
            One of 'low', 'medium', or 'high'.
        """
        if policy is None:
            return "low"
        automation_rules = policy.automation_rules or AUTOMATION_RULES_DEFAULTS  # type: ignore[union-attr]
        level: str = automation_rules.get("autonomy_level", "low")  # type: ignore[union-attr]
        if level not in GUARDRAILS_BY_LEVEL:
            logger.warning(
                "Unknown autonomy_level '%s' for company_id=%s, defaulting to 'low'",
                level,
                policy.company_id,
            )
            return "low"
        return level

    async def resolve_guardrails(self, company_id: str, domain: str) -> List[str]:
        """Resolve which tools require user confirmation for a given company.

        Args:
            company_id: The company identifier.
            domain: The agent domain requesting guardrails (for logging).

        Returns:
            List of tool names that must be confirmed before execution.
        """
        policy = await self._load_policy(company_id)
        level = self._get_autonomy_level(policy)
        guardrails = GUARDRAILS_BY_LEVEL[level]
        logger.info(
            "AutonomyEngine resolved guardrails for company_id=%s domain=%s level=%s count=%d",
            company_id,
            domain,
            level,
            len(guardrails),
        )
        return guardrails

    async def get_automation_config(self, company_id: str) -> Dict[str, Any]:
        """Return the full automation_rules dict for a company.

        Args:
            company_id: The company identifier.

        Returns:
            The automation_rules JSON block, or defaults if no policy exists.
        """
        policy = await self._load_policy(company_id)
        if policy is None:
            return dict(AUTOMATION_RULES_DEFAULTS)
        raw: Any = policy.automation_rules  # type: ignore[union-attr]
        if raw and isinstance(raw, dict):
            return dict(raw)
        return dict(AUTOMATION_RULES_DEFAULTS)

    async def can_auto_execute(self, company_id: str, tool_name: str) -> bool:
        """Check whether a tool can run without user confirmation.

        Args:
            company_id: The company identifier.
            tool_name: The name of the tool to check.

        Returns:
            True if the tool is NOT in the guardrails list (i.e. it can auto-execute).
        """
        policy = await self._load_policy(company_id)
        level = self._get_autonomy_level(policy)
        guardrails = GUARDRAILS_BY_LEVEL[level]
        return tool_name not in guardrails

    def invalidate_cache(self, company_id: Optional[str] = None) -> None:
        """Invalidate cached policies.

        Args:
            company_id: If provided, only invalidate this company's cache entry.
                        If None, clear the entire cache.
        """
        if company_id:
            self._cache.pop(company_id, None)
            logger.debug("AutonomyEngine cache invalidated for company_id=%s", company_id)
        else:
            self._cache.clear()
            logger.debug("AutonomyEngine cache fully cleared")
