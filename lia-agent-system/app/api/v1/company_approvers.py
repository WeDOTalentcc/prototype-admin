import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.domains.company.dependencies import (
    get_approver_repo,
    get_company_profile_repo,
)
from app.domains.company.repositories.approver_repository import ApproverRepository
from app.domains.company.repositories.company_profile_repository import CompanyProfileRepository
from app.schemas.company import (
    ApproverCreate,
    ApproverResponse,
    ApproverUpdate,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/approvers", response_model=list[ApproverResponse])
async def list_approvers(
    company_id: uuid.UUID | None = Query(None),
    include_inactive: bool = Query(False),
    approver_repo: ApproverRepository = Depends(get_approver_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all approvers for a company."""
    try:
        if not company_id:
            return []
        approvers = await approver_repo.list_for_company(company_id)
        if include_inactive:
            # list_for_company filters active; re-fetch all if needed
            pass
        return approvers
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing approvers: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/approvers", response_model=ApproverResponse)
async def create_approver(
    company_id: str = Query(...),
    data: ApproverCreate = None,
    approver_repo: ApproverRepository = Depends(get_approver_repo),
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new approver."""
    try:
        resolved_company_id = None
        if company_id and company_id not in ("default", "unknown"):
            try:
                resolved_company_id = uuid.UUID(company_id)
            except ValueError:
                pass

        if not resolved_company_id:
            profile = await profile_repo.get_default()
            if not profile:
                profile_list = await profile_repo.list_for_company("", skip=0, limit=1)
                profile = profile_list[0] if profile_list else None
            if profile:
                resolved_company_id = profile.id

        approver = await approver_repo.create({"company_id": resolved_company_id, **data.model_dump()})
        # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
        logger.info(f"Created approver: {approver.id}")
        return approver
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating approver: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/approvers/{approver_id}", response_model=ApproverResponse)
async def update_approver(
    approver_id: uuid.UUID,
    data: ApproverUpdate,
    approver_repo: ApproverRepository = Depends(get_approver_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an approver."""
    # Onda 4.2a-P0.2 (2026-05-23): company_id passa ao repo pra cross-tenant guard.
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        approver = await approver_repo.update(
            approver_id, update_data, company_id=company_id,
        )
        if not approver:
            raise HTTPException(status_code=404, detail="Approver not found")
        return approver
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating approver: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/approvers/{approver_id}", response_model=None)
async def delete_approver(
    approver_id: uuid.UUID,
    approver_repo: ApproverRepository = Depends(get_approver_repo),
company_id: str = Depends(require_company_id)):
    # Onda 4.2a-P0.2 (2026-05-23): cross-tenant guard via company_id.
    """Soft delete an approver."""
    try:
        deleted = await approver_repo.delete(approver_id, company_id=company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Approver not found")
        return {"success": True, "message": "Approver deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting approver: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/users/search")
async def search_platform_users(
    q: str = Query(..., min_length=1, description="Search term (name or email)"),
    limit: int = Query(10, ge=1, le=50),
    company_id: str = Depends(require_company_id),
):
    """Search internal platform users by name or email — TIPO A approver selection.

    Multi-tenancy: company_id from JWT via Depends(require_company_id).
    Returns [{id, name, email, role}] for active users in the same company.
    """
    from app.core.database import get_db as _get_db
    from app.repositories.client_user_repository import ClientUserRepository
    import uuid as _uuid

    try:
        cid = _uuid.UUID(str(company_id))
    except ValueError:
        return []

    async for _db in _get_db():
        repo = ClientUserRepository(_db)
        users = await repo.list_users(cid, search=q, limit=limit, status="active")
        return [
            {
                "id": str(u.id),
                "name": u.name or "",
                "email": u.email or "",
                "role": u.role or "",
            }
            for u in users
        ]
    return []
