"""
job_offers.py — Sistema B (APOSENTADO).

Todos os endpoints retornam HTTP 410 Gone com redirect para o sistema canônico.
Ver: /api/v1/offers/

Removido em 2026-09-30 (Sunset). Use /api/v1/offers/.
"""
import logging
from fastapi import APIRouter, Response as _Response
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/job-offers", tags=["job-offers-deprecated"])
logger = logging.getLogger(__name__)

_GONE_BODY = {
    "error": "deprecated",
    "message": "Sistema B (job_offers) foi aposentado. Use /api/v1/offers/",
    "successor": "/api/v1/offers/",
    "docs": "https://docs.wedotalent.cc/offer-migration",
}

def _gone(response: _Response) -> JSONResponse:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2026-09-30"
    response.headers["Link"] = (
        '</api/v1/offers>; rel="successor-version", '
        '<https://docs.wedotalent.cc/offer-migration>; rel="deprecation"'
    )
    return JSONResponse(status_code=410, content=_GONE_BODY)


@router.get("")
async def list_job_offers_gone(response: _Response):
    """DEPRECATED — use GET /api/v1/offers/drafts."""
    return _gone(response)


@router.post("", status_code=410)
async def create_job_offer_gone(response: _Response):
    """DEPRECATED — use POST /api/v1/offers/drafts."""
    return _gone(response)


@router.patch("/{offer_id}/send")
async def send_job_offer_gone(offer_id: str, response: _Response):
    """DEPRECATED — use POST /api/v1/offers/drafts/{id}/send-auto."""
    return _gone(response)


@router.patch("/{offer_id}/respond")
async def respond_job_offer_gone(offer_id: str, response: _Response):
    """DEPRECATED — use public offer portal."""
    return _gone(response)


@router.patch("/{offer_id}/withdraw")
async def withdraw_job_offer_gone(offer_id: str, response: _Response):
    """DEPRECATED — use DELETE /api/v1/offers/drafts/{id}."""
    return _gone(response)
