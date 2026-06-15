"""
Interview event handlers.

Routes:
- POST /handle-trigger/interview-scheduled
- POST /handle-trigger/interview-completed
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service as get_activity_service_canonical

from .._shared import (
    InterviewScheduledRequest,
    InterviewScheduledResponse,
    InterviewCompletedRequest,
    InterviewCompletedResponse,
    ensure_company_access,
    get_activity_service,
    get_calendar_service,
    get_email_service,
    get_scheduling_service,
    get_whatsapp_service,
    get_wsi_service,
    log_automation_execution,
    validate_multi_tenancy,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helpers – interview scheduled
# ---------------------------------------------------------------------------

async def _create_interview_record(db, request, candidate_name: str, candidate_email, interviewer_name: str, interview_link: str, job_title: str):
    """Create interview record in DB. Returns interview_id or None on failure."""
    try:
        scheduling_service = get_scheduling_service()
        interview = await scheduling_service.create_interview(
            db=db, candidate_id=request.candidate_id, candidate_name=candidate_name,
            candidate_email=candidate_email or "", interviewer_name=interviewer_name,
            interviewer_email=request.interviewer_email or "",
            start_time=request.interview_datetime, duration_minutes=request.duration_minutes,
            interview_type=request.interview_type,
            interview_mode="video" if interview_link else "in_person",
            job_title=job_title, job_vacancy_id=request.vacancy_id,
            location=interview_link or None, notes=request.notes, created_by="automation_trigger"
        )
        return str(interview.id)
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Failed to create interview record: {e}")
        return None


async def _send_interview_email(request, candidate_name: str, candidate_email: str, job_title: str, interviewer_name: str, interview_link: str) -> bool:
    """Send email invitation to candidate. Returns True if sent."""
    if not candidate_email:
        return False
    try:
        from app.templates.communication_templates import EmailTemplates
        email_service = get_email_service()
        email_content = EmailTemplates.interview_scheduled(
            candidate_name=candidate_name, job_title=job_title,
            interview_date=request.interview_datetime,
            interview_link=interview_link or "A confirmar", interviewer_name=interviewer_name
        )
        send_result = await email_service.send_email(
            to_email=candidate_email, subject=email_content["subject"],
            body_html=email_content["body"].replace("\n", "<br>"),
            body_text=email_content["body"], company_id=request.company_id
        )
        return send_result.get("success", False)
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Failed to send email: {e}")
        return False


async def _send_interview_whatsapp(request, candidate_name: str, candidate_phone, interview_link: str, interview_id) -> bool:
    """Send WhatsApp confirmation to candidate. Returns True if sent."""
    if not candidate_phone:
        return False
    try:
        from app.templates.communication_templates import WhatsAppTemplates
        whatsapp_service = get_whatsapp_service()
        msg = WhatsAppTemplates.interview_scheduled(
            candidate_name=candidate_name, interview_date=request.interview_datetime,
            interview_link=interview_link or "A confirmar"
        )
        result = await whatsapp_service.send_message(
            to_phone=candidate_phone, message=msg,
            metadata={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "company_id": request.company_id, "interview_id": interview_id,
                "type": "interview_scheduled"
            }
        )
        return result.success
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Failed to send WhatsApp: {e}")
        return False


async def _create_interview_calendar_event(request, candidate_name: str, candidate_email, job_title: str, interview_link: str) -> tuple:
    """Create calendar event via Microsoft Graph. Returns (created, event_id)."""
    if not request.organizer_email or not request.interviewer_email:
        return False, None
    try:
        cal_svc = get_calendar_service()
        event = await cal_svc.schedule_interview(
            organizer_email=request.organizer_email, candidate_name=candidate_name,
            candidate_email=candidate_email or "",
            interviewer_emails=[request.interviewer_email],
            position=job_title, start_time=request.interview_datetime,
            duration_minutes=request.duration_minutes,
            location=interview_link if not interview_link else None,
            as_teams_meeting=bool(interview_link), notes=request.notes
        )
        return True, event.get("id")
    except Exception as e:
        logger.warning(f"⚠️ [INTERVIEW_SCHEDULED] Calendar creation skipped: {e}")
        return False, None


async def _log_interview_scheduled_audit(db, request, email_sent: bool, whatsapp_sent: bool, calendar_event_created: bool, notification_created: bool, interview_id, calendar_event_id) -> None:
    """Log automation execution log for interview_scheduled trigger."""
    try:
        from app.models.automation import AutomationExecutionLog
        db.add(AutomationExecutionLog(
            company_id=request.company_id, trigger_event="interview_scheduled",
            trigger_data={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "interview_datetime": request.interview_datetime.isoformat(),
                "interview_type": request.interview_type, "duration_minutes": request.duration_minutes
            },
            candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            action_executed="send_interview_invites",
            action_result={
                "email_sent": email_sent, "whatsapp_sent": whatsapp_sent,
                "calendar_event_created": calendar_event_created,
                "notification_created": notification_created,
                "interview_id": interview_id, "calendar_event_id": calendar_event_id
            },
            status="success" if (email_sent or whatsapp_sent) else "partial",
            execution_time_ms=0
        ))
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Failed to create audit log: {e}")


async def _notify_interview_scheduled(activity_svc, request, candidate_name: str, job_title: str, interviewer_name: str, interview_link: str, interview_id, email_sent: bool, whatsapp_sent: bool, calendar_event_id) -> bool:
    """Create recruiter notification for interview scheduled. Returns True if created."""
    try:
        await activity_svc.create_activity(
            activity_type="interview_scheduled",
            title=f"Entrevista Agendada - {candidate_name}",
            description=(
                f"Entrevista agendada para {candidate_name} na posição de {job_title}. "
                f"Data: {request.interview_datetime.strftime('%d/%m/%Y às %H:%M')}. "
                f"Tipo: {request.interview_type}."
            ),
            actor_id="system", actor_name="LIA Automation", actor_type="system",
            target_id=request.candidate_id, target_type="candidate",
            extra_data={
                "vacancy_id": request.vacancy_id, "company_id": request.company_id,
                "interview_id": interview_id, "interview_datetime": request.interview_datetime.isoformat(),
                "interview_type": request.interview_type, "duration_minutes": request.duration_minutes,
                "interviewer_name": interviewer_name, "interview_link": interview_link,
                "email_sent": email_sent, "whatsapp_sent": whatsapp_sent, "calendar_event_id": calendar_event_id
            },
            category="scheduling"
        )
        return True
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Failed to create notification: {e}")
        return False


def _build_interview_scheduled_response(request, email_sent: bool, whatsapp_sent: bool, calendar_event_created: bool, notification_created: bool, interview_id, calendar_event_id) -> dict:
    """Build the response dict for interview_scheduled trigger."""
    return {
        "success": True, "trigger": "interview_scheduled",
        "email_sent": email_sent, "whatsapp_sent": whatsapp_sent,
        "calendar_event_created": calendar_event_created, "notification_created": notification_created,
        "interview_id": interview_id, "calendar_event_id": calendar_event_id,
        "metadata": {
            "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
            "interview_datetime": request.interview_datetime.isoformat(),
            "interview_type": request.interview_type,
            "processed_at": datetime.utcnow().isoformat()
        }
    }


async def _send_all_interview_communications(request, db, activity_svc, candidate_name: str, candidate_email, job_title: str, interviewer_name: str, interview_link: str) -> tuple:
    """Send all communications for interview_scheduled. Returns (interview_id, email_sent, whatsapp_sent, calendar_event_created, calendar_event_id, notification_created)."""
    interview_id = await _create_interview_record(
        db, request, candidate_name, candidate_email, interviewer_name, interview_link, job_title
    )
    email_sent = await _send_interview_email(
        request, candidate_name, candidate_email, job_title, interviewer_name, interview_link
    )
    whatsapp_sent = await _send_interview_whatsapp(
        request, candidate_name, request.candidate_phone, interview_link, interview_id
    )
    calendar_event_created, calendar_event_id = await _create_interview_calendar_event(
        request, candidate_name, candidate_email, job_title, interview_link
    )
    notification_created = await _notify_interview_scheduled(
        activity_svc, request, candidate_name, job_title, interviewer_name,
        interview_link, interview_id, email_sent, whatsapp_sent, calendar_event_id
    )
    return interview_id, email_sent, whatsapp_sent, calendar_event_created, calendar_event_id, notification_created


async def _process_interview_scheduled(request, db, activity_svc) -> dict:
    """Orchestrate interview_scheduled trigger: validate, communicate, audit, respond."""
    logger.info(
        f"📅 [INTERVIEW_SCHEDULED] Processing: candidate={request.candidate_id}, "
        f"vacancy={request.vacancy_id}, datetime={request.interview_datetime.isoformat()}"
    )

    is_valid, error_message = await validate_multi_tenancy(
        db=db, candidate_id=request.candidate_id,
        vacancy_id=request.vacancy_id, company_id=request.company_id
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_message)

    candidate_name = request.candidate_name or "Candidato"
    job_title = request.job_title or "Vaga"
    interviewer_name = request.interviewer_name or "Equipe"
    interview_link = request.interview_link or ""

    interview_id, email_sent, whatsapp_sent, calendar_event_created, calendar_event_id, notification_created = \
        await _send_all_interview_communications(
            request, db, activity_svc, candidate_name, request.candidate_email,
            job_title, interviewer_name, interview_link
        )

    await _log_interview_scheduled_audit(
        db, request, email_sent, whatsapp_sent,
        calendar_event_created, notification_created, interview_id, calendar_event_id
    )

    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
    logger.info(f"✅ [INTERVIEW_SCHEDULED] Done: email={email_sent}, whatsapp={whatsapp_sent}, calendar={calendar_event_created}")

    return _build_interview_scheduled_response(
        request, email_sent, whatsapp_sent, calendar_event_created,
        notification_created, interview_id, calendar_event_id
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/interview-scheduled", response_model=InterviewScheduledResponse)
async def handle_interview_scheduled(
    request: InterviewScheduledRequest,
    db: AsyncSession = Depends(get_db),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Handle interview_scheduled trigger: send invites and create calendar event."""
    try:
        return await _process_interview_scheduled(request, db, activity_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/handle-trigger/interview-completed", response_model=InterviewCompletedResponse)
async def handle_interview_completed(
    request: InterviewCompletedRequest,
    db: AsyncSession = Depends(get_tenant_db),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Handle interview_completed trigger.

    Generates parecer (assessment) and suggests next stage when an interview is completed.

    This endpoint performs:
    1. Generate parecer using WSI Evaluator agent based on interview data
    2. Calculate recommendation (advance/hold/reject) based on competency ratings
    3. Suggest next stage based on interview performance
    4. Notify the recruiter with the assessment
    5. Log audit entry

    Args:
        request: InterviewCompletedRequest with interview results
        db: Database session

    Returns:
        Result with parecer, suggested_next_stage, confidence, and notification status
    """
    try:
        logger.info(
            f"📋 [INTERVIEW_COMPLETED] Processing trigger for "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}, "
            f"interview={request.interview_id}, type={request.interview_type}"
        )

        # Step 0: Multi-tenancy validation
        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="INTERVIEW_COMPLETED",
        )

        notification_created = False
        parecer_id = None

        candidate_name = request.candidate_name or "Candidato"
        job_title = request.job_title or "Vaga"
        interviewer_name = request.interviewer_name or "Entrevistador"

        strengths = []
        development_areas = []
        recommendation = "hold"
        confidence = 0.7
        average_rating = 0.0

        if request.competency_ratings:
            ratings = list(request.competency_ratings.values())
            if ratings:
                average_rating = sum(ratings) / len(ratings)

                for competency, rating in request.competency_ratings.items():
                    if rating >= 4.0:
                        strengths.append(f"{competency.replace('_', ' ').title()}: {rating:.1f}/5.0")
                    elif rating < 3.0:
                        development_areas.append(f"{competency.replace('_', ' ').title()}: precisa desenvolvimento ({rating:.1f}/5.0)")

                if average_rating >= 4.0:
                    recommendation = "advance"
                    confidence = min(0.95, 0.7 + (average_rating - 4.0) * 0.25)
                elif average_rating >= 3.0:
                    recommendation = "hold"
                    confidence = 0.7 + (average_rating - 3.0) * 0.1
                else:
                    recommendation = "reject"
                    confidence = min(0.9, 0.7 + (3.0 - average_rating) * 0.1)

        if request.transcript or request.interviewer_notes:
            try:
                get_wsi_service()
                from app.domains.ai.services.llm import llm_service

                analysis_prompt = f"""Analise os dados desta entrevista e forneça uma avaliação estruturada.

Tipo de Entrevista: {request.interview_type}
Vaga: {job_title}
Candidato: {candidate_name}

Notas do Entrevistador:
{request.interviewer_notes or "Não fornecidas"}

Avaliações de Competências:
{request.competency_ratings or "Não fornecidas"}

Impressão Geral:
{request.overall_impression or "Não fornecida"}

{f"Transcrição (resumo):{chr(10)}{request.transcript[:3000]}" if request.transcript else ""}

Por favor, forneça:
1. Resumo executivo (2-3 frases)
2. 3-5 pontos fortes identificados
3. 2-3 áreas de desenvolvimento
4. Recomendação: "advance" (próxima etapa), "hold" (aguardar mais informações), ou "reject" (não recomendado)

Responda em JSON:
{{
    "summary": "...",
    "strengths": ["...", "..."],
    "development_areas": ["...", "..."],
    "recommendation": "advance|hold|reject",
    "confidence": 0.85
}}"""

                content = await llm_service.safe_invoke(analysis_prompt, provider="claude")

                import json
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()

                analysis = json.loads(content)

                if analysis.get("strengths"):
                    strengths = analysis["strengths"]
                if analysis.get("development_areas"):
                    development_areas = analysis["development_areas"]
                if analysis.get("recommendation"):
                    recommendation = analysis["recommendation"]
                if analysis.get("confidence"):
                    confidence = analysis["confidence"]

                parecer_summary = analysis.get("summary", "")

                logger.info(f"🤖 [INTERVIEW_COMPLETED] AI analysis completed: recommendation={recommendation}")

            except Exception as e:
                logger.warning(f"⚠️ [INTERVIEW_COMPLETED] AI analysis failed, using fallback: {e}")
                parecer_summary = request.overall_impression or f"Entrevista {request.interview_type} concluída."
        else:
            parecer_summary = request.overall_impression or f"Entrevista {request.interview_type} concluída."

        if recommendation == "advance":
            if request.interview_type == "technical":
                suggested_next_stage = "Entrevista Comportamental"
            elif request.interview_type == "behavioral":
                suggested_next_stage = "Entrevista Cultural"
            elif request.interview_type == "cultural":
                suggested_next_stage = "Proposta"
            else:
                suggested_next_stage = "Entrevista Final"
        elif recommendation == "hold":
            suggested_next_stage = "Revisão Adicional"
        else:
            suggested_next_stage = "Reprovado"

        try:
            from app.models.lia_opinion import LiaOpinion

            score = average_rating if average_rating > 0 else (4.0 if recommendation == "advance" else 2.5 if recommendation == "hold" else 2.0)

            parecer = LiaOpinion(
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id,
                company_id=request.company_id,
                opinion_type="wsi",
                source="full_interview",
                score=score,
                wsi_score=score,
                recommendation="approved" if recommendation == "advance" else "pending_review" if recommendation == "hold" else "not_approved",
                summary=parecer_summary,
                strengths=strengths,
                concerns=development_areas,
                technical_analysis={
                    "interview_type": request.interview_type,
                    "competency_ratings": request.competency_ratings or {},
                    "average_rating": average_rating
                },
                behavioral_analysis={
                    "overall_impression": request.overall_impression,
                    "interviewer_name": interviewer_name
                },
                next_steps=f"Próxima etapa sugerida: {suggested_next_stage}",
                is_current=True,
                version=1,
                created_by="automation_trigger"
            )

            db.add(parecer)
            await db.flush()
            parecer_id = str(parecer.id)

            logger.info(f"📄 [INTERVIEW_COMPLETED] Parecer created: {parecer_id}")

        except Exception as e:
            logger.error(f"❌ [INTERVIEW_COMPLETED] Failed to save parecer: {e}")

        try:
            recommendation_text = {
                "advance": "✅ Recomendado para próxima etapa",
                "hold": "⏸️ Aguardando avaliação adicional",
                "reject": "❌ Não recomendado"
            }.get(recommendation, "Pendente")

            await activity_svc.create_activity(
                activity_type="interview_completed",
                title=f"Entrevista Concluída - {candidate_name}",
                description=(
                    f"Entrevista {request.interview_type} de {candidate_name} para {job_title} foi concluída. "
                    f"Avaliação: {average_rating:.1f}/5.0. {recommendation_text}. "
                    f"Próxima etapa sugerida: {suggested_next_stage}"
                ),
                actor_id="system",
                actor_name="LIA Automation",
                actor_type="system",
                target_id=request.candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    "interview_id": request.interview_id,
                    "interview_type": request.interview_type,
                    "interviewer_name": interviewer_name,
                    "average_rating": average_rating,
                    "recommendation": recommendation,
                    "suggested_next_stage": suggested_next_stage,
                    "parecer_id": parecer_id,
                    "confidence": confidence
                },
                category="interview"
            )
            notification_created = True
            logger.info("🔔 [INTERVIEW_COMPLETED] Recruiter notification created")
        except Exception as e:
            logger.error(f"❌ [INTERVIEW_COMPLETED] Failed to create notification: {e}")

        await log_automation_execution(
            db,
            trigger_event="interview_completed",
            trigger_data={
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "interview_id": request.interview_id,
                "interview_type": request.interview_type,
                "has_notes": bool(request.interviewer_notes),
                "has_transcript": bool(request.transcript),
                "competency_count": len(request.competency_ratings) if request.competency_ratings else 0,
            },
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id,
            action_executed="generate_parecer",
            action_result={
                "parecer_id": parecer_id,
                "recommendation": recommendation,
                "average_rating": average_rating,
                "suggested_next_stage": suggested_next_stage,
                "confidence": confidence,
                "notification_created": notification_created,
            },
            status="success" if parecer_id else "partial",
        )

        response_data = {
            "success": True,
            "trigger": "interview_completed",
            "parecer": {
                "id": parecer_id,
                "summary": parecer_summary,
                "strengths": strengths,
                "development_areas": development_areas,
                "recommendation": recommendation,
                "average_rating": round(average_rating, 2) if average_rating > 0 else None
            },
            "suggested_next_stage": suggested_next_stage,
            "confidence": round(confidence, 2),
            "notification_created": notification_created,
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "interview_id": request.interview_id,
                "interview_type": request.interview_type,
                "processed_at": datetime.utcnow().isoformat()
            }
        }

        logger.info(
            f"✅ [INTERVIEW_COMPLETED] Processing complete: "
            f"recommendation={recommendation}, next_stage={suggested_next_stage}, "
            f"confidence={confidence:.2f}, notification={notification_created}"
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_COMPLETED] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
