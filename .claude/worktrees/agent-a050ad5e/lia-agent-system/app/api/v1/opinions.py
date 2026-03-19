"""
API endpoints for LIA Opinions (Pareceres).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update, func
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.models.lia_opinion import LiaOpinion
from app.models.job_vacancy import JobVacancy
from app.schemas.lia_opinion import (
    LiaOpinionCreate,
    LiaOpinionUpdate,
    LiaOpinionCompact,
    LiaOpinionFull,
    CandidateOpinionsSummary,
    LiaOpinionListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opinions", tags=["LIA Opinions"])


@router.get("/candidate/{candidate_id}/summary", response_model=CandidateOpinionsSummary)
async def get_candidate_opinions_summary(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get summary of all opinions for a candidate (for preview display)."""
    company_id = current_user.company_id or "default"
    query = select(LiaOpinion).where(
        and_(
            LiaOpinion.candidate_id == candidate_id,
            LiaOpinion.company_id == company_id,
            LiaOpinion.is_current == True
        )
    ).order_by(desc(LiaOpinion.created_at))
    
    result = await db.execute(query)
    opinions = result.scalars().all()
    
    current_general = None
    vacancy_opinions = []
    has_pending = False
    
    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_query = select(JobVacancy.title).where(JobVacancy.id == op.job_vacancy_id)
            job_result = await db.execute(job_query)
            job_title = job_result.scalar_one_or_none()
        
        compact = LiaOpinionCompact(
            id=op.id,
            opinion_type=op.opinion_type,
            source=op.source,
            score=op.score,
            wsi_score=op.wsi_score,
            recommendation=op.recommendation,
            summary=op.summary,
            archetype=op.archetype,
            job_vacancy_id=op.job_vacancy_id,
            job_vacancy_title=job_title,
            created_at=op.created_at,
            is_current=op.is_current
        )
        
        if op.opinion_type == "general" and current_general is None:
            current_general = compact
        elif op.job_vacancy_id:
            vacancy_opinions.append(compact)
        
        if op.recommendation == "pending_review":
            has_pending = True
    
    return CandidateOpinionsSummary(
        candidate_id=candidate_id,
        total_opinions=len(opinions),
        current_general_opinion=current_general,
        vacancy_opinions=vacancy_opinions,
        has_pending_review=has_pending
    )


@router.get("/candidate/{candidate_id}/history", response_model=List[LiaOpinionFull])
async def get_candidate_opinions_history(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get full history of all opinions for a candidate (including non-current versions)."""
    company_id = current_user.company_id or "default"
    query = select(LiaOpinion).where(
        and_(
            LiaOpinion.candidate_id == candidate_id,
            LiaOpinion.company_id == company_id
        )
    ).order_by(desc(LiaOpinion.created_at))
    
    result = await db.execute(query)
    opinions = result.scalars().all()
    
    items = []
    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_query = select(JobVacancy.title).where(JobVacancy.id == op.job_vacancy_id)
            job_result = await db.execute(job_query)
            job_title = job_result.scalar_one_or_none()
        
        items.append(LiaOpinionFull(
            id=op.id,
            candidate_id=op.candidate_id,
            opinion_type=op.opinion_type,
            source=op.source,
            job_vacancy_id=op.job_vacancy_id,
            job_vacancy_title=job_title,
            wsi_screening_id=op.wsi_screening_id,
            score=op.score,
            wsi_score=op.wsi_score,
            recommendation=op.recommendation,
            summary=op.summary,
            archetype=op.archetype,
            archetype_match_score=op.archetype_match_score,
            score_breakdown=op.score_breakdown or {},
            technical_analysis=op.technical_analysis or {},
            behavioral_analysis=op.behavioral_analysis or {},
            cultural_fit=op.cultural_fit or {},
            strengths=op.strengths or [],
            concerns=op.concerns or [],
            gaps=op.gaps or [],
            matched_skills=op.matched_skills or [],
            missing_skills=op.missing_skills or [],
            next_steps=op.next_steps,
            recruiter_notes=op.recruiter_notes,
            recruiter_override=op.recruiter_override,
            recruiter_override_reason=op.recruiter_override_reason,
            recruiter_override_by=op.recruiter_override_by,
            recruiter_override_at=op.recruiter_override_at,
            is_current=op.is_current,
            version=op.version,
            created_at=op.created_at,
            updated_at=op.updated_at,
            created_by=op.created_by
        ))
    
    return items


@router.get("/candidate/{candidate_id}", response_model=LiaOpinionListResponse)
async def list_candidate_opinions(
    candidate_id: UUID,
    opinion_type: Optional[str] = Query(None, description="Filter by type: general or wsi"),
    job_vacancy_id: Optional[UUID] = Query(None, description="Filter by vacancy"),
    include_history: bool = Query(False, description="Include non-current versions"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """List all opinions for a candidate with optional filters."""
    company_id = current_user.company_id or "default"
    conditions = [
        LiaOpinion.candidate_id == candidate_id,
        LiaOpinion.company_id == company_id
    ]
    
    if not include_history:
        conditions.append(LiaOpinion.is_current == True)
    
    if opinion_type:
        conditions.append(LiaOpinion.opinion_type == opinion_type)
    
    if job_vacancy_id:
        conditions.append(LiaOpinion.job_vacancy_id == job_vacancy_id)
    
    count_query = select(LiaOpinion).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    query = select(LiaOpinion).where(and_(*conditions)).order_by(
        desc(LiaOpinion.created_at)
    ).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    opinions = result.scalars().all()
    
    items = []
    for op in opinions:
        job_title = None
        if op.job_vacancy_id:
            job_query = select(JobVacancy.title).where(JobVacancy.id == op.job_vacancy_id)
            job_result = await db.execute(job_query)
            job_title = job_result.scalar_one_or_none()
        
        items.append(LiaOpinionFull(
            id=op.id,
            candidate_id=op.candidate_id,
            opinion_type=op.opinion_type,
            source=op.source,
            job_vacancy_id=op.job_vacancy_id,
            job_vacancy_title=job_title,
            wsi_screening_id=op.wsi_screening_id,
            score=op.score,
            wsi_score=op.wsi_score,
            recommendation=op.recommendation,
            summary=op.summary,
            archetype=op.archetype,
            archetype_match_score=op.archetype_match_score,
            score_breakdown=op.score_breakdown or {},
            technical_analysis=op.technical_analysis or {},
            behavioral_analysis=op.behavioral_analysis or {},
            cultural_fit=op.cultural_fit or {},
            strengths=op.strengths or [],
            concerns=op.concerns or [],
            gaps=op.gaps or [],
            matched_skills=op.matched_skills or [],
            missing_skills=op.missing_skills or [],
            next_steps=op.next_steps,
            recruiter_notes=op.recruiter_notes,
            recruiter_override=op.recruiter_override,
            recruiter_override_reason=op.recruiter_override_reason,
            recruiter_override_by=op.recruiter_override_by,
            recruiter_override_at=op.recruiter_override_at,
            is_current=op.is_current,
            version=op.version,
            created_at=op.created_at,
            updated_at=op.updated_at,
            created_by=op.created_by
        ))
    
    return LiaOpinionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{opinion_id}", response_model=LiaOpinionFull)
async def get_opinion(
    opinion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get a specific opinion by ID."""
    company_id = current_user.company_id or "default"
    query = select(LiaOpinion).where(
        and_(
            LiaOpinion.id == opinion_id,
            LiaOpinion.company_id == company_id
        )
    )
    
    result = await db.execute(query)
    opinion = result.scalar_one_or_none()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")
    
    job_title = None
    if opinion.job_vacancy_id:
        job_query = select(JobVacancy.title).where(JobVacancy.id == opinion.job_vacancy_id)
        job_result = await db.execute(job_query)
        job_title = job_result.scalar_one_or_none()
    
    return LiaOpinionFull(
        id=opinion.id,
        candidate_id=opinion.candidate_id,
        opinion_type=opinion.opinion_type,
        source=opinion.source,
        job_vacancy_id=opinion.job_vacancy_id,
        job_vacancy_title=job_title,
        wsi_screening_id=opinion.wsi_screening_id,
        score=opinion.score,
        wsi_score=opinion.wsi_score,
        recommendation=opinion.recommendation,
        summary=opinion.summary,
        archetype=opinion.archetype,
        archetype_match_score=opinion.archetype_match_score,
        score_breakdown=opinion.score_breakdown or {},
        technical_analysis=opinion.technical_analysis or {},
        behavioral_analysis=opinion.behavioral_analysis or {},
        cultural_fit=opinion.cultural_fit or {},
        strengths=opinion.strengths or [],
        concerns=opinion.concerns or [],
        gaps=opinion.gaps or [],
        matched_skills=opinion.matched_skills or [],
        missing_skills=opinion.missing_skills or [],
        next_steps=opinion.next_steps,
        recruiter_notes=opinion.recruiter_notes,
        recruiter_override=opinion.recruiter_override,
        recruiter_override_reason=opinion.recruiter_override_reason,
        recruiter_override_by=opinion.recruiter_override_by,
        recruiter_override_at=opinion.recruiter_override_at,
        is_current=opinion.is_current,
        version=opinion.version,
        created_at=opinion.created_at,
        updated_at=opinion.updated_at,
        created_by=opinion.created_by
    )


@router.post("/", response_model=LiaOpinionFull)
async def create_opinion(
    data: LiaOpinionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Create a new LIA opinion."""
    company_id = current_user.company_id or "default"
    user_id = str(current_user.id)
    if data.opinion_type.value == "wsi" and not data.job_vacancy_id:
        raise HTTPException(
            status_code=400,
            detail="WSI opinions require a job_vacancy_id"
        )
    
    new_version = 1
    
    if data.job_vacancy_id:
        version_query = select(func.max(LiaOpinion.version)).where(
            and_(
                LiaOpinion.candidate_id == data.candidate_id,
                LiaOpinion.job_vacancy_id == data.job_vacancy_id,
                LiaOpinion.opinion_type == data.opinion_type.value,
                LiaOpinion.company_id == company_id
            )
        )
        version_result = await db.execute(version_query)
        max_version = version_result.scalar_one_or_none()
        if max_version:
            new_version = max_version + 1
        
        await db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == data.candidate_id,
                    LiaOpinion.job_vacancy_id == data.job_vacancy_id,
                    LiaOpinion.opinion_type == data.opinion_type.value,
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current == True
                )
            )
            .values(is_current=False)
        )
    else:
        version_query = select(func.max(LiaOpinion.version)).where(
            and_(
                LiaOpinion.candidate_id == data.candidate_id,
                LiaOpinion.opinion_type == "general",
                LiaOpinion.company_id == company_id
            )
        )
        version_result = await db.execute(version_query)
        max_version = version_result.scalar_one_or_none()
        if max_version:
            new_version = max_version + 1
        
        await db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == data.candidate_id,
                    LiaOpinion.opinion_type == "general",
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current == True
                )
            )
            .values(is_current=False)
        )
    
    opinion = LiaOpinion(
        candidate_id=data.candidate_id,
        opinion_type=data.opinion_type.value,
        source=data.source.value,
        job_vacancy_id=data.job_vacancy_id,
        wsi_screening_id=data.wsi_screening_id,
        score=data.score,
        wsi_score=data.wsi_score,
        recommendation=data.recommendation.value if data.recommendation else None,
        summary=data.summary,
        archetype=data.archetype,
        archetype_match_score=data.archetype_match_score,
        score_breakdown=data.score_breakdown,
        technical_analysis=data.technical_analysis,
        behavioral_analysis=data.behavioral_analysis,
        cultural_fit=data.cultural_fit,
        strengths=data.strengths,
        concerns=data.concerns,
        gaps=data.gaps,
        matched_skills=data.matched_skills,
        missing_skills=data.missing_skills,
        next_steps=data.next_steps,
        recruiter_notes=data.recruiter_notes,
        company_id=company_id,
        created_by=user_id,
        is_current=True,
        version=new_version
    )
    
    db.add(opinion)
    await db.commit()
    await db.refresh(opinion)
    
    logger.info(f"Created opinion {opinion.id} for candidate {data.candidate_id}")
    
    job_title = None
    if opinion.job_vacancy_id:
        job_query = select(JobVacancy.title).where(JobVacancy.id == opinion.job_vacancy_id)
        job_result = await db.execute(job_query)
        job_title = job_result.scalar_one_or_none()
    
    return LiaOpinionFull(
        id=opinion.id,
        candidate_id=opinion.candidate_id,
        opinion_type=opinion.opinion_type,
        source=opinion.source,
        job_vacancy_id=opinion.job_vacancy_id,
        job_vacancy_title=job_title,
        wsi_screening_id=opinion.wsi_screening_id,
        score=opinion.score,
        wsi_score=opinion.wsi_score,
        recommendation=opinion.recommendation,
        summary=opinion.summary,
        archetype=opinion.archetype,
        archetype_match_score=opinion.archetype_match_score,
        score_breakdown=opinion.score_breakdown or {},
        technical_analysis=opinion.technical_analysis or {},
        behavioral_analysis=opinion.behavioral_analysis or {},
        cultural_fit=opinion.cultural_fit or {},
        strengths=opinion.strengths or [],
        concerns=opinion.concerns or [],
        gaps=opinion.gaps or [],
        matched_skills=opinion.matched_skills or [],
        missing_skills=opinion.missing_skills or [],
        next_steps=opinion.next_steps,
        recruiter_notes=opinion.recruiter_notes,
        recruiter_override=opinion.recruiter_override,
        recruiter_override_reason=opinion.recruiter_override_reason,
        recruiter_override_by=opinion.recruiter_override_by,
        recruiter_override_at=opinion.recruiter_override_at,
        is_current=opinion.is_current,
        version=opinion.version,
        created_at=opinion.created_at,
        updated_at=opinion.updated_at,
        created_by=opinion.created_by
    )


@router.patch("/{opinion_id}", response_model=LiaOpinionFull)
async def update_opinion(
    opinion_id: UUID,
    data: LiaOpinionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Update a LIA opinion (e.g., recruiter notes or override)."""
    company_id = current_user.company_id or "default"
    user_id = str(current_user.id)
    query = select(LiaOpinion).where(
        and_(
            LiaOpinion.id == opinion_id,
            LiaOpinion.company_id == company_id
        )
    )
    
    result = await db.execute(query)
    opinion = result.scalar_one_or_none()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "recruiter_override" in update_data and update_data["recruiter_override"]:
        from datetime import datetime
        opinion.recruiter_override = update_data["recruiter_override"].value if hasattr(update_data["recruiter_override"], 'value') else update_data["recruiter_override"]
        opinion.recruiter_override_by = user_id
        opinion.recruiter_override_at = datetime.utcnow()
        if "recruiter_override_reason" in update_data:
            opinion.recruiter_override_reason = update_data["recruiter_override_reason"]
    
    for field, value in update_data.items():
        if field not in ["recruiter_override", "recruiter_override_reason"]:
            if hasattr(value, 'value'):
                setattr(opinion, field, value.value)
            else:
                setattr(opinion, field, value)
    
    await db.commit()
    await db.refresh(opinion)
    
    logger.info(f"Updated opinion {opinion_id}")
    
    job_title = None
    if opinion.job_vacancy_id:
        job_query = select(JobVacancy.title).where(JobVacancy.id == opinion.job_vacancy_id)
        job_result = await db.execute(job_query)
        job_title = job_result.scalar_one_or_none()
    
    return LiaOpinionFull(
        id=opinion.id,
        candidate_id=opinion.candidate_id,
        opinion_type=opinion.opinion_type,
        source=opinion.source,
        job_vacancy_id=opinion.job_vacancy_id,
        job_vacancy_title=job_title,
        wsi_screening_id=opinion.wsi_screening_id,
        score=opinion.score,
        wsi_score=opinion.wsi_score,
        recommendation=opinion.recommendation,
        summary=opinion.summary,
        archetype=opinion.archetype,
        archetype_match_score=opinion.archetype_match_score,
        score_breakdown=opinion.score_breakdown or {},
        technical_analysis=opinion.technical_analysis or {},
        behavioral_analysis=opinion.behavioral_analysis or {},
        cultural_fit=opinion.cultural_fit or {},
        strengths=opinion.strengths or [],
        concerns=opinion.concerns or [],
        gaps=opinion.gaps or [],
        matched_skills=opinion.matched_skills or [],
        missing_skills=opinion.missing_skills or [],
        next_steps=opinion.next_steps,
        recruiter_notes=opinion.recruiter_notes,
        recruiter_override=opinion.recruiter_override,
        recruiter_override_reason=opinion.recruiter_override_reason,
        recruiter_override_by=opinion.recruiter_override_by,
        recruiter_override_at=opinion.recruiter_override_at,
        is_current=opinion.is_current,
        version=opinion.version,
        created_at=opinion.created_at,
        updated_at=opinion.updated_at,
        created_by=opinion.created_by
    )


@router.delete("/{opinion_id}")
async def delete_opinion(
    opinion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Delete a LIA opinion (soft delete by marking as non-current)."""
    company_id = current_user.company_id or "default"
    query = select(LiaOpinion).where(
        and_(
            LiaOpinion.id == opinion_id,
            LiaOpinion.company_id == company_id
        )
    )
    
    result = await db.execute(query)
    opinion = result.scalar_one_or_none()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")
    
    opinion.is_current = False
    await db.commit()
    
    logger.info(f"Soft-deleted opinion {opinion_id}")
    
    return {"message": "Opinion deleted successfully", "id": str(opinion_id)}
