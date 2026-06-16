"""Contextual search hints for the GlobalSearchModal.

Returns 3-5 actionable hints based on:
- Pending tasks for user today
- Job vacancies in draft/pending approval states
- Candidates awaiting screening
- Page context (adjusts priority of hint types)

Multi-tenancy: company_id ALWAYS from JWT via Depends(require_company_id).
Fail-safe: every data fetch wrapped in try/except — endpoint NEVER returns 500.
Fallback hints are always returned when nothing else loads.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search-contextual"])


@router.get("/contextual-hints")
async def get_contextual_hints(
    page_context: Optional[str] = Query(None, description="Current page slug, e.g. jobs, funil-de-talentos"),
    limit: int = Query(5, ge=1, le=10),
    company_id: str = Depends(require_company_id),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """Returns contextual action hints for the search modal.

    Always returns HTTP 200 — data errors degrade gracefully to fallback hints.
    """
    hints = []
    user_id = str(current_user.id) if current_user and current_user.id else None

    # ── 1. Pending tasks for the user ──────────────────────────────────────
    try:
        from app.repositories.tasks_repository import TasksRepository
        tasks_repo = TasksRepository(db)
        tasks = await tasks_repo.get_pending_tasks(
            company_id=company_id,
            user_id=user_id,
            limit=3,
        )
        for task in (tasks or [])[:2]:
            title = getattr(task, "title", None) or "Tarefa pendente"
            hints.append({
                "label": f"Task: {title[:50]}",
                "action": "navigate",
                "target": "/tasks",
                "context": "Tarefas",
                "icon": "check_square",
            })
    except Exception as exc:
        logger.debug("contextual_hints: tasks fetch failed: %s", exc)

    # ── 2. Vacancies in draft/pending states ───────────────────────────────
    try:
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository
        jobs_repo = JobVacancyCrudRepository(db)

        STATUS_LABELS = {
            "rascunho": "Rascunho",
            "enriquecida": "Aguardando publicação",
            "aguardando_aprovacao": "Aguardando aprovação",
        }
        draft_jobs = []
        for status in ("rascunho", "enriquecida", "aguardando_aprovacao"):
            try:
                batch = await jobs_repo.list_vacancies(
                    company_id=company_id,
                    status=status,
                    limit=2,
                )
                draft_jobs.extend(list(batch))
                if len(draft_jobs) >= 2:
                    break
            except Exception:
                pass

        for job in draft_jobs[:2]:
            job_title = getattr(job, "title", None) or "Vaga"
            job_id = getattr(job, "id", None)
            job_status = getattr(job, "status", "")
            status_label = STATUS_LABELS.get(job_status, job_status)
            target = f"/jobs/{job_id}?tab=edit" if job_id else "/recrutar"
            hints.append({
                "label": f"{job_title[:45]} — {status_label}",
                "action": "navigate",
                "target": target,
                "context": "Vagas",
                "icon": "briefcase",
            })
    except Exception as exc:
        logger.debug("contextual_hints: jobs fetch failed: %s", exc)

    # ── 3. Candidates awaiting screening ──────────────────────────────────
    try:
        from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
        vc_repo = VacancyCandidateRepository(db)
        result = await vc_repo.list_for_talent_funnel(
            company_id=company_id,
            status="awaiting_screening",
            limit=5,
        )
        count = result.get("total", 0) if isinstance(result, dict) else 0
        if count > 0:
            label = (
                f"{count} candidato aguardando triagem"
                if count == 1
                else f"{count} candidatos aguardando triagem"
            )
            hints.append({
                "label": label,
                "action": "navigate",
                "target": "/funil-de-talentos?filter=pending_screening",
                "context": "Candidatos",
                "icon": "users",
            })
    except Exception as exc:
        logger.debug("contextual_hints: candidates fetch failed: %s", exc)

    # ── Fallback if nothing loaded ────────────────────────────────────────
    if not hints:
        hints = [
            {
                "label": "Criar nova vaga",
                "action": "navigate",
                "target": "/recrutar",
                "context": "Vagas",
                "icon": "plus",
            },
            {
                "label": "Ver pipeline de candidatos",
                "action": "navigate",
                "target": "/funil-de-talentos",
                "context": "Candidatos",
                "icon": "users",
            },
            {
                "label": "Verificar tasks do dia",
                "action": "navigate",
                "target": "/tasks",
                "context": "Tarefas",
                "icon": "check_square",
            },
        ]

    # ── Adjust order by page_context ──────────────────────────────────────
    if page_context:
        ctx = page_context.lower()
        if "funil" in ctx or "candidat" in ctx:
            hints = sorted(hints, key=lambda h: (0 if h["context"] == "Candidatos" else 1))
        elif "job" in ctx or "recrutar" in ctx or "vaga" in ctx:
            hints = sorted(hints, key=lambda h: (0 if h["context"] == "Vagas" else 1))
        elif "task" in ctx:
            hints = sorted(hints, key=lambda h: (0 if h["context"] == "Tarefas" else 1))

    return {"hints": hints[:limit]}
