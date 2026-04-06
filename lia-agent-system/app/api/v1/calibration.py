"""
Calibration API endpoints.

Endpoints for managing the calibration loop:
- Record explicit/implicit feedback
- Get divergences and stats
- Manage calibration suggestions
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.calibration_service import CalibrationService

router = APIRouter(prefix="/calibration", tags=["Calibration"])


class ExplicitFeedbackRequest(BaseModel):
    candidate_id: str
    job_id: str | None = None
    agrees_with_lia: bool
    lia_score: float | None = None
    lia_recommendation: str | None = None
    feedback_reason: str | None = None
    context: dict[str, Any] | None = None


class ImplicitFeedbackRequest(BaseModel):
    candidate_id: str
    job_id: str
    action: str
    stage_from: str | None = None
    stage_to: str | None = None
    lia_score: float | None = None
    lia_ranking: int | None = None
    context: dict[str, Any] | None = None


class PostHireFeedbackRequest(BaseModel):
    candidate_id: str
    job_id: str
    success: bool
    lia_score: float | None = None
    feedback_reason: str | None = None
    context: dict[str, Any] | None = None


class SuggestionActionRequest(BaseModel):
    reason: str | None = None


class StartCalibrationSessionRequest(BaseModel):
    job_vacancy_id: str
    job_description: str
    technical_skills: list[str] = []
    behavioral_competencies: list[str] = []
    location: str | None = None
    limit: int = 5


class CalibrationCandidate(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    experience_years: int | None = None
    location: str | None = None
    skills: list[str] = []
    match_score: float = 0.0
    source: str | None = None


class StartCalibrationSessionResponse(BaseModel):
    session_id: str
    candidates: list[CalibrationCandidate]
    total_found: int


@router.post("/start", response_model=StartCalibrationSessionResponse)
async def start_calibration_session(
    request: StartCalibrationSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Start a calibration session by finding potential candidates for the job.
    Returns candidates for the recruiter to approve/reject for LIA calibration.
    """
    import uuid

    from app.models.candidate import Candidate
    
    session_id = str(uuid.uuid4())
    
    try:
        query = db.query(Candidate)
        
        if request.technical_skills:
            skills_filter = " | ".join(request.technical_skills)
            query = query.filter(
                Candidate.skills.op('~*')(skills_filter)
            )
        
        if request.location:
            query = query.filter(
                Candidate.location.ilike(f"%{request.location}%")
            )
        
        candidates_db = query.limit(request.limit * 2).all()
        
        calibration_candidates = []
        for c in candidates_db[:request.limit]:
            skills_list = []
            if hasattr(c, 'skills') and c.skills:
                if isinstance(c.skills, str):
                    skills_list = [s.strip() for s in c.skills.split(',') if s.strip()]
                elif isinstance(c.skills, list):
                    skills_list = c.skills
            
            match_score = 0.5
            if request.technical_skills and skills_list:
                matching = sum(1 for s in request.technical_skills 
                              if any(s.lower() in skill.lower() for skill in skills_list))
                match_score = min(0.9, 0.3 + (matching / max(len(request.technical_skills), 1)) * 0.6)
            
            calibration_candidates.append(CalibrationCandidate(
                id=str(c.id),
                name=c.name or "Candidato",
                email=c.email,
                phone=c.phone,
                title=c.current_title,
                experience_years=c.years_experience,
                location=c.location,
                skills=skills_list,
                match_score=round(match_score, 2),
                source=c.source
            ))
        
        return StartCalibrationSessionResponse(
            session_id=session_id,
            candidates=calibration_candidates,
            total_found=len(calibration_candidates)
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error starting calibration session: {e}")
        return StartCalibrationSessionResponse(
            session_id=session_id,
            candidates=[],
            total_found=0
        )


@router.post("/feedback/explicit")
async def record_explicit_feedback(
    request: ExplicitFeedbackRequest,
    user_id: str = "system",
    db: Session = Depends(get_db)
):
    """Record explicit feedback (thumbs up/down) from recruiter."""
    service = CalibrationService(db)
    
    event = await service.record_explicit_feedback(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        user_id=user_id,
        agrees_with_lia=request.agrees_with_lia,
        lia_score=request.lia_score,
        lia_recommendation=request.lia_recommendation,
        feedback_reason=request.feedback_reason,
        context=request.context
    )
    
    return {
        "success": True,
        "message": "Feedback recorded",
        "data": event.to_dict()
    }


@router.post("/feedback/implicit")
async def record_implicit_feedback(
    request: ImplicitFeedbackRequest,
    user_id: str = "system",
    db: Session = Depends(get_db)
):
    """Record implicit feedback from recruiter actions (stage changes, etc)."""
    service = CalibrationService(db)
    
    event = await service.record_implicit_feedback(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        user_id=user_id,
        action=request.action,
        stage_from=request.stage_from,
        stage_to=request.stage_to,
        lia_score=request.lia_score,
        lia_ranking=request.lia_ranking,
        context=request.context
    )
    
    return {
        "success": True,
        "message": "Implicit feedback recorded",
        "data": event.to_dict()
    }


@router.post("/feedback/post-hire")
async def record_post_hire_feedback(
    request: PostHireFeedbackRequest,
    user_id: str = "system",
    db: Session = Depends(get_db)
):
    """Record post-hire outcome feedback."""
    service = CalibrationService(db)
    
    event = await service.record_post_hire_feedback(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        user_id=user_id,
        success=request.success,
        lia_score=request.lia_score,
        feedback_reason=request.feedback_reason,
        context=request.context
    )
    
    return {
        "success": True,
        "message": "Post-hire feedback recorded",
        "data": event.to_dict()
    }


@router.get("/divergences")
async def get_divergences(
    days: int = 30,
    min_delta: float = 5.0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recent divergences between LIA and recruiter decisions."""
    service = CalibrationService(db)
    
    divergences = await service.get_divergences(
        days=days,
        min_score_delta=min_delta,
        limit=limit
    )
    
    return {
        "success": True,
        "data": divergences,
        "count": len(divergences)
    }


@router.get("/stats")
async def get_calibration_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get calibration statistics for the dashboard."""
    service = CalibrationService(db)
    
    stats = await service.get_calibration_stats(days=days)
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/suggestions")
async def get_pending_suggestions(
    db: Session = Depends(get_db)
):
    """Get all pending calibration suggestions."""
    service = CalibrationService(db)
    
    suggestions = await service.get_pending_suggestions()
    
    return {
        "success": True,
        "data": suggestions,
        "count": len(suggestions)
    }


@router.post("/suggestions/generate")
async def generate_suggestions(
    db: Session = Depends(get_db)
):
    """Analyze divergences and generate new calibration suggestions."""
    service = CalibrationService(db)
    
    suggestions = await service.generate_suggestions()
    
    return {
        "success": True,
        "message": f"Generated {len(suggestions)} suggestions",
        "data": [s.to_dict() for s in suggestions]
    }


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: str,
    user_id: str = "system",
    db: Session = Depends(get_db)
):
    """Approve a calibration suggestion."""
    service = CalibrationService(db)
    
    suggestion = await service.approve_suggestion(suggestion_id, user_id)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    return {
        "success": True,
        "message": "Suggestion approved and weights updated",
        "data": suggestion.to_dict()
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: str,
    request: SuggestionActionRequest,
    user_id: str = "system",
    db: Session = Depends(get_db)
):
    """Reject a calibration suggestion."""
    service = CalibrationService(db)
    
    suggestion = await service.reject_suggestion(
        suggestion_id, 
        user_id, 
        reason=request.reason
    )
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    return {
        "success": True,
        "message": "Suggestion rejected",
        "data": suggestion.to_dict()
    }


@router.get("/events")
async def get_recent_events(
    limit: int = 50,
    feedback_types: str | None = None,
    db: Session = Depends(get_db)
):
    """Get recent calibration events."""
    service = CalibrationService(db)
    
    types_list = feedback_types.split(",") if feedback_types else None
    
    events = await service.get_recent_events(
        limit=limit,
        feedback_types=types_list
    )
    
    return {
        "success": True,
        "data": events,
        "count": len(events)
    }


@router.get("/weights")
async def get_weights(
    job_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Get current calibration weights."""
    service = CalibrationService(db)
    
    weights = await service.get_weights(job_id=job_id)
    
    return {
        "success": True,
        "data": weights,
        "count": len(weights)
    }


@router.get("/dashboard")
async def get_calibration_dashboard(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get complete calibration dashboard data."""
    service = CalibrationService(db)
    
    stats = await service.get_calibration_stats(days=days)
    divergences = await service.get_divergences(days=days, limit=10)
    suggestions = await service.get_pending_suggestions()
    weights = await service.get_weights()
    
    return {
        "success": True,
        "data": {
            "stats": stats,
            "divergences": divergences,
            "suggestions": suggestions,
            "weights": weights,
            "generated_at": datetime.utcnow().isoformat()
        }
    }
