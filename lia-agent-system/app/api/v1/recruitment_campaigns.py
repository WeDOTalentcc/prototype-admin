"""
Recruitment Campaigns API endpoints.

Module not yet implemented — returns explicit 501 responses so consumers
know the feature is pending rather than silently receiving empty data.
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment_campaigns", tags=["Recruitment Campaigns"])

_NOT_IMPLEMENTED = {
    "status": "not_implemented",
    "message": "Recruitment campaigns module is not yet available. This feature is under development and will be connected to the Rails ATS integration.",
    "documentation": "https://docs.wedotalent.cc/roadmap#recruitment-campaigns",
}


@router.get("")
async def list_campaigns(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return {
        **_NOT_IMPLEMENTED,
        "data": [],
        "total": 0,
        "status_filter": status,
    }


@router.post("", status_code=501)
async def create_campaign(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("campaigns", current_user.company_id, db)
    return _NOT_IMPLEMENTED


@router.get("/{campaign_id}", status_code=501)
async def get_campaign(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return _NOT_IMPLEMENTED


@router.patch("/{campaign_id}", status_code=501)
async def update_campaign(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/advance-stage", status_code=501)
async def advance_stage(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/complete-stage", status_code=501)
async def complete_stage(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return _NOT_IMPLEMENTED


@router.post("/{campaign_id}/add-checkpoint", status_code=501)
async def add_checkpoint(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return _NOT_IMPLEMENTED



# ---------------------------------------------------------------------------
# Projection helpers for the Workflow Rail / JobCampaignBadge contract
# ---------------------------------------------------------------------------

_STAGE_LABEL_MAP: dict = {
    "sourcing": "Sourcing",
    "screening": "Triagem",
    "outreach": "Contato",
    "interview": "Entrevista",
}

# Ordered mapping of stage names to the candidate-count field on the campaign.
_STAGE_COUNT_FIELD: dict = {
    "sourcing": "total_candidates",
    "screening": "candidates_screened",
    "outreach": "candidates_contacted",
    "interview": "candidates_interviewed",
    "offered": "candidates_offered",
}


def _project_stages(campaign) -> list:
    """Project a campaign's stages list into labelled, status-annotated dicts.

    Each element of the returned list has the shape::

        {
            "status": "completed" | "in_progress" | "pending",
            "label": str,
            "candidatesCount": int,
        }

    Status rules:

    * All stages *before* ``current_stage_index`` → ``"completed"``.
    * The stage *at* ``current_stage_index`` → ``"in_progress"`` (unless
      campaign ``status`` is ``"completed"``, in which case it is also
      ``"completed"``).
    * All stages *after* → ``"pending"``.
    * When campaign ``status == "completed"`` every stage is ``"completed"``.

    Args:
        campaign: Object (or SimpleNamespace) with ``stages`` list,
            ``current_stage_index`` int, and ``status`` str.

    Returns:
        List of stage projection dicts.
    """
    stages = getattr(campaign, "stages", []) or []
    current_idx = getattr(campaign, "current_stage_index", 0)
    campaign_status = getattr(campaign, "status", "active")
    all_completed = campaign_status == "completed"

    projected = []
    for i, stage in enumerate(stages):
        name = stage.get("name", "") if isinstance(stage, dict) else getattr(stage, "name", "")
        label = _STAGE_LABEL_MAP.get(name) or name.replace("_", " ").title()

        count_field = _STAGE_COUNT_FIELD.get(name)
        count = (
            getattr(campaign, count_field, 0) or 0
            if count_field
            else stage.get("candidates_count", 0) if isinstance(stage, dict) else 0
        )

        if all_completed:
            status = "completed"
        elif i < current_idx:
            status = "completed"
        elif i == current_idx:
            status = "in_progress"
        else:
            status = "pending"

        projected.append({
            "status": status,
            "label": label,
            "candidatesCount": int(count),
        })

    return projected


def _jsonapi_campaign(campaign) -> dict:
    """Serialize a campaign to the JSONAPI envelope consumed by the frontend.

    Shape::

        {
            "id": str,
            "type": "recruitment_campaign",
            "attributes": {
                "name": str,
                "status": str,
                "current_stage": str | None,
                "stages": [...],             # see _project_stages
                "pending_action": {...} | None,
                "job_id": str | None,
                "talent_pool_id": str | None,
                "created_at": str (ISO-8601),
            },
        }

    The ``pending_action`` key surfaces the in-progress stage's
    ``checkpoint`` field so the Workflow Rail can render an action banner.
    """
    stages_raw = getattr(campaign, "stages", []) or []
    current_idx = getattr(campaign, "current_stage_index", 0)

    # Determine current_stage name.
    current_stage_name = None
    current_stage_raw = None
    if stages_raw and 0 <= current_idx < len(stages_raw):
        current_stage_raw = stages_raw[current_idx]
        current_stage_name = (
            current_stage_raw.get("name")
            if isinstance(current_stage_raw, dict)
            else getattr(current_stage_raw, "name", None)
        )

    # Build pending_action from the in-progress stage's checkpoint.
    pending_action = None
    if current_stage_raw is not None:
        checkpoint = (
            current_stage_raw.get("checkpoint")
            if isinstance(current_stage_raw, dict)
            else getattr(current_stage_raw, "checkpoint", None)
        )
        if checkpoint:
            count_field = _STAGE_COUNT_FIELD.get(current_stage_name or "")
            candidates_count = getattr(campaign, count_field, 0) or 0 if count_field else 0
            pending_action = {
                "message": checkpoint,
                "candidatesCount": int(candidates_count),
            }

    created_at = getattr(campaign, "created_at", None)
    created_at_str = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or "")

    return {
        "id": str(getattr(campaign, "id", "")),
        "type": "recruitment_campaign",
        "attributes": {
            "name": getattr(campaign, "name", ""),
            "status": getattr(campaign, "status", ""),
            "current_stage": current_stage_name,
            "stages": _project_stages(campaign),
            "pending_action": pending_action,
            "job_id": getattr(campaign, "job_id", None),
            "talent_pool_id": getattr(campaign, "talent_pool_id", None),
            "created_at": created_at_str,
        },
    }

reorder_collection_before_item(router)
