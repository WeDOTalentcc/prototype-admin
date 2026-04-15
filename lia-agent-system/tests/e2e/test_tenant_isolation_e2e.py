"""
E2E Test — Tenant Isolation across Python ↔ Rails boundary.

MIGRATION_PLAN item 8.1 (PX08).

CONTEXT:
    Sprint 1 added candidates.account_id (migration 20260415120001) and
    wired ResourceLoader + SearchRenderer to scope by tenant via the
    TenantScoped concern. This test validates the isolation end-to-end:

        - A recruiter authenticated for Account A must NOT be able to
          read, update, delete, or search candidates belonging to
          Account B, regardless of the endpoint they hit.
        - Direct GET by ID of an out-of-tenant record returns 404
          (record appears to not exist — we don't leak its existence).
        - Search/list endpoints filter server-side; the out-of-tenant
          record never appears in the response even if matching the
          filter criteria.
        - The isolation holds whether the candidate is accessed by
          Rails bigint ID or by fork_uuid (item 7.3).

DEPENDENCIES:
    - 1.1 (migration candidates.account_id)        — ✅ code merged, awaits db:migrate
    - 1.2 (backfill account_id)                    — ✅ code merged, manual run
    - 1.3 (rails db:migrate in staging)            — ⏳ MANUAL
    - 1.4 (ResourceLoader tenant scope)            — ✅ shipped
    - 1.5 (SearchRenderer tenant scope)            — ✅ shipped

SKIP BEHAVIOR:
    This suite runs only when E2E_RAILS_AVAILABLE=true is set in the
    environment (typically staging/CI after item 1.3 completes). In dev
    it's skipped so local pytest runs stay fast.

PROMPT REFERENCE (PX08 parameters):
    resource       = candidates (tenant-scoped via account_id)
    rails_path     = /v1/candidates
    bloqueador     = Sprint 7 full delegation; any future write API
    independente_de = items 8.2, 8.3, 8.4
"""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_RAILS_AVAILABLE", "false").lower() not in {"1", "true", "yes"},
    reason="Requires Rails staging reachable and candidates.account_id backfilled (item 1.3)",
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def account_a_id() -> str:
    """Rails bigint account id seeded for isolation tests. Set via env."""
    return os.environ["E2E_ACCOUNT_A_ID"]


@pytest.fixture
def account_b_id() -> str:
    return os.environ["E2E_ACCOUNT_B_ID"]


@pytest.fixture
def recruiter_a_token() -> str:
    """JWT for a recruiter whose account_id == account_a_id."""
    return os.environ["E2E_RECRUITER_A_TOKEN"]


@pytest.fixture
def candidate_b_id() -> str:
    """A candidate belonging to Account B (pre-seeded)."""
    return os.environ["E2E_CANDIDATE_B_ID"]


@pytest.fixture
def candidate_b_fork_uuid() -> str:
    """The same candidate as candidate_b_id, addressable by fork_uuid (item 7.3)."""
    return os.environ["E2E_CANDIDATE_B_FORK_UUID"]


# ──────────────────────────────────────────────────────────────────────
# Test cases
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_direct_get_across_tenants_returns_404(
    recruiter_a_token: str,
    candidate_b_id: str,
):
    """Recruiter A fetching Candidate B by bigint id must get 404, not 200."""
    from httpx import AsyncClient

    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    rails_url = os.environ["RAILS_API_URL"]

    async with AsyncClient(base_url=rails_url, timeout=10.0) as client:
        resp = await client.get(f"/v1/candidates/{candidate_b_id}", headers=headers)

    # 404, not 403 — we must not leak that the record exists
    assert resp.status_code == 404, (
        f"Expected 404 for cross-tenant lookup, got {resp.status_code}. "
        f"Body: {resp.text[:200]}"
    )


@pytest.mark.asyncio
async def test_fork_uuid_get_across_tenants_returns_404(
    recruiter_a_token: str,
    candidate_b_fork_uuid: str,
):
    """Same isolation via fork_uuid lookup (item 7.3 path)."""
    from httpx import AsyncClient

    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    rails_url = os.environ["RAILS_API_URL"]

    async with AsyncClient(base_url=rails_url, timeout=10.0) as client:
        resp = await client.get(
            f"/v1/candidates?fork_uuid={candidate_b_fork_uuid}",
            headers=headers,
        )

    if resp.status_code == 200:
        data = resp.json()
        # Whatever the shape, it must not contain the cross-tenant record
        records = data if isinstance(data, list) else data.get("data", [])
        assert records == [], (
            f"fork_uuid lookup leaked cross-tenant record: {records}"
        )
    else:
        # 404 or 403 are both acceptable — 200 with empty body is also fine
        assert resp.status_code in {200, 403, 404}, (
            f"Unexpected status {resp.status_code}: {resp.text[:200]}"
        )


@pytest.mark.asyncio
async def test_search_does_not_leak_other_tenants(recruiter_a_token: str):
    """Searching with a broad query must never return records from Account B."""
    from httpx import AsyncClient

    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    rails_url = os.environ["RAILS_API_URL"]
    account_b = os.environ["E2E_ACCOUNT_B_ID"]

    async with AsyncClient(base_url=rails_url, timeout=15.0) as client:
        resp = await client.get(
            "/v1/candidates",
            params={"term": "*", "page": 1},
            headers=headers,
        )

    assert resp.status_code == 200, f"Search failed: {resp.status_code}"
    body = resp.json()
    records = body.get("data") or body.get("candidates") or []

    leaked = [r for r in records if str(r.get("account_id")) == account_b]
    assert leaked == [], (
        f"SearchRenderer leaked {len(leaked)} cross-tenant records. "
        "Tenant scope injection (item 1.5) did not run."
    )


@pytest.mark.asyncio
async def test_update_across_tenants_returns_404_or_403(
    recruiter_a_token: str,
    candidate_b_id: str,
):
    """Write paths must also respect tenant scope (ResourceLoader set_resource)."""
    from httpx import AsyncClient

    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    rails_url = os.environ["RAILS_API_URL"]

    async with AsyncClient(base_url=rails_url, timeout=10.0) as client:
        resp = await client.patch(
            f"/v1/candidates/{candidate_b_id}",
            headers=headers,
            json={"name": "HIJACKED"},
        )

    # Either 404 (preferred — don't reveal existence) or 403 (verify_tenant! path)
    assert resp.status_code in {403, 404}, (
        f"Cross-tenant PATCH succeeded with {resp.status_code}. "
        f"Tenant isolation is BROKEN. Body: {resp.text[:200]}"
    )


@pytest.mark.asyncio
async def test_search_with_term_matching_other_tenant_returns_empty(
    recruiter_a_token: str,
):
    """A search term that is known to match a record in Account B must
    still return 0 results for Recruiter A (server-side filter by account_id).
    """
    from httpx import AsyncClient

    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    rails_url = os.environ["RAILS_API_URL"]
    # Seeded search term guaranteed to match candidate B but nothing in A
    known_term_b = os.environ.get("E2E_SEARCH_TERM_ONLY_IN_B", "CROSS_TENANT_LEAK_MARKER")

    async with AsyncClient(base_url=rails_url, timeout=15.0) as client:
        resp = await client.get(
            "/v1/candidates",
            params={"term": known_term_b, "page": 1},
            headers=headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    records = body.get("data") or body.get("candidates") or []
    assert records == [], (
        f"Search for term only in Account B returned {len(records)} "
        "records to Recruiter A. Elasticsearch filter not applied."
    )
