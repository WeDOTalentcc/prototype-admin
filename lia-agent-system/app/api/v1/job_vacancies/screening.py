from datetime import datetime
from typing import Any
from uuid import UUID

"""
Screening configuration routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Path

from ._shared import (  # noqa: F401
    VALID_SCREENING_STATUSES,
    derive_screening_status,
    get_current_user_or_demo,
    User,
    Depends,
    HTTPException,
    BaseModel,
    logger,
)
from app.domains.job_management.repositories.job_vacancy_screening_repository import JobVacancyScreeningRepository
from app.domains.job_management.dependencies import get_job_vacancy_screening_repo
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError
from app.shared.optimistic_lock import check_optimistic_lock

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ScreeningConfigStatus(BaseModel):
    enabled: bool = True
    paused_at: str | None = None
    paused_by: str | None = None
    pause_reason: str | None = None
    scheduled_end_date: str | None = None
    last_updated: str | None = None
    screening_status: str | None = "not_configured"


class ScreeningConfigChannel(BaseModel):
    enabled: bool = True
    label: str | None = None


class ScreeningConfigChannels(BaseModel):
    whatsapp: ScreeningConfigChannel | None = None
    chat_web: ScreeningConfigChannel | None = None
    phone: ScreeningConfigChannel | None = None


class ScreeningConfigSettings(BaseModel):
    min_score: int | None = 70
    response_timeout_hours: int | None = 48
    max_retries: int | None = 2


class ScreeningConfigMetrics(BaseModel):
    screened_count: int | None = 0
    completion_rate: float | None = 0
    average_rating: float | None = 4.2


class ScreeningConfigScheduling(BaseModel):
    auto_enabled: bool | None = True
    min_score_for_auto: int | None = 75
    calendar_provider: str | None = "Microsoft"
    available_hours: str | None = "9h-18h"
    interview_duration_min: int | None = 45


class ScreeningConfigFeedback(BaseModel):
    approved: str | None = "Parabéns! Você foi aprovado na triagem inicial."
    rejected: str | None = "Agradecemos sua participação. Infelizmente não seguiremos com sua candidatura neste momento."


class ScreeningConfigRequest(WeDoBaseModel):
    status: ScreeningConfigStatus | None = None
    channels: ScreeningConfigChannels | None = None
    settings: ScreeningConfigSettings | None = None
    metrics: ScreeningConfigMetrics | None = None
    scheduling: ScreeningConfigScheduling | None = None
    feedback_templates: ScreeningConfigFeedback | None = None
    wsi_skills: list[str] | None = []
    # GAP-05-004: Optimistic locking control field
    expected_updated_at: datetime | None = None


class ScreeningConfigResponse(BaseModel):
    job_id: str
    is_default: bool = False
    screening_status: str | None = "not_configured"
    status: dict[str, Any] | None = None
    channels: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    scheduling: dict[str, Any] | None = None
    feedback_templates: dict[str, Any] | None = None
    wsi_skills: list[str] | None = []
    updated_at: str | None = None


class ScreeningStatusUpdateRequest(WeDoBaseModel):
    screening_status: str
    pause_reason: str | None = None
    scheduled_end_date: str | None = None
    # GAP-05-004: Optimistic locking control field
    expected_updated_at: datetime | None = None


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/vagas/{job_id}/screening-config", response_model=ScreeningConfigResponse)
async def get_screening_config(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    repo: JobVacancyScreeningRepository = Depends(get_job_vacancy_screening_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get screening configuration for a job vacancy."""
    try:
        job = await repo.get_vacancy_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")

        config = job.screening_config or {}
        screening_status = derive_screening_status(config)

        return ScreeningConfigResponse(
            job_id=str(job_id),
            is_default=not bool(config),
            screening_status=screening_status,
            status=config.get("status", {"enabled": True, "last_updated": None}),
            channels=config.get("channels", {
                "whatsapp": {"enabled": True, "label": "WhatsApp"},
                "chat_web": {"enabled": True, "label": "Chat Web"},
                "phone": {"enabled": False, "label": "Ligação"}
            }),
            settings=config.get("settings", {"min_score": 70, "response_timeout_hours": 48, "max_retries": 2}),
            metrics=config.get("metrics", {"screened_count": 0, "completion_rate": 0, "average_rating": 4.2}),
            scheduling=config.get("scheduling", {
                "auto_enabled": True,
                "min_score_for_auto": 75,
                "calendar_provider": "Microsoft",
                "available_hours": "9h-18h",
                "interview_duration_min": 45
            }),
            feedback_templates=config.get("feedback_templates", {
                "approved": "Parabéns! Você foi aprovado na triagem inicial.",
                "rejected": "Agradecemos sua participação. Infelizmente não seguiremos com sua candidatura neste momento."
            }),
            wsi_skills=config.get("wsi_skills", []),
            updated_at=config.get("status", {}).get("last_updated")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening config: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/vagas/{job_id}/screening-config", response_model=ScreeningConfigResponse)
async def update_screening_config(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    config_data: ScreeningConfigRequest = ...,
    repo: JobVacancyScreeningRepository = Depends(get_job_vacancy_screening_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update screening configuration for a job vacancy."""
    try:
        job = await repo.get_vacancy_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")

        new_config = {}

        if config_data.status:
            new_config["status"] = config_data.status.model_dump(exclude_none=True)
            new_config["status"]["last_updated"] = datetime.utcnow().isoformat()

        if config_data.channels:
            new_config["channels"] = config_data.channels.model_dump(exclude_none=True)

        if config_data.settings:
            new_config["settings"] = config_data.settings.model_dump(exclude_none=True)

        if config_data.metrics:
            new_config["metrics"] = config_data.metrics.model_dump(exclude_none=True)

        if config_data.scheduling:
            new_config["scheduling"] = config_data.scheduling.model_dump(exclude_none=True)

        if config_data.feedback_templates:
            new_config["feedback_templates"] = config_data.feedback_templates.model_dump(exclude_none=True)

        if config_data.wsi_skills:
            new_config["wsi_skills"] = config_data.wsi_skills

        existing_config = job.screening_config or {}
        merged_config = {**existing_config, **new_config}

        job = await repo.update_screening_config(job, merged_config)

        # F3.O5 fix — derive screening_status from merged_config so the response
        # reflects the just-saved state (was returning hardcoded default "not_configured").
        screening_status = derive_screening_status(merged_config)

        logger.info(f"Screening config updated for job {job_id} (status={screening_status})")

        return ScreeningConfigResponse(
            job_id=str(job_id),
            is_default=False,
            screening_status=screening_status,
            status=merged_config.get("status"),
            channels=merged_config.get("channels"),
            settings=merged_config.get("settings"),
            metrics=merged_config.get("metrics"),
            scheduling=merged_config.get("scheduling"),
            feedback_templates=merged_config.get("feedback_templates"),
            wsi_skills=merged_config.get("wsi_skills", []),
            updated_at=merged_config.get("status", {}).get("last_updated")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening config: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.put("/vagas/{job_id}/screening-status", response_model=None)
async def update_screening_status(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    request: ScreeningStatusUpdateRequest = ...,
    repo: JobVacancyScreeningRepository = Depends(get_job_vacancy_screening_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update the screening status for a job vacancy."""
    if request.screening_status not in VALID_SCREENING_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid screening status: {request.screening_status}. Valid: {VALID_SCREENING_STATUSES}"
        )

    try:
        job = await repo.get_vacancy_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")

        existing_config = job.screening_config or {}
        existing_status = existing_config.get("status", {})

        now = datetime.utcnow().isoformat()

        existing_status["screening_status"] = request.screening_status
        existing_status["last_updated"] = now

        if request.screening_status == "active":
            existing_status["enabled"] = True
            existing_status["paused_at"] = None
            existing_status["paused_by"] = None
            existing_status["pause_reason"] = None
            if not existing_status.get("activated_at"):
                existing_status["activated_at"] = now
        elif request.screening_status == "paused":
            existing_status["enabled"] = False
            existing_status["paused_at"] = now
            existing_status["paused_by"] = current_user.email if hasattr(current_user, "email") else "system"
            existing_status["pause_reason"] = request.pause_reason or "Pausado manualmente"
        elif request.screening_status == "completed":
            existing_status["enabled"] = False
            existing_status["completed_at"] = now
        elif request.screening_status == "not_started":
            existing_status["enabled"] = False
            existing_status["paused_at"] = None

        if request.scheduled_end_date:
            existing_status["scheduled_end_date"] = request.scheduled_end_date

        existing_config["status"] = existing_status

        job = await repo.update_screening_status(job, existing_config)

        logger.info(f"Screening status updated to '{request.screening_status}' for job {job_id}")

        return {
            "job_id": str(job_id),
            "screening_status": request.screening_status,
            "status": existing_config.get("status"),
            "updated_at": now
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening status: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
