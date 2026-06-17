"""
CrewAuditService — Audit trail for crew execution steps.

Logs each step of a crew execution to the existing audit infrastructure,
providing full traceability of delegation chains.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CrewAuditService:
    async def log_crew_started(
        self,
        crew_id: str,
        execution_id: str,
        company_id: str,
        crew_name: str,
        plan_name: str,
        total_tasks: int,
        roles: list[dict[str, Any]],
    ) -> None:
        await self._log(
            company_id=company_id,
            agent_name="crew_orchestrator",
            decision_type="crew_execution",
            action="crew_started",
            decision=f"Crew '{crew_name}' started with plan '{plan_name}' ({total_tasks} tasks)",
            reasoning=[
                f"crew_id={crew_id}",
                f"execution_id={execution_id}",
                f"roles={[r.get('agent_name') for r in roles]}",
            ],
        )

    async def log_task_started(
        self,
        execution_id: str,
        company_id: str,
        task_id: str,
        assigned_agent: str,
        action: str,
    ) -> None:
        await self._log(
            company_id=company_id,
            agent_name=assigned_agent,
            decision_type="crew_task",
            action="task_started",
            decision=f"Task '{task_id}' started: {action}",
            reasoning=[f"execution_id={execution_id}"],
        )

    async def log_task_completed(
        self,
        execution_id: str,
        company_id: str,
        task_id: str,
        assigned_agent: str,
        action: str,
        success: bool,
        duration_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        status = "completed" if success else "failed"
        reasoning = [f"execution_id={execution_id}", f"status={status}"]
        if duration_ms is not None:
            reasoning.append(f"duration_ms={duration_ms:.0f}")
        if error:
            reasoning.append(f"error={error}")

        await self._log(
            company_id=company_id,
            agent_name=assigned_agent,
            decision_type="crew_task",
            action=f"task_{status}",
            decision=f"Task '{task_id}' {status}: {action}",
            reasoning=reasoning,
        )

    async def log_delegation(
        self,
        execution_id: str,
        company_id: str,
        from_agent: str,
        to_agent: str,
        action: str,
        correlation_id: str,
    ) -> None:
        await self._log(
            company_id=company_id,
            agent_name=from_agent,
            decision_type="crew_delegation",
            action="delegate",
            decision=f"Delegated '{action}' to {to_agent}",
            reasoning=[
                f"execution_id={execution_id}",
                f"correlation_id={correlation_id}",
                f"to_agent={to_agent}",
            ],
        )

    async def log_crew_completed(
        self,
        crew_id: str,
        execution_id: str,
        company_id: str,
        crew_name: str,
        status: str,
        summary: dict[str, Any],
        duration_ms: float | None = None,
    ) -> None:
        reasoning = [
            f"crew_id={crew_id}",
            f"execution_id={execution_id}",
            f"status={status}",
        ]
        if duration_ms is not None:
            reasoning.append(f"duration_ms={duration_ms:.0f}")
        reasoning.append(f"summary={summary}")

        await self._log(
            company_id=company_id,
            agent_name="crew_orchestrator",
            decision_type="crew_execution",
            action="crew_completed",
            decision=f"Crew '{crew_name}' {status}",
            reasoning=reasoning,
        )

    async def _log(
        self,
        company_id: str,
        agent_name: str,
        decision_type: str,
        action: str,
        decision: str,
        reasoning: list[str],
    ) -> None:
        try:
            from app.shared.compliance.audit_service import audit_service
            await audit_service.log_decision(
                company_id=company_id,
                agent_name=agent_name,
                decision_type=decision_type,
                action=action,
                decision=decision,
                reasoning=reasoning,
                criteria_used=[
                    f"agent:{agent_name}",
                    f"decision_type:{decision_type}",
                    f"action:{action}",
                    f"decision:{decision}",
                    f"reasoning_count:{len(reasoning)}",
                ],
                criteria_ignored=[],
            )
        except Exception as exc:
            logger.warning("[CrewAudit] audit log failed (non-blocking): %s", exc)


crew_audit_service = CrewAuditService()
