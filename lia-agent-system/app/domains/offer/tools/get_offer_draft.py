"""Tool: get_offer_draft."""
import logging
from typing import Any
from uuid import UUID

from app.domains.base import DomainContext

logger = logging.getLogger(__name__)


async def run(params: dict[str, Any], context: DomainContext) -> dict[str, Any]:
    try:
        company_id = context.tenant_id or context.metadata.get("company_id", "")
        offer_id = UUID(str(params["offer_id"]))

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            from app.domains.offer.services.offer_service import OfferService
            svc = OfferService(db)
            draft = await svc.get_draft(offer_id, company_id)

        if not draft:
            return {"success": False, "error": "Proposta nao encontrada"}

        # Sprint F.4 #42 canonical-remap: read canonical column names from the
        # model and expose wire-level field names ("offered_salary",
        # "offered_salary_currency", "offered_start_date", "validity_days")
        # for FE compat.
        from app.domains.offer.services.offer_service import _validity_days_from_deadline
        job = draft.job_data_snapshot or {}
        candidate = draft.candidate_data_snapshot or {}
        return {
            "success": True,
            "offer_id": str(draft.id),
            "status": draft.status,
            "offered_salary": float(draft.salary) if draft.salary else None,
            "offered_salary_currency": draft.currency,
            "offered_start_date": str(draft.start_date) if draft.start_date else None,
            "validity_days": _validity_days_from_deadline(draft),
            "candidate_name": candidate.get("name", ""),
            "job_title": job.get("title", ""),
        }
    except Exception as exc:
        logger.error("[OFFER-TOOL] get_offer_draft failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}
