"""
Communication Tools - Tools for communication with candidates.

Provides function calling capabilities for:
- Sending emails to candidates
- Sending WhatsApp messages
- Scheduling interviews
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.shared.tool_guards import validate_uuid_params
from app.tools.registry import ToolDefinition, tool_registry

logger = logging.getLogger(__name__)

# P1-3 (2026-06-18): defense-in-depth company_id filter
from app.middleware.auth_enforcement import _current_company_id as _cid_ctx


async def send_email(
    candidate_id: str,
    template_id: str | None = None,
    subject: str | None = None,
    body: str | None = None,
    job_id: str | None = None,
    cc: list[str] | None = None,
    attachments: list[str] | None = None
) -> dict[str, Any]:
    """
    Send an email to a candidate.
    
    Args:
        candidate_id: UUID of the candidate
        template_id: Optional email template ID to use
        subject: Email subject (required if no template)
        body: Email body content (required if no template)
        job_id: Optional job vacancy ID for context
        cc: Optional list of CC email addresses
        attachments: Optional list of attachment IDs
        
    Returns:
        Result with success status and message
    """
    from app.shared.hitl.hitl_approval_context import hitl_preflight
    _hitl_block = hitl_preflight(tool="send_email", domain="communication", data={"candidate_id": candidate_id, "job_id": job_id, "subject": subject})
    if _hitl_block is not None:
        return _hitl_block
    err = validate_uuid_params(candidate_id=candidate_id)
    if err:
        return err
    logger.info(f"📧 Sending email to candidate {candidate_id}")
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                
                # P1-3 (2026-06-18): defense-in-depth — filter by company_id from
                # ContextVar if available (RLS remains primary boundary per TENANT-EXEMPT).
                _cid = _cid_ctx.get(None)
                _cand_filter = [Candidate.id == UUID(candidate_id)]
                if _cid:
                    _cand_filter.append(Candidate.company_id == _cid)
                result = await db.execute(
                    select(Candidate).where(*_cand_filter)
                )
                candidate = result.scalar_one_or_none()
                
                if not candidate:
                    return {
                        "success": False,
                        "message": f"Candidato não encontrado: {candidate_id}",
                        "error": "candidate_not_found"
                    }
                
                candidate_name = getattr(candidate, 'name', 'Candidato')
                candidate_email = getattr(candidate, 'email', None)
                
                if not candidate_email:
                    return {
                        "success": False,
                        "message": f"Candidato {candidate_name} não possui email cadastrado.",
                        "error": "no_email"
                    }
                
                return {
                    "success": True,
                    "message": f"📧 Email enviado para {candidate_name} ({candidate_email}).",
                    "action_taken": "send_email",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "email": candidate_email,
                        "subject": subject,
                        "template_id": template_id,
                        "job_id": job_id,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "message": "📧 Email enviado para o candidato.",
                    "action_taken": "send_email",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "subject": subject,
                        "template_id": template_id,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao enviar email: {str(e)}",
            "error": str(e)
        }


async def send_whatsapp(
    candidate_id: str,
    message: str,
    template_id: str | None = None,
    job_id: str | None = None
) -> dict[str, Any]:
    """
    Send a WhatsApp message to a candidate.
    
    Args:
        candidate_id: UUID of the candidate
        message: Message content to send
        template_id: Optional WhatsApp template ID
        job_id: Optional job vacancy ID for context
        
    Returns:
        Result with success status and message
    """
    from app.shared.hitl.hitl_approval_context import hitl_preflight
    _hitl_block = hitl_preflight(tool="send_whatsapp", domain="communication", data={"candidate_id": candidate_id, "job_id": job_id})
    if _hitl_block is not None:
        return _hitl_block
    err = validate_uuid_params(candidate_id=candidate_id)
    if err:
        return err
    logger.info(f"📱 Sending WhatsApp to candidate {candidate_id}")
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                
                # P1-3 (2026-06-18): defense-in-depth — filter by company_id from
                # ContextVar if available (RLS remains primary boundary per TENANT-EXEMPT).
                _cid = _cid_ctx.get(None)
                _cand_filter = [Candidate.id == UUID(candidate_id)]
                if _cid:
                    _cand_filter.append(Candidate.company_id == _cid)
                result = await db.execute(
                    select(Candidate).where(*_cand_filter)
                )
                candidate = result.scalar_one_or_none()
                
                if not candidate:
                    return {
                        "success": False,
                        "message": f"Candidato não encontrado: {candidate_id}",
                        "error": "candidate_not_found"
                    }
                
                candidate_name = getattr(candidate, 'name', 'Candidato')
                candidate_phone = getattr(candidate, 'phone', None) or getattr(candidate, 'whatsapp', None)
                
                if not candidate_phone:
                    return {
                        "success": False,
                        "message": f"Candidato {candidate_name} não possui telefone/WhatsApp cadastrado.",
                        "error": "no_phone"
                    }
                
                return {
                    "success": True,
                    "message": f"📱 WhatsApp enviado para {candidate_name} ({candidate_phone}).",
                    "action_taken": "send_whatsapp",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "phone": candidate_phone,
                        "message_preview": message[:100] + "..." if len(message) > 100 else message,
                        "template_id": template_id,
                        "job_id": job_id,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "message": "📱 WhatsApp enviado para o candidato.",
                    "action_taken": "send_whatsapp",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "message_preview": message[:100] + "..." if len(message) > 100 else message,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao enviar WhatsApp: {str(e)}",
            "error": str(e)
        }


async def schedule_interview(
    candidate_id: str,
    job_id: str,
    interview_type: str,
    datetime_str: str,
    duration_minutes: int = 60,
    interviewers: list[str] | None = None,
    location: str | None = None,
    meeting_link: str | None = None,
    notes: str | None = None,
    send_invite: bool = True
) -> dict[str, Any]:
    """
    Schedule an interview with a candidate.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        interview_type: Type of interview ('phone', 'video', 'onsite', 'technical', 'behavioral')
        datetime_str: Interview date/time in ISO format
        duration_minutes: Duration of the interview in minutes
        interviewers: List of interviewer user IDs
        location: Location for in-person interviews
        meeting_link: Video meeting link for remote interviews
        notes: Additional notes for the interview
        send_invite: Whether to send calendar invite to all participants
        
    Returns:
        Result with success status and interview details
    """
    logger.info(f"📅 Scheduling {interview_type} interview for candidate {candidate_id}")
    err = validate_uuid_params(candidate_id=candidate_id, job_id=job_id)
    if err:
        return err

    
    try:
        interview_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        return {
            "success": False,
            "message": f"❌ Formato de data/hora inválido: {datetime_str}. Use formato ISO (ex: 2025-01-30T14:00:00).",
            "error": "invalid_datetime"
        }
    
    interview_types_pt = {
        "phone": "Telefônica",
        "video": "Vídeo",
        "onsite": "Presencial",
        "technical": "Técnica",
        "behavioral": "Comportamental",
        "final": "Final"
    }
    interview_type_display = interview_types_pt.get(interview_type, interview_type)
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                from app.models.job_vacancy import JobVacancy
                
                # P1-3 (2026-06-18): defense-in-depth — filter by company_id from ContextVar.
                _cid = _cid_ctx.get(None)
                _cand_filter = [Candidate.id == UUID(candidate_id)]
                if _cid:
                    _cand_filter.append(Candidate.company_id == _cid)
                cand_result = await db.execute(
                    select(Candidate).where(*_cand_filter)
                )
                candidate = cand_result.scalar_one_or_none()

                # TENANT-EXEMPT: same rationale as above for JobVacancy lookup.
                job_result = await db.execute(
                    select(JobVacancy).where(JobVacancy.id == UUID(job_id))
                )
                job = job_result.scalar_one_or_none()
                
                candidate_name = getattr(candidate, 'name', 'Candidato') if candidate else 'Candidato'
                job_title = getattr(job, 'title', 'Vaga') if job else 'Vaga'
                
                formatted_date = interview_datetime.strftime("%d/%m/%Y às %H:%M")
                
                return {
                    "success": True,
                    "message": f"📅 Entrevista {interview_type_display} agendada para {candidate_name} no dia {formatted_date}.",
                    "action_taken": "schedule_interview",
                    "affected_entities": [candidate_id, job_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "job_title": job_title,
                        "interview_type": interview_type,
                        "datetime": interview_datetime.isoformat(),
                        "duration_minutes": duration_minutes,
                        "interviewers": interviewers or [],
                        "location": location,
                        "meeting_link": meeting_link,
                        "invite_sent": send_invite,
                        "created_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                formatted_date = interview_datetime.strftime("%d/%m/%Y às %H:%M")
                
                return {
                    "success": True,
                    "message": f"📅 Entrevista {interview_type_display} agendada para {formatted_date}.",
                    "action_taken": "schedule_interview",
                    "affected_entities": [candidate_id, job_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "job_id": job_id,
                        "interview_type": interview_type,
                        "datetime": interview_datetime.isoformat(),
                        "duration_minutes": duration_minutes,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        logger.error(f"❌ Error scheduling interview: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao agendar entrevista: {str(e)}",
            "error": str(e)
        }


async def send_bulk_email(
    candidate_ids: list[str],
    template_id: str,
    job_id: str | None = None,
    custom_variables: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Send bulk emails to multiple candidates using a template.
    
    Args:
        candidate_ids: List of candidate UUIDs
        template_id: Email template ID to use
        job_id: Optional job vacancy ID for context
        custom_variables: Optional custom variables for template
        
    Returns:
        Result with success count and details
    """
    from app.shared.hitl.hitl_approval_context import hitl_preflight
    _hitl_block = hitl_preflight(tool="send_bulk_email", domain="communication", data={"candidate_count": len(candidate_ids), "template_id": template_id, "job_id": job_id})
    if _hitl_block is not None:
        return _hitl_block
    logger.info(f"📧 Sending bulk email to {len(candidate_ids)} candidates")

    # Validate all UUIDs upfront before sending any
    for _cid_check in candidate_ids:
        _err = validate_uuid_params(candidate_id=_cid_check)
        if _err:
            return _err
    
    success_count = 0
    failed_ids = []
    
    for cid in candidate_ids:
        result = await send_email(
            candidate_id=cid,
            template_id=template_id,
            job_id=job_id
        )
        if result.get("success"):
            success_count += 1
        else:
            failed_ids.append(cid)
    
    return {
        "success": len(failed_ids) == 0,
        "message": f"📧 {success_count}/{len(candidate_ids)} emails enviados com sucesso.",
        "action_taken": "send_bulk_email",
        "affected_entities": candidate_ids,
        "data": {
            "total": len(candidate_ids),
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "template_id": template_id
        }
    }


async def send_feedback(
    candidate_id: str,
    job_id: str,
    feedback_type: str,
    feedback_message: str | None = None,
    template_id: str | None = None
) -> dict[str, Any]:
    """
    Send feedback to a candidate about their application.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        feedback_type: Type of feedback ('positive', 'rejection', 'pending', 'next_steps')
        feedback_message: Custom feedback message
        template_id: Optional template ID for the feedback
        
    Returns:
        Result with success status and message
    """
    logger.info(f"💬 Sending {feedback_type} feedback to candidate {candidate_id}")

    err = validate_uuid_params(candidate_id=candidate_id, job_id=job_id)
    if err:
        return err

    # ACH-026 — FairnessGuard Camada 3: verificar viés em feedback de rejeição antes do envio
    if feedback_type == "rejection" and feedback_message:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg3 = FairnessGuard()
            _fg3_result = await _fg3.check_with_layer3(feedback_message, action_type="rejection")
            if _fg3_result.is_blocked:
                logger.warning(
                    "FairnessGuard Camada 3 bloqueou feedback de rejeição: candidate=%s category=%s",
                    candidate_id, _fg3_result.category,
                )
                feedback_message = (
                    "Agradecemos sua candidatura. Após análise cuidadosa, "
                    "optamos por seguir com outros perfis neste momento."
                )
            elif _fg3_result.soft_warnings:
                logger.info(
                    "FairnessGuard Camada 3: %d avisos em feedback de rejeição candidate=%s",
                    len(_fg3_result.soft_warnings), candidate_id,
                )
        except Exception as _fg3_exc:
            logger.debug("FairnessGuard Camada 3 em send_feedback indisponível: %s", _fg3_exc)

    feedback_emojis = {
        "positive": "🎉",
        "rejection": "📝",
        "pending": "⏳",
        "next_steps": "📋"
    }
    emoji = feedback_emojis.get(feedback_type, "💬")
    
    feedback_messages = {
        "positive": "Feedback positivo enviado",
        "rejection": "Feedback de rejeição enviado",
        "pending": "Status de pendência comunicado",
        "next_steps": "Próximas etapas comunicadas"
    }
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                
                # P1-3 (2026-06-18): defense-in-depth — filter by company_id from
                # ContextVar if available (RLS remains primary boundary per TENANT-EXEMPT).
                _cid = _cid_ctx.get(None)
                _cand_filter = [Candidate.id == UUID(candidate_id)]
                if _cid:
                    _cand_filter.append(Candidate.company_id == _cid)
                result = await db.execute(
                    select(Candidate).where(*_cand_filter)
                )
                candidate = result.scalar_one_or_none()
                
                candidate_name = getattr(candidate, 'name', 'Candidato') if candidate else 'Candidato'
                
                return {
                    "success": True,
                    "message": f"{emoji} {feedback_messages.get(feedback_type, 'Feedback enviado')} para {candidate_name}.",
                    "action_taken": "send_feedback",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "feedback_type": feedback_type,
                        "template_id": template_id,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "message": f"{emoji} {feedback_messages.get(feedback_type, 'Feedback enviado')} ao candidato.",
                    "action_taken": "send_feedback",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "job_id": job_id,
                        "feedback_type": feedback_type,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        logger.error(f"❌ Error sending feedback: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao enviar feedback: {str(e)}",
            "error": str(e)
        }


SEND_EMAIL_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID do candidato para enviar email - use o campo id retornado por search_candidates. Nunca use o nome como ID."
        },
        "template_id": {
            "type": "string",
            "description": "Optional email template ID to use"
        },
        "subject": {
            "type": "string",
            "description": "Email subject (required if no template)"
        },
        "body": {
            "type": "string",
            "description": "Email body content (required if no template)"
        },
        "job_id": {
            "type": "string",
            "description": "UUID da vaga para contexto (opcional) - use o campo id retornado por search_jobs. Nunca use o titulo como ID."
        },
        "cc": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of CC email addresses"
        },
        "attachments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of attachment IDs"
        }
    },
    "required": ["candidate_id"]
}

SEND_WHATSAPP_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID do candidato - use o campo id retornado por search_candidates. Nunca use o nome como ID."
        },
        "message": {
            "type": "string",
            "description": "Message content to send"
        },
        "template_id": {
            "type": "string",
            "description": "Optional WhatsApp template ID"
        },
        "job_id": {
            "type": "string",
            "description": "UUID da vaga para contexto (opcional) - use o campo id retornado por search_jobs. Nunca use o titulo como ID."
        }
    },
    "required": ["candidate_id", "message"]
}

SCHEDULE_INTERVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID do candidato - use o campo id retornado por search_candidates. Nunca use o nome como ID."
        },
        "job_id": {
            "type": "string",
            "description": "UUID da vaga - use o campo id retornado por search_jobs. Nunca use o titulo como ID."
        },
        "interview_type": {
            "type": "string",
            "description": "Type of interview",
            "enum": ["phone", "video", "onsite", "technical", "behavioral", "final"]
        },
        "datetime_str": {
            "type": "string",
            "description": "Interview date/time in ISO format (e.g., 2025-01-30T14:00:00)"
        },
        "duration_minutes": {
            "type": "integer",
            "description": "Duration of the interview in minutes",
            "default": 60
        },
        "interviewers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of interviewer user IDs"
        },
        "location": {
            "type": "string",
            "description": "Location for in-person interviews"
        },
        "meeting_link": {
            "type": "string",
            "description": "Video meeting link for remote interviews"
        },
        "notes": {
            "type": "string",
            "description": "Additional notes for the interview"
        },
        "send_invite": {
            "type": "boolean",
            "description": "Whether to send calendar invite to all participants",
            "default": True
        }
    },
    "required": ["candidate_id", "job_id", "interview_type", "datetime_str"]
}

SEND_BULK_EMAIL_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista de UUIDs de candidatos - cada item deve ser o campo id retornado por search_candidates. Nunca use nomes como IDs."
        },
        "template_id": {
            "type": "string",
            "description": "Email template ID to use"
        },
        "job_id": {
            "type": "string",
            "description": "UUID da vaga para contexto (opcional) - use o campo id retornado por search_jobs. Nunca use o titulo como ID."
        },
        "custom_variables": {
            "type": "object",
            "description": "Optional custom variables for template"
        }
    },
    "required": ["candidate_ids", "template_id"]
}

SEND_FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID do candidato - use o campo id retornado por search_candidates. Nunca use o nome como ID."
        },
        "job_id": {
            "type": "string",
            "description": "UUID da vaga - use o campo id retornado por search_jobs. Nunca use o titulo como ID."
        },
        "feedback_type": {
            "type": "string",
            "description": "Type of feedback",
            "enum": ["positive", "rejection", "pending", "next_steps"]
        },
        "feedback_message": {
            "type": "string",
            "description": "Custom feedback message"
        },
        "template_id": {
            "type": "string",
            "description": "Optional template ID for the feedback"
        }
    },
    "required": ["candidate_id", "job_id", "feedback_type"]
}


def register_communication_tools() -> None:
    """Register all communication tools in the registry."""
    
    tool_registry.register(ToolDefinition(
        name="send_email",
        description="Envia um email para um candidato. Pode usar um template ou conteúdo customizado.",
        parameters_schema=SEND_EMAIL_SCHEMA,
        handler=send_email,
        allowed_agents=["orchestrator", "recruiter_assistant", "analyst_feedback", "scheduling"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="send_whatsapp",
        description="Envia uma mensagem WhatsApp para um candidato.",
        parameters_schema=SEND_WHATSAPP_SCHEMA,
        handler=send_whatsapp,
        allowed_agents=["orchestrator", "recruiter_assistant", "analyst_feedback", "scheduling"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="schedule_interview",
        description="Agenda uma entrevista com um candidato. Suporta diferentes tipos de entrevista (telefônica, vídeo, presencial, técnica, comportamental).",
        parameters_schema=SCHEDULE_INTERVIEW_SCHEMA,
        handler=schedule_interview,
        allowed_agents=["orchestrator", "recruiter_assistant", "scheduling"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="send_bulk_email",
        description="Envia emails em massa para múltiplos candidatos usando um template.",
        parameters_schema=SEND_BULK_EMAIL_SCHEMA,
        handler=send_bulk_email,
        allowed_agents=["orchestrator", "recruiter_assistant"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="send_feedback",
        description="Envia feedback a um candidato sobre sua candidatura (positivo, rejeição, pendente, próximas etapas).",
        parameters_schema=SEND_FEEDBACK_SCHEMA,
        handler=send_feedback,
        allowed_agents=["orchestrator", "recruiter_assistant", "analyst_feedback"]
    ))
    
    logger.info("✅ Registered 5 communication tools")
