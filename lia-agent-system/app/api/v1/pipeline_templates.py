"""
Pipeline Templates API endpoints.

Manages reusable recruitment process stage templates + their application to vacancies.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 1.5:
- RBAC: mutations gated por admin OR wedotalent_admin (UserRole canonical).
- Service-layer canonical: lógica de mutação delegada a PipelineTemplateService
  (audit log automático REGRA #1 ACH-026).
- 3 endpoints novos: GET /suggest (auto-suggest), POST /{id}/archive,
  POST /vacancies/{vacancy_id}/apply-pipeline-template.
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item
from app.auth.dependencies import get_current_user_or_demo, require_role
from app.auth.models import User, UserRole
from app.core.database import get_db, get_tenant_db
from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from app.domains.pipeline.services.pipeline_template_service import (
    APPLY_VALID_SOURCES,
    PipelineTemplateService,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

# Task #489 canonical DUAL_ID path pattern (UUID v4 OR bigint legacy)
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

# Canonical RBAC gate — admin do cliente (tenant) OR staff WeDOTalent.
# Decisão Paulo 2026-05-26: ambos podem CRUD templates do tenant; recruiter/manager/viewer só leem.
require_pipeline_template_admin = require_role([UserRole.admin, UserRole.wedotalent_admin])


# ─────────────────────────────────────────────────────────────────────
# Schemas canonical
# ─────────────────────────────────────────────────────────────────────


class PipelineStage(WeDoBaseModel):
    name: str
    order: int
    type: Literal["automatic", "manual", "hybrid"] = "manual"
    sla_days: int = 3
    instructions: str | None = None

    @field_validator("order")
    @classmethod
    def _order_min_1(cls, v: int) -> int:
        if v < 1:
            raise ValueError("order must be >= 1")
        return v

    @field_validator("sla_days")
    @classmethod
    def _sla_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("sla_days must be >= 0")
        return v


class PipelineTemplateCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    stages: list[PipelineStage]
    is_default: bool = False
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None


class PipelineTemplateUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    stages: list[PipelineStage] | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    is_archived: bool | None = None
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None


class PipelineTemplateResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None = None
    stages: list[dict[str, Any]]
    is_default: bool
    is_active: bool
    is_archived: bool = False
    usage_count: int
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PipelineTemplateListResponse(BaseModel):
    items: list[PipelineTemplateResponse]
    total: int
    page: int
    size: int


class PipelineTemplateSuggestion(BaseModel):
    template: PipelineTemplateResponse
    score: float


class ApplyPipelineTemplateRequest(WeDoBaseModel):
    template_id: str
    source: Literal["manual_modal", "wizard_auto_suggest", "wizard_explicit"] = "manual_modal"


class ApplyPipelineTemplateResponse(BaseModel):
    vacancy_id: str
    template_id: str
    template_name: str
    stages_applied: int
    usage_count: int
    source: str


def _to_response(t) -> PipelineTemplateResponse:
    return PipelineTemplateResponse(
        id=str(t.id),
        company_id=t.company_id,
        name=t.name,
        description=t.description,
        stages=t.stages or [],
        is_default=t.is_default,
        is_active=t.is_active,
        is_archived=bool(getattr(t, "is_archived", False)),
        usage_count=t.usage_count or 0,
        department_hint=getattr(t, "department_hint", None),
        seniority_hint=getattr(t, "seniority_hint", None),
        job_family_hint=getattr(t, "job_family_hint", None),
        created_by=t.created_by,
        updated_by=getattr(t, "updated_by", None),
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
    )


# ─────────────────────────────────────────────────────────────────────
# Router 1: /company/pipeline-templates/* (gestão de templates)
# ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/company/pipeline-templates", tags=["pipeline-templates"])


@router.get("/", response_model=PipelineTemplateListResponse)
async def list_pipeline_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = True,
    is_archived: bool | None = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """List pipeline templates for the company.

    Default exclui arquivados (is_archived=False). Pass is_archived=None para incluir.
    """
    repo = PipelineTemplateRepository(db)
    templates, total = await repo.list_for_company(
        company_id,
        is_active=is_active,
        is_archived=is_archived,
        search=search,
        page=page,
        size=size,
    )
    return PipelineTemplateListResponse(
        items=[_to_response(t) for t in templates],
        total=total,
        page=page,
        size=size,
    )


@router.get("/suggest", response_model=list[PipelineTemplateSuggestion])
async def suggest_pipeline_template(
    department: str | None = Query(None),
    seniority: str | None = Query(None),
    job_family: str | None = Query(None),
    threshold: float = Query(0.4, ge=0.0, le=1.0),
    top: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Suggest pipeline templates ranked by hint match.

    Scoring canonical em PipelineTemplateRepository.list_for_suggestion:
    department 0.50 + seniority 0.25 + job_family 0.25. Fallback: nenhum template
    com hints + existe default → sugere default com score 0.5.

    Caller filtra por threshold (default 0.4) e retorna top-N (default 3).
    """
    repo = PipelineTemplateRepository(db)
    scored = await repo.list_for_suggestion(
        company_id,
        department=department,
        seniority=seniority,
        job_family=job_family,
    )
    filtered = [(t, s) for t, s in scored if s >= threshold][:top]
    return [
        PipelineTemplateSuggestion(template=_to_response(t), score=round(s, 3))
        for t, s in filtered
    ]


@router.post(
    "/",
    response_model=PipelineTemplateResponse,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def create_pipeline_template(
    data: PipelineTemplateCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Create a new pipeline template (admin/wedotalent_admin only)."""
    user_email = current_user.email or "demo@example.com"
    service = PipelineTemplateService(db)
    payload = {
        "name": data.name,
        "description": data.description,
        "stages": [s.model_dump() for s in data.stages],
        "is_default": data.is_default,
        "department_hint": data.department_hint,
        "seniority_hint": data.seniority_hint,
        "job_family_hint": data.job_family_hint,
    }
    template = await service.create(company_id, payload, created_by=user_email)
    logger.info("Created pipeline template id=%s for company=%s", template.id, company_id)
    return _to_response(template)


@router.get("/{template_id}", response_model=PipelineTemplateResponse)
async def get_pipeline_template(
    template_id: _DualId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Get a specific pipeline template by ID."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    return _to_response(template)


@router.put(
    "/{template_id}",
    response_model=PipelineTemplateResponse,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def update_pipeline_template(
    template_id: _DualId,
    data: PipelineTemplateUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Update a pipeline template (admin/wedotalent_admin only)."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    update_data = data.model_dump(exclude_unset=True)
    if "stages" in update_data and update_data["stages"] is not None:
        update_data["stages"] = [s if isinstance(s, dict) else s.model_dump() for s in data.stages]
    user_email = current_user.email or "demo@example.com"
    service = PipelineTemplateService(db)
    template = await service.update(template_uuid, company_id, update_data, updated_by=user_email)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    logger.info("Updated pipeline template id=%s", template.id)
    return _to_response(template)


@router.delete(
    "/{template_id}",
    response_model=None,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def delete_pipeline_template(
    template_id: _DualId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Soft delete (is_active=False) — legado. Use POST /{id}/archive para canonical."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    await repo.soft_delete(template)
    logger.info("Soft-deleted pipeline template id=%s", template.id)
    return {"success": True, "message": "Template deleted successfully"}


@router.post(
    "/{template_id}/archive",
    response_model=PipelineTemplateResponse,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def archive_pipeline_template(
    template_id: _DualId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Archive canonical — set is_archived=True (distinct from soft_delete is_active=False).

    Templates arquivados continuam visíveis em analytics histórico mas somem do seletor
    de aplicar. Emite audit log canonical.
    """
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    user_email = current_user.email or "demo@example.com"
    service = PipelineTemplateService(db)
    template = await service.archive(template_uuid, company_id, updated_by=user_email)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    logger.info("Archived pipeline template id=%s", template.id)
    return _to_response(template)


@router.post(
    "/{template_id}/clone",
    response_model=PipelineTemplateResponse,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def clone_pipeline_template(
    template_id: _DualId,
    new_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Clone an existing template (admin/wedotalent_admin only)."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    user_email = current_user.email or "demo@example.com"
    service = PipelineTemplateService(db)
    repo = PipelineTemplateRepository(db)
    original = await repo.get_by_id(template_uuid, company_id)
    if not original:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    target_name = new_name or f"{original.name} (Cópia)"
    cloned = await service.clone(template_uuid, company_id, target_name, created_by=user_email)
    if not cloned:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    logger.info("Cloned pipeline template src=%s -> dst=%s", original.id, cloned.id)
    return _to_response(cloned)


@router.post(
    "/seed-defaults",
    response_model=None,
    dependencies=[Depends(require_pipeline_template_admin)],
)
async def seed_default_templates(
    force: bool = Query(False, description="Force re-seeding even if templates exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Seed default templates for the company (admin/wedotalent_admin only)."""
    user_email = current_user.email or "demo@example.com"
    repo = PipelineTemplateRepository(db)
    count = await repo.count_active(company_id)
    if count > 0 and not force:
        return {
            "success": True,
            "message": f"Company already has {count} templates. Use force=true to re-seed.",
            "seeded": 0,
        }
    seeded = await repo.seed_defaults(company_id, created_by=user_email)
    logger.info("Seeded %d default pipeline templates for company=%s", seeded, company_id)
    return {"success": True, "message": f"Seeded {seeded} default templates", "seeded": seeded}


@router.post("/{template_id}/increment-usage", response_model=None)
async def increment_template_usage(
    template_id: _DualId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Increment usage_count (called when template applied to a job).

    NOTA: prefira POST /vacancies/{id}/apply-pipeline-template (Fase 1.5) que faz
    apply canonical com audit. Este endpoint persiste legado pra retrocompat
    do frontend useEditJob.ts.
    """
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    template = await repo.increment_usage(template)
    return {"success": True, "usage_count": template.usage_count}


# Task #489 — Keep collection-scoped routes ahead of item-scoped routes
_reorder_collection_before_item(router)


# ─────────────────────────────────────────────────────────────────────
# Router 2: /vacancies/{vacancy_id}/apply-pipeline-template
# Canonical apply endpoint — copy-on-write + audit + multi-tenancy gate.
# ─────────────────────────────────────────────────────────────────────

vacancy_apply_router = APIRouter(prefix="/vacancies", tags=["pipeline-templates", "vacancies"])


@vacancy_apply_router.post(
    "/{vacancy_id}/apply-pipeline-template",
    response_model=ApplyPipelineTemplateResponse,
)
async def apply_pipeline_template_to_vacancy(
    vacancy_id: _DualId,
    payload: ApplyPipelineTemplateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Apply pipeline template to vacancy (copy-on-write + audit).

    Source in {manual_modal, wizard_auto_suggest, wizard_explicit}. Source canonical
    é registrado no audit log para identificar origem da aplicação (UI manual,
    sugestão automática da LIA, escolha explícita do recrutador no wizard chat).

    Multi-tenancy fail-closed: template + vacancy ambos verificados por company_id.
    Cross-tenant: 404 (não 403 — canonical: nunca expor existência cross-tenant).
    """
    try:
        template_uuid = uuid.UUID(payload.template_id)
        vacancy_uuid = uuid.UUID(vacancy_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if payload.source not in APPLY_VALID_SOURCES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid source. Expected one of {sorted(APPLY_VALID_SOURCES)}",
        )

    user_email = current_user.email or "demo@example.com"
    service = PipelineTemplateService(db)
    result = await service.apply_to_vacancy(
        template_id=template_uuid,
        vacancy_id=vacancy_uuid,
        company_id=company_id,
        applied_by=user_email,
        source=payload.source,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Pipeline template or vacancy not found")
    return ApplyPipelineTemplateResponse(**result)
