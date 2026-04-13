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


agent_deployment_service = AgentDeploymentService()
