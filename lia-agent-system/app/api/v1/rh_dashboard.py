"""RH Dashboard — LGPD Art. 20 candidate requests proxy to Rails."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_company_id
from app.schemas.api_envelope import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/rh/lgpd-requests",
    response_model=APIResponse,
    summary="LGPD Art. 20 candidate requests for RH dashboard",
    tags=["rh-dashboard"],
)
async def list_lgpd_requests(
    status: Optional[str] = Query(None, description="pending|responded|closed"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: str = Depends(get_current_company_id),
):
    """Proxies to Rails GET /v1/candidate-portal/lgpd-requests.

    Returns LGPD Art. 20 right-to-explanation requests filed by candidates.
    Rails stores the records; FastAPI forwards auth + filters.
    Falls back to empty response if Rails endpoint not yet available.
    """
    logger.info(
        "[RH Dashboard] lgpd-requests company_id=%s status=%s page=%s",
        company_id, status, page,
    )
    try:
        from app.shared.rails_client import rails_get
        params: dict = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        result = await rails_get(
            f"/v1/companies/{company_id}/candidate-portal/lgpd-requests",
            params=params,
        )
        return APIResponse.ok(data=result)
    except Exception as exc:
        logger.warning("[RH Dashboard] Rails proxy failed — returning empty: %s", exc)
        return APIResponse.ok(data={"items": [], "total": 0, "pending_count": 0})


@router.patch(
    "/rh/lgpd-requests/{request_id}/respond",
    response_model=APIResponse,
    summary="Mark LGPD Art. 20 request as responded",
    tags=["rh-dashboard"],
)
async def mark_lgpd_request_responded(
    request_id: str,
    company_id: str = Depends(get_current_company_id),
):
    """Proxies to Rails PATCH /v1/candidate-portal/lgpd-requests/:id/respond."""
    logger.info(
        "[RH Dashboard] mark-responded request_id=%s company_id=%s",
        request_id, company_id,
    )
    try:
        from app.shared.rails_client import rails_patch
        result = await rails_patch(
            f"/v1/companies/{company_id}/candidate-portal/lgpd-requests/{request_id}/respond",
            data={},
        )
        return APIResponse.ok(data=result)
    except Exception as exc:
        logger.error("[RH Dashboard] mark-responded failed: %s", exc, exc_info=True)
        return APIResponse.error(message=f"Erro ao atualizar pedido: {exc}")
