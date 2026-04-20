import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.shared.compliance.audit_service import audit_service
from app.shared.learning.finetuning_export import finetuning_export_service as _service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finetuning", tags=["finetuning-export"])


async def _resolve_company_id(current_user: User, action: str) -> str:
    """Return the authenticated user's company_id or raise 403.

    Task #306 — the fine-tuning endpoints used to accept ``company_id`` as
    a path parameter, which let any caller export another tenant's
    training data (IDOR). The path no longer carries ``company_id``; it
    is derived exclusively from the JWT-authenticated user. A user with
    no ``company_id`` cannot belong to any tenant and is rejected with
    403. Denied attempts are recorded via ``audit_service.log_decision``
    so compliance keeps a deny-trail of fine-tuning access attempts.
    """
    company_id = str(current_user.company_id) if current_user.company_id else None
    if not company_id:
        try:
            await audit_service.log_decision(
                company_id="unknown",
                agent_name="finetuning_export_api",
                decision_type="generate_feedback",
                action=action,
                decision="denied_no_company",
                reasoning=[
                    f"User {current_user.id} has no company_id; denied "
                    f"access to fine-tuning data."
                ],
                criteria_used=["user.company_id"],
            )
        except Exception as exc:  # pragma: no cover - audit must never block auth
            logger.warning(
                "Failed to log denied finetuning access attempt: %s", exc
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to fine-tuning data",
        )
    return company_id


@router.get("/stats", response_model=None)
async def get_export_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company_id = await _resolve_company_id(current_user, action="get_export_stats")
    stats = await _service.get_export_stats(company_id, db)
    try:
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="finetuning_export_api",
            decision_type="generate_feedback",
            action="get_export_stats",
            decision="allowed",
            reasoning=[f"User {current_user.id} fetched fine-tuning stats."],
            criteria_used=["user.company_id"],
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to log finetuning stats access: %s", exc)
    return stats


@router.post("/export", response_model=None)
async def trigger_export(
    format: str = Query(default="claude", regex="^(claude|gpt)$"),
    min_quality: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company_id = await _resolve_company_id(current_user, action="trigger_export")
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
            criteria_used=["user.company_id", "format", "min_quality"],
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
