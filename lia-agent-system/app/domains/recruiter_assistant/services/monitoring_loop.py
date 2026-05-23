# ADR-001-EXEMPT: complex JOIN/HAVING/SUM(CASE)/EXTRACT patterns + admin cross-tenant scan, no ORM equivalent without builder.
"""
Monitoring Loop — Proactive pipeline monitoring service.

Runs periodically (default: hourly) evaluating pipeline conditions:
- Stale candidates (no movement for N days)
- SLA breach risk (deadlines approaching/expired)
- Funnel drop-off (bottleneck detection)
- Cooling candidates (high-value candidates going idle)

Generates and stores proactive alerts that are surfaced via daily briefing,
chat notifications, and stakeholder escalations.
"""
import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


def _resolve_check_interval_from_env(default: int) -> int:
    """Task #1060: allow ops to tune (or disable) the proactive poll cadence
    without redeploying. Setting MONITORING_LOOP_INTERVAL_SECONDS=0 turns
    the loop into a no-op (used in dev to keep `lia-backend` quiet during
    long Playwright runs)."""
    raw = os.environ.get("MONITORING_LOOP_INTERVAL_SECONDS")
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "MONITORING_LOOP_INTERVAL_SECONDS=%r is not an int — using default %ds",
            raw, default,
        )
        return default
    if value < 0:
        logger.warning(
            "MONITORING_LOOP_INTERVAL_SECONDS=%d is negative — using default %ds",
            value, default,
        )
        return default
    return value


class AlertSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(StrEnum):
    STALE_CANDIDATE = "stale_candidate"
    SLA_BREACH = "sla_breach"
    SLA_APPROACHING = "sla_approaching"
    FUNNEL_BOTTLENECK = "funnel_bottleneck"
    COOLING_CANDIDATE = "cooling_candidate"
    EXTENDED_OPEN_TIME = "extended_open_time"
    NO_CANDIDATES = "no_candidates"
    HIGH_REJECTION_RATE = "high_rejection_rate"


@dataclass
class ProactiveAlert:
    alert_id: str
    category: AlertCategory
    severity: AlertSeverity
    title: str
    message: str
    company_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    job_id: str | None = None
    candidate_id: str | None = None
    candidate_name: str | None = None
    job_title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "company_id": self.company_id,
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "resolved": self.resolved,
        }


STALE_DAYS_LOW = 5
STALE_DAYS_MEDIUM = 10
STALE_DAYS_HIGH = 14
SLA_WARN_DAYS = 7
SLA_CRITICAL_DAYS = 3
EXTENDED_OPEN_DAYS = 45
BOTTLENECK_THRESHOLD = 0.6
MIN_CANDIDATES_FOR_BOTTLENECK = 5
DEFAULT_CHECK_INTERVAL_SECONDS = 3600


class MonitoringLoop:
    _instance: "MonitoringLoop | None" = None

    @classmethod
    def get_instance(cls) -> "MonitoringLoop":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, check_interval: int | None = None):
        self._running = False
        self._task: asyncio.Task | None = None
        # Task #1060: env override (MONITORING_LOOP_INTERVAL_SECONDS); 0 disables the loop entirely.
        self._check_interval = (
            _resolve_check_interval_from_env(DEFAULT_CHECK_INTERVAL_SECONDS)
            if check_interval is None
            else check_interval
        )
        self._idle_backoff_count = 0
        self._alert_store: dict[str, list[ProactiveAlert]] = {}
        self._last_run: dict[str, datetime] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        if self._running:
            return
        # Task #1060: when interval=0 we treat the loop as disabled (used in
        # dev to keep `lia-backend` quiet during long Playwright runs).
        if self._check_interval == 0:
            logger.info(
                "MonitoringLoop disabled (MONITORING_LOOP_INTERVAL_SECONDS=0) — "
                "proactive pipeline checks will not run."
            )
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("MonitoringLoop started (interval=%ds)", self._check_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("MonitoringLoop stopped")

    async def _loop(self) -> None:
        # Task #1060: idle backoff. Quando uma iteração não encontra tenants
        # ativos (cenário típico em dev / Replit fresh DB), não faz sentido
        # voltar a varrer em 1h — multiplica o sleep até 8× pra reduzir
        # carga em logs e DB sem sumir com o loop completamente.
        while self._running:
            iteration_did_work = False
            try:
                iteration_did_work = await self._run_all_tenants()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("MonitoringLoop iteration failed: %s", exc, exc_info=True)
            if iteration_did_work:
                self._idle_backoff_count = 0
            else:
                self._idle_backoff_count = min(self._idle_backoff_count + 1, 3)
            sleep_for = self._check_interval * (2 ** self._idle_backoff_count)
            try:
                await asyncio.sleep(sleep_for)
            except asyncio.CancelledError:
                break

    async def _run_all_tenants(self) -> bool:
        """Returns True if at least one tenant was processed (signals
        the polling loop to keep its base cadence; False triggers idle
        backoff in `_loop`)."""
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text(
                    "SELECT DISTINCT id FROM companies WHERE status = 'active' LIMIT 100"
                ))
                rows = result.fetchall()
                tenant_ids = [str(r[0]) for r in rows]
            except Exception:
                tenant_ids = []

        if not tenant_ids:
            return False

        for tenant_id in tenant_ids:
            try:
                await self.run_checks(tenant_id)
            except Exception as exc:
                logger.error("MonitoringLoop check failed for tenant %s: %s", tenant_id, exc)
        return True

    async def run_checks(self, company_id: str) -> list[ProactiveAlert]:
        logger.info("MonitoringLoop running checks for company %s", company_id)
        alerts: list[ProactiveAlert] = []

        alerts.extend(await self._check_stale_candidates(company_id))
        alerts.extend(await self._check_sla_risks(company_id))
        alerts.extend(await self._check_funnel_bottlenecks(company_id))
        alerts.extend(await self._check_empty_pipelines(company_id))
        alerts.extend(await self._check_high_rejection_rate(company_id))

        self._alert_store[company_id] = alerts
        self._last_run[company_id] = datetime.now(timezone.utc)

        await self._persist_alerts(company_id, alerts)

        logger.info(
            "MonitoringLoop completed for company %s: %d alerts generated",
            company_id, len(alerts),
        )
        return alerts

    def get_alerts(
        self,
        company_id: str,
        severity: str | None = None,
        category: str | None = None,
        unresolved_only: bool = True,
    ) -> list[ProactiveAlert]:
        alerts = self._alert_store.get(company_id, [])
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if category:
            alerts = [a for a in alerts if a.category == category]
        return alerts

    def get_alert_summary(self, company_id: str) -> dict[str, Any]:
        alerts = self.get_alerts(company_id)
        by_severity = {}
        by_category = {}
        for a in alerts:
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
            by_category[a.category] = by_category.get(a.category, 0) + 1
        return {
            "total": len(alerts),
            "by_severity": by_severity,
            "by_category": by_category,
            "last_run": self._last_run.get(company_id, "never"),
        }

    async def _check_stale_candidates(self, company_id: str) -> list[ProactiveAlert]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.candidate_id, vc.stage, vc.vacancy_id,
                           c.name AS candidate_name,
                           jv.title AS job_title,
                           EXTRACT(DAY FROM NOW() - vc.updated_at) AS days_idle
                    FROM vacancy_candidates vc
                    LEFT JOIN candidates c ON c.id = vc.candidate_id
                    LEFT JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE vc.company_id = :company_id
                      AND vc.stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                      AND vc.updated_at < NOW() - INTERVAL '5 days'
                    ORDER BY vc.updated_at ASC
                    LIMIT 50
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Stale candidates check failed: %s", exc)
                return alerts

        for row in rows:
            days_idle = int(row[5] or 0)
            if days_idle >= STALE_DAYS_HIGH:
                severity = AlertSeverity.HIGH
            elif days_idle >= STALE_DAYS_MEDIUM:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW

            alerts.append(ProactiveAlert(
                alert_id=str(uuid.uuid4()),
                category=AlertCategory.STALE_CANDIDATE,
                severity=severity,
                title=f"Candidato parado há {days_idle} dias",
                message=(
                    f"{row[3] or 'Candidato'} está na etapa '{row[1]}' "
                    f"da vaga '{row[4] or row[2]}' sem movimentação há {days_idle} dias."
                ),
                company_id=company_id,
                candidate_id=str(row[0]),
                candidate_name=row[3],
                job_id=str(row[2]),
                job_title=row[4],
                metadata={"days_idle": days_idle, "stage": row[1]},
            ))
        return alerts

    async def _check_sla_risks(self, company_id: str) -> list[ProactiveAlert]:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to JobVacancyCrudRepository
        from lia_config.database import AsyncSessionLocal
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            try:
                repo = JobVacancyCrudRepository(session)
                raw_rows = await repo.get_jobs_near_deadline(company_id=company_id, days_ahead=7)
                rows = [(r["id"], r["title"], r["deadline"], r["days_remaining"]) for r in raw_rows]
            except Exception as exc:
                logger.warning("SLA risk check failed: %s", exc)
                return alerts

        for row in rows:
            days_remaining = int(row[3] or 0)
            if days_remaining < 0:
                severity = AlertSeverity.CRITICAL
                category = AlertCategory.SLA_BREACH
                title = f"SLA expirado há {abs(days_remaining)} dias"
                message = f"A vaga '{row[1]}' teve o prazo expirado há {abs(days_remaining)} dias."
            elif days_remaining <= SLA_CRITICAL_DAYS:
                severity = AlertSeverity.HIGH
                category = AlertCategory.SLA_APPROACHING
                title = f"SLA expira em {days_remaining} dias"
                message = f"A vaga '{row[1]}' expira em {days_remaining} dias. Ação urgente necessária."
            else:
                severity = AlertSeverity.MEDIUM
                category = AlertCategory.SLA_APPROACHING
                title = f"SLA se aproximando ({days_remaining} dias)"
                message = f"A vaga '{row[1]}' tem prazo em {days_remaining} dias."

            alerts.append(ProactiveAlert(
                alert_id=str(uuid.uuid4()),
                category=category,
                severity=severity,
                title=title,
                message=message,
                company_id=company_id,
                job_id=str(row[0]),
                job_title=row[1],
                metadata={"days_remaining": days_remaining, "deadline": str(row[2])},
            ))
        return alerts

    async def _check_funnel_bottlenecks(self, company_id: str) -> list[ProactiveAlert]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.vacancy_id, jv.title, vc.stage, COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE vc.company_id = :company_id
                      AND jv.status = 'Ativa'
                      AND vc.stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                    GROUP BY vc.vacancy_id, jv.title, vc.stage
                    ORDER BY vc.vacancy_id
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Bottleneck check failed: %s", exc)
                return alerts

        job_stages: dict[str, dict[str, Any]] = {}
        for row in rows:
            job_key = str(row[0])
            if job_key not in job_stages:
                job_stages[job_key] = {"title": row[1], "stages": {}, "total": 0}
            job_stages[job_key]["stages"][row[2]] = int(row[3])
            job_stages[job_key]["total"] += int(row[3])

        for job_id, data in job_stages.items():
            total = data["total"]
            if total < MIN_CANDIDATES_FOR_BOTTLENECK:
                continue
            for stage, count in data["stages"].items():
                ratio = count / total
                if ratio >= BOTTLENECK_THRESHOLD:
                    alerts.append(ProactiveAlert(
                        alert_id=str(uuid.uuid4()),
                        category=AlertCategory.FUNNEL_BOTTLENECK,
                        severity=AlertSeverity.MEDIUM,
                        title=f"Gargalo em '{stage}'",
                        message=(
                            f"{count} candidatos ({ratio:.0%}) da vaga '{data['title']}' "
                            f"estão acumulados na etapa '{stage}'."
                        ),
                        company_id=company_id,
                        job_id=job_id,
                        job_title=data["title"],
                        metadata={"stage": stage, "count": count, "ratio": round(ratio, 2)},
                    ))
        return alerts

    async def _check_empty_pipelines(self, company_id: str) -> list[ProactiveAlert]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT jv.id, jv.title,
                           EXTRACT(DAY FROM NOW() - jv.created_at) AS days_open
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc
                        ON vc.vacancy_id = jv.id
                        AND vc.stage NOT IN ('Rejeitado', 'Desistiu')
                    WHERE jv.company_id = :company_id
                      AND jv.status = 'Ativa'
                      AND jv.created_at < NOW() - INTERVAL '3 days'
                    GROUP BY jv.id, jv.title, jv.created_at
                    HAVING COUNT(vc.id) = 0
                    LIMIT 10
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Empty pipeline check failed: %s", exc)
                return alerts

        for row in rows:
            days_open = int(row[2] or 0)
            alerts.append(ProactiveAlert(
                alert_id=str(uuid.uuid4()),
                category=AlertCategory.NO_CANDIDATES,
                severity=AlertSeverity.HIGH if days_open > 7 else AlertSeverity.MEDIUM,
                title=f"Vaga sem candidatos há {days_open} dias",
                message=f"A vaga '{row[1]}' está aberta há {days_open} dias sem nenhum candidato ativo.",
                company_id=company_id,
                job_id=str(row[0]),
                job_title=row[1],
                metadata={"days_open": days_open},
            ))
        return alerts

    async def _check_high_rejection_rate(self, company_id: str) -> list[ProactiveAlert]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.vacancy_id, jv.title,
                           COUNT(*) AS total,
                           SUM(CASE WHEN vc.stage IN ('Rejeitado', 'Desistiu') THEN 1 ELSE 0 END) AS rejected
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE vc.company_id = :company_id
                      AND jv.status = 'Ativa'
                    GROUP BY vc.vacancy_id, jv.title
                    HAVING COUNT(*) >= 5
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Rejection rate check failed: %s", exc)
                return alerts

        for row in rows:
            total = int(row[2])
            rejected = int(row[3])
            rejection_rate = rejected / total if total > 0 else 0
            if rejection_rate >= 0.7:
                alerts.append(ProactiveAlert(
                    alert_id=str(uuid.uuid4()),
                    category=AlertCategory.HIGH_REJECTION_RATE,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Taxa de rejeição alta ({rejection_rate:.0%})",
                    message=(
                        f"A vaga '{row[1]}' tem {rejection_rate:.0%} de rejeição "
                        f"({rejected}/{total} candidatos). Considere revisar os requisitos."
                    ),
                    company_id=company_id,
                    job_id=str(row[0]),
                    job_title=row[1],
                    metadata={"rejection_rate": round(rejection_rate, 2), "total": total, "rejected": rejected},
                ))
        return alerts

    async def _persist_alerts(self, company_id: str, alerts: list[ProactiveAlert]) -> None:
        if not alerts:
            return
        try:
            from lia_messaging.notification_service import (
                NotificationService,
                NotificationType,
            )

            svc = NotificationService()
            high_alerts = [a for a in alerts if a.severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL)]

            for alert in high_alerts[:10]:
                ntype = (
                    NotificationType.URGENT
                    if alert.severity == AlertSeverity.CRITICAL
                    else NotificationType.WARNING
                )
                await svc.create_notification(
                    user_id=f"system:{company_id}",
                    title=alert.title,
                    message=alert.message,
                    notification_type=ntype,
                    category="proactive_alert",
                    source_agent="monitoring_loop",
                    source_trigger=alert.category.value,
                    related_job_id=alert.job_id,
                    related_candidate_id=alert.candidate_id,
                    channels=["bell", "chat"],
                    metadata=alert.metadata,
                    expires_in_hours=24,
                )
        except Exception as exc:
            logger.warning("Failed to persist alerts as notifications: %s", exc)


monitoring_loop = MonitoringLoop.get_instance()
