"""
Template Seeder Service for creating default system templates.
Creates templates for all channels: email, whatsapp, bell, chat_lia, briefing, parecer, report.
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.email_template_repository import EmailTemplateRepository

from app.core.template_channels import (
    CHANNEL_BELL,
    CHANNEL_BRIEFING,
    CHANNEL_EMAIL,
    CHANNEL_PARECER,
    CHANNEL_REPORT,
    CHANNEL_TEAMS,
    CHANNEL_WHATSAPP,
)
from lia_models.email_template import EmailTemplate

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "template_seeds.json"

with open(_DATA_PATH, encoding="utf-8") as _f:
    DEFAULT_TEMPLATES: list[dict[str, Any]] = json.load(_f)


def determine_template_visibility(template_data: dict[str, Any]) -> str:
    """
    Determine template visibility based on channel, category, and name.
    
    Returns:
        admin - For system templates, alerts, reports, internal notifications
        recruiter - For candidate communication templates
        all - For templates usable by both
    """
    channel = template_data.get("channel", "")
    category = template_data.get("category", "")
    name = template_data.get("name", "")
    
    if channel in [CHANNEL_BELL, CHANNEL_TEAMS, CHANNEL_BRIEFING, CHANNEL_PARECER, CHANNEL_REPORT]:
        return "admin"
    
    if category in ["alerts", "reports", "workflow", "integrations", "billing", "onboarding", "briefings", "parecer", "workforce"]:
        return "admin"
    
    admin_template_names = [
        "Meta em Risco", "Meta Não Atingida", "SLA Violado", "Aprovação Pendente",
        "Aprovação Expirada", "Alerta No-Show", "Variância Workforce", "Alerta Crítico",
        "Performance Semanal", "Relatório Mensal", "Resumo Semanal", "Relatório de Equipe",
        "Relatório Executivo da Vaga", "Sync ATS Falhou", "Créditos Baixos",
        "Boas-vindas Usuário", "Briefing Diário", "Resumo de Fim de Dia",
        "Parecer Resumido", "Parecer Completo", "Vaga Pausada", "Vaga Reativada",
        "Triagem Concluída", "Alerta Crítico via Teams", "Triagem Concluída via Teams"
    ]
    
    if name in admin_template_names:
        return "admin"
    
    recruiter_template_names = [
        "Primeiro Contato", "Contato Inicial", "Follow-up", "Convite Triagem",
        "Convite Entrevista", "Feedback Positivo", "Feedback Construtivo",
        "Proposta de Trabalho", "Proposta Aceita", "Proposta Recusada",
        "Vaga Encerrada", "Lembrete de Triagem", "Lembrete de Entrevista",
        "Entrevista Agendada", "Aprovação na Triagem", "Rejeição na Triagem",
        "Rejeição Pós-Entrevista", "Processo Encerrado",
        "Contato Inicial (WhatsApp)", "Convite Triagem (WhatsApp)",
        "Convite Entrevista (WhatsApp)", "Feedback Construtivo (WhatsApp)",
        "Vaga Encerrada (WhatsApp)", "Lembrete de Triagem (WhatsApp)",
        "Lembrete de Entrevista (WhatsApp)", "Screening Invite",
        "Screening Reminder", "Interview Reminder",
        "Compartilhamento com Gestor", "Compartilhamento com Gestor (WhatsApp)"
    ]
    
    if name in recruiter_template_names:
        return "recruiter"
    
    if category == "candidates" and channel in [CHANNEL_EMAIL, CHANNEL_WHATSAPP]:
        return "recruiter"
    
    if category in ["offers", "sharing"]:
        return "recruiter"
    
    return "recruiter"


async def seed_default_templates(db: AsyncSession) -> dict[str, Any]:
    """
    Seed default system templates.
    Creates templates with company_id=NULL and is_system_template=True.
    
    Returns:
        Dict with created count and list of template names
    """
    created_templates = []
    skipped_templates = []
    
    for template_data in DEFAULT_TEMPLATES:
        existing_template = await EmailTemplateRepository(db).find_system_template(
            situation=template_data["situation"], channel=template_data["channel"]
        )
        
        if existing_template:
            skipped_templates.append(template_data["name"])
            continue
        
        visibility = determine_template_visibility(template_data)
        
        template = EmailTemplate(
            id=uuid.uuid4(),
            name=template_data["name"],
            subject=template_data.get("subject"),
            body_html=template_data["body_html"].strip(),
            body_text=None,
            category=template_data.get("category"),
            channel=template_data["channel"],
            situation=template_data["situation"],
            variables=template_data.get("variables", []),
            trigger_type=template_data.get("trigger_type", "manual"),
            used_in=template_data.get("used_in", []),
            priority=template_data.get("priority", "medium"),
            is_active=True,
            company_id=None,
            is_system_template=True,
            visibility=visibility,
            version=1,
            created_by="system",
        )
        
        db.add(template)
        created_templates.append(template_data["name"])
    
    await db.commit()
    
    logger.info(f"Template seeder: Created {len(created_templates)} templates, skipped {len(skipped_templates)}")
    
    return {
        "created": len(created_templates),
        "skipped": len(skipped_templates),
        "created_templates": created_templates,
        "skipped_templates": skipped_templates,
    }


async def clone_templates_for_client(db: AsyncSession, client_id: str, auto_commit: bool = True) -> dict[str, Any]:
    """
    Clone all system templates for a new client.
    
    Works with the provided session and can optionally skip commit to allow
    the caller to control the transaction.
    
    Args:
        db: Database session (existing session, works within callers transaction)
        client_id: The company_id for the new client
        auto_commit: If True (default), commits after cloning. Set to False to let caller control transaction.
        
    Returns:
        Dict with count of cloned templates
        
    Raises:
        Any database errors are propagated to the caller (not swallowed)
    """
    repo = EmailTemplateRepository(db)
    system_templates = await repo.list_active_system_templates()
    
    cloned_templates = []
    
    for template in system_templates:
        existing = await repo.find_for_client(
            company_id=client_id,
            situation=template.situation,
            channel=template.channel,
        )
        if existing:
            continue
        
        cloned = EmailTemplate(
            id=uuid.uuid4(),
            name=template.name,
            subject=template.subject,
            body_html=template.body_html,
            body_text=template.body_text,
            category=template.category,
            channel=template.channel,
            situation=template.situation,
            variables=template.variables,
            is_active=True,
            company_id=client_id,
            is_system_template=False,
            visibility=template.visibility,
            origin_template_id=template.id,
            version=1,
            created_by="system_clone",
        )
        
        db.add(cloned)
        cloned_templates.append(template.name)
    
    if auto_commit:
        await db.commit()
    
    logger.info(f"Cloned {len(cloned_templates)} templates for client {client_id}")
    
    return {
        "client_id": client_id,
        "cloned_count": len(cloned_templates),
        "cloned_templates": cloned_templates,
    }
