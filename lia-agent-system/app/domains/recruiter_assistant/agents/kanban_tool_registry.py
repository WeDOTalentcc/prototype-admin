"""
Kanban Tool Registry - Exposes kanban analysis tools to the ReAct loop.

Wraps pipeline analytics operations into ToolDefinition format so the
ReActLoop can autonomously decide which tools to call for strategic
pipeline analysis and optimization.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()

async def _fetch_candidate_name_map(candidate_ids: list[str], company_id: str) -> dict[str, str]:
    """Fetch {id: name} map for bulk result labels. Fail-open: returns {} on error."""
    if not candidate_ids:
        return {}
    try:
        from app.domains.candidates.repositories.candidate_repository import CandidateRepository
        async with AsyncSessionLocal() as _sess:
            _repo = CandidateRepository(_sess)
            _candidates = await _repo.list_by_ids(candidate_ids, company_id=company_id)
            return {str(c.id): (c.name or str(c.id)) for c in _candidates}
    except Exception as _e:
        import logging as _lg
        _lg.getLogger(__name__).debug("[kanban_tools] _fetch_candidate_name_map fail-open: %s", _e)
        return {}



@tool_handler("kanban")
async def _wrap_check_rejection_fairness(**kwargs: Any) -> dict[str, Any]:
    """Check rejection reason against FairnessGuard for discriminatory bias."""
    rejection_reason = kwargs.get("rejection_reason", "")
    candidate_name = kwargs.get("candidate_name", "")
    logger.info(
        f"[kanban_tools] check_rejection_fairness called: "
        f"candidate={candidate_name or 'N/A'} reason='{rejection_reason[:60]}...'"
    )

    explicit_result = _fairness_guard.check(rejection_reason)
    implicit_warnings = _fairness_guard.check_implicit_bias(rejection_reason)

    warnings = []
    educational_message = None

    if explicit_result.is_blocked:
        educational_message = explicit_result.educational_message
        warnings.extend([
            f"Vies explicito detectado ({explicit_result.category}): {', '.join(explicit_result.blocked_terms)}"
        ])

    if implicit_warnings:
        warnings.extend(implicit_warnings)

    if explicit_result.soft_warnings:
        for sw in explicit_result.soft_warnings:
            if sw not in warnings:
                warnings.append(sw)

    if not explicit_result.is_blocked:
        try:
            semantic_result = await _fairness_guard.check_semantic(rejection_reason, context="candidate_rejection")
            if semantic_result.is_blocked:
                educational_message = semantic_result.educational_message
                warnings.append(f"Vies semantico detectado: {semantic_result.educational_message}")
            if semantic_result.soft_warnings:
                for sw in semantic_result.soft_warnings:
                    if sw not in warnings:
                        warnings.append(sw)
        except Exception as sem_err:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"[kanban_tools] semantic check skipped: {sem_err}")

    is_fair = not explicit_result.is_blocked and len(warnings) == 0

    return {
        "is_fair": is_fair,
        "warnings": warnings,
        "educational_message": educational_message,
        "candidate_name": candidate_name,
        "rejection_reason": rejection_reason,
    }


@tool_handler("kanban")
async def _wrap_get_pipeline_benchmarks(**kwargs: Any) -> dict[str, Any]:
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(
        f"[kanban_tools] get_pipeline_benchmarks called: "
        f"vacancy={vacancy_id} company={company_id}"
    )

    try:
        # W1-004-B (2026-05-23): SQL inline → RecruiterMetricsRepository (ADR-001).
        # _require_company_id fail-closed garante zero cross-tenant aggregation.
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )

        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            per_stage_metrics = {}
            company_averages = {}
            if vacancy_id:
                per_stage_metrics = await repo.avg_days_per_stage_for_vacancy(
                    vacancy_id=vacancy_id, company_id=company_id
                )
            if company_id:
                company_averages = await repo.avg_days_per_stage_for_company(
                    company_id=company_id
                )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] SQL error in get_pipeline_benchmarks: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar os benchmarks do pipeline agora. Tente novamente em instantes.",
        }

    status_map = {}
    for stage_name, metrics in per_stage_metrics.items():
        company_avg = company_averages.get(stage_name, {}).get("avg_days", 0)
        if company_avg > 0 and metrics["avg_days"] > 0:
            ratio = metrics["avg_days"] / company_avg
            if ratio <= 0.8:
                status_map[stage_name] = "ahead"
            elif ratio <= 1.2:
                status_map[stage_name] = "on_track"
            else:
                status_map[stage_name] = "behind"
        else:
            status_map[stage_name] = "no_data"

    overall = "on_track"
    if any(s == "behind" for s in status_map.values()):
        overall = "behind"
    elif all(s == "ahead" for s in status_map.values()) and status_map:
        overall = "ahead"

    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "per_stage_metrics": per_stage_metrics,
            "company_averages": company_averages,
            "status": status_map,
            "overall_status": overall,
        },
        "message": f"Benchmarks do pipeline carregados para vaga {vacancy_id or 'N/A'}.",
        "sources": [
            "Dados internos da empresa (historico de vagas)",
            "Medias calculadas a partir de todas as vagas da empresa",
            "ABRH - Pesquisa de Indicadores de RH 2024",
            "GPTW - Benchmarks de Recrutamento Brasil 2024",
            "LinkedIn Talent Solutions - Recruiting Benchmarks 2024",
        ],
    }


@tool_handler("kanban")
async def _wrap_get_recruiter_backlog(**kwargs: Any) -> dict[str, Any]:
    """Return the recruiter's prioritized action backlog — candidates waiting beyond stage thresholds."""
    from app.shared.services.recruiter_metrics_service import recruiter_metrics_service

    recruiter_id = kwargs.get("recruiter_id", "")
    company_id = kwargs["company_id"]

    if not recruiter_id:
        return {
            "success": False,
            "error": "recruiter_id e company_id são obrigatórios.",
        }

    backlog = await recruiter_metrics_service.get_action_backlog(
        recruiter_id=recruiter_id,
        company_id=company_id,
    )
    summary = await recruiter_metrics_service.get_weekly_summary(
        recruiter_id=recruiter_id,
        company_id=company_id,
    )
    return {
        "success": True,
        "total_waiting": len(backlog),
        "critical_count": summary.get("critical_count", 0),
        "offers_pending": summary.get("offers_pending", 0),
        "avg_response_time_days": summary.get("avg_response_time_days"),
        "candidates_advanced_this_week": summary.get("candidates_advanced_this_week", 0),
        "backlog": backlog[:10],  # top 10 mais urgentes
    }


@tool_handler("kanban")
async def _wrap_get_recruiter_benchmark(**kwargs: Any) -> dict[str, Any]:
    """Compare recruiter metrics against anonymised company median (Sprint 2D)."""
    from app.shared.services.recruiter_metrics_service import recruiter_metrics_service

    recruiter_id = kwargs.get("recruiter_id", "")
    company_id = kwargs["company_id"]

    if not recruiter_id:
        return {"success": False, "error": "recruiter_id e company_id são obrigatórios."}

    result = await recruiter_metrics_service.get_recruiter_benchmark_comparison(
        recruiter_id=recruiter_id,
        company_id=company_id,
    )

    if not result.get("benchmark_available"):
        return {
            "success": True,
            "benchmark_available": False,
            "message": "Dados insuficientes para benchmark (requer ≥ 2 recrutadores ativos na empresa).",
        }

    cmp = result.get("comparison", {})
    overall = result.get("overall_performance", "unknown")

    perf_map = {"above_average": "acima da média", "average": "na média", "below_average": "abaixo da média"}
    lines = [f"Performance geral: {perf_map.get(overall, overall)}"]
    for key, label in [
        ("response_time", "Tempo de resposta"),
        ("advanced_per_week", "Candidatos avançados/semana"),
        ("backlog_count", "Backlog"),
        ("offers_pending", "Ofertas pendentes"),
    ]:
        c = cmp.get(key, {})
        if c.get("personal") is not None and c.get("benchmark") is not None:
            perf = {"better": "✅ melhor", "at_par": "➡️ na média", "worse": "⚠️ abaixo"}.get(
                c.get("performance", ""), ""
            )
            lines.append(f"  {label}: {c['personal']} (mediana: {c['benchmark']}) {perf}")

    result["interpretation"] = "\n".join(lines)
    result["success"] = True
    return result


@tool_handler("kanban")
async def _wrap_get_journey_metrics(**kwargs: Any) -> dict[str, Any]:
    """Return funnel metrics, health score and risk patterns for a vacancy."""
    from app.shared.services.journey_intelligence_service import journey_intelligence_service

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs["company_id"]

    if not vacancy_id:
        return {"success": False, "error": "vacancy_id e company_id são obrigatórios."}

    result = await journey_intelligence_service.get_vacancy_metrics(
        vacancy_id=vacancy_id,
        company_id=company_id,
    )
    if not result.get("success"):
        return result

    # Gerar mensagem interpretativa para a LIA
    hs = result["health_score"]
    label = result["health_label"]
    patterns = result["risk_patterns"]
    summary = result["summary"]

    interpretation = (
        f"Health score: {hs}/100 ({label}). "
        f"{summary['total_active']} candidatos ativos, "
        f"{summary['candidates_in_advanced_stages']} em etapas avançadas, "
        f"conversão geral: {summary['conversion_rate_overall']:.0%}."
    )
    if patterns:
        interpretation += " Padrões de risco: " + " | ".join(p["message"] for p in patterns[:2])

    result["interpretation"] = interpretation
    return result


@tool_handler("kanban")
async def _wrap_get_pipeline_prediction(**kwargs: Any) -> dict[str, Any]:
    """Return closure probability prediction for a vacancy or company overview."""
    from app.shared.services.pipeline_prediction_service import pipeline_prediction_service

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs["company_id"]

    if vacancy_id:
        result = await pipeline_prediction_service.get_vacancy_prediction(
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
    else:
        result = await pipeline_prediction_service.get_company_overview(
            company_id=company_id,
        )

    # Interpretação para a LIA
    if vacancy_id:
        prob = result.get("closure_probability", 0)
        est = result.get("estimated_days_to_close")
        conf = result.get("confidence_level", "medium")
        days_str = f" em aproximadamente {est} dias" if est else ""
        pos = result.get("positive_factors", [])
        risks = result.get("risk_factors", [])
        interpretation = (
            f"Probabilidade de fechamento: {prob}% (confiança: {conf}){days_str}. "
        )
        if pos:
            interpretation += f"Pontos positivos: {', '.join(pos[:3])}. "
        if risks:
            interpretation += f"Riscos: {', '.join(risks[:3])}."
    else:
        summary = result.get("summary", {})
        interpretation = (
            f"{summary.get('total_active_vacancies', 0)} vagas ativas. "
            f"{summary.get('at_risk_count', 0)} em risco de não fechar (<30%), "
            f"{summary.get('near_closure_count', 0)} prestes a fechar (≥80%). "
            f"Probabilidade média: {summary.get('avg_closure_probability', 0)}%."
        )

    result["success"] = True
    result["interpretation"] = interpretation
    return result


@tool_handler("kanban")
async def _wrap_get_at_risk_candidates(**kwargs: Any) -> dict[str, Any]:
    """Return candidates at risk of ghosting ranked by EWS score."""
    from app.shared.services.early_warning_service import early_warning_service

    company_id = kwargs["company_id"]
    min_risk_level = kwargs.get("min_risk_level", "medium")

    candidates = await early_warning_service.get_at_risk_candidates(
        company_id=company_id,
        min_risk_level=min_risk_level,
    )
    summary = await early_warning_service.get_summary_by_risk_level(
        company_id=company_id,
    )
    return {
        "success": True,
        "total": len(candidates),
        "summary": summary,
        "candidates": candidates[:15],
        "message": (
            f"{summary['by_risk_level']['critical']} candidato(s) em risco crítico, "
            f"{summary['by_risk_level']['high']} alto risco, "
            f"{summary['by_risk_level']['medium']} risco médio."
            if candidates else
            "Nenhum candidato em risco de desengajamento no momento."
        ),
    }


@tool_handler("kanban")
async def _wrap_find_silver_medalists(**kwargs: Any) -> dict[str, Any]:
    """Find warm candidates from past processes to re-surface for current vacancies."""
    from app.shared.services.silver_medalist_service import silver_medalist_service

    vacancy_id = kwargs.get("vacancy_id") or None
    company_id = kwargs.get("company_id") or ""
    limit = int(kwargs.get("limit", 20))
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] find_silver_medalists called: vacancy={vacancy_id} company={company_id}")

    if vacancy_id:
        medalists = await silver_medalist_service.find_for_vacancy(
            target_vacancy_id=vacancy_id,
            company_id=company_id,
            limit=limit,
        )
    else:
        medalists = await silver_medalist_service.find_for_company(
            company_id=company_id,
            limit=limit,
        )
    return {
        "success": True,
        "total": len(medalists),
        "medalists": medalists,
        "message": (
            f"{len(medalists)} candidato(s) prata encontrado(s) — "
            f"chegaram à etapa de entrevista em processos anteriores e não foram contratados."
            if medalists else
            "Nenhum candidato prata encontrado no período."
        ),
    }


@tool_handler("kanban")
async def _wrap_get_pipeline_velocity(**kwargs: Any) -> dict[str, Any]:
    """Return per-stage velocity metrics using precise stage_entered_at timestamps."""
    from app.shared.services.pipeline_velocity_service import pipeline_velocity_service

    vacancy_id = kwargs.get("vacancy_id") or None
    company_id = kwargs.get("company_id") or None
    logger.info(
        f"[kanban_tools] get_pipeline_velocity called: vacancy={vacancy_id} company={company_id}"
    )

    metrics = await pipeline_velocity_service.get_velocity_metrics(
        vacancy_id=vacancy_id,
        company_id=company_id,
    )
    return {"success": True, "data": metrics}


@tool_handler("kanban")
async def _wrap_get_pipeline_summary(**kwargs: Any) -> dict[str, Any]:
    """Get overall pipeline summary with candidate counts per stage."""
    # W1-004-B (2026-05-23): SQL inline → RecruiterMetricsRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] get_pipeline_summary called for vacancy={vacancy_id or 'all'}")

    try:
        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            result = await repo.count_candidates_per_stage(
                vacancy_id=vacancy_id, company_id=company_id
            )
        stages = result["per_stage"]
        total = sum(stages.values())
        hired = result["hired_count"]
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] get_pipeline_summary DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar o resumo do pipeline agora. Tente novamente em instantes.",
        }

    conversion = round(hired / total * 100, 1) if total > 0 else 0.0
    _rrp_blocks = []
    try:
        if stages:
            from app.shared.rrp_ranking_builder import build_pipeline_funnel_block
            _rrp_blocks = build_pipeline_funnel_block(
                f"Pipeline ({vacancy_id or 'todas as vagas'})",
                stages, total, conversion,
            )
    except Exception as _e:
        logger.warning(f"[kanban_tools] funnel block skipped: {_e}")
    return {
        "success": True,
        "data": {"vacancy_id": vacancy_id or "all", "total_candidates": total,
                 "stages": stages, "conversion_rate": conversion,
                 "response_blocks": _rrp_blocks or None},
        "message": f"Pipeline: {total} candidatos distribuidos em {len(stages)} etapas. Conversao: {conversion}%.",
    }


@tool_handler("kanban")
async def _wrap_get_stage_metrics(**kwargs: Any) -> dict[str, Any]:
    """Get metrics for a specific pipeline stage."""
    # W1-004-B (2026-05-23): SQL inline → RecruiterMetricsRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    stage = kwargs.get("stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] get_stage_metrics called: stage={stage} vacancy={vacancy_id or 'all'}")
    try:
        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            data = await repo.get_stage_metrics(
                stage=stage, vacancy_id=vacancy_id, company_id=company_id
            )
        metrics = {
            "stage": stage,
            "vacancy_id": vacancy_id or "all",
            **data,
        }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] get_stage_metrics DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar as métricas da etapa agora. Tente novamente em instantes.",
        }
    return {
        "success": True,
        "data": metrics,
        "message": f"Etapa '{stage}': {metrics.get('candidate_count', 0)} candidatos, {metrics.get('avg_time_days', 0)} dias media, risco: {metrics.get('bottleneck_risk', 'low')}.",
    }


@tool_handler("kanban")
async def _wrap_list_stage_candidates(**kwargs: Any) -> dict[str, Any]:
    """List candidates in a specific stage."""
    # W1-004-B (2026-05-23): SQL inline → CandidatePipelineRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
        CandidatePipelineRepository,
    )

    stage = kwargs.get("stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    limit = int(kwargs.get("limit", 20))
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] list_stage_candidates called: stage={stage} vacancy={vacancy_id or 'all'}")
    if not company_id:
        return {"error": "company_id is required", "success": False}
    try:
        async with AsyncSessionLocal() as session:
            repo = CandidatePipelineRepository(session)
            candidates, total = await repo.list_candidates_in_stage(
                vacancy_id=vacancy_id, company_id=company_id, stage=stage, limit=limit
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] list_stage_candidates DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui listar os candidatos da etapa agora. Tente novamente em instantes.",
        }
    return {
        "success": True,
        "data": {"stage": stage, "vacancy_id": vacancy_id or "all",
                 "candidates": candidates, "total": total, "limit": limit},
        "message": f"{total} candidatos na etapa '{stage}'.",
    }


@tool_handler("kanban")
async def _wrap_analyze_stage(**kwargs: Any) -> dict[str, Any]:
    """Deep analysis of a pipeline stage."""
    stage = kwargs.get("stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] analyze_stage called: stage={stage} vacancy={vacancy_id or 'all'}")

    metrics_result = await _wrap_get_stage_metrics(
        stage=stage, vacancy_id=vacancy_id, company_id=company_id)
    m = metrics_result.get("data", {})
    count = m.get("candidate_count", 0)
    avg_days = m.get("avg_time_days", 0.0)
    avg_score = m.get("avg_lia_score", 0.0)
    bottleneck_risk = m.get("bottleneck_risk", "low")

    risks = []
    recommendations = []
    if bottleneck_risk == "high":
        risks.append({"type": "stagnation", "severity": "high",
                      "detail": f"Candidatos parados ha {avg_days} dias em media"})
        recommendations.append("Agendar entrevistas pendentes com urgencia")
    if avg_score > 0 and avg_score < 3.0:
        risks.append({"type": "low_quality", "severity": "medium",
                      "detail": f"Score medio baixo ({avg_score}/5)"})
        recommendations.append("Revisar criterios de avanco para esta etapa")
    if count == 0:
        risks.append({"type": "empty_stage", "severity": "low",
                      "detail": "Nenhum candidato nesta etapa"})

    health = "critical" if any(r["severity"] == "high" for r in risks) else \
             ("attention" if risks else "healthy")

    return {
        "success": True,
        "data": {"stage": stage, "vacancy_id": vacancy_id or "all",
                 "health": health, "candidate_count": count,
                 "avg_time_days": avg_days, "avg_lia_score": avg_score,
                 "recommendations": recommendations, "risks": risks},
        "message": f"Analise da etapa '{stage}': {health}. {len(risks)} riscos, {count} candidatos.",
    }


@tool_handler("kanban")
async def _wrap_identify_bottlenecks(**kwargs: Any) -> dict[str, Any]:
    """Identify bottlenecks across the pipeline."""
    # W1-004-B (2026-05-23): SQL inline → RecruiterMetricsRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] identify_bottlenecks called for vacancy={vacancy_id or 'all'}")
    bottlenecks = []
    critical_stages = []
    try:
        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            all_stage_metrics = await repo.get_stage_bottleneck_metrics(
                vacancy_id=vacancy_id, company_id=company_id
            )
        for row in all_stage_metrics:
            avg_days = row["avg_days"]
            stagnant = row["stagnant_count"]
            cnt = row["candidate_count"]
            if avg_days > 14 or (cnt > 0 and stagnant / cnt > 0.3):
                entry = {"stage": row["stage"], "candidate_count": cnt,
                         "avg_days": avg_days, "stagnant_count": stagnant,
                         "severity": "high" if avg_days > 21 else "medium"}
                bottlenecks.append(entry)
                if entry["severity"] == "high":
                    critical_stages.append(row["stage"])
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[kanban_tools] identify_bottlenecks error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": "Erro ao identificar gargalos."}

    overall_health = "critical" if critical_stages else ("attention" if bottlenecks else "healthy")
    return {
        "success": True,
        "data": {"vacancy_id": vacancy_id or "all", "bottlenecks": bottlenecks,
                 "critical_stages": critical_stages, "overall_health": overall_health},
        "message": f"{len(bottlenecks)} gargalos encontrados. Etapas criticas: {critical_stages or 'nenhuma'}.",
    }


@tool_handler("kanban")
async def _wrap_get_candidate_aging(**kwargs: Any) -> dict[str, Any]:
    """Get aging report for candidates stuck in stages."""
    # W1-004-B (2026-05-23): SQL inline → CandidatePipelineRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
        CandidatePipelineRepository,
    )

    stage = kwargs.get("stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    days_threshold = int(kwargs.get("days_threshold", 7))
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] get_candidate_aging called: stage={stage or 'all'} threshold={days_threshold}d")
    aging_candidates = []
    if not company_id:
        return {"error": "company_id is required", "success": False}
    try:
        async with AsyncSessionLocal() as session:
            repo = CandidatePipelineRepository(session)
            aging_candidates = await repo.get_aging_candidates(
                vacancy_id=vacancy_id, company_id=company_id,
                threshold_days=days_threshold, stage=stage
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] get_candidate_aging DB error: {e}")

    avg_days = round(sum(c["days_stuck"] for c in aging_candidates) / len(aging_candidates), 1) \
               if aging_candidates else 0.0
    return {
        "success": True,
        "data": {"stage": stage or "all", "days_threshold": days_threshold,
                 "aging_candidates": aging_candidates, "total_stagnant": len(aging_candidates),
                 "avg_days_stuck": avg_days},
        "message": f"{len(aging_candidates)} candidatos parados ha mais de {days_threshold} dias.",
    }


@tool_handler("kanban")
async def _wrap_compare_stages(**kwargs: Any) -> dict[str, Any]:
    """Compare metrics between pipeline stages."""
    stages = kwargs.get("stages", [])
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] compare_stages called for stages={stages}")
    comparison = []
    for s in stages:
        result = await _wrap_get_stage_metrics(stage=s, vacancy_id=vacancy_id, company_id=company_id)
        comparison.append(result.get("data", {"stage": s}))

    best = min(comparison, key=lambda x: x.get("avg_time_days", 999)) if comparison else None
    worst = max(comparison, key=lambda x: x.get("avg_time_days", 0)) if comparison else None
    return {
        "success": True,
        "data": {"stages": stages, "comparison": comparison,
                 "best_performing": best.get("stage") if best else None,
                 "worst_performing": worst.get("stage") if worst else None},
        "message": f"Comparacao de {len(stages)} etapas concluida.",
    }


@tool_handler("kanban")
async def _wrap_suggest_movements(**kwargs: Any) -> dict[str, Any]:
    """Suggest candidate movements based on score and aging."""
    # W1-004-B (2026-05-23): SQL inline → CandidatePipelineRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
        CandidatePipelineRepository,
    )

    stage = kwargs.get("stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] suggest_movements called: stage={stage} vacancy={vacancy_id or 'all'}")
    suggestions = []
    if not company_id:
        return {"error": "company_id is required", "success": False}
    try:
        async with AsyncSessionLocal() as session:
            repo = CandidatePipelineRepository(session)
            rows = await repo.get_candidates_for_movement_suggestion(
                vacancy_id=vacancy_id, company_id=company_id, stage=stage
            )
        for row in rows:
            score = row["lia_score"]
            days = row["days_in_stage"]
            action = None
            if score >= 4.2:
                action = {"type": "advance", "reason": f"Score alto ({score:.1f}/5) — avancar para proxima etapa"}
            elif days > 14:
                action = {"type": "follow_up", "reason": f"Parado ha {days} dias — fazer follow-up ou tomar decisao"}
            elif score < 3.0 and score > 0:
                action = {"type": "disqualify", "reason": f"Score baixo ({score:.1f}/5) — considerar desqualificacao"}
            if action:
                suggestions.append({
                    "candidate_id": row["candidate_id"],
                    "name": row["name"],
                    "current_stage": row["stage"],
                    "lia_score": score,
                    "days_in_stage": days,
                    "suggested_action": action,
                })
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[kanban_tools] suggest_movements error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": "Erro ao gerar sugestoes de movimentacao."}
    return {
        "success": True,
        "data": {"stage": stage or "all", "vacancy_id": vacancy_id or "all",
                 "suggestions": suggestions, "total_suggested": len(suggestions)},
        "message": f"{len(suggestions)} sugestoes de movimentacao geradas.",
    }


@tool_handler("kanban")
async def _wrap_batch_move_candidates(**kwargs: Any) -> dict[str, Any]:
    """Move multiple candidates to a target stage (real DB UPDATE)."""
    # W1-004-B (2026-05-23): SQL inline → RecruiterMetricsRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    candidate_ids = kwargs.get("candidate_ids", [])
    target_stage = kwargs.get("target_stage", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    reason = kwargs.get("reason", "")
    # F3: HITL gate — batch move é mutação sensível; dormante com LIA_HITL_GATE off.
    from app.shared.hitl.hitl_approval_context import hitl_preflight as _hitl_preflight
    _hitl_block = _hitl_preflight(
        tool="batch_move_candidates",
        domain="kanban",
        message="Mover candidatos em lote é uma ação que requer confirmação.",
        data={"candidate_count": len(candidate_ids), "target_stage": target_stage},
    )
    if _hitl_block is not None:
        return _hitl_block
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] batch_move_candidates called: candidates={len(candidate_ids)} target={target_stage}")
    if not candidate_ids or not target_stage:
        return {"success": False, "data": {}, "message": "Parametros 'candidate_ids' e 'target_stage' sao obrigatorios."}
    moved = 0
    try:
        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            moved = await repo.bulk_update_candidate_stage(
                vacancy_id=vacancy_id, company_id=company_id,
                candidate_ids=candidate_ids, new_stage=target_stage
            )
    except Exception as e:
        # rollback handled automatically by `async with AsyncSessionLocal()`
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[kanban_tools] batch_move_candidates error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": "Erro ao mover candidatos em lote."}
    # F5 bulk_execute producer: emite ui_action para FE abrir BulkResultReport.
    # Honesto: bulk SQL retorna só o count; per-item ok apenas quando moved==total.
    _name_map = await _fetch_candidate_name_map(candidate_ids, company_id)
    _ui_results = (
        [{"id": cid, "name": _name_map.get(cid, cid), "ok": True} for cid in candidate_ids]
        if moved == len(candidate_ids)
        else (
            [{"id": cid, "name": _name_map.get(cid, cid), "ok": True} for cid in candidate_ids[:moved]]
            + [{"id": cid, "name": _name_map.get(cid, cid), "ok": False, "reason": "Não confirmado"} for cid in candidate_ids[moved:]]
        )
    )
    return {
        "success": True,
        "data": {
            "ui_action": "bulk_execute",
            "ui_action_params": {
                "action": "batch_move_candidates",
                "title": f"Candidatos movidos para '{target_stage}'",
                "results": _ui_results,
            },
            "moved_count": moved,
            "target_stage": target_stage,
            "candidate_ids": candidate_ids,
            "reason": reason,
        },
        "message": f"{moved} candidatos movidos para '{target_stage}'.",
    }


@tool_handler("kanban")
async def _wrap_send_batch_communication(**kwargs: Any) -> dict[str, Any]:
    """Send communication to multiple candidates."""
    candidate_ids = kwargs.get("candidate_ids", [])
    company_id = kwargs.get("company_id", "")
    channel = kwargs.get("channel", "email")
    template = kwargs.get("template", "")
    # F3: HITL gate -- comunicacao em lote e acao sensivel (outreach); dormante com LIA_HITL_GATE off.
    from app.shared.hitl.hitl_approval_context import hitl_preflight as _hitl_preflight
    _hitl_block = _hitl_preflight(
        tool="send_batch_communication",
        domain="kanban",
        message="Enviar comunicacao em lote requer confirmacao.",
        data={"candidate_count": len(candidate_ids), "channel": channel},
    )
    if _hitl_block is not None:
        return _hitl_block
    logger.info(
        f"[kanban_tools] send_batch_communication called: candidates={len(candidate_ids)} "
        f"channel={channel}"
    )
    _comm_name_map = await _fetch_candidate_name_map(candidate_ids, company_id)
    return {
        "success": True,
        "data": {
            "ui_action": "bulk_execute",
            "ui_action_params": {
                "action": "send_batch_communication",
                "title": f"Comunicação via {channel} enviada",
                "results": [{"id": cid, "name": _comm_name_map.get(cid, cid), "ok": True} for cid in candidate_ids],
            },
            "sent_count": len(candidate_ids),
            "channel": channel,
            "template": template,
            "candidate_ids": candidate_ids,
        },
        "message": f"Comunicacao enviada para {len(candidate_ids)} candidatos via {channel}.",
    }


@tool_handler("kanban")
async def _wrap_start_screening_batch(**kwargs: Any) -> dict[str, Any]:
    """Start WSI screening for multiple candidates."""
    candidate_ids = kwargs.get("candidate_ids", [])
    vacancy_id = kwargs.get("vacancy_id", "unknown")
    logger.info(
        f"[kanban_tools] start_screening_batch called: candidates={len(candidate_ids)} "
        f"vacancy={vacancy_id}"
    )
    return {
        "success": True,
        "data": {
            "started_count": len(candidate_ids),
            "vacancy_id": vacancy_id,
            "candidate_ids": candidate_ids,
            "status": "screening_initiated",
        },
        "message": f"Screening WSI iniciado para {len(candidate_ids)} candidatos.",
    }


@tool_handler("kanban")
async def _wrap_generate_pipeline_report(**kwargs: Any) -> dict[str, Any]:
    """Generate pipeline analytics report with real data."""
    report_type = kwargs.get("report_type", "summary")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] generate_pipeline_report called: type={report_type} vacancy={vacancy_id or 'all'}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"

    summary_result = await _wrap_get_pipeline_summary(
        vacancy_id=vacancy_id, company_id=company_id)
    bottleneck_result = await _wrap_identify_bottlenecks(
        vacancy_id=vacancy_id, company_id=company_id)
    summary = {
        "total_candidates": summary_result.get("data", {}).get("total_candidates", 0),
        "stages": summary_result.get("data", {}).get("stages", {}),
        "conversion_rate": summary_result.get("data", {}).get("conversion_rate", 0.0),
        "bottleneck_count": len(bottleneck_result.get("data", {}).get("bottlenecks", [])),
        "overall_health": bottleneck_result.get("data", {}).get("overall_health", "unknown"),
    }
    return {
        "success": True,
        "data": {"report_type": report_type, "vacancy_id": vacancy_id or "all",
                 "report_id": report_id, "generated": True, "summary": summary},
        "message": f"Relatorio '{report_type}' gerado (id: {report_id}). {summary['total_candidates']} candidatos no pipeline.",
    }


@tool_handler("kanban")
async def _wrap_view_candidate_full_profile(**kwargs: Any) -> dict[str, Any]:
    """View complete candidate profile including education, work history and scores."""
    # W1-004-B (2026-05-23): SQL inline → CandidatePipelineRepository (ADR-001).
    from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
        CandidatePipelineRepository,
    )

    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII (email+salary+gender) leak gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[kanban_tools] view_candidate_full_profile called for candidate={candidate_id}")

    try:
        async with AsyncSessionLocal() as session:
            repo = CandidatePipelineRepository(session)
            data = await repo.get_candidate_full_profile(
                candidate_id=candidate_id, company_id=company_id
            )
        if not data:
            return {
                "success": False,
                "data": {"candidate_id": candidate_id},
                "message": f"Candidato {candidate_id} nao encontrado.",
            }
        profile = data
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[kanban_tools] view_candidate_full_profile DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui carregar o perfil do candidato agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": profile,
        "message": f"Perfil completo do candidato {profile.get('name', candidate_id)} carregado.",
    }


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "phone",
        "linkedin_url"],
        name="view_candidate_full_profile",
        description="Visualiza o perfil completo do candidato: dados pessoais, formacao academica, historico de trabalho, skills, scores LIA/WSI, pretensao salarial, idiomas e preferencias. Use para perguntas sobre um candidato especifico como 'formacao de Joao', 'experiencia de Maria', 'perfil completo de [nome]'.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_view_candidate_full_profile,
    ),
    ToolDefinition(
        name="get_pipeline_benchmarks",
        description="Obtem benchmarks reais do pipeline via SQL: tempo medio por etapa para esta vaga vs media da empresa, com status comparativo (ahead/on_track/behind).",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga para benchmarks especificos"},
            },
            "required": ["vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_benchmarks,
    ),
    ToolDefinition(
        name="get_pipeline_summary",
        description="Obtem resumo geral do pipeline com contagem de candidatos por etapa, taxas de conversao e metricas gerais.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional, padrao: todas)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_summary,
    ),
    ToolDefinition(
        name="get_stage_metrics",
        description="Obtem metricas detalhadas de uma etapa especifica do pipeline: volume, tempo medio, taxa de conversao.",
        parameters={
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Nome da etapa do pipeline"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
            },
            "required": ["stage"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_stage_metrics,
    ),
    ToolDefinition(
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "linkedin_url"],
        name="list_stage_candidates",
        description="Lista candidatos em uma etapa especifica do pipeline com informacoes resumidas.",
        parameters={
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Nome da etapa do pipeline"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
                "limit": {"type": "integer", "description": "Numero maximo de candidatos (opcional, padrao: 20)"},
            },
            "required": ["stage"],
        },
        output_schema=ToolOutput,
        function=_wrap_list_stage_candidates,
    ),
    ToolDefinition(
        name="analyze_stage",
        description="Analise profunda de uma etapa do pipeline incluindo saude, riscos e recomendacoes estrategicas.",
        parameters={
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Nome da etapa do pipeline"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
            },
            "required": ["stage"],
        },
        output_schema=ToolOutput,
        function=_wrap_analyze_stage,
    ),
    ToolDefinition(
        name="identify_bottlenecks",
        description="Identifica gargalos em todo o pipeline, destacando etapas criticas e candidatos estagnados.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional, padrao: todas)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_identify_bottlenecks,
    ),
    ToolDefinition(
        name="get_candidate_aging",
        description="Gera relatorio de aging mostrando candidatos parados ha muito tempo em cada etapa.",
        parameters={
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Etapa especifica (opcional, padrao: todas)"},
                "days_threshold": {"type": "integer", "description": "Limite de dias para considerar estagnado (opcional, padrao: 7)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_candidate_aging,
    ),
    ToolDefinition(
        name="compare_stages",
        description="Compara metricas entre etapas do pipeline para identificar discrepancias e oportunidades.",
        parameters={
            "type": "object",
            "properties": {
                "stages": {"type": "array", "items": {"type": "string"}, "description": "Lista de etapas para comparar"},
            },
            "required": ["stages"],
        },
        output_schema=ToolOutput,
        function=_wrap_compare_stages,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="suggest_movements",
        description="Gera sugestoes inteligentes de movimentacao de candidatos baseadas em dados e metricas.",
        parameters={
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Etapa de origem para sugestoes"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
            },
            "required": ["stage"],
        },
        output_schema=ToolOutput,
        function=_wrap_suggest_movements,
    ),
    ToolDefinition(
        side_effects=["write"],
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="batch_move_candidates",
        description="Move multiplos candidatos entre etapas do pipeline de uma vez. Requer confirmacao.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos"},
                "target_stage": {"type": "string", "description": "Etapa de destino no pipeline"},
                "reason": {"type": "string", "description": "Motivo da movimentacao em massa"},
            },
            "required": ["candidate_ids", "target_stage", "reason"],
        },
        output_schema=ToolOutput,
        function=_wrap_batch_move_candidates,
    ),
    ToolDefinition(
        side_effects=["send"],
        touches_pii=True,
        pii_output_fields=["email_address",
        "phone"],
        name="send_batch_communication",
        description="Envia comunicacao em massa para multiplos candidatos via email, WhatsApp ou outro canal.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos"},
                "channel": {"type": "string", "description": "Canal de comunicacao: email, whatsapp, sms"},
                "template": {"type": "string", "description": "Template da mensagem a ser enviada"},
            },
            "required": ["candidate_ids", "channel", "template"],
        },
        output_schema=ToolOutput,
        function=_wrap_send_batch_communication,
    ),
    ToolDefinition(
        side_effects=["write"],
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="start_screening_batch",
        description="Inicia screening WSI para multiplos candidatos de uma vaga especifica.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para o screening"},
            },
            "required": ["candidate_ids", "vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_start_screening_batch,
    ),
    ToolDefinition(
        name="generate_pipeline_report",
        description="Gera relatorio de analytics do pipeline com metricas, graficos e recomendacoes.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo do relatorio: summary, bottleneck, aging, conversion"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional, padrao: todas)"},
            },
            "required": ["report_type"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_pipeline_report,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["candidate_name"],
        name="check_rejection_fairness",
        description="Valida justificativa de rejeicao de candidato contra vies discriminatorio. Bloqueia vies explicito e alerta sobre vies implicito.",
        parameters={
            "type": "object",
            "properties": {
                "rejection_reason": {"type": "string", "description": "Justificativa de rejeicao do candidato a ser validada"},
                "candidate_name": {"type": "string", "description": "Nome do candidato (opcional, para contexto)"},
            },
            "required": ["rejection_reason"],
        },
        output_schema=ToolOutput,
        function=_wrap_check_rejection_fairness,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email"],
        name="find_silver_medalists",
        description=(
            "Busca candidatos 'prata' — que chegaram à etapa de entrevista em processos anteriores "
            "mas não foram contratados. Permite reaproveitar talentos qualificados para novas vagas similares. "
            "Use para responder: 'temos candidatos de processos anteriores para esta vaga?', "
            "'quem pode ser reaproveitado?', 'temos um banco de talentos?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga alvo (opcional — retorna medalists compatíveis com esta vaga)"},
                "limit": {"type": "integer", "description": "Numero maximo de candidatos a retornar (padrao: 20)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_find_silver_medalists,
    ),
    ToolDefinition(
        name="get_recruiter_backlog",
        description=(
            "Retorna a lista priorizada de candidatos que estão aguardando ação do recrutador. "
            "Usa quando o usuário perguntar: 'quais candidatos estão me esperando?', "
            "'tenho candidatos parados?', 'meu backlog de hoje', 'o que preciso fazer hoje?'. "
            "Ordena por urgência: offer > entrevista > triagem. "
            "Inclui dias_em_espera, etapa, nome do candidato e vaga."
        ),
        parameters={
            "type": "object",
            "properties": {
                "recruiter_id": {
                    "type": "string",
                    "description": "ID do recrutador (user_id). Use o contexto da sessão atual.",
                },
            },
            "required": ["recruiter_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_recruiter_backlog,
    ),
    ToolDefinition(
        name="get_recruiter_benchmark",
        description=(
            "Compara as métricas do recrutador com a mediana anônima da empresa. "
            "Retorna: tempo de resposta, candidatos avançados/semana, backlog e ofertas — "
            "comparados com a mediana dos colegas (sem identificar ninguém individualmente). "
            "Use para responder: 'como estou comparado à empresa?', 'minha performance está boa?', "
            "'quanto tempo outros recrutadores levam para responder?', "
            "'estou acima ou abaixo da média do time?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "recruiter_id": {
                    "type": "string",
                    "description": "ID do recrutador. Use o contexto da sessão atual.",
                },
            },
            "required": ["recruiter_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_recruiter_benchmark,
    ),
    ToolDefinition(
        name="get_journey_metrics",
        description=(
            "Retorna métricas detalhadas do funil de uma vaga: conversão por etapa, drop-off, "
            "health score (0-100) e padrões de risco preditivos. "
            "Use quando o contexto tiver uma vaga específica ou o recrutador perguntar sobre saúde do pipeline: "
            "'como está o funil desta vaga?', 'o pipeline está saudável?', 'onde os candidatos estão saindo?', "
            "'qual o health score da vaga X?', 'temos risco de não fechar esta vaga?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga a analisar.",
                },
            },
            "required": ["vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_journey_metrics,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email"],
        name="get_at_risk_candidates",
        description=(
            "Retorna candidatos em risco de desengajamento (ghosting) ordenados por EWS score. "
            "Usa thresholds inteligentes por etapa (offer=2/4d, entrevista=3/5d, triagem=5/8d, aplicado=7/12d) "
            "e pondera pelo LIA score do candidato. "
            "Use para responder: 'quais candidatos podem sumir?', 'temos riscos de ghosting?', "
            "'candidatos sem contato há dias?', 'quem devo contatar urgente?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "min_risk_level": {
                    "type": "string",
                    "description": "Nível mínimo de risco a retornar: medium (padrão), high ou critical.",
                    "enum": ["medium", "high", "critical"],
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_at_risk_candidates,
    ),
    ToolDefinition(
        name="get_pipeline_prediction",
        description=(
            "Prevê a probabilidade de fechamento de uma vaga específica (ou visão geral da empresa) "
            "usando dados operacionais: velocidade do pipeline, candidatos em etapas avançadas, "
            "health score, EWS risk e volume. Retorna closure_probability (0–100%), "
            "estimated_days_to_close, confidence_level, positive_factors e risk_factors. "
            "Use para responder: 'qual a chance de fechar essa vaga?', 'quando vamos fechar?', "
            "'preciso apresentar previsão para o gestor', 'quais vagas estão em risco de não fechar?', "
            "'quais vagas vão fechar logo?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga (opcional — sem este campo retorna visão geral da empresa).",
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_prediction,
    ),
    ToolDefinition(
        name="get_pipeline_velocity",
        description=(
            "Retorna metricas de velocidade por etapa do pipeline usando timestamps precisos de entrada em cada etapa. "
            "Identifica gargalos (etapas onde candidatos ficam mais tempo do que o esperado) e saude geral do pipeline. "
            "Use para responder: 'qual etapa esta travando?', 'onde o processo esta demorando?', 'temos gargalos no pipeline?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional — sem este campo retorna dados da empresa)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_velocity,
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "pipeline_overview": ["get_pipeline_summary", "get_stage_metrics", "list_stage_candidates", "view_candidate_full_profile", "check_rejection_fairness", "get_pipeline_benchmarks", "get_pipeline_velocity", "find_silver_medalists", "get_recruiter_backlog", "get_at_risk_candidates", "get_journey_metrics", "get_recruiter_benchmark", "get_pipeline_prediction"],
    "stage_analysis": ["analyze_stage", "identify_bottlenecks", "get_candidate_aging", "compare_stages", "get_stage_metrics", "view_candidate_full_profile", "check_rejection_fairness", "get_pipeline_benchmarks", "get_pipeline_velocity", "find_silver_medalists", "get_recruiter_backlog", "get_at_risk_candidates", "get_journey_metrics", "get_recruiter_benchmark", "get_pipeline_prediction"],
    "pipeline_actions": ["suggest_movements", "batch_move_candidates", "send_batch_communication", "start_screening_batch", "generate_pipeline_report", "view_candidate_full_profile", "check_rejection_fairness", "get_pipeline_benchmarks", "get_pipeline_velocity", "find_silver_medalists", "get_recruiter_backlog", "get_at_risk_candidates", "get_journey_metrics", "get_recruiter_benchmark", "get_pipeline_prediction"],
}

from app.shared.compliance.safety_category import SafetyCategory

GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "batch_move_candidates": SafetyCategory.BULK_ACTION,
    "send_batch_communication": SafetyCategory.OUTREACH,
    "start_screening_batch": SafetyCategory.BULK_ACTION,
}


def get_kanban_tools(stage: str = "") -> list[ToolDefinition]:
    """Return kanban analysis tools, optionally filtered by stage.

    Args:
        stage: Current kanban analysis phase identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.debug(f"[kanban_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
