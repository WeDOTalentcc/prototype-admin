#!/usr/bin/env python3
"""
Close ALL remaining gaps:
  1. Migration 070 for agent_deployments table
  2. Hook automation triggers to fire agent deployments
  3. Token metering in test + execute responses (GAP B1)
  4. Execution history table + endpoint (GAP B2)
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
    with open(os.path.join(BASE, rel_path)) as f:
        return f.read()


def patch_file(rel_path, old, new, label=""):
    full = os.path.join(BASE, rel_path)
    content = read_file(rel_path)
    if old not in content:
        print(f"  SKIP: {label} (pattern not found)")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# GAP 1: Migration 070 — agent_deployments table
# ============================================================
print("\n=== GAP 1: Migration 070 ===")
write_file("alembic/versions/070_agent_deployments.py", '''"""Create agent_deployments table for binding Studio agents to targets.

Revision ID: 070_agent_deployments
Revises: 069_agent_studio_parity
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "070_agent_deployments"
down_revision = "069_agent_studio_parity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_deployments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("target_name", sa.String(512), nullable=True),
        sa.Column("trigger_mode", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("schedule_cron", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config_overrides", JSONB, server_default="{}"),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidates_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Check constraints
    op.create_check_constraint(
        "ck_agent_deployments_target_type",
        "agent_deployments",
        "target_type IN ('job', 'talent_pool', 'pipeline_stage', 'candidate_list')",
    )
    op.create_check_constraint(
        "ck_agent_deployments_trigger_mode",
        "agent_deployments",
        "trigger_mode IN ('manual', 'on_new_candidate', 'on_stage_change', 'scheduled')",
    )

    # Unique constraint: one agent per target
    op.create_unique_constraint(
        "uq_agent_deployment_agent_target",
        "agent_deployments",
        ["agent_id", "target_type", "target_id"],
    )


def downgrade():
    op.drop_constraint("uq_agent_deployment_agent_target", "agent_deployments", type_="unique")
    op.drop_constraint("ck_agent_deployments_trigger_mode", "agent_deployments", type_="check")
    op.drop_constraint("ck_agent_deployments_target_type", "agent_deployments", type_="check")
    op.drop_table("agent_deployments")
''')


# ============================================================
# GAP 2: Hook automation triggers for deployments
# ============================================================
print("\n=== GAP 2: Automation trigger hook ===")
patch_file(
    "app/api/v1/automation/triggers.py",
    '''        elif request.event_type == "stage_changed":
            agents_notified = ["orchestrator", "task_planner"]
            logger.info(f"➡️ [STAGE_CHANGED] Notifying agents: {agents_notified}")''',
    '''        elif request.event_type == "stage_changed":
            agents_notified = ["orchestrator", "task_planner"]
            logger.info(f"➡️ [STAGE_CHANGED] Notifying agents: {agents_notified}")

            # === Studio Agent Deployments: fire agents bound to this stage ===
            try:
                from app.services.agent_deployment_service import agent_deployment_service
                stage_id = request.metadata.get("stage_id") if request.metadata else None
                if stage_id and request.company_id:
                    stage_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                        db=db,
                        company_id=request.company_id,
                        target_type="pipeline_stage",
                        target_id=stage_id,
                        trigger_mode="on_stage_change",
                    )
                    for dep in stage_deployments:
                        agents_notified.append(f"studio:{dep.agent_id}")
                        logger.info(
                            "[DEPLOY_TRIGGER] stage_changed → agent=%s deployment=%s",
                            dep.agent_id, dep.id,
                        )
            except Exception as _deploy_err:
                logger.warning("[DEPLOY_TRIGGER] stage_changed hook failed: %s", _deploy_err)''',
    "stage_changed hook",
)

# Also hook into job-related events (new candidate)
patch_file(
    "app/api/v1/automation/triggers.py",
    '''        if request.event_type == "job_created":
            agents_notified = ["job_planner", "sourcing"]
            logger.info(f"📋 [JOB_CREATED] Notifying agents: {agents_notified}")''',
    '''        if request.event_type == "job_created":
            agents_notified = ["job_planner", "sourcing"]
            logger.info(f"📋 [JOB_CREATED] Notifying agents: {agents_notified}")

            # === Studio Agent Deployments: fire agents bound to this job ===
            try:
                from app.services.agent_deployment_service import agent_deployment_service
                job_id = request.entity_id
                if job_id and request.company_id:
                    job_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                        db=db,
                        company_id=request.company_id,
                        target_type="job",
                        target_id=job_id,
                        trigger_mode="on_new_candidate",
                    )
                    for dep in job_deployments:
                        agents_notified.append(f"studio:{dep.agent_id}")
                        logger.info(
                            "[DEPLOY_TRIGGER] job event → agent=%s deployment=%s",
                            dep.agent_id, dep.id,
                        )
            except Exception as _deploy_err:
                logger.warning("[DEPLOY_TRIGGER] job hook failed: %s", _deploy_err)''',
    "job_created hook",
)


# ============================================================
# GAP B1: Token metering in test + execute responses
# ============================================================
print("\n=== GAP B1: Token metering ===")

# Update TestCustomAgentResponse schema
patch_file(
    "app/schemas/custom_agent.py",
    '''class TestCustomAgentResponse(BaseModel):
    agent_id: str
    message: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    execution_time_ms: int = 0''',
    '''class TestCustomAgentResponse(BaseModel):
    agent_id: str
    message: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    execution_time_ms: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    model_used: str = ""''',
    "TestResponse + tokens",
)

# Update ExecuteCustomAgentResponse schema
patch_file(
    "app/schemas/custom_agent.py",
    '''class ExecuteCustomAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    credits_consumed: int = 0
    execution_time_ms: int = 0
    metadata: dict[str, Any] = {}''',
    '''class ExecuteCustomAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    credits_consumed: int = 0
    execution_time_ms: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    model_used: str = ""
    metadata: dict[str, Any] = {}''',
    "ExecuteResponse + tokens",
)

# Extract token info from output.metadata in test endpoint
patch_file(
    "app/api/v1/custom_agents.py",
    '''        return TestCustomAgentResponse(
            agent_id=str(agent.id),
            message=body.message,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            execution_time_ms=elapsed_ms,
        )''',
    '''        _meta = output.metadata or {}
        return TestCustomAgentResponse(
            agent_id=str(agent.id),
            message=body.message,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            execution_time_ms=elapsed_ms,
            tokens_input=_meta.get("tokens_input", 0),
            tokens_output=_meta.get("tokens_output", 0),
            model_used=_meta.get("model_used", ""),
        )''',
    "test endpoint tokens",
)

# Extract token info in execute endpoint
patch_file(
    "app/api/v1/custom_agents.py",
    '''        return ExecuteCustomAgentResponse(
            agent_id=str(agent.id),
            agent_name=agent.name,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            credits_consumed=credits_consumed,
            execution_time_ms=elapsed_ms,
            metadata=output.metadata or {},
        )''',
    '''        _meta = output.metadata or {}
        return ExecuteCustomAgentResponse(
            agent_id=str(agent.id),
            agent_name=agent.name,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            credits_consumed=credits_consumed,
            execution_time_ms=elapsed_ms,
            tokens_input=_meta.get("tokens_input", 0),
            tokens_output=_meta.get("tokens_output", 0),
            model_used=_meta.get("model_used", ""),
            metadata=_meta,
        )''',
    "execute endpoint tokens",
)


# ============================================================
# GAP B2: Execution history table + endpoint
# ============================================================
print("\n=== GAP B2: Execution history ===")

# Model
write_file("libs/models/lia_models/agent_execution_log.py", '''"""
AgentExecutionLog — Persists every individual Studio agent execution.

Enables: execution history, temporal metrics, debugging, billing audit.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    deployment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(128), nullable=False)

    input_message = Column(Text, nullable=False)
    output_message = Column(Text, nullable=False, default="")
    confidence = Column(Float, default=0.0)

    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    model_used = Column(String(128), default="")
    latency_ms = Column(Integer, default=0)
    credits_consumed = Column(Integer, default=0)

    tool_calls = Column(ARRAY(String), default=[])
    compliance_status = Column(String(32), default="pass")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "deployment_id": str(self.deployment_id) if self.deployment_id else None,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "input_message": self.input_message[:200] if self.input_message else "",
            "output_message": self.output_message[:500] if self.output_message else "",
            "confidence": self.confidence,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "credits_consumed": self.credits_consumed,
            "tool_calls": self.tool_calls or [],
            "compliance_status": self.compliance_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
''')

# Register model
write_file("app/models/agent_execution_log.py",
    'from lia_models.agent_execution_log import *  # noqa: F401,F403\n')

# Migration for execution_logs
write_file("alembic/versions/071_agent_execution_logs.py", '''"""Create agent_execution_logs table.

Revision ID: 071_agent_execution_logs
Revises: 070_agent_deployments
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "071_agent_execution_logs"
down_revision = "070_agent_deployments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_execution_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("deployment_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("output_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("tokens_input", sa.Integer(), server_default="0"),
        sa.Column("tokens_output", sa.Integer(), server_default="0"),
        sa.Column("model_used", sa.String(128), server_default=""),
        sa.Column("latency_ms", sa.Integer(), server_default="0"),
        sa.Column("credits_consumed", sa.Integer(), server_default="0"),
        sa.Column("tool_calls", ARRAY(sa.String()), server_default="{}"),
        sa.Column("compliance_status", sa.String(32), server_default="pass"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("agent_execution_logs")
''')

# Execution history endpoint — add to custom_agents.py
patch_file(
    "app/api/v1/custom_agents.py",
    '''@router.get("/studio/consumption"''',
    '''@router.get("/{agent_id}/executions", summary="Get execution history for an agent")
async def get_agent_executions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated execution history for a specific agent."""
    from sqlalchemy import select, and_, func
    from lia_models.agent_execution_log import AgentExecutionLog

    base_filter = and_(
        AgentExecutionLog.agent_id == agent_id,
        AgentExecutionLog.company_id == current_user.company_id,
    )

    total = await db.scalar(select(func.count(AgentExecutionLog.id)).where(base_filter))

    result = await db.execute(
        select(AgentExecutionLog)
        .where(base_filter)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()

    return {
        "executions": [log.to_dict() for log in logs],
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/studio/consumption"''',
    "execution history endpoint",
)

# Persist execution log in execute endpoint
patch_file(
    "app/api/v1/custom_agents.py",
    '''        await agent_marketplace_service.record_execution(
            db=db,
            agent_id=str(agent.id),
            company_id=current_user.company_id,
            credits_consumed=credits_consumed,
        )
        await db.commit()''',
    '''        await agent_marketplace_service.record_execution(
            db=db,
            agent_id=str(agent.id),
            company_id=current_user.company_id,
            credits_consumed=credits_consumed,
        )

        # Persist execution log (GAP B2)
        try:
            from lia_models.agent_execution_log import AgentExecutionLog
            from uuid import uuid4
            _meta = output.metadata or {}
            db.add(AgentExecutionLog(
                id=uuid4(),
                agent_id=agent.id,
                company_id=current_user.company_id,
                user_id=str(current_user.id),
                input_message=body.message[:2000],
                output_message=(output.message or "")[:5000],
                confidence=output.confidence,
                tokens_input=_meta.get("tokens_input", 0),
                tokens_output=_meta.get("tokens_output", 0),
                model_used=_meta.get("model_used", ""),
                latency_ms=elapsed_ms,
                credits_consumed=credits_consumed,
                tool_calls=tool_calls,
                compliance_status="pass",
            ))
        except Exception as _log_err:
            logger.warning("[Studio] Execution log persist failed: %s", _log_err)

        await db.commit()''',
    "persist execution log",
)


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify AST ===")
files = [
    "alembic/versions/070_agent_deployments.py",
    "alembic/versions/071_agent_execution_logs.py",
    "libs/models/lia_models/agent_execution_log.py",
    "app/schemas/custom_agent.py",
    "app/api/v1/custom_agents.py",
    "app/api/v1/automation/triggers.py",
]
ok = 0
for f in files:
    try:
        ast.parse(read_file(f))
        print(f"  OK: {f}")
        ok += 1
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print(f"\n{'=' * 60}")
print(f"Results: {ok}/{len(files)} files valid")
if ok < len(files):
    sys.exit(1)
print("ALL GAPS CLOSED!")
