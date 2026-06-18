"""
Job Management Query Tools - Tools for job search, details, velocity, quality, and benchmarks.
Provides function calling capabilities for:
- Searching and filtering job vacancies
- Getting job details with candidates and funnel data
- Job velocity metrics and progress tracking
- Job quality metrics for candidate scoring
- Job benchmarking against historical similar jobs
All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import logging
from types import SimpleNamespace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID
from app.tools.registry import ToolDefinition, tool_registry
from app.tools.context_helpers import normalize_wrapper_kwargs
if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext
logger = logging.getLogger(__name__)

# Canonical slug → PT-BR label map (mirrors DEFAULT_RECRUITMENT_STAGES).
# Normalizes mixed PT/EN slugs that exist in historical DB data.
_STAGE_DISPLAY = {
    "sourcing": "Funil",
    "screening": "Triagem",
    "long_list": "Long List",
    "short_list": "Short List",
    "interview_hr": "Entrevista RH",
    "technical_test": "Teste Tecnico",
    "interview_technical": "Entrevista Tecnica",
    "interview_manager": "Entrevista Gestor",
    "interview_final": "Entrevista Final",
    "references": "Referencias",
    "offer": "Proposta",
    "offer_declined": "Proposta Recusada",
    "hired": "Contratado",
    "rejected": "Reprovado",
    # PT aliases that may exist in historical DB
    "triagem": "Triagem",
    "entrevista": "Entrevista RH",
    "proposta": "Proposta",
    "reprovado": "Reprovado",
    "contratado": "Contratado",
}


def _normalize_stage(raw):
    """Normalize raw slug or display name to canonical PT-BR label."""
    if not raw:
        return "Indefinido"
    s = raw.strip()
    return _STAGE_DISPLAY.get(s, _STAGE_DISPLAY.get(s.lower(), s))


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)
def _format_search_jobs_result(jobs_list: list, applied_filters: dict) -> dict:
    """P0.2 (autocorrecao 0-resultados): formata resultado de search_jobs.
    Em 0-resultados, anexa sinal ESTRUTURADO de relaxamento via
    build_empty_result_guidance (helper puro) -> a LIA relaxa 1 filtro e oferece
    opcoes com contagem, nunca beco sem saida (extensao da REGRA 4 anti-fallback
    silencioso). Funcao PURA -> testavel sem DB.
    """
    if not jobs_list:
        from app.orchestrator.context.empty_result_guidance import (
            build_empty_result_guidance,
        )
        g = build_empty_result_guidance("vaga", applied_filters)
        return {
            "success": True,
            "message": g.get("guidance")
            or "Nenhuma vaga encontrada com esses criterios.",
            "data": {"total": 0, "jobs": [], **g},
        }
    return {
        "success": True,
        "message": f"✅ Encontradas {len(jobs_list)} vagas.",
        "data": {
            "total": len(jobs_list),
            "jobs": jobs_list,
            "filters_applied": {
                k: v for k, v in (applied_filters or {}).items() if v not in (None, "")
            },
        },
    }
async def search_jobs(
    status: str | None = None,
    department: str | None = None,
    seniority: str | None = None,
    work_model: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    has_candidates: bool | None = None,
    min_candidates: int | None = None,
    urgent: bool | None = None,
    recruiter_id: str | None = None,
    limit: int = 20,
    **kwargs
) -> dict[str, Any]:
    """
    Search job vacancies with various filters.
    
    Args:
        status: Job status canonical (Ativa, Pausada, Concluída, Rascunho, Cancelada, Arquivada)
        department: Department filter
        seniority: Seniority level filter
        work_model: Work model (Remoto, Híbrido, Presencial)
        created_after: Filter jobs created after this date (ISO format)
        created_before: Filter jobs created before this date (ISO format)
        has_candidates: Filter jobs that have/don't have candidates
        min_candidates: Minimum number of candidates required
        urgent: Filter urgent jobs
        recruiter_id: Filter by recruiter
        limit: Maximum number of results (default 20)
        
    Returns:
        List of matching jobs with their details
    """
    # G2 canonical fix (2026-05-24): fail-loud via require_company_id_from_context.
    # The previous antipattern caused silent 0-rows when _context was missing.
    # Per CLAUDE.md REGRA 4 multi-tenancy fail-closed.
    from app.tools.context_helpers import require_company_id_from_context
    company_id = require_company_id_from_context(kwargs, "search_jobs")
    logger.info(f"🔍 Searching jobs with filters (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select
        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            # P0-RLS (2026-06-03): seta o GUC app.company_id na transacao.
            # Sem isso, no contexto do agentic loop (sem middleware RLS) a
            # policy `company_id = app_current_company_id()` retorna NULL e
            # BLOQUEIA todas as linhas -> "0 vagas" mesmo com 101 no banco.
            from app.core.database import set_tenant_context
            await set_tenant_context(db, company_id)
            # TENANT-EXEMPT: dynamic builder — conditions[0] is always
            # JobVacancy.company_id == company_id (line below). AST sensor
            # cannot trace upstream tenant gate.
            query = select(JobVacancy)
            conditions = [JobVacancy.company_id == company_id]
            
            if status:
                conditions.append(JobVacancy.status == status)
            
            if department:
                conditions.append(JobVacancy.department == department)
            
            if seniority:
                conditions.append(JobVacancy.seniority_level == seniority)
            
            if work_model:
                conditions.append(JobVacancy.work_model == work_model)
            
            if recruiter_id:
                conditions.append(JobVacancy.recruiter == recruiter_id)
            
            if created_after:
                try:
                    date_after = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                    conditions.append(JobVacancy.created_at >= date_after)
                except ValueError:
                    pass
            
            if created_before:
                try:
                    date_before = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                    conditions.append(JobVacancy.created_at <= date_before)
                except ValueError:
                    pass
            
            query = query.where(and_(*conditions))
            query = query.order_by(JobVacancy.created_at.desc())
            query = query.limit(limit)
            
            result = await db.execute(query)
            jobs = result.scalars().all()
            
            jobs_list = []
            for j in jobs:
                job_data = {
                    "id": str(j.id),
                    "title": j.title,
                    "department": getattr(j, 'department', None),
                    "seniority": getattr(j, 'seniority_level', None),
                    "work_model": getattr(j, 'work_model', None),
                    "location": getattr(j, 'location', None),
                    "status": j.status,
                    "stage": getattr(j, 'stage', None),
                    "recruiter": getattr(j, 'recruiter', None),
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "published_at": j.published_at.isoformat() if getattr(j, 'published_at', None) else None,
                    "candidate_count": getattr(j, 'candidate_count', 0),
                    "salary_range": getattr(j, 'salary_range', None),
                }
                jobs_list.append(job_data)
            
            return _format_search_jobs_result(jobs_list, {
                "status": status,
                "department": department,
                "seniority": seniority,
                "work_model": work_model,
                "recruiter_id": recruiter_id,
                "created_after": created_after,
                "created_before": created_before,
            })
            
    except Exception as e:
        logger.error(f"❌ Error searching jobs: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar vagas: {str(e)}",
            "error": str(e)
        }
async def get_job_details(
    job_id: str,
    include_candidates: bool = True,
    include_funnel: bool = True,
    **kwargs
) -> dict[str, Any]:
    """
    Get detailed information about a specific job vacancy.
    
    Args:
        job_id: UUID of the job vacancy
        include_candidates: Include list of candidates
        include_funnel: Include funnel statistics
        
    Returns:
        Detailed job information with metrics
    """
    from app.tools.context_helpers import require_company_id_from_context
    from app.shared.entity_resolver import get_active_vacancy
    company_id = require_company_id_from_context(kwargs, "get_job_details")
    # P0-A fix (2026-06-14): fallback to active vacancy when LLM omits job_id.
    # Without this, UUID("") raises ValueError -> "instabilidade tecnica".
    job_id = job_id or get_active_vacancy()
    if not job_id:
        return {
            "success": False,
            "needs_clarification": True,
            "message": "Preciso saber qual vaga voce quer ver. Pode me dizer o nome ou titulo da vaga?",
        }
    # Guard: UUID antes de converter — evita ValueError quando LLM passa titulo em vez de ID
    import re as _re_uuid
    _UUID_RE = _re_uuid.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    if job_id and not _UUID_RE.match(str(job_id)):
        logger.warning('get_job_details: job_id invalido (nao-UUID): %r', str(job_id)[:60])
        return {
            "success": False,
            "needs_clarification": True,
            "message": (
                f"O valor '{str(job_id)[:40]}' nao e um ID de vaga valido. "
                "Use o UUID do campo 'id' retornado por list_jobs ou search_jobs."
            ),
        }
    logger.info(f"📋 Getting job details: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select
        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
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
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            job_data = {
                "id": str(job.id),
                "title": job.title,
                "department": getattr(job, 'department', None),
                "seniority": getattr(job, 'seniority_level', None),
                "work_model": getattr(job, 'work_model', None),
                "location": getattr(job, 'location', None),
                "description": getattr(job, 'description', None),
                "requirements": getattr(job, 'requirements', []) or [],
                "status": job.status,
                "stage": getattr(job, 'stage', None),
                "recruiter": getattr(job, 'recruiter', None),
                "salary_range": getattr(job, 'salary_range', None),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "published_at": job.published_at.isoformat() if getattr(job, 'published_at', None) else None,
                "closed_at": job.closed_at.isoformat() if getattr(job, 'closed_at', None) else None,
            }
            
            if include_candidates or include_funnel:
                vc_result = await db.execute(
                    select(VacancyCandidate, Candidate).join(
                        Candidate,
                        and_(
                            VacancyCandidate.candidate_id == Candidate.id,
                            Candidate.company_id == company_id
                        )
                    ).where(
                        and_(
                            VacancyCandidate.vacancy_id == UUID(job_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                vacancy_candidates = vc_result.all()
                
                if include_funnel:
                    funnel = {}
                    seen_ids_funnel = set()
                    for vc, c in vacancy_candidates:
                        cid = str(getattr(c, 'id', '') or '')
                        if cid in seen_ids_funnel:
                            continue
                        seen_ids_funnel.add(cid)
                        stage = _normalize_stage(getattr(vc, 'stage', None))
                        funnel[stage] = funnel.get(stage, 0) + 1

                    job_data["funnel"] = funnel
                    job_data["total_candidates"] = len(seen_ids_funnel)
                
                if include_candidates:
                    seen_ids_cands = set()
                    cands = []
                    for vc, c in vacancy_candidates:
                        cid = str(getattr(c, 'id', '') or '')
                        if cid in seen_ids_cands:
                            continue
                        seen_ids_cands.add(cid)
                        cands.append({
                            "id": cid,
                            "name": getattr(c, 'name', 'N/A'),
                            "stage": _normalize_stage(getattr(vc, 'stage', None)),
                            "status": getattr(vc, 'status', None),
                            "lia_score": getattr(c, 'lia_score', None),
                            "wsi_score": getattr(c, 'wsi_score', None),
                        })
                    job_data["candidates"] = cands
            
            return {
                "success": True,
                "message": f"✅ Detalhes da vaga: {job_data['title']}",
                "data": job_data
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting job details: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar detalhes da vaga: {str(e)}",
            "error": str(e)
        }
async def get_job_velocity(
    job_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Get velocity metrics for a specific job.
    
    Args:
        job_id: UUID of the job vacancy (required)
        
    Returns:
        Velocity metrics including days_since_opened, estimated_days_to_close,
        velocity_score, on_track status
    """
    company_id = require_company_id_from_context(kwargs, "get_job_velocity")
    
    logger.info(f"🚀 Getting job velocity: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select
        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
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
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            open_date = getattr(job, 'open_date', None) or getattr(job, 'published_at', None) or job.created_at
            days_since_opened = (datetime.utcnow() - open_date).days if open_date else 0
            
            deadline = getattr(job, 'deadline', None) or getattr(job, 'deadline_closing', None)
            sla_days = (deadline - open_date).days if deadline and open_date else 30
            
            vc_result = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.company_id == company_id
                    )
                )
            )
            candidates = vc_result.scalars().all()
            
            stage_weights = {
                "Triagem": 0.1,
                "Entrevista RH": 0.3,
                "Entrevista Técnica": 0.5,
                "Entrevista Final": 0.7,
                "Oferta": 0.9,
                "Contratado": 1.0
            }
            
            max_progress = 0
            for vc in candidates:
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'
                progress = stage_weights.get(stage, 0.05)
                if progress > max_progress:
                    max_progress = progress
            
            if max_progress >= 1.0:
                estimated_days_to_close = 0
            elif max_progress > 0 and days_since_opened > 0:
                remaining_progress = 1.0 - max_progress
                days_per_progress = days_since_opened / max_progress
                estimated_days_to_close = int(remaining_progress * days_per_progress)
            else:
                estimated_days_to_close = sla_days
            
            historical_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.company_id == company_id,
                        JobVacancy.status == "Concluída",
                        JobVacancy.department == job.department
                    )
                ).limit(20)
            )
            similar_jobs = historical_result.scalars().all()
            
            historical_ttf = []
            for sj in similar_jobs:
                if hasattr(sj, 'closed_at') and sj.closed_at and sj.created_at:
                    ttf = (sj.closed_at - sj.created_at).days
                    historical_ttf.append(ttf)
            
            avg_historical_ttf = sum(historical_ttf) / len(historical_ttf) if historical_ttf else 30
            
            expected_days_at_this_point = sla_days * max_progress if max_progress > 0 else 0
            if days_since_opened > 0 and expected_days_at_this_point > 0:
                velocity_score = min(100, int((expected_days_at_this_point / days_since_opened) * 100))
            else:
                velocity_score = 100 if max_progress > 0 else 50
            
            on_track = (days_since_opened + estimated_days_to_close) <= sla_days
            
            return {
                "success": True,
                "message": f"✅ Velocidade da vaga '{job.title}'",
                "data": {
                    "job_id": job_id,
                    "job_title": job.title,
                    "status": job.status,
                    "days_since_opened": days_since_opened,
                    "sla_days": sla_days,
                    "estimated_days_to_close": estimated_days_to_close,
                    "total_estimated_days": days_since_opened + estimated_days_to_close,
                    "current_progress": round(max_progress * 100, 1),
                    "velocity_score": velocity_score,
                    "on_track": on_track,
                    "candidates_in_pipeline": len(candidates),
                    "historical_avg_ttf": round(avg_historical_ttf, 1),
                    "deadline": deadline.isoformat() if deadline else None
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting job velocity: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao calcular velocidade da vaga: {str(e)}",
            "error": str(e)
        }
async def get_job_quality_metrics(
    job_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Get candidate quality metrics for a specific job.
    
    Args:
        job_id: UUID of the job vacancy (required)
        
    Returns:
        Quality metrics including average_candidate_score, requirement_fit_percentage,
        top_candidates_count, quality_trend
    """
    company_id = require_company_id_from_context(kwargs, "get_job_quality_metrics")
    
    logger.info(f"⭐ Getting job quality metrics: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select
        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
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
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            vc_result = await db.execute(
                select(VacancyCandidate, Candidate).join(
                    Candidate, VacancyCandidate.candidate_id == Candidate.id
                ).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.company_id == company_id
                    )
                )
            )
            vacancy_candidates = vc_result.all()
            
            if not vacancy_candidates:
                return {
                    "success": True,
                    "message": "📊 Sem candidatos para análise de qualidade",
                    "data": {
                        "job_id": job_id,
                        "job_title": job.title,
                        "total_candidates": 0,
                        "average_candidate_score": 0,
                        "requirement_fit_percentage": 0,
                        "top_candidates_count": 0,
                        "quality_trend": "neutral"
                    }
                }
            
            lia_scores = []
            match_percentages = []
            top_candidates = []
            scores_by_week: dict[int, list[float]] = {}
            
            now = datetime.utcnow()
            
            for vc, c in vacancy_candidates:
                lia_score = getattr(c, 'lia_score', None) or getattr(vc, 'lia_score', None)
                match_pct = getattr(vc, 'match_percentage', None) or getattr(c, 'skills_match_percentage', None)
                
                if lia_score is not None:
                    lia_scores.append(lia_score)
                    
                    if hasattr(vc, 'created_at') and vc.created_at:
                        weeks_ago = (now - vc.created_at).days // 7
                        if weeks_ago not in scores_by_week:
                            scores_by_week[weeks_ago] = []
                        scores_by_week[weeks_ago].append(lia_score)
                
                if match_pct is not None:
                    match_percentages.append(match_pct)
                
                if lia_score and lia_score >= 80:
                    top_candidates.append({
                        "id": str(c.id),
                        "name": getattr(c, 'name', 'N/A'),
                        "lia_score": lia_score,
                        "stage": getattr(vc, 'stage', 'N/A')
                    })
            
            average_score = sum(lia_scores) / len(lia_scores) if lia_scores else 0
            avg_match = sum(match_percentages) / len(match_percentages) if match_percentages else 0
            
            sorted_weeks = sorted(scores_by_week.keys())
            if len(sorted_weeks) >= 2:
                recent_avg = sum(scores_by_week[sorted_weeks[0]]) / len(scores_by_week[sorted_weeks[0]]) if scores_by_week[sorted_weeks[0]] else 0
                older_avg = sum(scores_by_week[sorted_weeks[-1]]) / len(scores_by_week[sorted_weeks[-1]]) if scores_by_week[sorted_weeks[-1]] else 0
                
                if recent_avg > older_avg + 5:
                    quality_trend = "improving"
                elif recent_avg < older_avg - 5:
                    quality_trend = "declining"
                else:
                    quality_trend = "stable"
            else:
                quality_trend = "neutral"
            
            score_distribution = {"0-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
            for score in lia_scores:
                if score <= 40:
                    score_distribution["0-40"] += 1
                elif score <= 60:
                    score_distribution["41-60"] += 1
                elif score <= 80:
                    score_distribution["61-80"] += 1
                else:
                    score_distribution["81-100"] += 1
            
            return {
                "success": True,
                "message": f"✅ Métricas de qualidade para '{job.title}'",
                "data": {
                    "job_id": job_id,
                    "job_title": job.title,
                    "total_candidates": len(vacancy_candidates),
                    "candidates_with_scores": len(lia_scores),
                    "average_candidate_score": round(average_score, 1),
                    "requirement_fit_percentage": round(avg_match, 1),
                    "top_candidates_count": len(top_candidates),
                    "top_candidates": sorted(top_candidates, key=lambda x: x["lia_score"], reverse=True)[:5],
                    "quality_trend": quality_trend,
                    "score_distribution": score_distribution
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting job quality metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de qualidade: {str(e)}",
            "error": str(e)
        }
async def get_job_benchmark(
    job_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Get job performance compared to historical similar jobs.
    
    Args:
        job_id: UUID of the job to benchmark (required)
        
    Returns:
        Benchmark comparison including percentile ranking and key differences
    """
    company_id = require_company_id_from_context(kwargs, "get_job_benchmark")
    
    logger.info(f"📊 Getting job benchmark for {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select
        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == UUID(job_id),
                        JobVacancy.company_id == company_id
                    )
                )
            )
            current_job = job_result.scalar_one_or_none()
            
            if not current_job:
                return {
                    "success": False,
                    "message": f"❌ Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            similar_conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == 'Concluída',
                JobVacancy.id != UUID(job_id)
            ]
            
            if current_job.department:
                similar_conditions.append(JobVacancy.department == current_job.department)
            
            if current_job.seniority_level:
                similar_conditions.append(JobVacancy.seniority_level == current_job.seniority_level)
            
            similar_result = await db.execute(
                # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace upstream tenant gate
                select(JobVacancy).where(and_(*similar_conditions)).limit(50)
            )
            similar_jobs = similar_result.scalars().all()
            
            current_vc_result = await db.execute(
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.company_id == company_id
                    )
                )
            )
            current_candidates = len(current_vc_result.scalars().all())
            
            current_days_open = (datetime.utcnow() - current_job.created_at).days if current_job.created_at else 0
            
            if not similar_jobs:
                return {
                    "success": True,
                    "message": "✅ Benchmark: sem vagas similares para comparação",
                    "data": {
                        "job_id": job_id,
                        "job_title": current_job.title,
                        "similar_jobs_found": 0,
                        "current_metrics": {
                            "candidates": current_candidates,
                            "days_open": current_days_open
                        },
                        "current_vs_similar": None,
                        "better_than_average": None,
                        "percentile_ranking": None,
                        "key_differences": ["Não há vagas similares fechadas para comparação"]
                    }
                }
            
            avg_candidates_list = []
            avg_days_list = []
            
            for sj in similar_jobs:
                sj_vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.vacancy_id == sj.id,
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                sj_candidates = len(sj_vc_result.scalars().all())
                avg_candidates_list.append(sj_candidates)
                
                if sj.created_at and sj.closed_at:
                    days_to_close = (sj.closed_at - sj.created_at).days
                    avg_days_list.append(days_to_close)
            
            avg_candidates = sum(avg_candidates_list) / len(avg_candidates_list) if avg_candidates_list else 0
            avg_days_to_close = sum(avg_days_list) / len(avg_days_list) if avg_days_list else 30
            
            candidate_comparison = current_candidates - avg_candidates
            days_comparison = current_days_open - avg_days_to_close
            
            sorted_candidates = sorted(avg_candidates_list)
            position = sum(1 for x in sorted_candidates if x < current_candidates)
            percentile = (position / len(sorted_candidates) * 100) if sorted_candidates else 50
            
            key_differences = []
            better_than_avg = True
            
            if current_candidates > avg_candidates * 1.2:
                key_differences.append(f"Mais candidatos que média (+{round(candidate_comparison)})")
            elif current_candidates < avg_candidates * 0.8:
                key_differences.append(f"Menos candidatos que média ({round(candidate_comparison)})")
                better_than_avg = False
            
            if avg_days_list and current_days_open > avg_days_to_close * 1.2:
                key_differences.append(f"Tempo aberto acima da média (+{round(days_comparison - avg_days_to_close)} dias)")
                better_than_avg = False
            elif avg_days_list and current_days_open < avg_days_to_close * 0.8:
                key_differences.append("Progresso mais rápido que média")
            
            if not key_differences:
                key_differences.append("Performance dentro da média")
            
            return {
                "success": True,
                "message": f"✅ Benchmark da vaga: {current_job.title}",
                "data": {
                    "job_id": job_id,
                    "job_title": current_job.title,
                    "similar_jobs_found": len(similar_jobs),
                    "comparison_criteria": {
                        "department": current_job.department,
                        "seniority": current_job.seniority_level
                    },
                    "current_vs_similar": {
                        "current_candidates": current_candidates,
                        "average_candidates": round(avg_candidates, 1),
                        "candidate_difference": round(candidate_comparison, 1),
                        "current_days_open": current_days_open,
                        "average_days_to_close": round(avg_days_to_close, 1)
                    },
                    "better_than_average": better_than_avg,
                    "percentile_ranking": round(percentile, 1),
                    "key_differences": key_differences
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting job benchmark: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao calcular benchmark: {str(e)}",
            "error": str(e)
        }
async def _wrap_search_jobs(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).
    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await search_jobs(**normalize_wrapper_kwargs(kwargs))
async def _wrap_get_job_details(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).
    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_job_details(**normalize_wrapper_kwargs(kwargs))
async def _wrap_get_job_velocity(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).
    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_job_velocity(**normalize_wrapper_kwargs(kwargs))
async def _wrap_get_job_quality_metrics(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).
    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_job_quality_metrics(**normalize_wrapper_kwargs(kwargs))
async def _wrap_get_job_benchmark(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).
    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_job_benchmark(**normalize_wrapper_kwargs(kwargs))
def register_job_management_query_tools() -> None:
    """Register job-management-domain query tools in the tool registry."""
    
    tool_registry.register(ToolDefinition(
        name="search_jobs",
        description="Buscar vagas com filtros como status, departamento, senioridade, modelo de trabalho, data de criação. Use para listar vagas ou responder perguntas sobre as vagas da empresa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["Ativa", "Pausada", "Concluída", "Rascunho", "Cancelada", "Arquivada"], "description": "Status da vaga (canonical DB). Use Concluída para vagas encerradas/fechadas."},
                "department": {"type": "string", "description": "Departamento"},
                "seniority": {"type": "string", "description": "Nível de senioridade"},
                "work_model": {"type": "string", "enum": ["Remoto", "Híbrido", "Presencial"], "description": "Modelo de trabalho"},
                "created_after": {"type": "string", "format": "date", "description": "Vagas criadas após esta data (ISO format)"},
                "created_before": {"type": "string", "format": "date", "description": "Vagas criadas antes desta data (ISO format)"},
                "urgent": {"type": "boolean", "description": "Filtrar vagas urgentes"},
                "recruiter_id": {"type": "string", "description": "Filtrar por recrutador"},
                "limit": {"type": "integer", "default": 20, "description": "Número máximo de resultados"}
            }
        },
        handler=_wrap_search_jobs,
        allowed_agents=["recruiter_assistant", "job_planner", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_job_details",
        description="Obter detalhes completos de uma vaga incluindo requisitos, candidatos, e métricas do funil.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga"},
                "include_candidates": {"type": "boolean", "default": True, "description": "Incluir lista de candidatos"},
                "include_funnel": {"type": "boolean", "default": True, "description": "Incluir estatísticas do funil"}
            },
            "required": ["job_id"]
        },
        handler=_wrap_get_job_details,
        allowed_agents=["recruiter_assistant", "job_planner", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_job_velocity",
        description="Obter velocidade de uma vaga: dias desde abertura, estimativa para fechamento, score de velocidade, status on_track.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"}
            },
            "required": ["job_id"]
        },
        handler=_wrap_get_job_velocity,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_job_quality_metrics",
        description="Obter métricas de qualidade dos candidatos de uma vaga: score médio, percentual de aderência, candidatos top, tendência de qualidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"}
            },
            "required": ["job_id"]
        },
        handler=_wrap_get_job_quality_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "wsi_evaluator", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_job_benchmark",
        description="Comparar performance de uma vaga com vagas similares já fechadas: ranking percentil, diferenças-chave, performance vs média.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para benchmark (obrigatório)"}
            },
            "required": ["job_id"]
        },
        handler=_wrap_get_job_benchmark,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    logger.info("✅ Registered 5 job management query tools")
