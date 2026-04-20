"""
Recruitment Campaigns API endpoints.

The list endpoint reads from the FastAPI ``recruitment_campaigns`` table so the
workflow rail and ``JobCampaignBadge`` can show real data (status, current
stage, per-stage candidate counts). Writes (create/update/advance) still live
on the Rails ATS — those handlers remain ``501 Not Implemented`` while the
Rails ↔ FastAPI sync is being wired up.

WebSocket boundary
------------------
This module intentionally does **not** push ``campaign_update`` messages
itself. Real-time updates for the rail are sourced from the Rails ATS via
ActionCable's ``WorkflowChannel`` (see ``ats-api-copia/app/channels/
workflow_channel.rb``) — Rails owns the broadcast because it owns the
mutations today. ``useWorkflowRail`` falls back to polling this list endpoint
every 30s when no Rails WS URL is configured. Follow-up #642 tracks adding a
FastAPI-native WS bridge for environments that don't run Rails.
"""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from lia_models.recruitment_campaign import RecruitmentCampaign

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment_campaigns", tags=["Recruitment Campaigns"])

_NOT_IMPLEMENTED = {
    "status": "not_implemented",
    "message": (
        "Recruitment campaign writes still live on the Rails ATS. "
        "Use the Rails endpoint until the FastAPI sync is enabled."
    ),
    "documentation": "https://docs.wedotalent.cc/roadmap#recruitment-campaigns",
}


# ---------------------------------------------------------------------------
# Stage projection
# ---------------------------------------------------------------------------

# Human-readable labels for the canonical stage names emitted by
# ``DEFAULT_CAMPAIGN_STAGES`` in ``lia_models.recruitment_campaign``. Custom
# stages fall back to a Title-cased version of their ``name``.
_STAGE_LABELS = {
    "sourcing": "Sourcing",
    "screening": "Triagem",
    "outreach": "Contato",
    "interview": "Entrevista",
    "evaluation": "Avaliação",
    "offer": "Oferta",
}

# Per-stage candidate counts surfaced to the rail. Stages without a dedicated
# counter on the model contribute zero — never None — so the frontend can
# always render the number badge.
_STAGE_COUNT_FIELDS = {
    "sourcing": "total_candidates",
    "screening": "candidates_screened",
    "outreach": "candidates_contacted",
    "interview": "candidates_interviewed",
    "offer": "candidates_offered",
}


def _stage_label(stage: dict[str, Any]) -> str:
    name = str(stage.get("name") or "").strip()
    if not name:
        return "Etapa"
    return _STAGE_LABELS.get(name, name.replace("_", " ").title())


def _stage_count(campaign: RecruitmentCampaign, stage_name: str) -> int:
    field = _STAGE_COUNT_FIELDS.get(stage_name)
    if not field:
        return 0
    value = getattr(campaign, field, 0) or 0
    return int(value)


def _project_stages(campaign: RecruitmentCampaign) -> list[dict[str, Any]]:
    """Return the rail-facing stage list with status + counts."""
    raw_stages = campaign.stages or []
    current_idx = campaign.current_stage_index or 0
    completed = (campaign.status or "").lower() == "completed"

    out: list[dict[str, Any]] = []
    for idx, stage in enumerate(raw_stages):
        if not isinstance(stage, dict):
            continue
        name = str(stage.get("name") or f"stage_{idx}")
        if completed:
            status = "completed"
        elif idx < current_idx:
            status = "completed"
        elif idx == current_idx:
            status = "in_progress"
        else:
            status = "pending"
        checkpoint = stage.get("checkpoint")
        out.append({
            "stage": name,
            "label": _stage_label(stage),
            "status": status,
            "candidatesCount": _stage_count(campaign, name),
            "checkpoint": checkpoint if isinstance(checkpoint, str) else None,
        })
    return out


def _current_stage_name(campaign: RecruitmentCampaign) -> str | None:
    stages = campaign.stages or []
    idx = campaign.current_stage_index or 0
    if 0 <= idx < len(stages) and isinstance(stages[idx], dict):
        name = stages[idx].get("name")
        return str(name) if name else None
    return None


def _pending_action(campaign: RecruitmentCampaign, stages: list[dict[str, Any]]) -> dict[str, Any] | None:
    current = next((s for s in stages if s["status"] == "in_progress"), None)
    if not current or not current.get("checkpoint"):
        return None
    return {
        "message": current["checkpoint"],
        "candidatesCount": current.get("candidatesCount", 0),
    }


def _jsonapi_campaign(campaign: RecruitmentCampaign) -> dict[str, Any]:
    stages = _project_stages(campaign)
    return {
        "id": str(campaign.id),
        "type": "recruitment_campaign",
        "attributes": {
            "name": campaign.name,
            "status": campaign.status,
            "current_stage": _current_stage_name(campaign),
            "stages": stages,
            "pending_action": _pending_action(campaign, stages),
            "job_id": campaign.job_id,
            "talent_pool_id": campaign.talent_pool_id,
            "automation_level": campaign.automation_level,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("")
async def list_campaigns(
    status: str | None = Query(None, description="Filter by status (active, paused, completed, ...)"),
    job_id: str | None = Query(None, description="Filter campaigns associated with a job"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """List recruitment campaigns for the current tenant.

    Supports ``?status=`` and ``?job_id=`` query filters. Returns a JSONAPI
    ``data`` envelope so the workflow rail and ``JobCampaignBadge`` can map
    each entry directly.
    """
    company_id = get_user_company_id(current_user)
    stmt = (
        select(RecruitmentCampaign)
        .where(RecruitmentCampaign.company_id == str(company_id))
        .order_by(RecruitmentCampaign.created_at.desc())
    )
    if status:
        stmt = stmt.where(RecruitmentCampaign.status == status)
    if job_id:
        stmt = stmt.where(RecruitmentCampaign.job_id == str(job_id))

    # Let DB errors propagate as a 500 so the rail / badge surface a real
    # failure instead of silently rendering "Sem campanha". The frontend
    # already tolerates a non-200 by leaving the rail empty.
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    payload = [_jsonapi_campaign(c) for c in campaigns]
    return {
        "data": payload,
        "total": len(payload),
        "status_filter": status,
        "job_id_filter": job_id,
    }


@router.post("", status_code=501)
async def create_campaign(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("campaigns", current_user.company_id, db)
    return _NOT_IMPLEMENTED


@router.get("/{campaign_id}", status_code=501)
async def get_campaign(
    campaign_id: _DualId,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.patch("/{campaign_id}", status_code=501)
async def update_campaign(
    campaign_id: _DualId,
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/advance-stage", status_code=501)
async def advance_stage(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/complete-stage", status_code=501)
async def complete_stage(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/add-checkpoint", status_code=501)
async def add_checkpoint(
    campaign_id: _DualId,
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
):
    return _NOT_IMPLEMENTED

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
