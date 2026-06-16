"""
User Agent Preferences API — Sprint J3

Endpoint para gerenciar preferência de auto_confirm por usuário/domínio.

Endpoints:
  GET  /user-preferences/agent           — listar preferências do usuário
  POST /user-preferences/agent           — criar/atualizar preferência
  GET  /user-preferences/agent/check     — verificar se auto_confirm ativo
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-preferences/agent", tags=["user-preferences"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PreferenceUpsertRequest(WeDoBaseModel):
    user_id: str
    domain: str
    action_type: str
    auto_confirm: bool


class PreferenceResponse(BaseModel):
    id: str
    user_id: str
    company_id: str
    domain: str
    action_type: str
    auto_confirm: bool
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj) -> PreferenceResponse:
        return cls(
            id=str(obj.id),
            user_id=obj.user_id,
            company_id=obj.company_id,
            domain=obj.domain,
            action_type=obj.action_type,
            auto_confirm=obj.auto_confirm,
            updated_at=obj.updated_at,
        )


class AutoConfirmCheckResponse(BaseModel):
    user_id: str
    company_id: str
    domain: str
    action_type: str
    auto_confirm: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[PreferenceResponse])
async def list_user_preferences(
    user_id: str = Query(...),
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Lista todas as preferências de auto_confirm de um usuário."""
    prefs = await UserAgentPreferenceService.list_user_preferences(
        db, user_id=user_id, company_id=company_id
    )
    return [PreferenceResponse.from_orm(p) for p in prefs]


@router.post("", response_model=PreferenceResponse)
async def upsert_preference(
    data: PreferenceUpsertRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Cria ou atualiza preferência de auto_confirm."""
    pref = await UserAgentPreferenceService.upsert(
        db,
        user_id=data.user_id,
        company_id=company_id,
        domain=data.domain,
        action_type=data.action_type,
        auto_confirm=data.auto_confirm,
    )
    return PreferenceResponse.from_orm(pref)


@router.get("/check", response_model=AutoConfirmCheckResponse)
async def check_auto_confirm(
    user_id: str = Query(...),
    company_id: str = Query(...),
    domain: str = Query(...),
    action_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Verifica se auto_confirm está ativo para um usuário/domínio/ação.
    Usado pelo HITL service antes de cada aprovação.
    """
    auto = await UserAgentPreferenceService.check_auto_confirm(
        db, user_id=user_id, company_id=company_id,
        domain=domain, action_type=action_type,
    )
    return AutoConfirmCheckResponse(
        user_id=user_id, company_id=company_id,
        domain=domain, action_type=action_type,
        auto_confirm=auto,
    )
