"""Celery tasks: briefing dispatch reading briefing_frequency from HiringPolicy canonical.

Wave 3 Camada 3 Item 2 — registered 2026-05-22
Sprint D+1 partial — refactored 2026-05-22
==========================================

Contexto (ADR-WT-2025 §Sprint D+1 partial)
------------------------------------------
ATE 2026-05-22 (Sprint D fim): briefing_frequency vivia em
``AlertConfig.briefing_frequency``. Este modulo lia direto da tabela
legacy.

A PARTIR de Sprint D+1 partial (migration 174_briefing_frequency_canonical):
- Canonical: ``CompanyHiringPolicy.communication_rules.briefing_frequency``
  (JSONB, mesmo local que `lia_tone`, `preferred_channel`, `ai_persona`).
- Legacy read fallback: ``AlertConfig.briefing_frequency`` (deprecated,
  removido em Sprint D+2 DROP TABLE alert_configs ~2026-09-22).

Read-shadow pattern:
1. Tenta ler ``HiringPolicy.communication_rules.briefing_frequency``.
2. Se NULL/empty (HiringPolicy ainda nao backfilled OR tenant fora da
   migration 174 OR novo tenant criado pos-migration sem briefing config):
   - Fall back para ``AlertConfig.briefing_frequency`` legacy.
   - Emite counter ``briefing_dispatch_legacy_alertconfig_read_total``
     (canary metric — Sprint D+1 vai usar esse counter pra decidir
      quando remover endpoint /alerts/config pre-sunset).
   - Emite logger.warning estruturado.
3. Se AlertConfig tambem NULL/empty: default canonical 'weekly'.

REGRA 4 (no silent fallback): briefing_frequency invalido (None, "" ou
valor fora do enum) NAO causa skip silencioso — emite warning log
explicito e contabiliza em metric ``briefing_dispatched_total{result=skip_invalid_frequency}``.

Multi-tenancy: filtra tenants por ``company_id`` (NOT NULL). Tenants
fora do HiringPolicy backfill cairao no fallback AlertConfig (com
counter de canary).

ADR-001 Repository: usa ``HiringPolicyRepository.get_by_company`` +
``AlertConfigRepository`` (legacy fallback path). Para briefing content
em si, delega ao ``BriefingService.generate_daily_briefing`` (legacy,
marcado deprecated; nao mexer ate handoff Rails completo).
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

# Canonical briefing_frequency enum (mirror HiringPolicy.communication_rules schema)
CANONICAL_FREQUENCIES = frozenset(
    {"daily", "weekly", "twice_daily", "monthly"}
)

# Canonical default when neither HiringPolicy nor AlertConfig has value.
# Matches ADR-WT-2025 + UI default in plataforma-lia AlertPreferencesPanel.
DEFAULT_BRIEFING_FREQUENCY = "weekly"


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


async def _resolve_briefing_frequency(
    db, company_id: str
) -> tuple[str | None, str]:
    """Read briefing_frequency canonical from HiringPolicy, fallback to AlertConfig.

    Returns:
        (frequency, source) where source in {'hiring_policy', 'alert_config_legacy',
        'default'}. ``frequency`` may be None if neither source has value AND we
        want caller to apply DEFAULT_BRIEFING_FREQUENCY.

    Read-shadow pattern (Sprint D+1 partial):
        1. canonical: HiringPolicy.communication_rules.briefing_frequency
        2. legacy: AlertConfig.briefing_frequency (emits canary counter)
        3. default: DEFAULT_BRIEFING_FREQUENCY (caller decides)
    """
    from app.domains.hiring_policy.repositories.hiring_policy_repository import (
        HiringPolicyRepository,
    )

    # Step 1: canonical read from HiringPolicy
    repo = HiringPolicyRepository(db)
    policy = await repo.get_by_company(company_id)
    if policy is not None:
        comm_rules = policy.communication_rules or {}
        canonical_freq = comm_rules.get("briefing_frequency")
        if canonical_freq and canonical_freq in CANONICAL_FREQUENCIES:
            return canonical_freq, "hiring_policy"

    # Step 2: legacy fallback to AlertConfig (emit canary counter)
    legacy_freq = await _legacy_alertconfig_briefing_frequency(db, company_id)
    if legacy_freq:
        _emit_legacy_alertconfig_read_counter(company_id)
        logger.warning(
            "[briefing_dispatch] fallback HiringPolicy.communication_rules.briefing_frequency "
            "missing for company=%s, reading legacy AlertConfig.briefing_frequency=%r "
            "(Sprint D+1 partial — migrate via migration 174_briefing_frequency_canonical)",
            company_id,
            legacy_freq,
        )
        return legacy_freq, "alert_config_legacy"

    # Step 3: no source — caller defaults
    return None, "default"


async def _legacy_alertconfig_briefing_frequency(
    db, company_id: str
) -> str | None:
    """Legacy read path: AlertConfig.briefing_frequency for the given company.

    Returns first valid canonical value found (any active config for the
    company). None if no row or invalid value.

    NOTE: this is the ONLY function in this module that still references
    AlertConfig. It is the read-shadow fallback path during Sprint D+1
    partial transition. Will be removed in Sprint D+1 final (sunset
    2026-08-22) when endpoint /alerts/config also goes away.
    """
    from sqlalchemy import select

    from app.models.alert import AlertConfig  # legacy fallback only

    result = await db.execute(
        select(AlertConfig.briefing_frequency).where(
            AlertConfig.is_active.is_(True),
            AlertConfig.company_id == company_id,
            AlertConfig.briefing_frequency.is_not(None),
        )
    )
    rows = result.scalars().all()
    for freq in rows:
        if freq and freq in CANONICAL_FREQUENCIES:
            return freq
    return None


def _emit_legacy_alertconfig_read_counter(company_id: str | None) -> None:
    """Emit canary counter ``briefing_dispatch_legacy_alertconfig_read_total``.

    Tracked in app/shared/observability/canary_metrics.py. Spike = tenants
    not yet backfilled by migration 174 (or new tenants without HiringPolicy
    briefing_frequency set). Pre-sunset (2026-08-22) Paulo monitors this
    counter to decide whether to remove the legacy fallback path early.
    """
    try:
        from app.shared.observability.canary_metrics import (
            briefing_dispatch_legacy_alertconfig_read_total,
        )

        if briefing_dispatch_legacy_alertconfig_read_total is not None:
            briefing_dispatch_legacy_alertconfig_read_total.labels(
                company_id_hash=_hash_company_id(company_id),
            ).inc()
    except Exception:  # pragma: no cover — metric must never break dispatch
        pass


async def _list_alert_configs_for_frequency(db, frequencies: list[str]) -> list[Any]:
    """Repository-pattern wrapper — load active AlertConfig rows matching
    any of ``frequencies``. Filters out global (company_id NULL) configs.

    Sprint D+1 partial (2026-05-22): legacy listing path kept for
    backward-compat with existing test_briefing_scheduler.py sensors.
    Source-of-truth resolution per company happens in
    _resolve_briefing_frequency (HiringPolicy canonical, AlertConfig
    fallback). This listing function continues to query AlertConfig
    because it carries the per-user mapping (user_id), which HiringPolicy
    does not. Sprint D+2 will rebase user_id lookup along with DROP TABLE
    alert_configs.
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


async def _list_tenants_with_briefing_frequency(
    db, frequencies: list[str]
) -> list[dict[str, Any]]:
    """Discover (company_id, user_id, freq, source) tuples whose CANONICAL
    briefing_frequency (HiringPolicy preferred, AlertConfig fallback) is in
    ``frequencies``.

    Sprint D+1 partial bridges both sources during the read-shadow window:

    1. Load active AlertConfig rows (carry user_id mapping).
    2. For each unique company_id, resolve canonical frequency via
       _resolve_briefing_frequency (HiringPolicy.communication_rules
       preferred; AlertConfig.briefing_frequency fallback w/ canary counter).
    3. Filter: keep only tuples whose RESOLVED frequency is in ``frequencies``.

    Returns list of dicts: {company_id, user_id, frequency, source}.

    NOTE: this is the path used by _dispatch_for_frequency_async (canonical).
    The older _list_alert_configs_for_frequency above is kept as a thin
    backward-compat hook for existing sensors.
    """
    from sqlalchemy import select

    from app.models.alert import AlertConfig  # legacy: holds user_id mapping

    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.is_active.is_(True),
            AlertConfig.company_id.is_not(None),
        )
    )
    configs = list(result.scalars().all())

    matched: list[dict[str, Any]] = []
    # Resolve canonical frequency per unique company_id (HiringPolicy is per-company,
    # so cache lookups to avoid N+1 reads).
    freq_cache: dict[str, tuple[str | None, str]] = {}
    for cfg in configs:
        company_id = cfg.company_id
        if not company_id:
            continue
        if company_id not in freq_cache:
            freq_cache[company_id] = await _resolve_briefing_frequency(
                db, str(company_id)
            )
        resolved_freq, source = freq_cache[company_id]
        if resolved_freq and resolved_freq in frequencies:
            matched.append(
                {
                    "company_id": str(company_id),
                    "user_id": cfg.user_id,
                    "frequency": resolved_freq,
                    "source": source,
                }
            )
    return matched


async def _dispatch_for_frequency_async(frequencies: list[str], task_name: str) -> dict:
    """Shared core: load tenants, dispatch via BriefingService per user.

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
        tenants = await _list_tenants_with_briefing_frequency(db, frequencies)

        for tenant in tenants:
            company_id = tenant["company_id"]
            user_id = tenant["user_id"]
            freq = tenant["frequency"]

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

            # Defense: user_id may be None for company-scope config.
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
        # Sprint 7C Part 1.5b/c: audit dim 5 canonical.
        try:
            from app.shared.compliance.audit_service import AuditService as _AuditBriefing
            async def _audit_briefing():
                _svc = _AuditBriefing()
                await _svc.log_decision(
                    company_id="__system__",
                    agent_name="briefing_dispatch",
                    decision_type="dispatch",
                    action="briefing.dispatch_daily",
                    decision="executed",
                    reasoning=[f"frequency_label='daily'", f"result={result}"],
                    criteria_used=[],
                )
            asyncio.run(_audit_briefing())
        except Exception:
            pass  # audit best-effort
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
        # Sprint 7C Part 1.5b/c: audit dim 5 canonical.
        try:
            from app.shared.compliance.audit_service import AuditService as _AuditBriefing
            async def _audit_briefing():
                _svc = _AuditBriefing()
                await _svc.log_decision(
                    company_id="__system__",
                    agent_name="briefing_dispatch",
                    decision_type="dispatch",
                    action="briefing.dispatch_weekly",
                    decision="executed",
                    reasoning=[f"frequency_label='weekly'", f"result={result}"],
                    criteria_used=[],
                )
            asyncio.run(_audit_briefing())
        except Exception:
            pass  # audit best-effort
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
        # Sprint 7C Part 1.5b/c: audit dim 5 canonical.
        try:
            from app.shared.compliance.audit_service import AuditService as _AuditBriefing
            async def _audit_briefing():
                _svc = _AuditBriefing()
                await _svc.log_decision(
                    company_id="__system__",
                    agent_name="briefing_dispatch",
                    decision_type="dispatch",
                    action="briefing.dispatch_monthly",
                    decision="executed",
                    reasoning=[f"frequency_label='monthly'", f"result={result}"],
                    criteria_used=[],
                )
            asyncio.run(_audit_briefing())
        except Exception:
            pass  # audit best-effort
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
