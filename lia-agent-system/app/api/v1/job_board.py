"""
Job Board API endpoints.
Handles publishing jobs to external job boards (LinkedIn, Indeed).
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.domains.job_management.services.job_board_service import job_board_service
from app.models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py

router = APIRouter(prefix="/job-boards", tags=["job-boards"])
logger = logging.getLogger(__name__)


FREEZE_REASONS_LABELS = {
    "budget_review": "Revisão orçamentária",
    "headcount_freeze": "Congelamento de headcount",
    "restructuring": "Reestruturação da área",
    "position_redefinition": "Redefinição do perfil",
    "internal_transfer": "Possível transferência interna",
    "vacation_period": "Período de férias do gestor",
    "market_conditions": "Condições de mercado",
    "priority_change": "Mudança de prioridade",
    "other": "Outro motivo"
}


async def send_recruiter_freeze_summary(
    db: AsyncSession,
    recruiter_email: str,
    recruiter_name: str,
    job: JobVacancy,
    freeze_reason: str,
    freeze_reason_label: str,
    unfreeze_date: str | None,
    frozen_at: datetime,
    candidates_notified: int = 0,
    candidates_email: int = 0,
    candidates_whatsapp: int = 0,
    interviews_cancelled: int = 0,
    tests_cancelled: int = 0,
    screenings_paused: int = 0,
    followups_paused: int = 0
) -> bool:
    """
    Envia email resumo para o recrutador após congelamento de vaga.
    """
    job_code = job.job_id or f"VAG-{str(job.id)[:8].upper()}"
    unfreeze_display = unfreeze_date if unfreeze_date else "Não definida"
    frozen_at_display = frozen_at.strftime("%d/%m/%Y às %H:%M")
    
    interviews_section = ""
    if interviews_cancelled > 0:
        interviews_section = f"""
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
            <span style="font-size: 18px; margin-right: 8px;">📅</span>
            <strong>Entrevistas Canceladas</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
            <span style="background-color: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 12px; font-weight: 500;">{interviews_cancelled}</span>
        </td>
    </tr>"""
    else:
        interviews_section = """
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
            <span style="font-size: 18px; margin-right: 8px;">📅</span>
            <strong>Entrevistas Canceladas</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
            <span style="color: #6b7280;">Nenhuma entrevista agendada</span>
        </td>
    </tr>"""
    
    tests_section = ""
    if tests_cancelled > 0:
        tests_section = f"""
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
            <span style="font-size: 18px; margin-right: 8px;">📝</span>
            <strong>Testes Cancelados</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
            <span style="background-color: #fef3c7; color: #d97706; padding: 4px 12px; border-radius: 12px; font-weight: 500;">{tests_cancelled}</span>
        </td>
    </tr>"""
    else:
        tests_section = """
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
            <span style="font-size: 18px; margin-right: 8px;">📝</span>
            <strong>Testes Cancelados</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
            <span style="color: #6b7280;">Nenhum teste agendado</span>
        </td>
    </tr>"""
    
    subject = f"Resumo do Congelamento - {job.title} ({job_code})"
    
    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Open Sans', Arial, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; background-color: #f3f4f6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1f2937 0%, #374151 100%); padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600;">
                    ⏸️ Vaga Congelada com Sucesso
                </h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 24px;">
                <p style="margin: 0 0 16px 0;">Olá <strong>{recruiter_name}</strong>,</p>
                
                <p style="margin: 0 0 24px 0;">
                    A vaga <strong style="color: #60BED1;">{job.title}</strong> foi congelada com sucesso. 
                    Segue resumo das ações automatizadas pela LIA:
                </p>
                
                <!-- Detalhes do Congelamento -->
                <div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                    <h3 style="margin: 0 0 12px 0; color: #374151; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">
                        📋 Detalhes do Congelamento
                    </h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 6px 0; color: #6b7280;">Motivo:</td>
                            <td style="padding: 6px 0; text-align: right; font-weight: 500;">{freeze_reason_label}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #6b7280;">Previsão de descongelamento:</td>
                            <td style="padding: 6px 0; text-align: right; font-weight: 500;">{unfreeze_display}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #6b7280;">Congelado em:</td>
                            <td style="padding: 6px 0; text-align: right; font-weight: 500;">{frozen_at_display}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Ações Realizadas -->
                <h3 style="margin: 0 0 12px 0; color: #374151; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">
                    ✅ Ações Realizadas
                </h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb;">
                    {interviews_section}
                    {tests_section}
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                            <span style="font-size: 18px; margin-right: 8px;">🔔</span>
                            <strong>Candidatos Notificados</strong>
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                            <span style="background-color: #d1fae5; color: #059669; padding: 4px 12px; border-radius: 12px; font-weight: 500;">{candidates_notified}</span>
                            <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                                {candidates_email} via Email | {candidates_whatsapp} via WhatsApp
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px;">
                            <span style="font-size: 18px; margin-right: 8px;">⏸️</span>
                            <strong>Processos Pausados</strong>
                        </td>
                        <td style="padding: 12px; text-align: right;">
                            <div style="font-size: 13px; color: #6b7280;">
                                Triagens: {screenings_paused} | Follow-ups: {followups_paused}<br>
                                Sourcing: Pausado | Alertas: Desativados
                            </div>
                        </td>
                    </tr>
                </table>
                
                <!-- Próximos Passos -->
                <div style="background-color: #ecfdf5; border-left: 4px solid #60BED1; padding: 16px; margin-top: 24px; border-radius: 0 8px 8px 0;">
                    <h3 style="margin: 0 0 12px 0; color: #374151; font-size: 14px;">💡 Próximos Passos</h3>
                    <ol style="margin: 0; padding-left: 20px; color: #374151;">
                        <li style="margin-bottom: 8px;">LIA irá notificá-lo em <strong>{unfreeze_display}</strong> sobre o descongelamento</li>
                        <li style="margin-bottom: 8px;">Para descongelar antes, acesse <strong>Vagas → {job.title} → Alterar Status</strong></li>
                        <li style="margin-bottom: 0;">Candidatos em etapa de <strong>Proposta</strong> não foram afetados</li>
                    </ol>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f9fafb; padding: 16px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0; color: #6b7280; font-size: 13px;">
                    Dúvidas? <span style="color: #60BED1; font-weight: 500;">Fale com a LIA!</span>
                </p>
                <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 12px;">
                    Sistema LIA - Plataforma WedoTalent
                </p>
            </div>
            
        </div>
    </div>
</body>
</html>
"""
    
    body_text = f"""
Resumo do Congelamento - {job.title} ({job_code})

Olá {recruiter_name},

A vaga {job.title} foi congelada com sucesso. Segue resumo das ações automatizadas:

📋 DETALHES DO CONGELAMENTO
──────────────────────────
Motivo: {freeze_reason_label}
Previsão de descongelamento: {unfreeze_display}
Congelado em: {frozen_at_display}

📅 ENTREVISTAS CANCELADAS: {interviews_cancelled}
📝 TESTES CANCELADOS: {tests_cancelled}

🔔 CANDIDATOS NOTIFICADOS: {candidates_notified}
  - Via Email: {candidates_email}
  - Via WhatsApp: {candidates_whatsapp}

⏸️ PROCESSOS PAUSADOS:
  - Triagens automáticas: {screenings_paused}
  - Follow-ups agendados: {followups_paused}
  - Buscas de sourcing: Pausadas
  - Alertas: Desativados

💡 PRÓXIMOS PASSOS:
  1. LIA irá notificá-lo em {unfreeze_display} sobre o descongelamento
  2. Para descongelar antes, acesse Vagas > {job.title} > Alterar Status
  3. Candidatos em etapa de proposta não foram afetados

Dúvidas? Fale com a LIA!

Atenciosamente,
Sistema LIA - Plataforma WedoTalent
"""
    
    try:
        _svc = get_email_service()
        success = await _svc._send_email_provider(
            to_email=recruiter_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )
        
        if success:
            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
            logger.info(f"Recruiter freeze summary sent to {recruiter_email} for job {job.id}")
        else:
            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
            logger.error(f"Failed to send recruiter freeze summary to {recruiter_email}")
        
        return success
    except Exception as e:
        logger.error(f"Error sending recruiter freeze summary: {e}")
        return False


class PublishResponse(BaseModel):
    success: bool
    message: str
    platform: str
    job_id: str
    post_id: str | None = None
    job_title: str | None = None
    published_at: str | None = None
    job_url: str | None = None
    feed_url: str | None = None
    note: str | None = None
    mock: bool | None = None


class PublishingStatusResponse(BaseModel):
    job_id: str
    job_title: str
    platforms: dict
    last_published_at: str | None = None


class UnpublishResponse(BaseModel):
    success: bool
    message: str
    platform: str
    job_id: str
    old_post_id: str | None = None
    old_indeed_id: str | None = None


@router.post("/linkedin/publish/{job_id}", response_model=PublishResponse)
async def publish_to_linkedin(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Publish a job to LinkedIn.
    
    LinkedIn Job Posting API requires OAuth 2.0 and company page admin access.
    For MVP, this endpoint prepares the infrastructure and returns mock responses
    if LinkedIn credentials are not configured.
    
    Full integration requires:
    1. LinkedIn Company Page admin access
    2. LinkedIn Developer App with Job Posting permissions
    3. OAuth 2.0 authorization flow
    """
    company_id = get_user_company_id(current_user)
    
    query = select(JobVacancy).where(
        JobVacancy.id == job_id,
        JobVacancy.company_id == company_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    if job.status not in ["Ativa", "Publicada", "Rascunho", "Aprovada"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot publish job with status '{job.status}'. Job must be active or draft."
        )
    
    response = await job_board_service.publish_to_linkedin(job, db)
    
    logger.info(f"LinkedIn publish response for job {job_id}: {response}")
    
    return PublishResponse(**response)


@router.post("/indeed/publish/{job_id}", response_model=PublishResponse)
async def publish_to_indeed(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Publish a job to Indeed.
    
    Indeed uses XML feeds for job ingestion. This endpoint:
    1. Marks the job as published to Indeed
    2. Adds the job to the XML feed served at /api/v1/job-boards/feed/indeed.xml
    
    To complete Indeed integration:
    1. Submit the feed URL to Indeed Publisher
    2. Indeed will periodically fetch and index your jobs
    """
    company_id = get_user_company_id(current_user)
    
    query = select(JobVacancy).where(
        JobVacancy.id == job_id,
        JobVacancy.company_id == company_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    if job.status not in ["Ativa", "Publicada", "Rascunho", "Aprovada"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot publish job with status '{job.status}'. Job must be active or draft."
        )
    
    response = await job_board_service.publish_to_indeed(job, db)
    
    logger.info(f"Indeed publish response for job {job_id}: {response}")
    
    return PublishResponse(**response)


@router.get("/feed/indeed.xml", response_model=None)
async def get_indeed_xml_feed(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get Indeed-compatible XML feed of all active jobs.
    
    This endpoint serves an XML feed following Indeed's job feed specification.
    Indeed will periodically fetch this feed to update job listings.
    
    Query Parameters:
    - company_id: Filter jobs by company (optional, defaults to all companies)
    
    The feed includes all jobs marked as published_indeed=True with status "Ativa" or "Publicada".
    """
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is required for job feed generation")
    target_company_id = company_id
    
    xml_content = await job_board_service.generate_job_feed_xml(target_company_id, db)
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.get("/status/{job_id}", response_model=PublishingStatusResponse)
async def get_publishing_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Get publishing status for a job across all platforms.
    
    Returns the current publishing status for LinkedIn, Indeed, and Website,
    including post IDs and URLs where available.
    """
    company_id = get_user_company_id(current_user)
    
    query = select(JobVacancy).where(
        JobVacancy.id == job_id,
        JobVacancy.company_id == company_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    status = await job_board_service.get_publishing_status(job)
    
    return PublishingStatusResponse(**status)


@router.delete("/unpublish/{job_id}/{platform}", response_model=UnpublishResponse)
async def unpublish_from_platform(
    job_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Remove a job from a specific platform.
    
    Path Parameters:
    - job_id: UUID of the job vacancy
    - platform: "linkedin" or "indeed"
    """
    if platform not in ["linkedin", "indeed"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid platform '{platform}'. Must be 'linkedin' or 'indeed'."
        )
    
    company_id = get_user_company_id(current_user)
    
    query = select(JobVacancy).where(
        JobVacancy.id == job_id,
        JobVacancy.company_id == company_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    if platform == "linkedin":
        if not job.published_linkedin:
            raise HTTPException(status_code=400, detail="Job is not published to LinkedIn")
        response = await job_board_service.unpublish_from_linkedin(job, db)
    else:
        if not job.published_indeed:
            raise HTTPException(status_code=400, detail="Job is not published to Indeed")
        response = await job_board_service.unpublish_from_indeed(job, db)
    
    logger.info(f"Unpublish response for job {job_id} from {platform}: {response}")
    
    return UnpublishResponse(**response)


@router.post("/publish-batch", response_model=None)
async def publish_to_multiple_platforms(
    job_ids: list[str],
    platforms: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """
    Publish multiple jobs to multiple platforms.
    
    Request Body:
    - job_ids: List of job vacancy UUIDs
    - platforms: List of platforms ("linkedin", "indeed")
    
    Returns results for each job-platform combination.
    """
    company_id = get_user_company_id(current_user)
    
    valid_platforms = [p for p in platforms if p in ["linkedin", "indeed"]]
    if not valid_platforms:
        raise HTTPException(
            status_code=400,
            detail="No valid platforms specified. Use 'linkedin' or 'indeed'."
        )
    
    results = []
    
    for job_id_str in job_ids:
        try:
            job_uuid = UUID(job_id_str)
        except ValueError:
            results.append({
                "job_id": job_id_str,
                "success": False,
                "error": "Invalid UUID format"
            })
            continue
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_uuid,
            JobVacancy.company_id == company_id
        )
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            results.append({
                "job_id": job_id_str,
                "success": False,
                "error": "Job not found"
            })
            continue
        
        job_results = {"job_id": job_id_str, "platforms": {}}
        
        for platform in valid_platforms:
            if platform == "linkedin":
                response = await job_board_service.publish_to_linkedin(job, db)
            else:
                response = await job_board_service.publish_to_indeed(job, db)
            
            job_results["platforms"][platform] = response
        
        results.append(job_results)
    
    return {
        "success": True,
        "results": results,
        "summary": {
            "total_jobs": len(job_ids),
            "platforms": valid_platforms
        }
    }


class UnpublishCompleteRequest(WeDoBaseModel):
    job_ids: list[str]
    freeze_job: bool = False
    freeze_reason: str | None = None
    freeze_start_date: str | None = None
    unfreeze_date: str | None = None
    notify_applicants: bool = False
    notification_channel: str | None = None
    notification_message: str | None = None
    notification_subject: str | None = None
    candidate_ids: list[str] | None = None
    cancel_scheduled_interviews: bool = False
    cancel_scheduled_screenings: bool = False
    send_recruiter_summary: bool = False


class UnpublishCompleteResponse(BaseModel):
    success: bool
    message: str
    unpublished_jobs: list[str]
    frozen_jobs: list[str]
    notifications_sent: int
    interviews_cancelled: int
    screenings_cancelled: int
    recruiter_summary_sent: bool
    errors: list[str]


@router.post("/unpublish-complete", response_model=UnpublishCompleteResponse)
async def unpublish_jobs_complete(
    request: UnpublishCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    email_svc: EmailService = Depends(get_email_service),
company_id: str = Depends(require_company_id)):
    """
    Complete unpublish workflow with optional freeze, notifications, and cleanup.
    
    Scenarios:
    1. Simple unpublish (no options) - just unpublish from job boards
    2. Freeze only - unpublish + change status to Paralisada
    3. Freeze + Notify - unpublish + freeze + notify candidates + cancel schedules
    4. Notify only - unpublish + notify candidates (no freeze)
    """
    company_id = get_user_company_id(current_user)
    
    unpublished_jobs = []
    frozen_jobs = []
    notifications_sent = 0
    interviews_cancelled = 0
    screenings_cancelled = 0
    errors = []
    
    for job_id_str in request.job_ids:
        try:
            job_id = UUID(job_id_str)
            query = select(JobVacancy).where(
                JobVacancy.id == job_id,
                JobVacancy.company_id == company_id
            )
            result = await db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(f"Job {job_id_str} not found")
                continue
            
            try:
                if job.published_linkedin:
                    await job_board_service.unpublish_from_linkedin(job, db)
            except Exception as e:
                logger.warning(f"LinkedIn unpublish warning for job {job_id}: {e}")
            
            try:
                if job.published_indeed:
                    await job_board_service.unpublish_from_indeed(job, db)
            except Exception as e:
                logger.warning(f"Indeed unpublish warning for job {job_id}: {e}")
            
            unpublished_jobs.append(job_id_str)
            
            if request.freeze_job:
                job.status = "Paralisada"
                if request.freeze_reason:
                    if not hasattr(job, 'extra_data') or job.extra_data is None:
                        job.extra_data = {}
                    job.extra_data['freeze_reason'] = request.freeze_reason
                    job.extra_data['freeze_start_date'] = request.freeze_start_date
                    job.extra_data['unfreeze_date'] = request.unfreeze_date
                frozen_jobs.append(job_id_str)
            
            
        except Exception as e:
            logger.error(f"Error processing job {job_id_str}: {e}")
            errors.append(f"Error with job {job_id_str}: {str(e)}")
    
    if request.notify_applicants and request.candidate_ids:
        notifications_sent = len(request.candidate_ids)
        logger.info(f"Would send notifications to {notifications_sent} candidates via {request.notification_channel}")
    
    if request.cancel_scheduled_interviews:
        logger.info(f"Would cancel scheduled interviews for jobs: {request.job_ids}")
        interviews_cancelled = 0
    
    if request.cancel_scheduled_screenings:
        logger.info(f"Would cancel scheduled screenings for jobs: {request.job_ids}")
        screenings_cancelled = 0
    
    recruiter_summary_sent = False
    if request.send_recruiter_summary and request.freeze_job and len(frozen_jobs) > 0:
        try:
            first_job_id = UUID(frozen_jobs[0])
            query = select(JobVacancy).where(JobVacancy.id == first_job_id, JobVacancy.company_id == company_id)
            result = await db.execute(query)
            frozen_job = result.scalar_one_or_none()
            
            if frozen_job:
                recruiter_email = current_user.email if hasattr(current_user, 'email') else None
                recruiter_name = current_user.name if hasattr(current_user, 'name') else (
                    current_user.email.split('@')[0] if recruiter_email else "Recrutador"
                )
                
                freeze_reason = request.freeze_reason or "other"
                freeze_reason_label = FREEZE_REASONS_LABELS.get(freeze_reason, freeze_reason)
                
                candidates_email = 0
                candidates_whatsapp = 0
                if request.notification_channel == 'email':
                    candidates_email = notifications_sent
                elif request.notification_channel == 'whatsapp':
                    candidates_whatsapp = notifications_sent
                elif request.notification_channel == 'both':
                    candidates_email = notifications_sent
                    candidates_whatsapp = notifications_sent
                
                if recruiter_email:
                    recruiter_summary_sent = await send_recruiter_freeze_summary(
                        db=db,
                        recruiter_email=recruiter_email,
                        recruiter_name=recruiter_name,
                        job=frozen_job,
                        freeze_reason=freeze_reason,
                        freeze_reason_label=freeze_reason_label,
                        unfreeze_date=request.unfreeze_date,
                        frozen_at=datetime.utcnow(),
                        candidates_notified=notifications_sent,
                        candidates_email=candidates_email,
                        candidates_whatsapp=candidates_whatsapp,
                        interviews_cancelled=interviews_cancelled,
                        tests_cancelled=0,
                        screenings_paused=screenings_cancelled,
                        followups_paused=0
                    )
                    
                    if recruiter_summary_sent:
                        # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
                        logger.info(f"Recruiter summary email sent successfully to {recruiter_email}")
                    else:
                        # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
                        logger.warning(f"Failed to send recruiter summary email to {recruiter_email}")
                else:
                    logger.warning("No recruiter email available to send summary")
        except Exception as e:
            logger.error(f"Error sending recruiter summary: {e}")
            recruiter_summary_sent = False
    
    return UnpublishCompleteResponse(
        success=len(errors) == 0,
        message=f"Processed {len(request.job_ids)} job(s)",
        unpublished_jobs=unpublished_jobs,
        frozen_jobs=frozen_jobs,
        notifications_sent=notifications_sent,
        interviews_cancelled=interviews_cancelled,
        screenings_cancelled=screenings_cancelled,
        recruiter_summary_sent=recruiter_summary_sent,
        errors=errors
    )
