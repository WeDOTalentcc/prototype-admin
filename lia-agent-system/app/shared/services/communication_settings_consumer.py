"""
WT-2022 P0.SCH1/P0.ALR1/P0.SIG1: Helpers canonical para ler CommunicationSettings tenant-aware.

Decisão Paulo 2026-05-21 + Wave 2 audit 2026-05-22:

    ✅ Helper canonical criado (este arquivo)
    ✅ Wire em communication_service: _is_within_sending_hours aceita settings
       (callers existem). Estende com respect_holidays + timezone tenant-aware.
    ✅ Wire em proactive_detector_service: respeitar alerts[].enabled gate
    ✅ Wire em email_service.send_email: anexa settings.signature ao body

## Pattern de uso (caller canônico)

    from app.shared.services.communication_settings_consumer import (
        get_company_communication_settings,
        append_signature_to_body,
        is_alert_enabled,
        get_alert_channel,
        is_brazilian_holiday,
        check_cooldown_hours,
        check_max_per_candidate,
        get_tenant_now,
    )

    settings = await get_company_communication_settings(db, company_id)
    if not communication_service._is_within_sending_hours(settings):
        return  # outside sending hours / weekend / holiday

    # cooldown check (tenant-aware, sente DB)
    allowed, reason = await check_cooldown_hours(db, candidate_id, company_id, settings)
    if not allowed:
        inc_skip("cooldown"); return

    body_with_sig = append_signature_to_body(body, settings)
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus counter — communication skips (Wave 2 P0.SCH-1 sensor).
# ---------------------------------------------------------------------------
_COMMUNICATION_SKIP_TOTAL = None  # type: ignore[assignment]

try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _name = "communication_skip_total"
    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(_name)
    if _existing is not None:
        _COMMUNICATION_SKIP_TOTAL = _existing
    else:
        _COMMUNICATION_SKIP_TOTAL = _PromCounter(
            _name,
            (
                "Communication dispatcher skip counter (Wave 2 P0.SCH-1). "
                "Increment per skip reason: cooldown / max_per_candidate / holiday / "
                "outside_hours / alert_disabled."
            ),
            labelnames=("reason",),
        )
except Exception as _exc:  # pragma: no cover — prometheus optional
    logger.debug("prometheus_client unavailable for communication_skip_total: %s", _exc)


def inc_communication_skip(reason: str) -> None:
    """Increment communication_skip_total counter (fail-open)."""
    if _COMMUNICATION_SKIP_TOTAL is None:
        return
    try:
        _COMMUNICATION_SKIP_TOTAL.labels(reason=str(reason)).inc()
    except Exception:  # pragma: no cover — fail-open
        pass


# ---------------------------------------------------------------------------
# Holiday detection (Wave 2 P0.SCH-1).
# ---------------------------------------------------------------------------
_HOLIDAYS_CACHE: dict[int, Any] = {}


def is_brazilian_holiday(d: date | None = None) -> bool:
    """Check se data é feriado nacional BR. Fail-safe False se lib indisponível.

    Cobertura: feriados nacionais Brasil via lib . NÃO inclui
    feriados estaduais/municipais (próxima sprint — exige UF tenant-aware).
    """
    target = d or datetime.utcnow().date()
    try:
        import holidays  # type: ignore

        year = target.year
        cached = _HOLIDAYS_CACHE.get(year)
        if cached is None:
            cached = holidays.Brazil(years=year)
            _HOLIDAYS_CACHE[year] = cached
        return target in cached
    except Exception as exc:
        logger.debug(
            "WT-2022 P0.SCH-1: holidays lib unavailable, defaulting False: %s", exc
        )
        return False


# ---------------------------------------------------------------------------
# Tenant timezone resolution (Wave 2 P0.SCH-1).
# ---------------------------------------------------------------------------
def get_tenant_now(settings: dict[str, Any] | None = None) -> datetime:
    """Get current datetime in tenant timezone (default America/Sao_Paulo).

    Fail-safe: se pytz indisponível ou tz inválida, retorna UTC-3 fixo
    (Brasília sem horário de verão).
    """
    s = settings or {}
    tz_name = s.get("timezone") or "America/Sao_Paulo"
    try:
        import pytz  # type: ignore

        tz = pytz.timezone(str(tz_name))
        return datetime.now(tz).replace(tzinfo=None)
    except Exception as exc:
        logger.debug(
            "WT-2022 P0.SCH-1: pytz unavailable or invalid tz %r, falling back UTC-3: %s",
            tz_name, exc,
        )
        return datetime.utcnow() + timedelta(hours=-3)


# ---------------------------------------------------------------------------
# Settings loader (extended Wave 2 com timezone/cooldown/max_per_candidate).
# ---------------------------------------------------------------------------
async def get_company_communication_settings(
    db: "AsyncSession",
    company_id: str,
) -> dict[str, Any]:
    """Load communication_settings per company.

    Returns dict com keys:
      - sending_hours_start, sending_hours_end (int)
      - respect_weekends, respect_holidays (bool)
      - timezone (str, IANA)
      - max_messages_per_day, max_messages_per_candidate (int)
      - cooldown_hours_between_messages (int)
      - signature, signature_html (str)
      - alerts (list[{id, enabled, channel}])
      - briefing_frequency (str)
      - default_email_from_name, default_reply_to (str)
      - require_consent_before_contact (bool)
      - auto_unsubscribe_after_days (int)
      - mailgun_enabled, twilio_enabled (bool)

    Fallback: dict vazio se record nao existe ou DB error.
    """
    try:
        from sqlalchemy import select
        from app.models.communication_settings import CommunicationSettings

        result = await db.execute(
            select(CommunicationSettings).where(
                CommunicationSettings.company_id == company_id
            )
        )
        settings_obj = result.scalar_one_or_none()
        if not settings_obj:
            return {}

        return {
            "sending_hours_start": getattr(settings_obj, "sending_hours_start", 8),
            "sending_hours_end": getattr(settings_obj, "sending_hours_end", 20),
            "respect_weekends": getattr(settings_obj, "respect_weekends", True),
            "respect_holidays": getattr(settings_obj, "respect_holidays", False),
            "timezone": getattr(settings_obj, "timezone", "America/Sao_Paulo") or "America/Sao_Paulo",
            "max_messages_per_day": getattr(settings_obj, "max_messages_per_day", 3),
            "max_messages_per_candidate": getattr(settings_obj, "max_messages_per_candidate", 5),
            "cooldown_hours_between_messages": getattr(settings_obj, "cooldown_hours_between_messages", 24),
            "signature": getattr(settings_obj, "signature", "") or "",
            "signature_html": getattr(settings_obj, "signature_html", "") or "",
            "alerts": getattr(settings_obj, "alerts", []) or [],
            "briefing_frequency": getattr(settings_obj, "briefing_frequency", "daily"),
            "default_email_from_name": getattr(settings_obj, "default_email_from_name", None),
            "default_reply_to": getattr(settings_obj, "default_reply_to", None),
            "require_consent_before_contact": getattr(settings_obj, "require_consent_before_contact", True),
            "auto_unsubscribe_after_days": getattr(settings_obj, "auto_unsubscribe_after_days", 90),
            "mailgun_enabled": getattr(settings_obj, "mailgun_enabled", True),
            "twilio_enabled": getattr(settings_obj, "twilio_enabled", False),
        }
    except Exception as exc:
        logger.warning(
            "WT-2022 P0.SCH1: failed to load communication_settings for company %s: %s "
            "(defaulting to empty dict — caller usa defaults canonical)",
            company_id, exc,
        )
        return {}


def append_signature_to_body(
    body: str,
    settings: dict[str, Any],
    *,
    html: bool = False,
) -> str:
    """WT-2022 P0.SIG1: append signature de communication_settings ao body do email.

    Antes: signature gravava em DB mas ZERO outbound service anexava — ghost setting.
    """
    sig_field = "signature_html" if html else "signature"
    signature = settings.get(sig_field, "")
    if not signature:
        return body

    separator = "<br><br>" if html else "\n\n"
    return f"{body}{separator}{signature}"


def is_alert_enabled(
    settings: dict[str, Any],
    alert_id: str,
) -> bool:
    """WT-2022 P0.ALR1: check se alert tipo X esta enabled em settings.alerts[].

    Antes: 5 toggles enabled/channel gravavam em DB mas dispatcher NAO consultava.
    Fail-safe: True (default ativo) se settings vazio ou alert_id nao listado.
    """
    alerts = settings.get("alerts", [])
    if not isinstance(alerts, list):
        return True  # malformed settings — fail-safe ativo

    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        if str(alert.get("id", "")) == str(alert_id):
            return bool(alert.get("enabled", True))

    # Alert nao listado em settings — default ativo
    return True


def get_alert_channel(
    settings: dict[str, Any],
    alert_id: str,
    default: str = "email",
) -> str:
    """WT-2022 P0.ALR1: get channel preferido pra alert tipo X."""
    alerts = settings.get("alerts", [])
    if not isinstance(alerts, list):
        return default

    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        if str(alert.get("id", "")) == str(alert_id):
            return str(alert.get("channel", default))

    return default


# ---------------------------------------------------------------------------
# Cooldown / per-candidate volume checks (Wave 2 P0.SCH-1).
# ---------------------------------------------------------------------------
async def check_cooldown_hours(
    db: "AsyncSession",
    candidate_id: str,
    company_id: str,
    settings: dict[str, Any],
) -> tuple[bool, str | None]:
    """Check se candidato esta DENTRO do cooldown desde a ultima mensagem.

    Returns:
        (allowed, reason): allowed=True se cooldown ja expirou ou nunca houve msg.
                          reason="cooldown" se bloqueado.
    Fail-safe: True (deixa passar) se DB error.
    """
    cooldown_hours = int(settings.get("cooldown_hours_between_messages", 24) or 24)
    if cooldown_hours <= 0:
        return True, None  # toggle off / zero = sem cooldown

    try:
        from app.domains.communication.repositories.communication_repository import (
            CommunicationRepository,
        )

        since = datetime.utcnow() - timedelta(hours=cooldown_hours)
        logs = await CommunicationRepository(db).list_logs_since(
            candidate_id=candidate_id,
            company_id=company_id,
            since=since,
            statuses=["sent", "delivered", "read"],
        )
        if logs:
            return False, "cooldown"
        return True, None
    except Exception as exc:
        logger.warning(
            "WT-2022 P0.SCH-1 cooldown check failed (fail-open) candidate=%s company=%s: %s",
            candidate_id, company_id, exc,
        )
        return True, None


async def check_max_per_candidate(
    db: "AsyncSession",
    candidate_id: str,
    company_id: str,
    settings: dict[str, Any],
    *,
    window_days: int = 7,
) -> tuple[bool, str | None]:
    """Check se candidato ainda esta abaixo do max_messages_per_candidate em janela rolling.

    Janela canonical: 7 dias (consistente com semana de campanha de pipeline).
    Fail-safe: True (deixa passar) se DB error.
    """
    max_per_candidate = int(settings.get("max_messages_per_candidate", 5) or 5)
    if max_per_candidate <= 0:
        return True, None  # zero = no limit (config defensiva)

    try:
        from app.domains.communication.repositories.communication_repository import (
            CommunicationRepository,
        )

        since = datetime.utcnow() - timedelta(days=window_days)
        logs = await CommunicationRepository(db).list_logs_since(
            candidate_id=candidate_id,
            company_id=company_id,
            since=since,
            statuses=["sent", "delivered", "read"],
        )
        if len(logs) >= max_per_candidate:
            return False, "max_per_candidate"
        return True, None
    except Exception as exc:
        logger.warning(
            "WT-2022 P0.SCH-1 max_per_candidate check failed (fail-open) candidate=%s company=%s: %s",
            candidate_id, company_id, exc,
        )
        return True, None
