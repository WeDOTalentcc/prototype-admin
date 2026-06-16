"""Sprint E — ats-events foundation — contrato TDD."""
import pytest


# ─── GRUPO 1: libs/events/ package ───────────────────────────────────────────

def test_libs_events_package_importable():
    """libs/events/ deve ser um package Python importável."""
    import importlib
    mod = importlib.import_module("lia_events")
    assert mod is not None


def test_event_schemas_importable_from_libs():
    """Schemas canônicos devem ser importáveis de lia_events."""
    from lia_events.schemas import (
        PlatformEvent,
        JobPublishedEvent,
        CandidateAppliedEvent,
        StageChangedEvent,
        ScreeningCompletedEvent,
        OfferSentEvent,
    )
    assert PlatformEvent is not None
    assert OfferSentEvent is not None  # novo evento


def test_platform_event_has_version_field():
    """PlatformEvent deve ter campo version."""
    from lia_events.schemas import PlatformEvent
    fields = PlatformEvent.model_fields
    assert "version" in fields


def test_event_types_registry_importable():
    """EVENT_TYPES registry deve estar disponível."""
    from lia_events.schemas import EVENT_TYPES, CRITICAL_EVENT_TYPES
    assert isinstance(EVENT_TYPES, dict)
    assert len(EVENT_TYPES) >= 5
    assert isinstance(CRITICAL_EVENT_TYPES, (set, frozenset))
    assert len(CRITICAL_EVENT_TYPES) >= 3


def test_critical_event_types_subset_of_all():
    """CRITICAL_EVENT_TYPES deve ser subconjunto de EVENT_TYPES."""
    from lia_events.schemas import EVENT_TYPES, CRITICAL_EVENT_TYPES
    all_types = set(EVENT_TYPES.keys())
    missing = CRITICAL_EVENT_TYPES - all_types
    assert not missing, f"Critical types não encontrados em EVENT_TYPES: {missing}"


# ─── GRUPO 2: domain_events_outbox table ─────────────────────────────────────

def test_domain_events_outbox_model_importable():
    """DomainEventsOutbox model deve ser importável."""
    from lia_models.domain_events_outbox import DomainEventsOutbox
    assert DomainEventsOutbox.__tablename__ == "domain_events_outbox"


def test_domain_events_outbox_has_required_columns():
    """Tabela deve ter: event_type, event_id, payload, status, correlation_id."""
    from lia_models.domain_events_outbox import DomainEventsOutbox
    cols = {c.key for c in DomainEventsOutbox.__table__.columns}
    required = {"id", "event_type", "event_id", "company_id", "payload",
                "status", "correlation_id", "created_at", "delivered_at",
                "attempts", "last_error"}
    missing = required - cols
    assert not missing, f"Colunas faltando: {missing}"


def test_domain_events_outbox_status_values():
    """Status válidos: pending, delivered, failed, dead_letter."""
    from lia_models.domain_events_outbox import OutboxStatus
    assert hasattr(OutboxStatus, "PENDING")
    assert hasattr(OutboxStatus, "DELIVERED")
    assert hasattr(OutboxStatus, "FAILED")
    assert hasattr(OutboxStatus, "DEAD_LETTER")


# ─── GRUPO 3: EventsOutboxService ────────────────────────────────────────────

def test_outbox_service_importable():
    """EventsOutboxService deve ser importável."""
    from app.shared.messaging.events_outbox_service import EventsOutboxService
    svc = EventsOutboxService()
    assert hasattr(svc, "publish_via_outbox")
    assert hasattr(svc, "drain_to_pubsub")


def test_outbox_service_publish_creates_record():
    """publish_via_outbox() deve criar registro no outbox."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.shared.messaging.events_outbox_service import EventsOutboxService
    from lia_events.schemas import StageChangedEvent

    async def _run():
        svc = EventsOutboxService()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        event = StageChangedEvent(
            company_id="company-123",
            payload={"candidate_id": "c1", "from_stage": "applied", "to_stage": "screening"},
            source_api="lia-agent-system",
        )

        with patch("app.shared.messaging.events_outbox_service.DomainEventsOutbox") as MockOutbox:
            instance = MagicMock()
            MockOutbox.return_value = instance
            await svc.publish_via_outbox(event, db)

        db.add.assert_called_once()
        return True

    result = asyncio.get_event_loop().run_until_complete(_run())
    assert result is True


def test_outbox_service_fail_safe():
    """publish_via_outbox() falha → cai para fire-and-forget, nunca bloqueia."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app.shared.messaging.events_outbox_service import EventsOutboxService
    from lia_events.schemas import StageChangedEvent

    async def _run():
        svc = EventsOutboxService()
        db = AsyncMock()
        db.add.side_effect = Exception("DB error simulated")

        event = StageChangedEvent(
            company_id="company-123",
            payload={"candidate_id": "c1"},
            source_api="lia-agent-system",
        )

        # Must NOT raise — fail-safe
        await svc.publish_via_outbox(event, db)
        return True

    result = asyncio.get_event_loop().run_until_complete(_run())
    assert result is True


# ─── GRUPO 4: Sensor ─────────────────────────────────────────────────────────

def test_critical_events_sensor_exists():
    """Sensor check_critical_events_use_outbox.py deve existir."""
    from pathlib import Path
    sensor = Path("scripts/check_critical_events_use_outbox.py")
    assert sensor.exists(), (
        "scripts/check_critical_events_use_outbox.py deve existir. "
        "Detecta publish_platform_event() para event_types críticos sem outbox."
    )
