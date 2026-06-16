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
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


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


# ---------------------------------------------------------------------------
# Real HTTP coverage (T11 / task #995) — anti-regression for B11.
#
# The route-order sentinel above proves /active/highlighted/summary are
# REGISTERED before /{benefit_id}, but does not prove the FastAPI matcher
# actually resolves them to the right handler at request time. These tests
# fire real requests through `TestClient` to make sure each canonical path
# returns 200 (not 422 from being parsed as a UUID), filters server-side,
# and yields the legacy `BenefitsSummaryResponse` shape used by the frontend
# hook `useCompanyBenefits`.
# ---------------------------------------------------------------------------

DEMO_COMPANY_ID = "00000000-0000-4000-a000-000000000001"


def _make_benefit(
    *,
    benefit_id: str,
    name: str,
    category: str = "health",
    is_highlighted: bool = False,
    is_active: bool = True,
    seniority_levels: str | None = None,
    value: float | None = None,
    percentage_value: float | None = None,
    value_type: str | None = "informative",
    description: str | None = "desc",
):
    """Lightweight stand-in for `CompanyBenefit` ORM rows."""
    b = MagicMock()
    b.id = benefit_id
    b.company_id = DEMO_COMPANY_ID
    b.name = name
    b.category = category
    b.description = description
    b.icon = None
    b.value = value
    b.percentage_value = percentage_value
    b.value_type = value_type
    b.value_details = None
    b.applicable_to = None
    b.seniority_levels = seniority_levels
    b.contract_types = None
    b.departments = None
    b.is_active = is_active
    b.is_highlighted = is_highlighted
    b.order = 0
    b.created_at = None
    b.updated_at = None
    return b


@pytest.fixture
def benefits_client():
    """TestClient with auth + DB deps overridden and the repository mocked.

    The `CompanyBenefitRepository.list_for_company` mock is exposed on the
    client as `client.list_mock` so individual tests can configure return
    values per scenario.
    """
    from app.main import app
    from app.core.database import get_db
    from app.auth.dependencies import (
        get_current_user_or_demo,
        get_current_user_strict,
        get_current_user,
        get_current_active_user,
    )

    def _mock_db():
        session = AsyncMock()
        session.rollback = AsyncMock()
        yield session

    def _mock_user():
        u = MagicMock()
        u.id = "user-1"
        u.company_id = DEMO_COMPANY_ID
        u.role = "recruiter"
        u.is_active = True
        u.email = "demo@wedotalent.com"
        return u

    list_mock = AsyncMock(return_value=[])

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides[get_current_user_or_demo] = _mock_user
    app.dependency_overrides[get_current_user_strict] = _mock_user
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_current_active_user] = _mock_user

    # Bypass `AuthEnforcementMiddleware` for this test — we want to exercise
    # the FastAPI matcher and the route handler, not the global auth gate
    # (which is covered by its own dedicated tests). With the middleware
    # active, requests get a 401 before dependency_overrides ever run.
    async def _passthrough_dispatch(self, request, call_next):
        return await call_next(request)

    with patch(
        "app.middleware.auth_enforcement.AuthEnforcementMiddleware.dispatch",
        _passthrough_dispatch,
    ), patch(
        "app.api.v1.company_benefits.CompanyBenefitRepository"
    ) as RepoCls, patch("app.main.init_db", AsyncMock()):
        RepoCls.return_value.list_for_company = list_mock
        with TestClient(app, raise_server_exceptions=False) as c:
            c.list_mock = list_mock
            yield c

    app.dependency_overrides.clear()


def test_get_active_returns_200_not_422_for_literal_path(benefits_client):
    """B11 reproduction: `/active` must NOT be parsed as a UUID benefit_id."""
    benefits_client.list_mock.return_value = [
        _make_benefit(benefit_id="b1", name="Vale Refeição"),
    ]
    resp = benefits_client.get(
        f"/api/v1/company/benefits/active?company_id={DEMO_COMPANY_ID}"
    )
    assert resp.status_code == 200, (
        f"/active resolved as UUID lookup (B11 regression): {resp.status_code} "
        f"{resp.text}"
    )
    body = resp.json()
    assert isinstance(body, list) and len(body) == 1
    assert body[0]["name"] == "Vale Refeição"


def test_get_active_filters_by_seniority_level(benefits_client):
    """`seniority_level` query param must filter server-side."""
    benefits_client.list_mock.return_value = [
        _make_benefit(benefit_id="b1", name="Plano Sênior", seniority_levels="senior"),
        _make_benefit(benefit_id="b2", name="Plano Junior", seniority_levels="junior"),
        _make_benefit(benefit_id="b3", name="Plano Geral", seniority_levels="all"),
        _make_benefit(benefit_id="b4", name="Plano Sem Filtro", seniority_levels=None),
    ]
    resp = benefits_client.get(
        "/api/v1/company/benefits/active"
        f"?company_id={DEMO_COMPANY_ID}&seniority_level=senior"
    )
    assert resp.status_code == 200, resp.text
    names = {item["name"] for item in resp.json()}
    # `senior` itself + entries with no restriction + the literal "all"
    assert names == {"Plano Sênior", "Plano Geral", "Plano Sem Filtro"}
    assert "Plano Junior" not in names


def test_get_highlighted_returns_only_highlighted(benefits_client):
    benefits_client.list_mock.return_value = [
        _make_benefit(benefit_id="b1", name="Destaque", is_highlighted=True),
        _make_benefit(benefit_id="b2", name="Comum", is_highlighted=False),
    ]
    resp = benefits_client.get(
        f"/api/v1/company/benefits/highlighted?company_id={DEMO_COMPANY_ID}"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [item["name"] for item in body] == ["Destaque"]


def test_get_summary_returns_legacy_shape(benefits_client):
    benefits_client.list_mock.return_value = [
        _make_benefit(
            benefit_id="b1",
            name="Plano de Saúde",
            category="health",
            is_highlighted=True,
            value=500.0,
            value_type="monetary",
        ),
        _make_benefit(
            benefit_id="b2",
            name="Vale Refeição",
            category="food",
            value=800.0,
            value_type="monetary",
        ),
        _make_benefit(
            benefit_id="b3",
            name="Inativo",
            category="other",
            is_active=False,
        ),
    ]
    resp = benefits_client.get(
        f"/api/v1/company/benefits/summary?company_id={DEMO_COMPANY_ID}"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Legacy `BenefitsSummaryResponse` contract consumed by the frontend hook.
    assert set(body.keys()) >= {
        "total_count",
        "active_count",
        "highlighted_count",
        "categories",
        "formatted_text",
        "benefits",
    }
    assert body["total_count"] == 3
    assert body["active_count"] == 2
    assert body["highlighted_count"] == 1
    assert set(body["categories"].keys()) == {"health", "food"}
    assert "Plano de Saúde" in body["formatted_text"]
    assert len(body["benefits"]) == 2  # only active in flat list
