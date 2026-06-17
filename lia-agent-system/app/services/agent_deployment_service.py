"""
AgentDeploymentService — Business logic for binding agents to targets.

Handles CRUD, validation, and automation trigger hooks.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.agent_deployment import AgentDeployment
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

MAX_DEPLOYMENTS_PER_AGENT = 10
MAX_DEPLOYMENTS_PER_TARGET = 5


class AgentDeploymentService:

    async def create_deployment(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        created_by: str,
        data: dict,
    ) -> AgentDeployment:
        """Create a deployment binding an agent to a target.

        Validates:
          - Agent exists and belongs to company
          - Agent is active or draft
          - Max deployments per agent not exceeded
          - Max deployments per target not exceeded
          - No duplicate (same agent + same target)
        """
        # Validate agent ownership
        agent = await db.execute(
            select(CustomAgent).where(
                and_(
                    CustomAgent.id == agent_id,
                    CustomAgent.company_id == company_id,
                )
            )
        )
        agent = agent.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found or does not belong to this company")
        if agent.status not in ("draft", "active"):
            raise ValueError(f"Agent status '{agent.status}' cannot be deployed")

        # Check max deployments per agent
        count = await db.scalar(
            select(func.count(AgentDeployment.id)).where(
                AgentDeployment.agent_id == agent_id
            )
        )
        if count >= MAX_DEPLOYMENTS_PER_AGENT:
            raise ValueError(f"Agent already has {count} deployments (max {MAX_DEPLOYMENTS_PER_AGENT})")

        # Check max deployments per target
        target_count = await db.scalar(
            select(func.count(AgentDeployment.id)).where(
                and_(
                    AgentDeployment.target_type == data["target_type"],
                    AgentDeployment.target_id == data["target_id"],
                    AgentDeployment.company_id == company_id,
                )
            )
        )
        if target_count >= MAX_DEPLOYMENTS_PER_TARGET:
            raise ValueError(f"Target already has {target_count} agents (max {MAX_DEPLOYMENTS_PER_TARGET})")

        # Check duplicate
        existing = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.agent_id == agent_id,
                    AgentDeployment.target_type == data["target_type"],
                    AgentDeployment.target_id == data["target_id"],
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("This agent is already deployed to this target")

        deployment = AgentDeployment(
            id=uuid4(),
            agent_id=agent_id,
            company_id=company_id,
            target_type=data["target_type"],
            target_id=data["target_id"],
            target_name=data.get("target_name"),
            trigger_mode=data.get("trigger_mode", "manual"),
            schedule_cron=data.get("schedule_cron"),
            config_overrides=data.get("config_overrides", {}),
            created_by=created_by,
        )
        db.add(deployment)
        logger.info(
            "[AgentDeploy] Created: agent=%s target=%s:%s trigger=%s company=%s",
            agent_id, data["target_type"], data["target_id"],
            data.get("trigger_mode", "manual"), company_id,
        )
        return deployment

    async def list_by_agent(
        self, db: AsyncSession, agent_id: str, company_id: str
    ) -> list[AgentDeployment]:
        result = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.agent_id == agent_id,
                    AgentDeployment.company_id == company_id,
                )
            ).order_by(AgentDeployment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_target(
        self,
        db: AsyncSession,
        company_id: str,
        target_type: str,
        target_id: str,
    ) -> list[AgentDeployment]:
        result = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.company_id == company_id,
                    AgentDeployment.target_type == target_type,
                    AgentDeployment.target_id == target_id,
                    AgentDeployment.is_active == True,
                )
            ).order_by(AgentDeployment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_targets(
        self,
        db: AsyncSession,
        company_id: str,
        target_type: str,
        target_ids: list[str],
    ) -> dict[str, list[AgentDeployment]]:
        """Onda 3.B1 — Batch list deployments for multiple targets in ONE query.

        Replaces N+1 from frontend Onda 2 (which called list_by_target N times).
        Returns a dict mapping each target_id (str) → list of active deployments.
        target_ids without deployments still get an empty list in the response.

        Multi-tenancy: company_id is the OUTER filter (RLS + explicit). target_ids
        are filtered IN within the tenant.
        """
        if not target_ids:
            return {}

        result = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.company_id == company_id,
                    AgentDeployment.target_type == target_type,
                    AgentDeployment.target_id.in_(target_ids),
                    AgentDeployment.is_active == True,
                )
            ).order_by(AgentDeployment.created_at.desc())
        )
        deployments = list(result.scalars().all())

        # Group by target_id (string normalization — model stores UUID, payload
        # may come as string).
        out: dict[str, list[AgentDeployment]] = {tid: [] for tid in target_ids}
        for d in deployments:
            key = str(d.target_id)
            if key in out:
                out[key].append(d)
            else:
                # Defensive — should not happen given the IN filter
                out[key] = [d]
        return out

    async def get_deployment(
        self, db: AsyncSession, deployment_id: str, company_id: str
    ) -> Optional[AgentDeployment]:
        result = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.id == deployment_id,
                    AgentDeployment.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_deployment(
        self, db: AsyncSession, deployment_id: str, company_id: str, data: dict
    ) -> Optional[AgentDeployment]:
        deployment = await self.get_deployment(db, deployment_id, company_id)
        if not deployment:
            return None
        for key, value in data.items():
            if value is not None and hasattr(deployment, key):
                setattr(deployment, key, value)
        return deployment

    async def delete_deployment(
        self, db: AsyncSession, deployment_id: str, company_id: str
    ) -> bool:
        deployment = await self.get_deployment(db, deployment_id, company_id)
        if not deployment:
            return False
        await db.delete(deployment)
        return True

    async def record_execution(
        self, db: AsyncSession, deployment_id: str, candidates_count: int = 1
    ) -> None:
        """Update deployment metrics after an execution."""
        deployment = await db.get(AgentDeployment, deployment_id)
        if deployment:
            deployment.execution_count = (deployment.execution_count or 0) + 1
            deployment.candidates_processed = (deployment.candidates_processed or 0) + candidates_count
            deployment.last_execution_at = datetime.now(timezone.utc)

    async def find_active_deployments_for_trigger(
        self,
        db: AsyncSession,
        company_id: str,
        target_type: str,
        target_id: str,
        trigger_mode: str,
    ) -> list[AgentDeployment]:
        """Find active deployments that match a trigger event.

        Used by automation hooks to find which agents should run
        when an event occurs (new candidate, stage change, etc).
        """
        result = await db.execute(
            select(AgentDeployment).where(
                and_(
                    AgentDeployment.company_id == company_id,
                    AgentDeployment.target_type == target_type,
                    AgentDeployment.target_id == target_id,
                    AgentDeployment.trigger_mode == trigger_mode,
                    AgentDeployment.is_active == True,
                )
            )
        )
        return list(result.scalars().all())


    async def bulk_create_deployments(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        created_by: str,
        target_type: str,
        target_ids: list[str],
        trigger_mode: str = "manual",
        schedule_cron: Optional[str] = None,
        is_active: bool = True,
        config_overrides: Optional[dict] = None,
    ) -> tuple[list[AgentDeployment], list[dict], list[dict]]:
        """Onda 3.B3 — Bulk acoplar 1 agente a N targets (atomic).

        Semantics:
          - Validation runs UPFRONT for the whole batch: agent exists, agent
            status deployable, every target_id has space (per-target cap),
            global agent cap not exceeded after addition.
          - Duplicates (target already has THIS agent active) are soft-skipped
            (added to `skipped`), not raised.
          - If ANY validation fails, the entire bulk is rolled back at the
            session level — caller is responsible for `db.rollback()` on
            exception.

        Returns:
            (created, skipped, failed) tuple:
              created: list[AgentDeployment] — newly inserted (not yet committed).
              skipped: list[dict] — {target_id, reason}.
              failed:  list[dict] — {target_id, error}.
        """
        # ── 1. Validate agent ownership + status ──────────────────────────
        agent_q = await db.execute(
            select(CustomAgent).where(
                and_(
                    CustomAgent.id == agent_id,
                    CustomAgent.company_id == company_id,
                )
            )
        )
        agent = agent_q.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found or does not belong to this company")
        if agent.status not in ("draft", "active"):
            raise ValueError(f"Agent status '{agent.status}' cannot be deployed")

        # ── 2. Check global agent cap ─────────────────────────────────────
        current_agent_count = await db.scalar(
            select(func.count(AgentDeployment.id)).where(
                AgentDeployment.agent_id == agent_id
            )
        ) or 0
        # Hipoteticamente max criados (assume worst-case sem skips). Real cap
        # check é mais permissivo porque skips não contam, mas falhar antes
        # da insert é mais barato que rollback.
        if current_agent_count + len(target_ids) > MAX_DEPLOYMENTS_PER_AGENT:
            raise ValueError(
                f"Bulk would exceed MAX_DEPLOYMENTS_PER_AGENT "
                f"({current_agent_count} + {len(target_ids)} > "
                f"{MAX_DEPLOYMENTS_PER_AGENT})"
            )

        # ── 3. Snapshot existing deployments for THIS agent within targets ─
        existing_q = await db.execute(
            select(AgentDeployment.target_id).where(
                and_(
                    AgentDeployment.agent_id == agent_id,
                    AgentDeployment.target_type == target_type,
                    AgentDeployment.target_id.in_(target_ids),
                    AgentDeployment.company_id == company_id,
                )
            )
        )
        existing_target_ids = {str(t) for t in existing_q.scalars().all()}

        # ── 4. Count deployments per target to enforce per-target cap ─────
        target_counts_q = await db.execute(
            select(
                AgentDeployment.target_id,
                func.count(AgentDeployment.id).label("cnt"),
            )
            .where(
                and_(
                    AgentDeployment.target_type == target_type,
                    AgentDeployment.target_id.in_(target_ids),
                    AgentDeployment.company_id == company_id,
                )
            )
            .group_by(AgentDeployment.target_id)
        )
        target_counts = {str(row[0]): row[1] for row in target_counts_q.all()}

        # ── 5. Iterate, classify, create ──────────────────────────────────
        created: list[AgentDeployment] = []
        skipped: list[dict] = []
        failed: list[dict] = []
        for tid in target_ids:
            tid_str = str(tid)
            if tid_str in existing_target_ids:
                skipped.append(
                    {"target_id": tid_str, "reason": "duplicate_active_deployment"}
                )
                continue
            current_tc = target_counts.get(tid_str, 0)
            if current_tc >= MAX_DEPLOYMENTS_PER_TARGET:
                failed.append(
                    {
                        "target_id": tid_str,
                        "error": (
                            f"Target já tem {current_tc} agentes "
                            f"(max {MAX_DEPLOYMENTS_PER_TARGET})"
                        ),
                    }
                )
                continue

            deployment = AgentDeployment(
                id=uuid4(),
                agent_id=agent_id,
                company_id=company_id,
                target_type=target_type,
                target_id=tid,
                target_name=None,
                trigger_mode=trigger_mode,
                schedule_cron=schedule_cron,
                config_overrides=config_overrides or {},
                is_active=is_active,
                created_by=created_by,
            )
            db.add(deployment)
            created.append(deployment)
            target_counts[tid_str] = current_tc + 1  # mantém invariant in-flight

        logger.info(
            "[AgentDeploy] Bulk: agent=%s target_type=%s requested=%d "
            "created=%d skipped=%d failed=%d company=%s",
            agent_id,
            target_type,
            len(target_ids),
            len(created),
            len(skipped),
            len(failed),
            company_id,
        )
        return created, skipped, failed


agent_deployment_service = AgentDeploymentService()
