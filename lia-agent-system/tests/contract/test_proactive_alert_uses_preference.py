"""ADR-WT-2025 Sprint A sensor: ProactiveAlertService honors AlertPreference canonical.

Wave 2 P0.A2 (Sprint A): proactive_alert_service.py agora consulta
AlertPreference per-tenant ANTES de aplicar threshold/cooldown/channel. Este
sensor protege contra regressao (se alguem voltar a copiar
ThresholdConfig.DEFAULT_THRESHOLDS hardcoded, testes falham).

Pattern espelha tests/contract/test_alert_detector_uses_template.py (6 detectors).

Cenarios cobertos:
1. is_enabled=False -> alerta nao eh enviado (skip silencioso + log INFO + metric).
2. threshold override (AlertPreference.threshold) -> usado em vez do default.
3. Sem AlertPreference -> fallback em ThresholdConfig.DEFAULT_THRESHOLDS.
4. cooldown_hours override -> respeitado em _can_send_alert.
5. channels override -> propagado pro _send_alert (NotificationChannel mapping).
6. Fail-closed: alert_type sem default NEM tenant -> _can_send_alert retorna False.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


COMPANY_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "user-00000000-0000-0000-0000-000000000001"


def _make_preference_row(
    alert_type: str,
    is_enabled: bool = True,
    threshold: int | None = None,
    cooldown_hours: int | None = None,
    channel_email: bool = True,
    channel_bell: bool = True,
    channel_teams: bool = False,
    channel_whatsapp: bool = False,
    updated_at: datetime | None = None,
):
    """Build a MagicMock que simula AlertPreference ORM row."""
    row = MagicMock()
    row.company_id = COMPANY_ID
    row.user_id = USER_ID
    row.alert_type = alert_type
    row.is_enabled = is_enabled
    row.threshold = threshold
    row.cooldown_hours = cooldown_hours
    row.channel_email = channel_email
    row.channel_bell = channel_bell
    row.channel_teams = channel_teams
    row.channel_whatsapp = channel_whatsapp
    row.updated_at = updated_at or datetime.utcnow()
    return row


@pytest.fixture
def service():
    """Fresh ProactiveAlertService per test (avoid history leak)."""
    from app.domains.automation.services.proactive_alert_service import (
        ProactiveAlertService,
    )
    svc = ProactiveAlertService()
    # Replace notification_service with spec'd mock to avoid side effects.
    # spec=NotificationService impede mockar metodo inexistente (anti-ghost):
    # se o codigo voltar a chamar create_proactive_notification (que nunca
    # existiu), o mock lanca AttributeError em vez de fingir sucesso. Foi esse
    # exato mock-do-ghost que mascarou a entrega quebrada ate 2026-06-09.
    from app.services.notification_service import NotificationService
    svc.notification_service = MagicMock(spec=NotificationService)
    svc.notification_service.send_multi_channel_notification = AsyncMock()
    return svc


@pytest.fixture
def fake_db_factory():
    """Factory que retorna AsyncSession mock pronta pra inject AlertPreference rows.

    Usage:
        db = fake_db_factory([row1, row2])
        # db.execute(select(AlertPreference)) -> scalars().all() == [row1, row2]
    """
    def _build(rows: list[MagicMock]):
        db = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=rows)
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.add = MagicMock()
        db.close = AsyncMock()
        return db
    return _build


# ---------------------------------------------------------------------------
# Test 1: is_enabled=False -> alert skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alert_skipped_when_preference_disabled(service, fake_db_factory) -> None:
    """AlertPreference.is_enabled=False -> _can_send_alert retorna False."""
    from app.domains.automation.services.proactive_alert_service import (
        AlertCondition,
    )

    row = _make_preference_row(
        alert_type="tasks_overdue",
        is_enabled=False,
    )
    db = fake_db_factory([row])

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    service._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    # _can_send_alert deve retornar False (tenant disabled).
    can_send = service._can_send_alert(
        AlertCondition.TASKS_OVERDUE,
        USER_ID,
        company_id=COMPANY_ID,
    )
    assert can_send is False, (
        "Alert tasks_overdue should be skipped when AlertPreference.is_enabled=False"
    )


# ---------------------------------------------------------------------------
# Test 2: tenant threshold override applied
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alert_uses_tenant_threshold_override(service, fake_db_factory) -> None:
    """AlertPreference.threshold -> overrides class-level default."""
    from app.domains.automation.services.proactive_alert_service import (
        AlertCondition,
        ThresholdConfig,
    )

    # Default conversion_rate_low threshold = 5.0
    default_threshold = ThresholdConfig.DEFAULT_THRESHOLDS[
        AlertCondition.CONVERSION_RATE_LOW
    ]["threshold"]
    assert default_threshold == 5.0

    # Tenant sets threshold=15 (much higher; alert fires for any rate < 15%)
    row = _make_preference_row(
        alert_type="conversion_rate_low",
        threshold=15,
    )
    db = fake_db_factory([row])

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    service._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    effective = service._get_effective_threshold(
        AlertCondition.CONVERSION_RATE_LOW, company_id=COMPANY_ID
    )
    assert effective["threshold"] == 15, (
        f"Tenant threshold should override default; got {effective['threshold']}"
    )


# ---------------------------------------------------------------------------
# Test 3: no preference row -> fallback to default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alert_falls_back_to_default_threshold_when_no_preference(
    service, fake_db_factory
) -> None:
    """Sem row em AlertPreference -> usa ThresholdConfig.DEFAULT_THRESHOLDS."""
    from app.domains.automation.services.proactive_alert_service import (
        AlertCondition,
        ThresholdConfig,
    )

    db = fake_db_factory([])  # No preference rows for this tenant.

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    service._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    effective = service._get_effective_threshold(
        AlertCondition.CANDIDATES_STAGNANT, company_id=COMPANY_ID
    )
    expected = ThresholdConfig.DEFAULT_THRESHOLDS[AlertCondition.CANDIDATES_STAGNANT]
    assert effective["threshold_days"] == expected["threshold_days"]
    assert effective["min_count"] == expected["min_count"]


# ---------------------------------------------------------------------------
# Test 4: tenant cooldown_hours respected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alert_respects_tenant_cooldown_hours(service, fake_db_factory) -> None:
    """AlertPreference.cooldown_hours -> overrides class-level cooldown."""
    from app.domains.automation.services.proactive_alert_service import (
        AlertCondition,
    )

    # Default cooldown for OFFERS_PENDING_LONG = 24h.
    # Tenant sets cooldown_hours=1 (much shorter).
    row = _make_preference_row(
        alert_type="offers_pending_long",
        cooldown_hours=1,
    )
    db = fake_db_factory([row])

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    service._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    # Simula que alerta foi enviado ha 2h.
    service.alert_history[
        f"{USER_ID}:{AlertCondition.OFFERS_PENDING_LONG.value}"
    ] = datetime.utcnow() - timedelta(hours=2)

    # Com cooldown_hours=1 (tenant), 2h depois ja pode reenviar.
    can_send = service._can_send_alert(
        AlertCondition.OFFERS_PENDING_LONG,
        USER_ID,
        company_id=COMPANY_ID,
    )
    assert can_send is True, (
        "Alert should be sendable after tenant cooldown_hours=1 expired (2h > 1h)"
    )

    # Sanity: sem override, cooldown default eh 24h, entao 2h NAO seria suficiente.
    service._tenant_overrides_cache = {}
    can_send_default = service._can_send_alert(
        AlertCondition.OFFERS_PENDING_LONG,
        USER_ID,
        company_id=COMPANY_ID,
    )
    assert can_send_default is False, (
        "Sanity: with default cooldown=24h, 2h is not enough"
    )


# ---------------------------------------------------------------------------
# Test 5: tenant channels propagated to _send_alert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alert_uses_tenant_channels_for_dispatch(
    service, fake_db_factory
) -> None:
    """AlertPreference channels -> mapeados pra NotificationChannel no _send_alert."""
    from app.domains.automation.services.proactive_alert_service import (
        AlertCategory,
        AlertCondition,
    )
    from app.services.notification_service import NotificationChannel, NotificationType

    # Tenant configura: bell OFF, email ON, teams ON, whatsapp ON.
    row = _make_preference_row(
        alert_type="ats_sync_failed",
        channel_email=True,
        channel_bell=False,
        channel_teams=True,
        channel_whatsapp=True,
    )
    db = fake_db_factory([row])

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    service._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    alert = {
        "condition": AlertCondition.ATS_SYNC_FAILED,
        "category": AlertCategory.SYSTEM,
        "title": "Test",
        "message": "Test",
        "severity": NotificationType.URGENT,
        "data": {},
        "suggested_action": "x",
        "action_label": "y",
    }

    await service._send_alert(alert, USER_ID, company_id=COMPANY_ID)

    # Inspect call to create_proactive_notification.
    assert service.notification_service.send_multi_channel_notification.called
    call_kwargs = (
        service.notification_service.send_multi_channel_notification.call_args.kwargs
    )
    channels = call_kwargs["channels"]

    # Bell deve estar AUSENTE; Email + Teams + WhatsApp + Chat (sempre) presentes.
    assert NotificationChannel.BELL not in channels, (
        "BELL should NOT be in channels (tenant disabled)"
    )
    assert NotificationChannel.EMAIL in channels, "EMAIL should be in channels"
    assert NotificationChannel.TEAMS in channels, "TEAMS should be in channels"
    assert NotificationChannel.WHATSAPP in channels, "WHATSAPP should be in channels"
    assert NotificationChannel.CHAT in channels, (
        "CHAT should always be included (LIA widget UX baseline)"
    )


# ---------------------------------------------------------------------------
# Test 6: fail-closed when no default and no tenant
# ---------------------------------------------------------------------------


def test_alert_fail_closed_when_no_threshold_anywhere(service) -> None:
    """Fail-closed: alert_type sem default NEM tenant override -> retorna False.

    Verifica gate de seguranca em _can_send_alert: se nem default existe
    (defensive coding), nao envia alerta.
    """
    from enum import StrEnum

    class FakeCondition(StrEnum):
        UNKNOWN = "unknown_condition_x9z"

    service.thresholds = {}  # Wipe all defaults.
    service._tenant_overrides_cache = {}  # No tenant overrides.

    # _can_send_alert deve retornar False (sem default, sem tenant).
    can_send = service._can_send_alert(
        FakeCondition.UNKNOWN,  # type: ignore[arg-type]
        USER_ID,
        company_id=COMPANY_ID,
    )
    assert can_send is False, (
        "Fail-closed: alert without any threshold (default or tenant) must skip"
    )


# ---------------------------------------------------------------------------
# Test 7: load_overrides queries AlertPreference with company_id filter (multi-tenancy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_overrides_filters_by_company_id(service, fake_db_factory) -> None:
    """_load_overrides_for_company DEVE filtrar por company_id (LGPD canonical)."""
    db = fake_db_factory([])

    await service._load_overrides_for_company(COMPANY_ID, db)

    # Verifica que execute foi chamado com select(AlertPreference).where(company_id == ...)
    assert db.execute.called, "_load_overrides_for_company must query DB"
    # Note: we don't introspect the SQL AST here (brittle); the contract test for
    # multi-tenancy filter lives in tests/contract/test_multi_tenant_isolation_contract.py.
    # Here we just confirm DB was queried at all (smoke gate).


# ---------------------------------------------------------------------------
# Test 8: latest-wins when multiple AlertPreference rows for same alert_type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_overrides_picks_latest_per_alert_type(
    service, fake_db_factory
) -> None:
    """Quando ha 2+ AlertPreference rows pro mesmo alert_type, pega a mais recente."""
    older = _make_preference_row(
        alert_type="conversion_rate_low",
        threshold=5,
        updated_at=datetime(2026, 1, 1, 0, 0, 0),
    )
    newer = _make_preference_row(
        alert_type="conversion_rate_low",
        threshold=20,
        updated_at=datetime(2026, 5, 22, 0, 0, 0),
    )
    db = fake_db_factory([older, newer])

    overrides = await service._load_overrides_for_company(COMPANY_ID, db)
    assert "conversion_rate_low" in overrides
    assert overrides["conversion_rate_low"].threshold == 20, (
        "Latest AlertPreference row should win (admin/team config canonical)"
    )
