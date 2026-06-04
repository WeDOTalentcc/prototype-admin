"""
Sourcing Query Tools - Tools for candidate search, talent metrics, and market benchmarks.

Provides function calling capabilities for:
- Searching and filtering candidates
- Getting candidate details, stats, and history
- Talent quality, engagement, and availability metrics
- Diversity metrics and market benchmarks

All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import logging
from types import SimpleNamespace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID


from app.tools.registry import ToolDefinition, tool_registry
from app.tools.context_helpers import require_company_id_from_context, normalize_wrapper_kwargs

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


def _format_search_candidates_result(candidates_list: list, applied_filters: dict) -> dict:
    """P0.2 (autocorrecao 0-resultados): formata resultado de search_candidates.

    Em 0-resultados, anexa sinal ESTRUTURADO de relaxamento via
    build_empty_result_guidance (produtor unico, reuso) -> a LIA relaxa 1 filtro e
    oferece opcoes, nunca beco sem saida (REGRA 4). Funcao PURA -> testavel sem DB.
    """
    if not candidates_list:
        from app.orchestrator.context.empty_result_guidance import (
            build_empty_result_guidance,
        )
        g = build_empty_result_guidance("candidato", applied_filters)
        return {
            "success": True,
            "message": g.get("guidance")
            or "Nenhum candidato encontrado com esses criterios.",
            "data": {"total": 0, "candidates": [], **g},
        }
    return {
        "success": True,
        "message": f"✅ Encontrados {len(candidates_list)} candidatos.",
        "data": {
            "total": len(candidates_list),
            "candidates": candidates_list,
            "filters_applied": {
                k: v for k, v in (applied_filters or {}).items() if v not in (None, "", [], {})
            },
        },
    }


async def search_candidates(
    skills: list[str] | None = None,
    min_experience_years: int | None = None,
    max_experience_years: int | None = None,
    seniority: str | None = None,
    min_score: float | None = None,
    status: str | None = None,
    available_immediately: bool | None = None,
    location: str | None = None,
    language: str | None = None,
    in_vacancy_id: str | None = None,
    limit: int = 20,
    **kwargs
) -> dict[str, Any]:
    """
    Search candidates with various filters.
    
    Args:
        skills: List of required skills to filter by
        min_experience_years: Minimum years of experience
        max_experience_years: Maximum years of experience
        seniority: Seniority level (Júnior, Pleno, Sênior, Especialista)
        min_score: Minimum LIA/WSI score (0-100)
        status: Candidate status filter
        available_immediately: Filter by immediate availability
        location: Location filter
        language: Language requirement (e.g., 'Inglês Fluente')
        in_vacancy_id: Filter candidates in a specific vacancy
        limit: Maximum number of results (default 20)
        
    Returns:
        List of matching candidates with their details
    """
    company_id = require_company_id_from_context(kwargs, "search_candidates")
    
    logger.info(f"🔍 Searching candidates with filters (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            query = select(Candidate)
            conditions = []
            
            if hasattr(Candidate, 'company_id'):
                conditions.append(Candidate.company_id == company_id)
            
            if status:
                conditions.append(Candidate.status == status)
            
            if seniority:
                conditions.append(Candidate.seniority_level == seniority)
            
            if location:
                conditions.append(Candidate.location_city.ilike(f"%{location}%"))
            
            if min_score is not None and hasattr(Candidate, 'lia_score'):
                conditions.append(Candidate.lia_score >= min_score)
            
            if min_experience_years is not None and hasattr(Candidate, 'years_experience'):
                conditions.append(Candidate.years_experience >= min_experience_years)
            
            if max_experience_years is not None and hasattr(Candidate, 'years_experience'):
                conditions.append(Candidate.years_experience <= max_experience_years)
            
            if available_immediately is not None and hasattr(Candidate, 'available_immediately'):
                conditions.append(Candidate.available_immediately == available_immediately)
            
            if in_vacancy_id:
                query = query.join(
                    VacancyCandidate, 
                    and_(
                        Candidate.id == VacancyCandidate.candidate_id,
                        VacancyCandidate.company_id == company_id
                    )
                ).where(VacancyCandidate.vacancy_id == UUID(in_vacancy_id))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            has_post_filters = skills or language
            effective_limit = limit * 5 if has_post_filters else limit
            
            query = query.limit(effective_limit)
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            if skills:
                skills_lower = [s.lower() for s in skills]
                candidates = [
                    c for c in candidates 
                    if any(
                        skill.lower() in skills_lower 
                        for skill in (getattr(c, 'technical_skills', []) or [])
                    )
                ]
            
            if language:
                language_lower = language.lower()
                candidates = [
                    c for c in candidates
                    if any(
                        language_lower in lang.lower()
                        for lang in (getattr(c, 'languages', []) or [])
                    )
                ]
            
            candidates = candidates[:limit]
            
            candidates_list = []
            for c in candidates:
                candidate_data = {
                    "id": str(c.id),
                    "name": getattr(c, 'name', 'N/A'),
                    "email": getattr(c, 'email', None),
                    "seniority": getattr(c, 'seniority_level', None),
                    "location": getattr(c, 'location', None),
                    "status": getattr(c, 'status', None),
                    "lia_score": getattr(c, 'lia_score', None),
                    "wsi_score": getattr(c, 'wsi_score', None),
                    "years_experience": getattr(c, 'years_experience', None),
                    "skills": getattr(c, 'technical_skills', []) or [],
                    "available_immediately": getattr(c, 'available_immediately', None),
                }
                candidates_list.append(candidate_data)
            
            return _format_search_candidates_result(candidates_list, {
                "skills": skills,
                "seniority": seniority,
                "min_score": min_score,
                "location": location,
                "status": status,
                "min_experience_years": min_experience_years,
                "language": language,
            })
            
    except Exception as e:
        logger.error(f"❌ Error searching candidates: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar candidatos: {str(e)}",
            "error": str(e)
        }


async def rank_candidates(
    vacancy_id: str | None = None,
    candidate_ids: list[str] | None = None,
    qualification_level: str | None = None,
    limit: int = 20,
    **kwargs
) -> dict[str, Any]:
    """
    Rank candidates using Weighted Rank Fusion (WRF).

    Args:
        vacancy_id: Optional vacancy ID to rank candidates within a vacancy
        candidate_ids: Optional list of candidate IDs to rank
        qualification_level: Job qualification level (alta, media, baixa) affects K parameter
        limit: Maximum number of ranked results

    Returns:
        Ranked list of candidates with WRF scores
    """
    company_id = require_company_id_from_context(kwargs, "rank_candidates")

    logger.info(f"🏆 Ranking candidates with WRF (company: {company_id}, level: {qualification_level})")

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.domains.sourcing.services.wrf_service import wrf_dynamic_k_service
        from app.models.candidate import Candidate, VacancyCandidate

        async with AsyncSessionLocal() as db:
            query = select(Candidate)
            conditions = []

            if hasattr(Candidate, 'company_id'):
                conditions.append(Candidate.company_id == company_id)

            if candidate_ids:
                conditions.append(Candidate.id.in_([UUID(cid) for cid in candidate_ids]))

            if vacancy_id:
                query = query.join(
                    VacancyCandidate,
                    and_(
                        Candidate.id == VacancyCandidate.candidate_id,
                        VacancyCandidate.company_id == company_id
                    )
                ).where(VacancyCandidate.vacancy_id == UUID(vacancy_id))

            if conditions:
                query = query.where(and_(*conditions))

            query = query.limit(limit * 3)

            result = await db.execute(query)
            candidates = result.scalars().all()

            candidates_for_ranking = []
            for i, c in enumerate(candidates):
                es_rank = i + 1
                lia_score = getattr(c, 'lia_score', None) or 0
                sorted_by_score = sorted(candidates, key=lambda x: getattr(x, 'lia_score', 0) or 0, reverse=True)
                pgv_rank = next((idx + 1 for idx, sc in enumerate(sorted_by_score) if sc.id == c.id), i + 1)

                candidates_for_ranking.append({
                    "id": str(c.id),
                    "name": getattr(c, 'name', 'N/A'),
                    "email": getattr(c, 'email', None),
                    "seniority": getattr(c, 'seniority_level', None),
                    "location": getattr(c, 'location', None),
                    "status": getattr(c, 'status', None),
                    "lia_score": lia_score,
                    "wsi_score": getattr(c, 'wsi_score', None),
                    "skills": getattr(c, 'technical_skills', []) or [],
                    "es_rank": es_rank,
                    "pgv_rank": pgv_rank,
                })

            ranked = wrf_dynamic_k_service.rank_candidates(candidates_for_ranking, qualification_level)
            ranked = ranked[:limit]

            # WT-2022 P0.C: LGPD Art. 20 + EU AI Act Art. 13 audit trail
            # para ranking automatizado de candidatos via tool de sourcing.
            try:
                from app.shared.services.automated_decision_logger import (
                    PROTECTED_CRITERIA_PT,
                    log_automated_decision,
                )
                top_summary = [
                    {
                        "candidate_id": item.get("id"),
                        "rank": item.get("wrf_rank"),
                        "score": item.get("wrf_score"),
                    }
                    for item in ranked[:10]
                ]
                await log_automated_decision(
                    db=db,
                    company_id=company_id,
                    job_id=vacancy_id,
                    decision_type="candidate_ranking_wrf_tool",
                    ai_model_used="wrf_dynamic_k_service_deterministic",
                    explanation_text=(
                        f"Sourcing tool rank_candidates: {len(candidates_for_ranking)} candidatos "
                        f"rankeados (top {len(ranked)}) com qualification_level="
                        f"{qualification_level or 'media'}"
                        + (f" para vaga {vacancy_id}." if vacancy_id else ".")
                    ),
                    criteria_used=[
                        "es_rank",
                        "pgv_rank",
                        "lia_score",
                        "wsi_score",
                        "qualification_level",
                        "wrf_dynamic_k",
                    ],
                    criteria_ignored=PROTECTED_CRITERIA_PT,
                    review_eligible=True,
                    extra_metadata={
                        "qualification_level": qualification_level,
                        "vacancy_id": vacancy_id,
                        "candidate_ids_input": candidate_ids,
                        "total_input": len(candidates_for_ranking),
                        "total_output": len(ranked),
                        "top_10_ranked": top_summary,
                        "caller": "sourcing.tools.query_tools.rank_candidates",
                    },
                )
            except Exception as _audit_exc:  # noqa: BLE001 - fail-safe
                logger.warning(
                    "WT-2022 P0.C: rank_candidates tool audit log failed: %s",
                    _audit_exc, exc_info=True,
                )

            return {
                "success": True,
                "message": f"✅ {len(ranked)} candidatos rankeados com WRF.",
                "data": {
                    "total": len(ranked),
                    "qualification_level": qualification_level or "media",
                    "candidates": ranked,
                }
            }

    except Exception as e:
        logger.error(f"❌ Error ranking candidates: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao rankear candidatos: {str(e)}",
            "error": str(e)
        }


async def get_candidate_details(
    candidate_id: str,
    include_vacancies: bool = True,
    include_evaluations: bool = True,
    **kwargs
) -> dict[str, Any]:
    """
    Get detailed information about a specific candidate.
    
    Args:
        candidate_id: UUID of the candidate
        include_vacancies: Include vacancies the candidate is part of
        include_evaluations: Include WSI evaluations
        
    Returns:
        Detailed candidate information
    """
    company_id = require_company_id_from_context(kwargs, "get_candidate_details")
    
    logger.info(f"📋 Getting candidate details: {candidate_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Candidate).where(
                    and_(
                        Candidate.id == UUID(candidate_id),
                        Candidate.company_id == company_id
                    )
                )
            )
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found"
                }
            
            candidate_data = {
                "id": str(candidate.id),
                "name": getattr(candidate, 'name', 'N/A'),
                "email": getattr(candidate, 'email', None),
                "phone": getattr(candidate, 'phone', None),
                "linkedin": getattr(candidate, 'linkedin_url', None),
                "location": getattr(candidate, 'location', None),
                "seniority": getattr(candidate, 'seniority_level', None),
                "status": getattr(candidate, 'status', None),
                "lia_score": getattr(candidate, 'lia_score', None),
                "wsi_score": getattr(candidate, 'wsi_score', None),
                "fit_score": getattr(candidate, 'fit_score', None),
                "years_experience": getattr(candidate, 'years_experience', None),
                "skills": getattr(candidate, 'skills', []) or [],
                "languages": getattr(candidate, 'languages', []) or [],
                "education": getattr(candidate, 'education', []) or [],
                "experience": getattr(candidate, 'experience', []) or [],
                "available_immediately": getattr(candidate, 'available_immediately', None),
                "salary_expectation": getattr(candidate, 'salary_expectation', None),
                "created_at": candidate.created_at.isoformat() if hasattr(candidate, 'created_at') and candidate.created_at else None,
            }
            
            if include_vacancies:
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.candidate_id == UUID(candidate_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                vacancy_candidates = vc_result.scalars().all()
                candidate_data["vacancies"] = [
                    {
                        "vacancy_id": str(vc.vacancy_id),
                        "stage": getattr(vc, 'stage', None),
                        "status": getattr(vc, 'status', None),
                        "added_at": vc.created_at.isoformat() if hasattr(vc, 'created_at') and vc.created_at else None
                    }
                    for vc in vacancy_candidates
                ]
            
            return {
                "success": True,
                "message": f"✅ Detalhes do candidato {candidate_data['name']}",
                "data": candidate_data
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting candidate details: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar detalhes do candidato: {str(e)}",
            "error": str(e)
        }


async def get_candidate_stats(
    job_id: str | None = None,
    period: str | None = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get statistics about candidates (quality, distribution, engagement).
    
    Args:
        job_id: Optional job ID to filter candidates
        period: Time period (week, month, quarter)
        
    Returns:
        Candidate statistics including quality metrics, distribution
    """
    company_id = require_company_id_from_context(kwargs, "get_candidate_stats")
    
    logger.info(f"📊 Getting candidate stats (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
        datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            if job_id:
                query = select(Candidate).join(
                    VacancyCandidate,
                    and_(
                        Candidate.id == VacancyCandidate.candidate_id,
                        VacancyCandidate.company_id == company_id
                    )
                ).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        Candidate.company_id == company_id
                    )
                )
            else:
                query = select(Candidate)
                if hasattr(Candidate, 'company_id'):
                    query = query.where(Candidate.company_id == company_id)
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            total = len(candidates)
            
            scores = [c.lia_score for c in candidates if hasattr(c, 'lia_score') and c.lia_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            high_quality = sum(1 for s in scores if s >= 80)
            
            seniority_dist = {}
            for c in candidates:
                sen = getattr(c, 'seniority_level', 'Indefinido') or 'Indefinido'
                seniority_dist[sen] = seniority_dist.get(sen, 0) + 1
            
            available_now = sum(1 for c in candidates if getattr(c, 'available_immediately', False))
            
            skills_count = {}
            for c in candidates:
                for skill in (getattr(c, 'technical_skills', []) or []):
                    skills_count[skill] = skills_count.get(skill, 0) + 1
            
            top_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            stats = {
                "total_candidates": total,
                "period": period,
                "quality": {
                    "avg_lia_score": round(avg_score, 1),
                    "high_quality_count": high_quality,
                    "high_quality_percentage": f"{(high_quality / total * 100):.1f}%" if total > 0 else "0%"
                },
                "distribution": {
                    "by_seniority": seniority_dist,
                    "available_immediately": available_now,
                    "availability_rate": f"{(available_now / total * 100):.1f}%" if total > 0 else "0%"
                },
                "skills": {
                    "top_10": [{"skill": s, "count": c} for s, c in top_skills]
                }
            }
            
            return {
                "success": True,
                "message": f"✅ Estatísticas de {total} candidatos",
                "data": stats
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting candidate stats: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar estatísticas: {str(e)}",
            "error": str(e)
        }


async def get_candidate_history(
    candidate_id: str | None = None,
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get candidate participation history across multiple processes.
    
    Args:
        candidate_id: Optional UUID of specific candidate
        job_id: Optional UUID of job to analyze its candidates' history
        
    Returns:
        History metrics including reapplication rates and process counts
    """
    company_id = require_company_id_from_context(kwargs, "get_candidate_history")
    
    logger.info(f"📜 Getting candidate history (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            if candidate_id:
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.candidate_id == UUID(candidate_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                participations = vc_result.scalars().all()
                
                return {
                    "success": True,
                    "message": f"✅ Histórico do candidato {candidate_id}",
                    "data": {
                        "candidate_id": candidate_id,
                        "total_processes": len(participations),
                        "processes": [
                            {
                                "vacancy_id": str(p.vacancy_id),
                                "stage": getattr(p, 'stage', None),
                                "status": getattr(p, 'status', None),
                                "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') and p.created_at else None
                            }
                            for p in participations
                        ],
                        "is_returning_candidate": len(participations) > 1
                    }
                }
            
            conditions = [VacancyCandidate.company_id == company_id]
            
            if job_id:
                job_vc_result = await db.execute(
                    select(VacancyCandidate.candidate_id).where(
                        and_(
                            VacancyCandidate.vacancy_id == UUID(job_id),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                candidate_ids = [row[0] for row in job_vc_result.all()]
                
                if candidate_ids:
                    conditions.append(VacancyCandidate.candidate_id.in_(candidate_ids))
                else:
                    return {
                        "success": True,
                        "message": f"✅ Nenhum candidato encontrado na vaga {job_id}",
                        "data": {
                            "job_id": job_id,
                            "candidates_with_prior_processes": 0,
                            "reapplication_rate": 0.0,
                            "average_processes_per_candidate": 0.0
                        }
                    }
            
            vc_result = await db.execute(
                # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
                select(VacancyCandidate).where(and_(*conditions))
            )
            all_participations = vc_result.scalars().all()
            
            candidate_process_count: dict[str, int] = {}
            for vc in all_participations:
                cid = str(vc.candidate_id)
                candidate_process_count[cid] = candidate_process_count.get(cid, 0) + 1
            
            total_candidates = len(candidate_process_count)
            candidates_with_multiple = sum(1 for count in candidate_process_count.values() if count > 1)
            total_processes = sum(candidate_process_count.values())
            
            reapplication_rate = (candidates_with_multiple / total_candidates * 100) if total_candidates > 0 else 0
            avg_processes = (total_processes / total_candidates) if total_candidates > 0 else 0
            
            return {
                "success": True,
                "message": "✅ Histórico de participação de candidatos",
                "data": {
                    "job_filter": job_id,
                    "total_candidates_analyzed": total_candidates,
                    "candidates_with_prior_processes": candidates_with_multiple,
                    "reapplication_rate": round(reapplication_rate, 2),
                    "average_processes_per_candidate": round(avg_processes, 2),
                    "top_recurring_candidates": [
                        {"candidate_id": cid, "process_count": count}
                        for cid, count in sorted(candidate_process_count.items(), key=lambda x: x[1], reverse=True)[:10]
                        if count > 1
                    ]
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting candidate history: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar histórico de candidatos: {str(e)}",
            "error": str(e)
        }


async def get_talent_quality(
    period: str = "month",
    min_score: float | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get talent quality metrics including average scores and score distribution.
    
    Args:
        period: Time period (week, month, quarter)
        min_score: Optional minimum score filter
        
    Returns:
        Quality metrics including average_lia_score, average_wsi_score, 
        high_fit_percentage, and score_distribution
    """
    company_id = require_company_id_from_context(kwargs, "get_talent_quality")
    
    logger.info(f"📊 Getting talent quality metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            conditions = [VacancyCandidate.company_id == company_id]
            if hasattr(VacancyCandidate, 'created_at'):
                conditions.append(VacancyCandidate.created_at >= start_date)
            
            query = select(Candidate).join(
                VacancyCandidate,
                and_(
                    Candidate.id == VacancyCandidate.candidate_id,
                    Candidate.company_id == company_id
                )
            ).where(and_(*conditions))
            
            if min_score is not None:
                query = query.where(Candidate.lia_score >= min_score)
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            total_candidates = len(candidates)
            
            if total_candidates == 0:
                return {
                    "success": True,
                    "message": f"📊 Nenhum candidato encontrado no período ({period})",
                    "data": {
                        "period": period,
                        "total_candidates": 0,
                        "average_lia_score": 0,
                        "average_wsi_score": 0,
                        "high_fit_percentage": 0,
                        "score_distribution": {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
                    }
                }
            
            lia_scores = [c.lia_score for c in candidates if c.lia_score is not None]
            wsi_scores = [getattr(c, 'skills_match_percentage', None) for c in candidates if getattr(c, 'skills_match_percentage', None) is not None]
            
            avg_lia = sum(lia_scores) / len(lia_scores) if lia_scores else 0
            avg_wsi = sum(wsi_scores) / len(wsi_scores) if wsi_scores else 0
            
            high_fit_count = sum(1 for s in lia_scores if s >= 80)
            high_fit_pct = (high_fit_count / len(lia_scores) * 100) if lia_scores else 0
            
            distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
            for score in lia_scores:
                if score <= 20:
                    distribution["0-20"] += 1
                elif score <= 40:
                    distribution["21-40"] += 1
                elif score <= 60:
                    distribution["41-60"] += 1
                elif score <= 80:
                    distribution["61-80"] += 1
                else:
                    distribution["81-100"] += 1
            
            return {
                "success": True,
                "message": f"✅ Métricas de qualidade de talentos ({period})",
                "data": {
                    "period": period,
                    "total_candidates": total_candidates,
                    "candidates_with_lia_score": len(lia_scores),
                    "candidates_with_wsi_score": len(wsi_scores),
                    "average_lia_score": round(avg_lia, 2),
                    "average_wsi_score": round(avg_wsi, 2),
                    "high_fit_percentage": round(high_fit_pct, 2),
                    "high_fit_count": high_fit_count,
                    "score_distribution": distribution
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting talent quality metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de qualidade: {str(e)}",
            "error": str(e)
        }


async def get_talent_engagement(
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get talent engagement metrics including response rates.
    
    Args:
        period: Time period (week, month, quarter)
        
    Returns:
        Engagement metrics including response_rate, average_response_time_hours,
        contacted_count, responded_count
    """
    company_id = require_company_id_from_context(kwargs, "get_talent_engagement")
    
    logger.info(f"📬 Getting talent engagement metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        
        period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            query = select(VacancyCandidate).where(
                and_(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.created_at >= start_date
                )
            )
            
            result = await db.execute(query)
            vacancy_candidates = result.scalars().all()
            
            contacted_statuses = {"contacted", "outreach_sent", "in_contact"}
            responded_statuses = {"in_process", "screening", "interview", "responded", "interested"}
            in_process_stages = {"Triagem", "Entrevista RH", "Entrevista Técnica", "Entrevista Final", "Oferta", "Contratado"}
            
            contacted_count = 0
            responded_count = 0
            response_times = []
            
            for vc in vacancy_candidates:
                status = getattr(vc, 'status', '').lower() if getattr(vc, 'status', None) else ''
                stage = getattr(vc, 'stage', '') or ''
                
                if status in contacted_statuses or stage in in_process_stages:
                    contacted_count += 1
                    
                if status in responded_statuses or stage in in_process_stages:
                    responded_count += 1
                    
                    if hasattr(vc, 'created_at') and hasattr(vc, 'updated_at'):
                        if vc.created_at and vc.updated_at and vc.updated_at > vc.created_at:
                            response_time = (vc.updated_at - vc.created_at).total_seconds() / 3600
                            if response_time > 0 and response_time < 720:
                                response_times.append(response_time)
            
            contacted_count = max(contacted_count, responded_count)
            response_rate = (responded_count / contacted_count * 100) if contacted_count > 0 else 0
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "success": True,
                "message": f"✅ Métricas de engajamento de talentos ({period})",
                "data": {
                    "period": period,
                    "total_candidates_in_pipeline": len(vacancy_candidates),
                    "contacted_count": contacted_count,
                    "responded_count": responded_count,
                    "response_rate": round(response_rate, 2),
                    "average_response_time_hours": round(avg_response_time, 2),
                    "response_samples": len(response_times)
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting talent engagement metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de engajamento: {str(e)}",
            "error": str(e)
        }


async def get_talent_availability(
    **kwargs
) -> dict[str, Any]:
    """
    Get talent availability metrics including immediate availability and salary expectations.
    
    Returns:
        Availability metrics including immediately_available_percentage,
        average_salary_expectation, availability_by_seniority
    """
    company_id = require_company_id_from_context(kwargs, "get_talent_availability")
    
    logger.info(f"📅 Getting talent availability metrics (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        async with AsyncSessionLocal() as db:
            query = select(Candidate).join(
                VacancyCandidate,
                and_(
                    Candidate.id == VacancyCandidate.candidate_id,
                    Candidate.company_id == company_id
                )
            ).where(VacancyCandidate.company_id == company_id)
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            total = len(candidates)
            
            if total == 0:
                return {
                    "success": True,
                    "message": "📅 Nenhum candidato encontrado no pipeline",
                    "data": {
                        "total_candidates": 0,
                        "immediately_available_percentage": 0,
                        "average_salary_expectation": 0,
                        "availability_by_seniority": {}
                    }
                }
            
            immediately_available = sum(
                1 for c in candidates 
                if getattr(c, 'is_open_to_work', False) or getattr(c, 'is_remote', False)
            )
            
            salary_expectations = []
            for c in candidates:
                salary = (
                    getattr(c, 'desired_salary_max', None) or 
                    getattr(c, 'desired_salary_min', None) or
                    getattr(c, 'salary_expectation_clt', None) or
                    getattr(c, 'salary_expectation_pj', None)
                )
                if salary and salary > 0:
                    salary_expectations.append(salary)
            
            avg_salary = sum(salary_expectations) / len(salary_expectations) if salary_expectations else 0
            
            by_seniority = {}
            for c in candidates:
                seniority = getattr(c, 'seniority_level', 'Não informado') or 'Não informado'
                if seniority not in by_seniority:
                    by_seniority[seniority] = {"total": 0, "available": 0}
                by_seniority[seniority]["total"] += 1
                if getattr(c, 'is_open_to_work', False) or getattr(c, 'is_remote', False):
                    by_seniority[seniority]["available"] += 1
            
            for seniority in by_seniority:
                total_s = by_seniority[seniority]["total"]
                avail_s = by_seniority[seniority]["available"]
                by_seniority[seniority]["percentage"] = round(avail_s / total_s * 100, 2) if total_s > 0 else 0
            
            return {
                "success": True,
                "message": "✅ Métricas de disponibilidade de talentos",
                "data": {
                    "total_candidates": total,
                    "immediately_available_count": immediately_available,
                    "immediately_available_percentage": round(immediately_available / total * 100, 2),
                    "salary_data_count": len(salary_expectations),
                    "average_salary_expectation": round(avg_salary, 2),
                    "availability_by_seniority": by_seniority
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting talent availability metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de disponibilidade: {str(e)}",
            "error": str(e)
        }


async def get_diversity_metrics(
    job_id: str | None = None,
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get diversity and inclusion metrics for candidates.
    
    Args:
        job_id: Optional UUID of job to filter candidates
        period: Time period (month, quarter, year)
        
    Returns:
        Diversity metrics including gender, ethnicity, PCD, and age distributions
    """
    company_id = require_company_id_from_context(kwargs, "get_diversity_metrics")
    
    logger.info(f"🌈 Getting diversity metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        period_days = {
            "month": 30,
            "quarter": 90,
            "year": 365
        }.get(period, 30)
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            query = select(Candidate)
            conditions = [Candidate.created_at >= start_date]
            
            if hasattr(Candidate, 'company_id'):
                conditions.append(Candidate.company_id == company_id)
            
            if job_id:
                query = query.join(
                    VacancyCandidate,
                    and_(
                        Candidate.id == VacancyCandidate.candidate_id,
                        VacancyCandidate.vacancy_id == UUID(job_id)
                    )
                )
            
            query = query.where(and_(*conditions))
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            total_candidates = len(candidates)
            
            gender_dist: dict[str, int] = {}
            ethnicity_dist: dict[str, int] = {}
            pcd_count = 0
            age_dist: dict[str, int] = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "55+": 0}
            
            today = datetime.utcnow().date()
            
            for c in candidates:
                gender = getattr(c, 'gender', None) or 'Não informado'
                gender_dist[gender] = gender_dist.get(gender, 0) + 1
                
                ethnicity = getattr(c, 'diversity_race_ethnicity', None) or 'Não informado'
                ethnicity_dist[ethnicity] = ethnicity_dist.get(ethnicity, 0) + 1
                
                if getattr(c, 'diversity_disability', False):
                    pcd_count += 1
                
                birth_date = getattr(c, 'date_of_birth', None)
                if birth_date:
                    try:
                        if isinstance(birth_date, str):
                            birth_date = datetime.fromisoformat(birth_date).date()
                        age = (today - birth_date).days // 365
                        if age < 26:
                            age_dist["18-25"] += 1
                        elif age < 36:
                            age_dist["26-35"] += 1
                        elif age < 46:
                            age_dist["36-45"] += 1
                        elif age < 56:
                            age_dist["46-55"] += 1
                        else:
                            age_dist["55+"] += 1
                    except (ValueError, TypeError):
                        pass
            
            pcd_percentage = (pcd_count / total_candidates * 100) if total_candidates > 0 else 0
            
            return {
                "success": True,
                "message": f"✅ Métricas de diversidade ({period})",
                "data": {
                    "period": period,
                    "job_filter": job_id,
                    "total_candidates_analyzed": total_candidates,
                    "gender_distribution": gender_dist,
                    "ethnicity_distribution": ethnicity_dist,
                    "pcd_percentage": round(pcd_percentage, 2),
                    "pcd_count": pcd_count,
                    "age_distribution": age_dist
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting diversity metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de diversidade: {str(e)}",
            "error": str(e)
        }


async def get_market_benchmarks(
    job_title: str | None = None,
    industry: str | None = None,
    region: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get market comparison benchmarks for recruitment metrics.
    
    Args:
        job_title: Job title to benchmark (optional)
        industry: Industry for comparison (optional)
        region: Geographic region (optional)
        
    Returns:
        Market comparison data including salary competitiveness and time-to-fill comparison
    """
    company_id = require_company_id_from_context(kwargs, "get_market_benchmarks")
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"🏆 Getting market benchmarks (company: {company_id}, title: {job_title})")
    
    try:
        from sqlalchemy import and_, func, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            start_date = datetime.utcnow() - timedelta(days=90)
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.created_at >= start_date
            ]
            
            jobs_result = await db.execute(
                # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
                select(JobVacancy).where(and_(*conditions))
            )
            jobs = jobs_result.scalars().all()
            
            closed_jobs = [j for j in jobs if j.status == "Fechada" and j.closed_at]
            
            if closed_jobs:
                ttf_values = [(j.closed_at - j.created_at).days for j in closed_jobs if j.created_at]
                company_avg_ttf = sum(ttf_values) / len(ttf_values) if ttf_values else 35
            else:
                company_avg_ttf = 35
            
            
            market_avg_ttf = 42
            market_avg_salary_range = {"min": 8000, "max": 15000, "median": 11500}
            market_position = "competitive"
            
            if job_title:
                title_lower = job_title.lower()
                if "senior" in title_lower or "sênior" in title_lower:
                    market_avg_salary_range = {"min": 15000, "max": 28000, "median": 21000}
                    market_avg_ttf = 50
                elif "junior" in title_lower or "júnior" in title_lower:
                    market_avg_salary_range = {"min": 4000, "max": 8000, "median": 6000}
                    market_avg_ttf = 30
                elif "tech lead" in title_lower or "arquiteto" in title_lower:
                    market_avg_salary_range = {"min": 20000, "max": 35000, "median": 27000}
                    market_avg_ttf = 60
            
            if region:
                if "são paulo" in region.lower() or "sp" in region.lower():
                    market_avg_salary_range = {k: v * 1.2 for k, v in market_avg_salary_range.items()}
                elif "remoto" in region.lower():
                    market_avg_salary_range = {k: v * 1.1 for k, v in market_avg_salary_range.items()}
            
            ttf_comparison = company_avg_ttf - market_avg_ttf
            if ttf_comparison < -5:
                ttf_status = "faster_than_market"
            elif ttf_comparison > 5:
                ttf_status = "slower_than_market"
            else:
                ttf_status = "at_market_rate"
            
            total_candidates = 0
            if jobs:
                job_ids = [j.id for j in jobs]
                vc_result = await db.execute(
                    select(func.count(VacancyCandidate.id)).where(
                        VacancyCandidate.vacancy_id.in_(job_ids)
                    )
                )
                total_candidates = vc_result.scalar() or 0
            
            candidates_per_job = total_candidates / len(jobs) if jobs else 0
            market_avg_candidates = 45
            
            return {
                "success": True,
                "message": "✅ Benchmarks de mercado obtidos",
                "data": {
                    "filters": {
                        "job_title": job_title,
                        "industry": industry,
                        "region": region
                    },
                    "company_vs_market": {
                        "company_avg_time_to_fill": round(company_avg_ttf, 1),
                        "market_avg_time_to_fill": market_avg_ttf,
                        "company_candidates_per_job": round(candidates_per_job, 1),
                        "market_avg_candidates_per_job": market_avg_candidates
                    },
                    "salary_competitiveness": {
                        "market_salary_range": market_avg_salary_range,
                        "currency": "BRL",
                        "note": "Dados baseados em estimativas de mercado"
                    },
                    "time_to_fill_comparison": {
                        "difference_days": round(ttf_comparison, 1),
                        "status": ttf_status,
                        "percentile": 50 + int(ttf_comparison * -2)
                    },
                    "market_position": market_position,
                    "data_source": "simulated",
                    "recommendation": "Integre com APIs de mercado (Glassdoor, LinkedIn Salary) para dados reais"
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting market benchmarks: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar benchmarks de mercado: {str(e)}",
            "error": str(e)
        }




async def _wrap_search_candidates(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await search_candidates(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_candidate_details(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_candidate_details(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_candidate_stats(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_candidate_stats(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_candidate_history(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_candidate_history(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_talent_quality(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_talent_quality(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_talent_engagement(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_talent_engagement(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_talent_availability(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_talent_availability(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_diversity_metrics(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_diversity_metrics(**normalize_wrapper_kwargs(kwargs))




async def _wrap_get_market_benchmarks(**kwargs):
    """Canonical wrapper (2026-05-24-v3 normalize_wrapper_kwargs).

    Delegates via ``normalize_wrapper_kwargs`` to handle both dispatch paths:
    (A) Global ToolExecutor injects ``_context``; (B) tool_handler decorator
    injects ``company_id``/``user_id``. See app/tools/context_helpers.py.
    """
    return await get_market_benchmarks(**normalize_wrapper_kwargs(kwargs))


def register_sourcing_query_tools() -> None:
    """Register sourcing-domain query tools in the tool registry."""
    
    tool_registry.register(ToolDefinition(
        name="search_candidates",
        description="Buscar candidatos com filtros como skills, experiência, senioridade, score LIA, localização. Use para encontrar candidatos específicos ou responder perguntas sobre a base de candidatos.",
        parameters_schema={
            "type": "object",
            "properties": {
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills para filtrar"},
                "min_experience_years": {"type": "integer", "description": "Anos mínimos de experiência"},
                "max_experience_years": {"type": "integer", "description": "Anos máximos de experiência"},
                "seniority": {"type": "string", "enum": ["Júnior", "Pleno", "Sênior", "Especialista"], "description": "Nível de senioridade"},
                "min_score": {"type": "number", "description": "Score mínimo LIA/WSI (0-100)"},
                "status": {"type": "string", "description": "Status do candidato"},
                "available_immediately": {"type": "boolean", "description": "Disponibilidade imediata"},
                "location": {"type": "string", "description": "Localização"},
                "limit": {"type": "integer", "default": 20, "description": "Número máximo de resultados"}
            }
        },
        handler=_wrap_search_candidates,
        allowed_agents=["recruiter_assistant", "sourcing", "cv_screening", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_candidate_details",
        description="Obter detalhes completos de um candidato específico incluindo experiência, skills, avaliações e vagas em que participa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "include_vacancies": {"type": "boolean", "default": True, "description": "Incluir vagas do candidato"},
                "include_evaluations": {"type": "boolean", "default": True, "description": "Incluir avaliações WSI"}
            },
            "required": ["candidate_id"]
        },
        handler=_wrap_get_candidate_details,
        allowed_agents=["recruiter_assistant", "sourcing", "cv_screening", "wsi_evaluator", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_candidate_stats",
        description="Obter estatísticas agregadas sobre candidatos: qualidade média, distribuição por senioridade, skills mais comuns.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar candidatos"},
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=_wrap_get_candidate_stats,
        allowed_agents=["recruiter_assistant", "sourcing", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_candidate_history",
        description="Obter histórico de participação de candidatos em processos: taxa de recandidatura, média de processos por candidato, candidatos recorrentes.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato para ver histórico individual (opcional)"},
                "job_id": {"type": "string", "description": "UUID da vaga para analisar histórico dos candidatos dessa vaga (opcional)"}
            }
        },
        handler=_wrap_get_candidate_history,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "sourcing", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_talent_quality",
        description="Obter métricas de qualidade dos talentos: score médio LIA, score WSI, percentual de alta aderência (>80%), distribuição de scores.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month", "description": "Período de análise"},
                "min_score": {"type": "number", "description": "Score mínimo para filtrar candidatos"}
            }
        },
        handler=_wrap_get_talent_quality,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_talent_engagement",
        description="Obter métricas de engajamento dos talentos: taxa de resposta, tempo médio de resposta, candidatos contatados vs respondidos.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=_wrap_get_talent_engagement,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_talent_availability",
        description="Obter métricas de disponibilidade dos talentos: percentual disponível imediatamente, expectativa salarial média, disponibilidade por senioridade.",
        parameters_schema={
            "type": "object",
            "properties": {}
        },
        handler=_wrap_get_talent_availability,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "sourcing", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_diversity_metrics",
        description="Obter métricas de diversidade e inclusão: distribuição por gênero, etnia, PCD e faixa etária dos candidatos.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar candidatos (opcional)"},
                "period": {"type": "string", "enum": ["month", "quarter", "year"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=_wrap_get_diversity_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_market_benchmarks",
        description="Obter benchmarks de mercado para comparação: competitividade salarial, tempo de contratação vs mercado, posição competitiva da empresa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Título da vaga para benchmark (opcional)"},
                "industry": {"type": "string", "description": "Indústria para comparação (opcional)"},
                "region": {"type": "string", "description": "Região geográfica (opcional)"}
            }
        },
        handler=_wrap_get_market_benchmarks,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    logger.info("✅ Registered 9 sourcing query tools")



# ---------------------------------------------------------------------------
# compare_candidates — multi-tenant candidate comparison tool (Security P0)
# ---------------------------------------------------------------------------

async def compare_candidates(
    candidate_ids: "list[str]",
    company_id: "str | None" = None,  # ignored; always overridden by _context
    **kwargs,
) -> "dict":
    """Compare two or more candidates by their profile data.

    Multi-tenancy: the *company_id* kwarg is intentionally ignored so that
    a prompt-injected caller cannot target another tenant's data.  The only
    authoritative source is the ``_context`` object injected by the tool
    executor middleware.

    Args:
        candidate_ids: List of candidate UUID strings to compare.
        company_id: Silently ignored.  Caller-supplied value is never used.
        **kwargs: May contain ``_context`` with the authenticated tenant context.

    Returns:
        Dict with ``success``, ``candidates`` list, and optional ``error`` key.
    """
    context = _extract_context(kwargs)

    # Fail-fast: no context = no tenant = hard stop (never guess a tenant).
    tenant_company_id: "str | None" = getattr(context, "company_id", None) if context else None
    if not tenant_company_id:
        return {
            "success": False,
            "error": "missing_tenant_context",
            "candidates": [],
        }

    if not candidate_ids:
        return {"success": False, "error": "no_candidate_ids", "candidates": []}

    # P0-W4-07: consent gate ai_comparison — verificar por cada candidato (fail-closed, LGPD Art. 7 §III)
    try:
        from app.core.database import AsyncSessionLocal as _CSL_compare
        from app.domains.lgpd.services.granular_consent_consumers import check_ai_comparison

        blocked_ids: list[str] = []
        async with _CSL_compare() as _consent_db:
            for _cid in candidate_ids:
                if not await check_ai_comparison(
                    candidate_id=str(_cid),
                    company_id=tenant_company_id,
                    db=_consent_db,
                ):
                    blocked_ids.append(str(_cid))
        if blocked_ids:
            logger.info(
                "[ConsentGate] ai_comparison bloqueado para candidatos %s (company=%s)",
                blocked_ids, tenant_company_id,
            )
            candidate_ids = [c for c in candidate_ids if str(c) not in blocked_ids]
        if not candidate_ids:
            return {
                "success": False,
                "error": "consent_revoked_ai_comparison",
                "candidates": [],
                "blocked_candidate_count": len(blocked_ids),
            }
    except Exception as _ce:
        logger.warning("[ConsentGate] ai_comparison check failed (fail-closed): %s", _ce)
        return {"success": False, "error": "consent_check_failed", "candidates": []}

    try:
        from sqlalchemy import text as sa_text
        from app.core.database import AsyncSessionLocal

        placeholders = ", ".join(f":id_{i}" for i in range(len(candidate_ids)))
        params: dict = {"_company_id": tenant_company_id}
        for i, cid in enumerate(candidate_ids):
            params[f"id_{i}"] = cid

        sql = sa_text(
            f"SELECT id, name, email, status, company_id "
            f"FROM candidates "
            f"WHERE id IN ({placeholders}) "
            f"AND company_id = :_company_id"
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(sql, params)
            rows = result.mappings().all()

        candidates = [dict(r) for r in rows]
        if not candidates:
            return {"success": False, "error": "Candidatos nao encontrados.", "candidates": []}

        return {"success": True, "candidates": candidates}

    except Exception as exc:
        logger.error("[compare_candidates] DB error: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc), "candidates": []}
