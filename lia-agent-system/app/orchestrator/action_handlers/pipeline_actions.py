"""
Pipeline Actions — task, note, and briefing actions.

Handles: create_task, create_note, generate_daily_briefing
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def execute_pipeline_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    """Route pipeline actions to specific handler."""
    if action_id == "create_task":
        return await _create_task(params, context)
    elif action_id == "create_note":
        return await _create_note(params, context)
    elif action_id == "generate_daily_briefing":
        return await _generate_daily_briefing(params, context)
    elif action_id == "create_automation":
        return await _create_automation(params, context)
    elif action_id == "check_proactive_alerts":
        return await _check_proactive_alerts(params, context)
    return None


def _resolve_ptbr_datetime(date_str: str) -> datetime | None:
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
    except Exception as exc:
        logger.debug("[pipeline_actions] dateutil.parse(%r) failed: %s", date_str, exc, exc_info=True)
        return None


async def _create_task(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from app.domains.automation.services.task_service import TaskService
        from app.models.task import TaskPriority, TaskType

        title = params.get("title", "")
        description = params.get("description", "")
        due_date_str = params.get("due_date", "")
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id")
        priority_str = params.get("priority", "medium")
        task_type_str = params.get("task_type", "general")
        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None  # WT-2022 P0.TASK

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
                company_id=company_id,  # WT-2022 P0.TASK: propaga do agent context
            )

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit
        await log_action_audit("create_task", context.get("company_id") if context else None, candidate_id=candidate_id, job_vacancy_id=job_id)

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


async def _create_note(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

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
                "Note will be created without tenant association."
            )
        if not candidate_id:
            logger.warning(
                "[_create_note] candidate_id is missing from params. "
                "Note will be created without candidate association."
            )
        effective_company_id = str(company_id) if company_id else None
        effective_candidate_id = str(candidate_id) if candidate_id else None

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

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit
        await log_action_audit("create_note", company_id, candidate_id=effective_candidate_id, job_vacancy_id=job_id)

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
        logger.warning(f"create_note failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível salvar a nota. Tente novamente.",
            error_detail=str(e),
            action_type="create_note",
        )


async def _generate_daily_briefing(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from app.shared.services.briefing_service import BriefingService

        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None  # WT-2022 P0.TASK
        if not user_id:
            return ActionResult(
                status="error",
                message="Não foi possível identificar o usuário para gerar o resumo da agenda.",
                action_type="generate_daily_briefing",
            )

        briefing_svc = BriefingService()
        async with AsyncSessionLocal() as db:
            briefing = await briefing_svc.generate_daily_briefing(
                user_id=user_id, db=db, company_id=company_id
            )

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

        _briefing_data = dict(briefing) if isinstance(briefing, dict) else {}
        _briefing_data["_legacy_disclaimer"] = (
            "Os dados deste resumo provêm do serviço legado BriefingService. "
            "Migração para rails_adapter prevista para antes de 2026-07-16."
        )
        return ActionResult(
            status="executed",
            message="\n".join(parts),
            data=_briefing_data,
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


async def _create_automation(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        trigger = params.get("trigger", "")
        action = params.get("action", "")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        stage = params.get("stage", "")
        conditions = params.get("conditions", {})
        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None

        if not trigger or not action:
            return ActionResult(
                status="error",
                message="Informe o gatilho e a ação da automação.",
                error_detail="Missing trigger or action",
                action_type="create_automation",
            )

        automation_id = str(uuid_mod.uuid4())
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                INSERT INTO automation_rules (id, company_id, trigger_type, action_type,
                    job_id, stage, conditions, created_by, is_active, created_at, updated_at)
                VALUES (CAST(:id AS uuid), :co, :trigger, :action,
                    CAST(:jid AS uuid), :stage, :conditions::jsonb, :user_id, true, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": automation_id, "co": str(company_id) if company_id else None,
                "trigger": trigger, "action": action,
                "jid": str(job_id) if job_id else None,
                "stage": stage, "conditions": str(conditions) if conditions else "{}",
                "user_id": user_id,
            })
            await db.commit()

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit
        await log_action_audit("create_automation", company_id, job_vacancy_id=str(job_id) if job_id else None)

        return ActionResult(
            status="executed",
            message=f"Automação criada: quando **{trigger}**, executar **{action}**.",
            data={
                "automation_id": automation_id,
                "trigger": trigger, "action": action,
                "job_id": job_id, "stage": stage,
                "created_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="create_automation",
        )
    except Exception as e:
        logger.warning(f"create_automation failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao criar automação. Tente novamente.",
            error_detail=str(e),
            action_type="create_automation",
        )


async def _check_proactive_alerts(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        company_id = context.get("company_id") if context else None
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")

        if not company_id:
            return ActionResult(
                status="error",
                message="Empresa não identificada para verificar alertas.",
                error_detail="Missing company_id",
                action_type="check_proactive_alerts",
            )

        alerts = []
        async with AsyncSessionLocal() as db:
            stale = await db.execute(text("""
                SELECT COUNT(*) as cnt
                FROM vacancy_candidates vc
                WHERE vc.company_id = :co
                  AND vc.status = 'active'
                  AND vc.updated_at < NOW() - INTERVAL '7 days'
            """), {"co": str(company_id)})
            stale_row = stale.fetchone()
            if stale_row and stale_row.cnt > 0:
                alerts.append(f"**{stale_row.cnt}** candidatos sem atualização há mais de 7 dias")

            overdue_tasks = await db.execute(text("""
                SELECT COUNT(*) as cnt
                FROM tasks
                WHERE assigned_to_user_id = :uid
                  AND status = 'pending'
                  AND due_date < NOW()
            """), {"uid": context.get("user_id", "")})
            overdue_row = overdue_tasks.fetchone()
            if overdue_row and overdue_row.cnt > 0:
                alerts.append(f"**{overdue_row.cnt}** tarefa(s) vencida(s)")

            upcoming = await db.execute(text("""
                SELECT COUNT(*) as cnt
                FROM interviews
                WHERE status = 'scheduled'
                  AND start_time BETWEEN NOW() AND NOW() + INTERVAL '24 hours'
            """))
            upcoming_row = upcoming.fetchone()
            if upcoming_row and upcoming_row.cnt > 0:
                alerts.append(f"**{upcoming_row.cnt}** entrevista(s) nas próximas 24h")

            empty_jobs = await db.execute(text("""
                SELECT COUNT(*) as cnt
                FROM job_vacancies jv
                WHERE jv.company_id = :co
                  AND jv.status = 'Ativa'
                  AND NOT EXISTS (
                    SELECT 1 FROM vacancy_candidates vc
                    WHERE vc.vacancy_id = jv.id AND vc.status = 'active'
                  )
            """), {"co": str(company_id)})
            empty_row = empty_jobs.fetchone()
            if empty_row and empty_row.cnt > 0:
                alerts.append(f"**{empty_row.cnt}** vaga(s) ativa(s) sem candidatos")

        if not alerts:
            return ActionResult(
                status="executed",
                message="Nenhum alerta pendente. Tudo em dia!",
                data={"alerts": [], "status": "all_clear"},
                action_type="check_proactive_alerts",
            )

        lines = ["**Alertas Proativos:**\n"] + [f"  - {a}" for a in alerts]
        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"alerts": alerts, "count": len(alerts)},
            action_type="check_proactive_alerts",
        )
    except Exception as e:
        logger.warning(f"check_proactive_alerts failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao verificar alertas.",
            error_detail=str(e),
            action_type="check_proactive_alerts",
        )
