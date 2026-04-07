import uuid

"""
Event handler trigger routes.

Includes:
- POST /handle-trigger/screening-completed
- POST /handle-trigger/interview-scheduled
- POST /handle-trigger/interview-completed
- POST /handle-trigger/candidate-inactive
- POST /handle-trigger/candidate-no-show
- POST /handle-trigger/ats-sync
- POST /handle-trigger/offer-sent
- POST /handle-trigger/candidate-hired
- POST /handle-trigger/candidate-rejected
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service as get_activity_service_canonical
from app.shared.compliance.audit_service import AuditService, get_audit_service

from ._shared import (
    WSI_PASS_THRESHOLD,
    ATSSyncRequest,
    ATSSyncResponse,
    CandidateHiredPayload,
    CandidateHiredResponse,
    CandidateInactiveRequest,
    CandidateInactiveResponse,
    CandidateNoShowRequest,
    CandidateNoShowResponse,
    CandidateRejectedPayload,
    CandidateRejectedResponse,
    InterviewCompletedRequest,
    InterviewCompletedResponse,
    InterviewScheduledRequest,
    InterviewScheduledResponse,
    OfferSentPayload,
    OfferSentResponse,
    ScreeningCompletedRequest,
    ScreeningCompletedResponse,
    CommunicationService,
    get_communication_service,
    get_activity_service,
    get_ats_sync_service,
    get_calendar_service,
    get_email_service,
    get_whatsapp_service,
    get_wsi_service,
    map_lia_stage_to_ats,
    notify_unmapped_stage,
    validate_multi_tenancy,
)

logger = logging.getLogger(__name__)

router = APIRouter()

async def _fetch_candidate_and_vacancy(db, candidate_id: str, vacancy_id: str):
    """Fetch candidate and vacancy from DB, raise 404 if not found."""
    from sqlalchemy import select
    from app.models.candidate import Candidate
    from app.models.job_vacancy import JobVacancy

    candidate_result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = candidate_result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")

    vacancy_result = await db.execute(select(JobVacancy).where(JobVacancy.id == vacancy_id))
    vacancy = vacancy_result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    return candidate, vacancy


def _build_screening_response_analyses(responses: list) -> list:
    """Build ResponseAnalysis objects from structured response list."""
    from app.domains.cv_screening.services.wsi_service import ResponseAnalysis
    result = []
    for resp in responses:
        result.append(ResponseAnalysis(
            question_id=resp.get("question_id", str(uuid.uuid4())),
            competency=resp.get("competency", "general"),
            response_text=resp.get("response", ""),
            evidences=resp.get("evidences", []),
            red_flags=resp.get("red_flags", []),
            final_score=resp.get("score", 3.0),
            justification=resp.get("justification", "Análise automática")
        ))
    return result


def _normalize_weights(weights: dict, response_analyses: list) -> dict:
    """Compute and normalize competency weights.

    Returns an empty dict when response_analyses is empty (no division-by-zero).
    """
    if not response_analyses:
        return {}
    if not weights:
        equal_weight = 1.0 / len(response_analyses)
        weights = {a.competency: equal_weight for a in response_analyses}
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    return weights


def _determine_screening_decision(overall_wsi: float):
    """Determine screening decision and next stage from WSI score."""
    passed = overall_wsi >= WSI_PASS_THRESHOLD
    recommendation = "passed" if passed else "failed"
    if overall_wsi >= WSI_PASS_THRESHOLD:
        decision, suggested_next_stage = "aprovado", "Entrevista Técnica"
    elif overall_wsi >= 3.0:
        decision, suggested_next_stage = "aguardando", "Entrevista Técnica"
    else:
        decision, suggested_next_stage = "nao_aprovado", None
    return passed, recommendation, decision, suggested_next_stage


async def _send_screening_communication(
    comm_svc, db, request, passed: bool, overall_wsi: float,
    candidate, vacancy, candidate_feedback
) -> bool:
    """Send screening result communication to candidate. Returns True if sent."""
    candidate_email = getattr(candidate, 'email', None)
    candidate_name = getattr(candidate, 'name', 'Candidato')
    candidate_phone = getattr(candidate, 'phone', None)
    company_name = getattr(vacancy, 'company_name', None) or request.company_id
    all_strengths = (
        candidate_feedback.technical_strengths + candidate_feedback.behavioral_strengths
    )
    try:
        comm_result = await comm_svc.send_screening_result(
            db=db, candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            company_id=request.company_id, passed=passed, wsi_score=overall_wsi,
            strengths=all_strengths, development_areas=candidate_feedback.development_opportunities,
            candidate_name=candidate_name, candidate_email=candidate_email,
            candidate_phone=candidate_phone, job_title=vacancy.title, company_name=company_name
        )
        return comm_result.get("success", False)
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to send communication: {e}")
        return False


async def _create_screening_recruiter_notification(
    activity_svc, request, overall_wsi: float, wsi_result,
    recommendation: str, passed: bool, suggested_next_stage, candidate_name: str, vacancy
) -> bool:
    """Create recruiter notification for screening completion. Returns True if created."""
    try:
        await activity_svc.create_activity(
            activity_type="screening_wsi_completed",
            title=f"Triagem WSI Concluída - {candidate_name}",
            description=(
                f"Candidato {candidate_name} completou triagem por {request.screening_type}. "
                f"WSI: {overall_wsi:.2f}/5.0 ({wsi_result.classification}). "
                f"Recomendação: {recommendation.upper()}"
            ),
            actor_id="system", actor_name="LIA Automation", actor_type="system",
            target_id=request.candidate_id, target_type="candidate",
            extra_data={
                "vacancy_id": request.vacancy_id, "vacancy_title": vacancy.title,
                "company_id": request.company_id, "screening_type": request.screening_type,
                "wsi_score": overall_wsi, "wsi_classification": wsi_result.classification,
                "recommendation": recommendation, "passed": passed,
                "suggested_next_stage": suggested_next_stage
            },
            category="screening"
        )
        return True
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create notification: {e}")
        return False


def _add_screening_execution_log(db, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool) -> None:
    """Persist AutomationExecutionLog for screening WSI calculation."""
    try:
        from app.models.automation import AutomationExecutionLog
        execution_time = int((request.metadata or {}).get("duration_seconds", 0) * 1000)
        db.add(AutomationExecutionLog(
            company_id=request.company_id, trigger_event="screening_completed",
            trigger_data={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "screening_type": request.screening_type, "has_transcript": bool(request.transcript),
                "responses_count": len(request.responses) if request.responses else 0
            },
            candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            action_executed="wsi_calculation",
            action_result={
                "wsi_score": overall_wsi, "technical_wsi": wsi_result.technical_wsi,
                "behavioral_wsi": wsi_result.behavioral_wsi,
                "classification": wsi_result.classification,
                "recommendation": recommendation, "passed": passed
            },
            status="success", execution_time_ms=str(execution_time)
        ))
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create execution log: {e}")


async def _record_screening_decision(audit_svc, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool, suggested_next_stage, weights: dict) -> None:
    """Call audit_svc.log_decision for screening WSI evaluation."""
    try:
        wsi_dimensions = list(weights.keys()) if weights else ["technical", "behavioral"]
        reasoning_list = [
            f"WSI Score: {overall_wsi:.2f}/5.0 ({wsi_result.classification})",
            f"Technical WSI: {wsi_result.technical_wsi:.2f}",
            f"Behavioral WSI: {wsi_result.behavioral_wsi:.2f}",
            f"Threshold: {WSI_PASS_THRESHOLD}",
            f"Screening Type: {request.screening_type}",
            f"Candidate passed screening - recommended for: {suggested_next_stage}" if passed else "Candidate did not meet minimum WSI threshold",
        ]
        await audit_svc.log_decision(
            company_id=request.company_id, agent_name="wsi_evaluator",
            decision_type="screening_evaluation", action="evaluate_screening",
            decision=recommendation, score=overall_wsi, confidence=0.85,
            reasoning=reasoning_list, criteria_used=wsi_dimensions,
            candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
            human_review_required=not passed
        )
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Failed to create audit log: {e}")


async def _log_screening_audit(db, audit_svc, request, overall_wsi: float, wsi_result, recommendation: str, passed: bool, suggested_next_stage, weights: dict) -> None:
    """Log automation execution log and centralized audit for screening."""
    _add_screening_execution_log(db, request, overall_wsi, wsi_result, recommendation, passed)
    await _record_screening_decision(audit_svc, request, overall_wsi, wsi_result, recommendation, passed, suggested_next_stage, weights)


def _validate_screening_request(request) -> None:
    """Raise HTTPException if screening request payload is invalid."""
    if not request.candidate_id or not request.vacancy_id:
        raise HTTPException(status_code=400, detail="candidate_id e vacancy_id são obrigatórios")
    if not request.transcript and not request.responses:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer 'transcript' ou 'responses' para calcular o WSI"
        )


async def _calculate_wsi(request, vacancy, wsi_service) -> tuple:
    """Calculate WSI score and classification. Returns (wsi_result, response_analyses, weights)."""
    if request.responses:
        response_analyses = _build_screening_response_analyses(request.responses)
    else:
        response_analyses = await _analyze_transcript_for_wsi(
            transcript=request.transcript, vacancy_title=vacancy.title, wsi_service=wsi_service
        )
    weights = _normalize_weights(request.competency_weights or {}, response_analyses)
    wsi_result = wsi_service.calculate_wsi(
        candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
        responses=response_analyses, weights=weights
    )
    return wsi_result, response_analyses, weights


def _build_screening_response(request, wsi_result, response_analyses, overall_wsi: float, recommendation: str, passed: bool, communication_sent: bool, notification_created: bool, suggested_next_stage: str, candidate_feedback) -> dict:
    """Build the final response dict for screening_completed trigger."""
    return {
        "success": True,
        "trigger": "screening_completed",
        "wsi_score": round(overall_wsi, 2),
        "wsi_details": {
            "technical_wsi": round(wsi_result.technical_wsi, 2),
            "behavioral_wsi": round(wsi_result.behavioral_wsi, 2),
            "classification": wsi_result.classification,
            "percentile": wsi_result.percentile
        },
        "recommendation": recommendation,
        "passed": passed,
        "communication_sent": communication_sent,
        "notification_created": notification_created,
        "suggested_next_stage": suggested_next_stage,
        "confidence": 0.85,
        "candidate_feedback": {
            "decision": candidate_feedback.decision,
            "main_message": candidate_feedback.main_message,
            "technical_strengths": candidate_feedback.technical_strengths,
            "development_opportunities": candidate_feedback.development_opportunities,
            "next_steps": candidate_feedback.next_steps
        },
        "metadata": {
            "screening_type": request.screening_type,
            "responses_analyzed": len(response_analyses),
            "processed_at": datetime.utcnow().isoformat()
        }
    }


async def _score_and_decide(request, vacancy, wsi_service):
    """Run WSI calculation and decide outcome. Returns (wsi_result, analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage)."""
    wsi_result, response_analyses, weights = await _calculate_wsi(request, vacancy, wsi_service)
    overall_wsi = wsi_result.overall_wsi
    passed, recommendation, decision, suggested_next_stage = _determine_screening_decision(overall_wsi)
    logger.info(
        f"📊 [SCREENING_COMPLETED] WSI={overall_wsi:.2f}, "
        f"classification={wsi_result.classification}, recommendation={recommendation}"
    )
    return wsi_result, response_analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage


async def _process_screening_completed(request, db, audit_svc, activity_svc, comm_svc) -> dict:
    """Orchestrate screening_completed trigger: validate, score, notify, audit, respond."""
    logger.info(
        f"🎯 [SCREENING_COMPLETED] Processing: candidate={request.candidate_id}, "
        f"vacancy={request.vacancy_id}, type={request.screening_type}"
    )

    is_valid, error_message = await validate_multi_tenancy(
        db=db, candidate_id=request.candidate_id,
        vacancy_id=request.vacancy_id, company_id=request.company_id
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_message)

    _validate_screening_request(request)

    candidate, vacancy = await _fetch_candidate_and_vacancy(db, request.candidate_id, request.vacancy_id)
    wsi_service = get_wsi_service()
    wsi_result, response_analyses, weights, overall_wsi, passed, recommendation, decision, suggested_next_stage = \
        await _score_and_decide(request, vacancy, wsi_service)

    candidate_feedback = await wsi_service.generate_candidate_feedback(
        wsi_result=wsi_result, responses=response_analyses, decision=decision
    )
    communication_sent = await _send_screening_communication(
        comm_svc, db, request, passed, overall_wsi, candidate, vacancy, candidate_feedback
    )
    notification_created = await _create_screening_recruiter_notification(
        activity_svc, request, overall_wsi, wsi_result,
        recommendation, passed, suggested_next_stage, getattr(candidate, 'name', 'Candidato'), vacancy
    )
    await _log_screening_audit(
        db, audit_svc, request, overall_wsi, wsi_result, recommendation, passed, suggested_next_stage, weights
    )

    logger.info(f"✅ [SCREENING_COMPLETED] Done: wsi={overall_wsi:.2f}, recommendation={recommendation}")

    return _build_screening_response(
        request, wsi_result, response_analyses, overall_wsi, recommendation,
        passed, communication_sent, notification_created, suggested_next_stage, candidate_feedback
    )


@router.post("/handle-trigger/screening-completed", response_model=ScreeningCompletedResponse)
async def handle_screening_completed(request: ScreeningCompletedRequest, db: AsyncSession = Depends(get_db), audit_svc: AuditService = Depends(get_audit_service), activity_svc: ActivityService = Depends(get_activity_service_canonical), comm_svc: CommunicationService = Depends(get_communication_service)):
    """Handle screening_completed trigger: WSI calculation and candidate notification."""
    try:
        return await _process_screening_completed(request, db, audit_svc, activity_svc, comm_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SCREENING_COMPLETED] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar triagem: {str(e)}")


def _build_wsi_prompt(transcript: str, vacancy_title: str) -> str:
    """Build the LLM prompt for WSI transcript analysis."""
    return f"""Analise esta transcrição de triagem e extraia as respostas do candidato para avaliação WSI.

Vaga: {vacancy_title}

Transcrição:
{transcript[:8000]}

Extraia cada pergunta/resposta relevante e avalie:
1. Competência avaliada
2. Qualidade da resposta (1-5)
3. Evidências concretas mencionadas
4. Red flags identificados
5. Justificativa da nota

Responda em JSON:
{{
  "responses": [
    {{
      "question_id": "q1",
      "competency": "Nome da competência",
      "response_text": "Resumo da resposta",
      "score": 4.0,
      "evidences": ["Evidência 1", "Evidência 2"],
      "red_flags": [],
      "justification": "Candidato demonstrou X com exemplo concreto Y"
    }}
  ]
}}"""


def _parse_wsi_llm_response(content: str, transcript: str, ResponseAnalysis) -> list:
    """Parse LLM JSON output into ResponseAnalysis objects; falls back on error."""
    import json
    try:
        if "```json" in content:
            start = content.find("```json") + 7
            content = content[content.find("```json") + 7:content.find("```", start)].strip()
        elif "```" in content:
            start = content.find("```") + 3
            content = content[start:content.find("```", start)].strip()
        return [
            ResponseAnalysis(
                question_id=r.get("question_id", str(uuid.uuid4())),
                competency=r.get("competency", "general"),
                response_text=r.get("response_text", ""),
                evidences=r.get("evidences", []),
                red_flags=r.get("red_flags", []),
                final_score=float(r.get("score", 3.0)),
                justification=r.get("justification", "Análise automática"),
            )
            for r in json.loads(content).get("responses", [])
        ]
    except Exception:
        return [ResponseAnalysis(
            question_id=str(uuid.uuid4()), competency="general",
            response_text=transcript[:500] if transcript else "",
            evidences=[], red_flags=["Falha na análise automática"],
            final_score=3.0, justification="Análise automática não completada - score padrão aplicado",
        )]


async def _analyze_transcript_for_wsi(transcript: str, vacancy_title: str, wsi_service) -> list:
    """Analyze a conversation transcript and extract structured ResponseAnalysis objects via LLM."""
    from app.domains.cv_screening.services.wsi_service import ResponseAnalysis
    from app.services.llm import llm_service
    try:
        content = await llm_service.safe_invoke(_build_wsi_prompt(transcript, vacancy_title), provider="claude")
        return _parse_wsi_llm_response(content, transcript, ResponseAnalysis)
    except Exception as e:
        logger.error(f"Failed to analyze transcript: {e}")
        return [ResponseAnalysis(
            question_id=str(uuid.uuid4()), competency="general",
            response_text=transcript[:500] if transcript else "",
            evidences=[], red_flags=["Falha na análise automática"],
            final_score=3.0, justification="Análise automática não completada - score padrão aplicado",
        )]


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
            execution_time_ms="0"
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

    logger.info(f"✅ [INTERVIEW_SCHEDULED] Done: email={email_sent}, whatsapp={whatsapp_sent}, calendar={calendar_event_created}")

    return _build_interview_scheduled_response(
        request, email_sent, whatsapp_sent, calendar_event_created,
        notification_created, interview_id, calendar_event_id
    )


@router.post("/handle-trigger/interview-scheduled", response_model=InterviewScheduledResponse)
async def handle_interview_scheduled(request: InterviewScheduledRequest, db: AsyncSession = Depends(get_db), activity_svc: ActivityService = Depends(get_activity_service_canonical)):
    """Handle interview_scheduled trigger: send invites and create calendar event."""
    try:
        return await _process_interview_scheduled(request, db, activity_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [INTERVIEW_SCHEDULED] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar agendamento de entrevista: {str(e)}")


@router.post("/handle-trigger/interview-completed", response_model=InterviewCompletedResponse)
async def handle_interview_completed(
    request: InterviewCompletedRequest,
    db: AsyncSession = Depends(get_db),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
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
        is_valid, error_message = await validate_multi_tenancy(
            db=db,
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id
        )
        if not is_valid:
            logger.warning(f"🚫 [INTERVIEW_COMPLETED] Multi-tenancy validation failed: {error_message}")
            raise HTTPException(status_code=403, detail=error_message)
        
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
                from app.services.llm import llm_service
                
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
            activity_service = get_activity_service()
            
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
        
        try:
            from app.models.automation import AutomationExecutionLog
            
            audit_log = AutomationExecutionLog(
                company_id=request.company_id,
                trigger_event="interview_completed",
                trigger_data={
                    "candidate_id": request.candidate_id,
                    "vacancy_id": request.vacancy_id,
                    "interview_id": request.interview_id,
                    "interview_type": request.interview_type,
                    "has_notes": bool(request.interviewer_notes),
                    "has_transcript": bool(request.transcript),
                    "competency_count": len(request.competency_ratings) if request.competency_ratings else 0
                },
                candidate_id=request.candidate_id,
                vacancy_id=request.vacancy_id,
                action_executed="generate_parecer",
                action_result={
                    "parecer_id": parecer_id,
                    "recommendation": recommendation,
                    "average_rating": average_rating,
                    "suggested_next_stage": suggested_next_stage,
                    "confidence": confidence,
                    "notification_created": notification_created
                },
                status="success" if parecer_id else "partial",
                execution_time_ms="0"
            )
            db.add(audit_log)
            logger.info("📝 [INTERVIEW_COMPLETED] Audit log created")
        except Exception as e:
            logger.error(f"❌ [INTERVIEW_COMPLETED] Failed to create audit log: {e}")
        
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
            detail=f"Erro ao processar entrevista concluída: {str(e)}"
        )


@router.post("/handle-trigger/candidate-inactive", response_model=CandidateInactiveResponse)
async def handle_candidate_inactive(
    request: CandidateInactiveRequest,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
    """
    Handle candidate_inactive trigger.
    
    Sends follow-up communication and notifies recruiter when a candidate
    has been inactive for 7+ days (no status change, no communication).
    
    This endpoint performs:
    1. Validate multi-tenancy
    2. Determine appropriate follow-up action based on current stage
    3. Send follow-up email/WhatsApp to candidate
    4. Create notification for recruiter about inactive candidate
    5. Log audit entry
    
    Args:
        request: CandidateInactiveRequest with candidate and inactivity details
        db: Database session
    
    Returns:
        Result with follow_up_sent, follow_up_type, and notification status
    """
    try:
        logger.info(
            f"⏰ [CANDIDATE_INACTIVE] Processing trigger for "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}, "
            f"days_inactive={request.days_inactive}, stage={request.current_stage}"
        )
        
        # Step 0: Multi-tenancy validation
        is_valid, error_message = await validate_multi_tenancy(
            db=db,
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id
        )
        if not is_valid:
            logger.warning(f"🚫 [CANDIDATE_INACTIVE] Multi-tenancy validation failed: {error_message}")
            raise HTTPException(status_code=403, detail=error_message)
        
        # Result tracking
        email_sent = False
        whatsapp_sent = False
        notification_created = False
        follow_up_type = "general"
        email_error = None
        whatsapp_error = None
        communication_failures = []
        
        # Get candidate and job info
        candidate_name = request.candidate_name or "Candidato"
        candidate_email = request.candidate_email
        candidate_phone = request.candidate_phone
        job_title = request.job_title or "Vaga"
        current_stage = request.current_stage or "general"
        days_inactive = request.days_inactive
        
        # Step 1: Determine follow-up type based on current stage
        stage_lower = current_stage.lower() if current_stage else ""
        if "triagem" in stage_lower:
            follow_up_type = "screening_reminder"
        elif "entrevista" in stage_lower:
            follow_up_type = "interview_availability"
        elif "proposta" in stage_lower:
            follow_up_type = "proposal_reminder"
        else:
            follow_up_type = "general_follow_up"
        
        logger.info(f"📋 [CANDIDATE_INACTIVE] Follow-up type determined: {follow_up_type}")
        
        # Step 2: Send follow-up email to candidate
        if candidate_email:
            try:
                from app.templates.communication_templates import EmailTemplates
                email_service = get_email_service()
                
                email_content = EmailTemplates.follow_up(
                    candidate_name=candidate_name,
                    job_title=job_title,
                    days_inactive=days_inactive,
                    current_stage=current_stage,
                    follow_up_type=follow_up_type
                )
                
                send_result = await email_service.send_email(
                    to_email=candidate_email,
                    subject=email_content["subject"],
                    body_html=email_content["body"].replace("\n", "<br>"),
                    body_text=email_content["body"],
                    company_id=request.company_id
                )
                
                email_sent = send_result.get("success", False)
                if not email_sent:
                    email_error = send_result.get("error", "Unknown email send failure")
                    communication_failures.append({"channel": "email", "error": email_error})
                logger.info(f"📧 [CANDIDATE_INACTIVE] Email sent (ok=: {email_sent}")
            except Exception as e:
                email_error = str(e)
                communication_failures.append({"channel": "email", "error": email_error})
                logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to send email: {e}")
        else:
            logger.warning("⚠️ [CANDIDATE_INACTIVE] No candidate email provided, skipping email")
        
        # Step 3: Send WhatsApp follow-up to candidate
        if candidate_phone:
            try:
                from app.templates.communication_templates import WhatsAppTemplates
                whatsapp_service = get_whatsapp_service()
                
                whatsapp_message = WhatsAppTemplates.follow_up(
                    candidate_name=candidate_name,
                    job_title=job_title,
                    days_inactive=days_inactive,
                    current_stage=current_stage
                )
                
                send_result = await whatsapp_service.send_message(
                    to_phone=candidate_phone,
                    message=whatsapp_message,
                    metadata={
                        "candidate_id": request.candidate_id,
                        "vacancy_id": request.vacancy_id,
                        "company_id": request.company_id,
                        "type": "candidate_inactive_follow_up",
                        "days_inactive": days_inactive
                    }
                )
                
                whatsapp_sent = send_result.success
                if not whatsapp_sent:
                    whatsapp_error = getattr(send_result, 'error', None) or "Unknown WhatsApp send failure"
                    communication_failures.append({"channel": "whatsapp", "error": whatsapp_error})
                logger.info(f"💬 [CANDIDATE_INACTIVE] WhatsApp sent to {candidate_phone}: {whatsapp_sent}")
            except Exception as e:
                whatsapp_error = str(e)
                communication_failures.append({"channel": "whatsapp", "error": whatsapp_error})
                logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to send WhatsApp: {e}")
        else:
            logger.info("ℹ️ [CANDIDATE_INACTIVE] No candidate phone provided, skipping WhatsApp")
        
        # Step 4a: Notify recruiter if communications failed (error handling)
        if communication_failures and (candidate_email or candidate_phone):
            try:
                activity_service = get_activity_service()
                failure_details = "; ".join([f"{f['channel']}: {f['error']}" for f in communication_failures])
                await activity_svc.create_activity(
                    activity_type="follow_up_failed",
                    title=f"Falha no Follow-up - {candidate_name}",
                    description=(
                        f"Não foi possível enviar follow-up para o candidato {candidate_name} "
                        f"na posição de {job_title}. Detalhes: {failure_details}. "
                        f"Por favor, entre em contato manualmente."
                    ),
                    actor_id="system",
                    actor_name="LIA Automation",
                    actor_type="system",
                    target_id=request.candidate_id,
                    target_type="candidate",
                    extra_data={
                        "vacancy_id": request.vacancy_id,
                        "company_id": request.company_id,
                        "days_inactive": days_inactive,
                        "failures": communication_failures,
                        "follow_up_type": follow_up_type
                    },
                    category="error"
                )
                logger.info("🔔 [CANDIDATE_INACTIVE] Failure notification created for recruiter")
            except Exception as e:
                logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to create failure notification: {e}")
        
        # Step 4b: Create recruiter notification
        try:
            activity_service = get_activity_service()
            
            await activity_svc.create_activity(
                activity_type="candidate_inactive",
                title=f"Candidato Inativo - {candidate_name}",
                description=(
                    f"O candidato {candidate_name} está sem atividade há {days_inactive} dias "
                    f"na posição de {job_title}. Etapa atual: {current_stage}. "
                    f"Follow-up enviado: {'Sim' if (email_sent or whatsapp_sent) else 'Não'}."
                ),
                actor_id="system",
                actor_name="LIA Automation",
                actor_type="system",
                target_id=request.candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    "days_inactive": days_inactive,
                    "current_stage": current_stage,
                    "last_activity_date": request.last_activity_date.isoformat() if request.last_activity_date else None,
                    "follow_up_type": follow_up_type,
                    "email_sent": email_sent,
                    "whatsapp_sent": whatsapp_sent
                },
                category="follow_up"
            )
            notification_created = True
            logger.info("🔔 [CANDIDATE_INACTIVE] Recruiter notification created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to create notification: {e}")
        
        # Step 5: Log audit entries (both legacy and centralized)
        try:
            from app.models.automation import AutomationExecutionLog
            
            # Legacy audit log for backwards compatibility
            audit_log = AutomationExecutionLog(
                company_id=request.company_id,
                trigger_event="candidate_inactive",
                trigger_data={
                    "candidate_id": request.candidate_id,
                    "vacancy_id": request.vacancy_id,
                    "days_inactive": days_inactive,
                    "current_stage": current_stage,
                    "last_activity_date": request.last_activity_date.isoformat() if request.last_activity_date else None
                },
                candidate_id=request.candidate_id,
                vacancy_id=request.vacancy_id,
                action_executed="send_inactive_follow_up",
                action_result={
                    "email_sent": email_sent,
                    "whatsapp_sent": whatsapp_sent,
                    "notification_created": notification_created,
                    "follow_up_type": follow_up_type,
                    "communication_failures": communication_failures
                },
                status="success" if (email_sent or whatsapp_sent) else ("partial" if notification_created else "no_action"),
                execution_time_ms="0"
            )
            db.add(audit_log)
            logger.info("📝 [CANDIDATE_INACTIVE] Legacy audit log created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to create legacy audit log: {e}")
        
        # Centralized audit logging via audit_service
        try:
            await audit_svc.log_decision(
                company_id=request.company_id,
                agent_name="proactive_agent",
                decision_type="candidate_follow_up",
                action="send_follow_up",
                decision=follow_up_type,
                score=None,
                confidence=0.8,
                reasoning=[
                    f"Candidate inactive for {days_inactive} days",
                    f"Current stage: {current_stage}",
                    f"Email sent: {email_sent}",
                    f"WhatsApp sent: {whatsapp_sent}"
                ] + ([f"Communication failures: {len(communication_failures)}"] if communication_failures else []),
                criteria_used=["days_inactive", "current_stage"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id
            )
            logger.info("📝 [CANDIDATE_INACTIVE] Centralized audit log created via audit_service")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_INACTIVE] Failed to create centralized audit log: {e}")
        
        # Determine overall success status
        has_communication_target = bool(candidate_email or candidate_phone)
        communication_attempted = has_communication_target
        communication_succeeded = email_sent or whatsapp_sent
        partial_success = communication_attempted and not communication_succeeded and notification_created
        
        # Step 6: Build response
        response_data = {
            "success": communication_succeeded or not has_communication_target,
            "partial_success": partial_success,
            "trigger": "candidate_inactive",
            "days_inactive": days_inactive,
            "follow_up_sent": communication_succeeded,
            "follow_up_type": follow_up_type,
            "email_sent": email_sent,
            "whatsapp_sent": whatsapp_sent,
            "notification_created": notification_created,
            "communication_failures": communication_failures if communication_failures else None,
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "current_stage": current_stage,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            f"✅ [CANDIDATE_INACTIVE] Processing complete: "
            f"email={email_sent}, whatsapp={whatsapp_sent}, "
            f"notification={notification_created}, type={follow_up_type}"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_INACTIVE] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar candidato inativo: {str(e)}"
        )


@router.post("/handle-trigger/candidate-no-show", response_model=CandidateNoShowResponse)
async def handle_candidate_no_show(
    request: CandidateNoShowRequest,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
    """
    Handle candidate_no_show trigger.
    
    Offers rescheduling or suggests rejection based on no-show count.
    
    Logic:
    - If first no-show (no_show_count == 1):
      - Send email/WhatsApp asking to reschedule
      - Create AI suggestion to reschedule
      - Notify recruiter
    - If second no-show (no_show_count >= 2):
      - Suggest rejection with high confidence
      - Send final communication
      - Notify recruiter with recommendation to reject
    
    Args:
        request: CandidateNoShowRequest with no-show details
        db: Database session
    
    Returns:
        Result with action taken, communications sent, and suggestions created
    """
    try:
        logger.info(
            f"🚫 [CANDIDATE_NO_SHOW] Processing no-show: "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}, "
            f"interview={request.interview_id}, no_show_count={request.no_show_count}"
        )
        
        # Step 0: Multi-tenancy validation
        is_valid, error_message = await validate_multi_tenancy(
            db=db,
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id
        )
        if not is_valid:
            logger.warning(f"🚫 [CANDIDATE_NO_SHOW] Multi-tenancy validation failed: {error_message}")
            raise HTTPException(status_code=403, detail=error_message)
        
        # Initialize response tracking
        email_sent = False
        whatsapp_sent = False
        notification_created = False
        suggestion_created = False
        
        candidate_name = request.candidate_name or "Candidato"
        candidate_email = request.candidate_email
        candidate_phone = request.candidate_phone
        job_title = request.job_title or "Posição"
        interviewer_name = request.interviewer_name or "Equipe"
        no_show_count = request.no_show_count
        
        # Determine action based on no-show count
        if no_show_count == 1:
            action_taken = "reschedule_offered"
            recommendation = "Primeira ausência - oferecendo reagendamento"
            confidence_score = 0.7
        else:
            action_taken = "rejection_suggested"
            recommendation = f"Múltiplas ausências ({no_show_count}) - recomendamos rejeitar candidato"
            confidence_score = 0.9
        
        logger.info(f"📋 [CANDIDATE_NO_SHOW] Action determined: {action_taken}")
        
        # Step 1: Send communication to candidate
        from app.templates.communication_templates import EmailTemplates, WhatsAppTemplates
        
        if no_show_count == 1:
            # First no-show: Send polite reschedule offer
            if candidate_email:
                try:
                    email_service = get_email_service()
                    email_content = EmailTemplates.no_show_first(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        interview_datetime=request.interview_datetime,
                        interviewer_name=interviewer_name,
                        reschedule_link="",
                        company_name=None
                    )
                    
                    send_result = await email_service.send_email(
                        to_email=candidate_email,
                        subject=email_content["subject"],
                        body_html=email_content["body"].replace("\n", "<br>"),
                        body_text=email_content["body"],
                        company_id=request.company_id
                    )
                    
                    email_sent = send_result.get("success", False)
                    logger.info(f"📧 [CANDIDATE_NO_SHOW] Reschedule email sent ok={email_sent}")
                except Exception as e:
                    logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to send reschedule email: {e}")
            
            if candidate_phone:
                try:
                    whatsapp_service = get_whatsapp_service()
                    whatsapp_message = WhatsAppTemplates.no_show_first(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        interview_datetime=request.interview_datetime,
                        reschedule_link=""
                    )
                    
                    send_result = await whatsapp_service.send_message(
                        to_phone=candidate_phone,
                        message=whatsapp_message,
                        metadata={
                            "candidate_id": request.candidate_id,
                            "vacancy_id": request.vacancy_id,
                            "company_id": request.company_id,
                            "type": "no_show_reschedule",
                            "interview_id": request.interview_id
                        }
                    )
                    
                    whatsapp_sent = send_result.success
                    logger.info(f"💬 [CANDIDATE_NO_SHOW] Reschedule WhatsApp sent to {candidate_phone}: {whatsapp_sent}")
                except Exception as e:
                    logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to send reschedule WhatsApp: {e}")
        else:
            # Multiple no-shows: Send final notice
            if candidate_email:
                try:
                    email_service = get_email_service()
                    email_content = EmailTemplates.no_show_final(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        no_show_count=no_show_count,
                        company_name=None
                    )
                    
                    send_result = await email_service.send_email(
                        to_email=candidate_email,
                        subject=email_content["subject"],
                        body_html=email_content["body"].replace("\n", "<br>"),
                        body_text=email_content["body"],
                        company_id=request.company_id
                    )
                    
                    email_sent = send_result.get("success", False)
                    logger.info(f"📧 [CANDIDATE_NO_SHOW] Final notice email sent ok={email_sent}")
                except Exception as e:
                    logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to send final notice email: {e}")
            
            if candidate_phone:
                try:
                    whatsapp_service = get_whatsapp_service()
                    whatsapp_message = WhatsAppTemplates.no_show_final(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        no_show_count=no_show_count
                    )
                    
                    send_result = await whatsapp_service.send_message(
                        to_phone=candidate_phone,
                        message=whatsapp_message,
                        metadata={
                            "candidate_id": request.candidate_id,
                            "vacancy_id": request.vacancy_id,
                            "company_id": request.company_id,
                            "type": "no_show_final",
                            "interview_id": request.interview_id
                        }
                    )
                    
                    whatsapp_sent = send_result.success
                    logger.info(f"💬 [CANDIDATE_NO_SHOW] Final notice WhatsApp sent to {candidate_phone}: {whatsapp_sent}")
                except Exception as e:
                    logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to send final notice WhatsApp: {e}")
        
        # Step 2: Create AI suggestion
        try:
            from app.models.automation import AISuggestion
            
            if no_show_count == 1:
                suggestion_title = f"Reagendar entrevista - {candidate_name}"
                suggestion_description = (
                    f"O candidato {candidate_name} não compareceu à entrevista de {request.interview_type} "
                    f"agendada para {request.interview_datetime.strftime('%d/%m/%Y às %H:%M')}. "
                    f"Recomendamos oferecer reagendamento."
                )
                suggestion_action = "reschedule_interview"
            else:
                suggestion_title = f"Rejeitar candidato por ausência - {candidate_name}"
                suggestion_description = (
                    f"O candidato {candidate_name} não compareceu a {no_show_count} entrevistas agendadas "
                    f"para a posição de {job_title}. Recomendamos rejeição do candidato."
                )
                suggestion_action = "reject_candidate"
            
            suggestion = AISuggestion(
                company_id=request.company_id,
                candidate_id=request.candidate_id,
                vacancy_id=request.vacancy_id,
                suggestion_type="no_show_action",
                action_type=suggestion_action,
                action_config={
                    "interview_id": request.interview_id,
                    "interview_type": request.interview_type,
                    "no_show_count": no_show_count,
                    "interview_datetime": request.interview_datetime.isoformat()
                },
                title=suggestion_title,
                description=suggestion_description,
                confidence_score=str(confidence_score),
                reasoning=recommendation,
                status="pending",
                extra_data={
                    "candidate_name": candidate_name,
                    "job_title": job_title,
                    "interviewer_name": interviewer_name
                }
            )
            db.add(suggestion)
            await db.flush()
            suggestion_created = True
            logger.info(f"💡 [CANDIDATE_NO_SHOW] AI suggestion created: {suggestion.id}")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to create AI suggestion: {e}")
        
        # Step 3: Create recruiter notification
        try:
            activity_service = get_activity_service()
            
            await activity_svc.create_activity(
                activity_type="candidate_no_show",
                title=f"No-Show: {candidate_name} - {job_title}",
                description=(
                    f"O candidato {candidate_name} não compareceu à entrevista de {request.interview_type} "
                    f"({no_show_count}ª ausência). {recommendation}"
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
                    "interview_datetime": request.interview_datetime.isoformat(),
                    "no_show_count": no_show_count,
                    "action_taken": action_taken,
                    "email_sent": email_sent,
                    "whatsapp_sent": whatsapp_sent
                },
                category="no_show"
            )
            notification_created = True
            logger.info("🔔 [CANDIDATE_NO_SHOW] Recruiter notification created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to create notification: {e}")
        
        # Step 4: Log audit entries (both legacy and centralized)
        try:
            from app.models.automation import AutomationExecutionLog
            
            # Legacy audit log for backwards compatibility
            audit_log = AutomationExecutionLog(
                company_id=request.company_id,
                trigger_event="candidate_no_show",
                trigger_data={
                    "candidate_id": request.candidate_id,
                    "vacancy_id": request.vacancy_id,
                    "interview_id": request.interview_id,
                    "interview_datetime": request.interview_datetime.isoformat(),
                    "interview_type": request.interview_type,
                    "no_show_count": no_show_count
                },
                candidate_id=request.candidate_id,
                vacancy_id=request.vacancy_id,
                action_executed=action_taken,
                action_result={
                    "email_sent": email_sent,
                    "whatsapp_sent": whatsapp_sent,
                    "notification_created": notification_created,
                    "suggestion_created": suggestion_created,
                    "recommendation": recommendation,
                    "confidence_score": confidence_score
                },
                status="success" if (email_sent or whatsapp_sent or notification_created or suggestion_created) else "no_action",
                execution_time_ms="0"
            )
            db.add(audit_log)
            logger.info("📝 [CANDIDATE_NO_SHOW] Legacy audit log created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to create legacy audit log: {e}")
        
        # Centralized audit logging via audit_service
        try:
            await audit_svc.log_decision(
                company_id=request.company_id,
                agent_name="scheduling_agent",
                decision_type="no_show_handling",
                action=action_taken,
                decision=recommendation,
                score=None,
                confidence=confidence_score,
                reasoning=[
                    f"Candidate no-show count: {no_show_count}",
                    f"Action taken: {action_taken}",
                    f"Interview type: {request.interview_type}",
                    f"Communication sent: {email_sent or whatsapp_sent}",
                    f"Suggestion created: {suggestion_created}"
                ],
                criteria_used=["no_show_count", "interview_type", "action_policy"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id
            )
            logger.info("📝 [CANDIDATE_NO_SHOW] Centralized audit log created via audit_service")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to create centralized audit log: {e}")
        
        # Step 5: Build response
        response_data = {
            "success": True,
            "trigger": "candidate_no_show",
            "no_show_count": no_show_count,
            "action_taken": action_taken,
            "communication_sent": email_sent or whatsapp_sent,
            "suggestion_created": suggestion_created,
            "notification_created": notification_created,
            "details": {
                "email_sent": email_sent,
                "whatsapp_sent": whatsapp_sent,
                "recommendation": recommendation,
                "confidence_score": confidence_score
            },
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "interview_id": request.interview_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            f"✅ [CANDIDATE_NO_SHOW] Processing complete: "
            f"action={action_taken}, email={email_sent}, whatsapp={whatsapp_sent}, "
            f"suggestion={suggestion_created}, notification={notification_created}"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_NO_SHOW] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar no-show do candidato: {str(e)}"
        )


async def _execute_outbound_ats_sync(ats_sync_service, request, ats_stage: str) -> tuple:
    """Execute outbound ATS sync (LIA -> ATS). Returns (sync_status, ats_response, error)."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncTrigger
    sync_data = {
        "status": ats_stage, "previous_status": request.previous_stage,
        "candidate_name": request.candidate_name, "candidate_email": request.candidate_email,
        "job_title": request.job_title,
    }
    try:
        result = await ats_sync_service.trigger_sync(
            trigger=ATSSyncTrigger.STATUS_CHANGE, source_agent="automation",
            ats_type=request.ats_platform,
            candidate_id=request.ats_candidate_id or request.candidate_id,
            job_id=request.ats_vacancy_id or request.vacancy_id, data=sync_data
        )
        if result.get("success"):
            return "completed", result, None
        return "failed", result, result.get("message", "Sync failed without error message")
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Exception during outbound sync: {e}")
        return "failed", None, str(e)


async def _execute_inbound_ats_sync(ats_sync_service, request) -> tuple:
    """Execute inbound ATS sync (ATS -> LIA). Returns (sync_status, ats_response, error)."""
    try:
        result = await ats_sync_service.pull_candidate(
            ats_type=request.ats_platform,
            ats_candidate_id=request.ats_candidate_id or request.candidate_id,
            source_agent="automation"
        )
        if result.get("success"):
            return "completed", result, None
        return "failed", result, result.get("message", "Pull failed")
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Exception during inbound sync: {e}")
        return "failed", None, str(e)


async def _notify_ats_sync_failure(activity_svc, request, error: str) -> bool:
    """Notify recruiter of ATS sync failure. Returns True if notification created."""
    try:
        candidate_name = request.candidate_name or request.candidate_id
        await activity_svc.create_activity(
            activity_type="ats_sync_failed",
            title=f"Falha na Sincronização com {request.ats_platform.upper()}",
            description=(
                f"Não foi possível sincronizar a mudança de etapa do candidato "
                f"{candidate_name} de '{request.previous_stage or 'N/A'}' para '{request.new_stage}'. "
                f"Erro: {error}"
            ),
            actor_id="system", actor_name="LIA Automation", actor_type="system",
            target_id=request.candidate_id, target_type="candidate",
            extra_data={
                "vacancy_id": request.vacancy_id, "company_id": request.company_id,
                "ats_platform": request.ats_platform, "ats_candidate_id": request.ats_candidate_id,
                "new_stage": request.new_stage, "previous_stage": request.previous_stage, "error": error
            },
            category="ats_sync"
        )
        return True
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create failure notification: {e}")
        return False


async def _log_ats_sync_audit(db, audit_svc, request, ats_stage: str, is_mapped: bool, sync_status: str, ats_response, error, notification_created: bool) -> None:
    """Log automation execution log and centralized audit for ATS sync."""
    try:
        from app.models.automation import AutomationExecutionLog
        db.add(AutomationExecutionLog(
            company_id=request.company_id, trigger_event="ats_sync",
            trigger_data={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "ats_platform": request.ats_platform, "ats_candidate_id": request.ats_candidate_id,
                "ats_vacancy_id": request.ats_vacancy_id, "new_stage": request.new_stage,
                "previous_stage": request.previous_stage, "sync_direction": request.sync_direction,
                "ats_stage_mapped": ats_stage, "is_stage_mapped": is_mapped
            },
            candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            action_executed=f"ats_sync_{request.sync_direction}_{request.ats_platform}",
            action_result={
                "sync_status": sync_status, "ats_response": ats_response,
                "error": error, "notification_created": notification_created
            },
            status="success" if sync_status == "completed" else "failed",
            execution_time_ms="0"
        ))
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create execution log: {e}")

    try:
        reasoning_items = [
            f"ATS platform: {request.ats_platform}", f"Sync direction: {request.sync_direction}",
            f"Stage transition: {request.previous_stage or 'N/A'} → {request.new_stage}",
            f"Mapped ATS stage: {ats_stage} (explicit_mapping={is_mapped})",
            f"Sync status: {sync_status}"
        ]
        if error:
            reasoning_items.append(f"Error: {error}")
        await audit_svc.log_decision(
            company_id=request.company_id, agent_name="ats_integrator",
            decision_type="ats_sync", action=f"sync_{request.sync_direction}",
            decision=sync_status, score=None,
            confidence=1.0 if sync_status == "completed" else 0.0,
            reasoning=reasoning_items, criteria_used=["ats_platform", "sync_direction", "stage_mapping"],
            candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
            human_review_required=(sync_status == "failed")
        )
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create centralized audit log: {e}")


def _build_ats_sync_response(request, ats_stage: str, sync_status: str, ats_response, error) -> dict:
    """Build the response dict for ats_sync trigger."""
    return {
        "success": sync_status == "completed",
        "trigger": "ats_sync",
        "ats_platform": request.ats_platform,
        "sync_status": sync_status,
        "sync_direction": request.sync_direction,
        "stage_mapping": {"lia_stage": request.new_stage, "ats_stage": ats_stage},
        "ats_response": ats_response,
        "error": error,
        "metadata": {
            "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
            "ats_candidate_id": request.ats_candidate_id,
            "ats_vacancy_id": request.ats_vacancy_id,
            "processed_at": datetime.utcnow().isoformat()
        }
    }


async def _run_ats_sync_direction(ats_sync_service, request, ats_stage: str) -> tuple:
    """Dispatch sync by direction. Returns (sync_status, ats_response, error)."""
    if request.sync_direction == "outbound":
        return await _execute_outbound_ats_sync(ats_sync_service, request, ats_stage)
    if request.sync_direction == "inbound":
        return await _execute_inbound_ats_sync(ats_sync_service, request)
    return "pending", None, None


async def _process_ats_sync(request, db, audit_svc, activity_svc) -> dict:
    """Orchestrate ats_sync trigger: validate, map stage, sync, notify on failure, audit."""
    logger.info(
        f"🔄 [ATS_SYNC] Starting: platform={request.ats_platform}, "
        f"candidate={request.candidate_id}, stage={request.previous_stage} → {request.new_stage}"
    )

    is_valid, error_msg = await validate_multi_tenancy(
        db, request.candidate_id, request.vacancy_id, request.company_id
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_msg)

    ats_stage, is_mapped = map_lia_stage_to_ats(request.new_stage, request.ats_platform, request.company_id)
    if not is_mapped:
        await notify_unmapped_stage(
            company_id=request.company_id, lia_stage=request.new_stage,
            ats_platform=request.ats_platform, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id
        )

    sync_status, ats_response, error = await _run_ats_sync_direction(
        get_ats_sync_service(), request, ats_stage
    )

    notification_created = False
    if sync_status == "failed":
        notification_created = await _notify_ats_sync_failure(activity_svc, request, error or "Unknown error")

    await _log_ats_sync_audit(db, audit_svc, request, ats_stage, is_mapped, sync_status, ats_response, error, notification_created)

    logger.info(f"{'✅' if sync_status == 'completed' else '⚠️'} [ATS_SYNC] Done: status={sync_status}")
    return _build_ats_sync_response(request, ats_stage, sync_status, ats_response, error)


@router.post("/handle-trigger/ats-sync", response_model=ATSSyncResponse)
async def handle_ats_sync(request: ATSSyncRequest, db: AsyncSession = Depends(get_db), audit_svc: AuditService = Depends(get_audit_service), activity_svc: ActivityService = Depends(get_activity_service_canonical)):
    """Handle ats_sync trigger: sync candidate stage with external ATS platform."""
    try:
        return await _process_ats_sync(request, db, audit_svc, activity_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar com ATS: {str(e)}")


# ============== OFFER_SENT TRIGGER ==============

@router.post("/handle-trigger/offer-sent", response_model=OfferSentResponse)
async def handle_offer_sent(
    request: OfferSentPayload,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
    """
    Handle when an offer is sent to a candidate.
    
    Actions:
    1. Send offer email to candidate
    2. Notify recruiter about offer sent
    3. Schedule follow-up reminder if response_deadline provided
    4. Sync status to ATS
    5. Log activity
    """
    try:
        logger.info(
            f"📨 [OFFER_SENT] Processing offer sent: "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}"
        )
        
        is_valid, error_msg = await validate_multi_tenancy(
            db, request.candidate_id, request.vacancy_id, request.company_id
        )
        if not is_valid:
            logger.warning(f"⚠️ [OFFER_SENT] Multi-tenancy validation failed: {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)
        
        actions_taken = []
        email_sent = False
        notification_created = False
        ats_synced = False
        
        try:
            email_service = get_email_service()
            from app.templates.communication_templates import EmailTemplates
            
            template = EmailTemplates.offer_sent(
                candidate_name=request.candidate_name or "Candidato",
                job_title=request.job_title or "a posição",
                salary_offered=request.salary_offered,
                start_date=request.start_date,
                response_deadline=request.response_deadline,
                offer_details=request.offer_details
            )
            
            if request.candidate_email:
                await email_service.send_email(
                    to_email=request.candidate_email,
                    subject=template["subject"],
                    body=template["body"]
                )
                email_sent = True
                actions_taken.append("offer_email_sent")
                logger.info("✅ [OFFER_SENT] Offer email sent")
        except Exception as e:
            logger.error(f"❌ [OFFER_SENT] Failed to send offer email: {e}")
        
        try:
            await activity_svc.create_activity(
                activity_type="offer_sent",
                title=f"Proposta enviada para {request.candidate_name or 'candidato'}",
                description=(
                    f"Proposta para {request.job_title or 'a posição'} enviada. "
                    f"{'Salário: R$ ' + str(request.salary_offered) if request.salary_offered else ''} "
                    f"{'Data de início: ' + request.start_date if request.start_date else ''}"
                ),
                actor_id="system",
                actor_name="LIA Automation",
                actor_type="system",
                target_id=request.candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    "salary_offered": request.salary_offered,
                    "start_date": request.start_date,
                    "response_deadline": request.response_deadline
                },
                category="offer"
            )
            notification_created = True
            actions_taken.append("recruiter_notified")
            logger.info("✅ [OFFER_SENT] Notification created for recruiter")
        except Exception as e:
            logger.error(f"❌ [OFFER_SENT] Failed to create notification: {e}")
        
        try:
            ats_sync_service = get_ats_sync_service()
            from app.domains.ats_integration.services.ats_sync_service import ATSSyncTrigger
            
            sync_result = await ats_sync_service.trigger_sync(
                trigger=ATSSyncTrigger.STATUS_CHANGE,
                source_agent="automation",
                ats_type="gupy",
                candidate_id=request.candidate_id,
                job_id=request.vacancy_id,
                data={"status": "offer_sent"}
            )
            if sync_result.get("success"):
                ats_synced = True
                actions_taken.append("ats_synced")
                logger.info("✅ [OFFER_SENT] ATS synced successfully")
        except Exception as e:
            logger.error(f"❌ [OFFER_SENT] Failed to sync ATS: {e}")
        
        try:
            await audit_svc.log_decision(
                company_id=request.company_id,
                agent_name="automation",
                decision_type="offer_sent",
                action="send_offer",
                decision="offer_sent",
                score=None,
                confidence=1.0,
                reasoning=[
                    f"Offer sent to candidate {request.candidate_name or request.candidate_id}",
                    f"Salary: {request.salary_offered or 'Not specified'}",
                    f"Start date: {request.start_date or 'Not specified'}",
                    f"Response deadline: {request.response_deadline or 'Not specified'}"
                ],
                criteria_used=["salary", "start_date", "response_deadline"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id,
                human_review_required=False
            )
            logger.info("📝 [OFFER_SENT] Audit log created")
        except Exception as e:
            logger.error(f"❌ [OFFER_SENT] Failed to create audit log: {e}")
        
        response_data = {
            "success": True,
            "trigger": "offer_sent",
            "actions": actions_taken,
            "details": {
                "email_sent": email_sent,
                "notification_created": notification_created,
                "ats_synced": ats_synced
            },
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            f"✅ [OFFER_SENT] Processing complete: actions={actions_taken}"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [OFFER_SENT] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar envio de proposta: {str(e)}"
        )


# ============== CANDIDATE_HIRED TRIGGER ==============

@router.post("/handle-trigger/candidate-hired", response_model=CandidateHiredResponse)
async def handle_candidate_hired(
    request: CandidateHiredPayload,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
    """
    Handle when a candidate is hired.
    
    Actions:
    1. Send welcome/onboarding email
    2. Update candidate stage to hired
    3. Sync to ATS as hired
    4. Notify relevant stakeholders
    5. Log activity
    """
    try:
        logger.info(
            f"🎉 [CANDIDATE_HIRED] Processing hired event: "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}"
        )
        
        is_valid, error_msg = await validate_multi_tenancy(
            db, request.candidate_id, request.vacancy_id, request.company_id
        )
        if not is_valid:
            logger.warning(f"⚠️ [CANDIDATE_HIRED] Multi-tenancy validation failed: {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)
        
        actions_taken = []
        email_sent = False
        stage_updated = False
        notification_created = False
        ats_synced = False
        
        try:
            email_service = get_email_service()
            from app.templates.communication_templates import EmailTemplates
            
            template = EmailTemplates.candidate_hired_welcome(
                candidate_name=request.candidate_name or "Candidato",
                job_title=request.job_title or "a posição",
                hire_date=request.hire_date,
                department=request.department
            )
            
            if request.candidate_email:
                await email_service.send_email(
                    to_email=request.candidate_email,
                    subject=template["subject"],
                    body=template["body"]
                )
                email_sent = True
                actions_taken.append("welcome_email_sent")
                logger.info("✅ [CANDIDATE_HIRED] Welcome email sent")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to send welcome email: {e}")
        
        try:
            from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService
            pipeline_service = PipelineStageService()
            
            from sqlalchemy import and_, select

            from app.models.candidate import VacancyCandidate
            
            vc_result = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.candidate_id == request.candidate_id,
                        VacancyCandidate.vacancy_id == request.vacancy_id
                    )
                )
            )
            vacancy_candidate = vc_result.scalar_one_or_none()
            
            if vacancy_candidate:
                await pipeline_service.transition_candidate(
                    vacancy_candidate_id=str(vacancy_candidate.id),
                    to_stage="Contratado",
                    to_sub_status="contratado",
                    triggered_by="automation",
                    source_agent="offer_management",
                    reason="Candidate hired",
                    db=db
                )
                stage_updated = True
                actions_taken.append("stage_updated")
                logger.info("✅ [CANDIDATE_HIRED] Stage updated to Contratado")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to update stage: {e}")
        
        try:
            ats_sync_service = get_ats_sync_service()
            from app.domains.ats_integration.services.ats_sync_service import ATSSyncTrigger
            
            sync_result = await ats_sync_service.trigger_sync(
                trigger=ATSSyncTrigger.STATUS_CHANGE,
                source_agent="automation",
                ats_type="gupy",
                candidate_id=request.candidate_id,
                job_id=request.vacancy_id,
                data={"status": "hired"}
            )
            if sync_result.get("success"):
                ats_synced = True
                actions_taken.append("ats_synced")
                logger.info("✅ [CANDIDATE_HIRED] ATS synced successfully")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to sync ATS: {e}")
        
        try:
            await activity_svc.create_activity(
                activity_type="candidate_hired",
                title=f"🎉 {request.candidate_name or 'Candidato'} contratado!",
                description=(
                    f"Candidato contratado para {request.job_title or 'a posição'}. "
                    f"{'Data de início: ' + request.hire_date if request.hire_date else ''} "
                    f"{'Departamento: ' + request.department if request.department else ''}"
                ),
                actor_id="system",
                actor_name="LIA Automation",
                actor_type="system",
                target_id=request.candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    "hire_date": request.hire_date,
                    "department": request.department,
                    "final_salary": request.final_salary
                },
                category="hire"
            )
            notification_created = True
            actions_taken.append("stakeholders_notified")
            logger.info("✅ [CANDIDATE_HIRED] Notification created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to create notification: {e}")
        
        try:
            await audit_svc.log_decision(
                company_id=request.company_id,
                agent_name="automation",
                decision_type="candidate_hired",
                action="hire_candidate",
                decision="hired",
                score=None,
                confidence=1.0,
                reasoning=[
                    f"Candidate {request.candidate_name or request.candidate_id} hired",
                    f"Hire date: {request.hire_date or 'Not specified'}",
                    f"Department: {request.department or 'Not specified'}",
                    f"Final salary: {request.final_salary or 'Not specified'}"
                ],
                criteria_used=["hire_date", "department", "final_salary"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id,
                human_review_required=False
            )
            logger.info("📝 [CANDIDATE_HIRED] Audit log created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to create audit log: {e}")
        
        response_data = {
            "success": True,
            "trigger": "candidate_hired",
            "actions": actions_taken,
            "details": {
                "email_sent": email_sent,
                "stage_updated": stage_updated,
                "notification_created": notification_created,
                "ats_synced": ats_synced
            },
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            f"✅ [CANDIDATE_HIRED] Processing complete: actions={actions_taken}"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_HIRED] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar contratação: {str(e)}"
        )


# ============== CANDIDATE_REJECTED TRIGGER ==============

@router.post("/handle-trigger/candidate-rejected", response_model=CandidateRejectedResponse)
async def handle_candidate_rejected(
    request: CandidateRejectedPayload,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
):
    """
    Handle when a candidate is rejected.
    
    Actions:
    1. Send rejection email with feedback (if enabled)
    2. Add to talent pool for future opportunities (if enabled)
    3. Update candidate stage to rejected
    4. Sync to ATS
    5. Log activity
    """
    try:
        # Human Review Gate — block automated rejection without a human reviewer
        # Compliance: LGPD art. 20, EU AI Act art. 14
        if not request.reviewer_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "human_review_required",
                    "message": (
                        "Rejeição de candidato requer identificação do revisor humano (reviewer_id). "
                        "Rejeições automatizadas sem revisão humana não são permitidas."
                    ),
                    "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                },
            )

        logger.info(
            f"❌ [CANDIDATE_REJECTED] Processing rejection: "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}, "
            f"stage={request.rejection_stage}, reviewer={request.reviewer_id}"
        )

        is_valid, error_msg = await validate_multi_tenancy(
            db, request.candidate_id, request.vacancy_id, request.company_id
        )
        if not is_valid:
            logger.warning(f"⚠️ [CANDIDATE_REJECTED] Multi-tenancy validation failed: {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)

        actions_taken = []
        email_sent = False
        stage_updated = False
        added_to_talent_pool = False
        ats_synced = False
        
        if request.send_feedback:
            try:
                email_service = get_email_service()
                from app.templates.communication_templates import EmailTemplates
                
                template = EmailTemplates.candidate_rejected(
                    candidate_name=request.candidate_name or "Candidato",
                    job_title=request.job_title or "a posição",
                    rejection_reason=request.rejection_reason,
                    rejection_stage=request.rejection_stage
                )
                
                if request.candidate_email:
                    await email_service.send_email(
                        to_email=request.candidate_email,
                        subject=template["subject"],
                        body=template["body"]
                    )
                    email_sent = True
                    actions_taken.append("rejection_email_sent")
                    logger.info("✅ [CANDIDATE_REJECTED] Rejection email sent")
            except Exception as e:
                logger.error(f"❌ [CANDIDATE_REJECTED] Failed to send rejection email: {e}")
        
        if request.add_to_talent_pool:
            try:
                await activity_svc.create_activity(
                    activity_type="added_to_talent_pool",
                    title="Candidato adicionado ao banco de talentos",
                    description=(
                        f"{request.candidate_name or 'Candidato'} adicionado ao banco de talentos. "
                        f"Origem: {request.job_title or 'vaga'}. "
                        f"Rejeitado em: {request.rejection_stage or 'N/A'}. "
                        f"Motivo: {request.rejection_reason or 'Não especificado'}"
                    ),
                    actor_id="system",
                    actor_name="LIA Automation",
                    actor_type="system",
                    target_id=request.candidate_id,
                    target_type="candidate",
                    extra_data={
                        "vacancy_id": request.vacancy_id,
                        "company_id": request.company_id,
                        "source": "rejection",
                        "rejection_stage": request.rejection_stage,
                        "rejection_reason": request.rejection_reason
                    },
                    category="talent_pool"
                )
                added_to_talent_pool = True
                actions_taken.append("added_to_talent_pool")
                logger.info("✅ [CANDIDATE_REJECTED] Added to talent pool")
            except Exception as e:
                logger.error(f"❌ [CANDIDATE_REJECTED] Failed to add to talent pool: {e}")
        
        try:
            from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService
            pipeline_service = PipelineStageService()
            
            from sqlalchemy import and_, select

            from app.models.candidate import VacancyCandidate
            
            vc_result = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.candidate_id == request.candidate_id,
                        VacancyCandidate.vacancy_id == request.vacancy_id
                    )
                )
            )
            vacancy_candidate = vc_result.scalar_one_or_none()
            
            if vacancy_candidate:
                await pipeline_service.transition_candidate(
                    vacancy_candidate_id=str(vacancy_candidate.id),
                    to_stage="Reprovado",
                    to_sub_status="reprovado",
                    triggered_by="automation",
                    source_agent="rejection_management",
                    reason=request.rejection_reason or "Candidate rejected",
                    db=db
                )
                stage_updated = True
                actions_taken.append("stage_updated")
                logger.info("✅ [CANDIDATE_REJECTED] Stage updated to Reprovado")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_REJECTED] Failed to update stage: {e}")
        
        try:
            ats_sync_service = get_ats_sync_service()
            from app.domains.ats_integration.services.ats_sync_service import ATSSyncTrigger
            
            sync_result = await ats_sync_service.trigger_sync(
                trigger=ATSSyncTrigger.STATUS_CHANGE,
                source_agent="automation",
                ats_type="gupy",
                candidate_id=request.candidate_id,
                job_id=request.vacancy_id,
                data={"status": "rejected", "reason": request.rejection_reason}
            )
            if sync_result.get("success"):
                ats_synced = True
                actions_taken.append("ats_synced")
                logger.info("✅ [CANDIDATE_REJECTED] ATS synced successfully")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_REJECTED] Failed to sync ATS: {e}")
        
        try:
            await audit_svc.log_decision(
                company_id=request.company_id,
                agent_name="automation",
                decision_type="candidate_rejected",
                action="reject_candidate",
                decision="rejected",
                score=None,
                confidence=1.0,
                reasoning=[
                    f"Candidate {request.candidate_name or request.candidate_id} rejected",
                    f"Stage: {request.rejection_stage or 'Not specified'}",
                    f"Reason: {request.rejection_reason or 'Not specified'}",
                    f"Added to talent pool: {request.add_to_talent_pool}",
                    f"Feedback sent: {request.send_feedback}"
                ],
                criteria_used=["rejection_stage", "rejection_reason", "talent_pool", "feedback"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.vacancy_id,
                human_review_required=True
            )
            logger.info("📝 [CANDIDATE_REJECTED] Audit log created")
        except Exception as e:
            logger.error(f"❌ [CANDIDATE_REJECTED] Failed to create audit log: {e}")
        
        response_data = {
            "success": True,
            "trigger": "candidate_rejected",
            "actions": actions_taken,
            "details": {
                "email_sent": email_sent,
                "stage_updated": stage_updated,
                "added_to_talent_pool": added_to_talent_pool,
                "ats_synced": ats_synced
            },
            "metadata": {
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "rejection_stage": request.rejection_stage,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            f"✅ [CANDIDATE_REJECTED] Processing complete: actions={actions_taken}"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_REJECTED] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar rejeição: {str(e)}"
        )


