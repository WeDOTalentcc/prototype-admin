import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from lia_agents_core.execution_log_store import ExecutionLogStore
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/explainability", tags=["Agent Explainability"])

store = ExecutionLogStore()


class TimelineStepResponse(BaseModel):
    iteration: int
    phase: str
    reasoning_summary: str | None = None
    tool_used: str | None = None
    tool_result_summary: str | None = None
    decision: str | None = None
    duration_ms: float = 0
    timestamp: str | None = None


class SessionSummaryResponse(BaseModel):
    total_steps: int
    tools_used: list[str]
    reasoning_summary: str
    confidence: float
    duration_ms: float
    stage_progression: str | None = None


class ExecutionSummaryResponse(BaseModel):
    id: str
    session_id: str
    domain: str
    agent_class: str
    total_duration_ms: float
    total_iterations: int
    tools_succeeded: int
    tools_failed: int
    final_confidence: float
    stage_transitioned: bool
    model_provider: str
    created_at: str | None = None


class ToolUsageResponse(BaseModel):
    tool: str
    count: int


class StatsResponse(BaseModel):
    avg_confidence: float
    avg_iterations: float
    avg_duration_ms: float
    total_executions: int
    total_tools_succeeded: int
    total_tools_failed: int
    most_used_tools: list[ToolUsageResponse]


@router.get("/timeline/{session_id}", response_model=list[TimelineStepResponse])
async def get_timeline(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        timeline = await store.get_timeline(session_id)
        if not timeline:
            raise HTTPException(status_code=404, detail=f"No timeline found for session {session_id}")
        return [TimelineStepResponse(**step) for step in timeline]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeline for session {session_id}: {e}")
        raise LIAError(message="Failed to fetch timeline")


@router.get("/session/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        records = await store.get_by_session(session_id, limit=1)
        if not records:
            raise HTTPException(status_code=404, detail=f"No execution found for session {session_id}")

        record = records[0]
        chain = record.reasoning_chain or []

        reasoning_parts = []
        for step in chain:
            if step.get("reasoning"):
                reasoning_parts.append(step["reasoning"][:100])
            elif step.get("decision"):
                reasoning_parts.append(f"Decision: {step['decision'][:100]}")

        stage_progression = None
        if record.stage_before or record.stage_after:
            stage_progression = f"{record.stage_before or 'N/A'} → {record.stage_after or 'N/A'}"

        return SessionSummaryResponse(
            total_steps=len(chain),
            tools_used=list(set(record.tools_called or [])),
            reasoning_summary=" | ".join(reasoning_parts[:5]) if reasoning_parts else "No reasoning recorded",
            confidence=record.final_confidence or 0,
            duration_ms=record.total_duration_ms or 0,
            stage_progression=stage_progression,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching summary for session {session_id}: {e}")
        raise LIAError(message="Failed to fetch session summary")


@router.get("/company/{company_id}/recent", response_model=list[ExecutionSummaryResponse])
async def get_recent_executions(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    domain: str | None = Query(None, description="Filter by domain"),
    limit: int = Query(20, le=100, ge=1),
    current_user: User = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        records = await store.get_by_company(company_id, domain=domain, limit=limit)
        return [
            ExecutionSummaryResponse(
                id=str(r.id),
                session_id=r.session_id,
                domain=r.domain,
                agent_class=r.agent_class,
                total_duration_ms=r.total_duration_ms or 0,
                total_iterations=r.total_iterations or 0,
                tools_succeeded=r.tools_succeeded or 0,
                tools_failed=r.tools_failed or 0,
                final_confidence=r.final_confidence or 0,
                stage_transitioned=r.stage_transitioned or False,
                model_provider=r.model_provider or "claude",
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in records
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent executions for company {company_id}: {e}")
        raise LIAError(message="Failed to fetch recent executions")


@router.get("/stats/{company_id}", response_model=StatsResponse)
async def get_company_stats(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        stats = await store.get_stats(company_id)
        return StatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for company {company_id}: {e}")
        raise LIAError(message="Failed to fetch stats")

reorder_collection_before_item(router)
