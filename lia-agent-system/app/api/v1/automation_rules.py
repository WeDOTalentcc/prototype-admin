"""
Automation Rules API
CRUD endpoints for company-specific stage automation rules.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.automation.repositories.automation_rule_repository import (
    AutomationRuleRepository,
)

router = APIRouter(prefix="/automation-rules", tags=["automation-rules"])


class AutomationRuleCreate(BaseModel):
    trigger_type: str
    is_active: bool = True
    auto_execute: bool = False
    confidence_threshold: float = 0.8
    conditions: dict = {}
    actions: list = []
    source_stage: str | None = None
    target_stage: str | None = None
    name: str | None = None
    description: str | None = None
    priority: str = "normal"


class AutomationRuleUpdate(BaseModel):
    is_active: bool | None = None
    auto_execute: bool | None = None
    confidence_threshold: float | None = None
    conditions: dict | None = None
    actions: list | None = None
    source_stage: str | None = None
    target_stage: str | None = None
    name: str | None = None
    description: str | None = None
    priority: str | None = None


class AutomationRuleResponse(BaseModel):
    id: str
    company_id: str
    trigger_type: str
    is_active: bool
    auto_execute: bool
    confidence_threshold: float
    conditions: dict
    actions: list
    source_stage: str | None
    target_stage: str | None
    name: str | None
    description: str | None
    priority: str
    created_by: str | None
    created_at: str | None
    updated_at: str | None


@router.get("/company/{company_id}", response_model=None)
async def get_company_rules(
    company_id: str,
    is_active: bool | None = None,
    trigger_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Get all automation rules for a company with optional filters."""
    repo = AutomationRuleRepository(db)
    rules = await repo.list_for_company(company_id, is_active=is_active, trigger_type=trigger_type)
    return {"rules": [rule.to_dict() for rule in rules], "total": len(rules)}


@router.get("/company/{company_id}/{rule_id}", response_model=None)
async def get_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_db)):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Get a specific automation rule."""
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"rule": rule.to_dict()}


@router.post("/company/{company_id}", response_model=None)
async def create_rule(
    company_id: str,
    rule: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Create a new automation rule for a company."""
    repo = AutomationRuleRepository(db)
    data = rule.model_dump()
    data["confidence_threshold"] = str(data["confidence_threshold"])
    new_rule = await repo.create(company_id, data)
    return {"success": True, "rule_id": str(new_rule.id), "rule": new_rule.to_dict()}


@router.put("/company/{company_id}/{rule_id}", response_model=None)
async def update_rule(
    company_id: str,
    rule_id: str,
    updates: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Update an automation rule."""
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = updates.model_dump(exclude_unset=True)
    if "confidence_threshold" in update_data:
        update_data["confidence_threshold"] = str(update_data["confidence_threshold"])
    rule = await repo.update(rule, update_data)
    return {"success": True, "rule": rule.to_dict()}


@router.delete("/company/{company_id}/{rule_id}", response_model=None)
async def delete_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_db)):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Delete an automation rule."""
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await repo.delete(rule)
    return {"success": True, "deleted_id": rule_id}


@router.post("/company/{company_id}/toggle/{rule_id}", response_model=None)
async def toggle_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_db)):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Toggle the active status of an automation rule."""
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule = await repo.toggle(rule)
    return {"success": True, "is_active": rule.is_active, "rule": rule.to_dict()}


@router.post("/company/{company_id}/seed-defaults", response_model=None)
async def seed_default_rules(
    company_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Seed default automation rules for a new company."""
    repo = AutomationRuleRepository(db)
    existing = await repo.list_for_company(company_id)
    if existing and not force:
        return {
            "success": False,
            "message": "Company already has automation rules. Use force=true to add defaults anyway.",
            "existing_count": len(existing),
        }
    created = await repo.seed_defaults(company_id)
    return {"success": True, "rules_created": len(created), "trigger_types": created}


@router.get("/trigger-types", response_model=None)
async def get_available_trigger_types():
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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


@router.get("/action-types", response_model=None)
async def get_available_action_types():
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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
