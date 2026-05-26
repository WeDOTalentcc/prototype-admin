"""
Automation Rules API
CRUD endpoints for company-specific stage automation rules.

WT-2022 P3.2 (2026-05-21): endpoint DEPRECATED-mas-funcional. UI continua
escrevendo em `stage_automation_rules` (preserva compat) mas adapter
`StageRuleAdapter` faz DUAL-WRITE em `communication_automations` (canonical
engine read source — `stage_automation_engine.py:198`).

Pattern P3.2:
- CREATE/UPDATE/TOGGLE → grava em stage_automation_rules + espelha em
  communication_automations
- DELETE → remove de stage_automation_rules + soft-delete (is_active=False)
  em communication_automations
- READ (list/get) → continua só stage_automation_rules (UI legacy contract)

Para novas features, prefira `/api/v1/communication-automations` (canonical).
"""
# ESCOPO: Company-level Stage Automation Rules — ADR-031 (Sistema 1 de 2)
# Ver: docs/adr/ADR-031-automation-rules-disambiguation.md
# Este arquivo = regras de stage por empresa (tabela stage_automation_rules).
# NAO confundir com:
#   - company_hiring_policies.automation_rules (JSONB) — comportamento da LIA (Sistema 2)
#   - /api/v1/communication-automations — canonical futuro (para onde migrar)
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.automation.repositories.automation_rule_repository import (
    AutomationRuleRepository,
)
from app.domains.automation.services.stage_rule_adapter import StageRuleAdapter
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

# WT-2022 P3.2 DEPRECATED: endpoint manipula stage_automation_rules; engine
# real (stage_automation_engine.py:198) lê communication_automations. Adapter
# `StageRuleAdapter` faz dual-write para garantir consistência durante
# migration. Para novas features, usar /api/v1/communication-automations.

router = APIRouter(prefix="/automation-rules", tags=["automation-rules"])


class AutomationRuleCreate(WeDoBaseModel):
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


class AutomationRuleUpdate(WeDoBaseModel):
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
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all automation rules for a company with optional filters."""
    repo = AutomationRuleRepository(db)
    rules = await repo.list_for_company(company_id, is_active=is_active, trigger_type=trigger_type)
    return {"rules": [rule.to_dict() for rule in rules], "total": len(rules)}


@router.get("/company/{company_id}/{rule_id}", response_model=None)
async def get_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_db), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new automation rule for a company.

    WT-2022 P3.2: dual-write — grava em stage_automation_rules (UI legacy)
    e espelha em communication_automations (canonical engine read source).
    """
    repo = AutomationRuleRepository(db)
    data = rule.model_dump()
    # confidence_threshold kept as float (Column is Float as of mig 212)
    new_rule = await repo.create(company_id, data)
    # P3.2: mirror em communication_automations (non-fatal se falhar)
    await StageRuleAdapter.upsert_communication_automation_from_stage_rule(
        db, new_rule
    )
    return {"success": True, "rule_id": str(new_rule.id), "rule": new_rule.to_dict()}


@router.put("/company/{company_id}/{rule_id}", response_model=None)
async def update_rule(
    company_id: str,
    rule_id: str,
    updates: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an automation rule.

    WT-2022 P3.2: dual-write — update em stage_automation_rules + espelho em
    communication_automations.
    """
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = updates.model_dump(exclude_unset=True)
    # confidence_threshold kept as float (Column is Float as of mig 212)
    rule = await repo.update(rule, update_data)
    # P3.2: mirror update em communication_automations
    await StageRuleAdapter.upsert_communication_automation_from_stage_rule(
        db, rule
    )
    return {"success": True, "rule": rule.to_dict()}


@router.delete("/company/{company_id}/{rule_id}", response_model=None)
async def delete_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_tenant_db), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete an automation rule.

    WT-2022 P3.2: soft-delete em communication_automations mirror ANTES de
    delete físico em stage_automation_rules (preserva auditabilidade do
    canonical store).
    """
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    # P3.2: soft-delete mirror antes do delete físico
    await StageRuleAdapter.soft_delete_mirror(db, rule)
    await repo.delete(rule)
    return {"success": True, "deleted_id": rule_id}


@router.post("/company/{company_id}/toggle/{rule_id}", response_model=None)
async def toggle_rule(company_id: str, rule_id: str, db: AsyncSession = Depends(get_tenant_db), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Toggle the active status of an automation rule.

    WT-2022 P3.2: dual-write — toggle propagado para mirror em
    communication_automations.
    """
    repo = AutomationRuleRepository(db)
    rule = await repo.get_by_id(rule_id, company_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule = await repo.toggle(rule)
    # P3.2: propaga is_active para mirror
    await StageRuleAdapter.upsert_communication_automation_from_stage_rule(
        db, rule
    )
    return {"success": True, "is_active": rule.is_active, "rule": rule.to_dict()}


@router.post("/company/{company_id}/seed-defaults", response_model=None)
async def seed_default_rules(
    company_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed default automation rules for a new company.

    WT-2022 P3.2: dual-write — defaults também espelhados em
    communication_automations para que o engine canonical execute imediatamente
    a partir do onboarding (sem esperar reconciliação).
    """
    repo = AutomationRuleRepository(db)
    existing = await repo.list_for_company(company_id)
    if existing and not force:
        return {
            "success": False,
            "message": "Company already has automation rules. Use force=true to add defaults anyway.",
            "existing_count": len(existing),
        }
    created = await repo.seed_defaults(company_id)
    # P3.2: espelha defaults recém-criados em communication_automations.
    # `created` retorna list[str] (trigger_types) — re-fetch para mirror.
    try:
        seeded_rules = await repo.list_for_company(company_id)
        for rule in seeded_rules:
            await StageRuleAdapter.upsert_communication_automation_from_stage_rule(
                db, rule
            )
    except Exception as e:
        logger.warning(
            "[P3.2] seed_defaults mirror failed for company=%s: %s. UI write "
            "succeeded but engine may not see defaults until reconciliation.",
            company_id, e,
        )
        # P1-W4-10: fail-visible — retorna flag para caller diagnosticar
        return {
            "success": True,
            "rules_created": len(created),
            "trigger_types": created,
            "mirror_failed": True,
            "mirror_error": str(e)[:200],
        }
    return {"success": True, "rules_created": len(created), "trigger_types": created}


@router.get("/trigger-types", response_model=None)
async def get_available_trigger_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
async def get_available_action_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
