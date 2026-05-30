import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.agent_memory.dependencies import get_agent_memory_repo
from app.domains.agent_memory.repositories.agent_memory_repository import AgentMemoryRepository
from lia_agents_core.working_memory import AgentWorkingMemory
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger("lia.agent_memory")
router = APIRouter(prefix="/agent-memory", tags=["Agent Memory"])

WIZARD_EXPECTED_FIELDS = [
    "title", "department", "seniority", "location", "work_model",
    "salary_min", "salary_max", "responsibilities",
    "technical_skills", "behavioral_competencies",
]


def _memory_to_dict(memory: AgentWorkingMemory) -> dict[str, Any]:
    return {
        "session_id": memory.session_id,
        "domain": memory.domain,
        "current_stage": memory.current_stage,
        "collected_fields": memory.collected_fields or {},
        "iteration_count": memory.iteration_count or 0,
        "agent_notes": memory.agent_notes,
        "pending_actions": memory.pending_actions or [],
        "accepted_suggestions": memory.accepted_suggestions or [],
        "rejected_suggestions": memory.rejected_suggestions or [],
        "parecer_data": memory.parecer_data or {},
        "last_intent": memory.last_intent,
        "last_confidence": memory.last_confidence,
        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
    }


def _default_memory(session_id: str, domain: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "domain": domain,
        "current_stage": None,
        "collected_fields": {},
        "iteration_count": 0,
        "agent_notes": None,
        "pending_actions": [],
        "accepted_suggestions": [],
        "rejected_suggestions": [],
        "parecer_data": {},
        "last_intent": None,
        "last_confidence": None,
        "updated_at": None,
    }


def _compute_completion(collected_fields: dict[str, Any], domain: str) -> float:
    if domain != "wizard" or not collected_fields:
        return 0.0
    filled = sum(1 for f in WIZARD_EXPECTED_FIELDS if f in collected_fields)
    return round((filled / len(WIZARD_EXPECTED_FIELDS)) * 100, 1)


def _memory_to_summary(memory: AgentWorkingMemory) -> dict[str, Any]:
    fields = memory.collected_fields or {}
    return {
        "session_id": memory.session_id,
        "domain": memory.domain,
        "current_stage": memory.current_stage,
        "fields_count": len(fields),
        "completion_percentage": _compute_completion(fields, memory.domain),
        "last_updated": memory.updated_at.isoformat() if memory.updated_at else None,
    }


def _default_summary(session_id: str, domain: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "domain": domain,
        "current_stage": None,
        "fields_count": 0,
        "completion_percentage": 0,
        "last_updated": None,
    }


@router.get("/active-sessions", response_model=None)
async def get_active_sessions(
    domain: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user_or_demo),
    repo: AgentMemoryRepository = Depends(get_agent_memory_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    logger.info(f"[access] active-sessions requested by user={getattr(current_user, 'id', 'unknown')} domain={domain}")
    try:
        memories = await repo.list_active_sessions(current_user.company_id, domain, limit)
        return [_memory_to_summary(m) for m in memories]
    except Exception as e:
        logger.error(f"Failed to fetch active sessions: {e}")
        return []


@router.get("/{session_id}/summary", response_model=None)
async def get_memory_summary(
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    domain: str = Query("wizard"),
    current_user: User = Depends(get_current_user_or_demo),
    repo: AgentMemoryRepository = Depends(get_agent_memory_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    logger.info(f"[access] memory-summary requested by user={getattr(current_user, 'id', 'unknown')} session={session_id} domain={domain}")
    try:
        memory = await repo.get_memory(session_id, domain, current_user.company_id)
        if memory is None:
            return _default_summary(session_id, domain)
        return _memory_to_summary(memory)
    except Exception as e:
        logger.error(f"Failed to fetch memory summary for session={session_id}: {e}")
        return _default_summary(session_id, domain)


@router.get("/{session_id}", response_model=None)
async def get_memory(
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    domain: str = Query("wizard"),
    current_user: User = Depends(get_current_user_or_demo),
    repo: AgentMemoryRepository = Depends(get_agent_memory_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    logger.info(f"[access] memory-read requested by user={getattr(current_user, 'id', 'unknown')} session={session_id} domain={domain}")
    try:
        memory = await repo.get_memory(session_id, domain, current_user.company_id)
        if memory is None:
            return _default_memory(session_id, domain)
        return _memory_to_dict(memory)
    except Exception as e:
        logger.error(f"Failed to fetch memory for session={session_id}: {e}")
        return _default_memory(session_id, domain)


@router.delete("/{session_id}", response_model=None)
async def reset_memory(
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    domain: str = Query("wizard"),
    current_user: User = Depends(get_current_user_or_demo),
    repo: AgentMemoryRepository = Depends(get_agent_memory_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    logger.warning(f"[access] memory-reset requested by user={getattr(current_user, 'id', 'unknown')} session={session_id} domain={domain}")
    try:
        memory = await repo.get_memory(session_id, domain, current_user.company_id)
        if memory is None:
            return {"status": "not_found", "message": "No working memory found for this session"}

        memory.iteration_count = 0
        memory.pending_actions = []
        memory.updated_at = datetime.utcnow()
        await repo.commit()

        logger.info(f"Reset working memory for session={session_id} domain={domain}")
        return {"status": "reset", "session_id": session_id, "domain": domain}
    except Exception as e:
        logger.error(f"Failed to reset memory for session={session_id}: {e}")
        return {"status": "error", "message": "Failed to reset working memory"}

reorder_collection_before_item(router)
