"""
V3.2 sensor (2026-06-01): GET /alerts/preferences deve SEMPRE mesclar o catálogo
canônico (DEFAULT_ALERT_PREFERENCES, com name/description) com as preferências
armazenadas (overrides). Antes retornava só as armazenadas — uma empresa com 1
pref órfã (dsr_overdue) via só a CHAVE CRUA, pois AlertPreference não tem
colunas name/description.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.alerts import DEFAULT_ALERT_PREFERENCES, get_alert_preferences


def _stored(alert_type: str, **kw):
    m = MagicMock()
    m.alert_type = alert_type
    m.to_dict.return_value = {
        "id": "stored-id",
        "alert_type": alert_type,
        "is_enabled": kw.get("is_enabled", True),
        "threshold": kw.get("threshold"),
        "channels": kw.get("channels"),
        "cooldown_hours": kw.get("cooldown_hours"),
    }
    return m


def _call(stored):
    repo = MagicMock()
    repo.list_preferences_for_company_user = AsyncMock(return_value=stored)
    return asyncio.run(
        get_alert_preferences(user_id="u1", company_id="c1", repo=repo, _company_gate="c1")
    )["preferences"]


def test_merge_surfaces_full_catalog_with_friendly_names():
    prefs = _call([_stored("dsr_overdue", threshold=99)])
    # Catálogo completo (não só a 1 armazenada)
    assert len(prefs) == len(DEFAULT_ALERT_PREFERENCES)
    # Nenhuma chave crua: toda pref tem name não-vazio
    assert all(p.get("name") for p in prefs), [p["alert_type"] for p in prefs if not p.get("name")]


def test_stored_overrides_catalog_but_keeps_name():
    prefs = _call([_stored("dsr_overdue", threshold=99, is_enabled=False)])
    dsr = next(p for p in prefs if p["alert_type"] == "dsr_overdue")
    assert dsr["name"] == "Solicitacao LGPD Vencendo"   # nome vem do catálogo
    assert dsr["threshold"] == 99                         # override armazenado
    assert dsr["is_enabled"] is False                     # override armazenado


def test_empty_stored_returns_catalog():
    prefs = _call([])
    assert len(prefs) == len(DEFAULT_ALERT_PREFERENCES)
    assert all(p.get("name") for p in prefs)
