"""
Job Actions — closed-loop vacancy management actions.

Handles: pause_job, close_job, duplicate_job, reopen_job
"""
import logging
from datetime import datetime
from typing import Any

from app.orchestrator.action_handlers._handler_hooks import log_action_audit, sync_to_rails

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
    elif action_id == "suggest_salary":
        return await _suggest_salary(params, context)
    elif action_id == "generate_jd_direct":
        return await _generate_jd_direct(params, context)
    elif action_id == "duplicate_job":
        return await _duplicate_job(params, context)
    elif action_id == "reopen_job":
        return await _reopen_job(params, context)
    elif action_id == "set_job_urgent":
        return await _set_job_urgent(params, context)
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
                sql += " AND company_id = CAST(:co AS uuid)"
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
        await sync_to_rails("job_paused", "job", str(job_id))

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
                sql += " AND company_id = CAST(:co AS uuid)"
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
        await sync_to_rails("job_closed", "job", str(job_id))

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
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        new_title = params.get("new_title", "")
        job_title = params.get("job_title", "a vaga")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            select_sql = """
                SELECT title, company_id, department, location, work_model,
                       employment_type, seniority_level, description, requirements,
                       salary, salary_range, benefits, priority, recruiter,
                       recruiter_email, manager, manager_email, tags
                FROM job_vacancies
                WHERE id = CAST(:job_id AS uuid)
            """
            select_bind: dict[str, Any] = {"job_id": job_id}
            if company_id:
                select_sql += " AND company_id = CAST(:co AS uuid)"
                select_bind["co"] = str(company_id)
            original = await db.execute(text(select_sql), select_bind)
            row = original.fetchone()
            if not row:
                return ActionResult(
                    status="error",
                    message="Vaga original não encontrada",
                    error_detail="Vaga original não encontrada no sistema",
                    action_type="duplicate_job",
                )

            new_id = str(uuid_mod.uuid4())
            final_title = new_title if new_title else f"{row.title} (Cópia)"

            await db.execute(text("""
                INSERT INTO job_vacancies (
                    id, title, company_id, department, location, work_model,
                    employment_type, seniority_level, description, requirements,
                    salary, salary_range, benefits, priority, recruiter,
                    recruiter_email, manager, manager_email, tags,
                    status, created_at, updated_at
                ) VALUES (
                    CAST(:new_id AS uuid), :title, :company_id, :department, :location, :work_model,
                    :employment_type, :seniority_level, :description, :requirements,
                    :salary, :salary_range, :benefits, :priority, :recruiter,
                    :recruiter_email, :manager, :manager_email, :tags,
                    'Ativa', NOW(), NOW()
                )
            """), {
                "new_id": new_id, "title": final_title,
                "company_id": row.company_id, "department": row.department,
                "location": row.location, "work_model": row.work_model,
                "employment_type": row.employment_type, "seniority_level": row.seniority_level,
                "description": row.description, "requirements": row.requirements,
                "salary": row.salary, "salary_range": row.salary_range,
                "benefits": row.benefits, "priority": row.priority,
                "recruiter": row.recruiter, "recruiter_email": row.recruiter_email,
                "manager": row.manager, "manager_email": row.manager_email,
                "tags": row.tags,
            })
            await db.commit()

        await log_action_audit("duplicate_job", company_id, job_vacancy_id=new_id)
        await sync_to_rails("job_created", "job", new_id)

        return ActionResult(
            status="executed",
            message=f"Vaga **{job_title}** duplicada com sucesso. Nova vaga: **{final_title}**.",
            data={
                "job_id": job_id,
                "new_job_id": new_id,
                "job_title": job_title,
                "new_title": final_title,
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
                sql += " AND company_id = CAST(:co AS uuid)"
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
        await sync_to_rails("job_reopened", "job", str(job_id))

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
                update_sql += " AND company_id = CAST(:co AS uuid)"
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
        await sync_to_rails("job_updated", "job", str(job_id), {"priority": "Urgente"})

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


async def _suggest_salary(params: dict, context: dict):
    """WZ-003: Return salary benchmark for a job title/seniority/location."""
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

        from app.domains.job_management.agents.wizard_tool_registry import _wrap_get_salary_benchmarks
        result = await _wrap_get_salary_benchmarks(
            job_title=job_title,
            seniority=seniority,
            location=location,
        )

        market = result.get("market_range", {})
        min_sal = market.get("min")
        max_sal = market.get("max")
        rec = result.get("recommendation", "")
        confidence = market.get("confidence", "low")

        if min_sal and max_sal:
            lines = [
                f"**Benchmark salarial — {job_title} ({seniority.title()})**\n",
                f"📍 Mercado: **{location}**",
                f"💰 Faixa: **R$ {min_sal:,.0f}** – **R$ {max_sal:,.0f}**",
            ]
            if confidence == "high":
                lines.append("📊 Baseado em dados de mercado atualizados")
            if rec:
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
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao consultar benchmark salarial. Tente novamente.",
            error_detail=str(exc),
            action_type="suggest_salary",
        )


async def _generate_jd_direct(params: dict, context: dict):
    """WZ-002: Generate a structured job description directly from extracted params."""
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

        # Try to call the enrichment service first
        company_id = context.get("company_id") if context else None
        try:
            from app.domains.job_management.agents.wizard_tool_registry import _wrap_generate_enriched_jd
            enriched = await _wrap_generate_enriched_jd(
                title=title,
                seniority=seniority,
                detected_skills=skills,
                company_id=str(company_id) if company_id else None,
            )
            # If enrichment succeeded, build message from sections
            sections_data = enriched.get("sections", [])
            if sections_data:
                jd_lines = [f"**Descrição de Vaga — {title}**\n"]
                for sec in sections_data[:5]:  # up to 5 sections
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

        # Template-based fallback
        skills_text = "\n".join(f"- {s}" for s in skills[:6]) if skills else "- Habilidades técnicas relevantes para o cargo"
        jd = f"""**{title} — Descrição de Vaga**

**Sobre a Vaga**
Buscamos um(a) profissional para atuar como **{title}** ({seniority}), contribuindo diretamente para os objetivos estratégicos da empresa.

**Responsabilidades**
- Liderar e executar projetos relacionados a {title}
- Colaborar com equipes multifuncionais
- Propor melhorias de processos e boas práticas
- Apresentar resultados e métricas para stakeholders

**Requisitos Técnicos**
{skills_text}
- Experiência prévia em funções similares
- Inglês intermediário (desejável)

**Competências Comportamentais**
- Comunicação clara e objetiva
- Autonomia e proatividade
- Visão analítica e orientação a dados
- Trabalho em equipe e colaboração

**Benefícios**
- Salário competitivo com benchmark de mercado
- Vale Refeição / Alimentação
- Plano de Saúde e Odontológico
- Possibilidade de trabalho híbrido
- Ambiente de crescimento e aprendizado contínuo"""

        return ActionResult(
            status="executed",
            message=jd.strip(),
            data={"title": title, "skills": skills, "seniority": seniority},
            action_type="generate_jd_direct",
        )
    except Exception as exc:
        logger.warning(f"_generate_jd_direct failed: {exc}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao gerar a descrição de vaga. Tente novamente.",
            error_detail=str(exc),
            action_type="generate_jd_direct",
        )
