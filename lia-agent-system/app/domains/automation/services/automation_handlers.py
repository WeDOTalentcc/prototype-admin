"""
Automation Handlers
Individual handlers for automation triggers, called by the StageAutomationEngine.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # noqa: F401 — exposed for test mocking

from app.shared.messaging.rails_event_publisher import publish_rails_event

logger = logging.getLogger(__name__)

async def _create_automation_task(
    *,
    db: AsyncSession,
    company_id: str,
    task_type: str,
    priority: str,
    title: str,
    description: str | None = None,
    related_job_id: str | None = None,
    related_candidate_id: str | None = None,
    context: dict | None = None,
) -> str | None:
    """Cria task de automacao fail-open. Nunca deixa o handler falhar.

    Returns task.id ou None em caso de erro.
    Task 2.A (2026-05-25): preenche tasks table para Decidir page.
    """
    try:
        from app.domains.tasks.repositories.tasks_repository import TasksRepository
        from app.models.task import TaskPriority as _TP, TaskType as _TT
        repo = TasksRepository(db)
        task = await repo.create_task(
            company_id=company_id,
            title=title,
            description=description,
            task_type=_TT(task_type),
            priority=_TP(priority),
            created_by_agent="automation_handler",
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            context=context or {},
            is_automated=True,
        )
        logger.info(
            "[TASK] Created %s task %s for company %s",
            task_type, task.id, company_id,
        )
        return task.id
    except Exception as e:
        logger.warning(
            "[TASK] Failed to create automation task (fail-open): %s", e, exc_info=True
        )
        return None


async def _fetch_names(
    *,
    db,
    candidate_id: str | None = None,
    vacancy_id: str | None = None,
) -> tuple[str, str]:
    """Fail-open helper: fetch readable candidate name and job title for task titles.

    Returns ("Candidato", "") if any lookup fails.
    Task 5.A (2026-05-25).
    """
    candidate_name = "Candidato"
    job_title = ""
    try:
        if candidate_id:
            from app.domains.candidates.repositories.candidate_repository import CandidateRepository
            candidate = await CandidateRepository(db).get_by_id_str(candidate_id)
            if candidate and candidate.name:
                candidate_name = candidate.name
    except Exception as _e:
        pass
    try:
        if vacancy_id:
            from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository
            vacancy = await JobVacancyCRUDRepository(db).get_vacancy_by_id(vacancy_id)
            if vacancy and getattr(vacancy, "title", None):
                job_title = vacancy.title
    except Exception as _e:
        pass
    return candidate_name, job_title


async def validate_multi_tenancy(
    db: AsyncSession,
    candidate_id: str,
    vacancy_id: str,
    company_id: str
) -> tuple[bool, str]:
    """
    Validate that candidate and vacancy belong to the specified company.
    Returns (is_valid, error_message).
    """
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )

    job_repo = JobVacancyCRUDRepository(db)
    if not await job_repo.get_vacancy_by_id_and_company(vacancy_id, company_id):
        return False, "Vacancy not found or belongs to different company"

    vc_repo = VacancyCandidateRepository(db)
    vc = await vc_repo.get_by_vacancy_candidate_and_company(
        vacancy_id=vacancy_id,
        candidate_id=candidate_id,
        company_id=company_id,
    )
    if not vc:
        return False, "Candidate not found or not associated with this vacancy/company"

    return True, ""


async def handle_screening_completed(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    wsi_scores: dict[str, float] | None = None,
    passed: bool = True,
    **kwargs
) -> dict[str, Any]:
    """
    Handle screening completed trigger.
    Creates activity and sends feedback communication to candidate.
    CASCADE: screening_completed → send feedback communication
    """
    logger.info(f"[HANDLER] Screening completed for candidate {candidate_id}")

    result = {
        "action": "screening_completed",
        "candidate_id": candidate_id,
        "passed": passed,
        "activity_created": False,
        "feedback_sent": False,
        "cascade_errors": []
    }

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="screening_completed",
            title="Triagem Concluída",
            description=f"Candidato {'aprovado' if passed else 'reprovado'} na triagem.",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "wsi_scores": wsi_scores,
                "passed": passed
            },
            category="automation"
        )
        result["activity_created"] = True
    except Exception as e:
        logger.error(f"[HANDLER] Error creating screening activity: {e}")
        result["cascade_errors"].append(f"activity_creation: {e}")

    try:
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
        comm_dispatcher = CommunicationDispatcher()

        screening_type = kwargs.get("screening_type", "wsi")
        status_label = "aprovado" if passed else "reprovado"
        subject = f"Resultado da Triagem - {status_label.capitalize()}"
        body = (
            f"Sua triagem ({screening_type.upper()}) foi concluída. "
            f"Resultado: {status_label}."
        )

        candidate_repo = CandidateRepository(db)
        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if candidate and (candidate.email or getattr(candidate, 'phone', None)):
            dispatch_result = await comm_dispatcher.dispatch_message(
                company_id=company_id,
                recipient_email=candidate.email,
                recipient_phone=getattr(candidate, 'phone', None),
                subject=subject,
                message=body,
                candidate_name=candidate.name,
                db=db,
            )
            result["feedback_sent"] = dispatch_result.get("success", False)
            result["feedback_channels"] = dispatch_result.get("channels_sent", [])
            logger.info(
                f"[CASCADE] Screening feedback dispatched to candidate {candidate_id} "
                f"(passed={passed}, channels={dispatch_result.get('channels_sent', [])})"
            )
        else:
            logger.warning(
                f"[CASCADE] Cannot send screening feedback: no contact for candidate {candidate_id}"
            )
            result["cascade_errors"].append("feedback: candidate contact info not found")
    except Exception as e:
        logger.error(f"[CASCADE] Error sending screening feedback: {e}")
        result["cascade_errors"].append(f"feedback: {e}")

    _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
    result["task_id"] = await _create_automation_task(
        db=db,
        company_id=company_id,
        task_type="cv_review",
        priority="high" if not passed else "medium",
        title=f"Revisar triagem: {_cname}",
        description=f"Candidato {'aprovado' if passed else 'reprovado'} na triagem WSI. Revisar scores e confirmar.",
        related_job_id=vacancy_id,
        related_candidate_id=candidate_id,
        context={"candidate_name": _cname, "job_title": _jtitle},
    )
    return result


async def handle_interview_scheduled(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    interview_datetime: str | None = None,
    interview_type: str = "video",
    interviewer_name: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle interview scheduled trigger.
    Sends confirmation and creates calendar events.
    """
    logger.info(f"[HANDLER] Interview scheduled for candidate {candidate_id}")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="interview_scheduled",
            title="Entrevista Agendada",
            description=f"Entrevista {interview_type} agendada para {interview_datetime or 'data a confirmar'}.",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "interview_datetime": interview_datetime,
                "interview_type": interview_type,
                "interviewer_name": interviewer_name
            },
            category="automation"
        )

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="interview_schedule",
            priority="high",
            title=f"Preparar entrevista: {_cname}",
            description=f"Entrevista {interview_type} agendada para {interview_datetime or 'data a confirmar'}.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "interview_scheduled",
            "candidate_id": candidate_id,
            "interview_datetime": interview_datetime,
            "notification_sent": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling interview scheduled: {e}")
        return {"error": str(e)}


async def handle_interview_completed(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    interview_id: str | None = None,
    outcome: str | None = None,
    feedback: dict[str, Any] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle interview completed trigger.
    Generates parecer and updates candidate status.
    """
    logger.info(f"[HANDLER] Interview completed for candidate {candidate_id}")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="interview_completed",
            title="Entrevista Concluída",
            description=f"Resultado: {outcome or 'Pendente avaliação'}",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "interview_id": interview_id,
                "outcome": outcome,
                "feedback": feedback
            },
            category="automation"
        )

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="feedback_pending",
            priority="high",
            title=f"Fornecer feedback: {_cname}",
            description=f"Entrevista concluída. Resultado: {outcome or 'Pendente avaliação'}. Registrar parecer.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "interview_completed",
            "candidate_id": candidate_id,
            "outcome": outcome,
            "parecer_triggered": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling interview completed: {e}")
        return {"error": str(e)}


async def handle_candidate_inactive(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    days_inactive: int = 0,
    last_activity: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle candidate inactive trigger.
    Sends follow-up communication or creates task for recruiter.
    """
    logger.info(f"[HANDLER] Candidate {candidate_id} inactive for {days_inactive} days")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="candidate_inactive",
            title="Candidato Inativo",
            description=f"Sem atividade há {days_inactive} dias. Última ação: {last_activity or 'N/A'}",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "days_inactive": days_inactive,
                "last_activity": last_activity
            },
            category="automation"
        )

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="follow_up",
            priority="medium",
            title=f"Acompanhar candidato inativo: {_cname}",
            description=f"Sem atividade há {days_inactive} dias. Última ação: {last_activity or 'N/A'}.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "candidate_inactive",
            "candidate_id": candidate_id,
            "days_inactive": days_inactive,
            "followup_scheduled": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling candidate inactive: {e}")
        return {"error": str(e)}


async def handle_candidate_no_show(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    interview_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle candidate no-show trigger.
    Creates task to reschedule or reject candidate.
    """
    logger.info(f"[HANDLER] Candidate {candidate_id} no-show")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="candidate_no_show",
            title="No-Show na Entrevista",
            description="Candidato não compareceu à entrevista agendada.",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "interview_id": interview_id
            },
            category="automation"
        )

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="follow_up",
            priority="high",
            title=f"Reagendar ou encerrar: {_cname} (no-show)",
            description="Candidato não compareceu à entrevista. Decidir: reagendar ou reprovar.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "candidate_no_show",
            "candidate_id": candidate_id,
            "task_created": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling candidate no-show: {e}")
        return {"error": str(e)}


async def handle_offer_sent(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    offer_details: dict[str, Any] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle offer sent trigger.
    Logs activity and starts monitoring for response.
    """
    logger.info(f"[HANDLER] Offer sent to candidate {candidate_id}")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="offer_sent",
            title="Proposta Enviada",
            description="Proposta de emprego enviada ao candidato.",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "offer_details": offer_details
            },
            category="automation"
        )

        # UC-P0-21: publish offer.sent event to Rails (non-blocking fire-and-forget)
        try:
            _salary = (offer_details or {}).get("salary")
            _channel = (offer_details or {}).get("channel")
            await publish_rails_event(
                event_type="offer.sent",
                payload={
                    "candidate_id": candidate_id,
                    "job_id": kwargs.get("job_id"),
                    "apply_id": kwargs.get("apply_id"),
                    "salary_offered": float(_salary) if _salary is not None else None,
                    "channel": _channel,
                },
                company_id=company_id,
            )
        except Exception as _e:
            logger.warning("[HANDLER] Failed to publish offer.sent event: %s", _e)

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="general",
            priority="medium",
            title=f"Acompanhar proposta: {_cname}",
            description="Proposta enviada. Monitorar resposta do candidato.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "offer_sent",
            "candidate_id": candidate_id,
            "monitoring_started": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling offer sent: {e}")
        return {"error": str(e)}


async def handle_candidate_hired(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    start_date: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle candidate hired trigger.
    Syncs with ATS and triggers onboarding process.
    """
    logger.info(f"[HANDLER] Candidate {candidate_id} hired")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="candidate_hired",
            title="Candidato Contratado",
            description=f"Início previsto: {start_date or 'A definir'}",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "start_date": start_date
            },
            category="automation"
        )

        _cname, _jtitle = await _fetch_names(db=db, candidate_id=candidate_id, vacancy_id=vacancy_id)
        await _create_automation_task(
            db=db,
            company_id=company_id,
            task_type="send_report",
            priority="medium",
            title=f"Encerrar processo: {_cname} contratado",
            description=f"Candidato contratado. Início previsto: {start_date or 'A definir'}. Fechar vaga e gerar relatório.",
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            context={"candidate_name": _cname, "job_title": _jtitle},
        )
        return {
            "action": "candidate_hired",
            "candidate_id": candidate_id,
            "ats_sync_triggered": True,
            "onboarding_started": True
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling candidate hired: {e}")
        return {"error": str(e)}


async def handle_candidate_rejected(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    rejection_reason: str | None = None,
    add_to_talent_pool: bool = True,
    **kwargs
) -> dict[str, Any]:
    """
    Handle candidate rejected trigger.
    Sends feedback and optionally adds to talent pool.
    """
    logger.info(f"[HANDLER] Candidate {candidate_id} rejected")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="candidate_rejected",
            title="Candidato Não Aprovado",
            description=f"Motivo: {rejection_reason or 'Não informado'}",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "rejection_reason": rejection_reason,
                "add_to_talent_pool": add_to_talent_pool
            },
            category="automation"
        )

        queue_promoted = []
        try:
            promoted = await process_screening_queue(
                db=db,
                vacancy_id=vacancy_id,
                company_id=company_id,
                max_promote=1,
            )
            queue_promoted = promoted
            if promoted:
                logger.info(
                    f"[HANDLER] Auto-promoted {len(promoted)} candidate(s) from queue "
                    f"after rejection of {candidate_id}"
                )
        except Exception as queue_err:
            logger.error(f"[HANDLER] Error processing queue after rejection: {queue_err}")

        return {
            "action": "candidate_rejected",
            "candidate_id": candidate_id,
            "feedback_sent": True,
            "added_to_talent_pool": add_to_talent_pool,
            "queue_promoted": queue_promoted,
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling candidate rejected: {e}")
        return {"error": str(e)}


async def handle_ats_sync(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    new_stage: str | None = None,
    previous_stage: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Handle ATS sync trigger.
    Synchronizes stage changes with external ATS.
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[HANDLER] ATS sync for candidate {candidate_id}: {previous_stage} -> {new_stage}")

    try:
        from app.domains.ats_integration.services.ats_sync_service import ATSSyncService
        ats_sync_service = ATSSyncService()

        result = await ats_sync_service.sync_candidate_stage(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
            new_stage=new_stage
        )

        return {
            "action": "ats_sync",
            "candidate_id": candidate_id,
            "new_stage": new_stage,
            "sync_result": result
        }
    except Exception as e:
        logger.error(f"[HANDLER] Error handling ATS sync: {e}")
        return {"error": str(e)}


async def handle_stage_changed(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    new_stage: str | None = None,
    previous_stage: str | None = None,
    triggered_by: str = "system",
    **kwargs
) -> dict[str, Any]:
    """
    Handle stage changed trigger.
    Logs activity and triggers cross-domain cascades based on the new stage.
    CASCADE: stage_changed → schedule interview (if approved) OR send rejection (if rejected)
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[HANDLER] Stage changed for candidate {candidate_id}: {previous_stage} -> {new_stage}")

    result = {
        "action": "stage_changed",
        "candidate_id": candidate_id,
        "new_stage": new_stage,
        "previous_stage": previous_stage,
        "activity_logged": False,
        "cascade_action": None,
        "cascade_errors": []
    }

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="stage_changed",
            title="Etapa Alterada",
            description=f"De '{previous_stage or 'N/A'}' para '{new_stage or 'N/A'}'",
            actor_id=triggered_by,
            actor_name="LIA Automation" if triggered_by == "system" else triggered_by,
            actor_type="system" if triggered_by == "system" else "user",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "new_stage": new_stage,
                "previous_stage": previous_stage
            },
            category="pipeline"
        )
        result["activity_logged"] = True
    except Exception as e:
        logger.error(f"[HANDLER] Error logging stage change activity: {e}")
        result["cascade_errors"].append(f"activity_log: {e}")

    stage_lower = (new_stage or "").lower().strip()

    interview_stages = {"entrevista", "interview", "entrevista_agendada", "interview_scheduled"}
    rejected_stages = {"rejeitado", "rejected", "reprovado", "nao_aprovado", "declined"}

    if stage_lower in interview_stages:
        try:
            from datetime import datetime, timedelta

            from app.domains.candidates.repositories.candidate_repository import (
                CandidateRepository,
            )
            from app.domains.interview_scheduling.services.scheduling_service import SchedulingService
            from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                JobVacancyCRUDRepository,
            )

            scheduling_service = SchedulingService()

            candidate = await CandidateRepository(db).get_by_id_str(candidate_id)
            vacancy = await JobVacancyCRUDRepository(db).get_vacancy_by_id_and_company(
                vacancy_id, company_id
            )

            candidate_name = candidate.name if candidate else "Candidato"
            candidate_email = candidate.email if candidate else ""
            job_title = vacancy.title if vacancy else ""

            default_start = datetime.utcnow() + timedelta(days=3)
            start_time = kwargs.get("interview_start_time", default_start)
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)

            interviewer_name = kwargs.get("interviewer_name", "Recrutador")
            interviewer_email = kwargs.get("interviewer_email", "")

            interview = await scheduling_service.create_interview(
                db=db,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                interviewer_name=interviewer_name,
                interviewer_email=interviewer_email,
                start_time=start_time,
                duration_minutes=kwargs.get("duration_minutes", 60),
                interview_type=kwargs.get("interview_type", "video"),
                job_title=job_title,
                job_vacancy_id=vacancy_id,
                company_id=company_id,
                notes=f"Auto-scheduled after stage change to '{new_stage}'",
                dispatch_event=False
            )
            result["cascade_action"] = "interview_scheduled"
            result["interview_id"] = str(interview.id) if hasattr(interview, "id") else str(interview)
            logger.info(
                f"[CASCADE] Interview scheduled for candidate {candidate_id} "
                f"after stage change to '{new_stage}'"
            )
        except Exception as e:
            logger.error(f"[CASCADE] Error scheduling interview for candidate {candidate_id}: {e}")
            result["cascade_errors"].append(f"interview_scheduling: {e}")

    elif stage_lower in rejected_stages:
        try:
            from app.domains.candidates.repositories.candidate_repository import (
                CandidateRepository,
            )
            from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher

            comm_dispatcher = CommunicationDispatcher()
            rejection_reason = kwargs.get("rejection_reason", "Perfil não aderente aos requisitos da vaga")

            candidate = await CandidateRepository(db).get_by_id_str(candidate_id)

            if candidate and (candidate.email or getattr(candidate, 'phone', None)):
                rejection_body = (
                    f"Agradecemos seu interesse e participação no processo seletivo. "
                    f"Após análise cuidadosa, decidimos seguir com outros candidatos. "
                    f"Motivo: {rejection_reason}"
                )
                dispatch_result = await comm_dispatcher.dispatch_message(
                    company_id=company_id,
                    recipient_email=candidate.email,
                    recipient_phone=getattr(candidate, 'phone', None),
                    subject="Atualização sobre sua candidatura",
                    message=rejection_body,
                    candidate_name=candidate.name,
                    db=db,
                )
                result["cascade_action"] = "rejection_dispatched"
                result["rejection_channels"] = dispatch_result.get("channels_sent", [])
                logger.info(
                    f"[CASCADE] Rejection dispatched to candidate {candidate_id} "
                    f"after stage change to '{new_stage}' (channels={dispatch_result.get('channels_sent', [])})"
                )
            else:
                logger.warning(
                    f"[CASCADE] Cannot send rejection: no contact for candidate {candidate_id}"
                )
                result["cascade_errors"].append("rejection: candidate contact info not found")
        except Exception as e:
            logger.error(f"[CASCADE] Error sending rejection email for candidate {candidate_id}: {e}")
            result["cascade_errors"].append(f"rejection_email: {e}")

        try:
            promoted = await process_screening_queue(
                db=db,
                vacancy_id=vacancy_id,
                company_id=company_id,
                max_promote=1,
            )
            if promoted:
                result["queue_promoted"] = len(promoted)
                logger.info(
                    f"[CASCADE] Auto-promoveu {len(promoted)} candidato(s) da fila "
                    f"após rejeição de {candidate_id} no stage '{new_stage}'"
                )
        except Exception as queue_err:
            logger.error(f"[CASCADE] Erro ao processar fila após rejeição: {queue_err}")
            result["cascade_errors"].append(f"queue_promotion: {queue_err}")

    return result


async def handle_job_published(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    **kwargs
) -> dict[str, Any]:
    """
    Handle job published trigger.
    Activates sourcing pipeline to start searching for candidates.
    CASCADE: job_published → activate sourcing pipeline
    """
    job_id = kwargs.get("job_id") or vacancy_id
    job_title = kwargs.get("job_title", "")
    logger.info(f"[HANDLER] Job published: job={job_id}, company={company_id}")

    result = {
        "action": "job_published",
        "job_id": job_id,
        "company_id": company_id,
        "activity_created": False,
        "sourcing_activated": False,
        "cascade_errors": []
    }

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="job_published",
            title="Vaga Publicada",
            description=f"Vaga '{job_title or job_id}' publicada. Sourcing ativado automaticamente.",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=job_id,
            target_type="vacancy",
            extra_data={
                "company_id": company_id,
                "job_title": job_title
            },
            category="automation"
        )
        result["activity_created"] = True
    except Exception as e:
        logger.error(f"[HANDLER] Error creating job published activity: {e}")
        result["cascade_errors"].append(f"activity_creation: {e}")

    try:
        from app.domains.sourcing.services.sourcing_pipeline import SourcingPipelineService
        sourcing_service = SourcingPipelineService()

        user_credits = kwargs.get("user_credits", 100)
        expand_to_global = kwargs.get("expand_to_global", False)

        sourcing_result = await sourcing_service.run_post_publish_sourcing(
            db=db,
            job_id=job_id,
            user_credits=user_credits,
            expand_to_global=expand_to_global
        )
        result["sourcing_activated"] = True
        result["sourcing_result"] = sourcing_result if isinstance(sourcing_result, dict) else {"status": "triggered"}
        logger.info(
            f"[CASCADE] Sourcing pipeline activated for job {job_id} "
            f"after publication"
        )
    except Exception as e:
        logger.error(f"[CASCADE] Error activating sourcing for job {job_id}: {e}")
        result["cascade_errors"].append(f"sourcing_activation: {e}")

    result["task_id"] = await _create_automation_task(
        db=db,
        company_id=company_id,
        task_type="sourcing",
        priority="medium",
        title=f"Acompanhar sourcing: {job_title or job_id}",
        description=f"Vaga '{job_title or job_id}' publicada. Sourcing ativado. Revisar candidatos encontrados.",
        related_job_id=job_id,
        context={"job_title": job_title or ""},
    )
    return result


async def handle_candidates_sourced(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    **kwargs
) -> dict[str, Any]:
    """
    Handle candidates sourced trigger.
    Triggers screening pipeline for newly sourced candidates.
    CASCADE: candidates_sourced → trigger screening pipeline
    """
    job_id = kwargs.get("job_id") or vacancy_id
    candidates_added = kwargs.get("candidates_added", 0)
    candidate_ids = kwargs.get("candidate_ids", [])
    job_title = kwargs.get("job_title", "")
    logger.info(
        f"[HANDLER] Candidates sourced for job {job_id}: "
        f"added={candidates_added}"
    )

    result = {
        "action": "candidates_sourced",
        "job_id": job_id,
        "company_id": company_id,
        "candidates_added": candidates_added,
        "activity_created": False,
        "screening_triggered": False,
        "screening_count": 0,
        "cascade_errors": []
    }

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="candidates_sourced",
            title="Candidatos Encontrados",
            description=(
                f"{candidates_added} candidatos adicionados à vaga "
                f"'{job_title or job_id}'. Triagem iniciada automaticamente."
            ),
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=job_id,
            target_type="vacancy",
            extra_data={
                "company_id": company_id,
                "candidates_added": candidates_added,
                "source": kwargs.get("source", "local")
            },
            category="automation"
        )
        result["activity_created"] = True
    except Exception as e:
        logger.error(f"[HANDLER] Error creating candidates sourced activity: {e}")
        result["cascade_errors"].append(f"activity_creation: {e}")

    if candidates_added > 0 and candidate_ids:
        try:
            from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

            cv_scoring_service = CVScoringService()
            screening_count = 0
            for cid in candidate_ids:
                try:
                    await cv_scoring_service.screen_candidate(
                        candidate_id=cid,
                        vacancy_id=job_id,
                        company_id=company_id,
                        db=db
                    )
                    screening_count += 1
                except Exception as e:
                    logger.warning(
                        f"[CASCADE] Failed to trigger screening for "
                        f"candidate {cid}: {e}"
                    )

            result["screening_triggered"] = screening_count > 0
            result["screening_count"] = screening_count
            logger.info(
                f"[CASCADE] Screening dispatched for {screening_count}/{len(candidate_ids)} "
                f"candidates in job {job_id}"
            )
        except Exception as e:
            logger.error(f"[CASCADE] Error triggering screening pipeline: {e}")
            result["cascade_errors"].append(f"screening_pipeline: {e}")

    result["task_id"] = await _create_automation_task(
        db=db,
        company_id=company_id,
        task_type="cv_review",
        priority="medium",
        title=f"Revisar candidatos encontrados: {job_title or job_id}",
        description=f"{candidates_added} candidatos adicionados à vaga '{job_title or job_id}'. Triagem iniciada.",
        related_job_id=job_id,
        context={"job_title": job_title or ""},
    )
    return result


async def handle_slot_opened(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    db: AsyncSession,
    **kwargs
) -> dict[str, Any]:
    """
    Handle slot opened trigger — process the screening queue.

    When a slot opens (candidate rejected/withdrawn/completed), find the next
    candidate in the awaiting_screening queue ordered by rubric score DESC,
    creation date ASC, and send them an automatic screening invite.

    WhatsApp candidates → WhatsApp screening invite
    Email-only candidates → chat web screening link
    """
    logger.info(f"[HANDLER] Slot opened for vacancy {vacancy_id}, company {company_id}")

    result = {
        "action": "slot_opened",
        "vacancy_id": vacancy_id,
        "company_id": company_id,
        "candidates_promoted": 0,
        "invites_sent": 0,
        "cascade_errors": [],
    }

    try:
        promoted = await process_screening_queue(
            db=db,
            vacancy_id=vacancy_id,
            company_id=company_id,
            max_promote=kwargs.get("slots_available", 1),
        )
        result["candidates_promoted"] = len(promoted)
        result["invites_sent"] = len(promoted)
        result["promoted_candidates"] = promoted
        logger.info(
            f"[HANDLER] Promoted {len(promoted)} candidates from queue for vacancy {vacancy_id}"
        )
    except Exception as e:
        logger.error(f"[HANDLER] Error processing screening queue: {e}", exc_info=True)
        result["cascade_errors"].append(f"queue_processing: {e}")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="slot_opened",
            title="Slot Aberto na Fila de Triagem",
            description=(
                f"{result['candidates_promoted']} candidato(s) promovido(s) da fila de espera "
                f"para triagem na vaga {vacancy_id}."
            ),
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=vacancy_id,
            target_type="vacancy",
            extra_data={
                "company_id": company_id,
                "candidates_promoted": result["candidates_promoted"],
                "promoted_candidates": result.get("promoted_candidates", []),
            },
            category="automation",
        )
    except Exception as e:
        logger.warning(f"[HANDLER] Error creating slot_opened activity: {e}")
        result["cascade_errors"].append(f"activity_creation: {e}")

    return result


async def process_screening_queue(
    db: AsyncSession,
    vacancy_id: str,
    company_id: str,
    max_promote: int = 1,
) -> list:
    """
    Process the awaiting_screening queue for a vacancy.

    Ordering: pre_qualification_score DESC (higher rubric score first),
              created_at ASC (earlier application first as tiebreaker).

    For each promoted candidate:
    - Update VacancyCandidate status from 'awaiting_screening' to 'screening'
    - Update WhatsApp conversation state if applicable
    - Send screening invite via WhatsApp or chat web link via email
    """
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )
    from app.domains.communication.repositories.whatsapp_repository import (
        WhatsappRepository,
    )
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    from lia_models.whatsapp_conversation import ConversationState

    vc_repo = VacancyCandidateRepository(db)
    candidate_repo = CandidateRepository(db)
    whatsapp_repo = WhatsappRepository(db)
    job_repo = JobVacancyCRUDRepository(db)

    queued_candidates = await vc_repo.list_awaiting_screening_for_vacancy(
        vacancy_id=vacancy_id, limit=max_promote
    )

    promoted = []

    for vc in queued_candidates:
        try:
            candidate = await candidate_repo.get_by_id(vc.candidate_id)
            if not candidate:
                logger.warning(f"[QUEUE] Candidate {vc.candidate_id} not found, skipping")
                continue

            vc.status = "screening"
            vc.stage = "screening"
            # Task #1306: also persist the structural stage link so the SLA
            # detector can join by id instead of fragile name matching.
            from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
            vc.recruitment_stage_id = await resolve_recruitment_stage_id(
                db, str(vc.company_id), "screening"
            )
            vc.notes = (vc.notes or "") + "\n[Auto] Promovido da fila de espera"

            conversation = await whatsapp_repo.get_latest_awaiting_screening_for_candidate_vacancy(
                candidate_id=vc.candidate_id,
                job_vacancy_id=vc.vacancy_id,
            )

            invite_channel = "email"
            invite_sent = False

            job = await job_repo.get_vacancy_by_id_and_company(vc.vacancy_id, company_id)
            job_title = job.title if job else "a vaga"
            company_name = getattr(job, "company_name", None) or "Nossa Empresa"

            if conversation and conversation.phone_number:
                invite_channel = "whatsapp"
                try:
                    conversation.state = ConversationState.SCREENING
                    conversation.current_question_index = 0

                    from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory
                    provider = await WhatsAppProviderFactory.get_provider(company_id, db)

                    screening_msg = (
                        f"Olá, {candidate.name}! 👋\n\n"
                        f"Temos uma ótima notícia! Agora há uma vaga disponível para "
                        f"continuar o processo de triagem para *{job_title}*.\n\n"
                        f"Vamos continuar de onde paramos? Responda *SIM* para iniciarmos! 🚀"
                    )
                    await provider.send_text_message(conversation.phone_number, screening_msg)
                    invite_sent = True
                    logger.info(
                        f"[QUEUE] WhatsApp screening invite sent to {candidate.name} "
                        f"({conversation.phone_number})"
                    )
                except Exception as e:
                    logger.error(f"[QUEUE] Failed to send WhatsApp invite to {candidate.id}: {e}")
                    invite_channel = "email"

            if invite_channel == "email" and candidate.email:
                try:
                    from app.domains.candidates.services.candidate_feedback_service import candidate_feedback_service

                    screening_token = (vc.additional_data or {}).get("screening_invite_token")
                    if not screening_token:
                        import secrets as _secrets
                        screening_token = _secrets.token_urlsafe(32)
                        additional = dict(vc.additional_data or {})
                        additional["screening_invite_token"] = screening_token
                        vc.additional_data = additional

                    screening_url = f"/triagem/{screening_token}"

                    invite_sent = await candidate_feedback_service.send_gate_feedback(
                        gate_level="screening_invited",
                        candidate_email=candidate.email,
                        candidate_name=candidate.name,
                        vacancy_title=job_title,
                        company_name=company_name,
                        extra_context={"screening_url": screening_url},
                    )
                    logger.info(
                        f"[QUEUE] Screening invite via send_gate_feedback to {candidate.name} "
                        f"(sent={invite_sent})"
                    )
                except Exception as e:
                    logger.error(f"[QUEUE] Failed to dispatch invite to {candidate.id}: {e}")

            additional = dict(vc.additional_data or {})
            additional["promoted_from_queue_at"] = datetime.utcnow().isoformat()
            additional["invite_channel"] = invite_channel
            additional["invite_sent"] = invite_sent
            vc.additional_data = additional

            promoted.append({
                "candidate_id": str(vc.candidate_id),
                "candidate_name": candidate.name,
                "invite_channel": invite_channel,
                "invite_sent": invite_sent,
            })

        except Exception as e:
            logger.error(f"[QUEUE] Error promoting candidate {vc.candidate_id}: {e}", exc_info=True)

    if promoted:
        await db.commit()

    return promoted


async def handle_recruiter_override_approve(
    db: AsyncSession,
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
) -> dict[str, Any]:
    """
    Handle recruiter manual override — Approve button on awaiting_screening candidate.

    This is a priority promotion: the recruiter explicitly approves a queued
    candidate, bypassing the queue order.
    """
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )
    from app.domains.communication.repositories.whatsapp_repository import (
        WhatsappRepository,
    )
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    from lia_models.whatsapp_conversation import ConversationState

    logger.info(
        f"[OVERRIDE] Recruiter override approve for candidate {candidate_id} "
        f"in vacancy {vacancy_id}"
    )

    vc_repo = VacancyCandidateRepository(db)
    vc = await vc_repo.get_by_vacancy_and_candidate(
        vacancy_id=vacancy_id, candidate_id=candidate_id
    )

    if not vc:
        return {"success": False, "error": "VacancyCandidate not found"}

    if vc.status != "awaiting_screening":
        return {
            "success": False,
            "error": f"Candidate status is '{vc.status}', not 'awaiting_screening'",
        }

    vc.status = "screening"
    vc.stage = "screening"
    # Task #1306: also persist the structural stage link so the SLA detector
    # can join by id instead of fragile name matching.
    from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
    vc.recruitment_stage_id = await resolve_recruitment_stage_id(
        db, str(vc.company_id), "screening"
    )
    vc.notes = (vc.notes or "") + "\n[Override] Priorizado manualmente pelo recrutador"

    additional = dict(vc.additional_data or {})
    additional["recruiter_override_at"] = datetime.utcnow().isoformat()
    additional["override_type"] = "manual_approve"
    vc.additional_data = additional

    whatsapp_repo = WhatsappRepository(db)
    conversation = await whatsapp_repo.get_latest_awaiting_screening_for_candidate_vacancy(
        candidate_id=candidate_id,
        job_vacancy_id=vacancy_id,
    )

    if conversation:
        conversation.state = ConversationState.SCREENING
        conversation.current_question_index = 0

    await db.commit()

    await process_screening_queue(
        db=db,
        vacancy_id=vacancy_id,
        company_id=company_id,
        max_promote=0,
    )

    candidate_repo = CandidateRepository(db)
    candidate = await candidate_repo.get_by_id_str(candidate_id)
    candidate_name = candidate.name if candidate else "Candidato"

    invite_sent = False
    invite_channel = "none"

    job_repo = JobVacancyCRUDRepository(db)

    if conversation and conversation.phone_number:
        invite_channel = "whatsapp"
        try:
            from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory

            provider = await WhatsAppProviderFactory.get_provider(company_id, db)

            job = await job_repo.get_vacancy_by_id_and_company(vacancy_id, company_id)
            job_title = job.title if job else "a vaga"

            msg = (
                f"Olá, {candidate_name}! 👋\n\n"
                f"Temos uma ótima notícia! Você foi selecionado para "
                f"continuar o processo de triagem para *{job_title}*.\n\n"
                f"Vamos começar? Responda *SIM* para iniciarmos! 🚀"
            )
            await provider.send_text_message(conversation.phone_number, msg)
            invite_sent = True
        except Exception as e:
            logger.error(f"[OVERRIDE] Failed to send WhatsApp invite: {e}")

    if not invite_sent and candidate and candidate.email:
        invite_channel = "email"
        try:
            from app.domains.candidates.services.candidate_feedback_service import candidate_feedback_service

            job = await job_repo.get_vacancy_by_id_and_company(vacancy_id, company_id)
            job_title = job.title if job else "a vaga"
            company_name = getattr(job, "company_name", None) or "Nossa Empresa"

            screening_token = (vc.additional_data or {}).get("screening_invite_token")
            if not screening_token:
                import secrets as _secrets
                screening_token = _secrets.token_urlsafe(32)
                additional = dict(vc.additional_data or {})
                additional["screening_invite_token"] = screening_token
                vc.additional_data = additional
                await db.commit()

            screening_url = f"/triagem/{screening_token}"

            invite_sent = await candidate_feedback_service.send_gate_feedback(
                gate_level="screening_invited",
                candidate_email=candidate.email,
                candidate_name=candidate_name,
                vacancy_title=job_title,
                company_name=company_name,
                extra_context={"screening_url": screening_url},
            )
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"[OVERRIDE] Failed to dispatch invite: {e}")

    try:
        from app.domains.analytics.services.activity_service import ActivityService
        activity_service = ActivityService()

        await activity_service.create_activity(
            activity_type="recruiter_override_approve",
            title=f"Priorização Manual - {candidate_name}",
            description=(
                f"Recrutador priorizou candidato {candidate_name} da fila de espera. "
                f"Convite enviado via {invite_channel}."
            ),
            actor_id="recruiter",
            actor_name="Recrutador",
            actor_type="user",
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "invite_channel": invite_channel,
                "invite_sent": invite_sent,
            },
            category="pipeline",
        )
    except Exception as e:
        logger.warning(f"[OVERRIDE] Failed to create activity: {e}")

    return {
        "success": True,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "invite_channel": invite_channel,
        "invite_sent": invite_sent,
        "message": f"Candidato {candidate_name} priorizado com sucesso",
    }


from datetime import datetime


def register_all_handlers():
    """Register all handlers with the StageAutomationEngine."""
    from app.domains.automation.services.stage_automation_engine import TriggerType, stage_automation_engine

    stage_automation_engine.register_handler(TriggerType.SCREENING_COMPLETED, handle_screening_completed)
    stage_automation_engine.register_handler(TriggerType.INTERVIEW_SCHEDULED, handle_interview_scheduled)
    stage_automation_engine.register_handler(TriggerType.INTERVIEW_COMPLETED, handle_interview_completed)
    stage_automation_engine.register_handler(TriggerType.CANDIDATE_INACTIVE, handle_candidate_inactive)
    stage_automation_engine.register_handler(TriggerType.CANDIDATE_NO_SHOW, handle_candidate_no_show)
    stage_automation_engine.register_handler(TriggerType.OFFER_SENT, handle_offer_sent)
    stage_automation_engine.register_handler(TriggerType.CANDIDATE_HIRED, handle_candidate_hired)
    stage_automation_engine.register_handler(TriggerType.CANDIDATE_REJECTED, handle_candidate_rejected)
    stage_automation_engine.register_handler(TriggerType.ATS_SYNC, handle_ats_sync)
    stage_automation_engine.register_handler(TriggerType.STAGE_CHANGED, handle_stage_changed)
    stage_automation_engine.register_handler(TriggerType.JOB_PUBLISHED, handle_job_published)
    stage_automation_engine.register_handler(TriggerType.CANDIDATES_SOURCED, handle_candidates_sourced)
    stage_automation_engine.register_handler(TriggerType.SLOT_OPENED, handle_slot_opened)

    logger.info("[AUTOMATION] All handlers registered with StageAutomationEngine (including cross-domain cascades)")
