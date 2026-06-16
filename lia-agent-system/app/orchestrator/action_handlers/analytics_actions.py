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
    # Recovery #4 (2026-05-23) — restaurado branches perdidos pelo merge incident 02361f41c.
    # 2 actions canonical pra intents pt-BR "vagas_sem_candidatos" + "listar_candidatos_por_etapa".
    elif action_id == "vacancies_without_candidates":
        return await _vacancies_without_candidates(params, context)
    elif action_id == "list_candidates_by_stage":
        return await _list_candidates_by_stage(params, context)
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
                WHERE company_id = :co
            """), {"co": str(company_id)})
            jobs = jobs_result.fetchone()

            cands_result = await db.execute(text("""
                SELECT
                    COUNT(DISTINCT candidate_id) as total_candidates,
                    COUNT(*) FILTER (WHERE stage = 'Novos') as stage_new,
                    COUNT(*) FILTER (WHERE stage = 'Triagem') as stage_screening,
                    COUNT(*) FILTER (WHERE stage = 'Entrevista') as stage_interview,
                    COUNT(*) FILTER (WHERE stage = 'Proposta') as stage_offer,
                    COUNT(*) FILTER (WHERE stage IN ('Contratado', 'hired')) as stage_hired,
                    COUNT(*) FILTER (WHERE stage IN ('Rejeitado', 'Reprovado')) as stage_rejected,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)::int as avg_days_in_pipeline
                FROM vacancy_candidates
                WHERE company_id = :co
            """), {"co": str(company_id)})
            cands = cands_result.fetchone()

        lines = ["**Relatório de KPIs de Recrutamento:**\n"]
        lines.append(f"**Vagas:** {jobs.active_jobs} ativas | {jobs.paused_jobs} pausadas | {jobs.closed_jobs} fechadas ({jobs.total_jobs} total)")
        lines.append(f"**Candidatos Únicos:** {cands.total_candidates}")
        lines.append("\n**Distribuição no Pipeline:**")
        lines.append(f"  - Novos: {cands.stage_new}")
        lines.append(f"  - Triagem: {cands.stage_screening}")
        lines.append(f"  - Entrevista: {cands.stage_interview}")
        lines.append(f"  - Proposta: {cands.stage_offer}")
        lines.append(f"  - Contratados: {cands.stage_hired}")
        lines.append(f"  - Rejeitados: {cands.stage_rejected}")
        if cands.avg_days_in_pipeline:
            lines.append(f"\n**Tempo Médio no Pipeline:** {cands.avg_days_in_pipeline} dias")

        hire_rate = 0
        if cands.total_candidates and cands.total_candidates > 0:
            hire_rate = round((cands.stage_hired / cands.total_candidates) * 100, 1) if cands.stage_hired else 0
            lines.append(f"**Taxa de Contratação:** {hire_rate}%")

        ml_predictions = {}
        try:
            from app.services.ml.outcome_predictor import OutcomePredictor
            predictor = OutcomePredictor()
            job_data = {}
            if job_id:
                async with AsyncSessionLocal() as db2:
                    job_row = await db2.execute(text("""
                        SELECT title, department, location, seniority_level, work_model
                        FROM job_vacancies WHERE id = CAST(:jid AS uuid)
                    """), {"jid": str(job_id)})
                    jrow = job_row.fetchone()
                    if jrow:
                        job_data = {
                            "title": jrow.title, "department": jrow.department,
                            "location": jrow.location, "seniority": jrow.seniority_level,
                            "work_model": jrow.work_model,
                        }

            async with AsyncSessionLocal() as db3:
                ttf_pred = await predictor.predict_time_to_fill(db=db3, job_data=job_data, company_id=str(company_id))
                sal_pred = await predictor.predict_optimal_salary(db=db3, job_data=job_data, company_id=str(company_id))

            ttf = {
                "predicted_days": ttf_pred.predicted_days,
                "range_min": ttf_pred.range_min,
                "range_max": ttf_pred.range_max,
                "confidence": ttf_pred.confidence,
                "comparison_to_market": ttf_pred.comparison_to_market,
                "factors": ttf_pred.factors or [],
            }
            sal = {
                "suggested_min": sal_pred.suggested_min,
                "suggested_max": sal_pred.suggested_max,
                "market_percentile": sal_pred.market_percentile,
                "competitive_analysis": sal_pred.competitive_analysis,
                "confidence": sal_pred.confidence,
                "factors": sal_pred.factors or [],
            }
            ml_predictions = {"time_to_fill": ttf, "salary": sal}

            lines.append("\n**Predições ML:**")
            lines.append(f"  - Previsão Time-to-Fill: **{ttf['predicted_days']} dias** ({ttf['range_min']}-{ttf['range_max']}d, {round(ttf['confidence']*100)}% confiança)")
            lines.append(f"  - {ttf['comparison_to_market']}")
            lines.append(f"  - Faixa Salarial Sugerida: **R$ {sal['suggested_min']:,.0f} — R$ {sal['suggested_max']:,.0f}** (P{sal['market_percentile']})")
            lines.append(f"  - {sal['competitive_analysis']}")

            if ttf.get("factors"):
                high_factors = [f for f in ttf["factors"] if f.get("impact") == "high"]
                if high_factors:
                    lines.append("\n**Fatores de Risco (alto impacto):**")
                    for f in high_factors[:3]:
                        lines.append(f"  - ⚠️ {f['name']}: {f['value']}")
        except Exception as ml_err:
            logger.debug(f"ML enrichment skipped: {ml_err}")

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
                "hire_rate": hire_rate,
                "ml_predictions": ml_predictions,
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
                job_sql += " AND company_id = :co"
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
                    funnel_sql += " AND company_id = :co"
                    funnel_bind["co"] = str(company_id)
                funnel_sql += " GROUP BY stage"
                result = await db.execute(text(funnel_sql), funnel_bind)

                job_sql = "SELECT title FROM job_vacancies WHERE id = CAST(:jid AS uuid)"
                jb: dict[str, Any] = {"jid": str(job_id)}
                if company_id:
                    job_sql += " AND company_id = :co2"
                    jb["co2"] = str(company_id)
                job_result = await db.execute(text(job_sql), jb)
                job = job_result.fetchone()
                scope_label = f"da vaga \"{job.title}\"" if job else "da vaga"
            elif company_id:
                result = await db.execute(text("""
                    SELECT stage, COUNT(*) as cnt,
                           COUNT(*) FILTER (WHERE status = 'active') as active_cnt
                    FROM vacancy_candidates
                    WHERE company_id = :co
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


# ---------------------------------------------------------------------------
# Recovery #4 (2026-05-23) — handlers restored.
#
# 2 helpers perdidos pelo merge commit 02361f41c em 2026-05-01. Cadeia inteira
# foi destruída em coordenadamente:
#   - helpers em analytics_actions.py (esses 2 abaixo)
#   - elif branches em execute_analytics_action (acima)
#   - entries em intents_config.py ("vagas_sem_candidatos" + "listar_candidatos_por_etapa")
#
# Restaurado coordenadamente neste commit. Sem essas 3 peças sincronizadas,
# LLM/intent matcher não dispara essas actions, e usuários que perguntam
# "quais vagas estão sem candidatos?" ou "lista candidatos da vaga X na etapa Y"
# caem em fallback silent.
#
# TODO Boy Scout (não escopo deste commit, mas registrado):
# Queries usam `text(...)` raw SQL — viola ADR-001 Repository Pattern. Quando
# tocar nessas funções pra refactor, mover queries pra
# JobVacancyAnalyticsRepository + VacancyCandidateRepository.
# ---------------------------------------------------------------------------
async def _vacancies_without_candidates(params, context):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        company_id = context.get("company_id") if context else None
        days = int(params.get("days", 7))

        if not company_id:
            return ActionResult(
                status="error",
                message="Empresa não identificada para consultar vagas sem candidatos.",
                error_detail="Missing company_id",
                action_type="vacancies_without_candidates",
            )

        async with AsyncSessionLocal() as db:
            from app.core.database import set_tenant_context
            await set_tenant_context(db, str(company_id))

            result = await db.execute(text("""
                SELECT j.id, j.title, j.status, j.created_at,
                       EXTRACT(DAY FROM NOW() - j.created_at)::int as days_open
                FROM job_vacancies j
                LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = j.id
                WHERE vc.id IS NULL
                  AND j.company_id = :co
                  AND j.status = 'Ativa'
                  AND j.created_at < NOW() - INTERVAL '7 days'
                ORDER BY j.created_at ASC
                LIMIT 20
            """), {"co": str(company_id)})
            rows = result.fetchall()

        if not rows:
            return ActionResult(
                status="executed",
                message=(
                    "Todas as vagas têm candidatos. "
                    "Nenhuma vaga ativa está sem candidatos há mais de 7 dias."
                ),
                data={"vacancies_without_candidates": [], "days_threshold": days},
                action_type="vacancies_without_candidates",
            )

        lines = [f"**{len(rows)} vaga(s) sem candidatos há mais de {days} dias:**\n"]
        vacancy_list = []
        for row in rows:
            lines.append(f"- {row.title} ({row.days_open} dias aberta)")
            vacancy_list.append({
                "id": str(row.id),
                "title": row.title,
                "status": row.status,
                "days_open": row.days_open,
            })

        lines.append(
            "\nGostaria que eu inicie a triagem ou busca por candidatos para essas vagas?"
        )

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"vacancies_without_candidates": vacancy_list, "days_threshold": days},
            action_type="vacancies_without_candidates",
        )
    except Exception as e:
        logger.warning(f"vacancies_without_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao consultar vagas sem candidatos.",
            error_detail=str(e),
            action_type="vacancies_without_candidates",
        )


async def _list_candidates_by_stage(params: dict[str, Any], context: dict[str, Any]):
    """KB-006: List candidates in a specific pipeline stage for a job."""
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        job_id = (
            params.get("job_id")
            or (context or {}).get("job_id")
            or (context or {}).get("entity_id")
            or (context or {}).get("job_vacancy_id")
        )
        company_id = (context or {}).get("company_id")
        stage = params.get("stage") or params.get("to_stage")

        if not job_id:
            return ActionResult(
                status="error",
                message="Vaga não identificada. Informe a vaga para listar candidatos por etapa.",
                error_detail="Missing job_id",
                action_type="list_candidates_by_stage",
            )

        async with AsyncSessionLocal() as db:
            from app.core.database import set_tenant_context
            if company_id:
                await set_tenant_context(db, str(company_id))

            # Build query
            rows = []
            for attempt in range(2):
                try:
                    if attempt == 0:
                        if stage:
                            sql = """
                                SELECT c.name, c.current_title, vc.stage, vc.score, vc.lia_score
                                FROM vacancy_candidates vc
                                JOIN candidates c ON c.id = vc.candidate_id
                                WHERE vc.job_vacancy_id = CAST(:job_id AS uuid)
                                  AND LOWER(vc.stage) = LOWER(:stage)
                            """
                        else:
                            sql = """
                                SELECT c.name, c.current_title, vc.stage, vc.score, vc.lia_score
                                FROM vacancy_candidates vc
                                JOIN candidates c ON c.id = vc.candidate_id
                                WHERE vc.job_vacancy_id = CAST(:job_id AS uuid)
                            """
                    else:
                        # Fallback: try short job_id like V0037
                        if stage:
                            sql = """
                                SELECT c.name, c.current_title, vc.stage, vc.score, vc.lia_score
                                FROM vacancy_candidates vc
                                JOIN candidates c ON c.id = vc.candidate_id
                                JOIN job_vacancies jv ON jv.id = vc.job_vacancy_id
                                WHERE jv.job_id = :job_id
                                  AND LOWER(vc.stage) = LOWER(:stage)
                            """
                        else:
                            sql = """
                                SELECT c.name, c.current_title, vc.stage, vc.score, vc.lia_score
                                FROM vacancy_candidates vc
                                JOIN candidates c ON c.id = vc.candidate_id
                                JOIN job_vacancies jv ON jv.id = vc.job_vacancy_id
                                WHERE jv.job_id = :job_id
                            """

                    bind: dict[str, Any] = {"job_id": str(job_id)}
                    if stage:
                        bind["stage"] = stage
                    if company_id:
                        sql += " AND vc.company_id = :co"
                        bind["co"] = str(company_id)
                    sql += " ORDER BY COALESCE(vc.lia_score, vc.score, 0) DESC LIMIT 50"

                    result = await db.execute(text(sql), bind)
                    rows = result.fetchall()
                    break
                except Exception:
                    rows = []
                    continue

        if not rows:
            stage_label = stage or "qualquer etapa"
            return ActionResult(
                status="executed",
                message=f"Nenhum candidato encontrado na etapa **{stage_label}** para esta vaga.",
                data={"candidates": [], "job_id": str(job_id), "stage": stage},
                action_type="list_candidates_by_stage",
            )

        # Group by stage if no specific stage requested
        if stage:
            lines = []
            for i, row in enumerate(rows, 1):
                score = row.lia_score or row.score or 0
                score_str = f" | Score: {score}%" if score else ""
                lines.append(f"{i}. **{row.name}** — {row.current_title or 'N/A'}{score_str}")
            stage_label = stage or rows[0].stage
            msg = f"**Candidatos na etapa {stage_label} ({len(rows)}):**\n\n" + "\n".join(lines)
        else:
            from collections import defaultdict
            by_stage: dict = defaultdict(list)
            for row in rows:
                by_stage[row.stage or "Sem etapa"].append(row.name)
            lines = []
            for s, names in sorted(by_stage.items()):
                lines.append(f"**{s}** ({len(names)}): " + ", ".join(names[:5]) + ("..." if len(names) > 5 else ""))
            msg = f"**Candidatos por etapa ({len(rows)} total):**\n\n" + "\n".join(lines)

        candidates_data = [
            {"name": row.name, "stage": row.stage, "score": row.lia_score or row.score or 0}
            for row in rows
        ]
        return ActionResult(
            status="executed",
            message=msg,
            data={"candidates": candidates_data, "job_id": str(job_id), "stage": stage, "count": len(rows)},
            action_type="list_candidates_by_stage",
        )
    except Exception as e:
        logger.warning(f"list_candidates_by_stage failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao listar candidatos por etapa.",
            error_detail=str(e),
            action_type="list_candidates_by_stage",
        )
