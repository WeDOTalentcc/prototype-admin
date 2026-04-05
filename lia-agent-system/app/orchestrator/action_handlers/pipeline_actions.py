"""
Pipeline Actions — task, note, and briefing actions.

Handles: create_task, create_note, generate_daily_briefing
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def execute_pipeline_action(
    action_id: str,
    params: Dict[str, Any],
    context: Dict[str, Any],
):
    """Route pipeline actions to specific handler."""
    if action_id == "create_task":
        return await _create_task(params, context)
    elif action_id == "create_note":
        return await _create_note(params, context)
    elif action_id == "generate_daily_briefing":
        return await _generate_daily_briefing(params, context)
    return None


def _resolve_ptbr_datetime(date_str: str) -> Optional[datetime]:
    """Resolve Portuguese-language date/time string to datetime."""
    if not date_str:
        return None

    import re as _re
    from datetime import timedelta

    now = datetime.now()
    date_str_lower = date_str.lower().strip()

    hour, minute = None, 0
    time_m = _re.search(
        r"(?:às?|as)\s*(\d{1,2})\s*h?(?::?(\d{2}))?|(\d{1,2})[h:](\d{2})?",
        date_str_lower
    )
    if time_m:
        hour = int(time_m.group(1) or time_m.group(3) or 0)
        minute = int(time_m.group(2) or time_m.group(4) or 0)

    PTBR_WEEKDAYS = {
        "segunda": 0, "terça": 1, "terca": 1,
        "quarta": 2, "quinta": 3, "sexta": 4,
        "sábado": 5, "sabado": 5, "domingo": 6,
    }

    resolved_date = None
    if "amanhã" in date_str_lower or "amanha" in date_str_lower:
        resolved_date = now + timedelta(days=1)
    elif "hoje" in date_str_lower:
        resolved_date = now
    else:
        for ptbr_day, weekday_idx in PTBR_WEEKDAYS.items():
            if ptbr_day in date_str_lower:
                days_ahead = (weekday_idx - now.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                resolved_date = now + timedelta(days=days_ahead)
                break

    if resolved_date is not None:
        h = hour if hour is not None else 9
        return resolved_date.replace(hour=h, minute=minute, second=0, microsecond=0)

    try:
        from dateutil import parser as dt_parser
        parsed = dt_parser.parse(date_str, dayfirst=True, default=now)
        if hour is not None:
            parsed = parsed.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return parsed
    except Exception:
        return None


async def _create_task(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from app.domains.automation.services.task_service import TaskService
        from app.models.task import TaskType, TaskPriority

        title = params.get("title", "")
        description = params.get("description", "")
        due_date_str = params.get("due_date", "")
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id")
        priority_str = params.get("priority", "medium")
        task_type_str = params.get("task_type", "general")
        user_id = context.get("user_id") if context else None

        due_date_val = _resolve_ptbr_datetime(due_date_str)

        priority_map = {
            "low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL,
        }
        type_map = {
            "general": TaskType.GENERAL, "reminder": TaskType.FOLLOW_UP,
            "review": TaskType.CV_REVIEW, "follow_up": TaskType.FOLLOW_UP,
            "alert": TaskType.ALERT, "sourcing": TaskType.SOURCING,
        }
        task_priority = priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
        task_type = type_map.get(task_type_str.lower(), TaskType.GENERAL)

        task_svc = TaskService()
        async with AsyncSessionLocal() as db:
            task = await task_svc.create_task(
                db=db,
                title=title,
                description=description,
                task_type=task_type,
                priority=task_priority,
                created_by_agent="lia_chat",
                assigned_to_user_id=user_id,
                related_job_id=job_id,
                related_candidate_id=candidate_id,
                due_date=due_date_val,
                is_automated=False,
                requires_confirmation=False,
            )

        due_info = f" para **{due_date_str}**" if due_date_str else ""
        action_label = "Lembrete" if task_type_str.lower() in ("reminder", "lembrete") else "Tarefa"
        return ActionResult(
            status="executed",
            message=f"{action_label} **\"{title}\"** criado(a) com sucesso{due_info}.",
            data={
                "task_id": str(task.id),
                "title": title,
                "due_date": due_date_val.isoformat() if due_date_val else None,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "priority": priority_str,
                "created_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="create_task",
        )
    except Exception as e:
        logger.warning(f"TaskService create_task failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível criar a tarefa. Tente novamente.",
            error_detail=str(e),
            action_type="create_task",
        )


async def _create_note(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        import uuid as uuid_mod

        content = params.get("content", "")
        title = params.get("title", content[:60] + ("..." if len(content) > 60 else ""))
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id")
        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None

        note_id = str(uuid_mod.uuid4())
        if not company_id:
            logger.warning(
                "[_create_note] company_id is missing from context. "
                "Note will be created without tenant association. "
                "Ensure the caller provides company_id for proper multi-tenancy."
            )
        if not candidate_id:
            logger.warning(
                "[_create_note] candidate_id is missing from params. "
                "Note will be created without candidate association."
            )
        effective_company_id = str(company_id) if company_id else "00000000-0000-0000-0000-000000000000"
        effective_candidate_id = str(candidate_id) if candidate_id else "00000000-0000-0000-0000-000000000000"

        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                INSERT INTO interview_notes (
                    id, company_id, candidate_id, job_id,
                    general_notes, created_by, created_at, updated_at
                ) VALUES (
                    CAST(:id AS uuid),
                    CAST(:company_id AS uuid),
                    CAST(:candidate_id AS uuid),
                    CAST(:job_id AS uuid),
                    :general_notes, :created_by, NOW(), NOW()
                )
            """), {
                "id": note_id,
                "company_id": effective_company_id,
                "candidate_id": effective_candidate_id,
                "job_id": job_id,
                "general_notes": f"**{title}**\n\n{content}",
                "created_by": user_id or "system",
            })
            await db.commit()

        context_info = ""
        if params.get("candidate_name"):
            context_info = f" vinculada ao candidato **{params['candidate_name']}**"
        elif params.get("job_title"):
            context_info = f" vinculada à vaga **{params['job_title']}**"

        return ActionResult(
            status="executed",
            message=f"Nota salva com sucesso{context_info}.",
            data={
                "note_id": note_id,
                "title": title,
                "content": content,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "created_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="create_note",
        )
    except Exception as e:
        logger.warning(f"Direct create_note failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível salvar a nota. Tente novamente.",
            error_detail=str(e),
            action_type="create_note",
        )


async def _generate_daily_briefing(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.services.briefing_service import BriefingService
        from app.core.database import AsyncSessionLocal

        user_id = context.get("user_id") if context else None
        if not user_id:
            return ActionResult(
                status="error",
                message="Não foi possível identificar o usuário para gerar o resumo da agenda.",
                action_type="generate_daily_briefing",
            )

        briefing_svc = BriefingService()
        async with AsyncSessionLocal() as db:
            briefing = await briefing_svc.generate_daily_briefing(user_id=user_id, db=db)

        summary = briefing.get("summary", {})
        schedule = briefing.get("schedule", [])
        tasks = briefing.get("tasks", [])
        greeting = briefing.get("greeting", "Olá")

        schedule_lines = []
        for item in schedule[:5]:
            t = item.get("time", "")
            title_item = item.get("title", item.get("name", ""))
            schedule_lines.append(f"  • {t} — {title_item}" if t else f"  • {title_item}")

        task_lines = []
        for task in tasks[:5]:
            task_lines.append(f"  • {task.get('title', '')}")

        parts = [f"**{greeting}!** Aqui está o seu resumo para hoje:\n"]
        if summary.get("interviews_today", 0) > 0:
            parts.append(f"📅 **Entrevistas hoje:** {summary['interviews_today']}")
        if summary.get("tasks_today", 0) > 0:
            parts.append(f"✅ **Tarefas pendentes:** {summary['tasks_today']}")
        if summary.get("urgent_count", 0) > 0:
            parts.append(f"⚠️ **Ações urgentes:** {summary['urgent_count']}")
        if schedule_lines:
            parts.append("\n**Agenda de hoje:**\n" + "\n".join(schedule_lines))
        if task_lines:
            parts.append("\n**Tarefas:**\n" + "\n".join(task_lines))
        if not schedule_lines and not task_lines:
            parts.append("Sua agenda está livre hoje! Aproveite para prospectar candidatos ou revisar vagas abertas.")

        return ActionResult(
            status="executed",
            message="\n".join(parts),
            data=briefing,
            action_type="generate_daily_briefing",
        )
    except Exception as e:
        logger.warning(f"generate_daily_briefing failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível gerar o resumo da agenda. Tente novamente.",
            error_detail=str(e),
            action_type="generate_daily_briefing",
        )
