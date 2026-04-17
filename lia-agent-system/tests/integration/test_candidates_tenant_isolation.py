"""
Integration tests for task #290 — tenant isolation and sanitized errors on
GET /api/v1/candidates.

What we want to lock in:
  (a) An authenticated request from company A propagates `company_id=A` to the
      repository, so candidates belonging to company B can never appear in the
      response (even if the repository has them in memory).
  (b) When the repository raises an arbitrary internal exception, the endpoint
      returns a sanitized HTTP 500 message (no Python tracebacks, no raw error
      strings) — the real error is logged server-side instead.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

# Make sure rails is OFF so the endpoint exercises the local-DB path.
os.environ.pop("RAILS_API_URL", None)

from app.main import app  # noqa: E402
from app.auth.dependencies import (  # noqa: E402
    get_current_user,
    get_current_active_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
from app.auth.security import create_access_token  # noqa: E402
from app.domains.candidates.dependencies import get_candidate_repo  # noqa: E402

COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"

CAND_A_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CAND_B_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _make_candidate(cand_id: str, company_id: str, name: str):
    """Minimal Candidate-like object the slim serializer can read."""
    c = SimpleNamespace(
        id=cand_id,
        company_id=company_id,
        name=name,
        email=f"{name.lower()}@example.com",
        phone=None,
        mobile_phone=None,
        linkedin_url=None,
        avatar_url=None,
        current_title=None,
        current_company=None,
        seniority_level=None,
        years_of_experience=None,
        headline=None,
        technical_skills=[],
        location_city=None,
        location_state=None,
        location_country=None,
        is_remote=None,
        is_open_to_work=None,
        is_decision_maker=None,
        is_top_universities=None,
        is_hiring=None,
        lia_score=None,
        skills_match_percentage=None,
        source=None,
        status="active",
        is_active=True,
        is_blacklisted=False,
        tags=[],
        created_at=None,
        updated_at=None,
        last_activity_at=None,
    )
    return c


def _user_for_company(company_id: str):
    user = MagicMock()
    user.id = f"user-{company_id}"
    user.company_id = company_id
    user.role = "admin"
    user.is_active = True
    user.email = f"u@{company_id}.com"
    return user


class _TenantAwareRepo:
    """Stand-in for CandidateRepository that records the company_id used and
    only returns rows belonging to that company. Mirrors the real repo's
    contract for the two methods the endpoint calls."""

    def __init__(self, rows):
        self._rows = rows
        self.calls: list[dict] = []

    async def count_candidates(self, **kwargs):
        self.calls.append({"method": "count", **kwargs})
        cid = kwargs.get("company_id")
        return sum(1 for r in self._rows if r.company_id == cid)

    async def list_candidates(self, **kwargs):
        self.calls.append({"method": "list", **kwargs})
        cid = kwargs.get("company_id")
        return [r for r in self._rows if r.company_id == cid]


@pytest.fixture
def rows():
    return [
        _make_candidate(CAND_A_ID, COMPANY_A, "Alice"),
        _make_candidate(CAND_B_ID, COMPANY_B, "Bob"),
    ]


@pytest.fixture
def client_for_company(rows):
    """Yields a (TestClient, repo) factory bound to a given company id."""
    repo_holder: dict[str, _TenantAwareRepo] = {}

    def _factory(company_id: str):
        repo = _TenantAwareRepo(rows)
        repo_holder["repo"] = repo

        def _override_user():
            return _user_for_company(company_id)

        def _override_repo():
            return repo

        app.dependency_overrides[get_current_user] = _override_user
        app.dependency_overrides[get_current_active_user] = _override_user
        app.dependency_overrides[get_current_user_or_demo] = _override_user
        app.dependency_overrides[get_current_user_strict] = _override_user
        app.dependency_overrides[get_candidate_repo] = _override_repo

        # AuthEnforcementMiddleware runs before dependency_overrides take
        # effect, so we still need a real signed JWT in the Authorization
        # header. The middleware only cares that the token decodes; the user
        # behind the request is supplied by the overrides above.
        token = create_access_token(
            subject=f"user-{company_id}",
            role="admin",
            company_id=company_id,
        )

        with patch("app.main.init_db", AsyncMock()):
            tc = TestClient(app, raise_server_exceptions=False)
        tc.headers.update({"Authorization": f"Bearer {token}"})
        return tc, repo

    yield _factory
    app.dependency_overrides.clear()


def test_list_candidates_requires_authentication(client_for_company):
    """Without a Bearer token (and outside DEV_MODE) the endpoint must reject
    the request — this locks in the auth-enforcement guarantee from task #290.
    """
    tc, _ = client_for_company(COMPANY_A)
    # Drop the auth header that the fixture pre-populated. Also drop dev mode
    # so the AuthEnforcementMiddleware does NOT synthesize a demo identity.
    tc.headers.pop("Authorization", None)

    with patch("app.middleware.auth_enforcement._DEV_MODE", False):
        resp = tc.get("/api/v1/candidates")

    assert resp.status_code in (401, 403), (
        f"Unauthenticated request was not rejected (status={resp.status_code}, "
        f"body={resp.text[:200]!r})"
    )


def test_list_candidates_does_not_leak_other_tenants(client_for_company):
    """Recruiter for company A must never see candidates of company B."""
    tc, repo = client_for_company(COMPANY_A)
    resp = tc.get("/api/v1/candidates")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    items = body.get("items", [])
    names = [c["name"] for c in items]

    assert "Alice" in names, "Recruiter A should see their own candidate."
    assert "Bob" not in names, (
        "Cross-tenant leak: Bob (company B) appeared in company A's listing."
    )

    # And the repo must have actually been called with the user's company_id —
    # not None, not company B. This guards against future refactors that drop
    # the filter on the way to the DB.
    used_cids = {call.get("company_id") for call in repo.calls}
    assert used_cids == {COMPANY_A}, (
        f"list_candidates was invoked with unexpected company_id(s): {used_cids}"
    )


def test_list_candidates_internal_error_is_sanitized(client_for_company):
    """A raw DB exception must NOT bleed into the HTTP response body."""
    tc, repo = client_for_company(COMPANY_A)

    secret = "OperationalError: could not connect to db at 10.0.0.99:5432 (password=hunter2)"

    async def _boom(**_kwargs):
        raise RuntimeError(secret)

    repo.count_candidates = _boom  # type: ignore[assignment]
    repo.list_candidates = _boom  # type: ignore[assignment]

    resp = tc.get("/api/v1/candidates")

    assert resp.status_code == 500, resp.text
    body = resp.json()
    # The global StarletteHTTPException handler in app.main rewrites any 5xx
    # `detail` into a sanitized `message`, so we check both keys to be robust
    # to that wrapping.
    safe_text = body.get("message") or body.get("detail") or ""

    assert isinstance(safe_text, str) and safe_text, "Expected a sanitized error string."
    assert secret not in resp.text, (
        f"Internal error string leaked to client: {resp.text!r}"
    )
    assert "Traceback" not in resp.text
    assert "OperationalError" not in resp.text
    assert "hunter2" not in resp.text
