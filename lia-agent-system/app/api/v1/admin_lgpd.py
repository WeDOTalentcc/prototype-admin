"""
Admin endpoints para LGPD cleanup manual.

Endpoints:
  POST /api/v1/admin/lgpd/run-cleanup   — dispara cleanup via Celery (dry_run=true padrão)
  GET  /api/v1/admin/lgpd/cleanup-status — contagem de registros pendentes de deleção
  GET  /api/v1/admin/lgpd/retention-policy — exibe política de retenção configurada
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.core.database import get_db

router = APIRouter(prefix="/admin/lgpd", tags=["Admin - LGPD"])


@router.post("/run-cleanup", response_model=None)
async def trigger_lgpd_cleanup(
    dry_run: bool = Query(True, description="Simular sem deletar (default: True para segurança)"),
    _user=Depends(require_admin),
):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Dispara cleanup LGPD manual via Celery.

    - dry_run=true (padrão): apenas simula, retorna contagem sem deletar
    - dry_run=false: executa deleção real (requer confirmação explícita)
    """
    from app.jobs.celery_tasks import run_lgpd_cleanup_task
    task = run_lgpd_cleanup_task.delay(dry_run=dry_run)
    return {
        "task_id": task.id,
        "dry_run": dry_run,
        "status": "queued",
        "message": f"LGPD cleanup {'simulado' if dry_run else 'real'} agendado (task_id={task.id})",
    }


@router.get("/cleanup-status", response_model=None)
async def get_cleanup_status(
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Retorna contagem de registros pendentes de deleção LGPD.

    Útil para monitoramento e auditoria pré-go-live (LGPD Art. 16).
    Não executa nenhuma deleção.
    """
    from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS, get_pending_deletions_count
    counts = await get_pending_deletions_count(db)
    return {
        **counts,
        "retention_policy_days": RETENTION_DAYS,
        "schedule": "Diário 02h Brasília (Celery Beat: lgpd-cleanup-daily)",
    }


@router.get("/retention-policy", response_model=None)
async def get_retention_policy(
    _user=Depends(require_admin),
):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Retorna a política de retenção de dados configurada (LGPD Art. 16).
    """
    from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
    return {
        "retention_days": RETENTION_DAYS,
        "schedule": "Diário 02h Brasília (Celery Beat: lgpd-cleanup-daily)",
        "dry_run_default": True,
        "tables_covered": [
            "candidates", "vacancy_candidates", "ai_consumption",
            "lia_opinions (CASCADE via FK — OCEAN/personality data)",
            "conversation_messages", "chat_messages", "interview_notes",
            "screening_tasks", "fairness_audit_log",
        ],
        "lgpd_article": "Art. 16 — dados pessoais serão eliminados após o término do tratamento",
    }
