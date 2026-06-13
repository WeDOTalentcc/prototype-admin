"""
Recruitment Email Templates API endpoints.
Provides CRUD operations for pipeline stage email templates.
"""
from app.middleware.request_id import get_correlation_id
import logging
import uuid as uuid_module
from datetime import datetime
from app.shared.compliance.audit_service import AuditService  # P1-W2-03

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.communication.repositories.recruitment_email_template_repository import RecruitmentEmailTemplateRepository
from app.domains.job_management.services.recruitment_email_templates import (
    SAMPLE_DATA,
    clone_templates_for_company,
    get_template_for_stage,
    list_templates,
    render_template,
    seed_default_templates,
)
from app.models.recruitment_email_template import RecruitmentEmailTemplate, RecruitmentStageName, TemplateType
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment-email-templates", tags=["recruitment-email-templates"])


def get_recruitment_email_template_repo(
    db: AsyncSession = Depends(get_db),
) -> RecruitmentEmailTemplateRepository:
    return RecruitmentEmailTemplateRepository(db)


class TemplateResponse(BaseModel):
    id: str
    company_id: str | None = None
    stage_name: str
    template_type: str
    name: str
    description: str | None = None
    subject: str
    body_html: str
    body_text: str | None = None
    variables: list[str] = []
    is_active: bool
    is_default: bool
    is_system: bool
    version: int
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TemplateListResponse(BaseModel):
    total: int
    items: list[TemplateResponse]


class TemplateUpdateRequest(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class TemplatePreviewRequest(WeDoBaseModel):
    variables: dict[str, str] | None = Field(default_factory=dict)


class TemplatePreviewResponse(BaseModel):
    subject: str
    body_html: str
    body_text: str
    variables_used: dict[str, str]


class SeedResponse(BaseModel):
    message: str
    created_count: int
    templates: list[TemplateResponse]


class StageInfo(BaseModel):
    name: str
    value: str
    description: str


class TemplateTypeInfo(BaseModel):
    name: str
    value: str
    description: str


def template_to_response(template: RecruitmentEmailTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=str(template.id),
        company_id=template.company_id,
        stage_name=template.stage_name,
        template_type=template.template_type,
        name=template.name,
        description=template.description,
        subject=template.subject,
        body_html=template.body_html,
        body_text=template.body_text,
        variables=template.variables or [],
        is_active=template.is_active,
        is_default=template.is_default,
        is_system=template.is_system,
        version=template.version,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("", response_model=TemplateListResponse)
async def list_recruitment_email_templates(
    stage_name: str | None = Query(None, description="Filter by stage name"),
    template_type: str | None = Query(None, description="Filter by template type: candidate, recruiter, manager"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    company_id: str | None = Query(None, description="Filter by company ID"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all recruitment email templates with optional filtering.
    Returns company-specific templates plus system templates.
    """
    try:
        templates = await list_templates(
            db=db,
            company_id=company_id,
            stage_name=stage_name,
            template_type=template_type,
            is_active=is_active
        )

        return TemplateListResponse(
            total=len(templates),
            items=[template_to_response(t) for t in templates]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing recruitment email templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stages", response_model=list[StageInfo])
async def list_available_stages(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all available recruitment stages for templates.
    """
    stages = [
        StageInfo(name="Candidatura Recebida", value=RecruitmentStageName.CANDIDATE_APPLIED.value, description="Quando o candidato se inscreve"),
        StageInfo(name="Triagem Agendada", value=RecruitmentStageName.SCREENING_SCHEDULED.value, description="Quando a triagem é agendada"),
        StageInfo(name="Triagem Concluída", value=RecruitmentStageName.SCREENING_COMPLETED.value, description="Após conclusão da triagem"),
        StageInfo(name="Entrevista Agendada", value=RecruitmentStageName.INTERVIEW_SCHEDULED.value, description="Quando entrevista é agendada"),
        StageInfo(name="Lembrete de Entrevista", value=RecruitmentStageName.INTERVIEW_REMINDER.value, description="Lembrete antes da entrevista"),
        StageInfo(name="Entrevista Realizada", value=RecruitmentStageName.INTERVIEW_COMPLETED.value, description="Após a entrevista"),
        StageInfo(name="Proposta Enviada", value=RecruitmentStageName.OFFER_SENT.value, description="Quando proposta é enviada"),
        StageInfo(name="Contratado", value=RecruitmentStageName.CANDIDATE_HIRED.value, description="Confirmação de contratação"),
        StageInfo(name="Rejeitado", value=RecruitmentStageName.CANDIDATE_REJECTED.value, description="Feedback de rejeição"),
        StageInfo(name="Mudança de Etapa", value=RecruitmentStageName.STAGE_CHANGED.value, description="Notificação genérica de mudança"),
    ]
    return stages


@router.get("/types", response_model=list[TemplateTypeInfo])
async def list_template_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all available template types.
    """
    types = [
        TemplateTypeInfo(name="Candidato", value=TemplateType.CANDIDATE.value, description="Emails enviados para candidatos"),
        TemplateTypeInfo(name="Recrutador", value=TemplateType.RECRUITER.value, description="Notificações para recrutadores"),
        TemplateTypeInfo(name="Gestor", value=TemplateType.MANAGER.value, description="Notificações para gestores"),
    ]
    return types


@router.get("/variables", response_model=None)
async def list_available_variables(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all available template variables with sample values.
    """
    return {
        "variables": SAMPLE_DATA,
        "description": "Variáveis disponíveis para uso nos templates. Use {{nome_variavel}} no template."
    }


@router.get("/stage/{stage_name}", response_model=TemplateResponse)
async def get_template_by_stage(
    stage_name: str,
    template_type: str = Query("candidate", description="Template type: candidate, recruiter, manager"),
    company_id: str | None = Query(None, description="Company ID for company-specific templates"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the active template for a specific recruitment stage.
    Falls back to system template if no company-specific template exists.
    """
    try:
        template = await get_template_for_stage(
            db=db,
            stage_name=stage_name,
            company_id=company_id,
            template_type=template_type
        )

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"No template found for stage {stage_name} with type {template_type}"
            )

        return template_to_response(template)
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error getting template for stage {stage_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template_by_id(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: RecruitmentEmailTemplateRepository = Depends(get_recruitment_email_template_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a specific template by ID.
    """
    try:
        template = await repo.get_by_id(uuid_module.UUID(template_id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template_to_response(template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    update_data: TemplateUpdateRequest,
    repo: RecruitmentEmailTemplateRepository = Depends(get_recruitment_email_template_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update a recruitment email template.
    System templates cannot be modified directly.
    """
    try:
        template = await repo.get_by_id(uuid_module.UUID(template_id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.is_system:
            raise HTTPException(
                status_code=403,
                detail="System templates cannot be modified. Clone to company first."
            )

        update_fields = update_data.model_dump(exclude_unset=True)
        update_fields["version"] = (template.version or 1) + 1

        updated = await repo.update(template, update_fields)
        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="communication_template_updated", actor="system", target_id=template_id, target_type="email_template", metadata={"fields_updated": list(update_fields.keys())})  # P1-W2-03
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return template_to_response(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedResponse)
async def seed_templates(
    company_id: str | None = Query(None, description="Company ID to seed templates for"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Seed default recruitment email templates.
    If company_id is provided, seeds for that company.
    If not, seeds system-wide templates.
    """
    try:
        created_templates = await seed_default_templates(db=db, company_id=company_id)

        return SeedResponse(
            message=f"Successfully seeded {len(created_templates)} templates" + (f" for company {company_id}" if company_id else " as system templates"),
            created_count=len(created_templates),
            templates=[template_to_response(t) for t in created_templates]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error seeding templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone", response_model=SeedResponse)
async def clone_system_templates(
    company_id: str = Query(..., description="Company ID to clone templates for"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Clone system templates for a specific company.
    This allows companies to customize their own templates.
    """
    try:
        created_templates = await clone_templates_for_company(db=db, company_id=company_id)

        return SeedResponse(
            message=f"Successfully cloned {len(created_templates)} templates for company {company_id}",
            created_count=len(created_templates),
            templates=[template_to_response(t) for t in created_templates]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template_with_data(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    preview_request: TemplatePreviewRequest,
    repo: RecruitmentEmailTemplateRepository = Depends(get_recruitment_email_template_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Preview a template with provided or sample data.
    """
    try:
        template = await repo.get_by_id(uuid_module.UUID(template_id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        variables = {**SAMPLE_DATA}
        if preview_request.variables:
            variables.update(preview_request.variables)

        rendered = render_template(template, variables)

        return TemplatePreviewResponse(
            subject=rendered["subject"],
            body_html=rendered["body_html"],
            body_text=rendered["body_text"],
            variables_used=variables
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage/{stage_name}/preview", response_model=TemplatePreviewResponse)
async def preview_stage_template(
    stage_name: str,
    preview_request: TemplatePreviewRequest,
    template_type: str = Query("candidate"),
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Preview the template for a specific stage with provided or sample data.
    """
    try:
        template = await get_template_for_stage(
            db=db,
            stage_name=stage_name,
            company_id=company_id,
            template_type=template_type
        )

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"No template found for stage {stage_name}"
            )

        variables = {**SAMPLE_DATA}
        if preview_request.variables:
            variables.update(preview_request.variables)

        rendered = render_template(template, variables)

        return TemplatePreviewResponse(
            subject=rendered["subject"],
            body_html=rendered["body_html"],
            body_text=rendered["body_text"],
            variables_used=variables
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing stage template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", response_model=None)
async def delete_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: RecruitmentEmailTemplateRepository = Depends(get_recruitment_email_template_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Delete a recruitment email template.
    System templates cannot be deleted.
    """
    try:
        template = await repo.get_by_id(uuid_module.UUID(template_id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.is_system:
            raise HTTPException(
                status_code=403,
                detail="System templates cannot be deleted"
            )

        await repo.delete(template)

        try:
            await AuditService().log_action(trace_id=get_correlation_id(), company_id=company_id, action_type="communication_template_deleted", actor="system", target_id=template_id, target_type="email_template")  # P1-W2-03
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {"message": "Template deleted successfully", "id": template_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
