"""
Job Actions — closed-loop vacancy management actions.

Handles: pause_job, close_job, duplicate_job, reopen_job
"""
import logging
from datetime import datetime
from typing import Any

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
    return None


async def _pause_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                UPDATE job_vacancies
                SET status = 'Pausada', updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """), {"job_id": job_id})
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="pause_job",
                )
            await db.commit()
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
        logger.warning(f"Direct pause_job failed, falling back to domain: {e}")
        return None


async def _close_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                UPDATE job_vacancies
                SET status = 'Fechada', closed_at = NOW(), updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """), {"job_id": job_id})
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="close_job",
                )
            await db.commit()
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
        logger.warning(f"Direct close_job failed, falling back to domain: {e}")
        return None


async def _duplicate_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        new_title = params.get("new_title", "")
        job_title = params.get("job_title", "a vaga")

        async with AsyncSessionLocal() as db:
            original = await db.execute(text("""
                SELECT title, company_id, department, location, work_model,
                       employment_type, seniority_level, description, requirements,
                       salary, salary_range, benefits, priority, recruiter,
                       recruiter_email, manager, manager_email, tags
                FROM job_vacancies
                WHERE id = CAST(:job_id AS uuid)
            """), {"job_id": job_id})
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
        logger.warning(f"Direct duplicate_job failed, falling back to domain: {e}")
        return None


async def _reopen_job(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "")
        job_title = params.get("job_title", "a vaga")

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                UPDATE job_vacancies
                SET status = 'Ativa', closed_at = NULL, updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
            """), {"job_id": job_id})
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada",
                    error_detail="Vaga não encontrada no sistema",
                    action_type="reopen_job",
                )
            await db.commit()
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
        logger.warning(f"Direct reopen_job failed, falling back to domain: {e}")
        return None


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
