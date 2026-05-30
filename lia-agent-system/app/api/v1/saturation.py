import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.candidate import VacancyCandidate
from app.models.company import CompanyProfile
from app.models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN


# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
router = APIRouter()
logger = logging.getLogger(__name__)

EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
DEFAULT_SATURATION_THRESHOLD = 20
DEFAULT_UNLOCK_INCREMENT = 10
DEFAULT_UNLOCK_HOURS = 24

ORGANIC_ORIGINS = ('web', 'whatsapp')
SOURCING_ORIGINS = ('sourcing', 'ats')


class ChannelCounts(BaseModel):
    web: int = 0
    whatsapp: int = 0
    sourcing: int = 0
    ats: int = 0


class ChannelSaturation(BaseModel):
    count: int = 0
    threshold: int = DEFAULT_SATURATION_THRESHOLD
    is_saturated: bool = False
    slots_remaining: int = DEFAULT_SATURATION_THRESHOLD
    percentage: float = 0.0


class SaturationSettingsRequest(WeDoBaseModel):
    threshold_web: int | None = Field(None, ge=1, le=500)
    threshold_sourcing: int | None = Field(None, ge=1, le=500)
    unlock_increment: int | None = Field(None, ge=1, le=100)
    unlock_hours: int | None = Field(None, ge=1, le=168)


class SaturationSettingsResponse(BaseModel):
    company_id: str
    threshold_web: int
    threshold_sourcing: int
    unlock_increment: int
    unlock_hours: int
    updated_at: datetime | None = None


class SaturationStatusResponse(BaseModel):
    job_id: str
    approved_count: int
    saturation_threshold: int
    is_saturated: bool
    slots_remaining: int
    recommendation: str
    saturation_percentage: float
    queued_count: int
    last_screened_at: datetime | None = None
    saturation_disabled_until: datetime | None = None
    counts_by_channel: ChannelCounts
    organic: ChannelSaturation
    sourcing: ChannelSaturation
    threshold_web: int
    threshold_sourcing: int
    unlock_increment: int
    unlock_hours: int


class UnlockPipelineRequest(WeDoBaseModel):
    action: str = Field(..., pattern="^(increase_threshold|disable_temporarily)$")
    new_threshold: int | None = Field(None, ge=5, le=500)
    disable_hours: int | None = Field(None, ge=1)


class UnlockPipelineResponse(BaseModel):
    success: bool
    message: str
    new_threshold: int | None = None
    saturation_disabled_until: datetime | None = None


def _get_company_saturation_defaults(company: object | None) -> dict:
    if company and company.additional_data:
        sat = company.additional_data.get("saturation_settings", {})
        return {
            "threshold_web": sat.get("threshold_web", DEFAULT_SATURATION_THRESHOLD),
            "threshold_sourcing": sat.get("threshold_sourcing", DEFAULT_SATURATION_THRESHOLD),
            "unlock_increment": sat.get("unlock_increment", DEFAULT_UNLOCK_INCREMENT),
            "unlock_hours": sat.get("unlock_hours", DEFAULT_UNLOCK_HOURS),
        }
    return {
        "threshold_web": DEFAULT_SATURATION_THRESHOLD,
        "threshold_sourcing": DEFAULT_SATURATION_THRESHOLD,
        "unlock_increment": DEFAULT_UNLOCK_INCREMENT,
        "unlock_hours": DEFAULT_UNLOCK_HOURS,
    }


def _resolve_thresholds(vacancy_governance: dict, company_defaults: dict) -> dict:
    return {
        "threshold_web": vacancy_governance.get("threshold_web", company_defaults["threshold_web"]),
        "threshold_sourcing": vacancy_governance.get("threshold_sourcing", company_defaults["threshold_sourcing"]),
        "unlock_increment": vacancy_governance.get("unlock_increment", company_defaults["unlock_increment"]),
        "unlock_hours": vacancy_governance.get("unlock_hours", company_defaults["unlock_hours"]),
    }


async def _find_company(db: AsyncSession, company_id: str):
    try:
        from uuid import UUID as _UUID
        company_uuid = _UUID(company_id)
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == company_uuid)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
        )
        company = result.scalar_one_or_none()
        if company:
            return company
    except (ValueError, AttributeError):
        pass
    result2 = await db.execute(
        select(CompanyProfile).where(CompanyProfile.is_default).limit(1)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    )
    return result2.scalar_one_or_none()


@router.get("/settings/saturation", response_model=SaturationSettingsResponse, tags=["saturation"])
async def get_saturation_settings(
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id from JWT via require_company_id (canonical)
    company = await _find_company(db, company_id)
    defaults = _get_company_saturation_defaults(company)

    return SaturationSettingsResponse(
        company_id=company_id,
        threshold_web=defaults["threshold_web"],
        threshold_sourcing=defaults["threshold_sourcing"],
        unlock_increment=defaults["unlock_increment"],
        unlock_hours=defaults["unlock_hours"],
        updated_at=company.updated_at if company else None,
    )


@router.put("/settings/saturation", response_model=SaturationSettingsResponse, tags=["saturation"])
async def update_saturation_settings(
    request: SaturationSettingsRequest,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id from JWT via require_company_id (canonical)
    company = await _find_company(db, company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")

    additional = dict(company.additional_data or {})
    sat = additional.get("saturation_settings", {})

    if request.threshold_web is not None:
        sat["threshold_web"] = request.threshold_web
    if request.threshold_sourcing is not None:
        sat["threshold_sourcing"] = request.threshold_sourcing
    if request.unlock_increment is not None:
        sat["unlock_increment"] = request.unlock_increment
    if request.unlock_hours is not None:
        sat["unlock_hours"] = request.unlock_hours

    additional["saturation_settings"] = sat
    company.additional_data = additional
    company.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(company)

    defaults = _get_company_saturation_defaults(company)

    return SaturationSettingsResponse(
        company_id=company_id,
        threshold_web=defaults["threshold_web"],
        threshold_sourcing=defaults["threshold_sourcing"],
        unlock_increment=defaults["unlock_increment"],
        unlock_hours=defaults["unlock_hours"],
        updated_at=company.updated_at,
    )


@router.get("/job-vacancies/{job_id}/saturation-status", response_model=SaturationStatusResponse, tags=["saturation"])
async def get_saturation_status(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    company = await _find_company(db, str(vacancy.company_id))

    company_defaults = _get_company_saturation_defaults(company)
    governance_rules = vacancy.governance_rules or {}
    resolved = _resolve_thresholds(governance_rules, company_defaults)

    threshold_web = resolved["threshold_web"]
    threshold_sourcing = resolved["threshold_sourcing"]
    unlock_increment = resolved["unlock_increment"]
    unlock_hours = resolved["unlock_hours"]

    legacy_threshold = governance_rules.get(
        "saturation_threshold",
        threshold_web + threshold_sourcing,
    )

    active_filter = and_(
        VacancyCandidate.vacancy_id == job_id,
        not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
    )

    channel_counts_result = await db.execute(
        select(  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin == "web"
            ).label("web"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin == "whatsapp"
            ).label("whatsapp"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin == "sourcing"
            ).label("sourcing"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin == "ats"
            ).label("ats"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin.is_(None)
            ).label("unknown"),
        ).where(active_filter)
    )
    row = channel_counts_result.one()
    web_count = row.web or 0
    whatsapp_count = row.whatsapp or 0
    sourcing_count = row.sourcing or 0
    ats_count = row.ats or 0
    unknown_count = row.unknown or 0

    organic_count = web_count + whatsapp_count + unknown_count
    source_count = sourcing_count + ats_count
    total_active = organic_count + source_count

    queued_result = await db.execute(
        select(func.count(VacancyCandidate.id)).where(  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
            and_(
                VacancyCandidate.vacancy_id == job_id,
                VacancyCandidate.status.in_(('sourced', 'awaiting_screening')),
            )
        )
    )
    queued_count = queued_result.scalar() or 0

    last_screened_result = await db.execute(
        select(func.max(VacancyCandidate.updated_at)).where(  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
            and_(
                VacancyCandidate.vacancy_id == job_id,
                not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
                not_(VacancyCandidate.status.in_(('sourced', 'awaiting_screening')))
            )
        )
    )
    last_screened_at = last_screened_result.scalar()

    disabled_until_str = governance_rules.get("saturation_disabled_until")
    saturation_disabled_until = None
    bypass_active = False
    if disabled_until_str:
        try:
            saturation_disabled_until = datetime.fromisoformat(disabled_until_str)
            if saturation_disabled_until > datetime.utcnow():
                bypass_active = True
        except (ValueError, TypeError):
            pass

    organic_saturated = organic_count >= threshold_web and not bypass_active
    sourcing_saturated = source_count >= threshold_sourcing and not bypass_active
    is_saturated = organic_saturated or sourcing_saturated

    slots_remaining = max(0, (threshold_web - organic_count)) + max(0, (threshold_sourcing - source_count))
    total_threshold = threshold_web + threshold_sourcing
    saturation_percentage = round((total_active / total_threshold) * 100, 1) if total_threshold > 0 else 0.0

    if bypass_active:
        recommendation = "continue_screening"
    elif is_saturated:
        recommendation = "pause_screening"
    else:
        recommendation = "continue_screening"

    organic_slots = max(0, threshold_web - organic_count)
    sourcing_slots = max(0, threshold_sourcing - source_count)

    return SaturationStatusResponse(
        job_id=str(job_id),
        approved_count=total_active,
        saturation_threshold=legacy_threshold,
        is_saturated=is_saturated,
        slots_remaining=slots_remaining,
        recommendation=recommendation,
        saturation_percentage=saturation_percentage,
        queued_count=queued_count,
        last_screened_at=last_screened_at,
        saturation_disabled_until=saturation_disabled_until,
        counts_by_channel=ChannelCounts(
            web=web_count,
            whatsapp=whatsapp_count,
            sourcing=sourcing_count,
            ats=ats_count,
        ),
        organic=ChannelSaturation(
            count=organic_count,
            threshold=threshold_web,
            is_saturated=organic_saturated,
            slots_remaining=organic_slots,
            percentage=round((organic_count / threshold_web) * 100, 1) if threshold_web > 0 else 0.0,
        ),
        sourcing=ChannelSaturation(
            count=source_count,
            threshold=threshold_sourcing,
            is_saturated=sourcing_saturated,
            slots_remaining=sourcing_slots,
            percentage=round((source_count / threshold_sourcing) * 100, 1) if threshold_sourcing > 0 else 0.0,
        ),
        threshold_web=threshold_web,
        threshold_sourcing=threshold_sourcing,
        unlock_increment=unlock_increment,
        unlock_hours=unlock_hours,
    )


class QueueStatusResponse(BaseModel):
    job_id: str
    queued_count: int
    candidates: list = []


class ProcessQueueRequest(WeDoBaseModel):
    max_promote: int = Field(1, ge=1, le=50)


class ProcessQueueResponse(BaseModel):
    success: bool
    promoted_count: int
    promoted_candidates: list = []


@router.get("/job-vacancies/{job_id}/screening-queue", response_model=QueueStatusResponse, tags=["saturation"])
async def get_screening_queue(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    queued_result = await db.execute(
        select(VacancyCandidate)  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
        .where(
            VacancyCandidate.vacancy_id == job_id,
            VacancyCandidate.status == "awaiting_screening",
        )
        .order_by(
            VacancyCandidate.lia_score.desc().nullslast(),
            VacancyCandidate.created_at.asc(),
        )
    )
    queued = queued_result.scalars().all()

    candidates = []
    for vc in queued:
        candidates.append({
            "candidate_id": str(vc.candidate_id),
            "lia_score": vc.lia_score,
            "origin": vc.origin,
            "created_at": vc.created_at.isoformat() if vc.created_at else None,
        })

    return QueueStatusResponse(
        job_id=str(job_id),
        queued_count=len(candidates),
        candidates=candidates,
    )


@router.post("/job-vacancies/{job_id}/process-queue", response_model=ProcessQueueResponse, tags=["saturation"])
async def process_queue(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], request: ProcessQueueRequest, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    try:
        from app.domains.automation.services.automation_handlers import process_screening_queue

        promoted = await process_screening_queue(
            db=db,
            vacancy_id=str(job_id),
            company_id=str(vacancy.company_id),
            max_promote=request.max_promote,
        )
        return ProcessQueueResponse(
            success=True,
            promoted_count=len(promoted),
            promoted_candidates=promoted,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-vacancies/{job_id}/unlock-pipeline", response_model=UnlockPipelineResponse, tags=["saturation"])
async def unlock_pipeline(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: UnlockPipelineRequest,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id vem do JWT via require_company_id (canonical)
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    governance_rules = dict(vacancy.governance_rules or {})

    if request.action == "increase_threshold":
        if request.new_threshold is None:
            raise HTTPException(status_code=400, detail="new_threshold is required for increase_threshold action")
        
        old_threshold_web = governance_rules.get("threshold_web", DEFAULT_SATURATION_THRESHOLD)
        old_threshold_sourcing = governance_rules.get("threshold_sourcing", DEFAULT_SATURATION_THRESHOLD)
        increment = request.new_threshold - governance_rules.get("saturation_threshold", DEFAULT_SATURATION_THRESHOLD)
        if increment < 1:
            increment = DEFAULT_UNLOCK_INCREMENT
        
        governance_rules["saturation_threshold"] = request.new_threshold
        governance_rules["threshold_web"] = old_threshold_web + increment
        governance_rules["threshold_sourcing"] = old_threshold_sourcing + increment
        vacancy.governance_rules = governance_rules

        try:
            from app.domains.automation.services.automation_handlers import process_screening_queue
            await process_screening_queue(
                db=db,
                vacancy_id=str(job_id),
                company_id=str(vacancy.company_id),
                max_promote=increment,
            )
        except Exception as e:
            logger.warning(f"Failed to process queue after threshold increase: {e}")

        return UnlockPipelineResponse(
            success=True,
            message=f"Thresholds updated: web={governance_rules['threshold_web']}, sourcing={governance_rules['threshold_sourcing']}",
            new_threshold=request.new_threshold,
            saturation_disabled_until=None,
        )

    elif request.action == "disable_temporarily":
        if request.disable_hours is None:
            raise HTTPException(status_code=400, detail="disable_hours is required for disable_temporarily action")
        disabled_until = datetime.utcnow() + timedelta(hours=request.disable_hours)
        governance_rules["saturation_disabled_until"] = disabled_until.isoformat()
        vacancy.governance_rules = governance_rules

        try:
            from app.domains.automation.services.automation_handlers import process_screening_queue
            await process_screening_queue(
                db=db,
                vacancy_id=str(job_id),
                company_id=str(vacancy.company_id),
                max_promote=5,
            )
        except Exception as e:
            logger.warning(f"Failed to process queue after temporary unlock: {e}")

        return UnlockPipelineResponse(
            success=True,
            message=f"Saturation disabled until {disabled_until.isoformat()}",
            new_threshold=governance_rules.get("saturation_threshold", DEFAULT_SATURATION_THRESHOLD),
            saturation_disabled_until=disabled_until,
        )
