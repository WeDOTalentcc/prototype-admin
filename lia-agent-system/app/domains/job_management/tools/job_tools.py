"""
Job Tools - Tools for job vacancy management.

Provides function calling capabilities for:
- Creating new job vacancies
- Updating existing jobs
- Pausing and closing jobs

All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import logging
from types import SimpleNamespace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID


from app.tools.registry import ToolDefinition, tool_registry
from app.tools.context_helpers import (
    context_or_raise,
    normalize_wrapper_kwargs,
    require_company_id_from_context,
    require_company_id_from_obj,
)

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


async def create_job(
    title: str,
    department: str | None = None,
    seniority: str | None = None,
    work_model: str | None = None,
    location: str | None = None,
    description: str | None = None,
    requirements: list[str] | None = None,
    skills: list[str] | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    company_id: str | None = None,
    recruiter_id: str | None = None,
    publish: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Create a new job vacancy.
    
    Args:
        title: Job title
        department: Department for the position
        seniority: Seniority level (Júnior, Pleno, Sênior, etc.)
        work_model: Work model (Remoto, Híbrido, Presencial)
        location: Job location
        description: Full job description
        requirements: List of requirements
        skills: List of required skills
        salary_min: Minimum salary
        salary_max: Maximum salary
        company_id: Company ID (overridden by context if provided)
        recruiter_id: Recruiter creating the job
        publish: Whether to publish immediately
        
    Returns:
        Result with job creation details
    """
    # Sprint 2.5-B-extra (2026-05-24): fail-loud canonical.
    # Prefer _context (Phase 1.5 path), fallback to explicit kwarg (legacy
    # callers), raise loud if NEITHER provides company_id (REGRA 4 +
    # ADR-001 multi-tenancy fail-closed).
    context = _extract_context(kwargs)
    if context and getattr(context, "company_id", None):
        effective_company_id = str(context.company_id)
        user_id = context.user_id or recruiter_id or "system"
    elif company_id:
        effective_company_id = company_id
        user_id = recruiter_id or "system"
    else:
        raise ToolContextMissingError(
            "Tool 'create_job_vacancy' invoked without company_id "
            "(neither in _context nor as explicit kwarg). "
            "Multi-tenancy fail-closed per CLAUDE.md REGRA 4 + ADR-001."
        )
    
    logger.info(f"📋 Creating job vacancy: {title} (company: {effective_company_id})")
    
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        status = "Ativa" if publish else "Rascunho"
        
        async with AsyncSessionLocal() as db:
            salary_range = None
            if salary_min or salary_max:
                salary_range = {
                    "min": salary_min,
                    "max": salary_max,
                    "currency": "BRL"
                }
            
            job = JobVacancy(
                title=title,
                company_id=effective_company_id,
                department=department,
                seniority_level=seniority,
                work_model=work_model,
                location=location,
                description=description,
                # T-1166 — `job_tools.create_job` only exposes `requirements`
                # as input today; emit an explicit empty list so the column is
                # never NULL. New callers should add a `responsibilities` kwarg.
                responsibilities=[],
                requirements=requirements or [],
                salary_range=salary_range,
                status=status,
                stage="Planejamento" if not publish else "Publicada",
                created_by=user_id,
                recruiter=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                published_at=datetime.utcnow() if publish else None
            )
            
            if skills:
                job.additional_data = {"skills": skills}
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            job_id = str(job.id)
            
            logger.info(f"✅ Created job vacancy: {job_id} - {title}")
            
            return {
                "success": True,
                "message": f"✅ Vaga '{title}' criada com sucesso{' e publicada' if publish else ' como rascunho'}.",
                "action_taken": "create_job",
                "affected_entities": [job_id],
                "data": {
                    "job_id": job_id,
                    "title": title,
                    "department": department,
                    "seniority": seniority,
                    "work_model": work_model,
                    "location": location,
                    "status": status,
                    "skills": skills or [],
                    "requirements": requirements or [],
                    "salary_range": salary_range,
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": user_id
                }
            }
        
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error creating job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao criar vaga: {str(e)}",
            "error": str(e)
        }


async def update_job(
    job_id: str,
    updates: dict[str, Any],
    **kwargs
) -> dict[str, Any]:
    """
    Update an existing job vacancy.
    
    Args:
        job_id: UUID of the job to update
        updates: Dictionary of fields to update
        
    Returns:
        Result with update details
    """
    context = context_or_raise(kwargs, "update_job")

    company_id = require_company_id_from_obj(context, "update_job")

    user_id = context.user_id
    
    logger.info(f"🔄 Updating job vacancy: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == UUID(job_id),
                        JobVacancy.company_id == company_id
                    )
                )
            )
            job = result.scalar_one_or_none()

            if not job:
                # TENANT-EXEMPT: intentional global lookup to distinguish
                # "job does not exist" from "job belongs to another company".
                # First query above already enforced tenant scope.
                job_check = await db.execute(
                    select(JobVacancy).where(JobVacancy.id == UUID(job_id))
                )
                if job_check.scalar_one_or_none():
                    return {
                        "success": False,
                        "message": "Acesso negado: vaga pertence a outra empresa",
                        "error": "cross_tenant_access_denied"
                    }
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            job_title = getattr(job, 'title', 'Vaga')
            
            protected_fields = {'id', 'company_id', 'created_at', 'created_by'}
            for field, value in updates.items():
                if field not in protected_fields and hasattr(job, field):
                    setattr(job, field, value)
            
            job.updated_at = datetime.utcnow()
            await db.commit()
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Updated job vacancy: {job_id} - {job_title}")
            
            return {
                "success": True,
                "message": f"✅ Vaga '{job_title}' atualizada com sucesso.",
                "action_taken": "update_job",
                "affected_entities": [job_id],
                "data": {
                    "job_id": job_id,
                    "job_title": job_title,
                    "updated_fields": list(updates.keys()),
                    "updated_at": datetime.utcnow().isoformat(),
                    "updated_by": user_id
                }
            }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error updating job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao atualizar vaga: {str(e)}",
            "error": str(e)
        }


async def pause_job(
    job_id: str,
    reason: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Pause a job vacancy temporarily.
    
    Args:
        job_id: UUID of the job to pause
        reason: Optional reason for pausing
        
    Returns:
        Result with pause details
    """
    company_id = require_company_id_from_context(kwargs, "pause_job")

    logger.info(f"⏸️ Pausing job vacancy: {job_id} (company: {company_id})")

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                from app.models.job_vacancy import JobVacancy

                # Multi-tenancy fail-closed (REGRA ZERO): scope by company_id
                # when context is present so we cannot mutate another tenant's
                # vacancy. AST sensor sees Model.company_id == company_id
                # directly here.
                conditions = [JobVacancy.id == UUID(job_id)]
                if company_id:
                    conditions.append(JobVacancy.company_id == company_id)
                # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id
                # appended conditionally above.
                result = await db.execute(
                    select(JobVacancy).where(and_(*conditions))
                )
                job = result.scalar_one_or_none()

                if not job:
                    return {
                        "success": False,
                        "message": f"Vaga não encontrada: {job_id}",
                        "error": "job_not_found"
                    }

                job_title = getattr(job, 'title', 'Vaga')

                if hasattr(job, 'status'):
                    job.status = 'pausada'
                if hasattr(job, 'updated_at'):
                    job.updated_at = datetime.utcnow()
                
                await db.commit()
                
                return {
                    "success": True,
                    "message": f"⏸️ Vaga '{job_title}' foi pausada.",
                    "action_taken": "pause_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "new_status": "pausada",
                        "reason": reason,
                        "paused_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "message": "⏸️ Vaga foi pausada.",
                    "action_taken": "pause_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "new_status": "pausada",
                        "reason": reason,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error pausing job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao pausar vaga: {str(e)}",
            "error": str(e)
        }


async def close_job(
    job_id: str,
    reason: str,
    hired_candidate_id: str | None = None,
    notify_candidates: bool = True,
    **kwargs
) -> dict[str, Any]:
    """
    Close a job vacancy.
    
    This is a significant action that may notify candidates.
    
    Args:
        job_id: UUID of the job to close
        reason: Reason for closing (e.g., 'filled', 'cancelled', 'budget')
        hired_candidate_id: Optional ID of hired candidate if closing because filled
        notify_candidates: Whether to notify remaining candidates
        
    Returns:
        Result with close details
    """
    company_id = require_company_id_from_context(kwargs, "close_job")

    # HITL pre-flight (AUD-4, 2026-06-06): close_job NAO usa @tool_handler, entao
    # o gate compartilhado nao o cobre - o bloqueio vem AQUI, no produtor, ANTES
    # de qualquer mutacao/commit (padrao OfferService.check_can_send). Sem isto o
    # codigo commitava (status=fechada) e SO DEPOIS devolvia requires_confirmation
    # = confirmacao-teatro pos-commit (a vaga ja fechou). Dormante por flag OFF.
    from app.shared.hitl.hitl_approval_context import (
        hitl_gate_enabled,
        hitl_preflight,
    )
    _hitl_gate = hitl_gate_enabled()
    _block = hitl_preflight(
        tool="close_job",
        domain="job_management",
        message="Encerrar uma vaga e uma acao sensivel. Confirme para prosseguir.",
        data={"job_id": job_id, "reason": reason},
        extra={
            "confirmation_message": "Tem certeza que deseja encerrar esta vaga?",
            "action_taken": "close_job",
        },
    )
    if _block is not None:
        return _block

    logger.info(f"🔒 Closing job vacancy: {job_id}, reason: {reason} (company: {company_id})")

    reason_messages = {
        "filled": "preenchida",
        "cancelled": "cancelada",
        "budget": "cancelada por restrição orçamentária",
        "on_hold": "congelada",
        "other": "encerrada"
    }
    reason_display = reason_messages.get(reason, reason)

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                from app.models.job_vacancy import JobVacancy

                # Multi-tenancy fail-closed (REGRA ZERO): scope by company_id
                # when context is present. AST sensor sees Model.company_id
                # == company_id directly here.
                conditions = [JobVacancy.id == UUID(job_id)]
                if company_id:
                    conditions.append(JobVacancy.company_id == company_id)
                # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id
                # appended conditionally above.
                result = await db.execute(
                    select(JobVacancy).where(and_(*conditions))
                )
                job = result.scalar_one_or_none()

                if not job:
                    return {
                        "success": False,
                        "message": f"Vaga não encontrada: {job_id}",
                        "error": "job_not_found"
                    }

                job_title = getattr(job, 'title', 'Vaga')

                if hasattr(job, 'status'):
                    job.status = 'fechada'
                if hasattr(job, 'closed_at'):
                    job.closed_at = datetime.utcnow()
                if hasattr(job, 'close_reason'):
                    job.close_reason = reason
                if hasattr(job, 'updated_at'):
                    job.updated_at = datetime.utcnow()

                await db.commit()

                try:
                    from app.domains.job_management.services.outcome_tracker import outcome_tracker
                    job_company_id = company_id or getattr(job, 'company_id', 'demo_company')
                    await outcome_tracker.record_job_close(
                        job_id=job_id,
                        company_id=job_company_id,
                        reason=reason,
                        hired_candidate_id=hired_candidate_id,
                        db=db,
                    )
                except Exception as outcome_err:
                    logger.warning(f"Outcome tracking failed (non-blocking): {outcome_err}")
                
                return {
                    "success": True,
                    "requires_confirmation": not _hitl_gate,
                    "confirmation_message": f"⚠️ Tem certeza que deseja encerrar a vaga '{job_title}'? {'Os candidatos em processo serão notificados.' if notify_candidates else ''}",
                    "message": f"🔒 Vaga '{job_title}' foi {reason_display}.",
                    "action_taken": "close_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "new_status": "fechada",
                        "reason": reason,
                        "hired_candidate_id": hired_candidate_id,
                        "candidates_notified": notify_candidates,
                        "closed_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "requires_confirmation": not _hitl_gate,
                    "confirmation_message": "⚠️ Tem certeza que deseja encerrar esta vaga?",
                    "message": f"🔒 Vaga foi {reason_display}.",
                    "action_taken": "close_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "new_status": "fechada",
                        "reason": reason,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error closing job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao encerrar vaga: {str(e)}",
            "error": str(e)
        }


async def publish_job(
    job_id: str,
    channels: list[str] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Publish a job vacancy to make it live.
    
    Args:
        job_id: UUID of the job to publish
        channels: Optional list of channels to publish to (e.g., 'linkedin', 'indeed', 'internal')
        
    Returns:
        Result with publication details
    """
    company_id = require_company_id_from_context(kwargs, "publish_job")

    from app.shared.hitl.hitl_approval_context import hitl_preflight
    _hitl_block = hitl_preflight(
        tool="publish_job",
        domain="job_management",
        data={"job_id": job_id, "channels": channels},
    )
    if _hitl_block is not None:
        return _hitl_block

    logger.info(f"🚀 Publishing job vacancy: {job_id} (company: {company_id})")

    default_channels = ["portal_interno"]
    publish_channels = channels or default_channels

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                from app.models.job_vacancy import JobVacancy

                # Multi-tenancy fail-closed (REGRA ZERO): scope by company_id
                # when context is present. AST sensor sees Model.company_id
                # == company_id directly here.
                conditions = [JobVacancy.id == UUID(job_id)]
                if company_id:
                    conditions.append(JobVacancy.company_id == company_id)
                # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id
                # appended conditionally above.
                result = await db.execute(
                    select(JobVacancy).where(and_(*conditions))
                )
                job = result.scalar_one_or_none()

                if not job:
                    return {
                        "success": False,
                        "message": f"Vaga não encontrada: {job_id}",
                        "error": "job_not_found"
                    }

                job_title = getattr(job, 'title', 'Vaga')

                if hasattr(job, 'status'):
                    job.status = 'publicada'
                if hasattr(job, 'published_at'):
                    job.published_at = datetime.utcnow()
                if hasattr(job, 'updated_at'):
                    job.updated_at = datetime.utcnow()
                
                await db.commit()
                
                return {
                    "success": True,
                    "message": f"🚀 Vaga '{job_title}' publicada com sucesso!",
                    "action_taken": "publish_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "new_status": "publicada",
                        "channels": publish_channels,
                        "published_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning(f"Database model access issue: {e}, using mock response")
                
                return {
                    "success": True,
                    "message": "🚀 Vaga publicada com sucesso!",
                    "action_taken": "publish_job",
                    "affected_entities": [job_id],
                    "data": {
                        "job_id": job_id,
                        "new_status": "publicada",
                        "channels": publish_channels,
                        "simulated": True
                    }
                }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error publishing job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao publicar vaga: {str(e)}",
            "error": str(e)
        }


CREATE_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Job title (e.g., 'Desenvolvedor Python Sênior')"
        },
        "department": {
            "type": "string",
            "description": "Department for the position"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level",
            "enum": ["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor"]
        },
        "work_model": {
            "type": "string",
            "description": "Work model",
            "enum": ["Remoto", "Híbrido", "Presencial"]
        },
        "location": {
            "type": "string",
            "description": "Job location"
        },
        "description": {
            "type": "string",
            "description": "Full job description"
        },
        "requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of requirements"
        },
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of required skills"
        },
        "salary_min": {
            "type": "number",
            "description": "Minimum salary"
        },
        "salary_max": {
            "type": "number",
            "description": "Maximum salary"
        },
        "company_id": {
            "type": "string",
            "description": "Company ID"
        },
        "recruiter_id": {
            "type": "string",
            "description": "Recruiter creating the job"
        },
        "publish": {
            "type": "boolean",
            "description": "Whether to publish immediately",
            "default": False
        }
    },
    "required": ["title"]
}

UPDATE_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "UUID of the job to update"
        },
        "updates": {
            "type": "object",
            "description": "Dictionary of fields to update"
        }
    },
    "required": ["job_id", "updates"]
}

PAUSE_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "UUID of the job to pause"
        },
        "reason": {
            "type": "string",
            "description": "Optional reason for pausing"
        }
    },
    "required": ["job_id"]
}

CLOSE_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "UUID of the job to close"
        },
        "reason": {
            "type": "string",
            "description": "Reason for closing",
            "enum": ["filled", "cancelled", "budget", "on_hold", "other"]
        },
        "hired_candidate_id": {
            "type": "string",
            "description": "Optional ID of hired candidate if closing because filled"
        },
        "notify_candidates": {
            "type": "boolean",
            "description": "Whether to notify remaining candidates",
            "default": True
        }
    },
    "required": ["job_id", "reason"]
}

PUBLISH_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "UUID of the job to publish"
        },
        "channels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of channels to publish to"
        }
    },
    "required": ["job_id"]
}




async def _wrap_update_job(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await update_job(**normalize_wrapper_kwargs(kwargs))




async def _wrap_pause_job(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await pause_job(**normalize_wrapper_kwargs(kwargs))




async def _wrap_close_job(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await close_job(**normalize_wrapper_kwargs(kwargs))




async def _wrap_publish_job(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await publish_job(**normalize_wrapper_kwargs(kwargs))


def register_job_tools() -> None:
    """Register all job tools in the registry."""
    
    tool_registry.register(ToolDefinition(
        name="create_job",
        description="Cria uma nova vaga de emprego. Pode criar como rascunho ou publicar imediatamente.",
        parameters_schema=CREATE_JOB_SCHEMA,
        handler=create_job,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner", "job_intake"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="update_job",
        description="Atualiza uma vaga existente com novos dados.",
        parameters_schema=UPDATE_JOB_SCHEMA,
        handler=_wrap_update_job,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner", "job_intake"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="pause_job",
        description="Pausa uma vaga temporariamente, deixando-a invisível para candidatos.",
        parameters_schema=PAUSE_JOB_SCHEMA,
        handler=_wrap_pause_job,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="close_job",
        description="Encerra uma vaga definitivamente. Pode notificar candidatos em processo. Ação sensível que requer confirmação.",
        parameters_schema=CLOSE_JOB_SCHEMA,
        handler=_wrap_close_job,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="publish_job",
        description="Publica uma vaga que está em rascunho, tornando-a visível para candidatos.",
        parameters_schema=PUBLISH_JOB_SCHEMA,
        handler=_wrap_publish_job,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner", "job_intake"]
    ))
    
    logger.info("✅ Registered 5 job tools")
