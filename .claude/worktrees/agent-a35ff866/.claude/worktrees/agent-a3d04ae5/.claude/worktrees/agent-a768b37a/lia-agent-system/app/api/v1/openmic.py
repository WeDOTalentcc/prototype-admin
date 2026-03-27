"""
OpenMic.ai API Endpoints

Handles voice screening webhooks and call management.
"""

from fastapi import APIRouter, HTTPException, Request, Header, status, Query
from typing import Optional, List
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
import logging

from app.services.openmic_service import (
    openmic_service,
    OpenMicWebhookEvent,
    CreateCallRequest
)
from app.core.database import AsyncSessionLocal
from app.models import VoiceScreeningCall, VoiceScreeningAnalysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openmic", tags=["openmic"])


@router.post("/webhook")
async def openmic_webhook(
    request: Request,
    x_openmic_signature: Optional[str] = Header(None, alias="X-OpenMic-Signature"),
    x_openmic_event: Optional[str] = Header(None, alias="X-OpenMic-Event")
):
    """
    Receive webhooks from OpenMic.ai for call events.
    
    Events:
    - call.started: Call initiated
    - call.ended: Call completed (includes full transcript)
    
    Security: Validates HMAC-SHA256 signature from X-OpenMic-Signature header
    """
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        
        # Verify webhook signature (CRITICAL SECURITY)
        if x_openmic_signature:
            is_valid = openmic_service.verify_webhook_signature(raw_body, x_openmic_signature)
            if not is_valid:
                logger.error("❌ Invalid webhook signature - potential attack!")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        else:
            logger.warning("⚠️  Webhook received without signature - security risk!")
        
        # Parse webhook payload
        payload = await request.json()
        
        logger.info(f"📞 Received OpenMic webhook: {x_openmic_event or payload.get('event')}")
        logger.debug(f"Payload: {payload}")
        
        # Parse event (flexible schema handles different event types)
        try:
            event = OpenMicWebhookEvent(**payload)
        except Exception as e:
            logger.error(f"❌ Failed to parse webhook payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        
        # Process event
        result = await openmic_service.process_webhook(event)
        
        return {
            "status": "success",
            "message": "Webhook processed",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing OpenMic webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test-call")
async def create_test_call(request: CreateCallRequest):
    """
    Create a test screening call.
    
    This endpoint:
    1. Creates an OpenMic agent configured for the job
    2. Initiates a call to the candidate
    3. Returns call_id for tracking
    
    Example:
    ```json
    {
      "job_title": "Backend Engineer Sênior Node.js",
      "job_description": "Desenvolvimento de APIs...",
      "required_skills": ["Node.js", "PostgreSQL", "Docker"],
      "candidate_phone": "+5511999999999",
      "candidate_name": "João Silva",
      "candidate_id": "cand_123"
    }
    ```
    """
    try:
        # Create screening agent
        logger.info(f"🤖 Creating screening agent for: {request.job_title}")
        agent = await openmic_service.create_screening_agent(
            job_title=request.job_title,
            job_description=request.job_description,
            required_skills=request.required_skills,
            questions=request.questions
        )
        
        # Start call
        logger.info(f"📞 Starting call to {request.candidate_name}")
        call = await openmic_service.start_screening_call(
            agent_id=agent["agent_id"],
            candidate_phone=request.candidate_phone,
            candidate_name=request.candidate_name,
            candidate_id=request.candidate_id,
            job_title=request.job_title
        )
        
        return {
            "status": "success",
            "message": "Screening call initiated",
            "agent_id": agent["agent_id"],
            "call_id": call["call_id"],
            "candidate": {
                "name": request.candidate_name,
                "phone": request.candidate_phone
            },
            "job_title": request.job_title
        }
        
    except ValueError as e:
        logger.error(f"❌ Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error creating test call: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def openmic_health():
    """Check OpenMic.ai integration health"""
    return {
        "status": "healthy",
        "service": "OpenMic.ai Voice Screening",
        "api_key_configured": bool(openmic_service.api_key),
        "webhook_secret_configured": bool(openmic_service.webhook_secret),
        "webhook_url": openmic_service.webhook_url
    }


@router.get("/screenings")
async def list_screenings(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    job_title: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100)
):
    """
    List voice screening calls with analysis.
    
    Filters:
    - job_title: Filter by job title (partial match)
    - recommendation: Filter by recommendation (reject, maybe, interview, strong_yes)
    - min_score: Minimum overall score (0-100)
    """
    async with AsyncSessionLocal() as session:
        # Build query with JOIN to enable analysis-based filtering
        query = (
            select(VoiceScreeningCall)
            .options(selectinload(VoiceScreeningCall.analysis))
            .outerjoin(VoiceScreeningCall.analysis)
            .order_by(desc(VoiceScreeningCall.created_at))
        )
        
        # Apply filters at SQL level
        if job_title:
            query = query.where(VoiceScreeningCall.job_title.ilike(f"%{job_title}%"))
        
        # Recommendation filter requires analysis to exist
        if recommendation:
            query = query.where(
                VoiceScreeningAnalysis.overall_recommendation == recommendation
            )
        
        # Min score filter requires analysis to exist
        if min_score is not None:
            query = query.where(
                VoiceScreeningAnalysis.overall_score >= min_score
            )
        
        # Count total before pagination
        count_query = select(func.count()).select_from(VoiceScreeningCall).outerjoin(VoiceScreeningCall.analysis)
        if job_title:
            count_query = count_query.where(VoiceScreeningCall.job_title.ilike(f"%{job_title}%"))
        if recommendation:
            count_query = count_query.where(VoiceScreeningAnalysis.overall_recommendation == recommendation)
        if min_score is not None:
            count_query = count_query.where(VoiceScreeningAnalysis.overall_score >= min_score)
        
        total = await session.scalar(count_query)
        
        # Execute query with pagination
        result = await session.execute(query.offset(offset).limit(limit))
        screenings = result.scalars().unique().all()  # unique() to avoid duplicates from join
        
        # No more Python filtering needed
        filtered_screenings = screenings
        
        # Convert to dict
        screenings_data = []
        for screening in filtered_screenings:
            data = {
                "id": str(screening.id),
                "call_id": screening.call_id,
                "candidate_name": screening.candidate_name,
                "candidate_phone": screening.candidate_phone,
                "job_title": screening.job_title,
                "duration_seconds": screening.duration_seconds,
                "call_status": screening.call_status,
                "processing_status": screening.processing_status,
                "created_at": screening.created_at.isoformat() if screening.created_at is not None else None,
                "analysis": None
            }
            
            if screening.analysis:
                data["analysis"] = {
                    "overall_score": screening.analysis.overall_score,
                    "overall_recommendation": screening.analysis.overall_recommendation,
                    "overall_confidence": screening.analysis.overall_confidence,
                    "tech_score": screening.analysis.tech_score,
                    "comm_score": screening.analysis.comm_score,
                    "fit_score": screening.analysis.fit_score,
                    "summary": screening.analysis.summary,
                    "key_strengths": screening.analysis.key_strengths,
                    "key_concerns": screening.analysis.key_concerns
                }
            
            screenings_data.append(data)
        
        return {
            "screenings": screenings_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }


@router.get("/screenings/{screening_id}")
async def get_screening(screening_id: str):
    """
    Get detailed screening call and analysis.
    """
    async with AsyncSessionLocal() as session:
        query = (
            select(VoiceScreeningCall)
            .options(selectinload(VoiceScreeningCall.analysis))
            .where(VoiceScreeningCall.id == screening_id)
        )
        
        result = await session.execute(query)
        screening = result.scalar_one_or_none()
        
        if not screening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screening not found"
            )
        
        # Convert to detailed dict
        data = {
            "id": str(screening.id),
            "call_id": screening.call_id,
            "agent_id": screening.agent_id,
            "candidate_name": screening.candidate_name,
            "candidate_id": screening.candidate_id,
            "candidate_phone": screening.candidate_phone,
            "job_title": screening.job_title,
            "job_description": screening.job_description,
            "required_skills": screening.required_skills,
            "duration_seconds": screening.duration_seconds,
            "call_status": screening.call_status,
            "call_type": screening.call_type,
            "start_timestamp": screening.start_timestamp.isoformat() if screening.start_timestamp is not None else None,
            "end_timestamp": screening.end_timestamp.isoformat() if screening.end_timestamp is not None else None,
            "transcript": screening.transcript,
            "transcript_object": screening.transcript_object,
            "processing_status": screening.processing_status,
            "created_at": screening.created_at.isoformat() if screening.created_at is not None else None,
            "analysis": None
        }
        
        if screening.analysis:
            analysis = screening.analysis
            data["analysis"] = {
                "id": str(analysis.id),
                "analysis_model": analysis.analysis_model,
                "analysis_method": analysis.analysis_method,
                
                # Basic analysis
                "basic_skills_mentioned": analysis.basic_skills_mentioned,
                "basic_overall_score": analysis.basic_overall_score,
                
                # Technical assessment
                "technical_assessment": {
                    "skills_mentioned": analysis.tech_skills_mentioned,
                    "skills_matched": analysis.tech_skills_matched,
                    "skills_missing": analysis.tech_skills_missing,
                    "experience_years": analysis.tech_experience_years,
                    "projects_mentioned": analysis.tech_projects_mentioned,
                    "technical_score": analysis.tech_score
                },
                
                # Communication assessment
                "communication_assessment": {
                    "clarity": analysis.comm_clarity,
                    "confidence": analysis.comm_confidence,
                    "engagement": analysis.comm_engagement,
                    "professionalism": analysis.comm_professionalism,
                    "communication_score": analysis.comm_score,
                    "notes": analysis.comm_notes
                },
                
                # Cultural fit
                "cultural_fit": {
                    "motivation": analysis.fit_motivation,
                    "work_preferences": analysis.fit_work_preferences,
                    "red_flags": analysis.fit_red_flags,
                    "green_flags": analysis.fit_green_flags,
                    "fit_score": analysis.fit_score
                },
                
                # Overall evaluation
                "overall_evaluation": {
                    "overall_score": analysis.overall_score,
                    "recommendation": analysis.overall_recommendation,
                    "confidence": analysis.overall_confidence,
                    "key_strengths": analysis.key_strengths,
                    "key_concerns": analysis.key_concerns,
                    "next_steps": analysis.next_steps
                },
                
                "summary": analysis.summary,
                "detailed_notes": analysis.detailed_notes,
                "created_at": analysis.created_at.isoformat() if analysis.created_at is not None else None
            }
        
        return data


@router.get("/analytics")
async def get_analytics():
    """
    Get voice screening analytics and statistics.
    """
    async with AsyncSessionLocal() as session:
        # Total screenings
        total_screenings = await session.scalar(
            select(func.count()).select_from(VoiceScreeningCall)
        )
        
        # Screenings with analysis
        analyzed_screenings = await session.scalar(
            select(func.count()).select_from(VoiceScreeningCall).where(VoiceScreeningCall.is_analyzed == True)
        )
        
        # Average scores
        avg_overall = await session.scalar(
            select(func.avg(VoiceScreeningAnalysis.overall_score))
        )
        avg_tech = await session.scalar(
            select(func.avg(VoiceScreeningAnalysis.tech_score))
        )
        avg_comm = await session.scalar(
            select(func.avg(VoiceScreeningAnalysis.comm_score))
        )
        avg_fit = await session.scalar(
            select(func.avg(VoiceScreeningAnalysis.fit_score))
        )
        
        # Recommendation breakdown
        recommendations = await session.execute(
            select(
                VoiceScreeningAnalysis.overall_recommendation,
                func.count(VoiceScreeningAnalysis.id)
            ).group_by(VoiceScreeningAnalysis.overall_recommendation)
        )
        
        recommendation_breakdown = {rec: count for rec, count in recommendations}
        
        # Top job titles
        top_jobs = await session.execute(
            select(
                VoiceScreeningCall.job_title,
                func.count(VoiceScreeningCall.id).label('count')
            ).group_by(VoiceScreeningCall.job_title).order_by(desc('count')).limit(10)
        )
        
        top_job_titles = [{"job_title": title, "count": count} for title, count in top_jobs]
        
        return {
            "total_screenings": total_screenings or 0,
            "analyzed_screenings": analyzed_screenings or 0,
            "average_scores": {
                "overall": round(avg_overall, 1) if avg_overall else 0,
                "technical": round(avg_tech, 1) if avg_tech else 0,
                "communication": round(avg_comm, 1) if avg_comm else 0,
                "cultural_fit": round(avg_fit, 1) if avg_fit else 0
            },
            "recommendation_breakdown": recommendation_breakdown,
            "top_job_titles": top_job_titles
        }
