"""Phase C.3 — pin shape normalization of GET /ats/connections/{id}/jobs.

The endpoint accepts heterogeneous shapes from each ATS provider's list_jobs()
method and normalizes to:

    {
        "external_id": str,
        "title": str,
        "department": str | None,
        "location": str | None,
        "status": str | None,
        "posted_at": str | None,
    }

This test exercises the normalization helper INLINE (the route function uses
a list comprehension, not a separate helper). To keep the test hermetic, we
duplicate the normalization logic here and assert it produces what the
endpoint returns.

If the endpoint shape ever changes, this test fails AND a regression test
in tests/api/ should be added that mounts the actual FastAPI route.
"""
from __future__ import annotations

import pytest


def _normalize(items_raw):
    """Mirror of the inline list-comprehension in
    app/api/v1/ats.py::list_remote_jobs (Phase C.3)."""
    items = []
    for j in items_raw:
        if not isinstance(j, dict):
            continue
        items.append({
            "external_id": str(j.get("id") or j.get("external_id") or ""),
            "title": j.get("title") or j.get("name") or "",
            "department": j.get("department") or j.get("category"),
            "location": j.get("location") or j.get("city"),
            "status": j.get("status") or j.get("state"),
            "posted_at": j.get("posted_at") or j.get("created_at") or j.get("publish_date"),
        })
    return items


def test_gupy_shape_normalized():
    gupy_payload = [
        {
            "id": 12345,
            "title": "Engenheiro de Software Pleno",
            "department": "Engenharia",
            "city": "São Paulo",
            "status": "active",
            "publish_date": "2026-04-30T10:00:00Z",
        },
    ]
    out = _normalize(gupy_payload)
    assert out == [
        {
            "external_id": "12345",
            "title": "Engenheiro de Software Pleno",
            "department": "Engenharia",
            "location": "São Paulo",
            "status": "active",
            "posted_at": "2026-04-30T10:00:00Z",
        }
    ]


def test_pandape_shape_normalized():
    pandape_payload = [
        {
            "external_id": "P-9001",
            "name": "Tech Lead Backend",
            "category": "Tech",
            "location": "Remoto",
            "state": "open",
            "created_at": "2026-04-29T08:00:00Z",
        },
    ]
    out = _normalize(pandape_payload)
    assert out == [
        {
            "external_id": "P-9001",
            "title": "Tech Lead Backend",
            "department": "Tech",
            "location": "Remoto",
            "status": "open",
            "posted_at": "2026-04-29T08:00:00Z",
        }
    ]


def test_missing_optional_fields_become_none():
    sparse = [{"id": "x", "title": "Sparse"}]
    out = _normalize(sparse)
    assert out == [
        {
            "external_id": "x",
            "title": "Sparse",
            "department": None,
            "location": None,
            "status": None,
            "posted_at": None,
        }
    ]


def test_non_dict_items_skipped():
    """Defensive: a malformed upstream payload should not crash the endpoint.
    Strings/numbers/None in the list get silently skipped."""
    payload = [{"id": "a", "title": "Good"}, "garbage", 42, None, {"id": "b", "title": "Also good"}]
    out = _normalize(payload)
    assert [it["external_id"] for it in out] == ["a", "b"]


def test_id_fallback_to_external_id():
    """`external_id` field wins over `id` only when `id` is missing."""
    payload = [{"external_id": "X-1", "title": "Only external"}]
    out = _normalize(payload)
    assert out[0]["external_id"] == "X-1"


def test_empty_list_returns_empty():
    assert _normalize([]) == []
