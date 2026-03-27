"""
Notifications API endpoints.

Provides endpoints for:
- Listing notifications (bell/in-app)
- Chat queue notifications
- Marking as read
- Dismissing notifications
- Getting notification summary
- Multi-channel notification sending
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.notification_service import (
    notification_service, 
    NotificationType, 
    NotificationChannel,
    ProactiveNotificationType
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""
    user_id: str
    title: str
    message: Optional[str] = None
    notification_type: str = "info"
    category: Optional[str] = None
    source_agent: Optional[str] = None
    related_job_id: Optional[str] = None
    related_candidate_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None


class MultiChannelNotificationRequest(BaseModel):
    """Request model for sending multi-channel notifications."""
    user_id: str
    title: str
    message: str
    channels: List[str] = ["chat", "bell"]
    notification_type: str = "info"
    proactive_type: Optional[str] = None
    priority: str = "normal"
    data: Optional[dict] = None
    related_job_id: Optional[str] = None
    related_candidate_id: Optional[str] = None
    suggested_actions: Optional[List[str]] = None
    thread_id: Optional[str] = None


class MarkDeliveredRequest(BaseModel):
    """Request model for marking chat notifications as delivered."""
    notification_ids: List[str]


class RecruiterActionNotificationRequest(BaseModel):
    """Request model for sending recruiter notifications about job actions."""
    recruiter_ids: List[str]
    action: str  # 'pause', 'activate', 'unpublish', etc.
    job_titles: List[str]
    job_ids: List[str]
    channels: List[str] = ["bell"]  # email, teams, bell
    reason: Optional[str] = None
    cancelled_screenings: bool = False
    cancelled_interviews: bool = False
    cancelled_tests: bool = False
    notified_candidates_count: int = 0
    performed_by: Optional[str] = None


class TechnicalRequirement(BaseModel):
    name: str
    level: str
    required: bool = False

class BehavioralCompetency(BaseModel):
    name: str
    weight: str

class Language(BaseModel):
    name: str
    level: str

class SalaryRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "BRL"

class InterviewStageNotification(BaseModel):
    stageName: str
    order: int
    sla: Optional[int] = None

class PublishingPlatforms(BaseModel):
    linkedin: bool = False
    indeed: bool = False
    website: bool = False

class JobCreatedNotificationRequest(BaseModel):
    """Request model for sending job created notifications (workplan format)."""
    job_id: str
    job_title: str
    department: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    seniority_level: Optional[str] = None
    job_description: str
    technical_requirements: List[TechnicalRequirement] = []
    behavioral_competencies: List[BehavioralCompetency] = []
    languages: List[Language] = []
    salary_range: Optional[SalaryRange] = None
    benefits: List[str] = []
    deadline_screening: str
    deadline_shortlist: str
    deadline_closing: str
    interview_stages: List[InterviewStageNotification] = []
    publishing_platforms: PublishingPlatforms
    urgency_level: int = 3
    is_confidential: bool = False
    is_affirmative: bool = False
    recruiter_email: str
    recruiter_name: Optional[str] = None
    manager_email: Optional[str] = None
    manager_name: Optional[str] = None
    channels: List[str] = ["email", "teams"]


@router.get("")
async def get_notifications(
    user_id: str = "default_user",
    unread_only: bool = False,
    category: Optional[str] = None,
    notification_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for a user.
    """
    try:
        result = await notification_service.get_notifications(
            user_id=user_id,
            unread_only=unread_only,
            category=category,
            notification_type=notification_type,
            limit=limit,
            offset=offset,
            db=db
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_notification_summary(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification summary for header badge.
    """
    try:
        summary = await notification_service.get_notification_summary(user_id, db)
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting notification summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_notification(
    request: CreateNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new notification.
    """
    try:
        notification_type_enum = NotificationType(request.notification_type) if request.notification_type in [t.value for t in NotificationType] else NotificationType.INFO
        
        notification = await notification_service.create_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=notification_type_enum,
            category=request.category,
            source_agent=request.source_agent,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            action_url=request.action_url,
            action_label=request.action_label,
            db=db
        )
        return {
            "success": True,
            "data": notification
        }
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read.
    """
    try:
        success = await notification_service.mark_as_read(notification_id, user_id, db)
        if success:
            return {"success": True, "message": "Notificação marcada como lida"}
        else:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-all")
async def mark_all_as_read(
    user_id: str = "default_user",
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read for a user.
    """
    try:
        count = await notification_service.mark_all_as_read(user_id, category, db)
        return {
            "success": True,
            "message": f"{count} notificações marcadas como lidas"
        }
    except Exception as e:
        logger.error(f"Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: str,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Dismiss a notification.
    """
    try:
        success = await notification_service.dismiss_notification(notification_id, user_id, db)
        if success:
            return {"success": True, "message": "Notificação descartada"}
        else:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recruiter-action")
async def send_recruiter_action_notification(
    request: RecruiterActionNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send notifications to recruiters about job actions (pause, activate, unpublish, etc.).
    Supports multiple channels: email, teams, bell.
    """
    if not request.recruiter_ids:
        raise HTTPException(status_code=400, detail="recruiter_ids is required")
    if not request.job_titles or not request.job_ids:
        raise HTTPException(status_code=400, detail="job_titles and job_ids are required")
    if len(request.job_titles) != len(request.job_ids):
        raise HTTPException(status_code=400, detail="job_titles and job_ids must have the same length")
    
    try:
        action_labels = {
            'pause': 'pausada',
            'activate': 'reativada',
            'unpublish': 'despublicada',
            'publish': 'publicada',
            'close': 'encerrada',
            'assign': 'atribuída'
        }
        action_label = action_labels.get(request.action, request.action)
        
        jobs_text = ", ".join(request.job_titles[:3])
        if len(request.job_titles) > 3:
            jobs_text += f" e mais {len(request.job_titles) - 3}"
        
        title = f"Vaga {action_label}: {jobs_text}"
        
        message_parts = [f"A(s) vaga(s) {jobs_text} foi(ram) {action_label}."]
        
        if request.reason:
            message_parts.append(f"Motivo: {request.reason}")
        
        actions_taken = []
        if request.cancelled_screenings:
            actions_taken.append("triagens canceladas")
        if request.cancelled_interviews:
            actions_taken.append("entrevistas desmarcadas")
        if request.cancelled_tests:
            actions_taken.append("testes cancelados")
        
        if actions_taken:
            message_parts.append(f"Ações executadas: {', '.join(actions_taken)}.")
        
        if request.notified_candidates_count > 0:
            message_parts.append(f"{request.notified_candidates_count} candidato(s) notificado(s).")
        
        if request.performed_by:
            message_parts.append(f"Ação realizada por: {request.performed_by}")
        
        message = " ".join(message_parts)
        
        channel_map = {
            'email': NotificationChannel.EMAIL,
            'teams': NotificationChannel.TEAMS,
            'bell': NotificationChannel.BELL
        }
        channels = [channel_map[c] for c in request.channels if c in channel_map]
        
        if not channels:
            channels = [NotificationChannel.BELL]
        
        results = []
        for recruiter_id in request.recruiter_ids:
            result = await notification_service.send_multi_channel_notification(
                user_id=recruiter_id,
                title=title,
                message=message,
                channels=channels,
                notification_type=NotificationType.INFO,
                priority="normal",
                data={
                    "action": request.action,
                    "job_ids": request.job_ids,
                    "job_titles": request.job_titles,
                    "reason": request.reason,
                    "cancelled_screenings": request.cancelled_screenings,
                    "cancelled_interviews": request.cancelled_interviews,
                    "cancelled_tests": request.cancelled_tests,
                    "notified_candidates_count": request.notified_candidates_count
                },
                related_job_id=request.job_ids[0] if request.job_ids else None,
                db=db
            )
            results.append({"recruiter_id": recruiter_id, "result": result})
        
        return {
            "success": True,
            "message": f"Notificação enviada para {len(request.recruiter_ids)} recrutador(es)",
            "data": {
                "notifications_sent": len(results),
                "channels": request.channels,
                "results": results
            }
        }
    except Exception as e:
        logger.error(f"Error sending recruiter action notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Get the count of unread notifications for the bell badge.
    """
    try:
        summary = await notification_service.get_notification_summary(user_id, db)
        return {
            "success": True,
            "data": {
                "unread_count": summary["unread_count"],
                "urgent_count": summary.get("urgent_count", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat")
async def get_chat_notifications(
    user_id: str = "default_user",
    thread_id: Optional[str] = None,
    undelivered_only: bool = True,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending chat notifications for inline display in chat.
    """
    try:
        result = await notification_service.get_chat_notifications(
            user_id=user_id,
            thread_id=thread_id,
            undelivered_only=undelivered_only,
            limit=limit,
            db=db
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error getting chat notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{notification_id}/delivered")
async def mark_chat_notification_delivered(
    notification_id: str,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a single chat notification as delivered.
    """
    try:
        success = await notification_service.mark_chat_notification_delivered(
            notification_id, user_id, db
        )
        if success:
            return {"success": True, "message": "Notificação marcada como entregue"}
        else:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking chat notification as delivered: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/delivered")
async def mark_chat_notifications_delivered(
    request: MarkDeliveredRequest,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Mark multiple chat notifications as delivered.
    """
    try:
        count = await notification_service.mark_chat_notifications_delivered(
            request.notification_ids, user_id, db
        )
        return {
            "success": True,
            "message": f"{count} notificações marcadas como entregues"
        }
    except Exception as e:
        logger.error(f"Error marking chat notifications as delivered: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_multi_channel_notification(
    request: MultiChannelNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a notification to multiple channels (chat, bell, teams).
    """
    try:
        channels = []
        for ch in request.channels:
            try:
                channels.append(NotificationChannel(ch))
            except ValueError:
                pass
        
        if not channels:
            channels = [NotificationChannel.CHAT, NotificationChannel.BELL]
        
        notification_type_enum = NotificationType.INFO
        if request.notification_type:
            try:
                notification_type_enum = NotificationType(request.notification_type)
            except ValueError:
                pass
        
        proactive_type_enum = None
        if request.proactive_type:
            try:
                proactive_type_enum = ProactiveNotificationType(request.proactive_type)
            except ValueError:
                pass
        
        result = await notification_service.send_multi_channel_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            channels=channels,
            notification_type=notification_type_enum,
            proactive_type=proactive_type_enum,
            priority=request.priority,
            data=request.data,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            suggested_actions=request.suggested_actions,
            thread_id=request.thread_id,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error sending multi-channel notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive")
async def send_proactive_notification(
    user_id: str,
    proactive_type: str,
    title: str,
    message: str,
    data: Optional[dict] = None,
    related_job_id: Optional[str] = None,
    related_candidate_id: Optional[str] = None,
    suggested_actions: Optional[List[str]] = None,
    priority: str = "normal",
    db: AsyncSession = Depends(get_db)
):
    """
    Send a proactive notification (convenience endpoint).
    Automatically sends to both chat and bell channels.
    """
    try:
        proactive_type_enum = None
        try:
            proactive_type_enum = ProactiveNotificationType(proactive_type)
        except ValueError:
            pass
        
        if not proactive_type_enum:
            raise HTTPException(status_code=400, detail=f"Invalid proactive_type: {proactive_type}")
        
        result = await notification_service.send_proactive_notification(
            user_id=user_id,
            proactive_type=proactive_type_enum,
            title=title,
            message=message,
            data=data,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            suggested_actions=suggested_actions,
            priority=priority,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proactive notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ProactiveAlertCheckRequest(BaseModel):
    """Request model for triggering proactive alert check."""
    user_id: str
    company_id: str


class UpdateThresholdRequest(BaseModel):
    """Request model for updating alert thresholds."""
    condition: str
    threshold_config: dict


@router.post("/proactive/check")
async def trigger_proactive_check(
    request: ProactiveAlertCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a proactive alert check for a user.
    
    This checks all conditions (pipeline, productivity, communication,
    predictive, system) and sends notifications for any triggered alerts.
    """
    try:
        from app.services.proactive_alert_service import proactive_alert_service
        
        triggered_alerts = await proactive_alert_service.check_all_conditions(
            user_id=request.user_id,
            company_id=request.company_id,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "alerts_triggered": len(triggered_alerts),
                "alerts": [
                    {
                        "condition": (cond.value if hasattr(cond := alert.get("condition"), "value") else cond) if (cond := alert.get("condition")) is not None else None,
                        "category": (cat.value if hasattr(cat := alert.get("category"), "value") else cat) if (cat := alert.get("category")) is not None else None,
                        "title": alert.get("title"),
                        "severity": (sev.value if hasattr(sev := alert.get("severity"), "value") else str(sev)) if (sev := alert.get("severity")) is not None else None
                    }
                    for alert in triggered_alerts
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error triggering proactive check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/history")
async def get_proactive_alert_history(
    user_id: str = "default_user"
):
    """
    Get history of proactive alerts sent to a user.
    
    This shows which alerts were triggered and when to help
    understand notification patterns.
    """
    try:
        from app.services.proactive_alert_service import proactive_alert_service
        
        history = await proactive_alert_service.get_alert_history(user_id)
        
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/proactive/thresholds")
async def update_alert_threshold(
    request: UpdateThresholdRequest
):
    """
    Update threshold configuration for an alert condition.
    
    This allows customizing when alerts are triggered for
    each specific condition.
    """
    try:
        from app.services.proactive_alert_service import (
            proactive_alert_service,
            AlertCondition
        )
        
        try:
            condition = AlertCondition(request.condition)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid condition: {request.condition}. Valid conditions are: {[c.value for c in AlertCondition]}"
            )
        
        proactive_alert_service.update_threshold(condition, request.threshold_config)
        
        return {
            "success": True,
            "message": f"Threshold updated for {request.condition}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/thresholds")
async def get_alert_thresholds():
    """
    Get all alert threshold configurations.
    
    Returns the current configuration for all alert conditions
    including thresholds, cooldowns, and severity levels.
    """
    try:
        from app.services.proactive_alert_service import (
            ThresholdConfig,
            AlertCondition
        )
        
        thresholds = {}
        for condition in AlertCondition:
            config = ThresholdConfig.get_threshold(condition)
            thresholds[condition.value] = config
        
        return {
            "success": True,
            "data": thresholds
        }
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-created")
async def send_job_created_notification(
    request: JobCreatedNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send job created notification to recruiter and manager.
    
    Sends notification in workplan format with all job details including:
    - Job title, department, location
    - Technical requirements and behavioral competencies
    - Interview stages with SLAs
    - Deadlines (screening, shortlist, closing)
    - Publishing platforms
    
    Channels: email and/or teams
    Recipients: recruiter (required) and manager/hiring manager (optional)
    """
    try:
        from app.services.email_service import email_service
        from app.services.teams_service import teams_service
        from datetime import datetime
        
        notifications_sent = {
            "recruiter": {"email": False, "teams": False},
            "manager": {"email": False, "teams": False}
        }
        errors = []
        
        urgency_labels = {1: "Muito Baixa", 2: "Baixa", 3: "Média", 4: "Alta", 5: "Urgente"}
        urgency_label = urgency_labels.get(request.urgency_level, "Média")
        
        tech_reqs_list = "\n".join([
            f"  • {r.name} ({r.level}){' - Obrigatório' if r.required else ''}"
            for r in request.technical_requirements
        ]) if request.technical_requirements else "  Nenhum definido"
        
        competencies_list = "\n".join([
            f"  • {c.name} (Peso: {c.weight})"
            for c in request.behavioral_competencies
        ]) if request.behavioral_competencies else "  Nenhum definido"
        
        languages_list = ", ".join([
            f"{l.name} ({l.level})" for l in request.languages
        ]) if request.languages else "Não especificado"
        
        benefits_list = ", ".join(request.benefits) if request.benefits else "A definir"
        
        stages_list = "\n".join([
            f"  {s.order}. {s.stageName}" + (f" (SLA: {s.sla} dias)" if s.sla else "")
            for s in request.interview_stages
        ]) if request.interview_stages else "  Pipeline padrão"
        
        platforms = []
        if request.publishing_platforms.linkedin:
            platforms.append("LinkedIn")
        if request.publishing_platforms.indeed:
            platforms.append("Indeed")
        if request.publishing_platforms.website:
            platforms.append("Website")
        platforms_text = ", ".join(platforms) if platforms else "Nenhuma"
        
        salary_text = "A definir"
        if request.salary_range:
            if request.salary_range.min and request.salary_range.max:
                salary_text = f"R$ {request.salary_range.min:,.0f} - R$ {request.salary_range.max:,.0f}"
            elif request.salary_range.min:
                salary_text = f"A partir de R$ {request.salary_range.min:,.0f}"
            elif request.salary_range.max:
                salary_text = f"Até R$ {request.salary_range.max:,.0f}"
        
        workplan_content = f"""
═══════════════════════════════════════════════════════════
📋 WORKPLAN - NOVA VAGA CRIADA
═══════════════════════════════════════════════════════════

🎯 INFORMAÇÕES GERAIS
───────────────────────────────────────────────────────────
Título:           {request.job_title}
Área/Departamento: {request.department or 'A definir'}
Localização:       {request.location or 'A definir'}
Modelo de Trabalho: {request.work_model or 'A definir'}
Senioridade:       {request.seniority_level or 'A definir'}
Urgência:          {urgency_label}
{f"🔒 Vaga Confidencial" if request.is_confidential else ""}
{f"🌈 Vaga Afirmativa" if request.is_affirmative else ""}

💰 REMUNERAÇÃO
───────────────────────────────────────────────────────────
Faixa Salarial:    {salary_text}
Benefícios:        {benefits_list}

🛠️ REQUISITOS TÉCNICOS
───────────────────────────────────────────────────────────
{tech_reqs_list}

🎭 COMPETÊNCIAS COMPORTAMENTAIS
───────────────────────────────────────────────────────────
{competencies_list}

🌐 IDIOMAS
───────────────────────────────────────────────────────────
{languages_list}

📅 CRONOGRAMA E PRAZOS
───────────────────────────────────────────────────────────
Prazo Triagem:     {request.deadline_screening}
Prazo Shortlist:   {request.deadline_shortlist}
Prazo Fechamento:  {request.deadline_closing}

🔄 ETAPAS DO PROCESSO
───────────────────────────────────────────────────────────
{stages_list}

📢 PUBLICAÇÃO
───────────────────────────────────────────────────────────
Plataformas:       {platforms_text}

📝 DESCRIÇÃO DA VAGA
───────────────────────────────────────────────────────────
{request.job_description}

═══════════════════════════════════════════════════════════
ID da Vaga: {request.job_id}
Criado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Recrutador: {request.recruiter_name or request.recruiter_email}
{f"Gestor: {request.manager_name or request.manager_email}" if request.manager_email else ""}
═══════════════════════════════════════════════════════════
"""
        
        email_subject = f"🚀 Nova Vaga Criada: {request.job_title} | {request.department or 'Empresa'}"
        teams_title = f"📋 Nova Vaga: {request.job_title}"
        
        recipients = []
        if request.recruiter_email:
            recipients.append({
                "email": request.recruiter_email,
                "name": request.recruiter_name,
                "role": "recruiter"
            })
        if request.manager_email:
            recipients.append({
                "email": request.manager_email,
                "name": request.manager_name,
                "role": "manager"
            })
        
        for recipient in recipients:
            role = recipient["role"]
            
            if "email" in request.channels:
                try:
                    html_content = f"""
                    <html>
                    <body style="font-family: 'Open Sans', Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
                            <div style="background: linear-gradient(135deg, #60BED1 0%, #4A9BA8 100%); padding: 20px; border-radius: 8px 8px 0 0;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">
                                    🚀 Nova Vaga Criada
                                </h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">
                                    {request.job_title}
                                </p>
                            </div>
                            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                                <pre style="font-family: 'Courier New', monospace; font-size: 13px; background: white; padding: 20px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #e5e7eb;">{workplan_content}</pre>
                                <div style="margin-top: 20px; text-align: center;">
                                    <a href="https://lia.wedotalent.com/jobs/{request.job_id}" 
                                       style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                                        Ver Vaga no LIA
                                    </a>
                                </div>
                            </div>
                            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                                Este é um email automático do LIA - Sistema de Recrutamento Inteligente
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    await email_service.send_email(
                        to_email=recipient["email"],
                        subject=email_subject,
                        html_content=html_content,
                        text_content=workplan_content
                    )
                    notifications_sent[role]["email"] = True
                    logger.info(f"📧 Email sent to {role}: {recipient['email']}")
                except Exception as e:
                    error_msg = f"Failed to send email to {role} ({recipient['email']}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            if "teams" in request.channels:
                try:
                    await teams_service.send_message(
                        user_email=recipient["email"],
                        title=teams_title,
                        message=workplan_content,
                        action_url=f"https://lia.wedotalent.com/jobs/{request.job_id}",
                        action_label="Ver Vaga"
                    )
                    notifications_sent[role]["teams"] = True
                    logger.info(f"📨 Teams message sent to {role}: {recipient['email']}")
                except Exception as e:
                    error_msg = f"Failed to send Teams message to {role} ({recipient['email']}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        success = any([
            notifications_sent["recruiter"]["email"],
            notifications_sent["recruiter"]["teams"],
            notifications_sent["manager"]["email"],
            notifications_sent["manager"]["teams"]
        ])
        
        logger.info(f"📬 Job created notification sent: {request.job_title} - Results: {notifications_sent}")
        
        return {
            "success": success,
            "notifications_sent": notifications_sent,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error sending job created notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
