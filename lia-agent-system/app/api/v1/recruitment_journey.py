"""
Recruitment Journey API endpoints for templates, SLAs, and automations.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.domains.recruitment_journey.dependencies import get_recruitment_journey_repo
from app.domains.recruitment_journey.repositories.recruitment_journey_repository import (
    RecruitmentJourneyRepository,
)
from app.models.recruitment_journey import (
    DEFAULT_AUTOMATIONS,
    DEFAULT_SLAS,
    DEFAULT_TEMPLATES,
    AutomationType,
    TemplateType,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment-journey", tags=["recruitment-journey"])


def verify_ownership(resource, company_id: uuid.UUID, resource_name: str = "Resource"):
    """Verify that a resource belongs to the specified company."""
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if resource.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


class TemplateCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    template_type: str = "technical"
    stages_config: list[dict[str, Any]] = []
    required_fields: list[str] = []
    optional_fields: list[str] = []
    default_priority: str = "normal"
    default_sla_days: int = 30
    ai_screening_enabled: bool = True
    ai_matching_enabled: bool = True
    ai_config: dict[str, Any] = {}
    is_default: bool = False


class TemplateUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    template_type: str | None = None
    stages_config: list[dict[str, Any]] | None = None
    required_fields: list[str] | None = None
    optional_fields: list[str] | None = None
    default_priority: str | None = None
    default_sla_days: int | None = None
    ai_screening_enabled: bool | None = None
    ai_matching_enabled: bool | None = None
    ai_config: dict[str, Any] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class SLACreate(WeDoBaseModel):
    name: str
    description: str | None = None
    stage_id: str | None = None
    stage_name: str | None = None
    target_days: int
    warning_days: int | None = None
    critical_days: int | None = None
    applies_to_job_types: list[str] = []
    applies_to_priority: list[str] = []
    warning_action: dict[str, Any] = {}
    critical_action: dict[str, Any] = {}


class SLAUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    stage_id: str | None = None
    stage_name: str | None = None
    target_days: int | None = None
    warning_days: int | None = None
    critical_days: int | None = None
    applies_to_job_types: list[str] | None = None
    applies_to_priority: list[str] | None = None
    warning_action: dict[str, Any] | None = None
    critical_action: dict[str, Any] | None = None
    is_active: bool | None = None


class AutomationCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    automation_type: str
    trigger_event: str
    trigger_conditions: dict[str, Any] = {}
    action_config: dict[str, Any] = {}
    is_enabled: bool = True


class AutomationUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    automation_type: str | None = None
    trigger_event: str | None = None
    trigger_conditions: dict[str, Any] | None = None
    action_config: dict[str, Any] | None = None
    is_enabled: bool | None = None


class AISuggestTemplateRequest(WeDoBaseModel):
    job_title: str
    job_description: str | None = None
    job_type: str | None = None
    company_size: str | None = None
    industry: str | None = None


class AIOptimizeSLARequest(WeDoBaseModel):
    historical_data: dict[str, Any] | None = None
    target_metrics: dict[str, Any] | None = None
    current_slas: list[dict[str, Any]] | None = None


@router.get("/templates", response_model=None)
async def list_templates(
    company_id: str = Query(..., description="Company ID"),
    template_type: str | None = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(200, ge=1, le=500, description="Max templates to return"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List recruitment templates for a company."""
    try:
        templates = await repo.list_templates(
            company_id=uuid.UUID(company_id),
            template_type=template_type,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        return {
            "templates": [t.to_dict() for t in templates],
            "total": len(templates),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=None)
async def create_template(
    company_id: str = Query(..., description="Company ID"),
    data: TemplateCreate = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new recruitment template."""
    try:
        template_data = data.dict()
        is_default = template_data.pop("is_default", False)
        template = await repo.create_template(
            company_id=uuid.UUID(company_id),
            data={**template_data, "is_default": is_default},
            is_default=is_default,
        )
        return {"template": template.to_dict(), "message": "Template created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=None)
async def update_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: TemplateUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a recruitment template."""
    try:
        template = await repo.get_template(uuid.UUID(template_id))
        verify_ownership(template, uuid.UUID(company_id), "Template")

        update_data = data.dict(exclude_unset=True)
        template = await repo.update_template(template, update_data)
        return {"template": template.to_dict(), "message": "Template updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}", response_model=None)
async def delete_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete a recruitment template (soft delete)."""
    try:
        template = await repo.get_template(uuid.UUID(template_id))
        verify_ownership(template, uuid.UUID(company_id), "Template")

        await repo.soft_delete_template(template)
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/defaults", response_model=None)
async def get_default_templates(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get default template configurations."""
    return {
        "templates": DEFAULT_TEMPLATES,
        "types": [t.value for t in TemplateType],
    }


@router.post("/templates/initialize", response_model=None)
async def initialize_templates(
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Initialize default templates for a company."""
    try:
        existing = await repo.get_templates_for_company(uuid.UUID(company_id))
        if existing:
            return {"message": "Templates already initialized", "count": len(existing)}

        names = await repo.initialize_templates(uuid.UUID(company_id))
        return {
            "message": "Templates initialized successfully",
            "count": len(names),
            "templates": names,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slas", response_model=None)
async def list_slas(
    company_id: str = Query(..., description="Company ID"),
    stage_name: str | None = None,
    is_active: bool = True,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List SLAs for a company."""
    try:
        slas = await repo.list_slas(
            company_id=uuid.UUID(company_id),
            stage_name=stage_name,
            is_active=is_active,
        )
        return {
            "slas": [s.to_dict() for s in slas],
            "total": len(slas),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing SLAs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slas", response_model=None)
async def create_sla(
    company_id: str = Query(..., description="Company ID"),
    data: SLACreate = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new SLA."""
    try:
        sla_data = data.dict()
        if sla_data.get("stage_id"):
            sla_data["stage_id"] = uuid.UUID(sla_data["stage_id"])
        sla = await repo.create_sla(company_id=uuid.UUID(company_id), data=sla_data)
        return {"sla": sla.to_dict(), "message": "SLA created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/slas/{sla_id}", response_model=None)
async def update_sla(
    sla_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: SLAUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an SLA."""
    try:
        sla = await repo.get_sla(uuid.UUID(sla_id))
        verify_ownership(sla, uuid.UUID(company_id), "SLA")

        update_data = data.dict(exclude_unset=True)
        if "stage_id" in update_data and update_data["stage_id"]:
            update_data["stage_id"] = uuid.UUID(update_data["stage_id"])

        sla = await repo.update_sla(sla, update_data)
        return {"sla": sla.to_dict(), "message": "SLA updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/slas/{sla_id}", response_model=None)
async def delete_sla(
    sla_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete an SLA (soft delete)."""
    try:
        sla = await repo.get_sla(uuid.UUID(sla_id))
        verify_ownership(sla, uuid.UUID(company_id), "SLA")

        await repo.soft_delete_sla(sla)
        return {"message": "SLA deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slas/defaults", response_model=None)
async def get_default_slas(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get default SLA configurations."""
    return {"slas": DEFAULT_SLAS}


@router.post("/slas/initialize", response_model=None)
async def initialize_slas(
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Initialize default SLAs for a company."""
    try:
        existing = await repo.get_slas_for_company(uuid.UUID(company_id))
        if existing:
            return {"message": "SLAs already initialized", "count": len(existing)}

        names = await repo.initialize_slas(uuid.UUID(company_id))
        return {
            "message": "SLAs initialized successfully",
            "count": len(names),
            "slas": names,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing SLAs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slas/violations", response_model=None)
async def get_sla_violations(
    company_id: str = Query(..., description="Company ID"),
    job_id: str | None = None,
    violation_type: str | None = None,
    resolved: bool | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get SLA violations for a company."""
    try:
        violations, total = await repo.list_violations(
            company_id=uuid.UUID(company_id),
            job_id=uuid.UUID(job_id) if job_id else None,
            violation_type=violation_type,
            resolved=resolved,
            limit=limit,
            offset=offset,
        )
        return {
            "violations": [v.to_dict() for v in violations],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations", response_model=None)
async def list_automations(
    company_id: str = Query(..., description="Company ID"),
    automation_type: str | None = None,
    trigger_event: str | None = None,
    is_enabled: bool | None = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List automations for a company."""
    try:
        automations = await repo.list_automations(
            company_id=uuid.UUID(company_id),
            automation_type=automation_type,
            trigger_event=trigger_event,
            is_enabled=is_enabled,
        )
        return {
            "automations": [a.to_dict() for a in automations],
            "total": len(automations),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations", response_model=None)
async def create_automation(
    company_id: str = Query(..., description="Company ID"),
    data: AutomationCreate = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new automation."""
    try:
        automation = await repo.create_automation(
            company_id=uuid.UUID(company_id),
            data=data.dict(),
        )
        return {"automation": automation.to_dict(), "message": "Automation created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automations/{automation_id}", response_model=None)
async def update_automation(
    automation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: AutomationUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an automation."""
    try:
        automation = await repo.get_automation(uuid.UUID(automation_id))
        verify_ownership(automation, uuid.UUID(company_id), "Automation")

        update_data = data.dict(exclude_unset=True)
        automation = await repo.update_automation(automation, update_data)
        return {"automation": automation.to_dict(), "message": "Automation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automations/{automation_id}", response_model=None)
async def delete_automation(
    automation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete an automation."""
    try:
        automation = await repo.get_automation(uuid.UUID(automation_id))
        verify_ownership(automation, uuid.UUID(company_id), "Automation")

        await repo.delete_automation(automation)
        return {"message": "Automation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations/defaults", response_model=None)
async def get_default_automations(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get default automation configurations."""
    return {
        "automations": DEFAULT_AUTOMATIONS,
        "types": [t.value for t in AutomationType],
        "trigger_events": [
            "candidate_applied",
            "stage_changed",
            "interview_scheduled",
            "interview_completed",
            "offer_sent",
            "offer_accepted",
            "offer_declined",
            "sla_warning",
            "sla_critical",
            "document_uploaded",
        ],
    }


@router.post("/automations/initialize", response_model=None)
async def initialize_automations(
    company_id: str = Query(..., description="Company ID"),
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Initialize default automations for a company."""
    try:
        existing = await repo.get_automations_for_company(uuid.UUID(company_id))
        if existing:
            return {"message": "Automations already initialized", "count": len(existing)}

        names = await repo.initialize_automations(uuid.UUID(company_id))
        return {
            "message": "Automations initialized successfully",
            "count": len(names),
            "automations": names,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/suggest-template", response_model=None)
async def ai_suggest_template(
    company_id: str = Query(..., description="Company ID"),
    data: AISuggestTemplateRequest = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """AI-powered template suggestion based on job details."""
    try:
        job_title_lower = data.job_title.lower() if data.job_title else ""
        job_type = data.job_type or ""

        suggested_type = "technical"
        confidence = 0.7
        reasoning = []

        executive_keywords = ["director", "diretor", "vp", "vice", "cto", "cfo", "ceo", "head", "gerente geral", "c-level"]
        technical_keywords = ["developer", "desenvolvedor", "engineer", "engenheiro", "programador", "software", "data", "devops", "sre", "backend", "frontend", "fullstack"]
        operational_keywords = ["operador", "auxiliar", "assistente", "atendente", "vendedor", "recepcionista"]
        intern_keywords = ["estagio", "estágio", "trainee", "jovem aprendiz", "intern"]

        if any(kw in job_title_lower for kw in executive_keywords):
            suggested_type = "executive"
            confidence = 0.85
            reasoning.append("Cargo de liderança ou C-level identificado")
        elif any(kw in job_title_lower for kw in intern_keywords):
            suggested_type = "intern"
            confidence = 0.9
            reasoning.append("Programa de estágio ou trainee identificado")
        elif any(kw in job_title_lower for kw in technical_keywords):
            suggested_type = "technical"
            confidence = 0.85
            reasoning.append("Posição técnica identificada")
        elif any(kw in job_title_lower for kw in operational_keywords):
            suggested_type = "operational"
            confidence = 0.8
            reasoning.append("Posição operacional identificada")

        if job_type:
            if job_type.lower() in ["mass", "volume", "massa"]:
                suggested_type = "mass_hiring"
                confidence = 0.9
                reasoning.append("Contratação em massa indicada pelo tipo de vaga")

        template_data = None
        for t in DEFAULT_TEMPLATES:
            if t["template_type"] == suggested_type:
                template_data = t
                break

        company_template = await repo.get_active_template_by_type(
            company_id=uuid.UUID(company_id),
            template_type=suggested_type,
        )

        return {
            "suggested_template_type": suggested_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "default_template": template_data,
            "company_template": company_template.to_dict() if company_template else None,
            "all_types": [t.value for t in TemplateType],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/optimize-sla", response_model=None)
async def ai_optimize_sla(
    company_id: str = Query(..., description="Company ID"),
    data: AIOptimizeSLARequest = None,
    repo: RecruitmentJourneyRepository = Depends(get_recruitment_journey_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """AI-powered SLA optimization based on historical data."""
    try:
        current_slas = await repo.get_active_slas_for_company(uuid.UUID(company_id))
        violations = await repo.get_violations_for_company(uuid.UUID(company_id))

        recommendations = []

        for sla in current_slas:
            sla_violations = [v for v in violations if str(v.sla_id) == str(sla.id)]
            violation_count = len(sla_violations)

            if violation_count > 10:
                recommendations.append({
                    "sla_id": str(sla.id),
                    "sla_name": sla.name,
                    "recommendation": "increase_target",
                    "current_target_days": sla.target_days,
                    "suggested_target_days": int(sla.target_days * 1.2),
                    "reason": f"Alto número de violações ({violation_count}). Considere aumentar o prazo em 20%.",
                    "confidence": 0.75,
                })
            elif violation_count == 0 and sla.target_days > 5:
                recommendations.append({
                    "sla_id": str(sla.id),
                    "sla_name": sla.name,
                    "recommendation": "decrease_target",
                    "current_target_days": sla.target_days,
                    "suggested_target_days": max(2, int(sla.target_days * 0.8)),
                    "reason": "Sem violações recentes. O SLA pode estar muito flexível.",
                    "confidence": 0.6,
                })

        if not current_slas:
            for default_sla in DEFAULT_SLAS:
                recommendations.append({
                    "sla_name": default_sla["name"],
                    "recommendation": "create",
                    "suggested_config": default_sla,
                    "reason": "SLA padrão recomendado não encontrado",
                    "confidence": 0.8,
                })

        return {
            "recommendations": recommendations,
            "current_slas_count": len(current_slas),
            "total_violations": len(violations),
            "analysis_summary": {
                "overall_compliance": f"{100 - (len(violations) / max(len(current_slas), 1) * 10):.1f}%",
                "most_violated_stages": list(set([v.stage_name for v in violations[:5]])),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
