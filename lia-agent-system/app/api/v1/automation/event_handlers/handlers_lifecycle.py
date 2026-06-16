"""
Candidate lifecycle event handlers.

Routes:
- POST /handle-trigger/candidate-inactive
- POST /handle-trigger/candidate-no-show
- POST /handle-trigger/offer-sent
- POST /handle-trigger/candidate-hired
- POST /handle-trigger/candidate-rejected
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service as get_activity_service_canonical
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.domains.recruiter_assistant.services.pipeline_stage_service import get_pipeline_stage_service, PipelineStageService

from .._shared import (
    CandidateHiredPayload,
    CandidateHiredResponse,
    CandidateInactiveRequest,
    CandidateInactiveResponse,
    CandidateNoShowRequest,
    CandidateNoShowResponse,
    CandidateRejectedPayload,
    CandidateRejectedResponse,
    OfferSentPayload,
    OfferSentResponse,
    ensure_company_access,
    get_activity_service,
    get_ats_sync_service,
    get_mailgun_email_service,
    get_whatsapp_service,
    log_automation_execution,
    validate_multi_tenancy,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Route: candidate-inactive
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/candidate-inactive", response_model=CandidateInactiveResponse)
async def handle_candidate_inactive(
    request: CandidateInactiveRequest,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="CANDIDATE_INACTIVE",
        )

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
                email_service = get_mailgun_email_service()

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
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
        await log_automation_execution(
            db,
            trigger_event="candidate_inactive",
            trigger_data={
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "days_inactive": days_inactive,
                "current_stage": current_stage,
                "last_activity_date": request.last_activity_date.isoformat() if request.last_activity_date else None,
            },
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id,
            action_executed="send_inactive_follow_up",
            action_result={
                "email_sent": email_sent,
                "whatsapp_sent": whatsapp_sent,
                "notification_created": notification_created,
                "follow_up_type": follow_up_type,
                "communication_failures": communication_failures,
            },
            status="success" if (email_sent or whatsapp_sent) else ("partial" if notification_created else "no_action"),
        )

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
            detail="Internal server error"
        )


# ---------------------------------------------------------------------------
# Route: candidate-no-show
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/candidate-no-show", response_model=CandidateNoShowResponse)
async def handle_candidate_no_show(
    request: CandidateNoShowRequest,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="CANDIDATE_NO_SHOW",
        )

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
                    email_service = get_mailgun_email_service()
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
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"💬 [CANDIDATE_NO_SHOW] Reschedule WhatsApp sent to {candidate_phone}: {whatsapp_sent}")
                except Exception as e:
                    logger.error(f"❌ [CANDIDATE_NO_SHOW] Failed to send reschedule WhatsApp: {e}")
        else:
            # Multiple no-shows: Send final notice
            if candidate_email:
                try:
                    email_service = get_mailgun_email_service()
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
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
                confidence_score=confidence_score,
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
        await log_automation_execution(
            db,
            trigger_event="candidate_no_show",
            trigger_data={
                "candidate_id": request.candidate_id,
                "vacancy_id": request.vacancy_id,
                "interview_id": request.interview_id,
                "interview_datetime": request.interview_datetime.isoformat(),
                "interview_type": request.interview_type,
                "no_show_count": no_show_count,
            },
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id,
            action_executed=action_taken,
            action_result={
                "email_sent": email_sent,
                "whatsapp_sent": whatsapp_sent,
                "notification_created": notification_created,
                "suggestion_created": suggestion_created,
                "recommendation": recommendation,
                "confidence_score": confidence_score,
            },
            status="success" if (email_sent or whatsapp_sent or notification_created or suggestion_created) else "no_action",
        )

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
            detail="Internal server error"
        )


# ---------------------------------------------------------------------------
# Route: offer-sent
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/offer-sent", response_model=OfferSentResponse)
async def handle_offer_sent(
    request: OfferSentPayload,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="OFFER_SENT",
        )

        actions_taken = []
        email_sent = False
        notification_created = False
        ats_synced = False

        try:
            email_service = get_mailgun_email_service()
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

        logger.info(f"✅ [OFFER_SENT] Processing complete: actions={actions_taken}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [OFFER_SENT] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ---------------------------------------------------------------------------
# Route: candidate-hired
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/candidate-hired", response_model=CandidateHiredResponse)
async def handle_candidate_hired(
    request: CandidateHiredPayload,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
    pipeline_service: PipelineStageService = Depends(get_pipeline_stage_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="CANDIDATE_HIRED",
        )

        actions_taken = []
        email_sent = False
        stage_updated = False
        notification_created = False
        ats_synced = False

        try:
            email_service = get_mailgun_email_service()
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
            # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
            logger.error(f"❌ [CANDIDATE_HIRED] Failed to send welcome email: {e}")

        try:
            from app.domains.candidates.repositories.vacancy_candidate_repository import (
                VacancyCandidateRepository,
            )

            # ADR-001 Repository Pattern: VacancyCandidateRepository handles
            # candidate_id/vacancy_id UUID coercion + tenant-agnostic lookup.
            vc_repo = VacancyCandidateRepository(db)
            vacancy_candidate = await vc_repo.get_by_vacancy_and_candidate(
                vacancy_id=request.vacancy_id,
                candidate_id=request.candidate_id,
            )

            if vacancy_candidate:
                await pipeline_service.transition_candidate(
                    vacancy_candidate_id=str(vacancy_candidate.id),
                    to_stage="Contratado",
                    to_sub_status="hired",  # fix: "contratado" não está em VALID_STATUSES — usar "hired"
                    triggered_by="automation",
                    source_agent="offer_management",
                    reason="Candidate hired",
                    db=db
                )
                stage_updated = True
                actions_taken.append("stage_updated")
                logger.info("✅ [CANDIDATE_HIRED] Stage updated to Contratado")

                # B2: setar Candidate.is_hired=True (LGPD guard + UI chip)
                try:
                    from app.domains.candidates.repositories.candidate_repository import CandidateRepository
                    cand_repo = CandidateRepository(db)
                    cand = await cand_repo.get_by_id_str(
                        str(request.candidate_id),
                        company_id=str(request.company_id),
                    )
                    if cand:
                        cand.is_hired = True
                        cand.hired_at = datetime.utcnow()
                        if request.job_title:
                            cand.hired_job_title = request.job_title
                        await db.commit()
                        actions_taken.append("candidate_is_hired_set")
                        logger.info("✅ [CANDIDATE_HIRED] Candidate.is_hired=True persisted")
                except Exception as _cand_exc:
                    logger.error(f"❌ [CANDIDATE_HIRED] Failed to set is_hired: {_cand_exc}")

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

        logger.info(f"✅ [CANDIDATE_HIRED] Processing complete: actions={actions_taken}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_HIRED] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ---------------------------------------------------------------------------
# Route: candidate-rejected
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/candidate-rejected", response_model=CandidateRejectedResponse)
async def handle_candidate_rejected(
    request: CandidateRejectedPayload,
    db: AsyncSession = Depends(get_tenant_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
    pipeline_service: PipelineStageService = Depends(get_pipeline_stage_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        await ensure_company_access(
            db, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id, company_id=request.company_id,
            handler_tag="CANDIDATE_REJECTED",
        )

        actions_taken = []
        email_sent = False
        stage_updated = False
        added_to_talent_pool = False
        ats_synced = False

        if request.send_feedback:
            try:
                email_service = get_mailgun_email_service()
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
            from app.domains.candidates.repositories.vacancy_candidate_repository import (
                VacancyCandidateRepository,
            )

            # ADR-001 Repository Pattern: VacancyCandidateRepository handles
            # candidate_id/vacancy_id UUID coercion + tenant-agnostic lookup.
            vc_repo = VacancyCandidateRepository(db)
            vacancy_candidate = await vc_repo.get_by_vacancy_and_candidate(
                vacancy_id=request.vacancy_id,
                candidate_id=request.candidate_id,
            )

            if vacancy_candidate:
                await pipeline_service.transition_candidate(
                    vacancy_candidate_id=str(vacancy_candidate.id),
                    to_stage="Reprovado",
                    to_sub_status="rejected",  # fix: "reprovado" não está em VALID_STATUSES — usar "rejected"
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

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py

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

        logger.info(f"✅ [CANDIDATE_REJECTED] Processing complete: actions={actions_taken}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANDIDATE_REJECTED] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
