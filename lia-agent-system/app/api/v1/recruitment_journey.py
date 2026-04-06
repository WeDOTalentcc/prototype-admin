"""
Recruitment Journey API endpoints for templates, SLAs, and automations.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.recruitment_journey import (
    DEFAULT_AUTOMATIONS,
    DEFAULT_SLAS,
    DEFAULT_TEMPLATES,
    AutomationType,
    RecruitmentAutomation,
    RecruitmentSLA,
    RecruitmentTemplate,
    SLAViolation,
    TemplateType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment-journey", tags=["recruitment-journey"])


def verify_ownership(resource, company_id: uuid.UUID, resource_name: str = "Resource"):
    """Verify that a resource belongs to the specified company."""
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if resource.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


class TemplateCreate(BaseModel):
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


class TemplateUpdate(BaseModel):
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


class SLACreate(BaseModel):
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


class SLAUpdate(BaseModel):
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


class AutomationCreate(BaseModel):
    name: str
    description: str | None = None
    automation_type: str
    trigger_event: str
    trigger_conditions: dict[str, Any] = {}
    action_config: dict[str, Any] = {}
    is_enabled: bool = True


class AutomationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    automation_type: str | None = None
    trigger_event: str | None = None
    trigger_conditions: dict[str, Any] | None = None
    action_config: dict[str, Any] | None = None
    is_enabled: bool | None = None


class AISuggestTemplateRequest(BaseModel):
    job_title: str
    job_description: str | None = None
    job_type: str | None = None
    company_size: str | None = None
    industry: str | None = None


class AIOptimizeSLARequest(BaseModel):
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
    db: AsyncSession = Depends(get_db)
):
    """List recruitment templates for a company."""
    try:
        conditions = [
            RecruitmentTemplate.company_id == uuid.UUID(company_id),
            RecruitmentTemplate.is_active == is_active,
        ]

        if template_type:
            conditions.append(RecruitmentTemplate.template_type == template_type)

        query = select(RecruitmentTemplate).where(and_(*conditions)).offset(skip).limit(limit)
        result = await db.execute(query)
        templates = result.scalars().all()

        return {
            "templates": [t.to_dict() for t in templates],
            "total": len(templates),
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=None)
async def create_template(
    company_id: str = Query(..., description="Company ID"),
    data: TemplateCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new recruitment template."""
    try:
        template = RecruitmentTemplate(
            company_id=uuid.UUID(company_id),
            name=data.name,
            description=data.description,
            template_type=data.template_type,
            stages_config=data.stages_config,
            required_fields=data.required_fields,
            optional_fields=data.optional_fields,
            default_priority=data.default_priority,
            default_sla_days=data.default_sla_days,
            ai_screening_enabled=data.ai_screening_enabled,
            ai_matching_enabled=data.ai_matching_enabled,
            ai_config=data.ai_config,
            is_default=data.is_default,
        )
        
        if data.is_default:
            await db.execute(
                select(RecruitmentTemplate)
                .where(
                    RecruitmentTemplate.company_id == uuid.UUID(company_id),
                    RecruitmentTemplate.is_default == True
                )
            )
            existing = (await db.execute(
                select(RecruitmentTemplate).where(
                    RecruitmentTemplate.company_id == uuid.UUID(company_id),
                    RecruitmentTemplate.is_default == True
                )
            )).scalars().all()
            for t in existing:
                t.is_default = False
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return {"template": template.to_dict(), "message": "Template created successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=None)
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update a recruitment template."""
    try:
        result = await db.execute(
            select(RecruitmentTemplate).where(RecruitmentTemplate.id == uuid.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        verify_ownership(template, uuid.UUID(company_id), "Template")
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        return {"template": template.to_dict(), "message": "Template updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}", response_model=None)
async def delete_template(
    template_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a recruitment template (soft delete)."""
    try:
        result = await db.execute(
            select(RecruitmentTemplate).where(RecruitmentTemplate.id == uuid.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        verify_ownership(template, uuid.UUID(company_id), "Template")
        
        template.is_active = False
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/defaults", response_model=None)
async def get_default_templates():
    """Get default template configurations."""
    return {
        "templates": DEFAULT_TEMPLATES,
        "types": [t.value for t in TemplateType],
    }


@router.post("/templates/initialize", response_model=None)
async def initialize_templates(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Initialize default templates for a company."""
    try:
        result = await db.execute(
            select(RecruitmentTemplate).where(
                RecruitmentTemplate.company_id == uuid.UUID(company_id)
            )
        )
        existing = result.scalars().all()
        
        if existing:
            return {"message": "Templates already initialized", "count": len(existing)}
        
        templates_created = []
        for template_data in DEFAULT_TEMPLATES:
            template = RecruitmentTemplate(
                company_id=uuid.UUID(company_id),
                **template_data,
                is_default=template_data.get("template_type") == "technical",
            )
            db.add(template)
            templates_created.append(template_data["name"])
        
        await db.commit()
        
        return {
            "message": "Templates initialized successfully",
            "count": len(templates_created),
            "templates": templates_created,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error initializing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slas", response_model=None)
async def list_slas(
    company_id: str = Query(..., description="Company ID"),
    stage_name: str | None = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List SLAs for a company."""
    try:
        conditions = [
            RecruitmentSLA.company_id == uuid.UUID(company_id),
            RecruitmentSLA.is_active == is_active,
        ]
        
        if stage_name:
            conditions.append(RecruitmentSLA.stage_name == stage_name)
        
        query = select(RecruitmentSLA).where(and_(*conditions))
        result = await db.execute(query)
        slas = result.scalars().all()
        
        return {
            "slas": [s.to_dict() for s in slas],
            "total": len(slas),
        }
    except Exception as e:
        logger.error(f"Error listing SLAs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slas", response_model=None)
async def create_sla(
    company_id: str = Query(..., description="Company ID"),
    data: SLACreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new SLA."""
    try:
        sla = RecruitmentSLA(
            company_id=uuid.UUID(company_id),
            name=data.name,
            description=data.description,
            stage_id=uuid.UUID(data.stage_id) if data.stage_id else None,
            stage_name=data.stage_name,
            target_days=data.target_days,
            warning_days=data.warning_days,
            critical_days=data.critical_days,
            applies_to_job_types=data.applies_to_job_types,
            applies_to_priority=data.applies_to_priority,
            warning_action=data.warning_action,
            critical_action=data.critical_action,
        )
        
        db.add(sla)
        await db.commit()
        await db.refresh(sla)
        
        return {"sla": sla.to_dict(), "message": "SLA created successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/slas/{sla_id}", response_model=None)
async def update_sla(
    sla_id: str,
    data: SLAUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update an SLA."""
    try:
        result = await db.execute(
            select(RecruitmentSLA).where(RecruitmentSLA.id == uuid.UUID(sla_id))
        )
        sla = result.scalar_one_or_none()
        
        verify_ownership(sla, uuid.UUID(company_id), "SLA")
        
        update_data = data.dict(exclude_unset=True)
        
        if "stage_id" in update_data and update_data["stage_id"]:
            update_data["stage_id"] = uuid.UUID(update_data["stage_id"])
        
        for field, value in update_data.items():
            setattr(sla, field, value)
        
        sla.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(sla)
        
        return {"sla": sla.to_dict(), "message": "SLA updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/slas/{sla_id}", response_model=None)
async def delete_sla(
    sla_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete an SLA (soft delete)."""
    try:
        result = await db.execute(
            select(RecruitmentSLA).where(RecruitmentSLA.id == uuid.UUID(sla_id))
        )
        sla = result.scalar_one_or_none()
        
        verify_ownership(sla, uuid.UUID(company_id), "SLA")
        
        sla.is_active = False
        sla.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "SLA deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slas/defaults", response_model=None)
async def get_default_slas():
    """Get default SLA configurations."""
    return {"slas": DEFAULT_SLAS}


@router.post("/slas/initialize", response_model=None)
async def initialize_slas(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Initialize default SLAs for a company."""
    try:
        result = await db.execute(
            select(RecruitmentSLA).where(
                RecruitmentSLA.company_id == uuid.UUID(company_id)
            )
        )
        existing = result.scalars().all()
        
        if existing:
            return {"message": "SLAs already initialized", "count": len(existing)}
        
        slas_created = []
        for sla_data in DEFAULT_SLAS:
            sla = RecruitmentSLA(
                company_id=uuid.UUID(company_id),
                **sla_data,
            )
            db.add(sla)
            slas_created.append(sla_data["name"])
        
        await db.commit()
        
        return {
            "message": "SLAs initialized successfully",
            "count": len(slas_created),
            "slas": slas_created,
        }
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_db)
):
    """Get SLA violations for a company."""
    try:
        conditions = [SLAViolation.company_id == uuid.UUID(company_id)]
        
        if job_id:
            conditions.append(SLAViolation.job_id == uuid.UUID(job_id))
        
        if violation_type:
            conditions.append(SLAViolation.violation_type == violation_type)
        
        if resolved is not None:
            conditions.append(SLAViolation.resolved == resolved)
        
        count_query = select(func.count(SLAViolation.id)).where(and_(*conditions))
        total = (await db.execute(count_query)).scalar()
        
        query = (
            select(SLAViolation)
            .where(and_(*conditions))
            .order_by(SLAViolation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        violations = result.scalars().all()
        
        return {
            "violations": [v.to_dict() for v in violations],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error getting SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations", response_model=None)
async def list_automations(
    company_id: str = Query(..., description="Company ID"),
    automation_type: str | None = None,
    trigger_event: str | None = None,
    is_enabled: bool | None = None,
    db: AsyncSession = Depends(get_db)
):
    """List automations for a company."""
    try:
        conditions = [RecruitmentAutomation.company_id == uuid.UUID(company_id)]
        
        if automation_type:
            conditions.append(RecruitmentAutomation.automation_type == automation_type)
        
        if trigger_event:
            conditions.append(RecruitmentAutomation.trigger_event == trigger_event)
        
        if is_enabled is not None:
            conditions.append(RecruitmentAutomation.is_enabled == is_enabled)
        
        query = select(RecruitmentAutomation).where(and_(*conditions))
        result = await db.execute(query)
        automations = result.scalars().all()
        
        return {
            "automations": [a.to_dict() for a in automations],
            "total": len(automations),
        }
    except Exception as e:
        logger.error(f"Error listing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations", response_model=None)
async def create_automation(
    company_id: str = Query(..., description="Company ID"),
    data: AutomationCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new automation."""
    try:
        automation = RecruitmentAutomation(
            company_id=uuid.UUID(company_id),
            name=data.name,
            description=data.description,
            automation_type=data.automation_type,
            trigger_event=data.trigger_event,
            trigger_conditions=data.trigger_conditions,
            action_config=data.action_config,
            is_enabled=data.is_enabled,
        )
        
        db.add(automation)
        await db.commit()
        await db.refresh(automation)
        
        return {"automation": automation.to_dict(), "message": "Automation created successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automations/{automation_id}", response_model=None)
async def update_automation(
    automation_id: str,
    data: AutomationUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update an automation."""
    try:
        result = await db.execute(
            select(RecruitmentAutomation).where(RecruitmentAutomation.id == uuid.UUID(automation_id))
        )
        automation = result.scalar_one_or_none()
        
        verify_ownership(automation, uuid.UUID(company_id), "Automation")
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(automation, field, value)
        
        automation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(automation)
        
        return {"automation": automation.to_dict(), "message": "Automation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automations/{automation_id}", response_model=None)
async def delete_automation(
    automation_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete an automation."""
    try:
        result = await db.execute(
            select(RecruitmentAutomation).where(RecruitmentAutomation.id == uuid.UUID(automation_id))
        )
        automation = result.scalar_one_or_none()
        
        verify_ownership(automation, uuid.UUID(company_id), "Automation")
        
        await db.delete(automation)
        await db.commit()
        
        return {"message": "Automation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations/defaults", response_model=None)
async def get_default_automations():
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
    db: AsyncSession = Depends(get_db)
):
    """Initialize default automations for a company."""
    try:
        result = await db.execute(
            select(RecruitmentAutomation).where(
                RecruitmentAutomation.company_id == uuid.UUID(company_id)
            )
        )
        existing = result.scalars().all()
        
        if existing:
            return {"message": "Automations already initialized", "count": len(existing)}
        
        automations_created = []
        for automation_data in DEFAULT_AUTOMATIONS:
            automation = RecruitmentAutomation(
                company_id=uuid.UUID(company_id),
                **automation_data,
            )
            db.add(automation)
            automations_created.append(automation_data["name"])
        
        await db.commit()
        
        return {
            "message": "Automations initialized successfully",
            "count": len(automations_created),
            "automations": automations_created,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error initializing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/suggest-template", response_model=None)
async def ai_suggest_template(
    company_id: str = Query(..., description="Company ID"),
    data: AISuggestTemplateRequest = None,
    db: AsyncSession = Depends(get_db)
):
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
        
        result = await db.execute(
            select(RecruitmentTemplate).where(
                RecruitmentTemplate.company_id == uuid.UUID(company_id),
                RecruitmentTemplate.template_type == suggested_type,
                RecruitmentTemplate.is_active == True
            )
        )
        company_template = result.scalar_one_or_none()
        
        return {
            "suggested_template_type": suggested_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "default_template": template_data,
            "company_template": company_template.to_dict() if company_template else None,
            "all_types": [t.value for t in TemplateType],
        }
    except Exception as e:
        logger.error(f"Error suggesting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/optimize-sla", response_model=None)
async def ai_optimize_sla(
    company_id: str = Query(..., description="Company ID"),
    data: AIOptimizeSLARequest = None,
    db: AsyncSession = Depends(get_db)
):
    """AI-powered SLA optimization based on historical data."""
    try:
        result = await db.execute(
            select(RecruitmentSLA).where(
                RecruitmentSLA.company_id == uuid.UUID(company_id),
                RecruitmentSLA.is_active == True
            )
        )
        current_slas = result.scalars().all()
        
        violations_query = select(SLAViolation).where(
            SLAViolation.company_id == uuid.UUID(company_id)
        )
        violations_result = await db.execute(violations_query)
        violations = violations_result.scalars().all()
        
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
    except Exception as e:
        logger.error(f"Error optimizing SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))
