"""
Automations API Endpoints - Full CRUD for communication automations.

Provides endpoints for:
- Listing all automations
- Creating new automations
- Updating automations
- Deleting automations
- Testing automations
- Triggering automations manually
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.automation.services.automation_service import AutomationService, automation_service, get_automation_service
from app.models.automation import ActionType, TriggerType
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automations", tags=["automations"])


class AutomationCondition(BaseModel):
    """Condition for automation execution."""
    field: str = Field(..., description="Field to evaluate")
    operator: str = Field(default="equals", description="Comparison operator: equals, not_equals, contains, in, greater_than, etc.")
    value: Any = Field(..., description="Value to compare against")


class CreateAutomationRequest(WeDoBaseModel):
    """Request model for creating an automation."""
    name: str = Field(..., min_length=1, max_length=255, description="Automation name")
    description: str | None = Field(None, max_length=1000, description="Automation description")
    trigger_type: str = Field(..., description="Trigger type: candidate_stage_changed, interview_scheduled, offer_sent, screening_completed, no_response_48h")
    trigger_config: dict[str, Any] | None = Field(default={}, description="Trigger configuration")
    action_type: str = Field(..., description="Action type: send_email, send_whatsapp, create_task, notify_recruiter")
    action_config: dict[str, Any] | None = Field(default={}, description="Action configuration (template_id, message, etc)")
    conditions: list[dict[str, Any]] | None = Field(default=[], description="Conditions for automation execution")
    is_active: bool = Field(default=True, description="Whether automation is active")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    cooldown_minutes: int = Field(default=0, ge=0, description="Cooldown in minutes between executions")


class UpdateAutomationRequest(WeDoBaseModel):
    """Request model for updating an automation."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    action_type: str | None = None
    action_config: dict[str, Any] | None = None
    conditions: list[dict[str, Any]] | None = None
    is_active: bool | None = None
    priority: str | None = None
    cooldown_minutes: int | None = Field(None, ge=0)


class TestAutomationRequest(WeDoBaseModel):
    """Request model for testing an automation."""
    test_data: dict[str, Any] | None = Field(default=None, description="Test trigger data")


class TriggerAutomationRequest(WeDoBaseModel):
    """Request model for manually triggering automations."""
    trigger_type: str = Field(..., description="Trigger type")
    trigger_data: dict[str, Any] = Field(..., description="Trigger event data")


@router.get("", summary="List automations", response_model=None)
async def list_automations(
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    is_active: bool | None = Query(None, description="Filter by active status"),
    trigger_type: str | None = Query(None, description="Filter by trigger type"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all automations for a company.
    
    Returns paginated list of automation configurations.
    """
    try:
        result = await auto_svc.list_automations(
            company_id=company_id,
            is_active=is_active,
            trigger_type=trigger_type,
            limit=limit,
            offset=offset,
            db=db
        )
        
        logger.info(f"📋 Listed {len(result['automations'])} automations (total: {result['total']})")
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing automations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list automations: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create automation", response_model=None)
async def create_automation(
    data: CreateAutomationRequest,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    user_id: str | None = Query(None, description="User creating the automation"),
    db: AsyncSession = Depends(get_tenant_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a new automation.
    
    Automations can be configured with:
    - Trigger types: candidate_stage_changed, interview_scheduled, offer_sent, screening_completed, no_response_48h
    - Action types: send_email, send_whatsapp, create_task, notify_recruiter
    - Conditions: Rules to filter when automation should execute
    """
    try:
        valid_trigger_types = [t.value for t in TriggerType]
        if data.trigger_type not in valid_trigger_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trigger_type. Must be one of: {', '.join(valid_trigger_types)}"
            )
        
        valid_action_types = [a.value for a in ActionType]
        if data.action_type not in valid_action_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action_type. Must be one of: {', '.join(valid_action_types)}"
            )
        
        automation = await auto_svc.create_automation(
            company_id=company_id,
            name=data.name,
            description=data.description,
            trigger_type=data.trigger_type,
            trigger_config=data.trigger_config,
            action_type=data.action_type,
            action_config=data.action_config,
            conditions=data.conditions,
            is_active=data.is_active,
            priority=data.priority,
            cooldown_minutes=data.cooldown_minutes,
            created_by=user_id,
            db=db
        )
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created automation: {automation.name} (ID: {automation.id})")
        
        return {
            "success": True,
            "message": "Automação criada com sucesso",
            "data": automation.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create automation: {str(e)}"
        )


@router.get("/{automation_id}", summary="Get automation", response_model=None)
async def get_automation(
    automation_id: str,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    db: AsyncSession = Depends(get_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a single automation by ID.
    
    Returns full automation details or 404 if not found.
    """
    try:
        automation = await auto_svc.get_automation(
            automation_id=automation_id,
            company_id=company_id,
            db=db
        )
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        return {
            "success": True,
            "data": automation.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get automation: {str(e)}"
        )


@router.put("/{automation_id}", summary="Update automation", response_model=None)
async def update_automation(
    automation_id: str,
    data: UpdateAutomationRequest,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    user_id: str | None = Query(None, description="User updating the automation"),
    db: AsyncSession = Depends(get_tenant_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update an existing automation.
    
    Only provided fields will be updated.
    """
    try:
        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        
        if "trigger_type" in updates:
            valid_trigger_types = [t.value for t in TriggerType]
            if updates["trigger_type"] not in valid_trigger_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid trigger_type. Must be one of: {', '.join(valid_trigger_types)}"
                )
        
        if "action_type" in updates:
            valid_action_types = [a.value for a in ActionType]
            if updates["action_type"] not in valid_action_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action_type. Must be one of: {', '.join(valid_action_types)}"
                )
        
        automation = await auto_svc.update_automation(
            automation_id=automation_id,
            company_id=company_id,
            updates=updates,
            updated_by=user_id,
            db=db
        )
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Updated automation: {automation.name}")
        
        return {
            "success": True,
            "message": "Automação atualizada com sucesso",
            "data": automation.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update automation: {str(e)}"
        )


@router.delete("/{automation_id}", summary="Delete automation", response_model=None)
async def delete_automation(
    automation_id: str,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    db: AsyncSession = Depends(get_tenant_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Delete an automation.
    
    This permanently removes the automation configuration.
    """
    try:
        success = await auto_svc.delete_automation(
            automation_id=automation_id,
            company_id=company_id,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        logger.info(f"🗑️ Deleted automation: {automation_id}")
        
        return {
            "success": True,
            "message": "Automação excluída com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete automation: {str(e)}"
        )


@router.post("/{automation_id}/test", summary="Test automation", response_model=None)
async def test_automation(
    automation_id: str,
    data: TestAutomationRequest = None,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    db: AsyncSession = Depends(get_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Test an automation without executing the actual action.
    
    Simulates the automation execution and returns:
    - Whether conditions would be met
    - Whether cooldown is active
    - What action would be executed
    """
    try:
        test_data = data.test_data if data else None
        
        result = await auto_svc.test_automation(
            automation_id=automation_id,
            company_id=company_id,
            test_data=test_data,
            db=db
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Automation not found")
            )
        
        logger.info(f"🧪 Tested automation: {automation_id}")
        
        return {
            "success": True,
            "message": "Teste de automação executado",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test automation: {str(e)}"
        )


@router.post("/trigger", summary="Manually trigger automations", response_model=None)
async def trigger_automations(
    data: TriggerAutomationRequest,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    db: AsyncSession = Depends(get_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Manually trigger automations for a specific event.
    
    This will find all active automations matching the trigger type
    and execute their actions if conditions are met.
    """
    try:
        result = await auto_svc.trigger_automation(
            trigger_type=data.trigger_type,
            trigger_data=data.trigger_data,
            company_id=company_id,
            db=db
        )
        
        logger.info(f"⚡ Triggered automations: {result['automations_executed']} executed")
        
        return {
            "success": True,
            "message": f"{result['automations_executed']} automações executadas",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error triggering automations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger automations: {str(e)}"
        )


@router.get("/{automation_id}/logs", summary="Get automation execution logs", response_model=None)
async def get_automation_logs(
    automation_id: str,
    company_id: str = Depends(require_company_id),  # JWT canonical (REGRA 2)
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    auto_svc: AutomationService = Depends(get_automation_service)
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get execution logs for a specific automation.
    
    Returns history of when the automation was triggered and results.
    """
    try:
        result = await auto_svc.get_execution_logs(
            company_id=company_id,
            automation_id=automation_id,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting automation logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get automation logs: {str(e)}"
        )


@router.get("/trigger-types/available", summary="Get available trigger types", response_model=None)
async def get_trigger_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get list of available trigger types for automations.
    """
    return {
        "success": True,
        "data": {
            "trigger_types": [
                {
                    "value": TriggerType.CANDIDATE_STAGE_CHANGED.value,
                    "name": "Candidato mudou de etapa",
                    "description": "Dispara quando um candidato muda de etapa no processo seletivo"
                },
                {
                    "value": TriggerType.INTERVIEW_SCHEDULED.value,
                    "name": "Entrevista agendada",
                    "description": "Dispara quando uma entrevista é agendada"
                },
                {
                    "value": TriggerType.OFFER_SENT.value,
                    "name": "Proposta enviada",
                    "description": "Dispara quando uma proposta é enviada ao candidato"
                },
                {
                    "value": TriggerType.SCREENING_COMPLETED.value,
                    "name": "Triagem concluída",
                    "description": "Dispara quando a triagem do candidato é concluída"
                },
                {
                    "value": TriggerType.NO_RESPONSE_48H.value,
                    "name": "Sem resposta há 48h",
                    "description": "Dispara quando não há resposta do candidato por 48 horas"
                },
                {
                    "value": TriggerType.CANDIDATE_APPLIED.value,
                    "name": "Candidato se candidatou",
                    "description": "Dispara quando um candidato se candidata a uma vaga"
                },
                {
                    "value": TriggerType.CANDIDATE_REJECTED.value,
                    "name": "Candidato rejeitado",
                    "description": "Dispara quando um candidato é rejeitado"
                },
                {
                    "value": TriggerType.CANDIDATE_HIRED.value,
                    "name": "Candidato contratado",
                    "description": "Dispara quando um candidato é contratado"
                },
                {
                    "value": TriggerType.FEEDBACK_RECEIVED.value,
                    "name": "Feedback recebido",
                    "description": "Dispara quando um feedback é recebido"
                },
                {
                    "value": TriggerType.DEADLINE_APPROACHING.value,
                    "name": "Prazo se aproximando",
                    "description": "Dispara quando o prazo de uma vaga está se aproximando"
                }
            ]
        }
    }


@router.get("/action-types/available", summary="Get available action types", response_model=None)
async def get_action_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get list of available action types for automations.
    """
    return {
        "success": True,
        "data": {
            "action_types": [
                {
                    "value": ActionType.SEND_EMAIL.value,
                    "name": "Enviar e-mail",
                    "description": "Envia um e-mail usando um template configurado",
                    "config_fields": ["template_id", "subject", "to_email"]
                },
                {
                    "value": ActionType.SEND_WHATSAPP.value,
                    "name": "Enviar WhatsApp",
                    "description": "Envia uma mensagem via WhatsApp",
                    "config_fields": ["template_name", "to_phone"]
                },
                {
                    "value": ActionType.CREATE_TASK.value,
                    "name": "Criar tarefa",
                    "description": "Cria uma tarefa para o recrutador",
                    "config_fields": ["title", "description", "task_type", "priority"]
                },
                {
                    "value": ActionType.NOTIFY_RECRUITER.value,
                    "name": "Notificar recrutador",
                    "description": "Envia notificação para o recrutador responsável",
                    "config_fields": ["title", "message", "recruiter_id"]
                },
                {
                    "value": ActionType.NOTIFY_MANAGER.value,
                    "name": "Notificar gestor",
                    "description": "Envia notificação para o gestor da vaga",
                    "config_fields": ["title", "message", "manager_id"]
                },
                {
                    "value": ActionType.LOG_ACTIVITY.value,
                    "name": "Registrar atividade",
                    "description": "Registra uma atividade no histórico",
                    "config_fields": ["activity_type", "description"]
                }
            ]
        }
    }
