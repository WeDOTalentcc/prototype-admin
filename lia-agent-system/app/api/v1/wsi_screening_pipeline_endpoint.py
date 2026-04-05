"""
WSI Screening Pipeline API - Unified endpoint for complete WSI screening question generation.

Orchestrates all WSI blocks:
- Block 1.5: Company default screening questions
- Block 2: WSI Eligibility (deduplicated)
- Block 3: Technical Assessment (Bloom/Dreyfus)
- Block 4: Behavioral/Situational (Big Five/CBI)
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.screening import (
    WSIScreeningPipelineRequest,
    WSIScreeningPipelineResponse,
)
from app.services.wsi_screening_pipeline import wsi_screening_pipeline
from app.auth.dependencies import (
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
)
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wsi", tags=["WSI Screening Pipeline"])


@router.post("/screening-pipeline", response_model=WSIScreeningPipelineResponse)
async def generate_screening_pipeline(
    request: WSIScreeningPipelineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Generate unified WSI screening questions across all blocks.
    
    Fetches company questions from database and generates WSI questions
    using scientific frameworks (Big Five, Bloom, Dreyfus, CBI).
    """
    try:
        company_id = get_user_company_id(current_user)
        request.company_id = company_id

        company_questions_raw = []
        if request.include_company_questions:
            try:
                from app.models.screening_question import CompanyScreeningQuestion

                stmt = select(CompanyScreeningQuestion).where(
                    CompanyScreeningQuestion.company_id == company_id,
                    CompanyScreeningQuestion.is_active == True,
                ).order_by(CompanyScreeningQuestion.order)

                result = await db.execute(stmt)
                rows = result.scalars().all()

                for row in rows:
                    company_questions_raw.append({
                        "id": str(row.id),
                        "question_text": row.question_text,
                        "question_type": row.question_type or "text",
                        "options": row.options,
                        "is_required": row.is_required,
                        "is_eliminatory": row.is_eliminatory,
                        "expected_answer": row.expected_answer,
                        "category": row.category,
                        "order": row.order or 0,
                        "is_active": row.is_active,
                    })

                logger.info(
                    f"Fetched {len(company_questions_raw)} company questions for company {company_id}"
                )
            except Exception as e:
                logger.warning(f"Could not fetch company questions: {e}")
                company_questions_raw = []

        response = await wsi_screening_pipeline.build_pipeline(
            request=request,
            company_questions_raw=company_questions_raw,
        )

        logger.info(
            f"WSI Pipeline generated {response.total_count} questions "
            f"for '{request.job_title}' ({request.seniority}) - "
            f"company: {company_id}, user: {current_user.email}, "
            f"distribution: {response.block_distribution}, "
            f"is_affirmative: {request.is_affirmative}, "
            f"affirmative_type: {request.affirmative_type}"
        )

        return response

    except Exception as e:
        logger.error(f"Error in WSI screening pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
