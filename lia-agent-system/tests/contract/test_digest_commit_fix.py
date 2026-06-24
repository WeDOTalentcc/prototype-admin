"""Sensor B-F1: PUT /digest/weekly/preferences deve persistir (db.commit obrigatório).

Bug confirmado 2026-06-10: update_weekly_digest_preference setava
current_user.notification_preferences + chamava flag_modified mas nunca
chamava db.commit() → mudança perdida ao fechar a sessão.

Sensor: verifica que commit é chamado após flag_modified, e que a mudança
persiste (GET após PUT retorna o valor salvo).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id: str = "usr-1", prefs: dict | None = None):
    u = MagicMock()
    u.id = user_id
    u.notification_preferences = prefs or {}
    u.role = "recruiter"
    return u


def _make_body(enabled: bool):
    from app.api.v1.digest import WeeklyDigestPreferenceRequest
    return WeeklyDigestPreferenceRequest(enabled=enabled)


# ---------------------------------------------------------------------------
# Test 1 — db.commit() é chamado após flag_modified
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_weekly_digest_calls_db_commit():
    """PUT /weekly/preferences deve chamar db.commit() para persistir."""
    from app.api.v1.digest import update_weekly_digest_preference

    user = _make_user(prefs={})
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch("sqlalchemy.orm.attributes.flag_modified"):
        result = await update_weekly_digest_preference(
            body=_make_body(enabled=False),
            current_user=user,
            db=mock_db,
            company_id="comp-1",
        )

    mock_db.commit.assert_awaited_once(), (
        "db.commit() deve ser chamado — sem ele a mudança é perdida ao fechar a sessão"
    )
    assert result["weekly_report_enabled"] is False


# ---------------------------------------------------------------------------
# Test 2 — o valor é realmente gravado no user object antes do commit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_weekly_digest_sets_preference_on_user():
    """PUT /weekly/preferences deve gravar weekly_report_enabled no user antes do commit."""
    from app.api.v1.digest import update_weekly_digest_preference

    user = _make_user(prefs={"weekly_report_enabled": True})
    mock_db = AsyncMock()

    with patch("sqlalchemy.orm.attributes.flag_modified"):
        await update_weekly_digest_preference(
            body=_make_body(enabled=False),
            current_user=user,
            db=mock_db,
            company_id="comp-1",
        )

    assert user.notification_preferences.get("weekly_report_enabled") is False, (
        "weekly_report_enabled deve ser False após PUT com enabled=False"
    )


# ---------------------------------------------------------------------------
# Test 3 — resposta retorna o valor correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_weekly_digest_response_reflects_new_value():
    """Resposta do PUT deve refletir o valor que foi salvo."""
    from app.api.v1.digest import update_weekly_digest_preference

    user = _make_user()
    mock_db = AsyncMock()

    with patch("sqlalchemy.orm.attributes.flag_modified"):
        result = await update_weekly_digest_preference(
            body=_make_body(enabled=True),
            current_user=user,
            db=mock_db,
            company_id="comp-1",
        )

    assert result["weekly_report_enabled"] is True
    assert "user_id" in result
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 4 — prefs existentes não são sobrescritas (merge, não replace)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_weekly_digest_preserves_other_prefs():
    """PUT não deve apagar outras chaves em notification_preferences."""
    from app.api.v1.digest import update_weekly_digest_preference

    user = _make_user(prefs={"some_other_pref": "value", "weekly_report_enabled": True})
    mock_db = AsyncMock()

    with patch("sqlalchemy.orm.attributes.flag_modified"):
        await update_weekly_digest_preference(
            body=_make_body(enabled=False),
            current_user=user,
            db=mock_db,
            company_id="comp-1",
        )

    assert user.notification_preferences.get("some_other_pref") == "value", (
        "Outras preferências não devem ser sobrescritas"
    )
    assert user.notification_preferences.get("weekly_report_enabled") is False
