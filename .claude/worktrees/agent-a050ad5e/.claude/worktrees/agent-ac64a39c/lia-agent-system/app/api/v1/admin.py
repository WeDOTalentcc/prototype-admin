"""
Admin API endpoints - Administrative operations including seed data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.models.task import TaskTemplate, TaskType, TaskPriority
from app.models.alert import AlertRule, AlertType, AlertSeverity
from app.services.seed_service import seed_demo_data, clear_demo_data

router = APIRouter(prefix="/admin", tags=["admin"])
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
    
    await session.flush()
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
    
    await session.flush()
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


@router.post("/seed-data")
async def seed_database(db: AsyncSession = Depends(get_db)):
    """
    Seed the database with default Task Templates and Alert Rules.
    
    This endpoint is idempotent - running it multiple times will only
    create records that don't already exist.
    
    Returns:
        Summary of seeding operations including created and skipped counts
    """
    try:
        logger.info("🌱 API: Starting database seeding via admin endpoint")
        
        results = await run_all_seeds(db)
        
        total_created = results["task_templates"]["created"] + results["alert_rules"]["created"]
        total_skipped = results["task_templates"]["skipped"] + results["alert_rules"]["skipped"]
        
        return {
            "success": True,
            "message": f"Seeding completed. Created: {total_created}, Skipped: {total_skipped}",
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Seeding failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed database: {str(e)}"
        )


@router.post("/seed-data/task-templates")
async def seed_task_templates_only(db: AsyncSession = Depends(get_db)):
    """
    Seed only Task Templates.
    
    Returns:
        Summary of task template seeding operations
    """
    try:
        logger.info("🌱 API: Seeding task templates only")
        results = await seed_task_templates(db)
        
        return {
            "success": True,
            "message": f"Task templates seeded. Created: {results['created']}, Skipped: {results['skipped']}",
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Task template seeding failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed task templates: {str(e)}"
        )


@router.post("/seed-data/alert-rules")
async def seed_alert_rules_only(db: AsyncSession = Depends(get_db)):
    """
    Seed only Alert Rules.
    
    Returns:
        Summary of alert rule seeding operations
    """
    try:
        logger.info("🌱 API: Seeding alert rules only")
        results = await seed_alert_rules(db)
        
        return {
            "success": True,
            "message": f"Alert rules seeded. Created: {results['created']}, Skipped: {results['skipped']}",
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Alert rule seeding failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed alert rules: {str(e)}"
        )


@router.post("/seed-data/demo")
async def seed_demo_data_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Seed demo data for vagas (jobs) and candidatos (candidates).
    
    Creates:
    - 10 realistic job vacancies with [DEMO] prefix
    - 15 candidates with [DEMO] prefix in their names
    - Vacancy-candidate relationships with various stages
    
    All demo data is clearly marked and can be easily identified/removed.
    
    Returns:
        Summary of demo data seeding operations
    """
    try:
        logger.info("🌱 API: Seeding demo data (jobs + candidates)")
        results = await seed_demo_data(db)
        
        if results["success"]:
            return {
                "success": True,
                "message": results["message"],
                "data": {
                    "jobs_created": results["jobs_created"],
                    "candidates_created": results["candidates_created"],
                    "relationships_created": results["relationships_created"]
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to seed demo data: {results.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Demo data seeding failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed demo data: {str(e)}"
        )


@router.delete("/seed-data/demo")
async def clear_demo_data_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Clear all demo data from the database.
    
    Removes:
    - All job vacancies with [DEMO] prefix
    - All candidates with source = 'SEED_DATA'
    - All vacancy-candidate relationships with source = 'SEED_DATA'
    
    Returns:
        Summary of cleared demo data
    """
    try:
        logger.info("🗑️ API: Clearing demo data")
        results = await clear_demo_data(db)
        
        if results["success"]:
            return {
                "success": True,
                "message": results["message"],
                "data": {
                    "jobs_deleted": results["jobs_deleted"],
                    "candidates_deleted": results["candidates_deleted"],
                    "relationships_deleted": results["relationships_deleted"]
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear demo data: {results.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Demo data clearing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear demo data: {str(e)}"
        )
