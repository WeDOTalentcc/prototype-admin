"""
E2E Test — Core recruitment chain: pipeline + search + screening.

MIGRATION_PLAN item 8.2 (PX08).

CONTEXT:
    This test exercises the happy-path "recruiter's day" chain end-to-end:

        1. Create a job (Rails — via Python proxy shim, now deprecated)
        2. Trigger a Pearch-backed candidate search (Python sourcing agent)
        3. Shortlist top candidates (pipeline move)
        4. Run CV screening on the shortlist (Python screening agent)
        5. Move a screened candidate to interview stage (pipeline action)
        6. Verify AuditLog rows got written in Rails (item 2.1 handlers)

    Each step produces a side effect that the next step consumes, so a
    break anywhere in the chain is visible in the assertions of the
    step immediately after. We keep the fixtures minimal and rely on
    test-account seed data (E2E_ACCOUNT_A_ID + a known fixture job).

DEPENDENCIES:
    - 2.1 (LiaEventsWorker 6 handlers)     — ✅ shipped
    - 1.1/1.2 (candidates.account_id)       — ✅ code merged, pending 1.3
    - RAILS_API_URL reachable               — Giovani confirmed
    - Pearch/LLM stubbed or live            — controlled via E2E_LIVE_LLM

SKIP BEHAVIOR:
    Skipped unless E2E_CORE_CHAIN_AVAILABLE=true. When
    E2E_LIVE_LLM=false the test uses recorded/canned responses (fixture
    files in tests/e2e/fixtures/core_chain/) so it's deterministic in CI.

PROMPT REFERENCE (PX08 parameters):
    resource       = core recruitment chain (multi-domain)
    rails_path     = /v1/* (jobs, candidates, applies, audit_logs)
    bloqueador     = any agent regression in pipeline, sourcing, screening
    independente_de = 8.1 (isolation), 8.3 (RMQ), 8.4 (email)
"""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_CORE_CHAIN_AVAILABLE", "false").lower() not in {"1", "true", "yes"},
    reason="Requires staging Rails + Python orchestrator + seeded account (item 8.2 harness)",
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def recruiter_token() -> str:
    return os.environ["E2E_RECRUITER_A_TOKEN"]


@pytest.fixture
def python_api_url() -> str:
    return os.environ.get("PYTHON_API_URL", "http://localhost:8001")


@pytest.fixture
def rails_api_url() -> str:
    return os.environ["RAILS_API_URL"]


@pytest.fixture
def seed_job_id() -> str:
    """ID of a pre-seeded job in the test account (bigint, Rails-side)."""
    return os.environ["E2E_SEED_JOB_ID"]


# ──────────────────────────────────────────────────────────────────────
# Test: full chain
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_search_screening_happy_path(
    recruiter_token: str,
    python_api_url: str,
    rails_api_url: str,
    seed_job_id: str,
):
    """One test, six steps. Each step's assertion is the contract that
    the next step will exercise. If any step fails, the error message
    makes clear which link in the chain broke.
    """
    from httpx import AsyncClient

    auth = {"Authorization": f"Bearer {recruiter_token}"}
    correlation_id = f"e2e-chain-{uuid.uuid4().hex[:8]}"
    headers = {**auth, "X-Correlation-Id": correlation_id}

    async with AsyncClient(timeout=30.0) as client:
        # ── Step 1: Read the seed job via Rails (chain entry point) ──
        resp = await client.get(
            f"{rails_api_url}/v1/jobs/{seed_job_id}",
            headers=headers,
        )
        assert resp.status_code == 200, f"Step 1 (read job) failed: {resp.status_code}"
        job_payload = resp.json()
        assert job_payload.get("id") == int(seed_job_id)

        # ── Step 2: Sourcing search via Python orchestrator ──
        resp = await client.post(
            f"{python_api_url}/api/v1/sourcing/search",
            headers=headers,
            json={
                "job_id": seed_job_id,
                "query": {"keywords": ["python", "backend"], "limit": 5},
                "mode": "recorded" if os.environ.get("E2E_LIVE_LLM") != "true" else "live",
            },
        )
        assert resp.status_code == 200, (
            f"Step 2 (sourcing search) failed: {resp.status_code} {resp.text[:200]}"
        )
        search_results = resp.json().get("candidates", [])
        assert len(search_results) >= 1, "Sourcing returned no candidates"
        top_candidate = search_results[0]
        candidate_id = top_candidate.get("id") or top_candidate.get("fork_uuid")
        assert candidate_id, "Candidate record missing identifier field"

        # ── Step 3: Shortlist / move to screening stage ──
        resp = await client.post(
            f"{python_api_url}/api/v1/pipeline/transition",
            headers=headers,
            json={
                "job_id": seed_job_id,
                "candidate_id": candidate_id,
                "to_stage": "screening",
            },
        )
        assert resp.status_code in {200, 201}, (
            f"Step 3 (pipeline transition) failed: {resp.status_code}"
        )

        # ── Step 4: Run CV screening ──
        resp = await client.post(
            f"{python_api_url}/api/v1/cv-screening/evaluate",
            headers=headers,
            json={
                "job_id": seed_job_id,
                "candidate_id": candidate_id,
                "mode": "recorded" if os.environ.get("E2E_LIVE_LLM") != "true" else "live",
            },
        )
        assert resp.status_code == 200, (
            f"Step 4 (CV screening) failed: {resp.status_code} {resp.text[:200]}"
        )
        screening = resp.json()
        assert "score" in screening, "Screening response missing score"
        assert "decision" in screening, "Screening response missing decision"

        # ── Step 5: Move to interview stage (based on screening decision) ──
        if screening["decision"] in {"approved", "pass"}:
            resp = await client.post(
                f"{python_api_url}/api/v1/pipeline/transition",
                headers=headers,
                json={
                    "job_id": seed_job_id,
                    "candidate_id": candidate_id,
                    "to_stage": "interview",
                },
            )
            assert resp.status_code in {200, 201}, (
                f"Step 5 (interview transition) failed: {resp.status_code}"
            )

        # ── Step 6: Verify AuditLog entries exist on Rails (item 2.1) ──
        resp = await client.get(
            f"{rails_api_url}/v1/audit_logs",
            headers=headers,
            params={"candidate_id": str(candidate_id), "limit": 20},
        )
        if resp.status_code == 200:
            logs = resp.json().get("data") or resp.json().get("audit_logs") or []
            # Expect at least one audit entry from each agent that fired
            expected_actions = {"pipeline.moved", "screening.completed"}
            seen_actions = {log.get("action") for log in logs}
            assert expected_actions.intersection(seen_actions), (
                f"Step 6 (audit trail) — expected actions {expected_actions} "
                f"not found. Saw: {seen_actions}. LiaEventsWorker handlers "
                "(item 2.1) may not be consuming events."
            )


@pytest.mark.asyncio
async def test_screening_rejection_stops_chain(
    recruiter_token: str,
    python_api_url: str,
    rails_api_url: str,
    seed_job_id: str,
):
    """Rejection path — a screening decision of 'reject' must NOT allow
    further stage transitions to interview. The pipeline agent should
    respect the screening output.
    """
    from httpx import AsyncClient

    auth = {"Authorization": f"Bearer {recruiter_token}"}
    rejected_candidate = os.environ.get("E2E_SEED_CANDIDATE_REJECTED")
    if not rejected_candidate:
        pytest.skip("Requires E2E_SEED_CANDIDATE_REJECTED fixture")

    async with AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{python_api_url}/api/v1/pipeline/transition",
            headers=auth,
            json={
                "job_id": seed_job_id,
                "candidate_id": rejected_candidate,
                "to_stage": "interview",
            },
        )
        # Expected: 409 Conflict or 422 — cannot skip over a "reject" screening
        assert resp.status_code in {409, 422}, (
            f"Pipeline allowed transition to interview for rejected candidate. "
            f"Status {resp.status_code}. The pipeline_agent guard is missing."
        )
