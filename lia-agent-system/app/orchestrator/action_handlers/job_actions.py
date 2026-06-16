"""
Job Actions — closed-loop vacancy management actions.

Handles: pause_job, close_job, duplicate_job, reopen_job
"""
import logging
from datetime import datetime
from typing import Any

from app.core.database import AsyncSessionLocal
from app.domains.job_management.services.job_clone_service import job_clone_service
from app.orchestrator.action_handlers._handler_hooks import log_action_audit

logger = logging.getLogger(__name__)


async def execute_job_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    """Route job actions to specific handler."""
    if action_id == "pause_job":
        return await _pause_job(params, context)
    elif action_id == "close_job":
        return await _close_job(params, context)
    elif action_id == "duplicate_job":
        return await _duplicate_job(params, context)
    elif action_id == "reopen_job":
        return await _reopen_job(params, context)
    elif action_id == "set_job_urgent":
        return await _set_job_urgent(params, context)
    # Recovery #5 (2026-05-23) — branches restaurados (merge incident 02361f41c).
    elif action_id == "suggest_salary":
        return await _suggest_salary(params, context)
    elif action_id == "generate_jd_direct":
        return await _generate_jd_direct(params, context)
    return None


async def _pause_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            sql = """
                UPDATE job_vacancies
                SET status = 'Pausada', updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """
            bind: dict[str, Any] = {"job_id": job_id}
            if company_id:
                sql += " AND company_id = :co"
                bind["co"] = str(company_id)
            result = await db.execute(text(sql), bind)
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="pause_job",
                )
            await db.commit()

        await log_action_audit("pause_job", company_id, job_vacancy_id=str(job_id))

        return ActionResult(
            status="executed",
            message=f"Vaga **{job_title}** pausada com sucesso.",
            data={
                "job_id": job_id,
                "job_title": job_title,
                "paused_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="pause_job",
        )
    except Exception as e:
        logger.warning(f"pause_job failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao pausar a vaga.",
            error_detail=str(e),
            action_type="pause_job",
        )


async def _close_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            sql = """
                UPDATE job_vacancies
                SET status = 'Fechada', closed_at = NOW(), updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """
            bind: dict[str, Any] = {"job_id": job_id}
            if company_id:
                sql += " AND company_id = :co"
                bind["co"] = str(company_id)
            result = await db.execute(text(sql), bind)
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="close_job",
                )
            await db.commit()

        await log_action_audit("close_job", company_id, job_vacancy_id=str(job_id))

        return ActionResult(
            status="executed",
            message=f"Vaga **{job_title}** fechada com sucesso.",
            data={
                "job_id": job_id,
                "job_title": job_title,
                "closed_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="close_job",
        )
    except Exception as e:
        logger.warning(f"close_job failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao fechar a vaga.",
            error_detail=str(e),
            action_type="close_job",
        )


async def _duplicate_job(params: dict[str, Any], context: dict[str, Any]):
    """Duplicate a vacancy via the canonical JobCloneService.

    Canonical-fix (ADR-001 + T-1166): this handler MUST NOT reimplement cloning
    with raw inline SQL. `JobCloneService.clone_from_template` is the single
    producer — it clones job DATA only (no candidates), creates the copy as a
    DRAFT (status Rascunho, never auto-published as active), and copies the full canonical
    FIELDS_TO_CLONE set (incl. `responsibilities`, `technical_requirements`,
    `languages`, `behavioral_competencies`, `screening_questions`,
    `interview_stages`, ...). Reusing it keeps a single source of truth and
    avoids the broken short-field/auto-publish copy this handler used to build.
    """
    from app.orchestrator.action_executor import ActionResult
    try:
        job_id = params.get("job_id", "")
        new_title = params.get("new_title", "") or None
        job_title = params.get("job_title", "a vaga")
        company_id = context.get("company_id") if context else None
        created_by = context.get("user_id") if context else None

        if not company_id:
            return ActionResult(
                status="error",
                message="Empresa não identificada para duplicar a vaga.",
                error_detail="company_id ausente no contexto (multi-tenancy)",
                action_type="duplicate_job",
            )

        async with AsyncSessionLocal() as db:
            # Resolve the source vacancy (id, job_id, or title) within the tenant.
            source = await job_clone_service.get_job_by_id_or_title(
                db, str(job_id), str(company_id)
            )
            if not source:
                return ActionResult(
                    status="error",
                    message="Vaga original não encontrada",
                    error_detail="Vaga original não encontrada no sistema",
                    action_type="duplicate_job",
                )

            result = await job_clone_service.clone_from_template(
                db=db,
                source_job_id=source.id,
                company_id=str(company_id),
                new_title=new_title,
                created_by=created_by,
            )

        if not result.get("success"):
            return ActionResult(
                status="error",
                message="Erro ao duplicar a vaga.",
                error_detail=result.get("error") or "Falha ao clonar a vaga (produtor canonical).",
                action_type="duplicate_job",
            )

        created = result.get("created_job") or {}
        new_id = created.get("id")
        final_title = created.get("title")
        new_status = created.get("status")

        await log_action_audit("duplicate_job", company_id, job_vacancy_id=new_id)

        return ActionResult(
            status="executed",
            message=(
                f"Vaga **{job_title}** duplicada com sucesso. "
                f"Nova vaga (rascunho): **{final_title}**."
            ),
            data={
                "job_id": str(source.id),
                "new_job_id": new_id,
                "job_title": job_title,
                "new_title": final_title,
                "status": new_status,
                "duplicated_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="duplicate_job",
        )
    except Exception as e:
        logger.warning(f"duplicate_job failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao duplicar a vaga.",
            error_detail=str(e),
            action_type="duplicate_job",
        )


async def _reopen_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            sql = """
                UPDATE job_vacancies
                SET status = 'Ativa', closed_at = NULL, updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """
            bind: dict[str, Any] = {"job_id": job_id}
            if company_id:
                sql += " AND company_id = :co"
                bind["co"] = str(company_id)
            result = await db.execute(text(sql), bind)
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="reopen_job",
                )
            await db.commit()

        await log_action_audit("reopen_job", company_id, job_vacancy_id=str(job_id))

        return ActionResult(
            status="executed",
            message=f"Vaga **{job_title}** reaberta com sucesso.",
            data={
                "job_id": job_id,
                "job_title": job_title,
                "reopened_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="reopen_job",
        )
    except Exception as e:
        logger.warning(f"reopen_job failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao reabrir a vaga.",
            error_detail=str(e),
            action_type="reopen_job",
        )


async def _set_job_urgent(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "") or (context or {}).get("job_vacancy_id", "")
        job_title = params.get("job_title", "a vaga")
        reason = params.get("reason", "")
        company_id = context.get("company_id") if context else None

        if not job_id:
            return ActionResult(
                status="error",
                message="Informe a vaga para classificar como urgente.",
                error_detail="Missing job_id",
                action_type="set_job_urgent",
            )

        async with AsyncSessionLocal() as db:
            update_sql = """
                UPDATE job_vacancies
                SET priority = 'Urgente', updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """
            update_bind: dict[str, Any] = {"job_id": str(job_id)}
            if company_id:
                update_sql += " AND company_id = :co"
                update_bind["co"] = str(company_id)
            result = await db.execute(text(update_sql), update_bind)
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada.",
                    error_detail="Job not found",
                    action_type="set_job_urgent",
                )
            await db.commit()

        await log_action_audit("set_job_urgent", company_id, job_vacancy_id=str(job_id))

        return ActionResult(
            status="executed",
            message=f"Vaga **{job_title}** classificada como **urgente**.",
            data={
                "job_id": job_id, "job_title": job_title,
                "priority": "Urgente", "reason": reason,
                "updated_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="set_job_urgent",
        )
    except Exception as e:
        logger.warning(f"set_job_urgent failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao classificar vaga como urgente.",
            error_detail=str(e),
            action_type="set_job_urgent",
        )


# ---------------------------------------------------------------------------
# Recovery #5 (2026-05-23) — handlers restored.
#
# 2 helpers perdidos pelo merge commit 02361f41c em 2026-05-01. Trio canonical:
#   - handlers em job_actions.py (esses 2 abaixo)
#   - elif branches em execute_job_action (acima)
#   - entries em intents_config.py ("sugerir_salario" + "gerar_jd")
#
# Sem essas 3 peças sincronizadas, LLM não despacha "sugere salário pro
# cargo X" nem "gera descrição da vaga Y". Cai em fallback silent.
#
# Dependência migrated: ``_fetch_market_range`` foi pra wizard_tool_registry
# (canonical) — usamos por import cross-module abaixo. ``_generate_jd_direct``
# usa ``jd_enrichment_service`` canonical + template fallback.
# ---------------------------------------------------------------------------
async def _suggest_salary(params: dict, context: dict):
    """Return a salary benchmark for a job title / seniority / location."""
    from app.orchestrator.action_executor import ActionResult
    try:
        job_title = params.get("job_title") or params.get("title", "")
        location = params.get("location", "Brasil")
        seniority = params.get("seniority", "pleno")

        if not job_title:
            return ActionResult(
                status="error",
                message="Qual cargo você quer pesquisar o salário?",
                action_type="suggest_salary",
            )

        # _fetch_market_range vive em wizard_tool_registry pós-migração (Task #850).
        from app.domains.job_management.agents.wizard_tool_registry import (
            _fetch_market_range,
        )
        market = await _fetch_market_range(job_title, seniority, location)
        min_sal = market.get("min")
        max_sal = market.get("max")
        rec = (
            f"Sem histórico interno. Benchmark de mercado para {seniority}: "
            f"R$ {min_sal:,.0f}–R$ {max_sal:,.0f}."
        ) if min_sal and max_sal else ""
        result = {"market_range": market}

        if min_sal and max_sal:
            lines = [
                f"**Benchmark salarial — {job_title} ({seniority.title()})**\n",
                f"📍 Mercado: **{location}**",
                f"💰 Faixa sugerida: **R$ {min_sal:,.0f}** – **R$ {max_sal:,.0f}**",
                f"📊 Baseado em dados do mercado brasileiro de tecnologia",
            ]
            if rec and "Sem histórico" not in rec:
                lines.append(f"\n{rec}")
            message = "\n".join(lines)
        else:
            message = (
                f"Não encontrei benchmark de mercado específico para **{job_title}**. "
                f"Para {seniority} em {location}, recomendo consultar Glassdoor, "
                f"LinkedIn Salaries ou pesquisas salariais do setor."
            )

        return ActionResult(
            status="executed",
            message=message,
            data=result,
            action_type="suggest_salary",
        )
    except Exception as exc:
        logger.warning(f"_suggest_salary failed: {exc}")
        return ActionResult(
            status="error",
            message="Erro ao consultar benchmark salarial. Tente novamente.",
            error_detail=str(exc),
            action_type="suggest_salary",
        )


async def _generate_jd_direct(params: dict, context: dict):
    """Generate a structured job description directly from extracted params."""
    from app.orchestrator.action_executor import ActionResult
    try:
        title = params.get("job_title") or params.get("title", "")
        skills = params.get("skills") or []
        seniority = params.get("seniority", "Pleno")

        if not title:
            return ActionResult(
                status="error",
                message="Qual é o cargo para a descrição de vaga?",
                action_type="generate_jd_direct",
            )

        company_id = context.get("company_id") if context else None
        try:
            # Task #850: chamada canonical ao JD enrichment service.
            from app.domains.job_management.services.jd_enrichment_service import (
                jd_enrichment_service,
            )
            enriched = await jd_enrichment_service.generate_enriched_jd(
                title=title,
                seniority=seniority,
                detected_skills=skills,
                company_id=str(company_id) if company_id else None,
            )
            sections_data = enriched.get("sections", [])
            if sections_data:
                jd_lines = [f"**Descrição de Vaga — {title}**\n"]
                for sec in sections_data[:5]:
                    sec_name = sec.get("section", "")
                    suggestions = sec.get("suggestions", [])
                    if sec_name and suggestions:
                        jd_lines.append(f"\n**{sec_name}**")
                        for s in suggestions[:3]:
                            val = s.get("value", "")
                            if val:
                                jd_lines.append(f"- {val}")
                if len(jd_lines) > 2:
                    return ActionResult(
                        status="executed",
                        message="\n".join(jd_lines),
                        data=enriched,
                        action_type="generate_jd_direct",
                    )
        except Exception:
            pass  # Fall through to template

        # Template-based fallback — build dynamic responsibilities from skills.
        skills_text = "\n".join(f"- {s}" for s in skills[:6]) if skills else "- Habilidades técnicas relevantes para o cargo"

        dynamic_resps = [f"- Liderar iniciativas de {title} alinhadas à estratégia do produto"]
        agile_skills = [s for s in skills if any(k in s.lower() for k in ["ágeis", "agil", "scrum", "kanban", "sprint"])]
        data_skills = [s for s in skills if any(k in s.lower() for k in ["dados", "data", "sql", "analytics", "bi"])]
        if agile_skills:
            dynamic_resps.append(f"- Gerenciar backlog e cerimônias ágeis (Scrum/Kanban)")
        if data_skills:
            dynamic_resps.append(f"- Tomar decisões orientadas a dados e definir métricas de produto (KPIs, OKRs)")
        dynamic_resps += [
            "- Colaborar com engenharia, design e stakeholders para entrega de valor",
            "- Mapear e priorizar oportunidades de melhoria de produto",
        ]
        resps_text = "\n".join(dynamic_resps[:5])

        jd = (
            f"**{title} — Descrição de Vaga**\n\n"
            f"**Sobre a Vaga**\n"
            f"Buscamos um(a) {title} ({seniority}) para impulsionar nossa "
            f"estratégia de produto, unindo visão de negócio, análise de dados "
            f"e execução ágil.\n\n"
            f"**Responsabilidades**\n{resps_text}\n\n"
            f"**Requisitos Técnicos**\n{skills_text}\n"
            f"- Experiência prévia em funções similares de produto\n"
            f"- Inglês intermediário (desejável)\n"
        )

        return ActionResult(
            status="executed",
            message=jd,
            data={"title": title, "seniority": seniority, "skills": skills, "source": "template_fallback"},
            action_type="generate_jd_direct",
        )
    except Exception as exc:
        logger.warning(f"_generate_jd_direct failed: {exc}")
        return ActionResult(
            status="error",
            message="Erro ao gerar descrição de vaga.",
            error_detail=str(exc),
            action_type="generate_jd_direct",
        )
