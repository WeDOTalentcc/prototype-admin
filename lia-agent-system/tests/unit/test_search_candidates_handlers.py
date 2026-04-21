"""Handler-level tests for Task #727.

Validates that the canonical service is wired into ALL three call sites
(action handler, talent tool, autonomous tool) and that scope_used /
fellback_to_global metadata propagates through to the consumer payload.

These are not pure unit tests of the canonical service (those live in
test_candidate_search_service.py); instead they exercise the wrapper
layer with the canonical search patched out, to prove the wiring.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


def _full_cand(**overrides):
    base = {
        "id": "c1",
        "name": "Alice",
        "current_title": "Engineer",
        "current_company": "Acme",
        "location_city": "São Paulo",
        "location_state": "SP",
        "seniority_level": "Senior",
        "technical_skills": ["python"],
        "years_of_experience": 5,
        "lia_score": 90.0,
        "skills_match_percentage": 80.0,
        "status": "active",
    }
    base.update(overrides)
    return base


# ─────────────────── action handler (sourcing_actions) ───────────────────


@pytest.mark.asyncio
async def test_sourcing_action_propagates_fallback_in_message():
    from app.orchestrator.action_handlers import sourcing_actions

    canonical_payload = {
        "status": "ok",
        "candidates": [_full_cand()],
        "total": 1,
        "scope_used": "global",
        "fellback_to_global": True,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ):
        result = await sourcing_actions._search_candidates(
            params={"query": "python", "scope": "both", "limit": 5},
            context={"company_id": "co-1"},
        )

    assert result.status == "executed"
    assert result.data["scope_used"] == "global"
    assert result.data["fellback_to_global"] is True
    # Fallback notice surfaces in markdown
    assert "global" in result.message.lower()


@pytest.mark.asyncio
async def test_sourcing_action_handles_invalid_limit_and_scope():
    from app.orchestrator.action_handlers import sourcing_actions

    canonical_payload = {
        "status": "ok", "candidates": [], "total": 0,
        "scope_used": "both", "fellback_to_global": False,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ) as mock_canon:
        result = await sourcing_actions._search_candidates(
            params={"query": "java", "scope": "weird", "limit": "not-a-number"},
            context={"company_id": "co-1"},
        )

    assert result.status == "executed"
    # Defensive parsing fell back to defaults
    call_kwargs = mock_canon.call_args.kwargs
    assert call_kwargs["limit"] == 10
    assert call_kwargs["scope"] == "both"


@pytest.mark.asyncio
async def test_sourcing_action_rejects_empty_query():
    from app.orchestrator.action_handlers import sourcing_actions

    result = await sourcing_actions._search_candidates(
        params={"query": "   "}, context={"company_id": "co-1"},
    )
    assert result.status == "error"


# ─────────────────── autonomous_tool_registry wrapper ───────────────────


@pytest.mark.asyncio
async def test_autonomous_wrapper_uses_canonical_service():
    from app.domains.autonomous.agents import autonomous_tool_registry

    canonical_payload = {
        "status": "ok",
        "candidates": [_full_cand(name="Bob")],
        "total": 1,
        "scope_used": "local",
        "fellback_to_global": False,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ) as mock_canon:
        out = await autonomous_tool_registry._wrap_auto_search_candidates(
            query="python", company_id="co-1", scope="both", limit=7,
        )

    assert out["success"] is True
    assert out["scope_used"] == "local"
    assert out["fellback_to_global"] is False
    assert out["data"]["candidates"][0]["name"] == "Bob"
    mock_canon.assert_awaited_once()
    assert mock_canon.call_args.kwargs["query"] == "python"
    assert mock_canon.call_args.kwargs["company_id"] == "co-1"


@pytest.mark.asyncio
async def test_autonomous_wrapper_rejects_empty_query():
    from app.domains.autonomous.agents import autonomous_tool_registry

    out = await autonomous_tool_registry._wrap_auto_search_candidates(query="")
    assert out["success"] is False
    err_text = (out.get("error") or out.get("message") or "").lower()
    assert "query" in err_text


@pytest.mark.asyncio
async def test_autonomous_wrapper_propagates_canonical_error():
    """Regression: canonical status='error' must NOT be reported as success."""
    from app.domains.autonomous.agents import autonomous_tool_registry

    canonical_payload = {
        "status": "error",
        "error": "DB connection lost",
        "candidates": [],
        "total": 0,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ):
        out = await autonomous_tool_registry._wrap_auto_search_candidates(
            query="python", company_id="co-1", scope="local",
        )
    assert out["success"] is False
    err_text = out.get("error") or out.get("message") or ""
    assert "DB connection lost" in err_text
    assert out["data"]["total"] == 0


@pytest.mark.asyncio
async def test_autonomous_wrapper_normalizes_invalid_scope():
    from app.domains.autonomous.agents import autonomous_tool_registry

    canonical_payload = {
        "status": "ok", "candidates": [], "total": 0,
        "scope_used": "both", "fellback_to_global": False,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ) as mock_canon:
        await autonomous_tool_registry._wrap_auto_search_candidates(
            query="x", company_id="co-1", scope="bogus", limit="abc",
        )
    kwargs = mock_canon.call_args.kwargs
    assert kwargs["scope"] == "both"
    assert kwargs["limit"] == 10


# ─────────────────── talent_tool_registry wrapper ───────────────────


@pytest.mark.asyncio
async def test_talent_wrapper_uses_canonical_service():
    from app.domains.recruiter_assistant.agents import talent_tool_registry

    canonical_payload = {
        "status": "ok",
        "candidates": [_full_cand(name="Carol")],
        "total": 1,
        "scope_used": "global",
        "fellback_to_global": True,
    }
    with patch(
        "app.domains.ai.services.candidate_search_service.search_candidates",
        new=AsyncMock(return_value=canonical_payload),
    ):
        out = await talent_tool_registry._wrap_search_candidates(
            query="react", company_id="co-1", limit=3,
        )

    assert out["success"] is True
    assert out["data"]["scope_used"] == "global"
    assert out["data"]["fellback_to_global"] is True
