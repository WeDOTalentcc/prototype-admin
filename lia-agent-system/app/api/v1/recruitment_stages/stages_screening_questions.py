"""
Screening questions CRUD endpoints.

Mounted at /api/v1 (not /api/v1/recruitment-stages) — the router prefix
is /screening-questions so the full path becomes /api/v1/screening-questions/...
This matches the original `screening_questions_router` that routes.py registered
with prefix="/api/v1".
"""
from app.middleware.request_id import get_correlation_id
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException

from ._shared import (
    ScreeningQuestion,
    get_current_active_user,
    get_user_company_id,
    require_admin_or_recruiter,
    get_screening_question_repo,
    ScreeningQuestionRepository,
    User,
)
from pydantic import BaseModel, Field
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.compliance.audit_service import AuditService  # P1-W1-08
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default questions data
# ---------------------------------------------------------------------------

# TODO P2-W1-03: DEFAULT_SCREENING_QUESTIONS é single source of truth no backend.
# Frontend NÃO tem cópia local — consome via GET /api/v1/company/screening-questions?default=true
# (endpoint existe em screening_questions.py). Validar periodicamente que listas estão sincronizadas.
DEFAULT_SCREENING_QUESTIONS = [
    {"id": "1", "question": "Você tem interesse real nesta vaga?", "question_type": "yes_no", "is_required": True, "order": 1, "is_default": True, "options": []},
    {"id": "2", "question": "Qual sua disponibilidade para início?", "question_type": "text", "is_required": True, "order": 2, "is_default": True, "options": []},
    {"id": "3", "question": "Qual sua pretensão salarial?", "question_type": "text", "is_required": True, "order": 3, "is_default": True, "options": []},
    {"id": "4", "question": "Quantos anos de experiência você tem na área?", "question_type": "text", "is_required": True, "order": 4, "is_default": True, "options": []},
    {"id": "5", "question": "Você aceita trabalhar no modelo híbrido/presencial?", "question_type": "yes_no", "is_required": True, "order": 5, "is_default": True, "options": []},
    {"id": "6", "question": "Você está em algum outro processo seletivo?", "question_type": "yes_no", "is_required": False, "order": 6, "is_default": True, "options": []}
]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ScreeningQuestionCreate(WeDoBaseModel):
    question: str = Field(..., min_length=1)
    question_type: str = Field(default="text")
    is_required: bool = True
    order: int = Field(default=0, ge=0)
    is_default: bool = False
    options: list[str] = Field(default_factory=list)


class ScreeningQuestionUpdate(WeDoBaseModel):
    id: str | None = None
    question: str | None = None
    question_type: str | None = None
    is_required: bool | None = None
    order: int | None = None
    is_default: bool | None = None
    options: list[str] | None = None


# ---------------------------------------------------------------------------
# Router (prefix set in __init__.py to match original routes.py registration)
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/screening-questions", tags=["screening-questions"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def initialize_default_questions(
    company_id: str,
    sq_repo: ScreeningQuestionRepository,
) -> list[ScreeningQuestion]:
    """Initialize default screening questions for a company if none exist."""
    existing = await sq_repo.list_all_for_company(company_id)

    if not existing:
        for q in DEFAULT_SCREENING_QUESTIONS:
            await sq_repo.create_no_commit({
                "company_id": company_id,
                "question": q["question"],
                "question_type": q["question_type"],
                "is_required": q["is_required"],
                "order": q["order"],
                "is_default": q["is_default"],
                "options": q.get("options", []),
            })
        await sq_repo.commit()
        return await sq_repo.list_for_company(company_id)

    return existing


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def list_screening_questions(
    current_user: User = Depends(get_current_active_user),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
company_id: str = Depends(require_company_id)):
    """
    List all screening questions for the authenticated user's company.
    Initializes default questions if none exist.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        await initialize_default_questions(effective_company_id, sq_repo)
        questions = await sq_repo.list_for_company(effective_company_id)

        return [q.to_dict() for q in questions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
async def create_screening_question(
    question: ScreeningQuestionCreate,
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
company_id: str = Depends(require_company_id)):
    """
    Create a new screening question for the authenticated user's company.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        next_order = await sq_repo.get_last_order(effective_company_id)

        new_question = await sq_repo.create({
            "company_id": effective_company_id,
            "question": question.question,
            "question_type": question.question_type,
            "is_required": question.is_required,
            "order": question.order if question.order > 0 else next_order,
            "is_default": False,
            "options": question.options,
        })

        logger.info(f"Created screening question: {question.question[:50]} for company {effective_company_id}")
        try:
            import uuid as _uuid
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=effective_company_id, action_type="screening_question_created", actor=str(getattr(current_user, "id", "system")), target_id=str(new_question.id), target_type="screening_question", metadata={"question_type": question.question_type})  # P1-W1-08
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {
            "success": True,
            "message": "Screening question created",
            "data": new_question.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("")
async def update_screening_questions(
    questions: list[dict] = Body(...),
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
company_id: str = Depends(require_company_id)):
    """
    Update screening questions (bulk update).
    Syncs the database with the provided list of questions.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        existing_list = await sq_repo.list_all_for_company(effective_company_id)
        existing_questions = {str(q.id): q for q in existing_list}

        incoming_ids = set()
        updated_questions = []

        for idx, q_data in enumerate(questions):
            q_id = q_data.get("id", "")

            if q_id in existing_questions:
                existing = existing_questions[q_id]
                existing.question = q_data.get("question", existing.question)
                existing.question_type = q_data.get("question_type", existing.question_type)
                existing.is_required = q_data.get("is_required", existing.is_required)
                existing.order = q_data.get("order", idx + 1)
                existing.options = q_data.get("options", existing.options)
                existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
                incoming_ids.add(q_id)
                updated_questions.append(existing)
            elif q_id.startswith("q-") or not q_id:
                new_question = await sq_repo.create_no_commit({
                    "company_id": effective_company_id,
                    "question": q_data.get("question", ""),
                    "question_type": q_data.get("question_type", "text"),
                    "is_required": q_data.get("is_required", True),
                    "order": q_data.get("order", idx + 1),
                    "is_default": q_data.get("is_default", False),
                    "options": q_data.get("options", []),
                })
                updated_questions.append(new_question)
            else:
                try:
                    existing_uuid = existing_questions.get(q_id)
                    if existing_uuid:
                        existing_uuid.question = q_data.get("question", existing_uuid.question)
                        existing_uuid.question_type = q_data.get("question_type", existing_uuid.question_type)
                        existing_uuid.is_required = q_data.get("is_required", existing_uuid.is_required)
                        existing_uuid.order = q_data.get("order", idx + 1)
                        existing_uuid.options = q_data.get("options", existing_uuid.options)
                        existing_uuid.updated_at = datetime.utcnow()  # type: ignore[assignment]
                        incoming_ids.add(q_id)
                        updated_questions.append(existing_uuid)
                except Exception:
                    pass

        for q_id, existing in existing_questions.items():
            if q_id not in incoming_ids:
                await sq_repo.soft_delete_no_commit(existing)

        await sq_repo.commit()

        for q in updated_questions:
            await sq_repo.refresh(q)

        logger.info(f"Updated {len(questions)} screening questions for company {effective_company_id}")
        try:
            import uuid as _uuid
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=effective_company_id, action_type="screening_question_bulk_updated", actor=str(getattr(current_user, "id", "system")), target_type="screening_question", metadata={"count": len(questions)})  # P1-W1-08
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {
            "success": True,
            "message": "Screening questions updated",
            "data": [q.to_dict() for q in updated_questions if q.is_active]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{question_id}")
async def update_screening_question(
    question_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    question: ScreeningQuestionUpdate,
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
company_id: str = Depends(require_company_id)):
    """
    Update a single screening question.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        try:
            q_uuid = uuid.UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        existing = await sq_repo.get_by_id(q_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Question not found")

        if existing.company_id != effective_company_id:  # type: ignore[truthy-bool]
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = question.model_dump(exclude_unset=True)
        updated = await sq_repo.update(q_uuid, update_data)

        try:
            import uuid as _uuid
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=effective_company_id, action_type="screening_question_updated", actor=str(getattr(current_user, "id", "system")), target_id=question_id, target_type="screening_question")  # P1-W1-08
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {
            "success": True,
            "message": "Screening question updated",
            "data": updated.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{question_id}")
async def delete_screening_question(
    question_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(require_admin_or_recruiter),
    sq_repo: ScreeningQuestionRepository = Depends(get_screening_question_repo),
company_id: str = Depends(require_company_id)):
    """
    Delete a screening question (soft delete).
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        try:
            q_uuid = uuid.UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        existing = await sq_repo.get_by_id(q_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Question not found")

        if existing.company_id != effective_company_id:  # type: ignore[truthy-bool]
            raise HTTPException(status_code=403, detail="Access denied")

        await sq_repo.soft_delete(q_uuid)

        logger.info(f"Deleted screening question: {question_id}")
        try:
            import uuid as _uuid
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=effective_company_id, action_type="screening_question_deleted", actor=str(getattr(current_user, "id", "system")), target_id=question_id, target_type="screening_question")  # P1-W1-08
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {
            "success": True,
            "message": "Screening question deleted",
            "deleted_id": question_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screening question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
