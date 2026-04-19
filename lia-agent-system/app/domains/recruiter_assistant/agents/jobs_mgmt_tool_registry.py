"""
Jobs Management Tool Registry - Exposes job portfolio tools to the ReAct loop.

Wraps job management operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for portfolio management.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal, get_tenant_aware_session
from app.domains.hiring_policy.agents.policy_tool_registry import INDUSTRY_BENCHMARKS
from app.shared.compliance.fairness_guard import FairnessGuard

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


@tool_handler("jobs_mgmt")
async def _wrap_get_recruitment_benchmarks(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    period_days = kwargs.get("period_days", 90)
    logger.info(
        f"[jobs_mgmt_tools] get_recruitment_benchmarks called: "
        f"company={company_id} period={period_days}d"
    )

    ttf = 0.0
    fill_rate = 0.0
    active_jobs = 0
    total_jobs = 0
    filled_jobs = 0

    try:
        async with get_tenant_aware_session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) AS avg_ttf,
                        COUNT(*) FILTER (WHERE status = 'closed') AS filled,
                        COUNT(*) FILTER (WHERE status = 'active') AS active,
                        COUNT(*) AS total
                    FROM job_vacancies
                    WHERE company_id = :cid
                      AND created_at > NOW() - MAKE_INTERVAL(days => :days)
                """),
                {"cid": company_id, "days": period_days},
            )
            row = result.mappings().first()
            if row:
                ttf = round(float(row["avg_ttf"] or 0), 1)
                filled_jobs = int(row["filled"] or 0)
                active_jobs = int(row["active"] or 0)
                total_jobs = int(row["total"] or 0)
                fill_rate = round((filled_jobs / total_jobs * 100) if total_jobs > 0 else 0, 1)
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] SQL error in get_recruitment_benchmarks: {e}")

    market_benchmarks = INDUSTRY_BENCHMARKS.get("technology", {})
    market_ttf = market_benchmarks.get("avg_time_to_fill_days", 35)
    market_sources = [s["name"] for s in market_benchmarks.get("sources", [])]
    if not market_sources:
        market_sources = [
            "Robert Half - Guia Salarial 2024",
            "Gupy - Pesquisa de Recrutamento 2024",
            "LinkedIn Talent Solutions - Global Talent Trends",
            "ABRH - Pesquisa de Indicadores de RH",
            "GPTW - Melhores Empresas para Trabalhar",
        ]

    if ttf > 0 and market_ttf > 0:
        ratio = ttf / market_ttf
        if ratio <= 0.8:
            comparison = "above_market"
        elif ratio <= 1.2:
            comparison = "at_market"
        else:
            comparison = "below_market"
    else:
        comparison = "no_data"

    return {
        "success": True,
        "data": {
            "company_id": company_id,
            "period_days": period_days,
            "ttf": ttf,
            "fill_rate": fill_rate,
            "active_jobs": active_jobs,
            "total_jobs": total_jobs,
            "filled_jobs": filled_jobs,
            "market_avg_ttf": market_ttf,
            "comparison_with_market": comparison,
        },
        "sources": market_sources + ["Dados internos da empresa (historico de vagas)"],
        "message": f"Benchmarks de recrutamento carregados para empresa {company_id or 'N/A'} ({period_days} dias).",
    }


@tool_handler("jobs_mgmt")
async def _wrap_list_jobs(**kwargs: Any) -> dict[str, Any]:
    status = kwargs.get("status", "all")
    department = kwargs.get("department", "all")
    company_id = kwargs.get("company_id", "")
    limit = int(kwargs.get("limit", 30))
    # Normalize Portuguese "all" synonyms
    if str(status).lower() in ("todas", "todos", "tudo", "qualquer", "any", "none", ""):
        status = "all"
    if str(department).lower() in ("todos", "todas", "tudo", "qualquer", "any", "none", ""):
        department = "all"
    logger.info(f"[jobs_mgmt_tools] list_jobs called: status={status} department={department}")
    jobs = []
    total = 0
    try:
        async with get_tenant_aware_session() as session:
            rows = await session.execute(
                text("""
                    SELECT id, title, status, priority, department, location,
                           created_at, deadline, company_id,
                           (SELECT COUNT(*) FROM vacancy_candidates vc
                            WHERE vc.vacancy_id = jv.id) AS candidate_count,
                           EXTRACT(DAY FROM NOW() - created_at)::int AS days_open
                    FROM job_vacancies jv
                    WHERE (:status = 'all' OR status ILIKE :status_val)
                      AND (:dept = 'all' OR department ILIKE :dept_val)
                      AND (:cid = '' OR company_id = :cid)
                    ORDER BY
                        CASE priority WHEN 'alta' THEN 1 WHEN 'média' THEN 2 ELSE 3 END,
                        created_at DESC
                    LIMIT :lim
                """),
                {"status": status, "status_val": f"%{status}%",
                 "dept": department, "dept_val": f"%{department}%",
                 "cid": company_id, "lim": limit},
            )
            for row in rows.mappings():
                jobs.append({
                    "id": str(row["id"]),
                    "title": row["title"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "department": row["department"],
                    "location": row["location"],
                    "candidate_count": int(row["candidate_count"] or 0),
                    "days_open": int(row["days_open"] or 0),
                    "deadline": str(row["deadline"]) if row["deadline"] else None,
                })
            count_row = await session.execute(
                text("""
                    SELECT COUNT(*) AS total FROM job_vacancies
                    WHERE (:status = 'all' OR status ILIKE :status_val)
                      AND (:dept = 'all' OR department ILIKE :dept_val)
                      AND (:cid = '' OR company_id = :cid)
                """),
                {"status": status, "status_val": f"%{status}%",
                 "dept": department, "dept_val": f"%{department}%", "cid": company_id},
            )
            total = int((count_row.mappings().first() or {}).get("total", len(jobs)))
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] list_jobs DB error: {e}")
    return {
        "success": True,
        "data": {"status_filter": status, "department_filter": department,
                 "total_jobs": total, "jobs": jobs},
        "message": f"{total} vagas encontradas (status={status}, departamento={department}).",
    }


@tool_handler("jobs_mgmt")
async def _wrap_view_job_details(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    logger.info(f"[jobs_mgmt_tools] view_job_details called for job={job_id}")
    async with get_tenant_aware_session() as session:
        row = await session.execute(
            text("""
                SELECT id, title, status, priority, department, location,
                       description, requirements, technical_requirements,
                       salary_range, benefits, created_at, deadline,
                       recruiter, manager, company_id,
                       EXTRACT(DAY FROM NOW() - created_at)::int AS days_open
                FROM job_vacancies WHERE id = :jid
            """),
            {"jid": job_id},
        )
        data = row.mappings().first()
        if not data:
            return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada."}

        counts = await session.execute(
            text("""
                SELECT status, COUNT(*) AS cnt
                FROM vacancy_candidates WHERE vacancy_id = :jid
                GROUP BY status
            """),
            {"jid": job_id},
        )
        by_status = {r["status"]: int(r["cnt"]) for r in counts.mappings()}
        total_candidates = sum(by_status.values())

        return {
            "success": True,
            "data": {
                "job_id": str(data["id"]),
                "title": data["title"],
                "status": data["status"],
                "priority": data["priority"],
                "department": data["department"],
                "location": data["location"],
                "description": (data["description"] or "")[:500],
                "technical_requirements": data["technical_requirements"],
                "salary_range": data["salary_range"],
                "recruiter": data["recruiter"],
                "manager": data["manager"],
                "deadline": str(data["deadline"]) if data["deadline"] else None,
                "days_open": int(data["days_open"] or 0),
                "candidates_total": total_candidates,
                "candidates_by_status": by_status,
            },
            "message": f"Detalhes da vaga '{data['title']}' carregados. {total_candidates} candidatos.",
        }
@tool_handler("jobs_mgmt")
async def _wrap_get_portfolio_metrics(**kwargs: Any) -> dict[str, Any]:
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[jobs_mgmt_tools] get_portfolio_metrics called: period={period}")
    metrics: dict[str, Any] = {}
    try:
        async with get_tenant_aware_session() as session:
            row = await session.execute(
                text("""
                    SELECT
                        COUNT(*) FILTER (WHERE status ILIKE '%ativa%' OR status ILIKE '%active%') AS total_active,
                        COUNT(*) FILTER (WHERE status ILIKE '%pausada%' OR status ILIKE '%paused%') AS total_paused,
                        COUNT(*) FILTER (WHERE status ILIKE '%conclu%' OR status ILIKE '%closed%') AS total_closed,
                        COUNT(*) FILTER (WHERE status ILIKE '%rascunho%' OR status ILIKE '%draft%') AS total_draft,
                        COUNT(*) AS total,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)
                            FILTER (WHERE status ILIKE '%conclu%' OR status ILIKE '%closed%') AS avg_ttf
                    FROM job_vacancies
                    WHERE (:cid = '' OR company_id = :cid)
                      AND created_at > NOW() - MAKE_INTERVAL(days => :days)
                """),
                {"cid": company_id, "days": period_days},
            )
            data = row.mappings().first() or {}
            total = int(data.get("total") or 0)
            closed = int(data.get("total_closed") or 0)
            metrics = {
                "period": period,
                "total_active": int(data.get("total_active") or 0),
                "total_paused": int(data.get("total_paused") or 0),
                "total_closed": closed,
                "total_draft": int(data.get("total_draft") or 0),
                "total": total,
                "avg_time_to_hire": round(float(data.get("avg_ttf") or 0), 1),
                "fill_rate": round(closed / total * 100, 1) if total > 0 else 0.0,
            }
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] get_portfolio_metrics DB error: {e}")
    return {
        "success": True,
        "data": metrics,
        "message": f"Metricas do portfolio ({period}): {metrics.get('total_active', 0)} ativas, fill rate {metrics.get('fill_rate', 0)}%.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_compare_jobs(**kwargs: Any) -> dict[str, Any]:
    job_ids = kwargs.get("job_ids", [])
    logger.info(f"[jobs_mgmt_tools] compare_jobs called: jobs={job_ids}")
    comparison = []
    try:
        if job_ids:
            async with get_tenant_aware_session() as session:
                rows = await session.execute(
                    text("""
                        SELECT jv.id, jv.title, jv.status, jv.priority, jv.department,
                               jv.created_at, jv.deadline,
                               EXTRACT(DAY FROM NOW() - jv.created_at)::int AS days_open,
                               COUNT(vc.id) AS candidate_count,
                               AVG(vc.lia_score) AS avg_score,
                               COUNT(vc.id) FILTER (WHERE vc.status = 'rejected') AS rejected_count
                        FROM job_vacancies jv
                        LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                        WHERE jv.id = ANY(:ids::uuid[])
                        GROUP BY jv.id
                        ORDER BY jv.created_at DESC
                    """),
                    {"ids": job_ids},
                )
                for row in rows.mappings():
                    comparison.append({
                        "id": str(row["id"]),
                        "title": row["title"],
                        "status": row["status"],
                        "priority": row["priority"],
                        "department": row["department"],
                        "days_open": int(row["days_open"] or 0),
                        "candidate_count": int(row["candidate_count"] or 0),
                        "avg_lia_score": round(float(row["avg_score"] or 0), 1),
                        "rejected_count": int(row["rejected_count"] or 0),
                    })
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] compare_jobs DB error: {e}")
    return {
        "success": True,
        "data": {"job_ids": job_ids, "comparison_count": len(comparison), "comparison": comparison},
        "message": f"Comparacao de {len(comparison)} vagas concluida.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_check_sla(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[jobs_mgmt_tools] check_sla called: job={job_id or 'all'}")
    overdue_jobs = []
    at_risk_jobs = []
    compliant_count = 0
    try:
        async with get_tenant_aware_session() as session:
            rows = await session.execute(
                text("""
                    SELECT id, title, status, deadline,
                           EXTRACT(DAY FROM NOW() - created_at)::int AS days_open,
                           EXTRACT(DAY FROM deadline - NOW())::int AS days_to_deadline
                    FROM job_vacancies
                    WHERE (status ILIKE '%ativa%' OR status ILIKE '%active%')
                      AND (:jid = '' OR id::text = :jid)
                      AND (:cid = '' OR company_id = :cid)
                """),
                {"jid": job_id, "cid": company_id},
            )
            for row in rows.mappings():
                dtd = row["days_to_deadline"]
                entry = {"id": str(row["id"]), "title": row["title"],
                         "days_open": int(row["days_open"] or 0),
                         "days_to_deadline": int(dtd) if dtd is not None else None}
                if dtd is not None and dtd < 0:
                    overdue_jobs.append({**entry, "overdue_days": abs(int(dtd))})
                elif dtd is not None and dtd <= 7:
                    at_risk_jobs.append({**entry, "urgency": "high"})
                elif dtd is not None and dtd <= 14:
                    at_risk_jobs.append({**entry, "urgency": "medium"})
                else:
                    compliant_count += 1
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] check_sla DB error: {e}")

    overall = "overdue" if overdue_jobs else ("at_risk" if at_risk_jobs else "compliant")
    return {
        "success": True,
        "data": {
            "job_id": job_id or "all",
            "sla_status": overall,
            "overdue": len(overdue_jobs),
            "at_risk": len(at_risk_jobs),
            "compliant": compliant_count,
            "overdue_jobs": overdue_jobs,
            "at_risk_jobs": at_risk_jobs,
        },
        "message": f"SLA: {len(overdue_jobs)} vencidas, {len(at_risk_jobs)} em risco, {compliant_count} ok.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_analyze_bottlenecks(**kwargs: Any) -> dict[str, Any]:
    department = kwargs.get("department", "all")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[jobs_mgmt_tools] analyze_bottlenecks called: department={department}")
    bottlenecks = []
    try:
        async with get_tenant_aware_session() as session:
            rows = await session.execute(
                text("""
                    SELECT jv.id, jv.title, jv.department,
                           EXTRACT(DAY FROM NOW() - jv.created_at)::int AS days_open,
                           COUNT(vc.id) AS total_candidates,
                           COUNT(vc.id) FILTER (
                               WHERE vc.updated_at < NOW() - INTERVAL '14 days'
                           ) AS stagnant_count,
                           AVG(vc.lia_score) AS avg_score
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE (jv.status ILIKE '%ativa%' OR jv.status ILIKE '%active%')
                      AND (:dept = 'all' OR jv.department ILIKE :dept_val)
                      AND (:cid = '' OR jv.company_id = :cid)
                    GROUP BY jv.id
                    HAVING COUNT(vc.id) > 0
                    ORDER BY stagnant_count DESC, days_open DESC
                    LIMIT 20
                """),
                {"dept": department, "dept_val": f"%{department}%", "cid": company_id},
            )
            for row in rows.mappings():
                stagnant = int(row["stagnant_count"] or 0)
                total = int(row["total_candidates"] or 0)
                days = int(row["days_open"] or 0)
                issues = []
                if stagnant > 0 and total > 0:
                    pct = stagnant / total * 100
                    if pct > 30:
                        issues.append({"type": "high_stagnation", "severity": "high",
                                       "detail": f"{stagnant}/{total} candidatos parados >14 dias ({pct:.0f}%)"})
                if days > 60:
                    issues.append({"type": "long_time_open", "severity": "medium",
                                   "detail": f"Vaga aberta ha {days} dias (benchmark: 35 dias)"})
                avg_score = round(float(row["avg_score"] or 0), 1)
                if 0 < avg_score < 3.0:
                    issues.append({"type": "low_quality_pool", "severity": "high",
                                   "detail": f"Score medio baixo ({avg_score}/5)"})
                if issues:
                    bottlenecks.append({
                        "job_id": str(row["id"]),
                        "title": row["title"],
                        "department": row["department"],
                        "days_open": days,
                        "total_candidates": total,
                        "issues": issues,
                    })
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] analyze_bottlenecks DB error: {e}")
    return {
        "success": True,
        "data": {"department": department, "bottlenecks": bottlenecks,
                 "total_identified": len(bottlenecks), "analysis_complete": True},
        "message": f"{len(bottlenecks)} gargalos identificados no departamento '{department}'.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_pause_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[jobs_mgmt_tools] pause_job called: job={job_id} reason={reason}")
    async with get_tenant_aware_session() as session:
        result = await session.execute(
            text("""
                UPDATE job_vacancies SET status = 'Pausada', updated_at = NOW()
                WHERE id = :jid AND (:cid = '' OR company_id = :cid)
                RETURNING status
            """),
            {"jid": job_id, "cid": company_id},
        )
        if not result.fetchone():
            return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada ou sem permissao."}
        await session.commit()
    return {"success": True,
            "data": {"job_id": job_id, "new_status": "Pausada", "reason": reason},
            "message": f"Vaga {job_id} pausada com sucesso."}
@tool_handler("jobs_mgmt")
async def _wrap_reopen_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[jobs_mgmt_tools] reopen_job called: job={job_id}")
    async with get_tenant_aware_session() as session:
        result = await session.execute(
            text("""
                UPDATE job_vacancies SET status = 'Ativa', updated_at = NOW()
                WHERE id = :jid AND (:cid = '' OR company_id = :cid)
                RETURNING status
            """),
            {"jid": job_id, "cid": company_id},
        )
        if not result.fetchone():
            return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada ou sem permissao."}
        await session.commit()
    return {"success": True,
            "data": {"job_id": job_id, "new_status": "Ativa"},
            "message": f"Vaga {job_id} reaberta com sucesso."}
@tool_handler("jobs_mgmt")
async def _wrap_close_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[jobs_mgmt_tools] close_job called: job={job_id} reason={reason}")
    async with get_tenant_aware_session() as session:
        result = await session.execute(
            text("""
                UPDATE job_vacancies SET status = 'Concluída', updated_at = NOW()
                WHERE id = :jid AND (:cid = '' OR company_id = :cid)
                RETURNING status
            """),
            {"jid": job_id, "cid": company_id},
        )
        if not result.fetchone():
            return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada ou sem permissao."}
        await session.commit()
    return {"success": True,
            "data": {"job_id": job_id, "new_status": "Concluída", "reason": reason},
            "message": f"Vaga {job_id} fechada com sucesso."}
@tool_handler("jobs_mgmt")
async def _wrap_update_priority(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    priority = kwargs.get("priority", "média")
    company_id = kwargs.get("company_id", "")
    priority_map = {"high": "alta", "medium": "média", "low": "baixa",
                    "alta": "alta", "média": "média", "baixa": "baixa"}
    priority_pt = priority_map.get(priority.lower(), priority)
    logger.info(f"[jobs_mgmt_tools] update_priority called: job={job_id} priority={priority_pt}")
    async with get_tenant_aware_session() as session:
        prev = await session.execute(
            text("SELECT priority FROM job_vacancies WHERE id = :jid AND (:cid = '' OR company_id = :cid)"),
            {"jid": job_id, "cid": company_id},
        )
        prev_row = prev.mappings().first()
        if not prev_row:
            return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada."}
        await session.execute(
            text("UPDATE job_vacancies SET priority = :p, updated_at = NOW() WHERE id = :jid"),
            {"p": priority_pt, "jid": job_id},
        )
        await session.commit()
    return {"success": True,
            "data": {"job_id": job_id, "previous_priority": prev_row["priority"], "new_priority": priority_pt},
            "message": f"Prioridade da vaga {job_id} atualizada para '{priority_pt}'."}
@tool_handler("jobs_mgmt")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[jobs_mgmt_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        async with get_tenant_aware_session() as session:
            row = await session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status ILIKE '%ativa%') AS active,
                        COUNT(*) FILTER (WHERE status ILIKE '%conclu%') AS closed,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)
                            FILTER (WHERE status ILIKE '%conclu%') AS avg_ttf
                    FROM job_vacancies
                    WHERE (:cid = '' OR company_id = :cid)
                      AND created_at > NOW() - MAKE_INTERVAL(days => :days)
                """),
                {"cid": company_id, "days": period_days},
            )
            data = row.mappings().first() or {}
            summary = {
                "total_jobs": int(data.get("total") or 0),
                "active": int(data.get("active") or 0),
                "closed": int(data.get("closed") or 0),
                "avg_ttf_days": round(float(data.get("avg_ttf") or 0), 1),
            }
    except Exception as e:
        logger.warning(f"[jobs_mgmt_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {"report_type": report_type, "period": period,
                 "report_id": report_id, "generated": True, "summary": summary},
        "message": f"Relatorio '{report_type}' gerado (id: {report_id}). {summary.get('total_jobs', 0)} vagas no periodo.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_validate_job_action_fairness(**kwargs: Any) -> dict[str, Any]:
    action_description = kwargs.get("action_description", "")
    action_type = kwargs.get("action_type", "general")
    logger.info(
        f"[jobs_mgmt_tools] validate_job_action_fairness called: "
        f"type={action_type} desc='{action_description[:60]}...'"
    )

    if not action_description.strip():
        return {
            "success": False,
            "message": "Descricao da acao vazia. Informe o texto a validar.",
        }

    try:
        result = _fairness_guard.check(action_description)
        implicit_warnings = _fairness_guard.check_implicit_bias(action_description)

        if result.is_blocked:
            return {
                "success": True,
                "data": {
                    "is_compliant": False,
                    "blocked": True,
                    "category": result.category,
                    "blocked_terms": result.blocked_terms,
                    "educational_message": result.educational_message,
                    "soft_warnings": implicit_warnings,
                },
                "message": f"Acao BLOQUEADA por vies discriminatorio: {result.educational_message}",
            }

        semantic_warnings = []
        try:
            semantic_result = await _fairness_guard.check_semantic(action_description, context=f"job_action_{action_type}")
            if semantic_result.is_blocked:
                return {
                    "success": True,
                    "data": {
                        "is_compliant": False,
                        "blocked": True,
                        "category": semantic_result.category,
                        "blocked_terms": semantic_result.blocked_terms,
                        "educational_message": semantic_result.educational_message,
                        "soft_warnings": implicit_warnings + (semantic_result.soft_warnings or []),
                    },
                    "message": f"Acao BLOQUEADA por vies semantico: {semantic_result.educational_message}",
                }
            semantic_warnings = semantic_result.soft_warnings or []
        except Exception as sem_err:
            logger.debug(f"[jobs_mgmt_tools] semantic check skipped: {sem_err}")

        all_warnings = implicit_warnings + [w for w in semantic_warnings if w not in implicit_warnings]

        return {
            "success": True,
            "data": {
                "is_compliant": True,
                "blocked": False,
                "soft_warnings": all_warnings,
            },
            "message": "Acao validada. Nenhum vies discriminatorio detectado."
            + (f" {len(all_warnings)} alertas de vies implicito." if all_warnings else ""),
        }
    except Exception as e:
        logger.error(f"[jobs_mgmt_tools] validate_job_action_fairness error: {e}", exc_info=True)
        return {"success": True, "data": {"is_compliant": True, "soft_warnings": []}, "error": str(e)}


@tool_handler("jobs_mgmt")
async def _wrap_get_pipeline_prediction_jobs_mgmt(**kwargs: Any) -> dict[str, Any]:
    """Return closure probability prediction for company overview or individual vacancy."""
    from app.shared.services.pipeline_prediction_service import pipeline_prediction_service

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")

    if vacancy_id:
        result = await pipeline_prediction_service.get_vacancy_prediction(
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
        prob = result.get("closure_probability", 0)
        est = result.get("estimated_days_to_close")
        days_str = f" em ~{est} dias" if est else ""
        interpretation = (
            f"Probabilidade de fechamento: {prob}%{days_str}. "
            f"Confiança: {result.get('confidence_level', 'medium')}."
        )
    else:
        result = await pipeline_prediction_service.get_company_overview(
            company_id=company_id,
        )
        summary = result.get("summary", {})
        vacancies = result.get("vacancies", [])
        at_risk = [v for v in vacancies if v["closure_probability"] < 30]
        near = [v for v in vacancies if v["closure_probability"] >= 80]
        interpretation = (
            f"{summary.get('total_active_vacancies', 0)} vagas ativas. "
            f"{len(at_risk)} em risco de não fechar: "
            + (", ".join(f"'{v['vacancy_title']}' ({v['closure_probability']}%)" for v in at_risk[:3]) or "nenhuma")
            + f". {len(near)} prestes a fechar: "
            + (", ".join(f"'{v['vacancy_title']}' ({v['closure_probability']}%)" for v in near[:3]) or "nenhuma")
            + "."
        )
    result["success"] = True
    result["interpretation"] = interpretation
    return result
TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="validate_job_action_fairness",
        description="Valida acoes de gestao de vagas contra vies discriminatorio usando FairnessGuard. Use ao fechar, pausar ou modificar vagas com justificativas do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {"type": "string", "description": "Texto descrevendo a acao ou justificativa a validar"},
                "action_type": {"type": "string", "description": "Tipo da acao: close, pause, reopen, priority_change"},
            },
            "required": ["action_description"],
        },
        function=_wrap_validate_job_action_fairness,
    ),
    ToolDefinition(
        name="get_recruitment_benchmarks",
        description="Obtem benchmarks reais de recrutamento via SQL: time-to-fill, fill rate, vagas por status, comparacao com mercado por setor. Fontes citaveis incluidas.",
        parameters={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID da empresa"},
                "period_days": {"type": "integer", "description": "Periodo em dias para analise (padrao: 90)"},
            },
            "required": ["company_id"],
        },
        function=_wrap_get_recruitment_benchmarks,
    ),
    ToolDefinition(
        name="list_jobs",
        description="Lista todas as vagas ativas com status, metricas e informacoes resumidas do portfolio.",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtro de status: active, paused, closed, all"},
                "department": {"type": "string", "description": "Filtro por departamento"},
            },
            "required": [],
        },
        function=_wrap_list_jobs,
    ),
    ToolDefinition(
        name="view_job_details",
        description="Visualiza informacoes detalhadas de uma vaga especifica, incluindo pipeline, candidatos e metricas.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
            },
            "required": ["job_id"],
        },
        function=_wrap_view_job_details,
    ),
    ToolDefinition(
        name="get_portfolio_metrics",
        description="Obtem metricas agregadas do portfolio de vagas como taxa de preenchimento, tempo medio e distribuicao.",
        parameters={
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": [],
        },
        function=_wrap_get_portfolio_metrics,
    ),
    ToolDefinition(
        name="compare_jobs",
        description="Compara multiplas vagas lado a lado em dimensoes como pipeline, velocidade e qualidade.",
        parameters={
            "type": "object",
            "properties": {
                "job_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs das vagas para comparar"},
            },
            "required": ["job_ids"],
        },
        function=_wrap_compare_jobs,
    ),
    ToolDefinition(
        name="check_sla",
        description="Verifica compliance de SLA das vagas, identificando vagas em risco ou com prazo vencido.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga (vazio para verificar todas)"},
            },
            "required": [],
        },
        function=_wrap_check_sla,
    ),
    ToolDefinition(
        name="analyze_bottlenecks",
        description="Identifica gargalos no pipeline de recrutamento entre todas as vagas, por departamento ou geral.",
        parameters={
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Departamento para analisar (vazio para todos)"},
            },
            "required": [],
        },
        function=_wrap_analyze_bottlenecks,
    ),
    ToolDefinition(
        name="pause_job",
        description="Pausa uma vaga ativa. Requer motivo e confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "reason": {"type": "string", "description": "Motivo para pausar a vaga"},
            },
            "required": ["job_id", "reason"],
        },
        function=_wrap_pause_job,
    ),
    ToolDefinition(
        name="reopen_job",
        description="Reabre uma vaga pausada ou fechada, reativando o pipeline de recrutamento.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
            },
            "required": ["job_id"],
        },
        function=_wrap_reopen_job,
    ),
    ToolDefinition(
        name="close_job",
        description="Fecha uma vaga definitivamente. Requer motivo e confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "reason": {"type": "string", "description": "Motivo para fechar a vaga"},
            },
            "required": ["job_id", "reason"],
        },
        function=_wrap_close_job,
    ),
    ToolDefinition(
        name="update_priority",
        description="Atualiza o nivel de prioridade de uma vaga (alta, media, baixa).",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "priority": {"type": "string", "description": "Nova prioridade: high, medium, low"},
            },
            "required": ["job_id", "priority"],
        },
        function=_wrap_update_priority,
    ),
    ToolDefinition(
        name="generate_report",
        description="Gera um relatorio do portfolio de vagas com metricas, analises e recomendacoes.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo: summary, detailed, sla"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": ["report_type"],
        },
        function=_wrap_generate_report,
    ),
    ToolDefinition(
        name="get_pipeline_prediction",
        description=(
            "Retorna previsão de fechamento de vagas ativas: probabilidade (0–100%), "
            "prazo estimado, confiança da previsão, fatores positivos e de risco. "
            "Sem vacancy_id retorna visão geral de todas as vagas da empresa ordenadas por risco. "
            "Use para responder: 'qual a chance de fechar essas vagas?', 'quais vagas vão fechar logo?', "
            "'quais vagas estão em risco?', 'previsão de fechamento do pipeline', "
            "'probabilidade de fechar esse mês'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga (opcional — sem este campo retorna visão geral da empresa).",
                },
                "company_id": {
                    "type": "string",
                    "description": "ID da empresa (multi-tenant, obrigatório).",
                },
            },
            "required": ["company_id"],
        },
        function=_wrap_get_pipeline_prediction_jobs_mgmt,
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "overview": ["list_jobs", "view_job_details", "get_portfolio_metrics", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
    "analysis": ["compare_jobs", "check_sla", "analyze_bottlenecks", "view_job_details", "get_portfolio_metrics", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
    "action": ["pause_job", "reopen_job", "close_job", "update_priority", "generate_report", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
}


def get_jobs_mgmt_tools(stage: str = "") -> list[ToolDefinition]:
    """Return jobs management tools, optionally filtered by stage.

    Args:
        stage: Current stage identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    logger.debug(f"[jobs_mgmt_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools


# ─── duplicate_job — NEW TOOL (eval fix: WZ-004) ──────────────────────────
@tool_handler("jobs_mgmt")
async def _wrap_duplicate_job(**kwargs: Any) -> dict[str, Any]:
    """Duplicate an existing job vacancy as a new draft."""
    job_id_or_title: str = (
        kwargs.get("job_id") or kwargs.get("vacancy_id") or kwargs.get("job_title") or ""
    )
    company_id: str = kwargs.get("company_id", "") or ""
    new_title: str = kwargs.get("new_title", "") or ""

    if not company_id:
        return {"success": False, "error": "company_id obrigatorio para duplicar vaga."}
    if not job_id_or_title:
        return {"success": False, "error": "Informe o ID ou titulo da vaga a duplicar."}

    logger.info(f"[jobs_mgmt] duplicate_job: identifier={job_id_or_title!r} company={company_id!r}")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    SELECT id, title, department, location, work_model, employment_type,
                           seniority_level, salary_range, requirements,
                           technical_requirements, behavioral_competencies, description
                    FROM job_vacancies
                    WHERE company_id = :cid
                      AND (job_id = :jid OR title ILIKE :title_pat)
                    LIMIT 2
                """),
                {
                    "cid": company_id,
                    "jid": job_id_or_title,
                    "title_pat": f"%{job_id_or_title}%",
                },
            )
            rows = result.fetchall()

        if not rows:
            return {
                "success": False,
                "error": f"Vaga '{job_id_or_title}' nao encontrada para esta empresa.",
            }
        if len(rows) > 1:
            titles = [r[1] for r in rows]
            return {
                "success": False,
                "error": f"Titulo ambiguo — {len(rows)} vagas encontradas: {titles}. Especifique melhor.",
            }

        source = rows[0]
        original_title = source[1]
        dup_title = new_title or f"{original_title} - Segunda Posicao"
        new_job_id = f"DUP-{uuid.uuid4().hex[:8].upper()}"
        new_uuid = uuid.uuid4()

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO job_vacancies (
                        id, company_id, job_id, title, department, location, work_model,
                        employment_type, seniority_level, description, salary_range,
                        status, stage, priority, urgency_level,
                        open_date, deadline, requirements, technical_requirements,
                        behavioral_competencies, visibility,
                        created_by, recruiter_email,
                        created_at, updated_at, is_pipeline_customized
                    )
                    SELECT
                        :new_id, company_id, :new_job_id, :new_title, department, location, work_model,
                        employment_type, seniority_level, description, salary_range,
                        'Rascunho', 'Planejamento', priority, urgency_level,
                        NOW(), NOW() + INTERVAL '60 days',
                        requirements, technical_requirements,
                        behavioral_competencies, visibility,
                        created_by, recruiter_email,
                        NOW(), NOW(), false
                    FROM job_vacancies
                    WHERE id = :source_id AND company_id = :cid
                """),
                {
                    "new_id": new_uuid,
                    "new_job_id": new_job_id,
                    "new_title": dup_title,
                    "source_id": source[0],
                    "cid": company_id,
                },
            )
            await db.commit()

        return {
            "success": True,
            "original_title": original_title,
            "new_title": dup_title,
            "new_job_id": new_job_id,
            "new_vacancy_id": str(new_uuid),
            "status": "Rascunho",
            "message": (
                f"Vaga duplicada com sucesso! "
                f"Nova vaga '{dup_title}' criada como rascunho (ID: {new_job_id}). "
                f"Revise e publique quando estiver pronta."
            ),
        }
    except Exception as exc:
        logger.error(f"[jobs_mgmt] duplicate_job error: {exc}", exc_info=True)
        return {"success": False, "error": f"Erro ao duplicar vaga: {str(exc)[:200]}"}


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="duplicate_job",
        description=(
            "Duplica uma vaga existente como novo rascunho. "
            "Use quando o usuario quiser criar uma segunda posicao ou copia de vaga. "
            "A copia e criada com status Rascunho — nao publicada diretamente. "
            "Busca por job_id exato ou titulo parcial."
        ),
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga a duplicar"},
                "job_title": {"type": "string", "description": "Titulo da vaga a duplicar"},
                "new_title": {"type": "string", "description": "Titulo para a nova vaga (opcional)"},
                "company_id": {"type": "string", "description": "ID da empresa (obrigatorio, multi-tenant)"},
            },
            "required": ["company_id"],
        },
        function=_wrap_duplicate_job,
    )
)
_TOOL_MAP["duplicate_job"] = TOOL_DEFINITIONS[-1]
