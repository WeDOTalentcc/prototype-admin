"""
Drift Alert Service — E.1

Integra ModelDriftService com NotificationService para enviar alertas automáticos
quando drift é detectado em produção.

Referências:
- Crença #7 (Autonomia Progressiva — o sistema avisa antes de o humano perceber)
- wedo-governance §18 (alertas de IA em produção)
- EU AI Act Art. 13 (transparência e supervisão humana)
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.services.model_drift_service import DriftStatus, model_drift_service
from app.services.notification_service import (
    NotificationChannel,
    NotificationType,
    notification_service,
)

logger = logging.getLogger(__name__)

ALERT_CHANNELS = [NotificationChannel.BELL, NotificationChannel.TEAMS]


class DriftAlertService:
    """
    Avalia drift via ModelDriftService e notifica automaticamente quando detectado.

    - 1 trigger → NotificationType.WARNING
    - 2+ triggers (alert_level=="critical") → NotificationType.URGENT
    - drift_detected=False ou notify_user_id=None → sem notificação
    """

    async def evaluate_and_alert(
        self,
        db: AsyncSession,
        company_id: UUID,
        notify_user_id: str | None = None,
    ) -> DriftStatus:
        """
        Avalia drift para a empresa e, se detectado, envia notificação Bell + Teams.

        Args:
            db: AsyncSession de banco de dados.
            company_id: UUID da empresa a ser avaliada.
            notify_user_id: ID do usuário que receberá os alertas. Se None, não notifica.

        Returns:
            DriftStatus com triggers e alert_level preenchidos.
        """
        status = await model_drift_service.evaluate(db, company_id)

        if status.drift_detected and notify_user_id:
            ntype = (
                NotificationType.URGENT
                if status.alert_level == "critical"
                else NotificationType.WARNING
            )
            trigger_names = [t.name for t in status.triggers if t.triggered]
            message = (
                f"Triggers: {', '.join(trigger_names)}. Empresa: {company_id}"
            )

            try:
                await notification_service.send_multi_channel_notification(
                    user_id=notify_user_id,
                    title=f"Model Drift Detectado — {status.alert_level.upper()}",
                    message=message,
                    channels=ALERT_CHANNELS,
                    notification_type=ntype,
                )
                logger.info(
                    "drift_alert: notificação enviada user=%s company=%s level=%s triggers=%s",
                    notify_user_id,
                    company_id,
                    status.alert_level,
                    trigger_names,
                )
            except Exception as exc:
                logger.error(
                    "drift_alert: falha ao enviar notificação user=%s company=%s: %s",
                    notify_user_id,
                    company_id,
                    exc,
                )

        return status


    async def check_agent_health(
        self,
        company_id: str,
        notify_user_id: str | None = None,
        days: int = 30,
    ) -> dict:
        """
        Verifica saúde dos agentes por domínio via ExecutionLogStore.

        Retorna resumo com domínios degradados/estagnados.
        Envia alerta Bell+Teams se notify_user_id fornecido e há domínios críticos.

        Args:
            company_id: ID da empresa.
            notify_user_id: Usuário para receber alertas (opcional).
            days: Janela de análise em dias.

        Returns:
            dict com `healthy`, `degraded`, `stale` e lista `domains`.
        """
        from lia_agents_core.execution_log_store import ExecutionLogStore
        store = ExecutionLogStore()
        domains = await store.get_domain_health(company_id=company_id, days=days)

        unhealthy = [d for d in domains if d["status"] in ("degraded", "stale")]
        result = {
            "total_domains": len(domains),
            "healthy": sum(1 for d in domains if d["status"] == "healthy"),
            "warning": sum(1 for d in domains if d["status"] == "warning"),
            "degraded": sum(1 for d in domains if d["status"] == "degraded"),
            "stale": sum(1 for d in domains if d["status"] == "stale"),
            "domains": domains,
        }

        if unhealthy and notify_user_id:
            names = ", ".join(d["domain"] for d in unhealthy)
            ntype = (
                NotificationType.URGENT
                if any(d["status"] == "degraded" for d in unhealthy)
                else NotificationType.WARNING
            )
            try:
                await notification_service.send_multi_channel_notification(
                    user_id=notify_user_id,
                    title="Saúde de Agentes — Atenção Necessária",
                    message=f"Domínios com problema: {names}. Empresa: {company_id}",
                    channels=ALERT_CHANNELS,
                    notification_type=ntype,
                )
                logger.info(
                    "agent_health_alert: notificação enviada user=%s company=%s domains=%s",
                    notify_user_id,
                    company_id,
                    names,
                )
            except Exception as exc:
                logger.error(
                    "agent_health_alert: falha ao enviar notificação: %s", exc
                )

        return result


drift_alert_service = DriftAlertService()
