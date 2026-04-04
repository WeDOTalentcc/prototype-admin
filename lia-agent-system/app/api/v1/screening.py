from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid as uuid_mod

from app.schemas.screening import (
    ScreeningQuestionRequest,
    ScreeningQuestionResponse,
    ScreeningQuestion,
    RegenerateQuestionsRequest
)
from app.services.wsi_question_generator import wsi_screening_generator
from app.auth.dependencies import get_current_active_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.models.screening import ScreeningTask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screening", tags=["screening"])


class AutoScreeningRequest(BaseModel):
    candidate_id: str
    job_id: str
    source: str
    resume_text: Optional[str] = None
    resume_url: Optional[str] = None
    company_id: str


@router.post("/questions", response_model=ScreeningQuestionResponse)
async def generate_screening_questions(
    request: ScreeningQuestionRequest,
    current_user: User = Depends(get_current_active_user)
) -> ScreeningQuestionResponse:
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Generating screening questions for: {request.title} ({request.seniority}) - company: {company_id}, user: {current_user.email}")
        
        response = wsi_screening_generator.generate_questions(request)
        
        logger.info(f"Generated {response.total_count} questions: "
                   f"{len(response.behavioral_questions)} behavioral, "
                   f"{len(response.technical_questions)} technical, "
                   f"{len(response.cultural_questions)} cultural")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating screening questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate screening questions: {str(e)}"
        )


@router.post("/questions/regenerate", response_model=List[ScreeningQuestion])
async def regenerate_questions(
    request: RegenerateQuestionsRequest,
    current_user: User = Depends(get_current_active_user)
) -> List[ScreeningQuestion]:
    try:
        company_id = get_user_company_id(current_user)
        category = request.category
        if not category:
            full_response = wsi_screening_generator.generate_questions(request.context)
            logger.info(f"Regenerated all questions for: {request.context.title} - company: {company_id}, user: {current_user.email}")
            return full_response.questions
        
        logger.info(f"Regenerating {category} questions for: {request.context.title} - company: {company_id}, user: {current_user.email}")
        
        questions = wsi_screening_generator.regenerate_category(
            context=request.context,
            category=category,
            exclude_ids=request.exclude_ids
        )
        
        logger.info(f"Regenerated {len(questions)} {category} questions")
        
        return questions
        
    except Exception as e:
        logger.error(f"Error regenerating questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate questions: {str(e)}"
        )


@router.get("/frameworks")
async def get_screening_frameworks(
    current_user: User = Depends(get_current_active_user)
):
    from app.domains.cv_screening.constants.wsi_constants import (
        BLOOM_LEVEL_LABELS,
        DREYFUS_STAGE_LABELS,
        SENIORITY_TO_DREYFUS,
        SENIORITY_TO_BLOOM,
    )
    from app.api.v1.wsi._shared import BLOOM_LEVELS as BLOOM_RICH, DREYFUS_LEVELS as DREYFUS_RICH

    return {
        "bloom_levels": {
            k: {"label": BLOOM_LEVEL_LABELS[k], "description": BLOOM_RICH[k]["description"]}
            for k in BLOOM_LEVEL_LABELS
        },
        "dreyfus_stages": {
            k: {"label": DREYFUS_STAGE_LABELS[k], "description": DREYFUS_RICH[k]["description"]}
            for k in DREYFUS_STAGE_LABELS
        },
        "big_five_traits": {
            "openness": {"label": "Abertura", "description": "Criatividade, curiosidade, inovação"},
            "conscientiousness": {"label": "Conscienciosidade", "description": "Organização, responsabilidade, disciplina"},
            "extraversion": {"label": "Extroversão", "description": "Sociabilidade, energia, assertividade"},
            "agreeableness": {"label": "Amabilidade", "description": "Cooperação, empatia, harmonia"},
            "stability": {"label": "Estabilidade", "description": "Calma, resiliência, equilíbrio emocional"}
        },
        "seniority_mapping": {
            k: {"dreyfus": SENIORITY_TO_DREYFUS[k], "bloom_range": SENIORITY_TO_BLOOM[k]}
            for k in SENIORITY_TO_DREYFUS
        }
    }


@router.post("/auto-trigger", status_code=202)
async def auto_trigger_screening(
    request: AutoScreeningRequest,
    db: AsyncSession = Depends(get_db),
):
    if request.source != "website":
        raise HTTPException(
            status_code=400,
            detail="Auto-screening only processes applications with source 'website'"
        )

    try:
        task = ScreeningTask(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            company_id=request.company_id,
            status="pending",
            source=request.source,
            resume_text=request.resume_text,
            resume_url=request.resume_url,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(
            f"Auto-screening task created: {task.id} for candidate={request.candidate_id} "
            f"job={request.job_id} company={request.company_id}"
        )

        return JSONResponse(
            status_code=202,
            content={"task_id": str(task.id), "status": "pending"},
        )
    except Exception as e:
        logger.error(f"Failed to create auto-screening task: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create screening task")


@router.get("/tasks/{job_id}")
async def list_screening_tasks(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(ScreeningTask)
            .where(ScreeningTask.job_id == job_id)
            .order_by(ScreeningTask.created_at.desc())
        )
        tasks = result.scalars().all()

        return {"job_id": job_id, "tasks": [t.to_dict() for t in tasks], "total": len(tasks)}
    except Exception as e:
        logger.error(f"Failed to list screening tasks for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list screening tasks")


@router.post("/tasks/{task_id}/execute")
async def execute_screening_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        task_uuid = uuid_mod.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task_id format")

    try:
        result = await db.execute(
            select(ScreeningTask).where(ScreeningTask.id == task_uuid)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Screening task not found")

        if task.status not in ("pending", "failed"):
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot be executed in current status: {task.status}"
            )

        task.status = "processing"
        await db.commit()
        await db.refresh(task)

        logger.info(f"Screening task {task_id} status updated to processing")

        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute screening task {task_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to execute screening task")
