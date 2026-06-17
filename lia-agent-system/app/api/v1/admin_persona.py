"""
Admin Persona — contract surface canonical for the admin2.wedotalent.cc UI.

Registrado 2026-05-21 (C5 / E4-prep). Endpoint primário de health-check +
versão do contrato. Time admin WeDOTalent (Anderson + equipe) chama este
endpoint para confirmar compatibilidade de protocolo ANTES de qualquer
operação cross-tenant.

## Por que um arquivo separado de ``admin_prompts.py``

``admin_prompts.py`` carrega o histórico de Sprint B + Wave 2 Agent B e
serve múltiplas concerns (prompt version registry + tenant overrides).
``admin_persona.py`` é a nova surface dedicada aos endpoints que o time
admin WeDOTalent consumirá especificamente — começa pequeno (versão) e
cresce conforme a integração evolui (listar tenants, ver audit history,
disparar rollback, etc.).

## Contract version semver

- MAJOR — quebra wire (rename de endpoint, alteração de schema)
- MINOR — adiciona endpoint/campo sem quebrar callers existentes
- PATCH — bugfix / clarificação sem efeito wire

Time admin WeDOTalent deve fazer pin no MAJOR e tolerar MINOR/PATCH.
Mudança de MAJOR exige coordenação prévia.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import require_wedotalent_admin
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/persona", tags=["admin-persona"])


# ---------------------------------------------------------------------------
# Canonical contract version (semver).
# BUMP MAJOR when removing/renaming endpoints or breaking response schemas.
# BUMP MINOR when adding new endpoints / non-breaking response fields.
# BUMP PATCH for internal fixes that do not affect callers.
# ---------------------------------------------------------------------------
ADMIN_PERSONA_CONTRACT_VERSION = "1.0.0"


class AdminPersonaContractVersionResponse(BaseModel):
    """Returned by ``GET /admin/persona/contract-version``.

    Time admin WeDOTalent valida `major` no início de cada release.
    Mismatch de major obriga coordenação prévia antes de chamar endpoints
    que mudaram.
    """
    model_config = ConfigDict(extra="forbid")

    contract_version: str = Field(..., description="Semver completo, ex: '1.0.0'")
    major: int = Field(..., ge=1, description="Versão major — bump quebra wire")
    minor: int = Field(..., ge=0)
    patch: int = Field(..., ge=0)
    surfaces: list[str] = Field(
        ...,
        description="Lista de surfaces de contrato disponíveis nesta versão. "
                    "Permite caller checar feature flags sem mais round-trips.",
    )
    docs_url_relative: str = Field(
        ...,
        description="Path canonical da documentação dentro do repositório.",
    )


@router.get(
    "/contract-version",
    response_model=AdminPersonaContractVersionResponse,
    summary="Versão do contrato Admin Persona (E4-prep)",
)
async def get_contract_version(
    # Mesmo gate de role do resto da surface — read-only mas só staff.
    current_user: User = Depends(require_wedotalent_admin),
) -> AdminPersonaContractVersionResponse:
    """Retorna a versão semver atual do contrato + lista de surfaces ativas.

    Caller esperado: admin2.wedotalent.cc no boot ou antes de releases
    importantes. Resposta cabe em <1KB e é cacheable do lado deles por
    poucos minutos (esta versão muda apenas quando há release de backend).
    """
    # multi-tenancy: nao toca dado de tenant — retorna constante estatica
    # (ADMIN_PERSONA_CONTRACT_VERSION) + lista de surfaces hardcoded. Gated por
    # require_wedotalent_admin (staff-only). Sensor false positive.
    parts = ADMIN_PERSONA_CONTRACT_VERSION.split(".")
    return AdminPersonaContractVersionResponse(
        contract_version=ADMIN_PERSONA_CONTRACT_VERSION,
        major=int(parts[0]),
        minor=int(parts[1]),
        patch=int(parts[2]),
        surfaces=[
            # Surfaces existentes em admin_prompts.py — declaradas aqui para
            # discovery. Time admin WeDOTalent itera essa lista.
            "tenant_overrides_crud",      # /admin/prompts/tenant-overrides/*
            "ethics_invariants_validation",  # validator C3 enforces
            "audit_trail_per_change",     # audit_service.log_decision
        ],
        docs_url_relative="docs/admin-wedotalent-integration.md",
    )
