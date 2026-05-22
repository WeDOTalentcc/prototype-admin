"""
WT-2022 P0.SCH1/P0.ALR1/P0.SIG1: Helpers canonical para ler CommunicationSettings tenant-aware.

Decisão Paulo 2026-05-21: ScheduleTab + AlertsTab + SignatureTab estavam ghosts
porque consumers em communication_service.py + email_service.py + alert_dispatcher
usavam constantes hardcoded ou ignoravam toggles.

Status (2026-05-21):
    ✅ Helper canonical criado (este arquivo)
    ❌ Wire em communication_service: _is_within_sending_hours já aceita settings
       (callers TODO passar)
    ❌ Wire em alert_dispatcher: respeitar alerts[].enabled + channel + briefing_frequency
    ❌ Wire em email_service.send_email: anexar settings.signature ao body

## Pattern de uso

    from app.shared.services.communication_settings_consumer import (
        get_company_communication_settings,
        append_signature_to_body,
        is_alert_enabled,
    )

    settings = await get_company_communication_settings(db, company_id)
    if not communication_service._is_within_sending_hours(settings):
        return  # outside sending hours

    body_with_sig = append_signature_to_body(body, settings)
    if is_alert_enabled(settings, "sla_warning"):
        ...
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_company_communication_settings(
    db: "AsyncSession",
    company_id: str,
) -> dict[str, Any]:
    """Load communication_settings per company.

    Returns dict com keys:
      - sending_hours_start, sending_hours_end (int)
      - respect_weekends, respect_holidays (bool)
      - max_messages_per_day (int)
      - signature, signature_html (str)
      - alerts (list[{id, enabled, channel}])
      - briefing_frequency (str)

    Fallback: dict vazio se record nao existe ou DB error.
    """
    try:
        from sqlalchemy import select
        from app.models.observability import CommunicationSettings

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
            "max_messages_per_day": getattr(settings_obj, "max_messages_per_day", 3),
            "signature": getattr(settings_obj, "signature", "") or "",
            "signature_html": getattr(settings_obj, "signature_html", "") or "",
            "alerts": getattr(settings_obj, "alerts", []) or [],
            "briefing_frequency": getattr(settings_obj, "briefing_frequency", "daily"),
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
