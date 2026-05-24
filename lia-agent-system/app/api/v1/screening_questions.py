"""
Company Screening Questions API endpoints.
Manages company-level default screening questions that can be imported into job vacancies.
"""
import logging
import uuid as uuid_lib
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
)
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.recruitment.repositories.company_screening_question_repository import CompanyScreeningQuestionRepository
from app.models.screening_question import (
    DEFAULT_SCREENING_QUESTIONS,
    QUESTION_CATEGORIES,
    QUESTION_TYPES,
    CompanyScreeningQuestion,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


def get_screening_question_repo(db: AsyncSession = Depends(get_db)) -> CompanyScreeningQuestionRepository:
    return CompanyScreeningQuestionRepository(db)


class ScreeningQuestionCreate(WeDoBaseModel):
    """Schema for creating a screening question."""
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = "text"  # text, single_choice, multiple_choice, yes_no, scale
    options: list[str] | None = None
    is_required: bool = True
    is_eliminatory: bool = False
    expected_answer: str | None = None
    category: str | None = None
    order: int | None = None


class ScreeningQuestionUpdate(WeDoBaseModel):
    """Schema for updating a screening question."""
    question_text: str | None = None
    question_type: str | None = None
    options: list[str] | None = None
    is_required: bool | None = None
    is_eliminatory: bool | None = None
    expected_answer: str | None = None
    category: str | None = None
    order: int | None = None
    is_active: bool | None = None


class ScreeningQuestionResponse(BaseModel):
    """Response schema for a screening question."""
    id: str
    company_id: str
    question_text: str
    question_type: str
    options: list[str] | None = None
    is_required: bool = True
    is_eliminatory: bool = False
    expected_answer: str | None = None
    category: str | None = None
    order: int = 0
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class ScreeningQuestionsListResponse(BaseModel):
    """Response for list of screening questions."""
    items: list[ScreeningQuestionResponse]
    total_count: int


class ReorderRequest(WeDoBaseModel):
    """Request to reorder questions."""
    question_ids: list[str]  # Ordered list of question IDs


class CategoriesResponse(BaseModel):
    """Response for available categories."""
    categories: dict
    types: dict


@router.get("/company/screening-questions", response_model=ScreeningQuestionsListResponse)
async def list_company_screening_questions(
    category: str | None = None,
    is_active: bool | None = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    List all company default screening questions.
    Multi-tenant: Only returns questions from the user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        questions = await repo.list_for_company(company_id, category=category, is_active=is_active)
        
        items = [
            ScreeningQuestionResponse(
                id=str(q.id),
                company_id=q.company_id,
                question_text=q.question_text,
                question_type=q.question_type or "text",
                options=q.options,
                is_required=q.is_required,
                is_eliminatory=q.is_eliminatory,
                expected_answer=q.expected_answer,
                category=q.category,
                order=q.order or 0,
                is_active=q.is_active,
                created_at=q.created_at.isoformat() if q.created_at else None,
                updated_at=q.updated_at.isoformat() if q.updated_at else None
            )
            for q in questions
        ]
        
        return ScreeningQuestionsListResponse(
            items=items,
            total_count=len(items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions", response_model=ScreeningQuestionResponse)
async def create_screening_question(
    request: ScreeningQuestionCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Create a new company default screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        max_order = await repo.get_max_order(company_id)
        
        question = await repo.create(company_id, {
            "question_text": request.question_text,
            "question_type": request.question_type,
            "options": request.options,
            "is_required": request.is_required,
            "is_eliminatory": request.is_eliminatory,
            "expected_answer": request.expected_answer,
            "category": request.category,
            "order": request.order if request.order is not None else max_order + 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        
        logger.info(f"Created screening question: {question.id} for company: {company_id}")
        
        return ScreeningQuestionResponse(
            id=str(question.id),
            company_id=question.company_id,
            question_text=question.question_text,
            question_type=question.question_type or "text",
            options=question.options,
            is_required=question.is_required,
            is_eliminatory=question.is_eliminatory,
            expected_answer=question.expected_answer,
            category=question.category,
            order=question.order or 0,
            is_active=question.is_active,
            created_at=question.created_at.isoformat() if question.created_at else None,
            updated_at=question.updated_at.isoformat() if question.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating screening question: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/company/screening-questions/{question_id}", response_model=ScreeningQuestionResponse)
async def update_screening_question(
    question_id: str,
    request: ScreeningQuestionUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Update a company screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        question = await repo.get_by_id(UUID(question_id), company_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Screening question not found")
        
        update_data = request.model_dump(exclude_unset=True)
        question = await repo.update(question, update_data)
        
        logger.info(f"Updated screening question: {question.id}")
        
        return ScreeningQuestionResponse(
            id=str(question.id),
            company_id=question.company_id,
            question_text=question.question_text,
            question_type=question.question_type or "text",
            options=question.options,
            is_required=question.is_required,
            is_eliminatory=question.is_eliminatory,
            expected_answer=question.expected_answer,
            category=question.category,
            order=question.order or 0,
            is_active=question.is_active,
            created_at=question.created_at.isoformat() if question.created_at else None,
            updated_at=question.updated_at.isoformat() if question.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening question: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/company/screening-questions/{question_id}", response_model=None)
async def delete_screening_question(
    question_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Delete a company screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        question = await repo.get_by_id(UUID(question_id), company_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Screening question not found")
        
        await repo.delete(question)
        
        logger.info(f"Deleted screening question: {question_id}")
        
        return {"success": True, "message": "Screening question deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screening question: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions/reorder", response_model=None)
async def reorder_screening_questions(
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Reorder company screening questions.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        await repo.reorder(company_id, request.question_ids)
        
        
        logger.info(f"Reordered {len(request.question_ids)} screening questions for company: {company_id}")
        
        return {"success": True, "message": "Questions reordered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering screening questions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions/seed", response_model=None)
async def seed_default_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Seed default screening questions for a company.
    Only creates if no questions exist.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = CompanyScreeningQuestionRepository(db)
        existing_count = await repo.count_for_company(company_id)
        
        if existing_count > 0:
            return {
                "success": False,
                "message": f"Company already has {existing_count} screening questions. Seed skipped.",
                "created_count": 0
            }
        
        questions_to_create = [
            {
                "question_text": q_data["question_text"],
                "question_type": q_data["question_type"],
                "options": q_data["options"],
                "is_required": q_data["is_required"],
                "is_eliminatory": q_data["is_eliminatory"],
                "expected_answer": q_data["expected_answer"],
                "category": q_data["category"],
                "order": q_data["order"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for q_data in DEFAULT_SCREENING_QUESTIONS
        ]
        created = await repo.bulk_create(company_id, questions_to_create)
        created_count = len(created)
        
        
        logger.info(f"Seeded {created_count} default screening questions for company: {company_id}")
        
        return {
            "success": True,
            "message": f"Created {created_count} default screening questions",
            "created_count": created_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error seeding screening questions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/screening-questions/categories", response_model=CategoriesResponse)
async def get_categories(
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get available question categories and types.
    """
    return CategoriesResponse(
        categories=QUESTION_CATEGORIES,
        types=QUESTION_TYPES
    )
