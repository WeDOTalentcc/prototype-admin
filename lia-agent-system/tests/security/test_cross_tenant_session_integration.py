"""Integration sentinel — proves that ``admin_token_budget`` enforces
``require_superadmin`` and opens an audited ``cross_tenant_session`` when a
superadmin queries a foreign tenant (Task #1148).

This test pins the production wiring at the handler level (skipping the
global auth middleware): a non-superadmin admin gets HTTP 403 on the
migrated endpoint, and a superadmin lookup of a foreign company id
produces start+end audit rows from ``cross_tenant_session``.

Runs offline — patches ``get_budget_status`` + ``AsyncSessionLocal`` so we
do not touch real Postgres / Redis.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api.v1 import admin_token_budget as endpoint_mod
from app.shared.admin import cross_tenant_session as ctm


class _Recorder:
    """Captures SQL emitted by the cross_tenant_session helper."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, dict | None]] = []
        self.committed: int = 0
        self.closed: bool = False

    async def execute(self, stmt: Any, params: dict | None = None) -> Any:
        raw = getattr(stmt, "text", str(stmt))
        self.executed.append((raw, params))
        return SimpleNamespace(scalar=lambda: None)

    async def commit(self) -> None:
        self.committed += 1

    async def close(self) -> None:
        self.closed = True

    @property
    def audit_actions(self) -> list[str]:
        out: list[str] = []
        for sql, params in self.executed:
            if "INSERT INTO audit_logs" in sql and params:
                out.append(str(params.get("action")))
        return out


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    rec = _Recorder()
    import app.core.database as core_db
    monkeypatch.setattr(core_db, "AsyncSessionLocal", lambda: rec, raising=False)

    async def _fake_status(company_id: str, plan_code: str | None = None) -> dict:
        return {
            "company_id": str(company_id),
            "plan_code": plan_code or "starter",
            "daily_limit": 10_000,
            "used_today": 1_234,
            "remaining": 8_766,
            "usage_pct": 12.34,
            "budget_exhausted": False,
            "reset_at": "2026-05-16T00:00:00+00:00",
        }

    monkeypatch.setattr(endpoint_mod, "get_budget_status", _fake_status)
    return rec


@pytest.fixture(autouse=True)
def _reset_marker():
    ctm._clear_superadmin_marker()
    yield
    ctm._clear_superadmin_marker()


# ─────────────────────────────────────────────────────────────────────────────
# 1) Plain tenant-admin (role='admin') is BLOCKED by require_superadmin.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_non_superadmin_admin_is_forbidden_by_require_superadmin(
    recorder: _Recorder,
) -> None:
    plain = SimpleNamespace(
        id="admin-1",
        role="admin",
        is_superadmin=False,
        company_id="00000000-0000-4000-a000-000000000001",
    )
    with pytest.raises(HTTPException) as exc_info:
        await ctm.require_superadmin(current_user=plain)
    assert exc_info.value.status_code == 403
    # Marker MUST NOT be set on failure → any later cross_tenant_session
    # call from a handler body would itself raise PermissionError.
    assert ctm._SUPERADMIN_CTX.get() is None
    # And no SQL was emitted (gate refused before any DB work).
    assert recorder.executed == []


# ─────────────────────────────────────────────────────────────────────────────
# 2) Superadmin querying a FOREIGN tenant opens cross_tenant_session and
#    emits start+end audit rows from inside the migrated endpoint body.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_superadmin_cross_tenant_lookup_audits_and_succeeds(
    recorder: _Recorder,
) -> None:
    own = "00000000-0000-4000-a000-000000000001"
    foreign = "11111111-1111-4111-a111-111111111111"
    boss = SimpleNamespace(
        id="boss-1",
        role="platform_admin",
        is_superadmin=True,
        company_id=own,
    )

    # Run the actual require_superadmin dep (this sets the ContextVar marker
    # the way the prod request handler would).
    await ctm.require_superadmin(current_user=boss)
    assert ctm._SUPERADMIN_CTX.get() == {"user_id": "boss-1", "company_id": own}

    # Invoke the migrated endpoint body directly. ``current_user`` test-only
    # alias bypasses the FastAPI-injected production deps.
    resp = await endpoint_mod.get_company_token_budget(
        company_id=foreign,
        plan_code=None,
        admin=None,
        current_user=boss,
    )

    assert resp.company_id == foreign
    assert resp.daily_limit == 10_000

    actions = recorder.audit_actions
    assert "start" in actions and "end" in actions, (
        f"expected start+end audit rows from cross_tenant_session, got {actions}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3) Same-tenant lookup must NOT open cross_tenant_session.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_superadmin_same_tenant_lookup_does_not_open_bypass(
    recorder: _Recorder,
) -> None:
    own = "00000000-0000-4000-a000-000000000001"
    boss = SimpleNamespace(
        id="boss-1",
        role="platform_admin",
        is_superadmin=True,
        company_id=own,
    )
    await ctm.require_superadmin(current_user=boss)

    resp = await endpoint_mod.get_company_token_budget(
        company_id=own,
        plan_code=None,
        admin=None,
        current_user=boss,
    )

    assert resp.company_id == own
    assert recorder.audit_actions == [], (
        "same-tenant lookup must NOT emit cross_tenant_session audit rows; "
        f"got {recorder.audit_actions}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4) Anti-spoofing E2E: even if a malicious handler tries to forge an
#    audit_user_id different from the marker's, cross_tenant_session refuses.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cross_tenant_session_in_endpoint_refuses_spoofed_actor(
    recorder: _Recorder,
) -> None:
    boss = SimpleNamespace(
        id="boss-1",
        role="platform_admin",
        is_superadmin=True,
        company_id="00000000-0000-4000-a000-000000000001",
    )
    await ctm.require_superadmin(current_user=boss)

    with pytest.raises(PermissionError, match="anti-spoofing"):
        async with ctm.cross_tenant_session(
            reason="forged_export",
            audit_user_id="someone-else",
        ):
            pytest.fail("body must not execute")

    assert recorder.executed == []


# ─────────────────────────────────────────────────────────────────────────────
# 5) API-LEVEL test (real FastAPI dependency chain, TestClient/ASGI).
#    Confirms the production path is reachable — the strict-match dependency
#    that previously made cross-tenant requests 403 before reaching the
#    handler is no longer in the way (Task #1148 round-N fix).
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_api_superadmin_cross_tenant_path_is_reachable_and_audited(
    recorder: _Recorder,
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.auth.dependencies import require_admin

    own = "00000000-0000-4000-a000-000000000001"
    foreign = "22222222-2222-4222-a222-222222222222"
    boss = SimpleNamespace(
        id="boss-api-1",
        role="platform_admin",
        is_superadmin=True,
        company_id=own,
    )
    plain = SimpleNamespace(
        id="admin-api-1",
        role="admin",
        is_superadmin=False,
        company_id=own,
    )

    app = FastAPI()
    app.include_router(endpoint_mod.router)

    # 5a) plain admin cross-tenant → 403 from require_superadmin (inside handler).
    app.dependency_overrides[require_admin] = lambda: plain
    client = TestClient(app, raise_server_exceptions=False)
    r1 = client.get(f"/admin/token-budget/{foreign}")
    assert r1.status_code == 403, (
        f"non-superadmin cross-tenant must be forbidden, got {r1.status_code} "
        f"body={r1.text}"
    )
    assert recorder.audit_actions == [], (
        "non-superadmin must NOT trigger cross_tenant_session audit rows"
    )

    # 5b) superadmin cross-tenant → 200 + start/end audit rows.
    app.dependency_overrides[require_admin] = lambda: boss
    r2 = client.get(f"/admin/token-budget/{foreign}")
    assert r2.status_code == 200, (
        f"superadmin cross-tenant must succeed, got {r2.status_code} "
        f"body={r2.text}"
    )
    body = r2.json()
    assert body["company_id"] == foreign
    actions = recorder.audit_actions
    assert "start" in actions and "end" in actions, (
        f"superadmin cross-tenant must emit start+end audit rows, got {actions}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6) FAIL-CLOSED: admin with empty/None company_id (missing tenant context in
#    JWT) is treated as cross-tenant. Non-superadmin → 403; superadmin gets
#    audited bypass. Prevents the bug where a stripped JWT could read any
#    company without going through require_superadmin + cross_tenant_session.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_actor_company_id_is_treated_as_cross_tenant(
    recorder: _Recorder,
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.auth.dependencies import require_admin

    target = "33333333-3333-4333-a333-333333333333"
    no_tenant_admin = SimpleNamespace(
        id="admin-no-tenant", role="admin", is_superadmin=False, company_id=None,
    )
    no_tenant_boss = SimpleNamespace(
        id="boss-no-tenant", role="platform_admin", is_superadmin=True, company_id="",
    )

    app = FastAPI()
    app.include_router(endpoint_mod.router)

    # 6a) non-superadmin without tenant context → 403 (NOT silently served).
    app.dependency_overrides[require_admin] = lambda: no_tenant_admin
    client = TestClient(app, raise_server_exceptions=False)
    r1 = client.get(f"/admin/token-budget/{target}")
    assert r1.status_code == 403, (
        f"empty-actor-company admin must be forbidden, got {r1.status_code}"
    )
    assert recorder.audit_actions == []

    # 6b) superadmin without tenant context → 200 + audited bypass.
    app.dependency_overrides[require_admin] = lambda: no_tenant_boss
    r2 = client.get(f"/admin/token-budget/{target}")
    assert r2.status_code == 200, (
        f"superadmin without tenant context must succeed, got {r2.status_code}"
    )
    actions = recorder.audit_actions
    assert "start" in actions and "end" in actions, (
        f"empty-actor superadmin must still emit audit rows, got {actions}"
    )
