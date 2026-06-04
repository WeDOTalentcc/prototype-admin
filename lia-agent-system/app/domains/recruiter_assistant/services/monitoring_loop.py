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
    # Task #1295: canais canônicos (AlertPreference). Default = surfaces in-app.
    channels: list[str] = field(default_factory=lambda: ["bell", "chat"])

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


def _resolve_alert_channels(cfg_channels: dict[str, bool] | None) -> list[str]:
    """Task #1295: dict de canais canônico (AlertPreference) -> lista p/ notificação.

    Preserva os surfaces in-app: quando 'bell' está ativo, também surface no
    'chat' (briefing). Fail-safe para ['bell','chat'] se nada estiver marcado,
    para não perder o alerta silenciosamente (a regra ainda está ENABLED aqui).
    """
    from app.shared.services.alert_config_resolver import channels_to_list

    chans = channels_to_list(cfg_channels)
    if "bell" in chans and "chat" not in chans:
        chans = chans + ["chat"]
    if not chans:
        chans = ["bell", "chat"]
    return chans


class MonitoringLoop:
    _instance: "MonitoringLoop | None" = None

    @classmethod
    def get_instance(cls) -> "MonitoringLoop":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_loop_health(self) -> dict[str, "Any"]:
        """Sprint 4.3 (M) — canonical health snapshot for ops/sensor.

        External monitor (Replit cron, scripts/check_monitoring_loop_alive.py,
        admin endpoint) reads this to detect a stalled or never-started loop.

        Returns:
            dict with:
              running: bool — loop is currently running
              iteration_count: int — total iterations completed
              last_iteration_at: ISO timestamp or None
              consecutive_failures: int — failure streak (resets on success)
              last_error: str | None — last exception message
              check_interval_seconds: int
              is_stale: bool — True if last_iteration_at older than 2×interval
        """
        now = datetime.now(timezone.utc)
        is_stale = True
        last_iso: str | None = None
        if self._last_iteration_at is not None:
            last_iso = self._last_iteration_at.isoformat()
            stale_threshold = self._check_interval * 2
            age_seconds = (now - self._last_iteration_at).total_seconds()
            is_stale = age_seconds > stale_threshold
        return {
            "running": self._running,
            "iteration_count": self._iteration_count,
            "last_iteration_at": last_iso,
            "consecutive_failures": self._consecutive_failures,
            "last_error": self._last_error,
            "check_interval_seconds": self._check_interval,
            "is_stale": is_stale,
            "now": now.isoformat(),
            "last_daily_task_runs": {
                k: v.isoformat() for k, v in self._last_daily_task_runs.items()
            },
            "last_hourly_task_runs": {
                k: v.isoformat() for k, v in self._last_hourly_task_runs.items()
            },
            "last_period_task_runs": {
                k: v.isoformat() for k, v in self._last_period_task_runs.items()
            },
        }

    def _should_run_daily(self, task_name: str) -> bool:
        """Sprint 11.0 — return True if task hasn\'t run in >24h.

        Used to gate daily Celery-migrated tasks in the MonitoringLoop
        iteration (loop runs hourly; daily flag prevents 24× execution).
        """
        last = self._last_daily_task_runs.get(task_name)
        if last is None:
            return True
        elapsed = datetime.now(timezone.utc) - last
        return elapsed.total_seconds() >= 86400  # 24h

    def _should_run_hourly(self, task_name: str) -> bool:
        """Sprint 11.0 — return True if task hasn\'t run in >1h.

        Used for hourly Celery-migrated tasks (since loop default = 3600s,
        usually fires every iteration unless drift).
        """
        last = self._last_hourly_task_runs.get(task_name)
        if last is None:
            return True
        elapsed = datetime.now(timezone.utc) - last
        return elapsed.total_seconds() >= 3600

    def _mark_daily_run(self, task_name: str) -> None:
        """Sprint 11.0 — record successful daily task run."""
        self._last_daily_task_runs[task_name] = datetime.now(timezone.utc)

    def _mark_hourly_run(self, task_name: str) -> None:
        """Sprint 11.0 — record successful hourly task run."""
        self._last_hourly_task_runs[task_name] = datetime.now(timezone.utc)

    def _should_run_with_period(
        self, task_name: str, period_seconds: float,
    ) -> bool:
        """Sprint 11.3 Batch 2 — generic period check.

        Single source of truth for all periodic task gating beyond
        daily/hourly. Used for: 2h safety nets, weekly/monthly briefings.

        Args:
            task_name: identity for tracking in _last_period_task_runs
            period_seconds: target period (7200=2h, 604800=1week, 2592000=30d)
        """
        last = self._last_period_task_runs.get(task_name)
        if last is None:
            return True
        elapsed = datetime.now(timezone.utc) - last
        return elapsed.total_seconds() >= period_seconds

    def _mark_period_run(self, task_name: str) -> None:
        """Sprint 11.3 Batch 2 — record successful periodic task run."""
        self._last_period_task_runs[task_name] = datetime.now(timezone.utc)

    async def _retry_with_backoff(
        self,
        task_name: str,
        coro_factory,
        max_attempts: int = 3,
        backoff_base: float = 60.0,
    ) -> "tuple[bool, Any]":
        """Sprint 11.2 — canonical retry wrapper for migrated Celery tasks.

        Args:
            task_name: name for logging
            coro_factory: callable returning awaitable (called fresh each attempt)
            max_attempts: total attempts (default 3 = initial + 2 retries)
            backoff_base: seconds between attempts, doubled each retry
                          (default: 60s, 120s, 240s = ~7min total worst case)

        Returns:
            tuple[success: bool, result_or_exception]
            - success=True, result=task_return_value
            - success=False, result=last_exception (after exhaust)

        Pattern canonical Sprint 11.3: every migrated task wraps with this.
        Failure does NOT mark _last_daily_task_runs → next iteration retries fresh.
        """
        import asyncio
        last_exc = None
        for attempt in range(max_attempts):
            try:
                result = await coro_factory()
                if attempt > 0:
                    logger.info(
                        "[MonitoringLoop retry] task=%s recovered at attempt %d/%d",
                        task_name, attempt + 1, max_attempts,
                    )
                return True, result
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    backoff = backoff_base * (2 ** attempt)
                    logger.warning(
                        "[MonitoringLoop retry] task=%s attempt %d/%d FAILED: %s. "
                        "Retrying in %.0fs",
                        task_name, attempt + 1, max_attempts, exc, backoff,
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        "[MonitoringLoop retry] task=%s EXHAUSTED %d attempts: %s",
                        task_name, max_attempts, exc, exc_info=True,
                    )
        return False, last_exc

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
        # Sprint 4.3 (M) — observability fields. External monitor reads
        # these via get_loop_health() to detect a stalled or never-started
        # loop. Without this, ops only knew the loop was broken when
        # proactive alerts stopped showing up (silent failure).
        self._last_iteration_at: datetime | None = None
        self._iteration_count: int = 0
        self._consecutive_failures: int = 0
        self._last_error: str | None = None

        # Sprint 11.0 (2026-05-24) — Celery migration canonical pattern.
        # Daily task tracking: each migrated Celery beat task has an entry
        # here. `_should_run_daily(task_name)` returns True if last run was
        # >24h ago OR never. Used to gate daily LGPD compliance jobs,
        # weekly digests, etc. without requiring Celery beat scheduler.
        self._last_daily_task_runs: dict[str, datetime] = {}
        self._last_hourly_task_runs: dict[str, datetime] = {}
        # Sprint 11.3 Batch 2 — generic period tracking (2h, weekly, monthly).
        self._last_period_task_runs: dict[str, datetime] = {}

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
                # Sprint 11.0 (2026-05-24) — execute global daily tasks
                # (Celery migration). Daily flags inside ensure 24h interval.
                try:
                    await self._run_daily_global_tasks()
                except Exception as _daily_exc:
                    logger.error(
                        "[MonitoringLoop] daily global tasks failed: %s",
                        _daily_exc, exc_info=True,
                    )
                # Sprint 4.3 (M) — successful iteration. Update health snapshot.
                self._last_iteration_at = datetime.now(timezone.utc)
                self._iteration_count += 1
                self._consecutive_failures = 0
                self._last_error = None
                logger.info(
                    "[MonitoringLoop healthz] iteration=%d did_work=%s "
                    "at=%s interval=%ds",
                    self._iteration_count, iteration_did_work,
                    self._last_iteration_at.isoformat(),
                    self._check_interval,
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                # Sprint 4.3 (M) — track failure streak for external monitor.
                self._consecutive_failures += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.error(
                    "[MonitoringLoop healthz] iteration FAILED consec=%d: %s",
                    self._consecutive_failures, exc, exc_info=True,
                )
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
                    "SELECT DISTINCT id FROM companies WHERE is_active = true LIMIT 100"
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
            # G9 canonical fix (2026-05-24): also trigger
            # ProactiveDetectorService so hints reach proactive_actions
            # table + WS broadcast + chat surface. Without this piggyback
            # path, the celery beat task `proactive.detect_hints_hourly`
            # is the only producer — and no celery worker runs on the
            # Replit dev environment, so the pipeline was effectively
            # dead. The detector is idempotent (dedup by PENDING status),
            # so this remains safe when celery is eventually deployed.
            try:
                from app.shared.services.proactive_detector_service import (
                    proactive_detector_service,
                )
                from lia_config.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _det_db:
                    await proactive_detector_service.run_for_company(_det_db, tenant_id)
            except Exception as exc:
                logger.warning(
                    "[G9 piggyback] ProactiveDetectorService failed for tenant %s: %s",
                    tenant_id, exc,
                )
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



    async def _run_daily_global_tasks(self) -> None:
        """Sprint 11.0 (2026-05-24) — execute daily-scheduled global tasks
        migrated from Celery beat.

        Currently migrated:
          - dsr.check_overdue_daily (LGPD Art. 20 — was orphan post-Sprint 4.4
            Celery deploy audit; this is the canonical wire-in)

        Sprint 11.3 batches will add more (lgpd.run_cleanup_daily, audit
        lifecycle, voice_retention, etc.)

        Pattern: each task wrapped in try/except so one failure doesn\'t
        block the others. Each tracks its own last_run via _mark_daily_run.
        """
        from lia_config.database import AsyncSessionLocal

        # ─── DSR overdue check (LGPD Art. 20) ───
        # Sprint 11.0 hotfix — migrated Celery task dsr.check_overdue_daily
        task_name = "dsr.check_overdue_daily"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.jobs.tasks.compliance import check_dsr_overdue_canonical
                async with AsyncSessionLocal() as db:
                    return await check_dsr_overdue_canonical(db)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── LGPD cleanup (Art. 16 retenção 90d/180d/365d) ───
        # Sprint 11.3 Batch 1 — migrated lgpd.run_cleanup_daily
        task_name = "lgpd.run_cleanup_daily"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.shared.services.lgpd_cleanup_service import run_cleanup
                return await run_cleanup(dry_run=False)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── Audit S3 lifecycle policy ───
        # Sprint 11.3 Batch 1 — migrated audit.apply_lifecycle_policy
        task_name = "audit.apply_lifecycle_policy"
        if self._should_run_daily(task_name):
            async def _coro():
                from lia_audit.audit_storage import get_audit_storage
                storage = get_audit_storage()
                return await storage.apply_lifecycle_policy()
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── Conversation TTL cleanup (Art. 18 minimização) ───
        # Sprint 11.3 Batch 1 — migrated conversation.ttl_cleanup
        task_name = "conversation.ttl_cleanup"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.shared.services.lgpd_cleanup_service import (
                    run_conversation_ttl_cleanup,
                )
                return await run_conversation_ttl_cleanup(dry_run=False)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── Routing learning adjustments (Sprint 15.3-A Loop A POC) ───
        # Migrated from Celery task routing.recompute_adjustments.
        # Aggregator-side wire. Producer (record_correction) still pending —
        # this loop computes adjustments per active tenant + caches Redis.
        # When producer is wired (future), the loop has data immediately.
        # Ref: SIGNALS_INVENTORY.md (Sprint 15.1 audit).
        task_name = "routing.recompute_adjustments"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.jobs.tasks.ml import (
                    recompute_routing_adjustments_all_tenants_canonical,
                )
                return await recompute_routing_adjustments_all_tenants_canonical()
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )


        # ─── Voice retention purge (LGPD voice recordings) ───
        # Sprint 11.3 Batch 1 — migrated voice_retention.purge_daily
        task_name = "voice_retention.purge_daily"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.jobs.tasks.voice_retention import _run_voice_retention
                return await _run_voice_retention(dry_run=False)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── Briefing daily dispatch — Sprint 11.3 Batch 2 ───
        task_name = "briefing.dispatch_daily"
        if self._should_run_daily(task_name):
            async def _coro():
                from app.jobs.tasks.briefing_dispatch import _dispatch_for_frequency_async
                return await _dispatch_for_frequency_async(
                    frequencies=["daily", "twice_daily"],
                    task_name="briefing.dispatch_daily",
                )
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_daily_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] daily_task=%s result=%s",
                    task_name, result,
                )

        # ─── Briefing weekly dispatch — Sprint 11.3 Batch 2 ───
        task_name = "briefing.dispatch_weekly"
        if self._should_run_with_period(task_name, 604800):  # 7 days
            async def _coro():
                from app.jobs.tasks.briefing_dispatch import _dispatch_for_frequency_async
                return await _dispatch_for_frequency_async(
                    frequencies=["weekly"],
                    task_name="briefing.dispatch_weekly",
                )
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # ─── Briefing monthly dispatch — Sprint 11.3 Batch 2 ───
        task_name = "briefing.dispatch_monthly"
        if self._should_run_with_period(task_name, 2592000):  # 30 days
            async def _coro():
                from app.jobs.tasks.briefing_dispatch import _dispatch_for_frequency_async
                return await _dispatch_for_frequency_async(
                    frequencies=["monthly"],
                    task_name="briefing.dispatch_monthly",
                )
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # ─── Followup pending (every 1h) — Sprint 11.3 Batch 2.5 ───
        task_name = "followup.process_pending"
        if self._should_run_with_period(task_name, 3600):  # 1h
            async def _coro():
                from app.core.database import AsyncSessionLocal
                from app.jobs.followup_service import process_email_followups
                async with AsyncSessionLocal() as db:
                    return await process_email_followups(db)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # ─── WSI abandoned check (every 4h) — Sprint 11.3 Batch 2.5 ───
        task_name = "wsi.check_abandoned"
        if self._should_run_with_period(task_name, 14400):  # 4h
            async def _coro():
                from app.core.database import AsyncSessionLocal
                from app.jobs.wsi_abandoned_service import check_abandoned_sessions
                async with AsyncSessionLocal() as db:
                    return await check_abandoned_sessions(db)
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # ─── DLQ health check (every 1h) — Sprint 11.3 Batch 2.5 ───
        task_name = "health.check_dlq_health"
        if self._should_run_with_period(task_name, 3600):  # 1h
            async def _coro():
                from app.shared.resilience.dlq_service import DLQService
                dlq = DLQService()
                return await dlq.summary()
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # ─── Feedback pending safety net (every 2h) — Sprint 11.3 Batch 2.5+ ───
        task_name = "feedback.process_pending_sends"
        if self._should_run_with_period(task_name, 7200):  # 2h
            async def _coro():
                from app.jobs.tasks.feedback import feedback_process_pending_sends_canonical
                return await feedback_process_pending_sends_canonical()
            ok, result = await self._retry_with_backoff(task_name, _coro)
            if ok:
                self._mark_period_run(task_name)
                logger.info(
                    "[MonitoringLoop healthz] period_task=%s result=%s",
                    task_name, result,
                )

        # Sprint 11.3 Batch 3+ will append more here (memory.compress
        # per-tenant, event-driven refactors).

    async def _check_stale_candidates(self, company_id: str) -> list[ProactiveAlert]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text
        from app.shared.services.alert_config_resolver import resolve_alert_config

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            # Task #1295: honra a config canônica da tela Configurações →
            # Comunicação & Alertas (AlertPreference). Regra desligada = NADA.
            cfg = await resolve_alert_config(
                session, company_id, "candidate_no_interaction"
            )
            if not cfg.is_enabled:
                logger.info(
                    "Stale candidates: alert candidate_no_interaction disabled "
                    "for company=%s — skipping", company_id,
                )
                return alerts

            # threshold (dias) vem da UI; tiers escalam a partir dele.
            min_days = cfg.threshold or STALE_DAYS_LOW
            tier_medium = min_days * 2
            tier_high = min_days * 3
            channels = _resolve_alert_channels(cfg.channels)

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
                      AND vc.updated_at < NOW() - (:min_days * INTERVAL '1 day')
                    ORDER BY vc.updated_at ASC
                    LIMIT 50
                """), {"company_id": company_id, "min_days": min_days})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Stale candidates check failed: %s", exc)
                return alerts

        for row in rows:
            days_idle = int(row[5] or 0)
            if days_idle >= tier_high:
                severity = AlertSeverity.HIGH
            elif days_idle >= tier_medium:
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
                channels=channels,
            ))
        return alerts

    async def _check_sla_risks(self, company_id: str) -> list[ProactiveAlert]:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to JobVacancyCrudRepository
        from lia_config.database import AsyncSessionLocal
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository
        from app.shared.services.alert_config_resolver import resolve_alert_config

        alerts: list[ProactiveAlert] = []
        async with AsyncSessionLocal() as session:
            # Task #1295: honra o toggle/canais da regra sla_near_expiration da
            # tela Configurações. O threshold de % do SLA da UI não se aplica ao
            # cálculo por dias deste check (semântica distinta — fora de escopo);
            # só enable + canais são wired aqui.
            cfg = await resolve_alert_config(
                session, company_id, "sla_near_expiration"
            )
            if not cfg.is_enabled:
                logger.info(
                    "SLA risk: alert sla_near_expiration disabled for "
                    "company=%s — skipping", company_id,
                )
                return alerts
            channels = _resolve_alert_channels(cfg.channels)
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
                channels=channels,
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
                    # Task #1295: canais canônicos por-alerta (AlertPreference),
                    # não mais hardcoded — honra a tela Configurações.
                    channels=alert.channels or ["bell", "chat"],
                    metadata=alert.metadata,
                    expires_in_hours=24,
                )
        except Exception as exc:
            logger.warning("Failed to persist alerts as notifications: %s", exc)


monitoring_loop = MonitoringLoop.get_instance()
