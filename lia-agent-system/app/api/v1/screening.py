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


def _wsi_questions_to_screening_response(wsi_questions, request) -> ScreeningQuestionResponse:
    """Convert WSIQuestion list from canonical generator to ScreeningQuestionResponse."""
    from app.domains.cv_screening.constants.wsi_constants import (
        BLOOM_LEVEL_LABELS,
        DREYFUS_STAGE_LABELS,
        SENIORITY_TO_DREYFUS,
        SENIORITY_TO_BLOOM,
    )
    all_questions = []
    behavioral_questions = []
    technical_questions = []
    cultural_questions = []

    for idx, wq in enumerate(wsi_questions):
        is_behavioral = wq.framework == "BigFive" or wq.question_type == "situational"
        category = "behavioral" if is_behavioral else "technical"
        bloom_level = wq.scoring_criteria.get("bloom_level", 3) if isinstance(wq.scoring_criteria, dict) else 3
        if not isinstance(bloom_level, int):
            try:
                bloom_level = int(bloom_level)
            except (ValueError, TypeError):
                bloom_level = 3
        dreyfus_stage = SENIORITY_TO_DREYFUS.get(request.seniority or "pleno", 3)
        bloom_info = BLOOM_LEVEL_LABELS.get(bloom_level, BLOOM_LEVEL_LABELS.get(3, {}))
        dreyfus_info = DREYFUS_STAGE_LABELS.get(dreyfus_stage, DREYFUS_STAGE_LABELS.get(3, {}))

        sq = ScreeningQuestion(
            id=wq.id,
            text=wq.question_text,
            category=category,
            trait=wq.scoring_criteria.get("ocean_trait") if isinstance(wq.scoring_criteria, dict) else None,
            skill=wq.competency if category == "technical" else None,
            bloom_level=bloom_level,
            bloom_label=bloom_info.get("name_pt", "Aplicar") if isinstance(bloom_info, dict) else "Aplicar",
            dreyfus_stage=dreyfus_stage,
            dreyfus_label=dreyfus_info.get("name_pt", "Competente") if isinstance(dreyfus_info, dict) else "Competente",
            framework=wq.framework,
            weight=wq.weight,
            expected_signals=wq.expected_signals,
            scoring_criteria=wq.scoring_criteria if isinstance(wq.scoring_criteria, dict) else {},
            is_selected=True,
            question_type="open",
            order=idx,
        )
        all_questions.append(sq)
        if category == "behavioral":
            behavioral_questions.append(sq)
        else:
            technical_questions.append(sq)

    seniority = request.seniority or "pleno"
    return ScreeningQuestionResponse(
        questions=all_questions,
        behavioral_questions=behavioral_questions,
        technical_questions=technical_questions,
        cultural_questions=cultural_questions,
        total_count=len(all_questions),
        metadata={
            "seniority": seniority,
            "dreyfus_stage": SENIORITY_TO_DREYFUS.get(seniority, 3),
            "bloom_levels": SENIORITY_TO_BLOOM.get(seniority, [3, 4]),
            "skills_count": len(request.skills) if request.skills else 0,
            "title": request.title,
            "department": request.department,
            "generator": "wsi_service_canonical_f6",
        }
    )


@router.post("/questions", response_model=ScreeningQuestionResponse)
async def generate_screening_questions(
    request: ScreeningQuestionRequest,
    current_user: User = Depends(get_current_active_user)
) -> ScreeningQuestionResponse:
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Generating screening questions for: {request.title} ({request.seniority}) - company: {company_id}, user: {current_user.email}")

        from app.services.wsi_service import WSIService
        wsi_svc = WSIService()
        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=request.skills or [],
            behavioral=[],
            seniority=request.seniority or "pleno",
            job_description=request.job_description,
            mode="compact",
        )

        response = _wsi_questions_to_screening_response(wsi_questions, request)

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
        logger.info(f"Regenerating questions for: {request.context.title} - company: {company_id}, user: {current_user.email}")

        from app.services.wsi_service import WSIService
        wsi_svc = WSIService()
        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=request.context.skills or [],
            behavioral=[],
            seniority=request.context.seniority or "pleno",
            job_description=request.context.job_description,
            mode="compact",
        )

        response = _wsi_questions_to_screening_response(wsi_questions, request.context)

        if request.category:
            filtered = [q for q in response.questions if q.category == request.category]
            if request.exclude_ids:
                filtered = [q for q in filtered if q.id not in request.exclude_ids]
            logger.info(f"Regenerated {len(filtered)} {request.category} questions")
            return filtered

        logger.info(f"Regenerated all {len(response.questions)} questions")
        return response.questions

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
