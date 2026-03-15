"""
Automation Rules API
CRUD endpoints for company-specific stage automation rules.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_db
from app.models.automation import StageAutomationRule, DEFAULT_STAGE_AUTOMATION_RULES

router = APIRouter(prefix="/automation-rules", tags=["automation-rules"])


class AutomationRuleCreate(BaseModel):
    trigger_type: str
    is_active: bool = True
    auto_execute: bool = False
    confidence_threshold: float = 0.8
    conditions: dict = {}
    actions: list = []
    source_stage: Optional[str] = None
    target_stage: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    priority: str = "normal"


class AutomationRuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    auto_execute: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    conditions: Optional[dict] = None
    actions: Optional[list] = None
    source_stage: Optional[str] = None
    target_stage: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


class AutomationRuleResponse(BaseModel):
    id: str
    company_id: str
    trigger_type: str
    is_active: bool
    auto_execute: bool
    confidence_threshold: float
    conditions: dict
    actions: list
    source_stage: Optional[str]
    target_stage: Optional[str]
    name: Optional[str]
    description: Optional[str]
    priority: str
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


@router.get("/company/{company_id}")
async def get_company_rules(
    company_id: str,
    is_active: Optional[bool] = None,
    trigger_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all automation rules for a company with optional filters."""
    query = select(StageAutomationRule).where(
        StageAutomationRule.company_id == company_id
    )
    
    if is_active is not None:
        query = query.where(StageAutomationRule.is_active == is_active)
    if trigger_type:
        query = query.where(StageAutomationRule.trigger_type == trigger_type)
    
    query = query.order_by(StageAutomationRule.created_at.desc())
    
    result = await db.execute(query)
    rules = result.scalars().all()
    return {"rules": [rule.to_dict() for rule in rules], "total": len(rules)}


@router.get("/company/{company_id}/{rule_id}")
async def get_rule(
    company_id: str,
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific automation rule."""
    result = await db.execute(
        select(StageAutomationRule).where(
            StageAutomationRule.id == rule_id,
            StageAutomationRule.company_id == company_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"rule": rule.to_dict()}


@router.post("/company/{company_id}")
async def create_rule(
    company_id: str, 
    rule: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new automation rule for a company."""
    new_rule = StageAutomationRule(
        company_id=company_id,
        trigger_type=rule.trigger_type,
        is_active=rule.is_active,
        auto_execute=rule.auto_execute,
        confidence_threshold=str(rule.confidence_threshold),
        conditions=rule.conditions,
        actions=rule.actions,
        source_stage=rule.source_stage,
        target_stage=rule.target_stage,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return {"success": True, "rule_id": str(new_rule.id), "rule": new_rule.to_dict()}


@router.put("/company/{company_id}/{rule_id}")
async def update_rule(
    company_id: str,
    rule_id: str,
    updates: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an automation rule."""
    result = await db.execute(
        select(StageAutomationRule).where(
            StageAutomationRule.id == rule_id,
            StageAutomationRule.company_id == company_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    if "confidence_threshold" in update_data:
        update_data["confidence_threshold"] = str(update_data["confidence_threshold"])
    
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    await db.commit()
    await db.refresh(rule)
    return {"success": True, "rule": rule.to_dict()}


@router.delete("/company/{company_id}/{rule_id}")
async def delete_rule(
    company_id: str,
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an automation rule."""
    result = await db.execute(
        select(StageAutomationRule).where(
            StageAutomationRule.id == rule_id,
            StageAutomationRule.company_id == company_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    return {"success": True, "deleted_id": rule_id}


@router.post("/company/{company_id}/toggle/{rule_id}")
async def toggle_rule(
    company_id: str,
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Toggle the active status of an automation rule."""
    result = await db.execute(
        select(StageAutomationRule).where(
            StageAutomationRule.id == rule_id,
            StageAutomationRule.company_id == company_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = not rule.is_active
    await db.commit()
    await db.refresh(rule)
    return {"success": True, "is_active": rule.is_active, "rule": rule.to_dict()}


@router.post("/company/{company_id}/seed-defaults")
async def seed_default_rules(
    company_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Seed default automation rules for a new company."""
    existing_result = await db.execute(
        select(StageAutomationRule).where(
            StageAutomationRule.company_id == company_id
        )
    )
    existing_rules = existing_result.scalars().all()
    
    if existing_rules and not force:
        return {
            "success": False,
            "message": "Company already has automation rules. Use force=true to add defaults anyway.",
            "existing_count": len(existing_rules)
        }
    
    created_rules = []
    for rule_data in DEFAULT_STAGE_AUTOMATION_RULES:
        rule = StageAutomationRule(
            company_id=company_id,
            trigger_type=rule_data["trigger_type"],
            name=rule_data.get("name"),
            auto_execute=rule_data.get("auto_execute", False),
            is_active=True,
            conditions=rule_data.get("conditions", {}),
            actions=rule_data.get("actions", []),
            priority=rule_data.get("priority", "normal"),
            confidence_threshold="0.8",
        )
        db.add(rule)
        created_rules.append(rule_data["trigger_type"])
    
    await db.commit()
    return {
        "success": True,
        "rules_created": len(created_rules),
        "trigger_types": created_rules
    }


@router.get("/trigger-types")
async def get_available_trigger_types():
    """Get list of available trigger types."""
    return {
        "trigger_types": [
            {"id": "screening_completed", "name": "Triagem Concluída", "description": "Quando um candidato completa a triagem"},
            {"id": "interview_completed", "name": "Entrevista Concluída", "description": "Quando uma entrevista é finalizada"},
            {"id": "interview_scheduled", "name": "Entrevista Agendada", "description": "Quando uma entrevista é agendada"},
            {"id": "candidate_applied", "name": "Nova Candidatura", "description": "Quando um novo candidato se inscreve"},
            {"id": "candidate_inactive", "name": "Candidato Inativo", "description": "Quando um candidato fica inativo por X dias"},
            {"id": "offer_sent", "name": "Oferta Enviada", "description": "Quando uma oferta é enviada ao candidato"},
            {"id": "offer_accepted", "name": "Oferta Aceita", "description": "Quando o candidato aceita a oferta"},
            {"id": "offer_rejected", "name": "Oferta Recusada", "description": "Quando o candidato recusa a oferta"},
            {"id": "candidate_rejected", "name": "Candidato Rejeitado", "description": "Quando um candidato é rejeitado do processo"},
            {"id": "candidate_hired", "name": "Candidato Contratado", "description": "Quando um candidato é contratado"},
            {"id": "wsi_score_calculated", "name": "Score WSI Calculado", "description": "Quando o score WSI é calculado"},
            {"id": "feedback_received", "name": "Feedback Recebido", "description": "Quando um feedback é adicionado"},
            {"id": "deadline_approaching", "name": "Prazo se Aproximando", "description": "Quando um prazo está próximo"},
            {"id": "stage_changed", "name": "Etapa Alterada", "description": "Quando o candidato muda de etapa"},
        ]
    }


@router.get("/action-types")
async def get_available_action_types():
    """Get list of available action types."""
    return {
        "action_types": [
            {"id": "send_email", "name": "Enviar E-mail", "description": "Enviar e-mail usando template"},
            {"id": "send_whatsapp", "name": "Enviar WhatsApp", "description": "Enviar mensagem WhatsApp"},
            {"id": "notify_recruiter", "name": "Notificar Recrutador", "description": "Enviar notificação ao recrutador"},
            {"id": "notify_team", "name": "Notificar Equipe", "description": "Notificar toda a equipe"},
            {"id": "create_task", "name": "Criar Tarefa", "description": "Criar tarefa no sistema"},
            {"id": "calculate_wsi", "name": "Calcular WSI", "description": "Calcular score WSI do candidato"},
            {"id": "generate_parecer", "name": "Gerar Parecer", "description": "Gerar parecer automático"},
            {"id": "suggest_next_stage", "name": "Sugerir Próxima Etapa", "description": "Sugerir próxima etapa do processo"},
            {"id": "move_to_stage", "name": "Mover para Etapa", "description": "Mover candidato para etapa específica"},
            {"id": "sync_ats", "name": "Sincronizar ATS", "description": "Sincronizar com sistema ATS"},
            {"id": "send_followup", "name": "Enviar Follow-up", "description": "Enviar mensagem de follow-up"},
            {"id": "initial_screening", "name": "Triagem Inicial", "description": "Iniciar triagem automatizada"},
            {"id": "log_activity", "name": "Registrar Atividade", "description": "Registrar atividade no histórico"},
        ]
    }
