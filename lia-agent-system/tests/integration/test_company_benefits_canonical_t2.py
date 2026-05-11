"""T2 (#989) regression sentinel — Minha Empresa Benefits consolidation.

Guards against the two bugs catalogued in T1 audit
(`.local/audit/minha-empresa-inventory.md`):

* B6 — duplicated routers `company_benefits.py` (canonical, `CompanyBenefit`
  model) vs `company_benefits_api.py` (legacy, `Benefit` model). Legacy was
  deleted; this test breaks if it comes back or if any route under
  `/api/v1/company/benefits/*` regresses.

* B11 — `useCompanyBenefits` calls `/api/v1/company/benefits/active`. The
  canonical router previously had a `/{benefit_id}` catch-all declared
  before any sibling literal route, so `active` was parsed as a UUID and
  422'd. This sentinel asserts the literal routes (`/active`, `/highlighted`,
  `/summary`) win the FastAPI route resolution before the UUID fallback.
"""
from __future__ import annotations

import importlib

import pytest


def _route_methods(app, path: str) -> set[str]:
    """Return the HTTP methods registered for an exact path."""
    methods: set[str] = set()
    for r in app.routes:
        if getattr(r, "path", None) == path:
            methods |= set(getattr(r, "methods", set()) or set())
    return methods


def test_legacy_company_benefits_api_module_is_gone():
    with pytest.raises(ImportError):
        importlib.import_module("app.api.v1.company_benefits_api")


def test_canonical_company_benefits_routes_registered():
    from app.main import app

    expected_paths = {
        "/api/v1/company/benefits/",
        "/api/v1/company/benefits/active",
        "/api/v1/company/benefits/highlighted",
        "/api/v1/company/benefits/summary",
        "/api/v1/company/benefits/{benefit_id}",
        "/api/v1/company/benefits/seed-defaults",
        "/api/v1/company/benefits/categories/list",
    }
    actual = {getattr(r, "path", None) for r in app.routes}
    missing = expected_paths - actual
    assert not missing, f"Canonical benefits routes missing after T2: {missing}"


def test_active_highlighted_summary_declared_before_uuid_catchall():
    """Route ORDER matters in FastAPI — `/{benefit_id}` would shadow the
    literal sibling routes if it is registered first. Bug B11 reproduction.
    """
    from app.main import app

    seen_literals: set[str] = set()
    for r in app.routes:
        path = getattr(r, "path", None) or ""
        if path in (
            "/api/v1/company/benefits/active",
            "/api/v1/company/benefits/highlighted",
            "/api/v1/company/benefits/summary",
        ):
            seen_literals.add(path)
        if path == "/api/v1/company/benefits/{benefit_id}":
            assert seen_literals == {
                "/api/v1/company/benefits/active",
                "/api/v1/company/benefits/highlighted",
                "/api/v1/company/benefits/summary",
            }, (
                f"Route order regression (B11): /{{benefit_id}} reached before "
                f"literal routes were registered. Seen so far: {seen_literals}"
            )
            return
    pytest.fail("/api/v1/company/benefits/{benefit_id} not registered")


def test_response_model_exposes_fields_used_by_hook():
    """Frontend `useCompanyBenefits` calls `b.seniority_levels.includes(...)`.
    The canonical response MUST expose the field or the hook crashes at runtime
    with `Cannot read properties of undefined`. Architect-flagged gap.
    """
    from app.api.v1.company_benefits import CompanyBenefitResponse

    fields = set(CompanyBenefitResponse.model_fields.keys())
    required_for_hook = {
        "seniority_levels",
        "applicable_to",
        "contract_types",
        "departments",
        "percentage_value",
        "value_details",
    }
    missing = required_for_hook - fields
    assert not missing, (
        f"CompanyBenefitResponse is missing fields used by frontend hooks: {missing}"
    )


def test_active_summary_highlighted_are_GET():
    from app.main import app

    for path in (
        "/api/v1/company/benefits/active",
        "/api/v1/company/benefits/highlighted",
        "/api/v1/company/benefits/summary",
    ):
        assert "GET" in _route_methods(app, path), f"{path} should accept GET"
