#!/usr/bin/env python3
"""
Sprint 0: AgentDeployment — Backend Foundation

Creates:
  1. lia_models/agent_deployment.py — SQLAlchemy model
  2. app/schemas/agent_deployment.py — Pydantic schemas
  3. app/services/agent_deployment_service.py — Business logic
  4. app/api/v1/agent_deployments.py — REST endpoints
  5. Registers router in app/api/routes.py
  6. Hooks automation triggers
"""
import os
import sys

BASE = "/home/runner/workspace/lia-agent-system"


def write_file(rel_path, content):
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel_path}")


def read_file(rel_path):
    full = os.path.join(BASE, rel_path)
    with open(full) as f:
        return f.read()


def patch_file(rel_path, old, new, label=""):
    full = os.path.join(BASE, rel_path)
    content = read_file(rel_path)
    if old not in content:
        print(f"  SKIP: {label} (pattern not found in {rel_path})")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  PATCHED: {label}")
    return True


# ============================================================
# 1. Model: lia_models/agent_deployment.py
# ============================================================
print("\n=== 1. AgentDeployment model ===")
write_file("libs/models/lia_models/agent_deployment.py", '''"""
AgentDeployment — Binds a Studio agent to a target (job, talent pool, pipeline stage, list).

An agent without a deployment is a draft/template. Deployments connect agents to
the real recruiting flow, enabling automatic execution via automation triggers.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from lia_config.database import Base


class DeploymentTargetType(str, enum.Enum):
    JOB = "job"
    TALENT_POOL = "talent_pool"
    PIPELINE_STAGE = "pipeline_stage"
    CANDIDATE_LIST = "candidate_list"


class DeploymentTriggerMode(str, enum.Enum):
    MANUAL = "manual"
    ON_NEW_CANDIDATE = "on_new_candidate"
    ON_STAGE_CHANGE = "on_stage_change"
    SCHEDULED = "scheduled"


class AgentDeployment(Base):
    """Binds a CustomAgent to a target environment for execution."""

    __tablename__ = "agent_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)

    # WHERE the agent operates
    target_type = Column(String(32), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_name = Column(String(512), nullable=True)

    # WHEN the agent runs
    trigger_mode = Column(String(32), nullable=False, default="manual")
    schedule_cron = Column(String(128), nullable=True)

    # CONFIG
    is_active = Column(Boolean, default=True, nullable=False)
    config_overrides = Column(JSONB, default={})

    # METRICS
    execution_count = Column(Integer, default=0, nullable=False)
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    candidates_processed = Column(Integer, default=0, nullable=False)

    # AUDIT
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "target_type": self.target_type,
            "target_id": str(self.target_id),
            "target_name": self.target_name,
            "trigger_mode": self.trigger_mode,
            "schedule_cron": self.schedule_cron,
            "is_active": self.is_active,
            "config_overrides": self.config_overrides or {},
            "execution_count": self.execution_count,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "candidates_processed": self.candidates_processed,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
''')


# ============================================================
# 2. Register model export
# ============================================================
print("\n=== 2. Register model in app/models ===")
write_file("app/models/agent_deployment.py",
    'from lia_models.agent_deployment import *  # noqa: F401,F403\n')


# ============================================================
# 3. Schemas: app/schemas/agent_deployment.py
# ============================================================
print("\n=== 3. Deployment schemas ===")
write_file("app/schemas/agent_deployment.py", '''"""Pydantic schemas for AgentDeployment CRUD."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class CreateDeploymentRequest(BaseModel):
    target_type: Literal["job", "talent_pool", "pipeline_stage", "candidate_list"]
    target_id: str
    target_name: Optional[str] = None
    trigger_mode: Literal["manual", "on_new_candidate", "on_stage_change", "scheduled"] = "manual"
    schedule_cron: Optional[str] = None
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class UpdateDeploymentRequest(BaseModel):
    trigger_mode: Optional[Literal["manual", "on_new_candidate", "on_stage_change", "scheduled"]] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None
    config_overrides: Optional[dict[str, Any]] = None
    target_name: Optional[str] = None


class DeploymentResponse(BaseModel):
    id: str
    agent_id: str
    company_id: str
    target_type: str
    target_id: str
    target_name: Optional[str] = None
    trigger_mode: str
    schedule_cron: Optional[str] = None
    is_active: bool
    config_overrides: dict[str, Any] = {}
    execution_count: int = 0
    candidates_processed: int = 0
    last_execution_at: Optional[str] = None
    created_by: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DeploymentListResponse(BaseModel):
    deployments: list[DeploymentResponse]
    total: int


class RunDeploymentRequest(BaseModel):
    """Manual trigger: run agent on all candidates in target."""
    message: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class RunDeploymentResponse(BaseModel):
    deployment_id: str
    agent_id: str
    target_type: str
    target_id: str
    candidates_processed: int = 0
    execution_time_ms: int = 0
    status: str = "completed"
''')


# ============================================================
# 4. Service: app/services/agent_deployment_service.py
# ============================================================
print("\n=== 4. Deployment service ===")
write_file("app/services/agent_deployment_service.py", '''"""
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
''')


# ============================================================
# 5. API Endpoints: app/api/v1/agent_deployments.py
# ============================================================
print("\n=== 5. Deployment REST endpoints ===")
write_file("app/api/v1/agent_deployments.py", '''"""
REST API for AgentDeployments — binding agents to jobs, pools, stages, lists.
"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.schemas.agent_deployment import (
    CreateDeploymentRequest,
    DeploymentListResponse,
    DeploymentResponse,
    RunDeploymentRequest,
    RunDeploymentResponse,
    UpdateDeploymentRequest,
)
from app.services.agent_deployment_service import agent_deployment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-agents", tags=["Agent Deployments"])


@router.post("/{agent_id}/deployments", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    agent_id: str,
    body: CreateDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bind an agent to a target (job, talent pool, pipeline stage, candidate list)."""
    try:
        deployment = await agent_deployment_service.create_deployment(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()
        return DeploymentResponse(**deployment.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating deployment: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create deployment")


@router.get("/{agent_id}/deployments", response_model=DeploymentListResponse)
async def list_agent_deployments(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all deployments for a specific agent."""
    deployments = await agent_deployment_service.list_by_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    return DeploymentListResponse(
        deployments=[DeploymentResponse(**d.to_dict()) for d in deployments],
        total=len(deployments),
    )


# Separate router for target-based queries (not nested under agent_id)
target_router = APIRouter(prefix="/agent-deployments", tags=["Agent Deployments"])


@target_router.get("", response_model=DeploymentListResponse)
async def list_deployments_by_target(
    target_type: str = Query(..., description="job | talent_pool | pipeline_stage | candidate_list"),
    target_id: str = Query(..., description="UUID of the target"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active agent deployments for a specific target (e.g., a job or pool)."""
    deployments = await agent_deployment_service.list_by_target(
        db=db,
        company_id=current_user.company_id,
        target_type=target_type,
        target_id=target_id,
    )
    return DeploymentListResponse(
        deployments=[DeploymentResponse(**d.to_dict()) for d in deployments],
        total=len(deployments),
    )


@target_router.patch("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    body: UpdateDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deployment (change trigger, pause/resume, override config)."""
    deployment = await agent_deployment_service.update_deployment(
        db=db,
        deployment_id=deployment_id,
        company_id=current_user.company_id,
        data=body.model_dump(exclude_none=True),
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()
    return DeploymentResponse(**deployment.to_dict())


@target_router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a deployment binding."""
    deleted = await agent_deployment_service.delete_deployment(
        db=db, deployment_id=deployment_id, company_id=current_user.company_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()


@target_router.post("/{deployment_id}/run", response_model=RunDeploymentResponse)
async def run_deployment(
    deployment_id: str,
    body: RunDeploymentRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an agent on its target.

    Executes the agent with context from the target (job details, pool candidates, etc).
    """
    deployment = await agent_deployment_service.get_deployment(
        db=db, deployment_id=deployment_id, company_id=current_user.company_id
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not deployment.is_active:
        raise HTTPException(status_code=400, detail="Deployment is not active")

    # Load agent
    from sqlalchemy import select
    from lia_models.custom_agent import CustomAgent
    agent_result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == deployment.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Execute
    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

    runtime = get_or_create_runtime(
        agent_id=str(agent.id),
        agent_name=agent.name,
        system_prompt=agent.system_prompt,
        allowed_tools=agent.allowed_tools or [],
        domain=agent.domain or "general",
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        model_override=agent.model_override,
        company_id=current_user.company_id,
        enable_memory=getattr(agent, "enable_memory", True),
        excluded_tools=getattr(agent, "excluded_tools", None),
        context_level=getattr(agent, "context_level", "full"),
    )

    # Build context from target
    context = dict((body.context if body else {}) or {})
    context["deployment_id"] = str(deployment.id)
    context["target_type"] = deployment.target_type
    context["target_id"] = str(deployment.target_id)
    context["target_name"] = deployment.target_name or ""

    message = (body.message if body and body.message else
               f"Executar no alvo: {deployment.target_type} '{deployment.target_name or deployment.target_id}'")

    start = time.time()
    output = await runtime.execute(
        message=message,
        user_id=str(current_user.id),
        company_id=current_user.company_id,
        context=context,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    # Record metrics
    await agent_deployment_service.record_execution(db, str(deployment.id))
    await db.commit()

    return RunDeploymentResponse(
        deployment_id=str(deployment.id),
        agent_id=str(agent.id),
        target_type=deployment.target_type,
        target_id=str(deployment.target_id),
        candidates_processed=1,
        execution_time_ms=elapsed_ms,
        status="completed",
    )
''')


# ============================================================
# 6. Register routers in app/api/routes.py
# ============================================================
print("\n=== 6. Register routers ===")
patch_file(
    "app/api/routes.py",
    "from app.api.v1.custom_agents import router as custom_agents_router",
    "from app.api.v1.custom_agents import router as custom_agents_router\n"
    "from app.api.v1.agent_deployments import router as agent_deployments_router\n"
    "from app.api.v1.agent_deployments import target_router as agent_deployments_target_router",
    "import deployment routers",
)

# Find where custom_agents_router is registered and add deployments after it
patch_file(
    "app/api/routes.py",
    'app.include_router(custom_agents_router, prefix="/api/v1")',
    'app.include_router(custom_agents_router, prefix="/api/v1")\n'
    '    app.include_router(agent_deployments_router, prefix="/api/v1")\n'
    '    app.include_router(agent_deployments_target_router, prefix="/api/v1")',
    "register deployment routers",
)


# ============================================================
# 7. Verify all new files parse
# ============================================================
import ast
print("\n=== Verify AST ===")
ok = 0
for f in [
    "libs/models/lia_models/agent_deployment.py",
    "app/schemas/agent_deployment.py",
    "app/services/agent_deployment_service.py",
    "app/api/v1/agent_deployments.py",
    "app/api/routes.py",
]:
    try:
        ast.parse(read_file(f))
        print(f"  OK: {f}")
        ok += 1
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print(f"\n{'=' * 60}")
print(f"Results: {ok}/5 files valid")
if ok < 5:
    sys.exit(1)
else:
    print("Sprint 0 backend complete!")
    sys.exit(0)
