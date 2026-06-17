"""
Admin API endpoints - Administrative operations including seed data.
"""
import logging
from app.shared.errors import LIAInternalError

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_admin
from app.repositories.dependencies import get_admin_repo
from app.repositories.admin_repository import AdminRepository
from app.models.alert import AlertSeverity, AlertType
from app.models.task import TaskPriority, TaskType
from app.shared.security.require_company_id import require_company_id

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


@router.post("/seed-data", response_model=None)
async def seed_database(
    repo: AdminRepository = Depends(get_admin_repo),
    _admin=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """
    Seed the database with default Task Templates and Alert Rules.

    This endpoint is idempotent - running it multiple times will only
    create records that don't already exist.

    Returns:
        Summary of seeding operations including created and skipped counts
    """
    try:
        logger.info("API: Starting database seeding via admin endpoint")

        results = {
            "task_templates": await repo.seed_task_templates(DEFAULT_TASK_TEMPLATES),
            "alert_rules": await repo.seed_alert_rules(DEFAULT_ALERT_RULES),
        }

        total_created = results["task_templates"]["created"] + results["alert_rules"]["created"]
        total_skipped = results["task_templates"]["skipped"] + results["alert_rules"]["skipped"]

        return {
            "success": True,
            "message": f"Seeding completed. Created: {total_created}, Skipped: {total_skipped}",
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Seeding failed: %s", str(e))
        raise LIAInternalError("Internal server error")


@router.post("/seed-data/task-templates", response_model=None)
async def seed_task_templates_only(
    repo: AdminRepository = Depends(get_admin_repo),
    _admin=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """
    Seed only Task Templates.

    Returns:
        Summary of task template seeding operations
    """
    try:
        logger.info("API: Seeding task templates only")
        results = await repo.seed_task_templates(DEFAULT_TASK_TEMPLATES)

        return {
            "success": True,
            "message": f"Task templates seeded. Created: {results['created']}, Skipped: {results['skipped']}",
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Task template seeding failed: %s", str(e))
        raise LIAInternalError("Internal server error")


@router.post("/seed-data/alert-rules", response_model=None)
async def seed_alert_rules_only(
    repo: AdminRepository = Depends(get_admin_repo),
    _admin=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """
    Seed only Alert Rules.

    Returns:
        Summary of alert rule seeding operations
    """
    try:
        logger.info("API: Seeding alert rules only")
        results = await repo.seed_alert_rules(DEFAULT_ALERT_RULES)

        return {
            "success": True,
            "message": f"Alert rules seeded. Created: {results['created']}, Skipped: {results['skipped']}",
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Alert rule seeding failed: %s", str(e))
        raise LIAInternalError("Internal server error")


@router.post("/seed-data/demo", response_model=None)
async def seed_demo_data_endpoint(
    repo: AdminRepository = Depends(get_admin_repo),
    _admin=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
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
        logger.info("API: Seeding demo data (jobs + candidates)")
        results = await repo.seed_demo()

        if results["success"]:
            return {
                "success": True,
                "message": results["message"],
                "data": {
                    "jobs_created": results["jobs_created"],
                    "candidates_created": results["candidates_created"],
                    "relationships_created": results["relationships_created"],
                },
            }
        else:
            raise LIAInternalError(f"Failed to seed demo data: {results.get('error', 'Unknown error')}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Demo data seeding failed: %s", str(e))
        raise LIAInternalError("Internal server error")


@router.delete("/seed-data/demo", response_model=None)
async def clear_demo_data_endpoint(
    repo: AdminRepository = Depends(get_admin_repo),
    _admin=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
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
        logger.info("API: Clearing demo data")
        results = await repo.clear_demo()

        if results["success"]:
            return {
                "success": True,
                "message": results["message"],
                "data": {
                    "jobs_deleted": results["jobs_deleted"],
                    "candidates_deleted": results["candidates_deleted"],
                    "relationships_deleted": results["relationships_deleted"],
                },
            }
        else:
            raise LIAInternalError(f"Failed to clear demo data: {results.get('error', 'Unknown error')}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Demo data clearing failed: %s", str(e))
        raise LIAInternalError("Internal server error")
