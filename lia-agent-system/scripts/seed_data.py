"""
Seed Data Script - Populates the database with default Task Templates and Alert Rules.

This script is idempotent - it checks if data already exists before inserting.
Can be run via CLI: python scripts/seed_data.py
Or through the API endpoint: POST /api/v1/admin/seed-data
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.task import TaskTemplate, TaskType, TaskPriority
from app.models.alert import AlertRule, AlertType, AlertSeverity
from app.core.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_TASK_TEMPLATES = [
    {
        "name": "Feedback Pendente",
        "description": "Template para tarefas de feedback pendente de recrutadores ou gestores",
        "task_type": TaskType.FEEDBACK_PENDING,
        "default_priority": TaskPriority.HIGH,
        "title_template": "Feedback Pendente: {candidate_name} - {job_title}",
        "description_template": "O candidato {candidate_name} está aguardando feedback para a vaga {job_title}. Por favor, forneça sua avaliação.",
        "default_due_days": 3,
        "assigned_agent": "recruiter_assistant",
    },
    {
        "name": "Agendar Entrevista",
        "description": "Template para agendamento de entrevistas com candidatos",
        "task_type": TaskType.INTERVIEW_SCHEDULE,
        "default_priority": TaskPriority.HIGH,
        "title_template": "Agendar Entrevista: {candidate_name} - {job_title}",
        "description_template": "Agendar entrevista com {candidate_name} para a vaga {job_title}. Coordenar disponibilidade com o gestor.",
        "default_due_days": 2,
        "assigned_agent": "scheduling",
    },
    {
        "name": "Revisar CV",
        "description": "Template para revisão de currículos de candidatos",
        "task_type": TaskType.CV_REVIEW,
        "default_priority": TaskPriority.MEDIUM,
        "title_template": "Revisar CV: {candidate_name}",
        "description_template": "Revisar currículo de {candidate_name} e avaliar adequação para vagas abertas.",
        "default_due_days": 1,
        "assigned_agent": "screening",
    },
    {
        "name": "Enviar Parecer",
        "description": "Template para envio de pareceres técnicos ou de RH",
        "task_type": TaskType.SEND_REPORT,
        "default_priority": TaskPriority.MEDIUM,
        "title_template": "Enviar Parecer: {candidate_name} - {job_title}",
        "description_template": "Preparar e enviar parecer sobre {candidate_name} para a vaga {job_title}.",
        "default_due_days": 2,
        "assigned_agent": "analytics",
    },
    {
        "name": "Buscar Candidatos",
        "description": "Template para sourcing de candidatos para vagas específicas",
        "task_type": TaskType.SOURCING,
        "default_priority": TaskPriority.MEDIUM,
        "title_template": "Buscar Candidatos: {job_title}",
        "description_template": "Realizar sourcing ativo de candidatos para a vaga {job_title}. Meta: {target_count} candidatos qualificados.",
        "default_due_days": 5,
        "assigned_agent": "sourcing",
    },
    {
        "name": "Follow-up com Candidato",
        "description": "Template para acompanhamento de candidatos no processo",
        "task_type": TaskType.FOLLOW_UP,
        "default_priority": TaskPriority.LOW,
        "title_template": "Follow-up: {candidate_name}",
        "description_template": "Realizar follow-up com {candidate_name}. Último contato: {last_contact_date}.",
        "default_due_days": 7,
        "assigned_agent": "communication",
    },
    {
        "name": "Alerta de Vaga Crítica",
        "description": "Template para alertas de vagas em situação crítica",
        "task_type": TaskType.ALERT,
        "default_priority": TaskPriority.CRITICAL,
        "title_template": "URGENTE: Vaga Crítica - {job_title}",
        "description_template": "A vaga {job_title} está em situação crítica. {alert_reason}. Ação imediata necessária.",
        "default_due_days": 1,
        "assigned_agent": "recruiter_assistant",
    },
]


DEFAULT_ALERT_RULES = [
    {
        "name": "Vaga Crítica",
        "description": "Alerta para vagas marcadas como críticas ou urgentes",
        "alert_type": AlertType.JOB_CRITICAL,
        "severity": AlertSeverity.HIGH,
        "condition": {
            "field": "priority",
            "operator": "equals",
            "value": "critical",
            "additional_conditions": [
                {"field": "status", "operator": "equals", "value": "open"}
            ]
        },
        "check_interval_hours": 4,
        "notification_channels": ["email", "in_app", "teams"],
        "title_template": "Vaga Crítica: {job_title}",
        "message_template": "A vaga {job_title} está marcada como crítica e requer atenção imediata. Cliente: {client_name}. Dias aberta: {days_open}.",
    },
    {
        "name": "Vaga Parada",
        "description": "Alerta para vagas sem atividade por mais de 7 dias",
        "alert_type": AlertType.JOB_STALE,
        "severity": AlertSeverity.MEDIUM,
        "condition": {
            "field": "last_activity_date",
            "operator": "older_than_days",
            "value": 7,
            "additional_conditions": [
                {"field": "status", "operator": "in", "value": ["open", "in_progress"]}
            ]
        },
        "check_interval_hours": 24,
        "notification_channels": ["email", "in_app"],
        "title_template": "Vaga Parada: {job_title}",
        "message_template": "A vaga {job_title} não teve atividade nos últimos {days_inactive} dias. Considere reativar o sourcing ou atualizar o status.",
    },
    {
        "name": "Baixo Volume de Candidatos",
        "description": "Alerta quando uma vaga tem poucos candidatos no pipeline",
        "alert_type": AlertType.JOB_LOW_VOLUME,
        "severity": AlertSeverity.MEDIUM,
        "condition": {
            "field": "candidate_count",
            "operator": "less_than",
            "value": 3,
            "additional_conditions": [
                {"field": "status", "operator": "equals", "value": "open"},
                {"field": "days_open", "operator": "greater_than", "value": 5}
            ]
        },
        "check_interval_hours": 24,
        "notification_channels": ["email", "in_app"],
        "title_template": "Baixo Volume: {job_title}",
        "message_template": "A vaga {job_title} tem apenas {candidate_count} candidatos após {days_open} dias. Recomendamos intensificar o sourcing.",
    },
    {
        "name": "Candidato Esperando",
        "description": "Alerta quando candidato está esperando feedback por mais de 5 dias",
        "alert_type": AlertType.CANDIDATE_WAITING,
        "severity": AlertSeverity.HIGH,
        "condition": {
            "field": "days_waiting_feedback",
            "operator": "greater_than",
            "value": 5,
            "additional_conditions": [
                {"field": "status", "operator": "in", "value": ["awaiting_feedback", "interview_completed"]}
            ]
        },
        "check_interval_hours": 12,
        "notification_channels": ["email", "in_app", "teams"],
        "title_template": "Candidato Esperando: {candidate_name}",
        "message_template": "O candidato {candidate_name} está aguardando feedback há {days_waiting} dias para a vaga {job_title}. Experiência do candidato pode ser afetada.",
    },
    {
        "name": "Feedback Pendente",
        "description": "Alerta para feedbacks pendentes de entrevistas",
        "alert_type": AlertType.FEEDBACK_PENDING,
        "severity": AlertSeverity.HIGH,
        "condition": {
            "field": "interview_feedback_pending",
            "operator": "equals",
            "value": True,
            "additional_conditions": [
                {"field": "interview_date", "operator": "older_than_days", "value": 2}
            ]
        },
        "check_interval_hours": 24,
        "notification_channels": ["email", "in_app"],
        "title_template": "Feedback Pendente: {interviewer_name}",
        "message_template": "O entrevistador {interviewer_name} ainda não forneceu feedback sobre {candidate_name} para a vaga {job_title}. Entrevista realizada em {interview_date}.",
    },
    {
        "name": "Lembrete de Entrevista",
        "description": "Lembrete 24 horas antes de entrevistas agendadas",
        "alert_type": AlertType.INTERVIEW_REMINDER,
        "severity": AlertSeverity.LOW,
        "condition": {
            "field": "interview_date",
            "operator": "within_hours",
            "value": 24,
            "additional_conditions": [
                {"field": "status", "operator": "equals", "value": "scheduled"}
            ]
        },
        "check_interval_hours": 1,
        "notification_channels": ["email", "in_app", "teams"],
        "title_template": "Lembrete: Entrevista Amanhã",
        "message_template": "Lembrete: Entrevista agendada com {candidate_name} para a vaga {job_title}. Data: {interview_date}. Local/Link: {interview_location}.",
    },
    {
        "name": "Proposta Expirando",
        "description": "Alerta quando proposta está próxima da data de expiração",
        "alert_type": AlertType.PROPOSAL_EXPIRING,
        "severity": AlertSeverity.HIGH,
        "condition": {
            "field": "proposal_expiry_date",
            "operator": "within_days",
            "value": 3,
            "additional_conditions": [
                {"field": "proposal_status", "operator": "equals", "value": "pending"}
            ]
        },
        "check_interval_hours": 12,
        "notification_channels": ["email", "in_app", "teams"],
        "title_template": "Proposta Expirando: {candidate_name}",
        "message_template": "A proposta para {candidate_name} expira em {days_until_expiry} dias. Vaga: {job_title}. Valor: {proposal_value}. Entre em contato para confirmar decisão.",
    },
]


async def get_async_session():
    """Create async database session for seeding."""
    database_url = os.environ.get("DATABASE_URL", "")
    
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    if "sslmode=" in database_url:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)
        query_params.pop('sslmode', None)
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session, engine


async def seed_task_templates(session: AsyncSession) -> dict:
    """
    Seed default task templates.
    
    Returns:
        dict with created, skipped counts and details
    """
    results = {"created": 0, "skipped": 0, "details": []}
    
    for template_data in DEFAULT_TASK_TEMPLATES:
        existing = await session.execute(
            select(TaskTemplate).where(TaskTemplate.name == template_data["name"])
        )
        existing_template = existing.scalar_one_or_none()
        
        if existing_template:
            logger.info(f"⏭️  TaskTemplate '{template_data['name']}' already exists, skipping")
            results["skipped"] += 1
            results["details"].append({
                "name": template_data["name"],
                "status": "skipped",
                "reason": "already_exists"
            })
        else:
            template = TaskTemplate(**template_data)
            session.add(template)
            logger.info(f"✅ Created TaskTemplate: {template_data['name']}")
            results["created"] += 1
            results["details"].append({
                "name": template_data["name"],
                "status": "created"
            })
    
    await session.commit()
    return results


async def seed_alert_rules(session: AsyncSession) -> dict:
    """
    Seed default alert rules.
    
    Returns:
        dict with created, skipped counts and details
    """
    results = {"created": 0, "skipped": 0, "details": []}
    
    for rule_data in DEFAULT_ALERT_RULES:
        existing = await session.execute(
            select(AlertRule).where(AlertRule.name == rule_data["name"])
        )
        existing_rule = existing.scalar_one_or_none()
        
        if existing_rule:
            logger.info(f"⏭️  AlertRule '{rule_data['name']}' already exists, skipping")
            results["skipped"] += 1
            results["details"].append({
                "name": rule_data["name"],
                "status": "skipped",
                "reason": "already_exists"
            })
        else:
            rule = AlertRule(**rule_data)
            session.add(rule)
            logger.info(f"✅ Created AlertRule: {rule_data['name']}")
            results["created"] += 1
            results["details"].append({
                "name": rule_data["name"],
                "status": "created"
            })
    
    await session.commit()
    return results


async def run_all_seeds(session: AsyncSession) -> dict:
    """
    Run all seed functions.
    
    Returns:
        dict with results from all seed operations
    """
    logger.info("🌱 Starting database seeding...")
    
    results = {
        "task_templates": await seed_task_templates(session),
        "alert_rules": await seed_alert_rules(session),
    }
    
    total_created = results["task_templates"]["created"] + results["alert_rules"]["created"]
    total_skipped = results["task_templates"]["skipped"] + results["alert_rules"]["skipped"]
    
    logger.info(f"🎉 Seeding completed! Created: {total_created}, Skipped: {total_skipped}")
    
    return results


async def main():
    """Main function to run seeds from CLI."""
    async_session_factory, engine = await get_async_session()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_factory() as session:
        results = await run_all_seeds(session)
        
    await engine.dispose()
    
    print("\n" + "="*50)
    print("SEED DATA RESULTS")
    print("="*50)
    print(f"\nTask Templates:")
    print(f"  - Created: {results['task_templates']['created']}")
    print(f"  - Skipped: {results['task_templates']['skipped']}")
    print(f"\nAlert Rules:")
    print(f"  - Created: {results['alert_rules']['created']}")
    print(f"  - Skipped: {results['alert_rules']['skipped']}")
    print("\n" + "="*50)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
