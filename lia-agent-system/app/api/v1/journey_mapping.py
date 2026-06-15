"""
Journey Mapping API endpoints for Admin section.
Manages recruitment journey blueprints, steps, and integrations.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.repositories.dependencies import get_journey_mapping_repo
from app.repositories.journey_mapping_repository import JourneyMappingRepository
from app.domains.ai.services.llm import llm_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journey-mapping", tags=["journey-mapping"])


def verify_ownership(resource, company_id: uuid.UUID, resource_name: str = "Resource"):
    """Verify that a resource belongs to the specified company."""
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if resource.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


class JourneyStepCreate(WeDoBaseModel):
    blueprint_id: uuid.UUID
    name: str
    description: str | None = None
    step_type: str
    order: int = 0
    is_enabled: bool = True
    is_required: bool = True
    config: dict[str, Any] = {}
    sla_days: int | None = None
    responsible_role: str | None = None
    automation_enabled: bool = False
    automation_config: dict[str, Any] = {}
    ai_enabled: bool = False
    ai_config: dict[str, Any] = {}


class JourneyStepUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    step_type: str | None = None
    order: int | None = None
    is_enabled: bool | None = None
    is_required: bool | None = None
    config: dict[str, Any] | None = None
    sla_days: int | None = None
    responsible_role: str | None = None
    automation_enabled: bool | None = None
    automation_config: dict[str, Any] | None = None
    ai_enabled: bool | None = None
    ai_config: dict[str, Any] | None = None


class JourneyStepResponse(BaseModel):
    id: uuid.UUID
    blueprint_id: uuid.UUID
    name: str
    description: str | None
    step_type: str
    order: int
    is_enabled: bool
    is_required: bool
    config: dict[str, Any]
    sla_days: int | None
    responsible_role: str | None
    automation_enabled: bool
    automation_config: dict[str, Any]
    ai_enabled: bool
    ai_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyIntegrationCreate(WeDoBaseModel):
    blueprint_id: uuid.UUID
    name: str
    integration_type: str
    provider: str | None = None
    is_enabled: bool = False
    connection_config: dict[str, Any] = {}
    field_mappings: dict[str, Any] = {}
    sync_direction: str = "bidirectional"
    sync_frequency: str = "realtime"


class JourneyIntegrationUpdate(WeDoBaseModel):
    name: str | None = None
    integration_type: str | None = None
    provider: str | None = None
    is_enabled: bool | None = None
    is_connected: bool | None = None
    connection_config: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    sync_direction: str | None = None
    sync_frequency: str | None = None


class JourneyIntegrationResponse(BaseModel):
    id: uuid.UUID
    blueprint_id: uuid.UUID
    name: str
    integration_type: str
    provider: str | None
    is_enabled: bool
    is_connected: bool
    connection_config: dict[str, Any]
    field_mappings: dict[str, Any]
    sync_direction: str
    sync_frequency: str
    last_sync_at: datetime | None
    sync_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyBlueprintCreate(WeDoBaseModel):
    name: str = "Jornada Principal"
    description: str | None = None
    vacancy_origin: str | None = None
    has_external_wfp: bool = False
    has_internal_wfp: bool = False


class JourneyBlueprintUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    wizard_step: int | None = None
    wizard_completed: bool | None = None
    wizard_data: dict[str, Any] | None = None
    ai_summary: str | None = None
    ai_recommendations: list[dict[str, Any]] | None = None
    vacancy_origin: str | None = None
    has_external_wfp: bool | None = None
    has_internal_wfp: bool | None = None


class JourneyBlueprintResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: str | None
    status: str
    wizard_step: int
    wizard_completed: bool
    wizard_data: dict[str, Any]
    ai_summary: str | None
    ai_recommendations: list[dict[str, Any]]
    vacancy_origin: str | None
    has_external_wfp: bool
    has_internal_wfp: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    steps: list[JourneyStepResponse] = []
    integrations: list[JourneyIntegrationResponse] = []

    class Config:
        from_attributes = True


class WizardStepData(BaseModel):
    model_config = ConfigDict(extra='forbid')

    blueprint_id: uuid.UUID
    step_number: int
    data: dict[str, Any]


class WizardCompleteData(BaseModel):
    """Complete wizard data submitted from frontend.

    # T-06 R2 fix canonical: company_id field removed.
    # Multi-tenancy via Depends(require_company_id) in complete_wizard handler.
    """
    model_config = ConfigDict(extra='forbid')

    vagas_abertura: str = Field(..., description="Origin type: requisicao_formal, demanda_direta, planejamento_anual")
    sistemas_usados: list[str] = Field(default=[], description="List of system IDs used")
    etapas_processo: list[str] = Field(default=[], description="List of process step names")
    automacoes_desejadas: list[str] = Field(default=[], description="List of automation IDs")
    canais_publicacao: list[str] = Field(default=[], description="List of publication channel IDs")
    careers_page_url: str | None = Field(None, description="URL of careers page if site_proprio selected")


class AIRecommendationsRequest(WeDoBaseModel):
    blueprint_id: uuid.UUID
    context: dict[str, Any] | None = {}


class AIRecommendationsResponse(BaseModel):
    recommendations: list[dict[str, Any]]
    summary: str
    suggested_steps: list[dict[str, Any]]


SYSTEM_CATEGORY_MAP = {
    "gupy": "ats", "pandape": "ats", "merge": "ats", "greenhouse": "ats",
    "workday": "workforce_planning", "sap_sf": "workforce_planning",
    "senior": "hris", "totvs": "hris", "adp": "hris",
    "hackerrank": "technical_assessment", "codility": "technical_assessment",
    "mindsight": "assessment",
    "docusign": "digital_signature", "clicksign": "digital_signature",
    "slack": "communication", "teams": "communication"
}

CHANNEL_NAMES = {
    "linkedin_jobs": "LinkedIn Jobs",
    "indeed": "Indeed",
    "glassdoor": "Glassdoor",
    "catho": "Catho",
    "infojobs": "InfoJobs",
    "site_proprio": "Site Próprio",
    "universidades": "Universidades",
    "redes_sociais": "Redes Sociais"
}

STEP_TYPE_MAP = {
    "Triagem de CVs": "cv_screening",
    "Entrevista Inicial": "initial_interview",
    "Teste Técnico": "technical_test",
    "Entrevista Técnica": "technical_interview",
    "Entrevista com Gestor": "manager_interview",
    "Assessment Cultural": "cultural_assessment",
    "Proposta": "offer",
    "Onboarding": "onboarding"
}


@router.post("/wizard/complete", response_model=JourneyBlueprintResponse)
async def complete_wizard(
    data: WizardCompleteData,
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Complete the journey mapping wizard by creating:
    - JourneyBlueprint with all wizard data
    - JourneyStep for each process step
    - JourneyIntegration for each system and publication channel
    """
    try:
        blueprint_kwargs = {
            "company_id": uuid.UUID(company_id) if isinstance(company_id, str) else company_id,  # T-06 R2 from JWT
            "name": "Jornada de Recrutamento",
            "description": f"Configurado via wizard em {datetime.utcnow().strftime('%d/%m/%Y')}",
            "vacancy_origin": data.vagas_abertura,
            "status": "active",
            "wizard_step": 5,
            "wizard_completed": True,
            "wizard_data": {
                "vagas_abertura": data.vagas_abertura,
                "sistemas_usados": data.sistemas_usados,
                "etapas_processo": data.etapas_processo,
                "automacoes_desejadas": data.automacoes_desejadas,
                "canais_publicacao": data.canais_publicacao,
                "careers_page_url": data.careers_page_url
            }
        }

        steps_data = []
        for order, etapa_name in enumerate(data.etapas_processo, start=1):
            step_type = STEP_TYPE_MAP.get(etapa_name, "custom")

            ai_enabled = False
            automation_enabled = False
            automation_config = {}

            if etapa_name == "Triagem de CVs" and "auto-screening" in data.automacoes_desejadas:
                ai_enabled = True
                automation_enabled = True
                automation_config = {"type": "cv_screening", "threshold": 0.7}

            if "Entrevista" in etapa_name and "auto-schedule" in data.automacoes_desejadas:
                automation_enabled = True
                automation_config = {"type": "scheduling", "calendar_integration": True}

            steps_data.append({
                "name": etapa_name,
                "description": f"Etapa de {etapa_name.lower()} do processo seletivo",
                "step_type": step_type,
                "order": order,
                "is_enabled": True,
                "is_required": True,
                "sla_days": 3 if "Triagem" in etapa_name else 5,
                "automation_enabled": automation_enabled,
                "automation_config": automation_config,
                "ai_enabled": ai_enabled,
                "ai_config": {"agent": "ScreeningAgent"} if ai_enabled else {}
            })

        integrations_data = []
        for sistema_id in data.sistemas_usados:
            category = SYSTEM_CATEGORY_MAP.get(sistema_id, "other")
            integrations_data.append({
                "name": sistema_id.replace("_", " ").title(),
                "integration_type": category,
                "provider": sistema_id,
                "is_enabled": True,
                "is_connected": False,
                "sync_direction": "bidirectional",
                "sync_frequency": "realtime"
            })

        for canal_id in data.canais_publicacao:
            canal_name = CHANNEL_NAMES.get(canal_id, canal_id.replace("_", " ").title())
            config = {}
            if canal_id == "site_proprio" and data.careers_page_url:
                config = {"careers_url": data.careers_page_url}

            integrations_data.append({
                "name": canal_name,
                "integration_type": "job_board",
                "provider": canal_id,
                "is_enabled": True,
                "is_connected": False,
                "connection_config": config,
                "sync_direction": "outbound",
                "sync_frequency": "on_demand"
            })

        blueprint = await repo.complete_wizard(
            blueprint_kwargs=blueprint_kwargs,
            steps_data=steps_data,
            integrations_data=integrations_data
        )

        logger.info(
            f"Wizard completed for company {data.company_id}: "
            f"{len(data.etapas_processo)} steps, "
            f"{len(data.sistemas_usados) + len(data.canais_publicacao)} integrations"
        )
        return blueprint

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing wizard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/blueprint", response_model=JourneyBlueprintResponse)
async def get_company_blueprint(
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get the company's journey blueprint with steps and integrations."""
    try:
        blueprint = await repo.get_company_blueprint(company_id)

        if not blueprint:
            raise HTTPException(status_code=404, detail="No journey blueprint found for this company")

        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching journey blueprint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/blueprint", response_model=JourneyBlueprintResponse)
async def create_blueprint(
    data: JourneyBlueprintCreate,
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new journey blueprint for a company."""
    try:
        blueprint = await repo.create_blueprint_with_commit(
            company_id=company_id,
            name=data.name,
            description=data.description,
            vacancy_origin=data.vacancy_origin,
            has_external_wfp=data.has_external_wfp,
            has_internal_wfp=data.has_internal_wfp,
            status="draft"
        )

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created journey blueprint: {blueprint.name} for company {company_id}")
        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating journey blueprint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/blueprint/{blueprint_id}", response_model=JourneyBlueprintResponse)
async def update_blueprint(
    blueprint_id: uuid.UUID,
    data: JourneyBlueprintUpdate,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an existing journey blueprint."""
    try:
        blueprint = await repo.get_blueprint_with_relations(blueprint_id)

        verify_ownership(blueprint, company_id, "Journey blueprint")

        update_data = data.model_dump(exclude_unset=True)
        blueprint = await repo.update_blueprint(blueprint, update_data)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated journey blueprint: {blueprint.id}")
        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating journey blueprint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/wizard/step", response_model=JourneyBlueprintResponse)
async def save_wizard_step(
    data: WizardStepData,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Save wizard step data and update progress."""
    try:
        blueprint = await repo.get_blueprint_with_relations(data.blueprint_id)

        verify_ownership(blueprint, company_id, "Journey blueprint")

        blueprint = await repo.save_wizard_step(blueprint, data.step_number, data.data)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Saved wizard step {data.step_number} for blueprint: {blueprint.id}")
        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving wizard step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/steps", response_model=list[JourneyStepResponse])
async def get_steps(
    blueprint_id: uuid.UUID = Query(..., description="Blueprint ID"),
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all steps for a journey blueprint."""
    try:
        blueprint = await repo.get_blueprint(blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        steps = await repo.list_steps(blueprint_id)
        return steps
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching journey steps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/steps", response_model=JourneyStepResponse)
async def create_step(
    data: JourneyStepCreate,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new journey step."""
    try:
        blueprint = await repo.get_blueprint(data.blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        step = await repo.create_step(**data.model_dump())

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created journey step: {step.name}")
        return step
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating journey step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/steps/{step_id}", response_model=JourneyStepResponse)
async def update_step(
    step_id: uuid.UUID,
    data: JourneyStepUpdate,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an existing journey step."""
    try:
        step = await repo.get_step(step_id)

        if not step:
            raise HTTPException(status_code=404, detail="Journey step not found")

        blueprint = await repo.get_blueprint(step.blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        update_data = data.model_dump(exclude_unset=True)
        step = await repo.update_step(step, update_data)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated journey step: {step.id}")
        return step
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating journey step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/steps/{step_id}", response_model=None)
async def delete_step(
    step_id: uuid.UUID,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete a journey step."""
    try:
        step = await repo.get_step(step_id)

        if not step:
            raise HTTPException(status_code=404, detail="Journey step not found")

        blueprint = await repo.get_blueprint(step.blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        await repo.delete_step(step)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Deleted journey step: {step_id}")
        return {"success": True, "message": "Step deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting journey step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/integrations", response_model=list[JourneyIntegrationResponse])
async def get_integrations(
    blueprint_id: uuid.UUID = Query(..., description="Blueprint ID"),
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all integrations for a journey blueprint."""
    try:
        blueprint = await repo.get_blueprint(blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        integrations = await repo.list_integrations(blueprint_id)
        return integrations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching journey integrations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/integrations", response_model=JourneyIntegrationResponse)
async def create_integration(
    data: JourneyIntegrationCreate,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new journey integration."""
    try:
        blueprint = await repo.get_blueprint(data.blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        integration = await repo.create_integration(**data.model_dump())

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created journey integration: {integration.name}")
        return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating journey integration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/integrations/{integration_id}", response_model=JourneyIntegrationResponse)
async def update_integration(
    integration_id: uuid.UUID,
    data: JourneyIntegrationUpdate,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an existing journey integration."""
    try:
        integration = await repo.get_integration(integration_id)

        if not integration:
            raise HTTPException(status_code=404, detail="Journey integration not found")

        blueprint = await repo.get_blueprint(integration.blueprint_id)
        verify_ownership(blueprint, company_id, "Journey blueprint")

        update_data = data.model_dump(exclude_unset=True)
        integration = await repo.update_integration(integration, update_data)

        logger.info(f"Updated journey integration: {integration.id}")
        return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating journey integration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/recommendations", response_model=AIRecommendationsResponse)
async def get_ai_recommendations(
    data: AIRecommendationsRequest,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    repo: JourneyMappingRepository = Depends(get_journey_mapping_repo), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get AI-generated recommendations for journey optimization."""
    try:
        blueprint = await repo.get_blueprint_with_relations(data.blueprint_id)

        verify_ownership(blueprint, company_id, "Journey blueprint")

        steps_info = [
            {
                "name": step.name,
                "type": step.step_type,
                "order": step.order,
                "enabled": step.is_enabled,
                "automation": step.automation_enabled,
                "ai_enabled": step.ai_enabled
            }
            for step in blueprint.steps
        ]

        integrations_info = [
            {
                "name": integration.name,
                "type": integration.integration_type,
                "provider": integration.provider,
                "connected": integration.is_connected
            }
            for integration in blueprint.integrations
        ]

        prompt = f"""Analise a jornada de recrutamento abaixo e forneça recomendações para otimização:

Jornada: {blueprint.name}
Descrição: {blueprint.description or 'Não informada'}
Status: {blueprint.status}
Origem de Vagas: {blueprint.vacancy_origin or 'Não definida'}

Etapas Configuradas:
{steps_info}

Integrações:
{integrations_info}

Contexto Adicional:
{data.context}

Por favor, forneça:
1. Análise geral da jornada
2. Pontos de melhoria identificados
3. Sugestões de automação
4. Etapas recomendadas que podem estar faltando
5. Integrações que poderiam agregar valor

Responda em formato JSON com as chaves: summary, recommendations (lista), suggested_steps (lista)"""

        try:
            ai_response = await llm_service.generate(prompt)

            import json
            try:
                parsed_response = json.loads(ai_response)
            except json.JSONDecodeError:
                parsed_response = {
                    "summary": ai_response[:500],
                    "recommendations": [
                        {"title": "Automatização de Triagem", "description": "Configure triagem automática de CVs com IA para agilizar o processo", "priority": "high"},
                        {"title": "Integração ATS", "description": "Conecte seu ATS para sincronização automática de candidatos", "priority": "medium"},
                        {"title": "Comunicação Automatizada", "description": "Configure templates de email para comunicação consistente", "priority": "medium"}
                    ],
                    "suggested_steps": [
                        {"name": "Triagem por IA", "type": "cv_screening", "description": "Análise automática de CVs com score de compatibilidade"},
                        {"name": "Entrevista Técnica", "type": "interview", "description": "Avaliação técnica estruturada"},
                        {"name": "Assessment Comportamental", "type": "assessment", "description": "Avaliação de fit cultural e competências"}
                    ]
                }

            await repo.update_blueprint_ai(
                blueprint,
                ai_recommendations=parsed_response.get("recommendations", []),
                ai_summary=parsed_response.get("summary", "")
            )

            return AIRecommendationsResponse(
                recommendations=parsed_response.get("recommendations", []),
                summary=parsed_response.get("summary", ""),
                suggested_steps=parsed_response.get("suggested_steps", [])
            )

        except Exception as llm_error:
            logger.warning(f"LLM service error, returning default recommendations: {llm_error}")

            default_response = AIRecommendationsResponse(
                recommendations=[
                    {"title": "Automatização de Triagem", "description": "Configure triagem automática de CVs com IA", "priority": "high"},
                    {"title": "Integração ATS", "description": "Conecte seu sistema ATS para sincronização", "priority": "medium"},
                    {"title": "Comunicação Automatizada", "description": "Configure templates de comunicação", "priority": "medium"},
                    {"title": "Métricas de Performance", "description": "Acompanhe SLAs e tempo de contratação", "priority": "low"}
                ],
                summary="Recomendações baseadas em melhores práticas de recrutamento. Configure automações para otimizar seu processo.",
                suggested_steps=[
                    {"name": "Triagem por IA", "type": "cv_screening", "description": "Análise automática de CVs"},
                    {"name": "Entrevista Inicial", "type": "interview", "description": "Primeira conversa com candidatos"},
                    {"name": "Assessment", "type": "assessment", "description": "Avaliação de competências"}
                ]
            )
            return default_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
