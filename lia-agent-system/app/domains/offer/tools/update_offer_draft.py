"""Tool: update_offer_draft."""
import logging
from typing import Any
from uuid import UUID

from app.domains.base import DomainContext
from app.schemas.offer import OfferDraftUpdate

logger = logging.getLogger(__name__)


async def run(params: dict[str, Any], context: DomainContext) -> dict[str, Any]:
    try:
        company_id = context.tenant_id or context.metadata.get("company_id", "")
        offer_id = UUID(str(params["offer_id"]))
        updates = OfferDraftUpdate.model_validate({k: v for k, v in params.items() if k != "offer_id"})

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            from app.domains.offer.services.offer_service import OfferService
            svc = OfferService(db)
            draft = await svc.update_draft(offer_id, company_id, updates)
            await db.commit()

        if not draft:
            return {"success": False, "error": "Proposta nao encontrada"}

        return {"success": True, "offer_id": str(draft.id), "status": draft.status, "message": "Rascunho atualizado"}
    except Exception as exc:
        logger.error("[OFFER-TOOL] update_offer_draft failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}
