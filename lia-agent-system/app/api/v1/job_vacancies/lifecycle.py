"""
Lifecycle routes: publish, confirm-global-search, sourcing-status,
bulk operations (pause, resume, archive, assign-recruiter, change-status),
close vacancy, duplicate/clone helpers.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from ._shared import (  # noqa: F401
    VALID_JOB_STATUSES,
    ALLOWED_STATUS_TRANSITIONS,
    BulkActionError,
    BulkActionResponse,
    BulkActionRequest,
    BulkAssignRecruiterRequest,
    BulkChangeStatusRequest,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
    User,
    Depends,
    HTTPException,
    teams_service,
    notification_service,
    BaseModel,
    logger,
)
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service
from app.domains.job_management.dependencies import get_job_vacancy_lifecycle_repo
from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import JobVacancyLifecycleRepository
from app.domains.communication.services.communication_service import CommunicationService, get_communication_service
from app.shared.security.require_company_id import require_company_id
from app.domains.sourcing.services.sourcing_pipeline_service import sourcing_pipeline_service
from app.domains.job_management.services.job_status_webhook_service import job_status_webhook_service
from app.services.notification_service import NotificationChannel, NotificationType
from app.shared.types import WeDoBaseModel
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class JobPublishRequest(WeDoBaseModel):
    """Request to publish a job vacancy (simple version)."""
    trigger_sourcing: bool = True


class JobPublishResponse(BaseModel):
    success: bool
    job_id: str
    status: str
    message: str
    sourcing_result: dict | None = None


class JobPublishRequestV2(BaseModel):
    """Full publish request with sourcing options."""
    expand_to_global: bool = False
    user_credits: int = 100


class JobPublishResponseV2(BaseModel):
    success: bool
    job_id: str
    job_title: str
    status: str
    sourcing_results: dict[str, Any]
    message: str


class ConfirmGlobalSearchRequest(WeDoBaseModel):
    credits_to_use: int = 20


class ConfirmGlobalSearchResponse(BaseModel):
    success: bool
    candidates_found: int
    candidates_added: int
    credits_used: int
    message: str


class ConfirmGlobalSearchResponseV2(BaseModel):
    success: bool
    candidates_found: int
    candidates_added: int
    credits_deducted: int
    message: str
    error: str | None = None


class SourcingStatusResponseSimple(BaseModel):
    job_id: str
    total_candidates: int
    qualified_candidates: int
    pipeline_status: str
    recommended_action: str | None = None


class SourcingStatusResponseV2(BaseModel):
    found: bool
    job_id: str | None = None
    job_title: str | None = None
    total_candidates: int = 0
    qualified_candidates: int = 0
    qualified_ratio: float = 0.0
    needs_more_candidates: bool = False
    days_open: int = 0
    pipeline_status: str = "idle"
    recommended_action: str | None = None
    min_candidates_target: int = 10
    error: str | None = None


# ─── Publish (job-vacancies prefix) ──────────────────────────────────────────

@router.post("/job-vacancies/{job_id}/publish", response_model=JobPublishResponse)
async def publish_job_vacancy_simple(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    request: JobPublishRequest = JobPublishRequest(),
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Publish a job vacancy and trigger automated sourcing (simple version)."""
    company_id = get_user_company_id(current_user)

    job = await repo.get_vacancy_by_id_and_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    old_status = job.status
    await repo.publish_vacancy(job)

    from app.domains.job_management.services.job_audit_service import job_audit_service
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)
    await job_audit_service.log_publication(
        job_id=str(job_id),
        platform="internal",
        changed_by=changed_by,
        company_id=company_id,
        db=repo.db,
        extra_data={"old_status": old_status, "trigger_sourcing": request.trigger_sourcing},
    )

    try:
        from app.shared.services.event_dispatcher import event_dispatcher
        await event_dispatcher.on_job_status_changed(
            job_id=str(job_id),
            company_id=company_id,
            new_status="Ativa",
            previous_status=old_status,
            changed_by=changed_by,
            job_title=job.title,
            # Guard: signal to automation handler that sourcing is handled inline
            sourcing_already_triggered=request.trigger_sourcing,
        )
    except Exception as e:
        logger.warning(f"Event dispatch failed for job publish: {e}")

    sourcing_result = None
    if request.trigger_sourcing:
        sourcing_result = await sourcing_pipeline_service.run_post_publish_sourcing(
            db=repo.db,
            job_id=str(job_id),
            user_credits=100,
            expand_to_global=False
        )

        if sourcing_result.get("local_candidates_added", 0) > 0:
            await notification_service.create_notification(
                db=repo.db,
                user_id=str(current_user.id),
                title="Candidatos Encontrados",
                message=f"LIA encontrou {sourcing_result['local_candidates_added']} candidatos para {job.title}",
                notification_type=NotificationType.INFO,
                channels=[NotificationChannel.APP, NotificationChannel.TEAMS],
                related_job_id=str(job_id),
                action_url=f"/jobs/{job_id}/pipeline",
                action_label="Ver Pipeline"
            )

    return JobPublishResponse(
        success=True,
        job_id=str(job_id),
        status=job.status,
        message=f"Vaga '{job.title}' publicada com sucesso!",
        sourcing_result=sourcing_result
    )


@router.post("/job-vacancies/{job_id}/confirm-global-search", response_model=ConfirmGlobalSearchResponse)
async def confirm_global_search_simple(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    request: ConfirmGlobalSearchRequest = ...,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Confirm global search expansion using Pearch AI."""
    company_id = get_user_company_id(current_user)

    job = await repo.get_vacancy_by_id_and_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    search_result = await sourcing_pipeline_service.confirm_global_search(
        db=repo.db,
        job_id=str(job_id),
        user_id=str(current_user.id),
        credits_to_use=request.credits_to_use
    )

    if not search_result.get("success"):
        raise HTTPException(status_code=500, detail=search_result.get("error", "Erro na busca global"))

    return ConfirmGlobalSearchResponse(
        success=True,
        candidates_found=search_result.get("candidates_found", 0),
        candidates_added=search_result.get("candidates_added", 0),
        credits_used=search_result.get("credits_deducted", 0),
        message=f"Encontrados {search_result.get('candidates_added', 0)} candidatos via Pearch AI"
    )


@router.get("/job-vacancies/{job_id}/sourcing-status", response_model=SourcingStatusResponseSimple)
async def get_sourcing_status_simple(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Get current sourcing status for a job (simple version)."""
    company_id = get_user_company_id(current_user)

    job = await repo.get_vacancy_by_id_and_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    status = await sourcing_pipeline_service.get_job_pipeline_status(
        db=repo.db,
        job_id=str(job_id)
    )

    if not status:
        raise HTTPException(status_code=404, detail="Status do pipeline não encontrado")

    return SourcingStatusResponseSimple(
        job_id=str(job_id),
        total_candidates=status.total_candidates,
        qualified_candidates=status.qualified_candidates,
        pipeline_status=status.pipeline_status,
        recommended_action=status.recommended_action
    )


# ─── Publish (jobs prefix — full version) ─────────────────────────────────────

async def _send_candidates_added_notification(
    db,
    user_id: str,
    job_id: str,
    job_title: str,
    candidates_added: int,
    recruiter_email: str,
    is_global: bool = False,
    company_id: str | None = None,
) -> None:
    """Send notification when candidates are added to pipeline."""
    try:
        source_type = "busca global" if is_global else "busca local"
        notification_message = f"LIA adicionou {candidates_added} candidatos ao pipeline de {job_title}. Aprove para iniciar triagem."

        await notification_service.create_notification(
            user_id=user_id,
            title=f"Candidatos adicionados - {job_title}",
            message=notification_message,
            notification_type=NotificationType.ACTION_REQUIRED,
            category="sourcing",
            source_agent="sourcing_pipeline",
            source_trigger="job_publish",
            related_job_id=job_id,
            action_url=f"/jobs/{job_id}",
            action_label="Ver Pipeline",
            channels=[NotificationChannel.IN_APP.value, NotificationChannel.TEAMS.value, NotificationChannel.EMAIL.value],
            metadata={
                "candidates_added": candidates_added,
                "source_type": source_type,
                "job_title": job_title,
                "recipient_email": recruiter_email,
                "action_url": f"/jobs/{job_id}"
            },
            db=db
        )

        teams_message = (
            f"**Candidatos Adicionados**\n\n"
            f"LIA adicionou **{candidates_added} candidatos** ao pipeline de **{job_title}** via {source_type}.\n\n"
            f"Aprove para iniciar triagem."
        )

        # Resolve per-tenant webhook URL so DB-configured URL drives delivery when env var is absent
        resolved_webhook_url: str | None = None
        if company_id:
            try:
                from app.api.v1.integrations import _get_tenant_teams_webhook_url
                resolved_webhook_url, _ = await _get_tenant_teams_webhook_url(company_id, db)
            except Exception as _url_err:
                logger.debug("Could not resolve per-tenant Teams URL: %s", _url_err)

        await teams_service.send_message(
            text=teams_message,
            title=f"Pipeline Atualizado - {job_title}",
            webhook_url=resolved_webhook_url,
        )

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Notification sent: {candidates_added} candidates added to {job_title}")

    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


@router.post("/job-vacancies/{job_id}/unpublish", response_model=JobPublishResponse)
async def unpublish_job_vacancy(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user),
company_id: str = Depends(require_company_id)):
    """Phase C.2 — clear published_* flags. Symmetric to /publish.

    Idempotent: returns 200 with {changed: false} when the vacancy was
    already unpublished. Multi-tenant: company_id from JWT, never payload.
    Audit event emitted only when state actually changed.
    """
    company_id = get_user_company_id(current_user)

    job = await repo.get_vacancy_by_id_and_company(job_id, company_id)
    if not job:
        # 404, not 403 — avoid leaking existence cross-tenant.
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    job, changed = await repo.unpublish_vacancy(job)

    if changed:
        from app.domains.job_management.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)
        try:
            await job_audit_service.log_publication(
                job_id=str(job_id),
                platform="internal",
                changed_by=changed_by,
                company_id=company_id,
                db=repo.db,
                extra_data={"action": "unpublish"},
            )
        except Exception as e:
            logger.warning(f"Audit log failed for job unpublish: {e}")

    return JobPublishResponse(
        success=True,
        job_id=str(job_id),
        status=job.status,
        published=False,
        message="Vaga despublicada" if changed else "Vaga já estava despublicada",
        sourcing_result=None,
    )


@router.post("/jobs/{job_id}/publish", response_model=JobPublishResponseV2)
async def publish_job_vacancy_v2(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    request: JobPublishRequestV2 = JobPublishRequestV2(),
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Publish a job vacancy and trigger initial sourcing pipeline (full version)."""
    try:
        logger.info(f"Publishing job vacancy: {job_id}")

        user_company = get_user_company_id(current_user)

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        old_status = job_vacancy.status
        await repo.publish_vacancy_v2(job_vacancy)

        logger.info(f"Job vacancy status changed: {job_id} ({old_status} -> Ativa)")

        try:
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                company_id=user_company,
                db=repo.db,
                changed_by=str(current_user.email) if hasattr(current_user, "email") else str(current_user.id),
                job_title=job_vacancy.title
            )
        except Exception as webhook_error:
            logger.warning(f"Webhook dispatch failed (non-blocking): {webhook_error}")

        sourcing_results = await sourcing_pipeline_service.run_post_publish_sourcing(
            db=repo.db,
            job_id=str(job_id),
            user_credits=request.user_credits,
            expand_to_global=request.expand_to_global
        )

        total_added = sourcing_results.get("total_candidates_added", 0)
        if total_added > 0:
            await _send_candidates_added_notification(
                db=repo.db,
                user_id=str(current_user.id),
                job_id=str(job_id),
                job_title=job_vacancy.title,
                candidates_added=total_added,
                recruiter_email=job_vacancy.recruiter_email or current_user.email,
                company_id=user_company,
            )

        message = f"Vaga '{job_vacancy.title}' publicada com sucesso!"
        if total_added > 0:
            message += f" LIA adicionou {total_added} candidatos ao pipeline."

        if sourcing_results.get("awaiting_global_confirmation"):
            message += " Busca global disponível para expandir o pipeline."

        return JobPublishResponseV2(
            success=True,
            job_id=str(job_id),
            job_title=job_vacancy.title,
            status="Ativa",
            sourcing_results=sourcing_results,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing job vacancy: {e}", exc_info=True)
        raise


@router.post("/jobs/{job_id}/confirm-global-search", response_model=ConfirmGlobalSearchResponseV2)
async def confirm_global_search_v2(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    request: ConfirmGlobalSearchRequest = ...,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Confirm global search expansion for a job vacancy (full version)."""
    try:
        logger.info(f"Confirming global search for job: {job_id}")

        user_company = get_user_company_id(current_user)

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        if job_vacancy.status != "Ativa":
            raise HTTPException(status_code=400, detail="Job vacancy must be published (status 'Ativa') before global search")

        search_result = await sourcing_pipeline_service.confirm_global_search(
            db=repo.db,
            job_id=str(job_id),
            user_id=str(current_user.id),
            credits_to_use=request.credits_to_use
        )

        if search_result.get("success") and search_result.get("candidates_added", 0) > 0:
            await _send_candidates_added_notification(
                db=repo.db,
                user_id=str(current_user.id),
                job_id=str(job_id),
                job_title=job_vacancy.title,
                candidates_added=search_result["candidates_added"],
                recruiter_email=job_vacancy.recruiter_email or current_user.email,
                is_global=True,
                company_id=user_company,
            )

        message = ""
        if search_result.get("success"):
            message = f"Busca global concluída! {search_result['candidates_added']} candidatos adicionados ao pipeline."
        else:
            message = f"Busca global falhou: {search_result.get('error', 'Unknown error')}"

        return ConfirmGlobalSearchResponseV2(
            success=search_result.get("success", False),
            candidates_found=search_result.get("candidates_found", 0),
            candidates_added=search_result.get("candidates_added", 0),
            credits_deducted=search_result.get("credits_deducted", 0),
            message=message,
            error=search_result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming global search: {e}", exc_info=True)
        raise


@router.get("/jobs/{job_id}/sourcing-status", response_model=SourcingStatusResponseV2)
async def get_sourcing_status_v2(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """Get current sourcing progress and candidates found for a job (full version)."""
    try:
        logger.info(f"Getting sourcing status for job: {job_id}")

        user_company = get_user_company_id(current_user)

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        status = await sourcing_pipeline_service.get_sourcing_status(
            db=repo.db,
            job_id=str(job_id)
        )

        if not status.get("found"):
            return SourcingStatusResponseV2(
                found=False,
                error=status.get("error", "Job not found in pipeline")
            )

        return SourcingStatusResponseV2(
            found=True,
            job_id=status.get("job_id"),
            job_title=status.get("job_title"),
            total_candidates=status.get("total_candidates", 0),
            qualified_candidates=status.get("qualified_candidates", 0),
            qualified_ratio=status.get("qualified_ratio", 0.0),
            needs_more_candidates=status.get("needs_more_candidates", False),
            days_open=status.get("days_open", 0),
            pipeline_status=status.get("pipeline_status", "idle"),
            recommended_action=status.get("recommended_action"),
            min_candidates_target=status.get("min_candidates_target", 10)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sourcing status: {e}", exc_info=True)
        raise


# ─── Close vacancy ────────────────────────────────────────────────────────────

@router.post("/{vacancy_id}/close", response_model=None)
async def close_vacancy(
    vacancy_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    request: Request = ...,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_user_or_demo),
    activity_svc: ActivityService = Depends(get_activity_service),
    comm_svc: CommunicationService = Depends(get_communication_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    """Close a vacancy. Pass close_reason='not_filled' when no hire was made."""
    try:
        company_id = get_user_company_id(current_user)
        data = await request.json()

        hired_candidate_id = data.get("hired_candidate_id")
        close_reason = data.get("close_reason", "filled")
        hired_notification = data.get("hired_notification", {})
        other_notifications = data.get("other_notifications", {})

        if not hired_candidate_id and close_reason != "not_filled":
            raise HTTPException(status_code=400, detail="hired_candidate_id is required when close_reason is 'filled'")

        vacancy = await repo.get_vacancy_by_uuid_str(vacancy_id)

        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        from app.domains.communication.services.communication_service import (
            MessageChannel,
            MessageType,
        )
        communication_service = comm_svc

        notifications_sent = {"hired": None, "others": []}

        if hired_notification.get("channel") and hired_notification.get("message"):
            try:
                channel_str = hired_notification["channel"]
                channel = MessageChannel.EMAIL if channel_str == "email" else MessageChannel.WHATSAPP

                result = await communication_service.send_message(
                    company_id=company_id,
                    candidate_id=hired_candidate_id,
                    candidate_email=hired_notification.get("candidate_email"),
                    candidate_phone=hired_notification.get("candidate_phone"),
                    message_type=MessageType.GENERAL,
                    channel=channel,
                    subject=hired_notification.get("subject", ""),
                    body=hired_notification["message"],
                    job_id=vacancy_id,
                    skip_policy_checks=True,
                    db=repo.db
                )
                notifications_sent["hired"] = {
                    "candidate_id": hired_candidate_id,
                    "channel": channel_str,
                    "success": result.get("success", True)
                }
            except Exception as e:
                logger.error(f"Failed to send hired notification: {e}")
                notifications_sent["hired"] = {"error": str(e)}

        other_candidate_ids = other_notifications.get("candidate_ids", [])
        if other_candidate_ids and other_notifications.get("message"):
            channel_str = other_notifications.get("channel", "email")
            channel = MessageChannel.EMAIL if channel_str == "email" else MessageChannel.WHATSAPP

            for cand_id in other_candidate_ids:
                try:
                    result = await communication_service.send_message(
                        company_id=company_id,
                        candidate_id=cand_id,
                        candidate_email=other_notifications.get("candidate_emails", {}).get(cand_id),
                        candidate_phone=other_notifications.get("candidate_phones", {}).get(cand_id),
                        message_type=MessageType.PROCESS_CLOSED,
                        channel=channel,
                        subject=other_notifications.get("subject", ""),
                        body=other_notifications["message"],
                        job_id=vacancy_id,
                        skip_policy_checks=True,
                        db=repo.db
                    )
                    notifications_sent["others"].append({
                        "candidate_id": cand_id,
                        "channel": channel_str,
                        "success": result.get("success", True)
                    })
                except Exception as e:
                    logger.error(f"Failed to send vacancy closed notification to {cand_id}: {e}")
                    notifications_sent["others"].append({
                        "candidate_id": cand_id,
                        "error": str(e)
                    })

        await repo.close_vacancy(vacancy)

        try:
            from app.shared.services.event_dispatcher import event_dispatcher
            await event_dispatcher.on_job_status_changed(
                job_id=vacancy_id,
                company_id=company_id,
                new_status="Concluída",
                previous_status="Ativa",
                changed_by=str(current_user.id),
                job_title=vacancy.title,
                hired_candidate_id=hired_candidate_id
            )
        except Exception as e:
            logger.warning(f"Event dispatch failed for job close: {e}")

        try:
            await activity_svc.create_activity(
                activity_type="vacancy_closed",
                title=f"Vaga Fechada: {vacancy.title}",
                description=f"Candidato contratado. {len(other_candidate_ids)} candidatos notificados." if hired_candidate_id else f"Vaga encerrada sem contratação. {len(other_candidate_ids)} candidatos notificados.",
                actor_id="system",
                actor_name="LIA",
                actor_type="system",
                target_id=vacancy_id,
                target_type="vacancy",
                extra_data={
                    "hired_candidate_id": hired_candidate_id,
                    "notified_count": len(other_candidate_ids),
                    "company_id": company_id,
                    "close_reason": close_reason
                },
                category="recruitment"
            )
        except Exception as e:
            logger.warning(f"Failed to log vacancy closed activity: {e}")

        return {
            "success": True,
            "vacancy_id": vacancy_id,
            "status": "Concluída",
            "hired_candidate_id": hired_candidate_id,
            "close_reason": close_reason,
            "notifications_sent": notifications_sent
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing vacancy: {e}")
        await repo.rollback()
        raise


# ─── Bulk operations ─────────────────────────────────────────────────────────

@router.post("/job-vacancies/bulk/pause", response_model=BulkActionResponse)
async def bulk_pause_job_vacancies(
    request: BulkActionRequest,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Pause multiple job vacancies."""
    from app.domains.job_management.services.job_audit_service import job_audit_service

    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)

    successful = 0
    failed = 0
    errors: list[BulkActionError] = []

    for job_id in request.job_ids:
        try:
            job = await repo.get_vacancy_by_id_and_company(job_id, company_id)

            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue

            if job.status != "Ativa":
                errors.append(BulkActionError(
                    job_id=str(job_id),
                    error_message=f"Apenas vagas ativas podem ser pausadas. Status atual: {job.status}"
                ))
                failed += 1
                continue

            old_status = job.status
            await repo.update_vacancy_status(job, "Pausada")

            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Pausada",
                changed_by=changed_by,
                company_id=company_id,
                db=repo.db,
                extra_data={"action": "bulk_pause"}
            )

            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Pausada",
                company_id=company_id,
                db=repo.db,
                changed_by=changed_by,
                job_title=job.title
            )

            try:
                from app.shared.services.event_dispatcher import event_dispatcher
                await event_dispatcher.on_job_status_changed(
                    job_id=str(job_id),
                    company_id=company_id,
                    new_status="Pausada",
                    previous_status=old_status,
                    changed_by=changed_by,
                    job_title=job.title
                )
            except Exception as evt_e:
                logger.warning(f"Event dispatch failed for job pause: {evt_e}")

            successful += 1

        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1

    logger.info(f"Bulk pause: {successful} succeeded, {failed} failed for company {company_id}")

    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/resume", response_model=BulkActionResponse)
async def bulk_resume_job_vacancies(
    request: BulkActionRequest,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Resume multiple paused job vacancies."""
    from app.domains.job_management.services.job_audit_service import job_audit_service

    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)

    successful = 0
    failed = 0
    errors: list[BulkActionError] = []

    for job_id in request.job_ids:
        try:
            job = await repo.get_vacancy_by_id_and_company(job_id, company_id)

            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue

            if job.status != "Pausada":
                errors.append(BulkActionError(
                    job_id=str(job_id),
                    error_message=f"Apenas vagas pausadas podem ser retomadas. Status atual: {job.status}"
                ))
                failed += 1
                continue

            old_status = job.status
            await repo.update_vacancy_status(job, "Ativa")

            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                changed_by=changed_by,
                company_id=company_id,
                db=repo.db,
                extra_data={"action": "bulk_resume"}
            )

            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                company_id=company_id,
                db=repo.db,
                changed_by=changed_by,
                job_title=job.title
            )

            successful += 1

        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1

    logger.info(f"Bulk resume: {successful} succeeded, {failed} failed for company {company_id}")

    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/archive", response_model=BulkActionResponse)
async def bulk_archive_job_vacancies(
    request: BulkActionRequest,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Archive multiple job vacancies (soft delete)."""
    from app.domains.job_management.services.job_audit_service import job_audit_service

    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)

    successful = 0
    failed = 0
    errors: list[BulkActionError] = []

    for job_id in request.job_ids:
        try:
            job = await repo.get_vacancy_by_id_and_company(job_id, company_id)

            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue

            if job.status == "Arquivada":
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga já está arquivada"))
                failed += 1
                continue

            old_status = job.status
            await repo.update_vacancy_status(job, "Arquivada")

            await job_audit_service.log_archive(
                job_id=str(job_id),
                changed_by=changed_by,
                company_id=company_id,
                db=repo.db,
                reason="Arquivamento em lote"
            )

            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Arquivada",
                company_id=company_id,
                db=repo.db,
                changed_by=changed_by,
                job_title=job.title
            )

            successful += 1

        except Exception as e:
            logger.error(f"Error archiving job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1

    logger.info(f"Bulk archive: {successful} succeeded, {failed} failed for company {company_id}")

    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/assign-recruiter", response_model=BulkActionResponse)
async def bulk_assign_recruiter(
    request: BulkAssignRecruiterRequest,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Assign a recruiter to multiple job vacancies."""
    from app.domains.job_management.services.job_audit_service import job_audit_service

    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)

    successful = 0
    failed = 0
    errors: list[BulkActionError] = []

    for job_id in request.job_ids:
        try:
            job = await repo.get_vacancy_by_id_and_company(job_id, company_id)

            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue

            old_recruiter = job.recruiter
            old_recruiter_email = job.recruiter_email

            await repo.update_vacancy_recruiter(job, request.recruiter_name, request.recruiter_email)

            changes = {}
            if old_recruiter != request.recruiter_name:
                changes["recruiter"] = {"old": old_recruiter, "new": request.recruiter_name}
            if old_recruiter_email != request.recruiter_email:
                changes["recruiter_email"] = {"old": old_recruiter_email, "new": request.recruiter_email}

            if changes:
                await job_audit_service.log_update(
                    job_id=str(job_id),
                    changes=changes,
                    changed_by=changed_by,
                    company_id=company_id,
                    db=repo.db
                )

            successful += 1

        except Exception as e:
            logger.error(f"Error assigning recruiter to job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1

    # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
    logger.info(f"Bulk assign recruiter ({request.recruiter_email}): {successful} succeeded, {failed} failed")

    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/change-status", response_model=BulkActionResponse)
async def bulk_change_status(
    request: BulkChangeStatusRequest,
    repo: JobVacancyLifecycleRepository = Depends(get_job_vacancy_lifecycle_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Change status for multiple job vacancies with transition validation."""
    from app.domains.job_management.services.job_audit_service import job_audit_service

    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)

    if request.new_status not in VALID_JOB_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido: '{request.new_status}'. Status válidos: {', '.join(VALID_JOB_STATUSES)}"
        )

    successful = 0
    failed = 0
    errors: list[BulkActionError] = []

    for job_id in request.job_ids:
        try:
            job = await repo.get_vacancy_by_id_and_company(job_id, company_id)

            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue

            old_status = job.status or "Rascunho"

            if old_status == request.new_status:
                errors.append(BulkActionError(
                    job_id=str(job_id),
                    error_message=f"Vaga já está com status '{request.new_status}'"
                ))
                failed += 1
                continue

            allowed_transitions = ALLOWED_STATUS_TRANSITIONS.get(old_status, [])
            if request.new_status not in allowed_transitions:
                errors.append(BulkActionError(
                    job_id=str(job_id),
                    error_message=f"Transição de status não permitida: '{old_status}' -> '{request.new_status}'"
                ))
                failed += 1
                continue

            await repo.update_vacancy_status(job, request.new_status)

            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status=request.new_status,
                changed_by=changed_by,
                company_id=company_id,
                db=repo.db,
                extra_data={"action": "bulk_change_status"}
            )

            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status=request.new_status,
                company_id=company_id,
                db=repo.db,
                changed_by=changed_by,
                job_title=job.title
            )

            successful += 1

        except Exception as e:
            logger.error(f"Error changing status for job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1

    logger.info(f"Bulk change status to '{request.new_status}': {successful} succeeded, {failed} failed")

    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )
