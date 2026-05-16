"""
Stub endpoints for features not yet implemented in the backend.
Returns empty but valid responses so the frontend doesn't loop on 404s.
"""
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id

router = APIRouter(tags=["stubs"])


@router.get("/talent-pools")
async def list_talent_pools(current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (stubs) — no tenant data
    return {"items": [], "total": 0}


@router.get("/talent-pools/{pool_id}")
async def get_talent_pool(pool_id: str, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (stubs) — no tenant data
    return {"id": pool_id, "name": "", "candidates": []}


@router.get("/recruitment-campaigns")
async def list_recruitment_campaigns(
    status: str = "active",
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (stubs) — no tenant data
    return {"items": [], "total": 0}


@router.get("/recruitment-campaigns/{campaign_id}")
async def get_recruitment_campaign(campaign_id: str, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (stubs) — no tenant data
    return {"id": campaign_id}
