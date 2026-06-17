"""Test: TalentPool list endpoint inclui assignments_count canonical.

Sub-sprint 7B-3a part 1 (2026-05-25). Cobre mudança em
app/api/v1/talent_pools.py:_jsonapi_pool — agora aceita assignments_count
e injeta no resource attributes. Listing endpoint agrega via GROUP BY
em pool_agent_assignments (M2M canonical Sprint 7A).

Esse teste é pure-unit (mocka TalentPool obj) — cobertura do behavior do
helper. Não exercita DB query (já coberta indiretamente por tests Sprint 7A).
"""
from __future__ import annotations

from unittest.mock import MagicMock

from app.api.v1.talent_pools import _jsonapi_pool


def test_jsonapi_pool_inclui_assignments_count():
    """_jsonapi_pool injeta assignments_count nos attributes."""
    pool = MagicMock()
    pool.to_dict.return_value = {
        "id": "pool-uuid-1",
        "company_id": "cid-test",
        "name": "Pool teste",
        "status": "active",
    }
    result = _jsonapi_pool(pool, assignments_count=2)
    assert result["id"] == "pool-uuid-1"
    assert result["type"] == "talent_pool"
    assert result["attributes"]["assignments_count"] == 2
    assert result["attributes"]["name"] == "Pool teste"


def test_jsonapi_pool_default_assignments_count_zero():
    """Default assignments_count=0 quando não passado (back-compat)."""
    pool = MagicMock()
    pool.to_dict.return_value = {
        "id": "pool-uuid-2",
        "company_id": "cid-test",
        "name": "Pool sem agents",
        "status": "active",
    }
    result = _jsonapi_pool(pool)
    assert result["attributes"]["assignments_count"] == 0
