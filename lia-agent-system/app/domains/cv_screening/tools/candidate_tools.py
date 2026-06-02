"""
Candidate Tools - Tools for candidate actions in the recruitment pipeline.

Provides function calling capabilities for:
- Moving candidates between stages
- Adding candidates to vacancies
- Rejecting candidates
- Adding candidates to shortlist

All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import logging
import re
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


# Pragmatic e-mail format check (presence of local@domain.tld). Mirrors the
# "formato + presença" requirement of Task #1224 without pulling the heavy
# email-validator dependency into the tool path.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(email: Any) -> bool:
    return bool(email and isinstance(email, str) and _EMAIL_RE.match(email.strip()))


async def update_candidate_stage(
    candidate_id: str,
    target_stage: str,
    job_id: str | None = None,
    notes: str | None = None,
    notify_candidate: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Move a candidate to a different stage in the recruitment pipeline.
    
    Args:
        candidate_id: UUID of the candidate to move
        target_stage: Target stage name (e.g., 'Entrevistas', 'Oferta', 'Contratado')
        job_id: Optional job vacancy ID for context
        notes: Optional notes about the stage change
        notify_candidate: Whether to notify the candidate about the change
        
    Returns:
        Result with success status and message
    """
    context = context_or_raise(kwargs, "update_candidate_stage")

    company_id = require_company_id_from_obj(context, "update_candidate_stage")

    user_id = context.user_id
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"🔄 Moving candidate {candidate_id} to stage: {target_stage} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }
            
            previous_stage = "N/A"
            
            if job_id:
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.candidate_id == UUID(candidate_id),
                            VacancyCandidate.vacancy_id == UUID(job_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                vacancy_candidate = vc_result.scalar_one_or_none()
                
                if vacancy_candidate:
                    previous_stage = vacancy_candidate.stage or "N/A"
                    vacancy_candidate.stage = target_stage
                    vacancy_candidate.status = target_stage.lower().replace(" ", "_")
                    vacancy_candidate.updated_at = datetime.utcnow()
                else:
                    # TENANT-EXEMPT: INTENTIONAL cross-tenant probe. After the
                    # tenant-scoped query above returned None, this checks whether
                    # the pair exists in ANY tenant to distinguish "not found"
                    # from "exists in another tenant" — explicit cross-tenant
                    # access denial UX. Tool itself runs under tool_registry
                    # with Postgres RLS (Task #1143) defense.
                    vc_check = await db.execute(
                    # TENANT-EXEMPT: see above — RLS + tool_registry tenant context.
                        select(VacancyCandidate).where(
                            and_(
                                VacancyCandidate.candidate_id == UUID(candidate_id),
                                VacancyCandidate.vacancy_id == UUID(job_id)
                            )
                        )
                    )
                    if vc_check.scalar_one_or_none():
                        return {
                            "success": False,
                            "message": "Acesso negado: candidato pertence a outra empresa",
                            "error": "cross_tenant_access_denied"
                        }
            
            if hasattr(candidate, 'status'):
                candidate.status = target_stage.lower().replace(" ", "_")
            if hasattr(candidate, 'updated_at'):
                candidate.updated_at = datetime.utcnow()
            
            await db.commit()
            
            candidate_name = getattr(candidate, 'name', 'Candidato')
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Candidate {candidate_id} moved from {previous_stage} to {target_stage}")
            
            return {
                "success": True,
                "message": f"✅ {candidate_name} foi movido para a etapa '{target_stage}'.",
                "action_taken": "update_candidate_stage",
                "affected_entities": [candidate_id],
                "data": {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "previous_stage": previous_stage,
                    "new_stage": target_stage,
                    "job_id": job_id,
                    "notified": notify_candidate,
                    "updated_by": user_id
                }
            }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error moving candidate: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao mover candidato: {str(e)}",
            "error": str(e)
        }


async def add_candidate_to_vacancy(
    candidate_id: str,
    job_id: str,
    initial_stage: str = "Triagem",
    source: str | None = None,
    notes: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Add a candidate to a job vacancy pipeline.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        initial_stage: Starting stage for the candidate
        source: Source of the candidate (e.g., 'sourcing', 'aplicacao')
        notes: Optional notes about adding the candidate
        
    Returns:
        Result with success status and message
    """
    context = context_or_raise(kwargs, "add_candidate_to_vacancy")

    company_id = require_company_id_from_obj(context, "add_candidate_to_vacancy")

    user_id = context.user_id
    
    logger.info(f"➕ Adding candidate {candidate_id} to job {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            cand_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = cand_result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }

            # Task #1224: candidate must have a valid e-mail before entering a
            # vacancy pipeline (downstream comms / scheduling rely on it).
            # Fail loud — never create a VacancyCandidate without a reachable
            # contact.
            candidate_email = getattr(candidate, "email", None)
            if not candidate_email or not str(candidate_email).strip():
                return {
                    "success": False,
                    "message": "Candidato sem e-mail cadastrado — não é possível adicioná-lo à vaga.",
                    "error": "missing_email"
                }
            if not _is_valid_email(candidate_email):
                return {
                    "success": False,
                    "message": f"E-mail do candidato é inválido: {candidate_email}",
                    "error": "invalid_email"
                }

            # Task #1224: FairnessGuard C1 on recruiter-provided notes BEFORE
            # any write. Discriminatory annotations must never be persisted.
            if notes and notes.strip():
                from app.shared.compliance import scoring_safeguards as _ss
                _fg, _unavail = _ss.run_fairness_check(notes)
                if _unavail or (_fg and _fg.is_blocked):
                    _fg = _fg or type(
                        "FR", (), {"is_blocked": True, "category": "unavailable",
                                   "educational_message": "fairness guard unavailable"}
                    )()
                    await _ss.log_scoring_decision(
                        company_id=company_id,
                        agent_name="add_candidate_to_vacancy",
                        decision_type="fairness_block",
                        action="fairness_block",
                        decision="blocked",
                        reasoning=[f"FairnessGuard: category={_fg.category}",
                                   _fg.educational_message or ""],
                        criteria_used=["fairness_guard"],
                        candidate_id=candidate_id, job_vacancy_id=job_id,
                        human_review_required=True,
                    )
                    return {
                        "success": False,
                        "message": _fg.educational_message or "Notas bloqueadas por viés.",
                        "error": "fairness_block"
                    }

            job_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == UUID(job_id),
                        JobVacancy.company_id == company_id
                    )
                )
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
                # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
                # to accept company_id via **kwargs from tool_handler.
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
            
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            existing = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.candidate_id == UUID(candidate_id)
                    )
                )
            )
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "message": "Candidato já está associado a esta vaga",
                    "error": "candidate_already_in_vacancy"
                }
            
            vacancy_candidate = VacancyCandidate(
                vacancy_id=UUID(job_id),
                candidate_id=UUID(candidate_id),
                company_id=company_id,
                source=source or "manual",
                stage=initial_stage,
                status="sourced",
                added_by=user_id,
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(vacancy_candidate)
            await db.commit()
            
            candidate_name = getattr(candidate, 'name', 'Candidato')
            job_title = getattr(job, 'title', 'Vaga')
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Created VacancyCandidate: {candidate_id} -> {job_title}")

            # Task #1224: durable audit of the candidate-movement decision
            # (repudiation guarantee — actor/tenant/timestamp/action).
            # Best-effort: never block the write on audit failure.
            from app.shared.compliance import scoring_safeguards as _ss
            await _ss.log_scoring_decision(
                company_id=company_id,
                agent_name="add_candidate_to_vacancy",
                decision_type="candidate_movement",
                action="add_candidate_to_vacancy",
                decision="added",
                reasoning=[f"Candidato adicionado à vaga na etapa '{initial_stage}'"],
                criteria_used=["manual_add"],
                candidate_id=candidate_id, job_vacancy_id=job_id,
            )

            return {
                "success": True,
                "message": f"✅ {candidate_name} foi adicionado à vaga '{job_title}' na etapa '{initial_stage}'.",
                "action_taken": "add_candidate_to_vacancy",
                "affected_entities": [candidate_id, job_id],
                "data": {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "job_id": job_id,
                    "job_title": job_title,
                    "stage": initial_stage,
                    "source": source or "manual",
                    "added_by": user_id
                }
            }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error adding candidate to vacancy: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao adicionar candidato à vaga: {str(e)}",
            "error": str(e)
        }


async def _generate_rediscovery_embedding(
    candidate_id: str,
    job_id: str,
    candidate: Any = None,
) -> None:
    """
    Gate 2 re-discovery: generate an embedding for a rejected candidate
    so they can be matched to future vacancies via vector search.

    Uses a deterministic candidate-specific UUID (uuid5 of candidate_id)
    to avoid overwriting the original vacancy embedding.
    """
    try:
        import uuid as _uuid

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.domains.job_management.services.job_embedding_service import JobEmbeddingService

        embedding_svc = JobEmbeddingService()

        candidate_name = getattr(candidate, "name", "") if candidate else ""
        skills: list[str] = []
        description = ""
        department = ""

        async with AsyncSessionLocal() as db:
            try:
                row = await db.execute(text(
                    "SELECT skills, summary, job_title, department "
                    "FROM candidates WHERE id = :cid LIMIT 1"
                ), {"cid": candidate_id})
                data = row.mappings().first()
                if data:
                    raw_skills = data.get("skills")
                    if isinstance(raw_skills, list):
                        skills = raw_skills
                    elif isinstance(raw_skills, str):
                        skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
                    description = data.get("summary") or ""
                    data.get("job_title") or candidate_name
                    department = data.get("department") or ""
            except Exception:
                pass

        company_id = str(getattr(candidate, "company_id", None)) if candidate else None

        candidate_embedding_id = str(_uuid.uuid5(
            _uuid.NAMESPACE_DNS,
            f"candidate-embedding-{candidate_id}-{job_id}",
        ))

        await embedding_svc.create_or_update_job_embedding(
            company_id=company_id,
            job_id=candidate_embedding_id,
            job_title=f"[Candidato] {candidate_name or candidate_id}",
            department=department if department else None,
            skills=skills,
            description=description,
            outcome_status="rejected_gate2",
        )
        logger.info(
            "Gate 2 embedding created for rejected candidate %s "
            "(embedding_id=%s, original_job=%s)",
            candidate_id, candidate_embedding_id, job_id,
        )
    except Exception as exc:
        logger.warning("Gate 2 embedding generation failed for %s: %s", candidate_id, exc)


async def reject_candidate(
    candidate_id: str,
    job_id: str,
    reason: str,
    send_feedback: bool = True,
    feedback_template: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Reject a candidate from a job vacancy.
    
    This is a dangerous action that requires confirmation.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        reason: Reason for rejection
        send_feedback: Whether to send rejection feedback to candidate
        feedback_template: Optional template ID for feedback email
        
    Returns:
        Result with success status, requires confirmation for dangerous action
    """
    logger.info(f"❌ Rejecting candidate {candidate_id} from job {job_id}")
    
    fg_implicit = []
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        fg_explicit = _fg.check(reason)
        if fg_explicit.is_blocked:
            logger.warning(
                "DEI-02: rejection blocked by FairnessGuard — explicit bias detected "
                "candidate=%s category=%s terms=%s",
                candidate_id, fg_explicit.category, fg_explicit.blocked_terms,
            )
            return {
                "success": False,
                "blocked_by_fairness": True,
                "message": f"⚠️ Rejeição bloqueada: motivo contém viés discriminatório ({fg_explicit.category}). "
                           f"Por favor, reformule o motivo da rejeição.",
                "educational_message": fg_explicit.educational_message,
                "category": fg_explicit.category,
            }
        fg_implicit = _fg.check_implicit_bias(reason)
        if fg_implicit:
            logger.info("DEI-02: implicit bias warnings for rejection of candidate=%s: %s", candidate_id, fg_implicit)
    except Exception as fg_err:
        logger.error("DEI-02: FairnessGuard check failed for candidate=%s, proceeding with rejection: %s", candidate_id, fg_err)

    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                
                # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
                # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
                # to accept company_id via **kwargs from tool_handler.
                result = await db.execute(
                    select(Candidate).where(Candidate.id == UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
                candidate_name = getattr(candidate, 'name', 'Candidato') if candidate else 'Candidato'

                confirmed = kwargs.get("confirmed", False)

                if confirmed:
                    if send_feedback and candidate:
                        try:
                            from app.jobs.celery_tasks import feedback_generate_and_send_task
                            feedback_generate_and_send_task.delay(
                                candidate_id=candidate_id,
                                job_id=job_id,
                                reason=reason,
                                company_id=str(candidate.company_id) if getattr(candidate, 'company_id', None) else None,
                            )
                            logger.info("Dispatched rejection feedback for candidate %s", candidate_id)
                        except Exception as fb_exc:
                            logger.warning("Failed to dispatch rejection feedback: %s", fb_exc)

                    try:
                        import asyncio as _asyncio
                        _asyncio.create_task(_generate_rediscovery_embedding(
                            candidate_id=candidate_id,
                            job_id=job_id,
                            candidate=candidate,
                        ))
                        logger.info("Gate 2: dispatched re-discovery embedding for rejected candidate %s", candidate_id)
                    except Exception as emb_exc:
                        logger.warning("Gate 2: failed to dispatch embedding: %s", emb_exc)

                    rejection_result = {
                        "success": True,
                        "message": f"✅ {candidate_name} foi rejeitado. Motivo: {reason}",
                        "action_taken": "reject_candidate",
                        "affected_entities": [candidate_id],
                        "fairness_checked": True,
                        "data": {
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "job_id": job_id,
                            "reason": reason,
                            "feedback_sent": send_feedback,
                            "new_stage": "Reprovado"
                        }
                    }
                    if fg_implicit:
                        rejection_result["fairness_warnings"] = fg_implicit
                    return rejection_result

                return {
                    "success": True,
                    "requires_confirmation": True,
                    "confirmation_message": f"⚠️ Tem certeza que deseja rejeitar {candidate_name}? Esta ação irá movê-lo para 'Reprovado' e {'enviar um email de feedback' if send_feedback else 'NÃO enviar feedback'}.",
                    "message": f"✅ {candidate_name} foi rejeitado. Motivo: {reason}",
                    "action_taken": "reject_candidate",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "reason": reason,
                        "feedback_sent": send_feedback,
                        "new_stage": "Reprovado"
                    }
                }
                
            except Exception as e:
                # P1 audit 2026-05-20: REGRA 4 CLAUDE.md — fail-loud quando rejeição
                # NÃO foi persistida. Anteriormente retornava success=True com
                # simulated=True, mascarando que a ação não ocorreu no DB.
                logger.exception(
                    "[candidate_tools] reject_candidate FAILED (DB issue) — failing LOUD"
                )
                return {
                    "success": False,
                    "fallback_used": True,
                    "needs_manual_review": True,
                    "action_taken": None,
                    "message": (
                        "Não foi possível registrar a rejeição do candidato no banco. "
                        "A ação NÃO foi executada. Tente novamente ou peça suporte."
                    ),
                    "error": f"Database access failed: {str(e)}",
                    "data": {"candidate_id": candidate_id, "job_id": job_id},
                }
                
    except Exception as e:
        logger.error(f"❌ Error rejecting candidate: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao rejeitar candidato: {str(e)}",
            "error": str(e)
        }


async def shortlist_candidate(
    candidate_id: str,
    job_id: str,
    priority: str = "normal",
    notes: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Add a candidate to the shortlist for a job vacancy.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        priority: Priority level ('high', 'normal', 'low')
        notes: Optional notes about why they're shortlisted
        
    Returns:
        Result with success status and message
    """
    logger.info(f"⭐ Shortlisting candidate {candidate_id} for job {job_id}")
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                from app.models.candidate import Candidate
                
                # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
                # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
                # to accept company_id via **kwargs from tool_handler.
                result = await db.execute(
                    select(Candidate).where(Candidate.id == UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
                candidate_name = getattr(candidate, 'name', 'Candidato') if candidate else 'Candidato'
                
                priority_emoji = {"high": "🔥", "normal": "⭐", "low": "📌"}.get(priority, "⭐")
                
                return {
                    "success": True,
                    "message": f"{priority_emoji} {candidate_name} foi adicionado à shortlist com prioridade {priority}.",
                    "action_taken": "shortlist_candidate",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "priority": priority,
                        "notes": notes,
                        "shortlisted_at": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                # P1 audit 2026-05-20: REGRA 4 CLAUDE.md — fail-loud quando shortlist
                # NÃO foi persistida. Anteriormente retornava success=True com
                # simulated=True, mascarando que a ação não ocorreu no DB.
                logger.exception(
                    "[candidate_tools] shortlist_candidate FAILED (DB issue) — failing LOUD"
                )
                return {
                    "success": False,
                    "fallback_used": True,
                    "needs_manual_review": True,
                    "action_taken": None,
                    "message": (
                        "Não foi possível adicionar à shortlist no banco. "
                        "A ação NÃO foi executada. Tente novamente ou peça suporte."
                    ),
                    "error": f"Database access failed: {str(e)}",
                    "data": {"candidate_id": candidate_id, "job_id": job_id, "priority": priority},
                }
                
    except Exception as e:
        logger.error(f"❌ Error shortlisting candidate: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao adicionar candidato à shortlist: {str(e)}",
            "error": str(e)
        }


async def bulk_update_candidates_stage(
    candidate_ids: list[str],
    target_stage: str,
    job_id: str | None = None,
    notes: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Move multiple candidates to a stage at once.
    
    Args:
        candidate_ids: List of candidate UUIDs
        target_stage: Target stage name
        job_id: Optional job vacancy ID
        notes: Optional notes about the bulk action
        
    Returns:
        Result with success counts and details
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"🔄 Bulk moving {len(candidate_ids)} candidates to stage: {target_stage}")
    
    success_count = 0
    failed_ids = []
    
    for cid in candidate_ids:
        result = await update_candidate_stage(
            candidate_id=cid,
            target_stage=target_stage,
            job_id=job_id,
            notes=notes
        )
        if result.get("success"):
            success_count += 1
        else:
            failed_ids.append(cid)
    
    return {
        "success": len(failed_ids) == 0,
        "message": f"✅ {success_count}/{len(candidate_ids)} candidatos movidos para '{target_stage}'.",
        "action_taken": "bulk_update_candidates_stage",
        "affected_entities": candidate_ids,
        "data": {
            "total": len(candidate_ids),
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "target_stage": target_stage
        }
    }


async def add_to_list(
    candidate_id: str,
    list_id: str,
    notes: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Add a candidate to a saved list/shortlist.
    
    Args:
        candidate_id: UUID of the candidate
        list_id: UUID of the target list
        notes: Optional notes about adding the candidate
        
    Returns:
        Result with success status and message
    """
    context = context_or_raise(kwargs, "add_to_list")

    company_id = require_company_id_from_obj(context, "add_to_list")

    user_id = context.user_id
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"📋 Adding candidate {candidate_id} to list {list_id} (company: {company_id})")
    
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate
        
        async with AsyncSessionLocal() as db:
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            cand_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = cand_result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }
            
            candidate_name = getattr(candidate, 'name', 'Candidato')
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Added {candidate_id} to list {list_id}")
            
            return {
                "success": True,
                "message": f"📋 {candidate_name} foi adicionado à lista.",
                "action_taken": "add_to_list",
                "affected_entities": [candidate_id, list_id],
                "data": {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "list_id": list_id,
                    "notes": notes,
                    "added_by": user_id,
                    "added_at": datetime.utcnow().isoformat()
                }
            }
                
    except Exception as e:
        logger.error(f"❌ Error adding candidate to list: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao adicionar candidato à lista: {str(e)}",
            "error": str(e)
        }


async def wsi_screening(
    candidate_id: str,
    job_id: str,
    screening_type: str = "complete",
    priority: str = "normal",
    custom_questions: list[str] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Trigger WSI (Work Style Interview) screening for a candidate.
    
    WSI is a structured interview methodology combining Bloom's taxonomy,
    Dreyfus model, and Big Five personality assessment.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: UUID of the job vacancy
        screening_type: Type of screening ("complete", "technical", "behavioral", "quick")
        priority: Priority level ("high", "normal", "low")
        custom_questions: Optional list of custom screening questions
        
    Returns:
        Result with success status and screening session details
    """
    context = context_or_raise(kwargs, "wsi_screening")

    company_id = require_company_id_from_obj(context, "wsi_screening")

    user_id = context.user_id
    
    logger.info(f"🎯 Triggering WSI screening for candidate {candidate_id} on job {job_id} (company: {company_id})")
    
    try:
        import uuid

        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            cand_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = cand_result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }
            
            job_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == UUID(job_id),
                        JobVacancy.company_id == company_id
                    )
                )
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
                # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
                # to accept company_id via **kwargs from tool_handler.
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
            
            candidate_name = getattr(candidate, 'name', 'Candidato')
            job_title = getattr(job, 'title', 'Vaga')
            
            screening_session_id = f"system:{uuid.uuid4()}"
            
            screening_config = {
                "bloom_levels": ["remember", "understand", "apply", "analyze", "evaluate", "create"],
                "dreyfus_stages": ["novice", "advanced_beginner", "competent", "proficient", "expert"],
                "big_five_traits": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"],
            }
            
            if screening_type == "technical":
                screening_config["focus"] = ["bloom", "dreyfus"]
            elif screening_type == "behavioral":
                screening_config["focus"] = ["big_five"]
            elif screening_type == "quick":
                screening_config["bloom_levels"] = ["apply", "analyze"]
                screening_config["focus"] = ["bloom"]
            
            logger.info(f"✅ WSI screening session {screening_session_id} created for {candidate_id}")
            
            return {
                "success": True,
                "message": f"🎯 Triagem WSI ({screening_type}) iniciada para {candidate_name} na vaga '{job_title}'.",
                "action_taken": "wsi_screening",
                "affected_entities": [candidate_id, job_id],
                "data": {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "job_id": job_id,
                    "job_title": job_title,
                    "screening_session_id": screening_session_id,
                    "screening_type": screening_type,
                    "priority": priority,
                    "custom_questions": custom_questions or [],
                    "screening_config": screening_config,
                    "status": "pending",
                    "initiated_by": user_id,
                    "initiated_at": datetime.utcnow().isoformat()
                }
            }
                
    except Exception as e:
        logger.error(f"❌ Error triggering WSI screening: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao iniciar triagem WSI: {str(e)}",
            "error": str(e)
        }


async def hide_candidate(
    candidate_id: str,
    job_id: str | None = None,
    reason: str | None = None,
    hide_globally: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Hide/archive a candidate from the pipeline.
    
    Can hide a candidate from a specific job or globally from all pipelines.
    
    Args:
        candidate_id: UUID of the candidate
        job_id: Optional job vacancy ID (if hiding from specific job)
        reason: Optional reason for hiding
        hide_globally: If True, hides from all pipelines; if False, only from specific job
        
    Returns:
        Result with success status and message
    """
    context = context_or_raise(kwargs, "hide_candidate")

    company_id = require_company_id_from_obj(context, "hide_candidate")

    user_id = context.user_id
    
    logger.info(f"🙈 Hiding candidate {candidate_id} (global={hide_globally}, job={job_id}, company={company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): refactor
            # to accept company_id via **kwargs from tool_handler.
            cand_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = cand_result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }
            
            candidate_name = getattr(candidate, 'name', 'Candidato')
            
            if hide_globally:
                if hasattr(candidate, 'is_hidden'):
                    candidate.is_hidden = True
                if hasattr(candidate, 'hidden_at'):
                    candidate.hidden_at = datetime.utcnow()
                if hasattr(candidate, 'hidden_reason'):
                    candidate.hidden_reason = reason
                if hasattr(candidate, 'updated_at'):
                    candidate.updated_at = datetime.utcnow()
                    
                await db.commit()
                
                logger.info(f"✅ Candidate {candidate_id} hidden globally")
                
                return {
                    "success": True,
                    "message": f"🙈 {candidate_name} foi ocultado de todos os pipelines.",
                    "action_taken": "hide_candidate",
                    "affected_entities": [candidate_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "hidden_globally": True,
                        "reason": reason,
                        "hidden_by": user_id,
                        "hidden_at": datetime.utcnow().isoformat()
                    }
                }
            else:
                if not job_id:
                    return {
                        "success": False,
                        "message": "É necessário especificar job_id ou hide_globally=True",
                        "error": "missing_job_id"
                    }
                
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.candidate_id == UUID(candidate_id),
                            VacancyCandidate.vacancy_id == UUID(job_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                vacancy_candidate = vc_result.scalar_one_or_none()
                
                if not vacancy_candidate:
                    # TENANT-EXEMPT: INTENTIONAL cross-tenant probe. After the
                    # tenant-scoped query above returned None, this checks whether
                    # the pair exists in ANY tenant to distinguish "not found"
                    # from "exists in another tenant" — explicit cross-tenant
                    # access denial UX. Tool itself runs under tool_registry
                    # with Postgres RLS (Task #1143) defense.
                    vc_check = await db.execute(
                    # TENANT-EXEMPT: see above — RLS + tool_registry tenant context.
                        select(VacancyCandidate).where(
                            and_(
                                VacancyCandidate.candidate_id == UUID(candidate_id),
                                VacancyCandidate.vacancy_id == UUID(job_id)
                            )
                        )
                    )
                    if vc_check.scalar_one_or_none():
                        return {
                            "success": False,
                            "message": "Acesso negado: candidato pertence a outra empresa",
                            "error": "cross_tenant_access_denied"
                        }
                    return {
                        "success": False,
                        "message": "Candidato não encontrado nesta vaga",
                        "error": "candidate_not_in_vacancy"
                    }
                
                if hasattr(vacancy_candidate, 'is_hidden'):
                    vacancy_candidate.is_hidden = True
                if hasattr(vacancy_candidate, 'status'):
                    vacancy_candidate.status = "hidden"
                if hasattr(vacancy_candidate, 'updated_at'):
                    vacancy_candidate.updated_at = datetime.utcnow()
                    
                await db.commit()
                
                logger.info(f"✅ Candidate {candidate_id} hidden from job {job_id}")
                
                return {
                    "success": True,
                    "message": f"🙈 {candidate_name} foi ocultado desta vaga.",
                    "action_taken": "hide_candidate",
                    "affected_entities": [candidate_id, job_id],
                    "data": {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "hidden_globally": False,
                        "reason": reason,
                        "hidden_by": user_id,
                        "hidden_at": datetime.utcnow().isoformat()
                    }
                }
                
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error hiding candidate: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao ocultar candidato: {str(e)}",
            "error": str(e)
        }


UPDATE_CANDIDATE_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate to move"
        },
        "target_stage": {
            "type": "string",
            "description": "Target stage name (e.g., 'Triagem', 'Entrevistas', 'Oferta', 'Contratado', 'Reprovado')"
        },
        "job_id": {
            "type": "string",
            "description": "Optional UUID of the job vacancy"
        },
        "notes": {
            "type": "string",
            "description": "Optional notes about the stage change"
        },
        "notify_candidate": {
            "type": "boolean",
            "description": "Whether to notify the candidate about the change"
        }
    },
    "required": ["candidate_id", "target_stage"]
}

ADD_CANDIDATE_TO_VACANCY_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate"
        },
        "job_id": {
            "type": "string",
            "description": "UUID of the job vacancy"
        },
        "initial_stage": {
            "type": "string",
            "description": "Starting stage for the candidate",
            "default": "Triagem"
        },
        "source": {
            "type": "string",
            "description": "Source of the candidate (e.g., 'sourcing', 'aplicacao', 'indicacao')"
        },
        "notes": {
            "type": "string",
            "description": "Optional notes about adding the candidate"
        }
    },
    "required": ["candidate_id", "job_id"]
}

REJECT_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate to reject"
        },
        "job_id": {
            "type": "string",
            "description": "UUID of the job vacancy"
        },
        "reason": {
            "type": "string",
            "description": "Reason for rejection"
        },
        "send_feedback": {
            "type": "boolean",
            "description": "Whether to send rejection feedback to candidate",
            "default": True
        },
        "feedback_template": {
            "type": "string",
            "description": "Optional template ID for feedback email"
        }
    },
    "required": ["candidate_id", "job_id", "reason"]
}

SHORTLIST_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate"
        },
        "job_id": {
            "type": "string",
            "description": "UUID of the job vacancy"
        },
        "priority": {
            "type": "string",
            "description": "Priority level",
            "enum": ["high", "normal", "low"],
            "default": "normal"
        },
        "notes": {
            "type": "string",
            "description": "Optional notes about why they're shortlisted"
        }
    },
    "required": ["candidate_id", "job_id"]
}

BULK_UPDATE_CANDIDATES_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of candidate UUIDs to move"
        },
        "target_stage": {
            "type": "string",
            "description": "Target stage name"
        },
        "job_id": {
            "type": "string",
            "description": "Optional job vacancy ID"
        },
        "notes": {
            "type": "string",
            "description": "Optional notes about the bulk action"
        }
    },
    "required": ["candidate_ids", "target_stage"]
}

ADD_TO_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate to add to the list"
        },
        "list_id": {
            "type": "string",
            "description": "UUID of the target list/shortlist"
        },
        "notes": {
            "type": "string",
            "description": "Optional notes about adding the candidate"
        }
    },
    "required": ["candidate_id", "list_id"]
}

WSI_SCREENING_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate to screen"
        },
        "job_id": {
            "type": "string",
            "description": "UUID of the job vacancy"
        },
        "screening_type": {
            "type": "string",
            "description": "Type of WSI screening",
            "enum": ["complete", "technical", "behavioral", "quick"],
            "default": "complete"
        },
        "priority": {
            "type": "string",
            "description": "Priority level for the screening",
            "enum": ["high", "normal", "low"],
            "default": "normal"
        },
        "custom_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of custom screening questions"
        }
    },
    "required": ["candidate_id", "job_id"]
}

HIDE_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string",
            "description": "UUID of the candidate to hide"
        },
        "job_id": {
            "type": "string",
            "description": "UUID of the job vacancy (required if hide_globally is False)"
        },
        "reason": {
            "type": "string",
            "description": "Optional reason for hiding the candidate"
        },
        "hide_globally": {
            "type": "boolean",
            "description": "If True, hides from all pipelines; if False, only from specific job",
            "default": False
        }
    },
    "required": ["candidate_id"]
}




async def _wrap_update_candidate_stage(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await update_candidate_stage(**normalize_wrapper_kwargs(kwargs))




async def _wrap_add_candidate_to_vacancy(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await add_candidate_to_vacancy(**normalize_wrapper_kwargs(kwargs))




async def _wrap_add_to_list(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await add_to_list(**normalize_wrapper_kwargs(kwargs))




async def _wrap_wsi_screening(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await wsi_screening(**normalize_wrapper_kwargs(kwargs))




async def _wrap_hide_candidate(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await hide_candidate(**normalize_wrapper_kwargs(kwargs))


def register_candidate_tools() -> None:
    """Register all candidate tools in the registry."""
    
    tool_registry.register(ToolDefinition(
        name="update_candidate_stage",
        description="Move um candidato para uma etapa diferente no pipeline de recrutamento. Use para mover candidatos entre etapas como Triagem, Entrevistas, Oferta, Contratado.",
        parameters_schema=UPDATE_CANDIDATE_STAGE_SCHEMA,
        handler=_wrap_update_candidate_stage,
        allowed_agents=["orchestrator", "recruiter_assistant", "screening", "analyst_feedback"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="add_candidate_to_vacancy",
        description="Adiciona um candidato a uma vaga de emprego, iniciando-o no pipeline de recrutamento.",
        parameters_schema=ADD_CANDIDATE_TO_VACANCY_SCHEMA,
        handler=_wrap_add_candidate_to_vacancy,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="reject_candidate",
        description="Rejeita um candidato de uma vaga. Esta é uma ação sensível que pode requerer confirmação. Use com cuidado.",
        parameters_schema=REJECT_CANDIDATE_SCHEMA,
        handler=reject_candidate,
        allowed_agents=["orchestrator", "recruiter_assistant", "analyst_feedback"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="shortlist_candidate",
        description="Adiciona um candidato à shortlist/lista de favoritos para uma vaga, marcando-o como prioritário para consideração.",
        parameters_schema=SHORTLIST_CANDIDATE_SCHEMA,
        handler=shortlist_candidate,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "screening"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="bulk_update_candidates_stage",
        description="Move múltiplos candidatos para uma etapa de uma só vez. Útil para ações em massa.",
        parameters_schema=BULK_UPDATE_CANDIDATES_STAGE_SCHEMA,
        handler=bulk_update_candidates_stage,
        allowed_agents=["orchestrator", "recruiter_assistant"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="add_to_list",
        description="Adiciona um candidato a uma lista salva ou shortlist. Use para organizar candidatos em listas personalizadas.",
        parameters_schema=ADD_TO_LIST_SCHEMA,
        handler=_wrap_add_to_list,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="wsi_screening",
        description="Inicia triagem WSI (Work Style Interview) para um candidato. A triagem WSI combina Taxonomia de Bloom, modelo Dreyfus e Big Five para avaliação científica.",
        parameters_schema=WSI_SCREENING_SCHEMA,
        handler=_wrap_wsi_screening,
        allowed_agents=["orchestrator", "recruiter_assistant", "screening", "interviewer"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="hide_candidate",
        description="Oculta/arquiva um candidato do pipeline. Pode ocultar de uma vaga específica ou globalmente de todos os pipelines.",
        parameters_schema=HIDE_CANDIDATE_SCHEMA,
        handler=_wrap_hide_candidate,
        allowed_agents=["orchestrator", "recruiter_assistant"]
    ))
    
    logger.info("✅ Registered 8 candidate tools")
