"""Fatia 4: bell notifications ao recrutador em candidate_applied e screening_complete.

Sensores que verificam que NotificationService.create_notification é chamado
com channel="bell" e os campos corretos para cada evento.
Fail-soft: erro na bell nao deve abortar o handler (Teams entrega segue normal).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(event_type: str, company_id: str = "comp-123", payload: dict | None = None):
    from app.shared.messaging.platform_events import PlatformEvent
    return PlatformEvent(
        event_type=event_type,
        company_id=company_id,
        source_api="lia-agent-system",
        payload=payload or {},
    )


def _mock_candidate(company_id: str = "comp-123", name: str = "Ana Lima"):
    c = MagicMock()
    c.company_id = company_id
    c.name = name
    return c


def _mock_vacancy(
    company_id: str = "comp-123",
    title: str = "Dev Sênior",
    recruiter_email: str = "rec@example.com",
):
    v = MagicMock()
    v.company_id = company_id
    v.title = title
    v.recruiter_email = recruiter_email
    return v


# ---------------------------------------------------------------------------
# Test 1 — candidate_applied: bell chamado com user_id correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_sends_bell_to_recruiter():
    """handle_candidate_applied_teams envia bell para o recrutador da vaga."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )
    cand = _mock_candidate()
    vac = _mock_vacancy(recruiter_email="rec@wedotalent.cc")

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[cand, vac])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock(return_value=True)

    mock_ns = AsyncMock()
    mock_ns.create_notification = AsyncMock(return_value={"id": "notif-1"})

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
        patch.object(handlers_mod, "_find_recruiter_user_id_by_email",
                     AsyncMock(return_value="user-rec-1")),
        patch("lia_messaging.notification_service.NotificationService",
              return_value=mock_ns),
    ):
        await handlers_mod.handle_candidate_applied_teams(event)

    mock_ns.create_notification.assert_awaited_once()
    call_kwargs = mock_ns.create_notification.call_args.kwargs
    assert call_kwargs["user_id"] == "user-rec-1"
    assert call_kwargs["category"] == "new_application"
    assert "bell" in call_kwargs["channels"]
    assert call_kwargs["related_candidate_id"] == "cand-1"
    assert call_kwargs["related_job_id"] == "vac-1"


# ---------------------------------------------------------------------------
# Test 2 — candidate_applied: sem recrutador → bell NÃO chamado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_no_recruiter_user_no_bell():
    """Se não encontrar user_id do recrutador, bell NÃO é chamado (sem erro)."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )
    cand = _mock_candidate()
    vac = _mock_vacancy(recruiter_email=None)

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[cand, vac])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock(return_value=True)

    mock_ns = AsyncMock()
    mock_ns.create_notification = AsyncMock()

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
        patch.object(handlers_mod, "_find_recruiter_user_id_by_email",
                     AsyncMock(return_value=None)),
        patch("lia_messaging.notification_service.NotificationService",
              return_value=mock_ns),
    ):
        await handlers_mod.handle_candidate_applied_teams(event)

    mock_ns.create_notification.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 3 — candidate_applied: erro na bell não aborta o handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_bell_error_does_not_abort():
    """Erro na bell notification não deve abortar o handler (fail-soft)."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )
    cand = _mock_candidate()
    vac = _mock_vacancy()

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[cand, vac])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock(return_value=True)

    # Simula NotificationService que levanta exceção
    mock_ns = MagicMock()
    mock_ns.create_notification = AsyncMock(side_effect=RuntimeError("Redis down"))

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
        patch.object(handlers_mod, "_find_recruiter_user_id_by_email",
                     AsyncMock(return_value="user-rec-1")),
        patch("lia_messaging.notification_service.NotificationService",
              return_value=mock_ns),
    ):
        # Não deve levantar exceção
        await handlers_mod.handle_candidate_applied_teams(event)

    engine.on_candidate_applied.assert_awaited_once()  # Teams foi chamado normalmente


# ---------------------------------------------------------------------------
# Test 4 — _find_recruiter_user_id_by_email: retorna user_id quando email bate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_recruiter_user_id_by_email_found():
    """_find_recruiter_user_id_by_email retorna str UUID quando encontra user."""
    import app.api.v1.platform_event_handlers as handlers_mod

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value="user-uuid-abc")
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch(
        "app.shared.encryption.encrypted_field_mixin._sha256_hash",
        return_value="deadbeef",
    ):
        result = await handlers_mod._find_recruiter_user_id_by_email(
            mock_db, "rec@example.com", "comp-123"
        )

    assert result == "user-uuid-abc"


# ---------------------------------------------------------------------------
# Test 5 — _find_recruiter_user_id_by_email: None quando email vazio
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_recruiter_user_id_by_email_no_email():
    """_find_recruiter_user_id_by_email retorna None imediatamente para email vazio."""
    import app.api.v1.platform_event_handlers as handlers_mod

    mock_db = AsyncMock()
    result = await handlers_mod._find_recruiter_user_id_by_email(mock_db, None, "comp-123")
    assert result is None
    mock_db.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 6 — _find_recruiter_user_id_by_email: fail-soft em erro DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_recruiter_user_id_by_email_db_error_returns_none():
    """_find_recruiter_user_id_by_email retorna None sem raise em erro de DB."""
    import app.api.v1.platform_event_handlers as handlers_mod

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await handlers_mod._find_recruiter_user_id_by_email(
        mock_db, "rec@example.com", "comp-123"
    )
    assert result is None
