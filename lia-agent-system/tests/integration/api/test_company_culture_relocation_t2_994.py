"""Sentinel test for T2/#994 — culture endpoints relocated from
``app/api/v1/company.py`` to ``app/api/v1/company_culture.py``.

Guarantees:
1. The 4 public paths remain registered on the FastAPI app under the
   exact same URLs (the frontend must not break).
2. The handler functions live in ``company_culture`` (not in
   ``company``), enforcing the module-cohesion invariant going forward.
"""
from __future__ import annotations

import importlib

import pytest


CULTURE_PATHS_AND_METHODS = [
    ("/api/v1/company/enrich", "POST"),
    ("/api/v1/company/auto-enrich/{profile_id}", "POST"),
    ("/api/v1/company/profile/{profile_id}/generate-evp", "POST"),
    ("/api/v1/company/analyze-culture", "POST"),
]


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app  # noqa: WPS433 — lazy import for test

    return fastapi_app


def _route_index(app):
    """Map (path, method) → endpoint module so we can assert location."""
    index: dict[tuple[str, str], str] = {}
    for route in app.routes:
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        methods = getattr(route, "methods", None) or set()
        if not path or endpoint is None:
            continue
        module = getattr(endpoint, "__module__", "")
        for method in methods:
            index[(path, method)] = module
    return index


def test_all_relocated_culture_paths_remain_registered(app):
    """The 4 legacy paths MUST still be served (no frontend breakage)."""
    index = _route_index(app)
    missing = [
        (path, method)
        for path, method in CULTURE_PATHS_AND_METHODS
        if (path, method) not in index
    ]
    assert not missing, f"Relocated culture endpoints missing from app: {missing}"


def test_relocated_culture_handlers_live_in_company_culture_module(app):
    """The handlers must be served from ``company_culture``, not ``company``.

    This is the cohesion guarantee — if someone re-adds these handlers
    to ``app.api.v1.company`` in the future, this test fails loudly.
    """
    index = _route_index(app)
    misplaced: list[tuple[str, str, str]] = []
    for path, method in CULTURE_PATHS_AND_METHODS:
        module = index.get((path, method), "")
        if not module.endswith(".company_culture"):
            misplaced.append((path, method, module))
    assert not misplaced, (
        "Culture handlers must live in app.api.v1.company_culture; found: "
        f"{misplaced}"
    )


def test_legacy_router_exported_from_company_culture():
    """The second router used in ``routes.py`` must exist on the module."""
    mod = importlib.import_module("app.api.v1.company_culture")
    assert hasattr(mod, "legacy_router"), (
        "company_culture.legacy_router missing — routes.py registration "
        "would fail."
    )
    legacy = mod.legacy_router
    # FastAPI APIRouter exposes ``.prefix`` and ``.routes``.
    assert legacy.prefix == "/company"
    legacy_paths = {getattr(r, "path", None) for r in legacy.routes}
    expected = {
        "/company/enrich",
        "/company/auto-enrich/{profile_id}",
        "/company/profile/{profile_id}/generate-evp",
        "/company/analyze-culture",
    }
    assert expected.issubset(legacy_paths), (
        f"legacy_router missing expected paths: {expected - legacy_paths}"
    )
