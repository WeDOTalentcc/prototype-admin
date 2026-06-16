"""
Interview Analysis API - Endpoints para análise de transcrições de entrevista.

Integra:
- Microsoft Teams transcription (FREE via Graph API)
- WSI deterministic analysis
- LIA Opinion generation
"""
import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.communication.services.teams_recording_service import teams_recording_service
from app.domains.interview_scheduling.repositories.interview_analysis_repository import InterviewAnalysisRepository
from app.domains.interview_scheduling.services.interview_transcript_analysis_service import (
    interview_transcript_analysis_service,
)
from app.models.interview import Interview
from app.models.lia_opinion import LiaOpinion
from app.schemas.lia_opinion import LiaOpinionCreate, OpinionSourceEnum, OpinionTypeEnum, RecommendationEnum
from app.services.notification_service import (
    NotificationChannel,
    NotificationType,
    ProactiveNotificationType,
    notification_service,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview-analysis", tags=["Interview Analysis"])


class AnalyzeInterviewRequest(WeDoBaseModel):
    """Request to analyze interview transcript."""
    interview_id: str
    force_refresh: bool = False


class AnalyzeTranscriptRequest(WeDoBaseModel):
    """Request to analyze raw transcript text."""
    transcript_text: str
    candidate_id: str
    job_vacancy_id: str | None = None
    interview_type: str = "technical"


# DUPLICATE_OF_INTENT: app/api/v1/teams.py — Microsoft Teams webhook validation envelope (Sprint Q.1 triagem I bucket)
class TeamsWebhookPayload(WeDoBaseModel):
    """Microsoft Teams subscription webhook payload."""
    value: list = []
    validationToken: str | None = None


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status check."""
    interview_id: str
    status: str
    has_transcript: bool
    has_analysis: bool
    analysis_result: dict[str, Any] | None = None
    error: str | None = None


# TODO(phase2): extract to repository — multi-model interview/opinion join
async def create_opinion_from_analysis(
    analysis_result,
    company_id: str,
    db: AsyncSession
) -> UUID:
    """
    Create a LiaOpinion record from TranscriptAnalysisResult.
    """
    try:
        repo = InterviewAnalysisRepository(db)

        candidate_id = UUID(analysis_result.candidate_id)
        job_vacancy_id = UUID(analysis_result.job_vacancy_id) if analysis_result.job_vacancy_id else None

        recommendation_map = {
            "approve": RecommendationEnum.APPROVED,
            "approved": RecommendationEnum.APPROVED,
            "reject": RecommendationEnum.NOT_APPROVED,
            "not_approved": RecommendationEnum.NOT_APPROVED,
            "pending_review": RecommendationEnum.PENDING_REVIEW
        }
        recommendation = recommendation_map.get(
            analysis_result.recommendation.lower(),
            RecommendationEnum.PENDING_REVIEW
        )

        normalized_score = (analysis_result.overall_wsi_score / 5.0) * 100.0

        new_opinion_type = OpinionTypeEnum.WSI if job_vacancy_id else OpinionTypeEnum.GENERAL

        # Deactivate previous opinions via repo
        await repo.deactivate_current_opinions(
            candidate_id=candidate_id,
            opinion_type=new_opinion_type.value,
            company_id=company_id,
            job_vacancy_id=job_vacancy_id,
        )

        opinion_data = LiaOpinionCreate(
            candidate_id=candidate_id,
            opinion_type=OpinionTypeEnum.WSI if job_vacancy_id else OpinionTypeEnum.GENERAL,
            source=OpinionSourceEnum.FULL_INTERVIEW,
            job_vacancy_id=job_vacancy_id,
            wsi_screening_id=None,
            score=normalized_score,
            wsi_score=analysis_result.overall_wsi_score,
            recommendation=recommendation,
            summary=analysis_result.summary,
            archetype=None,
            archetype_match_score=None,
            score_breakdown={
                "technical_score": analysis_result.technical_score,
                "behavioral_score": analysis_result.behavioral_score,
                "cultural_score": analysis_result.cultural_score,
                "bloom_average": analysis_result.bloom_average,
                "dreyfus_average": analysis_result.dreyfus_average,
                "cbi_completeness": analysis_result.cbi_completeness
            },
            technical_analysis={
                "score": analysis_result.technical_score,
                "strengths": analysis_result.strengths
            },
            behavioral_analysis={
                "score": analysis_result.behavioral_score,
                "big_five_profile": analysis_result.big_five_profile
            },
            cultural_fit={
                "score": analysis_result.cultural_score,
                "concerns": analysis_result.concerns
            },
            strengths=analysis_result.strengths,
            concerns=analysis_result.concerns,
            gaps=analysis_result.red_flags,
            matched_skills=[],
            missing_skills=[],
            next_steps=None,
            recruiter_notes=None
        )

        opinion = LiaOpinion(
            candidate_id=opinion_data.candidate_id,
            opinion_type=opinion_data.opinion_type.value,
            source=opinion_data.source.value,
            job_vacancy_id=opinion_data.job_vacancy_id,
            wsi_screening_id=opinion_data.wsi_screening_id,
            score=opinion_data.score,
            wsi_score=opinion_data.wsi_score,
            recommendation=opinion_data.recommendation.value if opinion_data.recommendation else None,
            summary=opinion_data.summary,
            archetype=opinion_data.archetype,
            archetype_match_score=opinion_data.archetype_match_score,
            score_breakdown=opinion_data.score_breakdown,
            technical_analysis=opinion_data.technical_analysis,
            behavioral_analysis=opinion_data.behavioral_analysis,
            cultural_fit=opinion_data.cultural_fit,
            strengths=opinion_data.strengths,
            concerns=opinion_data.concerns,
            gaps=opinion_data.gaps,
            matched_skills=opinion_data.matched_skills,
            missing_skills=opinion_data.missing_skills,
            next_steps=opinion_data.next_steps,
            recruiter_notes=opinion_data.recruiter_notes,
            is_current=True,
            version=1,
            created_by="system",
            company_id=company_id
        )

        opinion = await repo.create_opinion(opinion)

        logger.info(f"✅ Created LIA Opinion {opinion.id} for candidate {candidate_id}, score: {normalized_score}")

        return opinion.id

    except Exception as e:
        logger.error(f"❌ Failed to create opinion from analysis: {e}")
        raise


async def send_analysis_notification(
    interview: Interview,
    analysis_result,
    opinion_id: UUID,
    company_id: str,
    db: AsyncSession
):
    """
    Send notification to recruiter after interview analysis completes.
    """
    try:
        recruiter_id = interview.created_by or "default_user"
        candidate_name = interview.candidate_name or "Candidato"
        wsi_score = analysis_result.overall_wsi_score
        recommendation = analysis_result.recommendation

        rec_emoji = "✅" if recommendation == "approve" else "❌" if recommendation == "reject" else "⏳"
        rec_text = "APROVAR" if recommendation == "approve" else "REJEITAR" if recommendation == "reject" else "ANÁLISE PENDENTE"

        message = f"{rec_emoji} Score WSI: {wsi_score:.1f}/5.0\n"
        message += f"Recomendação: {rec_text}\n"
        message += f"Cargo: {interview.job_title or 'N/A'}"

        base_url = os.getenv("APP_URL", "https://plataforma-lia.replit.app")
        action_url = f"{base_url}/approvals?candidate_id={interview.candidate_id}&opinion_id={opinion_id}"

        actions = [
            {"type": "approve", "label": "Aprovar", "url": f"{action_url}&action=approve"},
            {"type": "reject", "label": "Rejeitar", "url": f"{action_url}&action=reject"},
            {"type": "view", "label": "Ver Detalhes", "url": action_url}
        ]

        await notification_service.send_multi_channel_notification(
            user_id=recruiter_id,
            title=f"Análise de Entrevista Concluída - {candidate_name}",
            message=message,
            channels=[NotificationChannel.TEAMS, NotificationChannel.BELL, NotificationChannel.EMAIL],
            notification_type=NotificationType.ACTION_REQUIRED,
            proactive_type=ProactiveNotificationType.SCREENING_COMPLETED,
            priority="high",
            data={
                "interview_id": str(interview.id),
                "candidate_id": str(interview.candidate_id),
                "opinion_id": str(opinion_id),
                "wsi_score": wsi_score,
                "recommendation": recommendation,
                "action_url": action_url,
                "action_label": "Ver Parecer Completo",
                "candidate_name": candidate_name,
                "job_title": interview.job_title or "N/A",
                "actions": actions
            },
            related_candidate_id=str(interview.candidate_id),
            related_job_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
            suggested_actions=["Aprovar Candidato", "Rejeitar Candidato", "Ver Parecer Completo"],
            db=db
        )

        logger.info(f"🔔 Analysis notification sent for interview {interview.id} to recruiter {recruiter_id}")

    except Exception as e:
        logger.error(f"❌ Failed to send analysis notification: {e}")


@router.post("/analyze/{interview_id}", response_model=None)
async def analyze_interview(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    force_refresh: bool = Query(False, description="Force fetch new transcript from Teams"),
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analyze an interview's transcript using WSI methodology.
    """
    try:
        repo = InterviewAnalysisRepository(db)
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        transcript_text = None

        if interview.feedback and interview.feedback.get("transcript_text") and not force_refresh:
            transcript_text = interview.feedback["transcript_text"]
            logger.info(f"Using stored transcript for interview {interview_id}")
        elif interview.meeting_id and interview.graph_organizer_email:
            logger.info(f"Fetching transcript from Teams for interview {interview_id}")
            transcript = await teams_recording_service.get_meeting_transcript(
                meeting_id=interview.meeting_id,
                organizer_id=interview.graph_organizer_email
            )
            if transcript:
                transcript_text = teams_recording_service.parse_vtt_to_text(transcript.content)
                current_feedback = interview.feedback or {}
                current_feedback["transcript_text"] = transcript_text
                current_feedback["transcript_fetched_at"] = datetime.utcnow().isoformat()
                await repo.update_interview_feedback(interview_id, current_feedback)

        if not transcript_text:
            raise HTTPException(
                status_code=400,
                detail="No transcript available. Meeting may not have transcription enabled or meeting hasn't ended yet."
            )

        if not interview.candidate_id:
            raise HTTPException(
                status_code=400,
                detail="Interview does not have an associated candidate"
            )

        candidate_id = str(interview.candidate_id)
        job_vacancy_id = str(interview.job_vacancy_id) if interview.job_vacancy_id else None

        analysis_result = interview_transcript_analysis_service.analyze_transcript(
            transcript_text=transcript_text,
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            job_competencies=None
        )

        current_feedback = interview.feedback or {}
        current_feedback["wsi_analysis"] = analysis_result.to_dict()
        current_feedback["analyzed_at"] = datetime.utcnow().isoformat()

        await repo.update_interview_feedback(interview_id, current_feedback)

        opinion_id = await create_opinion_from_analysis(
            analysis_result=analysis_result,
            company_id=company_id,
            db=db
        )

        logger.info(f"✅ Interview analysis completed: {interview_id}, WSI={analysis_result.overall_wsi_score}, opinion_id={opinion_id}")

        return {
            "success": True,
            "interview_id": interview_id,
            "candidate_name": interview.candidate_name,
            "opinion_id": str(opinion_id),
            "analysis": analysis_result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to analyze interview {interview_id}: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/analyze-transcript", response_model=None)
async def analyze_raw_transcript(
    request: AnalyzeTranscriptRequest,
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analyze a raw transcript text using WSI methodology.
    """
    try:
        if not request.transcript_text or len(request.transcript_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Transcript text is too short. Minimum 100 characters required."
            )

        interview_id = str(uuid.uuid4())

        analysis_result = interview_transcript_analysis_service.analyze_transcript(
            transcript_text=request.transcript_text,
            interview_id=interview_id,
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            job_competencies=None
        )

        opinion_id = await create_opinion_from_analysis(
            analysis_result=analysis_result,
            company_id=company_id,
            db=db
        )

        logger.info(f"✅ Raw transcript analysis completed: WSI={analysis_result.overall_wsi_score}, opinion_id={opinion_id}")

        return {
            "success": True,
            "generated_interview_id": interview_id,
            "candidate_id": request.candidate_id,
            "interview_type": request.interview_type,
            "opinion_id": str(opinion_id),
            "analysis": analysis_result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to analyze raw transcript: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/teams-webhook", response_model=None)
async def teams_meeting_webhook(
    payload: TeamsWebhookPayload,
    background_tasks: BackgroundTasks,
    response: Response,
    request: Request, 
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Webhook to receive Microsoft Graph subscription notifications.
    """
    if payload.validationToken:
        logger.info("📋 Responding to Teams subscription validation request")
        response.headers["Content-Type"] = "text/plain"
        return Response(content=payload.validationToken, media_type="text/plain")

    expected_client_state = os.getenv("TEAMS_WEBHOOK_CLIENT_STATE")
    webhook_secret = os.getenv("TEAMS_WEBHOOK_SECRET")

    if expected_client_state:
        client_state_found = False
        if payload.value and len(payload.value) > 0:
            client_state_found = payload.value[0].get("clientState") == expected_client_state

        if not client_state_found:
            logger.warning("❌ Invalid or missing clientState in webhook notification")
            raise HTTPException(status_code=401, detail="Invalid client state")

    if webhook_secret:
        webhook_signature = request.headers.get("X-Hub-Signature-256")

        if not webhook_signature:
            logger.warning("❌ Webhook secret configured but no X-Hub-Signature-256 header provided")
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(webhook_signature, expected_signature):
            logger.warning("❌ Invalid HMAC signature in webhook")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        logger.info("✅ HMAC signature verified")

    logger.info(f"📥 Received Teams webhook with {len(payload.value)} notifications")

    for notification in payload.value:
        change_type = notification.get("changeType")
        resource = notification.get("resource", "")
        resource_data = notification.get("resourceData", {})

        logger.info(f"Processing notification: changeType={change_type}, resource={resource}")

        if change_type == "created" and ("transcripts" in resource or "recordings" in resource):
            background_tasks.add_task(
                process_meeting_transcript,
                resource_data,
                resource
            )

    return {"status": "accepted", "processed": len(payload.value)}


@router.get("/status/{interview_id}", response_model=None)
async def get_analysis_status(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)) -> AnalysisStatusResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get status of interview analysis."""
    try:
        repo = InterviewAnalysisRepository(db)
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        feedback = interview.feedback or {}
        has_transcript = bool(feedback.get("transcript_text"))
        has_analysis = bool(feedback.get("wsi_analysis"))

        if interview.status == "completed" and has_analysis:
            status = "analyzed"
        elif interview.status == "completed" and has_transcript:
            status = "transcript_ready"
        elif interview.status == "completed":
            status = "awaiting_transcript"
        else:
            status = interview.status

        return AnalysisStatusResponse(
            interview_id=interview_id,
            status=status,
            has_transcript=has_transcript,
            has_analysis=has_analysis,
            analysis_result=feedback.get("wsi_analysis") if has_analysis else None,
            error=feedback.get("analysis_error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get analysis status for {interview_id}: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/results/{interview_id}", response_model=None)
async def get_analysis_results(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get full analysis results for an interview."""
    try:
        repo = InterviewAnalysisRepository(db)
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        feedback = interview.feedback or {}
        analysis = feedback.get("wsi_analysis")

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="No analysis found for this interview. Run analysis first."
            )

        return {
            "interview_id": interview_id,
            "candidate_name": interview.candidate_name,
            "candidate_email": interview.candidate_email,
            "interview_type": interview.interview_type,
            "job_title": interview.job_title,
            "interview_date": interview.start_time.isoformat() if interview.start_time else None,
            "analyzed_at": feedback.get("analyzed_at"),
            "analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get analysis results for {interview_id}: {e}")
        raise LIAError(message="Erro interno do servidor")


async def process_meeting_transcript(resource_data: dict, resource_path: str = ""):
    """
    Background task to process meeting transcript when notified by Teams webhook.
    """
    from app.core.database import AsyncSessionLocal

    try:
        meeting_id = resource_data.get("meetingId") or resource_data.get("id")
        organizer_id = resource_data.get("organizerId")

        if not meeting_id:
            logger.warning("No meeting ID in webhook notification")
            return

        logger.info(f"🔄 Processing transcript for meeting: {meeting_id}")

        async with AsyncSessionLocal() as db:
            repo = InterviewAnalysisRepository(db)
            interview = await repo.get_interview_by_meeting_id(meeting_id)

            if not interview:
                logger.info(f"No interview found for meeting {meeting_id}, skipping")
                return

            organizer = organizer_id or interview.graph_organizer_email

            if not organizer:
                logger.warning(f"No organizer ID for meeting {meeting_id}")
                return

            transcript = await teams_recording_service.get_meeting_transcript(
                meeting_id=meeting_id,
                organizer_id=organizer
            )

            if not transcript:
                logger.info(f"No transcript available yet for meeting {meeting_id}")
                return

            transcript_text = teams_recording_service.parse_vtt_to_text(transcript.content)

            if not interview.candidate_id:
                logger.error(f"Cannot process transcript: Interview {interview.id} does not have an associated candidate")
                return

            candidate_id = str(interview.candidate_id)
            job_vacancy_id = str(interview.job_vacancy_id) if interview.job_vacancy_id else None

            analysis_result = interview_transcript_analysis_service.analyze_transcript(
                transcript_text=transcript_text,
                interview_id=str(interview.id),
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                job_competencies=None
            )

            current_feedback = interview.feedback or {}
            current_feedback["transcript_text"] = transcript_text
            current_feedback["transcript_fetched_at"] = datetime.utcnow().isoformat()
            current_feedback["wsi_analysis"] = analysis_result.to_dict()
            current_feedback["analyzed_at"] = datetime.utcnow().isoformat()
            current_feedback["auto_analyzed"] = True

            interview.transcript = transcript_text
            interview.transcript_language = "pt-BR"
            interview.transcript_source = "teams"
            interview.transcribed_at = datetime.utcnow()

            await repo.update_interview_status_and_feedback(
                interview_id=str(interview.id),
                feedback=current_feedback,
                status="completed",
            )
            await db.commit()

            company_id = interview.company_id if hasattr(interview, 'company_id') and interview.company_id else None
            logger.warning(f"Using company_id='{company_id}' for background interview analysis task")
            opinion_id = await create_opinion_from_analysis(
                analysis_result=analysis_result,
                company_id=company_id,
                db=db
            )

            await send_analysis_notification(
                interview=interview,
                analysis_result=analysis_result,
                opinion_id=opinion_id,
                company_id=company_id,
                db=db
            )

            logger.info(
                f"✅ Auto-analyzed interview {interview.id}: "
                f"WSI={analysis_result.overall_wsi_score}, "
                f"recommendation={analysis_result.recommendation}, "
                f"opinion_id={opinion_id}"
            )

    except Exception as e:
        logger.error(f"❌ Failed to process meeting transcript: {e}")

reorder_collection_before_item(router)
