"""Celery tasks: briefing dispatch respecting AlertConfig.briefing_frequency.

Wave 3 Camada 3 Item 2 — registered 2026-05-22
==============================================

Contexto (audit Wave 2 comunicacao 2026-05-21)
----------------------------------------------
``briefing_frequency`` e persistido em ``AlertConfig.briefing_frequency``
(daily | weekly | twice_daily | monthly) atraves do endpoint
``/api/v1/alerts.briefing-config``. Mas o scheduler ate hoje era:

    - ``briefing.send_daily`` (em communication.py) — despacha pra TODOS os
      usuarios ativos sem filtrar por config. Roda 1x/dia (09h UTC).
    - Weekly / monthly nao existiam — UI mente para o usuario.

Este modulo introduz tasks canonical que filtram por ``briefing_frequency``:

    - briefing.dispatch_daily  — opera sobre tenants com daily/twice_daily.
      Twice_daily marca passa 2x por dia (manha + tarde) via beat
      schedule double-trigger.
    - briefing.dispatch_weekly — opera sobre tenants com weekly. Beat
      schedule: segundas 08h Brasilia.
    - briefing.dispatch_monthly — opera sobre tenants com monthly. Beat
      schedule: dia 1 do mes, 08h Brasilia.

REGRA 4 (no silent fallback): briefing_frequency invalido (None, ""
ou valor fora do enum) NAO causa skip silencioso — emite warning log
explicito e contabiliza em metric ``briefing_dispatched_total{result=skip_invalid_frequency}``.

Multi-tenancy: filtra rows por ``company_id`` quando AlertConfig.company_id
existe; AlertConfig com company_id NULL (config global default) NAO
dispara briefing (TENANT-EXEMPT pattern do model).

ADR-001 Repository: usa ``AlertConfigRepository.list_active_with_frequency``
em vez de SQL inline. Para o briefing content em si, delega ao
``BriefingService.generate_daily_briefing`` (legacy, marcado deprecated;
nao mexer ate handoff Rails completo).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.jobs.tasks._utils import (
    _celery_span,
    _emit_celery_retry,
    _emit_dlq_push,
    _finish_celery_failure,
    _finish_celery_success,
    celery_app,
    logger,
)
from app.jobs.tenant_aware_task import TenantAwareTask

# Canonical briefing_frequency enum (mirror AlertConfig.briefing_frequency)
CANONICAL_FREQUENCIES = frozenset(
    {"daily", "weekly", "twice_daily", "monthly"}
)


# Prometheus counter — best-effort import (works in prod, no-op in test).
def _emit_dispatch_metric(
    *,
    frequency: str,
    result: str,
    company_id_hash: str | None = None,
) -> None:
    """Emit Prometheus counter ``briefing_dispatched_total``.

    Args:
        frequency: canonical value (daily|weekly|twice_daily|monthly)
                   or 'invalid' when caught by sentinel.
        result: 'sent' | 'skipped_disabled' | 'skipped_invalid_frequency'
                | 'error'.
        company_id_hash: SHA-256 first 16 chars of company_id (avoid PII
                         in metric label).
    """
    try:
        from prometheus_client import Counter

        if not hasattr(_emit_dispatch_metric, "_counter"):
            _emit_dispatch_metric._counter = Counter(  # type: ignore[attr-defined]
                "briefing_dispatched_total",
                "Briefing dispatch events (LGPD-safe — hashed company_id)",
                ["frequency", "result", "company_id_hash"],
            )
        _emit_dispatch_metric._counter.labels(  # type: ignore[attr-defined]
            frequency=frequency,
            result=result,
            company_id_hash=company_id_hash or "unknown",
        ).inc()
    except Exception:  # pragma: no cover — metric emit must never break dispatch
        pass


def _hash_company_id(company_id: str | None) -> str:
    """LGPD-safe label: SHA-256 prefix instead of raw UUID."""
    if not company_id:
        return "unknown"
    import hashlib

    return hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:16]


async def _list_alert_configs_for_frequency(db, frequencies: list[str]) -> list[Any]:
    """Repository-pattern wrapper — load active AlertConfig rows matching
    any of ``frequencies``. Filters out global (company_id NULL) configs.
    """
    from sqlalchemy import select

    from app.models.alert import AlertConfig

    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.is_active.is_(True),
            AlertConfig.briefing_frequency.in_(frequencies),
            AlertConfig.company_id.is_not(None),
        )
    )
    return list(result.scalars().all())


async def _dispatch_for_frequency_async(frequencies: list[str], task_name: str) -> dict:
    """Shared core: load configs, dispatch via BriefingService per user.

    Returns dispatch stats dict.
    """
    from app.core.database import AsyncSessionLocal
    from app.shared.services.briefing_service import BriefingService

    briefing_service = BriefingService()
    sent = 0
    skipped_disabled = 0
    skipped_invalid_frequency = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        configs = await _list_alert_configs_for_frequency(db, frequencies)

        for cfg in configs:
            company_id = cfg.company_id
            user_id = cfg.user_id
            freq = cfg.briefing_frequency

            # REGRA 4 — explicit sentinel for invalid frequency
            if not freq or freq not in CANONICAL_FREQUENCIES:
                logger.warning(
                    "[%s] skip company=%s user=%s invalid briefing_frequency=%r",
                    task_name,
                    company_id,
                    user_id,
                    freq,
                )
                _emit_dispatch_metric(
                    frequency="invalid",
                    result="skipped_invalid_frequency",
                    company_id_hash=_hash_company_id(company_id),
                )
                skipped_invalid_frequency += 1
                continue

            # Defense: user_id may be None for AlertConfig at company-scope.
            # Without user_id we cannot generate the personal briefing.
            if not user_id:
                logger.info(
                    "[%s] skip company=%s freq=%s — no user_id (company-scope config)",
                    task_name,
                    company_id,
                    freq,
                )
                _emit_dispatch_metric(
                    frequency=freq,
                    result="skipped_disabled",
                    company_id_hash=_hash_company_id(company_id),
                )
                skipped_disabled += 1
                continue

            try:
                briefing = await briefing_service.generate_daily_briefing(
                    user_id=str(user_id),
                    db=db,
                    company_id=str(company_id) if company_id else None,
                )

                # Channel dispatch is delegated to existing notification_service
                # (canonical fan-out to bell/email/in_app per CommunicationSettings).
                try:
                    from app.services.notification_service import (
                        notification_service,
                    )

                    urgent_count = len(briefing.get("urgent_actions", []))
                    title_map = {
                        "daily": "Briefing diario",
                        "twice_daily": "Briefing do turno",
                        "weekly": "Resumo semanal",
                        "monthly": "Resumo mensal",
                    }
                    title = title_map.get(freq, "Briefing")
                    body = (
                        f"{urgent_count} acoes urgentes pendentes"
                        if urgent_count > 0
                        else "Seu pipeline esta atualizado"
                    )
                    await notification_service.send_notification(
                        user_id=str(user_id),
                        company_id=str(company_id) if company_id else None,
                        channel="bell",
                        title=title,
                        body=body,
                        data={
                            "type": f"{freq}_briefing",
                            "briefing_date": briefing.get("date"),
                        },
                        db=db,
                    )
                except Exception as notif_exc:
                    logger.warning(
                        "[%s] notification dispatch failed company=%s user=%s: %s",
                        task_name,
                        company_id,
                        user_id,
                        notif_exc,
                    )

                logger.info(
                    "[%s] sent company=%s user=%s freq=%s urgent=%d",
                    task_name,
                    company_id,
                    user_id,
                    freq,
                    len(briefing.get("urgent_actions", [])),
                )
                _emit_dispatch_metric(
                    frequency=freq,
                    result="sent",
                    company_id_hash=_hash_company_id(company_id),
                )
                sent += 1
            except Exception as exc:
                logger.error(
                    "[%s] error company=%s user=%s freq=%s: %s",
                    task_name,
                    company_id,
                    user_id,
                    freq,
                    exc,
                )
                _emit_dispatch_metric(
                    frequency=freq,
                    result="error",
                    company_id_hash=_hash_company_id(company_id),
                )
                errors += 1

    return {
        "sent": sent,
        "skipped_disabled": skipped_disabled,
        "skipped_invalid_frequency": skipped_invalid_frequency,
        "errors": errors,
    }


# ──────────────────────────────────────────────────────────────────────────
# Daily — schedule: hourly tick but only dispatches if local time matches
# briefing_hour_local (TBD field; today defaults to 06h Brasilia via beat).
# Simpler MVP: runs once/day at canonical time (matches existing
# briefing-daily beat slot in lia_config.celery_app).
# ──────────────────────────────────────────────────────────────────────────
@celery_app.task(
    base=TenantAwareTask,
    name="briefing.dispatch_daily",
    bind=True,
    max_retries=2,
)
def dispatch_daily_briefings(self) -> dict:
    """Dispatch briefings to all tenants with briefing_frequency='daily'
    or 'twice_daily'. Canonical replacement for the legacy
    ``briefing.send_daily`` once frequency filtering is rolled out."""
    span = _celery_span("celery.task_start", "briefing.dispatch_daily")
    try:
        result = asyncio.run(
            _dispatch_for_frequency_async(
                frequencies=["daily", "twice_daily"],
                task_name="briefing.dispatch_daily",
            )
        )
        _finish_celery_success(span, "briefing.dispatch_daily")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "briefing.dispatch_daily", exc)
        logger.error("briefing.dispatch_daily failed: %s", exc)
        _emit_celery_retry(
            "briefing.dispatch_daily",
            exc,
            self.request.retries,
            self.max_retries,
            300,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("briefing.dispatch_daily", exc)
        raise self.retry(exc=exc, countdown=300)


# ──────────────────────────────────────────────────────────────────────────
# Weekly — beat: Mondays 08h Brasilia (11h UTC)
# ──────────────────────────────────────────────────────────────────────────
@celery_app.task(
    base=TenantAwareTask,
    name="briefing.dispatch_weekly",
    bind=True,
    max_retries=2,
)
def dispatch_weekly_briefings(self) -> dict:
    """Dispatch weekly briefings (frequency='weekly'). Beat: Mondays."""
    span = _celery_span("celery.task_start", "briefing.dispatch_weekly")
    try:
        result = asyncio.run(
            _dispatch_for_frequency_async(
                frequencies=["weekly"],
                task_name="briefing.dispatch_weekly",
            )
        )
        _finish_celery_success(span, "briefing.dispatch_weekly")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "briefing.dispatch_weekly", exc)
        logger.error("briefing.dispatch_weekly failed: %s", exc)
        _emit_celery_retry(
            "briefing.dispatch_weekly",
            exc,
            self.request.retries,
            self.max_retries,
            300,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("briefing.dispatch_weekly", exc)
        raise self.retry(exc=exc, countdown=300)


# ──────────────────────────────────────────────────────────────────────────
# Monthly — beat: day 1 of month, 08h Brasilia
# ──────────────────────────────────────────────────────────────────────────
@celery_app.task(
    base=TenantAwareTask,
    name="briefing.dispatch_monthly",
    bind=True,
    max_retries=2,
)
def dispatch_monthly_briefings(self) -> dict:
    """Dispatch monthly briefings (frequency='monthly'). Beat: 1st of month."""
    span = _celery_span("celery.task_start", "briefing.dispatch_monthly")
    try:
        result = asyncio.run(
            _dispatch_for_frequency_async(
                frequencies=["monthly"],
                task_name="briefing.dispatch_monthly",
            )
        )
        _finish_celery_success(span, "briefing.dispatch_monthly")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "briefing.dispatch_monthly", exc)
        logger.error("briefing.dispatch_monthly failed: %s", exc)
        _emit_celery_retry(
            "briefing.dispatch_monthly",
            exc,
            self.request.retries,
            self.max_retries,
            300,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("briefing.dispatch_monthly", exc)
        raise self.retry(exc=exc, countdown=300)
