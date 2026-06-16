"""Tool: create_offer_draft — creates or returns existing draft."""
import logging
from typing import Any
from uuid import UUID

from app.domains.base import DomainContext
from app.schemas.offer import OfferDraftCreate

logger = logging.getLogger(__name__)


async def run(params: dict[str, Any], context: DomainContext) -> dict[str, Any]:
    try:
        company_id = context.tenant_id or context.metadata.get("company_id", "")
        user_id = context.user_id or ""
        candidate_id = params.get("candidate_id", "")
        job_id_raw = params.get("job_id", "")

        if not candidate_id or not job_id_raw:
            return {"success": False, "error": "candidate_id and job_id are required"}

        job_id = UUID(str(job_id_raw))

        # Fetch snapshots from Rails proxy
        job_snapshot = await _fetch_job_snapshot(job_id, company_id, context)
        candidate_snapshot = await _fetch_candidate_snapshot(candidate_id, company_id, context)

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            from app.domains.offer.services.offer_service import OfferService
            svc = OfferService(db)
            draft = await svc.create_or_get_draft(
                data=OfferDraftCreate(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    template_id=UUID(params["template_id"]) if params.get("template_id") else None,
                ),
                company_id=company_id,
                user_id=user_id,
                job_snapshot=job_snapshot,
                candidate_snapshot=candidate_snapshot,
            )
            await db.commit()

        return {
            "success": True,
            "offer_id": str(draft.id),
            "status": draft.status,
            "message": "Rascunho criado com sucesso",
            "ui_action": "open_offer_review",
            "ui_action_params": {
                "candidate_id": candidate_id,
                "job_id": str(job_id),
                "draft_id": str(draft.id),
            },
        }
    except Exception as exc:
        logger.error("[OFFER-TOOL] create_offer_draft failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}


async def _fetch_job_snapshot(
    job_id: UUID, company_id: str, context: DomainContext
) -> dict[str, Any]:
    import os
    import httpx
    # P2-W1-10: porta canonica FastAPI = 8001 no Replit. Configurar LIA_BACKEND_URL=http://localhost:8001
    base_url = os.environ.get("LIA_BACKEND_URL", "http://localhost:8001")
    auth_token = context.metadata.get("auth_token", "")
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            resp = await client.get(
                f"/api/v1/job-vacancies/{job_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "title": data.get("title", ""),
                    "manager": data.get("manager", ""),
                    "manager_email": data.get("manager_email", ""),
                    "department": data.get("department", ""),
                    "salary_range": data.get("salary_range", {}),
                    "benefits": data.get("benefits", []),
                    "contract_type": data.get("contract_type", ""),
                    "work_model": data.get("work_model", ""),
                    "company_name": data.get("company_name", ""),
                }
    except Exception as exc:
        logger.warning("[OFFER-TOOL] Could not fetch job snapshot: %s", exc)
    return {"job_id": str(job_id)}


async def _fetch_candidate_snapshot(
    candidate_id: str, company_id: str, context: DomainContext
) -> dict[str, Any]:
    import os
    import httpx
    # P2-W1-10: porta canonica FastAPI = 8001 no Replit. Configurar LIA_BACKEND_URL=http://localhost:8001
    base_url = os.environ.get("LIA_BACKEND_URL", "http://localhost:8001")
    auth_token = context.metadata.get("auth_token", "")
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            resp = await client.get(
                f"/api/v1/candidates/{candidate_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name": data.get("name", ""),
                    "email": data.get("email", ""),
                    "phone": data.get("phone", ""),
                    "current_title": data.get("current_title", ""),
                    "current_company": data.get("current_company", ""),
                    "desired_salary_min": data.get("desired_salary_min"),
                    "desired_salary_max": data.get("desired_salary_max"),
                }
    except Exception as exc:
        logger.warning("[OFFER-TOOL] Could not fetch candidate snapshot: %s", exc)
    return {"candidate_id": candidate_id}
