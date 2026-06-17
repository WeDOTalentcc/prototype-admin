"""Intelligence tools: ML predictions, conversion patterns, smart alerts."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ._base import analytics_db, error_response, extract_context, success_response
from app.tools.context_helpers import require_company_id_from_context

logger = logging.getLogger(__name__)


async def get_ml_predictions(
    candidate_id: str | None = None,
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get ML-based predictions for candidate success.

    Args:
        candidate_id: UUID of candidate to predict (optional)
        job_id: UUID of job for context (optional)

    Returns:
        ML predictions including acceptance probability, retention risk, and performance prediction
    """
    company_id = require_company_id_from_context(kwargs, "get_ml_predictions")

    logger.info(f"🤖 Getting ML predictions (company: {company_id}, candidate: {candidate_id}, job: {job_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        async with analytics_db() as db:
            predictions = []

            if candidate_id:
                candidate_result = await db.execute(
                    select(Candidate).where(
                        and_(
                            Candidate.id == UUID(candidate_id),
                            Candidate.company_id == company_id
                        )
                    )
                )
                candidate = candidate_result.scalar_one_or_none()

                if not candidate:
                    return {"success": False, "message": f"❌ Candidato não encontrado: {candidate_id}", "error": "candidate_not_found"}

                lia_score = getattr(candidate, 'lia_score', None) or 70
                skills_match = getattr(candidate, 'skills_match_percentage', None) or 65
                years_exp = getattr(candidate, 'years_of_experience', None) or 3

                base_acceptance = 0.6
                base_acceptance += (lia_score - 50) / 100
                base_acceptance += (skills_match - 50) / 200
                acceptance_probability = max(0.2, min(0.95, base_acceptance))

                base_retention = 0.75
                if years_exp and years_exp > 5:
                    base_retention += 0.1
                elif years_exp and years_exp < 2:
                    base_retention -= 0.1
                retention_risk_score = 1 - base_retention

                performance_base = 3.0
                performance_base += (lia_score - 50) / 50
                performance_base += (skills_match - 50) / 100
                performance_prediction = max(1.0, min(5.0, performance_base))

                if lia_score >= 80 and acceptance_probability >= 0.7:
                    recommendation = "Alta prioridade - Candidato com excelente perfil"
                elif lia_score >= 60 and acceptance_probability >= 0.5:
                    recommendation = "Boa opção - Avançar no processo"
                elif retention_risk_score > 0.4:
                    recommendation = "Atenção - Risco de rotatividade elevado"
                else:
                    recommendation = "Avaliar com cautela - Considerar outros candidatos"

                predictions.append({
                    "candidate_id": candidate_id,
                    "candidate_name": getattr(candidate, 'name', 'N/A'),
                    "acceptance_probability": round(acceptance_probability, 3),
                    "retention_risk_score": round(retention_risk_score, 3),
                    "performance_prediction": round(performance_prediction, 2),
                    "performance_scale": "1-5",
                    "recommendation": recommendation,
                    "input_scores": {
                        "lia_score": lia_score,
                        "skills_match": skills_match,
                        "years_experience": years_exp
                    }
                })

            if job_id:
                job_result = await db.execute(
                    select(JobVacancy).where(
                        and_(
                            JobVacancy.id == UUID(job_id),
                            JobVacancy.company_id == company_id
                        )
                    )
                )
                job = job_result.scalar_one_or_none()

                if job:
                    # TENANT-EXEMPT: job tenant-gated em L101-105 acima (JobVacancy.company_id == company_id); vc atrelado ao vacancy_id derivado da query tenant-safe — defense-in-depth implícita
                    vc_result = await db.execute(
                        select(VacancyCandidate, Candidate).join(
                            Candidate, VacancyCandidate.candidate_id == Candidate.id
                        ).where(VacancyCandidate.vacancy_id == UUID(job_id))
                    )
                    vacancy_candidates = vc_result.all()

                    for vc, c in vacancy_candidates[:10]:
                        if str(c.id) == candidate_id:
                            continue

                        lia_score = getattr(c, 'lia_score', None) or 70
                        skills_match = getattr(c, 'skills_match_percentage', None) or 65

                        base_acceptance = 0.6
                        base_acceptance += (lia_score - 50) / 100
                        acceptance_probability = max(0.2, min(0.95, base_acceptance))

                        base_retention = 0.75
                        retention_risk_score = 1 - base_retention

                        performance_prediction = 3.0 + (lia_score - 50) / 50
                        performance_prediction = max(1.0, min(5.0, performance_prediction))

                        predictions.append({
                            "candidate_id": str(c.id),
                            "candidate_name": getattr(c, 'name', 'N/A'),
                            "acceptance_probability": round(acceptance_probability, 3),
                            "retention_risk_score": round(retention_risk_score, 3),
                            "performance_prediction": round(performance_prediction, 2),
                            "performance_scale": "1-5"
                        })

            if not predictions:
                return success_response("📊 Nenhum candidato para predição. Forneça candidate_id ou job_id.", {
                    "predictions": [],
                    "model_info": {
                        "version": "1.0-heuristic",
                        "note": "Modelo baseado em heurísticas. ML real em desenvolvimento."
                    }
                })

            return success_response(f"✅ Predições ML geradas para {len(predictions)} candidato(s)", {
                "predictions": predictions,
                "model_info": {
                    "version": "1.0-heuristic",
                    "confidence_level": "medium",
                    "note": "Predições baseadas em scores existentes. Modelo ML completo em desenvolvimento."
                }
            })

    except Exception as e:
        logger.error(f"❌ Error getting ML predictions: {e}", exc_info=True)
        return error_response(f"❌ Erro ao gerar predições ML: {str(e)}", e)


async def get_conversion_patterns(
    period: str = "month",
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Analyze source and profile conversion patterns.

    Args:
        period: Time period for analysis (month, quarter, year)
        job_id: Optional job ID to filter analysis

    Returns:
        Conversion patterns including top converting profiles, efficient sources, and funnel data
    """
    company_id = require_company_id_from_context(kwargs, "get_conversion_patterns")

    logger.info(f"🔄 Getting conversion patterns (company: {company_id}, period: {period})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate, VacancyCandidate

        period_days = {"month": 30, "quarter": 90, "year": 365}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
            conditions = [
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.created_at >= start_date
            ]

            if job_id:
                conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))

            vc_result = await db.execute(
                select(VacancyCandidate, Candidate).join(
                    Candidate,
                    and_(
                        VacancyCandidate.candidate_id == Candidate.id,
                        Candidate.company_id == company_id
                    )
                ).where(and_(*conditions))
            )
            vacancy_candidates = vc_result.all()

            source_stats = {}
            seniority_stats = {}
            stage_funnel = {
                "Triagem": 0,
                "Entrevista RH": 0,
                "Entrevista Técnica": 0,
                "Entrevista Final": 0,
                "Oferta": 0,
                "Contratado": 0
            }

            for vc, c in vacancy_candidates:
                source = getattr(c, 'source', 'desconhecido') or 'desconhecido'
                seniority = getattr(c, 'seniority_level', 'Não especificado') or 'Não especificado'
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'

                if source not in source_stats:
                    source_stats[source] = {"total": 0, "hired": 0, "advanced": 0}
                source_stats[source]["total"] += 1
                if stage in ["Contratado", "hired"]:
                    source_stats[source]["hired"] += 1
                if stage in ["Entrevista RH", "Entrevista Técnica", "Entrevista Final", "Oferta", "Contratado", "hired"]:
                    source_stats[source]["advanced"] += 1

                if seniority not in seniority_stats:
                    seniority_stats[seniority] = {"total": 0, "hired": 0}
                seniority_stats[seniority]["total"] += 1
                if stage in ["Contratado", "hired"]:
                    seniority_stats[seniority]["hired"] += 1

                if stage in stage_funnel:
                    stage_funnel[stage] += 1

            most_efficient_sources = []
            for source, stats in source_stats.items():
                if stats["total"] > 0:
                    conversion_rate = stats["hired"] / stats["total"] * 100
                    advancement_rate = stats["advanced"] / stats["total"] * 100
                    most_efficient_sources.append({
                        "source": source,
                        "total_candidates": stats["total"],
                        "hired": stats["hired"],
                        "conversion_rate": round(conversion_rate, 2),
                        "advancement_rate": round(advancement_rate, 2)
                    })
            most_efficient_sources.sort(key=lambda x: x["conversion_rate"], reverse=True)

            top_converting_profiles = []
            for seniority, stats in seniority_stats.items():
                if stats["total"] > 0:
                    conversion_rate = stats["hired"] / stats["total"] * 100
                    top_converting_profiles.append({
                        "seniority": seniority,
                        "total_candidates": stats["total"],
                        "hired": stats["hired"],
                        "conversion_rate": round(conversion_rate, 2)
                    })
            top_converting_profiles.sort(key=lambda x: x["conversion_rate"], reverse=True)

            total_candidates = len(vacancy_candidates)
            conversion_funnel = {}
            for stage, count in stage_funnel.items():
                conversion_funnel[stage] = {
                    "count": count,
                    "percentage": round(count / total_candidates * 100, 2) if total_candidates > 0 else 0
                }

            return success_response(f"✅ Análise de conversão ({period})", {
                "period": period,
                "job_filter": job_id,
                "total_candidates_analyzed": total_candidates,
                "top_converting_profiles": top_converting_profiles[:5],
                "most_efficient_sources": most_efficient_sources[:5],
                "conversion_funnel": conversion_funnel,
                "insights": {
                    "best_source": most_efficient_sources[0]["source"] if most_efficient_sources else None,
                    "best_seniority": top_converting_profiles[0]["seniority"] if top_converting_profiles else None
                }
            })

    except Exception as e:
        logger.error(f"❌ Error getting conversion patterns: {e}", exc_info=True)
        return error_response(f"❌ Erro ao analisar padrões de conversão: {str(e)}", e)


async def get_smart_alerts(
    job_id: str | None = None,
    severity: str = "all",
    **kwargs
) -> dict[str, Any]:
    """
    Get intelligent alerts and risk detection for recruitment pipeline.

    Args:
        job_id: Optional job ID to filter alerts
        severity: Alert severity filter (low, medium, high, all)

    Returns:
        Smart alerts including SLA risks, cooling candidates, and bottleneck warnings
    """
    company_id = require_company_id_from_context(kwargs, "get_smart_alerts")

    logger.info(f"🚨 Getting smart alerts (company: {company_id}, severity: {severity})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        async with analytics_db() as db:
            sla_at_risk = []
            cooling_candidates = []
            bottleneck_warnings = []

            job_conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Ativa"
            ]

            if job_id:
                job_conditions.append(JobVacancy.id == UUID(job_id))

            jobs_result = await db.execute(
                # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace upstream tenant gate
                select(JobVacancy).where(and_(*job_conditions))
            )
            active_jobs = jobs_result.scalars().all()

            for job in active_jobs:
                deadline = getattr(job, 'deadline', None)
                if deadline:
                    days_remaining = (deadline - datetime.utcnow()).days

                    if days_remaining < 0:
                        sla_at_risk.append({
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "alert_type": "sla_expired",
                            "severity": "high",
                            "message": f"Prazo expirado há {abs(days_remaining)} dias",
                            "days_overdue": abs(days_remaining)
                        })
                    elif days_remaining <= 7:
                        alert_severity = "high" if days_remaining <= 3 else "medium"
                        sla_at_risk.append({
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "alert_type": "sla_approaching",
                            "severity": alert_severity,
                            "message": f"Prazo em {days_remaining} dias",
                            "days_remaining": days_remaining
                        })

                days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
                if days_open > 45:
                    bottleneck_warnings.append({
                        "job_id": str(job.id),
                        "job_title": job.title,
                        "alert_type": "extended_open_time",
                        "severity": "medium" if days_open <= 60 else "high",
                        "message": f"Vaga aberta há {days_open} dias",
                        "days_open": days_open
                    })

            vc_conditions = [VacancyCandidate.company_id == company_id]
            if job_id:
                vc_conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))

            vc_result = await db.execute(
                select(VacancyCandidate, Candidate, JobVacancy).join(
                    Candidate,
                    and_(
                        VacancyCandidate.candidate_id == Candidate.id,
                        Candidate.company_id == company_id
                    )
                ).join(
                    JobVacancy,
                    and_(
                        VacancyCandidate.vacancy_id == JobVacancy.id,
                        JobVacancy.company_id == company_id
                    )
                ).where(
                    and_(
                        *vc_conditions,
                        JobVacancy.status == "Ativa"
                    )
                )
            )
            vacancy_candidates = vc_result.all()

            stage_counts = {}
            for vc, c, job in vacancy_candidates:
                updated_at = getattr(vc, 'updated_at', None) or getattr(vc, 'created_at', None)
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'

                if updated_at:
                    days_idle = (datetime.utcnow() - updated_at).days

                    if days_idle >= 5 and stage not in ["Contratado", "Rejeitado", "Desistente", "hired"]:
                        idle_severity = "low"
                        if days_idle >= 10:
                            idle_severity = "medium"
                        if days_idle >= 14:
                            idle_severity = "high"

                        cooling_candidates.append({
                            "candidate_id": str(c.id),
                            "candidate_name": getattr(c, 'name', 'N/A'),
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "current_stage": stage,
                            "days_idle": days_idle,
                            "severity": idle_severity,
                            "message": f"Sem movimentação há {days_idle} dias na etapa {stage}"
                        })

                job_key = str(job.id)
                if job_key not in stage_counts:
                    stage_counts[job_key] = {"job_title": job.title, "stages": {}}
                stage_counts[job_key]["stages"][stage] = stage_counts[job_key]["stages"].get(stage, 0) + 1

            for job_key, data in stage_counts.items():
                stages = data["stages"]
                total = sum(stages.values())

                for stage, count in stages.items():
                    if stage not in ["Contratado", "Rejeitado", "Desistente", "hired"] and total >= 5:
                        if count / total >= 0.6:
                            bottleneck_warnings.append({
                                "job_id": job_key,
                                "job_title": data["job_title"],
                                "alert_type": "stage_bottleneck",
                                "severity": "medium",
                                "message": f"{count} candidatos ({round(count/total*100)}%) estagnados em '{stage}'",
                                "stage": stage,
                                "count": count
                            })

            all_alerts = sla_at_risk + cooling_candidates + bottleneck_warnings

            if severity != "all":
                all_alerts = [a for a in all_alerts if a.get("severity") == severity]
                sla_at_risk = [a for a in sla_at_risk if a.get("severity") == severity]
                cooling_candidates = [a for a in cooling_candidates if a.get("severity") == severity]
                bottleneck_warnings = [a for a in bottleneck_warnings if a.get("severity") == severity]

            high_count = len([a for a in all_alerts if a.get("severity") == "high"])
            medium_count = len([a for a in all_alerts if a.get("severity") == "medium"])
            low_count = len([a for a in all_alerts if a.get("severity") == "low"])

            return success_response(f"✅ {len(all_alerts)} alertas detectados", {
                "job_filter": job_id,
                "severity_filter": severity,
                "total_alerts": len(all_alerts),
                "by_severity": {
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count
                },
                "sla_at_risk": sla_at_risk[:10],
                "cooling_candidates": sorted(cooling_candidates, key=lambda x: x["days_idle"], reverse=True)[:10],
                "bottleneck_warnings": bottleneck_warnings[:10],
                "recommendations": [
                    "Priorize alertas de severidade alta",
                    "Candidatos inativos há mais de 10 dias podem perder interesse",
                    "Vagas com SLA expirando precisam de ação imediata"
                ] if all_alerts else ["Nenhum alerta crítico no momento"]
            })

    except Exception as e:
        logger.error(f"❌ Error getting smart alerts: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar alertas: {str(e)}", e)
