"""
Drift Batch Job — E.3

Itera todas as empresas ativas e executa evaluate_and_alert() de cada uma.
Celery-ready: pode ser wrappado em @celery.task em Ciclo F.

Referências:
- screening-compliance §7 (monitoramento contínuo de drift)
- wedo-governance Production Readiness #10 (alertas automáticos periódicos)
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile
from app.shared.services.drift_alert_service import drift_alert_service

logger = logging.getLogger(__name__)


async def run_drift_check_all_companies(
    db: AsyncSession,
    notify_user_id: str | None = None,
) -> dict:
    """
    Executa drift check para todas as empresas ativas.

    Celery-ready: pode ser wrappado em @celery.task em Ciclo F sem alterações.

    Args:
        db: AsyncSession de banco de dados.
        notify_user_id: ID do usuário que receberá alertas de drift. Opcional.

    Returns:
        dict com chaves: checked, drifted, errors
    """
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.is_active == True)  # noqa: E712
    )
    companies = result.scalars().all()

    summary = {"checked": 0, "drifted": 0, "errors": 0}

    for company in companies:
        try:
            status = await drift_alert_service.evaluate_and_alert(
                db, company.id, notify_user_id=notify_user_id
            )
            summary["checked"] += 1
            if status.drift_detected:
                summary["drifted"] += 1
        except Exception:
            logger.exception(
                "drift_job: falha no drift check company=%s", company.id
            )
            summary["errors"] += 1

    logger.info(
        "drift_job: batch concluído checked=%d drifted=%d errors=%d",
        summary["checked"],
        summary["drifted"],
        summary["errors"],
    )
    return summary
