"""
AgentVersionService — Gerencia historico de versoes de Custom Agents.

Operacoes:
  - create_snapshot(agent_before_update, changed_fields, reason, user_id)
  - list_versions(agent_id, company_id, limit, offset)
  - get_version(agent_id, version, company_id)
  - revert(agent_id, target_version, reverted_by)
"""
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agent_studio.repositories.agent_version_snapshot_repository import AgentVersionSnapshotRepository
from lia_models.agent_version_snapshot import AgentVersionSnapshot
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

# Fields included in snapshot (editaveis)
SNAPSHOT_FIELDS = [
    "name", "role", "description", "system_prompt", "allowed_tools",
    "domain", "icon", "config", "max_steps", "temperature", "model_override",
    "enable_memory", "context_level", "excluded_tools",
]


class AgentVersionService:

    async def create_snapshot(
        self,
        db: AsyncSession,
        agent: CustomAgent,
        changed_fields: list[str],
        changed_by: str,
        change_reason: Optional[str] = None,
    ) -> AgentVersionSnapshot:
        """Create a snapshot of the agent's current state BEFORE update is applied."""
        snapshot_data = {f: getattr(agent, f, None) for f in SNAPSHOT_FIELDS}

        # Normalize non-JSON-safe values
        for k, v in list(snapshot_data.items()):
            if hasattr(v, "isoformat"):
                snapshot_data[k] = v.isoformat()

        snapshot = AgentVersionSnapshot(
            id=uuid4(),
            agent_id=agent.id,
            company_id=agent.company_id,
            version=agent.version or 1,
            snapshot_data=snapshot_data,
            changed_fields=changed_fields,
            change_reason=change_reason,
            changed_by=changed_by,
        )
        db.add(snapshot)

        # Increment agent version
        agent.version = (agent.version or 1) + 1

        logger.info(
            "[AgentVersion] snapshot created: agent=%s version=%s fields=%s by=%s",
            agent.id, snapshot.version, changed_fields, changed_by,
        )
        return snapshot

    async def list_versions(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AgentVersionSnapshot], int]:
        """List version snapshots for an agent, newest first (ADR-001: via repository)."""
        repo = AgentVersionSnapshotRepository(db)
        return await repo.list_for_agent(agent_id, company_id, limit, offset)

    async def get_version(
        self,
        db: AsyncSession,
        agent_id: str,
        version: int,
        company_id: str,
    ) -> Optional[AgentVersionSnapshot]:
        """Get specific version snapshot (ADR-001: via repository)."""
        repo = AgentVersionSnapshotRepository(db)
        return await repo.get_by_version(agent_id, version, company_id)

    async def revert(
        self,
        db: AsyncSession,
        agent: CustomAgent,
        target_version: int,
        reverted_by: str,
    ) -> CustomAgent:
        """Revert agent to a previous version. Creates a new snapshot before reverting."""
        target = await self.get_version(db, str(agent.id), target_version, agent.company_id)
        if not target:
            raise ValueError(f"Version {target_version} not found")

        # Snapshot current state before reverting
        current_fields = list(SNAPSHOT_FIELDS)
        await self.create_snapshot(
            db=db,
            agent=agent,
            changed_fields=current_fields,
            changed_by=reverted_by,
            change_reason=f"Revert to version {target_version}",
        )

        # Apply snapshot data
        for field, value in (target.snapshot_data or {}).items():
            if field in SNAPSHOT_FIELDS and hasattr(agent, field):
                setattr(agent, field, value)

        logger.info(
            "[AgentVersion] reverted: agent=%s to version=%s by=%s",
            agent.id, target_version, reverted_by,
        )
        return agent


agent_version_service = AgentVersionService()
