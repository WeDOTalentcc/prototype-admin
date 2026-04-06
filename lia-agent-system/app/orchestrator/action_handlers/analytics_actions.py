"""
Analytics Actions — KPI reports, funnel analysis, job health checks.

Handles: generate_kpi_report, job_health_check, analyze_funnel
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def execute_analytics_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    if action_id == "generate_kpi_report":
        return await _generate_kpi_report(params, context)
    elif action_id == "job_health_check":
        return await _job_health_check(params, context)
    elif action_id == "analyze_funnel":
        return await _analyze_funnel(params, context)
    return None


async def _generate_kpi_report(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        company_id = context.get("company_id") if context else None
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")

        if not company_id:
            return ActionResult(
                status="error",
                message="Empresa não identificada para gerar o relatório.",
                error_detail="Missing company_id",
                action_type="generate_kpi_report",
            )

        async with AsyncSessionLocal() as db:
            jobs_result = await db.execute(text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'Ativa') as active_jobs,
                    COUNT(*) FILTER (WHERE status = 'Pausada') as paused_jobs,
                    COUNT(*) FILTER (WHERE status = 'Fechada') as closed_jobs,
                    COUNT(*) as total_jobs
                FROM job_vacancies
                WHERE company_id = CAST(:co AS uuid)
            """), {"co": str(company_id)})
            jobs = jobs_result.fetchone()

            cands_result = await db.execute(text("""
                SELECT
                    COUNT(DISTINCT candidate_id) as total_candidates,
                    COUNT(*) FILTER (WHERE stage = 'Novos') as stage_new,
                    COUNT(*) FILTER (WHERE stage = 'Triagem') as stage_screening,
                    COUNT(*) FILTER (WHERE stage = 'Entrevista') as stage_interview,
                    COUNT(*) FILTER (WHERE stage = 'Proposta') as stage_offer,
                    COUNT(*) FILTER (WHERE stage = 'Contratado') as stage_hired,
                    COUNT(*) FILTER (WHERE stage IN ('Rejeitado', 'Reprovado')) as stage_rejected,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)::int as avg_days_in_pipeline
                FROM vacancy_candidates
                WHERE company_id = CAST(:co AS uuid)
            """), {"co": str(company_id)})
            cands = cands_result.fetchone()

        lines = ["**Relatório de KPIs de Recrutamento:**\n"]
        lines.append(f"**Vagas:** {jobs.active_jobs} ativas | {jobs.paused_jobs} pausadas | {jobs.closed_jobs} fechadas ({jobs.total_jobs} total)")
        lines.append(f"**Candidatos Únicos:** {cands.total_candidates}")
        lines.append(f"\n**Distribuição no Pipeline:**")
        lines.append(f"  - Novos: {cands.stage_new}")
        lines.append(f"  - Triagem: {cands.stage_screening}")
        lines.append(f"  - Entrevista: {cands.stage_interview}")
        lines.append(f"  - Proposta: {cands.stage_offer}")
        lines.append(f"  - Contratados: {cands.stage_hired}")
        lines.append(f"  - Rejeitados: {cands.stage_rejected}")
        if cands.avg_days_in_pipeline:
            lines.append(f"\n**Tempo Médio no Pipeline:** {cands.avg_days_in_pipeline} dias")

        if cands.total_candidates and cands.total_candidates > 0:
            hire_rate = round((cands.stage_hired / cands.total_candidates) * 100, 1) if cands.stage_hired else 0
            lines.append(f"**Taxa de Contratação:** {hire_rate}%")

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={
                "active_jobs": jobs.active_jobs, "paused_jobs": jobs.paused_jobs,
                "closed_jobs": jobs.closed_jobs, "total_jobs": jobs.total_jobs,
                "total_candidates": cands.total_candidates,
                "stage_distribution": {
                    "new": cands.stage_new, "screening": cands.stage_screening,
                    "interview": cands.stage_interview, "offer": cands.stage_offer,
                    "hired": cands.stage_hired, "rejected": cands.stage_rejected,
                },
                "avg_days_in_pipeline": cands.avg_days_in_pipeline,
                "generated_at": datetime.utcnow().isoformat(),
            },
            action_type="generate_kpi_report",
        )
    except Exception as e:
        logger.warning(f"generate_kpi_report failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao gerar relatório de KPIs.",
            error_detail=str(e),
            action_type="generate_kpi_report",
        )


async def _job_health_check(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None

        if not job_id:
            return ActionResult(
                status="error",
                message="Informe a vaga para o diagnóstico.",
                error_detail="Missing job_id",
                action_type="job_health_check",
            )

        async with AsyncSessionLocal() as db:
            job_sql = """
                SELECT title, status, priority, created_at,
                       EXTRACT(DAY FROM NOW() - created_at)::int as days_open
                FROM job_vacancies WHERE id = CAST(:jid AS uuid)
            """
            job_bind: dict[str, Any] = {"jid": str(job_id)}
            if company_id:
                job_sql += " AND company_id = CAST(:co AS uuid)"
                job_bind["co"] = str(company_id)
            job_result = await db.execute(text(job_sql), job_bind)
            job = job_result.fetchone()

            if not job:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada.",
                    error_detail="Job not found",
                    action_type="job_health_check",
                )

            pipeline_result = await db.execute(text("""
                SELECT stage, COUNT(*) as cnt
                FROM vacancy_candidates
                WHERE vacancy_id = CAST(:jid AS uuid) AND status = 'active'
                GROUP BY stage
                ORDER BY cnt DESC
            """), {"jid": str(job_id)})
            stages = pipeline_result.fetchall()

            stale_result = await db.execute(text("""
                SELECT COUNT(*) as stale_count
                FROM vacancy_candidates
                WHERE vacancy_id = CAST(:jid AS uuid)
                  AND status = 'active'
                  AND updated_at < NOW() - INTERVAL '7 days'
            """), {"jid": str(job_id)})
            stale = stale_result.fetchone()

            total_candidates = sum(s.cnt for s in stages) if stages else 0

        alerts = []
        if total_candidates == 0:
            alerts.append("Nenhum candidato no pipeline — considere ampliar a divulgação")
        if stale and stale.stale_count > 0:
            alerts.append(f"{stale.stale_count} candidato(s) sem atualização há mais de 7 dias")
        if job.days_open and job.days_open > 30:
            alerts.append(f"Vaga aberta há {job.days_open} dias — acima da média de 30 dias")

        stage_lines = [f"  - {s.stage}: {s.cnt}" for s in stages] if stages else ["  - Nenhum candidato"]
        alert_lines = [f"  - {a}" for a in alerts] if alerts else ["  - Nenhum alerta"]
        health_emoji = "🟢" if not alerts else ("🟡" if len(alerts) <= 1 else "🔴")

        lines = [
            f"**Diagnóstico da Vaga \"{job.title}\":** {health_emoji}\n",
            f"**Status:** {job.status} | **Dias aberta:** {job.days_open or 0}",
            f"**Total de candidatos ativos:** {total_candidates}\n",
            "**Pipeline:**",
            *stage_lines,
            "\n**Alertas:**",
            *alert_lines,
        ]

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={
                "job_id": job_id, "job_title": job.title,
                "days_open": job.days_open, "total_candidates": total_candidates,
                "stages": {s.stage: s.cnt for s in stages} if stages else {},
                "stale_count": stale.stale_count if stale else 0,
                "alerts": alerts, "health": "good" if not alerts else "warning" if len(alerts) <= 1 else "critical",
            },
            action_type="job_health_check",
        )
    except Exception as e:
        logger.warning(f"job_health_check failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao executar diagnóstico da vaga.",
            error_detail=str(e),
            action_type="job_health_check",
        )


async def _analyze_funnel(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            if job_id:
                funnel_sql = """
                    SELECT stage, COUNT(*) as cnt,
                           COUNT(*) FILTER (WHERE status = 'active') as active_cnt
                    FROM vacancy_candidates
                    WHERE vacancy_id = CAST(:jid AS uuid)
                """
                funnel_bind: dict[str, Any] = {"jid": str(job_id)}
                if company_id:
                    funnel_sql += " AND company_id = CAST(:co AS uuid)"
                    funnel_bind["co"] = str(company_id)
                funnel_sql += " GROUP BY stage"
                result = await db.execute(text(funnel_sql), funnel_bind)

                job_sql = "SELECT title FROM job_vacancies WHERE id = CAST(:jid AS uuid)"
                jb: dict[str, Any] = {"jid": str(job_id)}
                if company_id:
                    job_sql += " AND company_id = CAST(:co2 AS uuid)"
                    jb["co2"] = str(company_id)
                job_result = await db.execute(text(job_sql), jb)
                job = job_result.fetchone()
                scope_label = f"da vaga \"{job.title}\"" if job else "da vaga"
            elif company_id:
                result = await db.execute(text("""
                    SELECT stage, COUNT(*) as cnt,
                           COUNT(*) FILTER (WHERE status = 'active') as active_cnt
                    FROM vacancy_candidates
                    WHERE company_id = CAST(:co AS uuid)
                    GROUP BY stage
                """), {"co": str(company_id)})
                scope_label = "geral da empresa"
            else:
                return ActionResult(
                    status="error",
                    message="Não foi possível determinar o escopo da análise de funil.",
                    error_detail="No job_id or company_id",
                    action_type="analyze_funnel",
                )

            rows = result.fetchall()

        STAGE_ORDER = ["Novos", "Triagem", "Entrevista", "Proposta", "Contratado"]
        stage_map = {r.stage: {"total": r.cnt, "active": r.active_cnt} for r in rows}
        total_all = sum(r.cnt for r in rows)

        lines = [f"**Análise de Funil {scope_label}:**\n"]
        funnel_data = []
        prev_count = None
        for stage_name in STAGE_ORDER:
            data = stage_map.get(stage_name, {"total": 0, "active": 0})
            pct = round((data["total"] / total_all * 100), 1) if total_all > 0 else 0
            conv = ""
            if prev_count and prev_count > 0:
                conv_rate = round((data["total"] / prev_count * 100), 1)
                conv = f" (conversão: {conv_rate}%)"
            lines.append(f"  {stage_name}: **{data['total']}** ({pct}%){conv}")
            funnel_data.append({"stage": stage_name, "count": data["total"], "pct": pct})
            prev_count = data["total"]

        rejected = stage_map.get("Rejeitado", {}).get("total", 0) + stage_map.get("Reprovado", {}).get("total", 0)
        if rejected:
            lines.append(f"\n  Rejeitados/Reprovados: **{rejected}**")

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"funnel": funnel_data, "total": total_all, "rejected": rejected, "job_id": job_id},
            action_type="analyze_funnel",
        )
    except Exception as e:
        logger.warning(f"analyze_funnel failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao analisar funil.",
            error_detail=str(e),
            action_type="analyze_funnel",
        )
