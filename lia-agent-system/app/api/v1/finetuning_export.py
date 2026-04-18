import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.shared.compliance.audit_service import audit_service
from app.shared.learning.finetuning_export import finetuning_export_service as _service
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finetuning", tags=["finetuning-export"])


async def _authorize_company_access(
    requested_company_id: str,
    current_user: User,
    action: str,
) -> str:
    """Enforce that the caller belongs to the company they are exporting.

    - 404 when the authenticated user has no company assigned (treat as if
      the resource doesn't exist for them).
    - 403 when the authenticated user's company does not match the path
      ``company_id``. Both successful and denied attempts are recorded via
      ``audit_service.log_decision`` so that exports of fine-tuning data
      leave an auditable trail.
    """
    user_company_id = str(current_user.company_id) if current_user.company_id else None

    if not user_company_id:
        try:
            await audit_service.log_decision(
                company_id=str(requested_company_id),
                agent_name="finetuning_export_api",
                decision_type="generate_feedback",
                action=action,
                decision="denied_no_company",
                reasoning=[
                    f"User {current_user.id} has no company_id; denied access "
                    f"to company {requested_company_id}."
                ],
                criteria_used=["user.company_id", "path.company_id"],
            )
        except Exception as exc:  # pragma: no cover - audit must never block auth
            logger.warning("Failed to log denied finetuning export attempt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found for current user",
        )

    if user_company_id != str(requested_company_id):
        try:
            await audit_service.log_decision(
                company_id=user_company_id,
                agent_name="finetuning_export_api",
                decision_type="generate_feedback",
                action=action,
                decision="denied_cross_tenant",
                reasoning=[
                    f"User {current_user.id} from company {user_company_id} "
                    f"attempted access to company {requested_company_id}."
                ],
                criteria_used=["user.company_id", "path.company_id"],
            )
        except Exception as exc:  # pragma: no cover - audit must never block auth
            logger.warning("Failed to log cross-tenant finetuning export attempt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company's fine-tuning data",
        )

    return user_company_id


@router.get("/stats/{company_id}", response_model=None)
async def get_export_stats(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _authorize_company_access(company_id, current_user, action="get_export_stats")
    stats = await _service.get_export_stats(company_id, db)
    try:
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="finetuning_export_api",
            decision_type="generate_feedback",
            action="get_export_stats",
            decision="allowed",
            reasoning=[f"User {current_user.id} fetched fine-tuning stats."],
            criteria_used=["user.company_id", "path.company_id"],
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to log finetuning stats access: %s", exc)
    return stats


@router.post("/export/{company_id}", response_model=None)
async def trigger_export(
    company_id: _DualId,
    format: str = Query(default="claude", regex="^(claude|gpt)$"),
    min_quality: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _authorize_company_access(company_id, current_user, action="trigger_export")
    content = await _service.export_to_file(company_id, db, output_format=format)
    lines = content.strip().split("\n") if content.strip() else []
    try:
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="finetuning_export_api",
            decision_type="generate_feedback",
            action="trigger_export",
            decision="allowed",
            reasoning=[
                f"User {current_user.id} exported fine-tuning data "
                f"(format={format}, min_quality={min_quality}, lines={len(lines)})."
            ],
            criteria_used=["user.company_id", "path.company_id", "format", "min_quality"],
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to log finetuning export: %s", exc)
    return {
        "company_id": company_id,
        "format": format,
        "min_quality": min_quality,
        "line_count": len(lines),
        "content": content,
    }

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
