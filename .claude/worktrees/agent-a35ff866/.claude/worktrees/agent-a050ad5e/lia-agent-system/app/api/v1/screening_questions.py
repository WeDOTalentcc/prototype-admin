"""
Company Screening Questions API endpoints.
Manages company-level default screening questions that can be imported into job vacancies.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging
import uuid as uuid_lib

from app.core.database import get_db
from app.models.screening_question import (
    CompanyScreeningQuestion, 
    DEFAULT_SCREENING_QUESTIONS,
    QUESTION_CATEGORIES,
    QUESTION_TYPES
)
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id
)
from app.auth.models import User
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class ScreeningQuestionCreate(BaseModel):
    """Schema for creating a screening question."""
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = "text"  # text, single_choice, multiple_choice, yes_no, scale
    options: Optional[List[str]] = None
    is_required: bool = True
    is_eliminatory: bool = False
    expected_answer: Optional[str] = None
    category: Optional[str] = None
    order: Optional[int] = None


class ScreeningQuestionUpdate(BaseModel):
    """Schema for updating a screening question."""
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[List[str]] = None
    is_required: Optional[bool] = None
    is_eliminatory: Optional[bool] = None
    expected_answer: Optional[str] = None
    category: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class ScreeningQuestionResponse(BaseModel):
    """Response schema for a screening question."""
    id: str
    company_id: str
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    is_required: bool = True
    is_eliminatory: bool = False
    expected_answer: Optional[str] = None
    category: Optional[str] = None
    order: int = 0
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ScreeningQuestionsListResponse(BaseModel):
    """Response for list of screening questions."""
    items: List[ScreeningQuestionResponse]
    total_count: int


class ReorderRequest(BaseModel):
    """Request to reorder questions."""
    question_ids: List[str]  # Ordered list of question IDs


class CategoriesResponse(BaseModel):
    """Response for available categories."""
    categories: dict
    types: dict


@router.get("/company/screening-questions", response_model=ScreeningQuestionsListResponse)
async def list_company_screening_questions(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List all company default screening questions.
    Multi-tenant: Only returns questions from the user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        stmt = select(CompanyScreeningQuestion).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        
        if is_active is not None:
            stmt = stmt.where(CompanyScreeningQuestion.is_active == is_active)
        
        if category:
            stmt = stmt.where(CompanyScreeningQuestion.category == category)
        
        stmt = stmt.order_by(CompanyScreeningQuestion.order, CompanyScreeningQuestion.created_at)
        
        result = await db.execute(stmt)
        questions = result.scalars().all()
        
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
        
    except Exception as e:
        logger.error(f"Error listing screening questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions", response_model=ScreeningQuestionResponse)
async def create_screening_question(
    request: ScreeningQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new company default screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        max_order_stmt = select(func.max(CompanyScreeningQuestion.order)).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        max_order_result = await db.execute(max_order_stmt)
        max_order = max_order_result.scalar() or 0
        
        question = CompanyScreeningQuestion(
            id=uuid_lib.uuid4(),
            company_id=company_id,
            question_text=request.question_text,
            question_type=request.question_type,
            options=request.options,
            is_required=request.is_required,
            is_eliminatory=request.is_eliminatory,
            expected_answer=request.expected_answer,
            category=request.category,
            order=request.order if request.order is not None else max_order + 1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(question)
        await db.commit()
        await db.refresh(question)
        
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
        
    except Exception as e:
        logger.error(f"Error creating screening question: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/company/screening-questions/{question_id}", response_model=ScreeningQuestionResponse)
async def update_screening_question(
    question_id: str,
    request: ScreeningQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a company screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        stmt = select(CompanyScreeningQuestion).where(
            CompanyScreeningQuestion.id == UUID(question_id),
            CompanyScreeningQuestion.company_id == company_id
        )
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Screening question not found")
        
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(question)
        
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


@router.delete("/company/screening-questions/{question_id}")
async def delete_screening_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a company screening question.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        stmt = select(CompanyScreeningQuestion).where(
            CompanyScreeningQuestion.id == UUID(question_id),
            CompanyScreeningQuestion.company_id == company_id
        )
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Screening question not found")
        
        await db.delete(question)
        await db.commit()
        
        logger.info(f"Deleted screening question: {question_id}")
        
        return {"success": True, "message": "Screening question deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screening question: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions/reorder")
async def reorder_screening_questions(
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reorder company screening questions.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        for idx, q_id in enumerate(request.question_ids, start=1):
            stmt = update(CompanyScreeningQuestion).where(
                CompanyScreeningQuestion.id == UUID(q_id),
                CompanyScreeningQuestion.company_id == company_id
            ).values(order=idx, updated_at=datetime.utcnow())
            await db.execute(stmt)
        
        await db.commit()
        
        logger.info(f"Reordered {len(request.question_ids)} screening questions for company: {company_id}")
        
        return {"success": True, "message": "Questions reordered successfully"}
        
    except Exception as e:
        logger.error(f"Error reordering screening questions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company/screening-questions/seed")
async def seed_default_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Seed default screening questions for a company.
    Only creates if no questions exist.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        count_stmt = select(func.count(CompanyScreeningQuestion.id)).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        count_result = await db.execute(count_stmt)
        existing_count = count_result.scalar() or 0
        
        if existing_count > 0:
            return {
                "success": False,
                "message": f"Company already has {existing_count} screening questions. Seed skipped.",
                "created_count": 0
            }
        
        created_count = 0
        for q_data in DEFAULT_SCREENING_QUESTIONS:
            question = CompanyScreeningQuestion(
                id=uuid_lib.uuid4(),
                company_id=company_id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                options=q_data["options"],
                is_required=q_data["is_required"],
                is_eliminatory=q_data["is_eliminatory"],
                expected_answer=q_data["expected_answer"],
                category=q_data["category"],
                order=q_data["order"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(question)
            created_count += 1
        
        await db.commit()
        
        logger.info(f"Seeded {created_count} default screening questions for company: {company_id}")
        
        return {
            "success": True,
            "message": f"Created {created_count} default screening questions",
            "created_count": created_count
        }
        
    except Exception as e:
        logger.error(f"Error seeding screening questions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/screening-questions/categories", response_model=CategoriesResponse)
async def get_categories(
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get available question categories and types.
    """
    return CategoriesResponse(
        categories=QUESTION_CATEGORIES,
        types=QUESTION_TYPES
    )
