"""
Tests for B3b (2026-06-09): Rail A entity modal entity_ids fix.
_collect_entity_ids_for_modal resolves entity_ids from metadata/context/resolver.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


pytestmark = pytest.mark.asyncio


@pytest.fixture
def _job_reqs():
    """Minimal entity_required for job_id param."""
    req = MagicMock()
    req.type = "job"
    req.param = "job_id"
    return [req]


@pytest.mark.asyncio
async def test_resolves_from_meta_entity_ids(_job_reqs):
    """Highest-priority: FE meta.entity_ids dict injected by entityContextRef."""
    from app.orchestrator.guards.rail_a_capability_check import _collect_entity_ids_for_modal
    meta = {"entity_ids": {"job_id": "job-111", "entity_type": "job"}}
    result = await _collect_entity_ids_for_modal(
        entity_requirements=_job_reqs,
        meta=meta, context={}, message="insights", company_id="co-1", db=None,
    )
    assert result["job_id"] == "job-111"


@pytest.mark.asyncio
async def test_resolves_from_meta_param_direct(_job_reqs):
    """Second priority: individual param key in meta."""
    from app.orchestrator.guards.rail_a_capability_check import _collect_entity_ids_for_modal
    meta = {"job_id": "job-222"}
    result = await _collect_entity_ids_for_modal(
        entity_requirements=_job_reqs,
        meta=meta, context={}, message="insights", company_id="co-1", db=None,
    )
    assert result["job_id"] == "job-222"


@pytest.mark.asyncio
async def test_resolves_from_context_typed(_job_reqs):
    """entity_id+entity_type in context resolves correctly."""
    from app.orchestrator.guards.rail_a_capability_check import _collect_entity_ids_for_modal
    result = await _collect_entity_ids_for_modal(
        entity_requirements=_job_reqs,
        meta={},
        context={"entity_id": "job-333", "entity_type": "job"},
        message="insights",
        company_id="co-1",
        db=None,
    )
    assert result["job_id"] == "job-333"


@pytest.mark.asyncio
async def test_empty_when_nothing_available_no_db(_job_reqs):
    """When no entity data and db=None, returns {} (caller decides fallback)."""
    from app.orchestrator.guards.rail_a_capability_check import _collect_entity_ids_for_modal
    result = await _collect_entity_ids_for_modal(
        entity_requirements=_job_reqs,
        meta={}, context={}, message="sem vaga", company_id="co-1", db=None,
    )
    assert result == {}


@pytest.mark.asyncio
async def test_no_requirements_returns_empty():
    """No entity_required → empty dict immediately."""
    from app.orchestrator.guards.rail_a_capability_check import _collect_entity_ids_for_modal
    result = await _collect_entity_ids_for_modal(
        entity_requirements=[],
        meta={"job_id": "irrelevant"}, context={}, message="msg", company_id="co-1", db=None,
    )
    assert result == {}


@pytest.mark.asyncio
async def test_check_rail_a_returns_modal_with_data(_job_reqs):
    """Full integration: check_rail_a_capability returns open_modal with data.job_id."""
    from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

    # Simulate Rail A context from FE with entityContextRef injected entity_ids
    context = {
        "metadata": {
            "source": "rail_a",
            "intent_hint": "job_insights",
            "entity_ids": {"job_id": "test-job-456", "entity_type": "job"},
        }
    }
    mock_db = MagicMock()
    result = await check_rail_a_capability(
        context=context,
        message="ver insights",
        company_id="co-1",
        db=mock_db,
    )
    assert result is not None
    assert result.get("ui_action") == "open_modal"
    params = result.get("ui_action_params", {})
    assert params.get("modal_id") == "job_insights"
    assert params.get("data", {}).get("job_id") == "test-job-456"


@pytest.mark.asyncio
async def test_check_rail_a_missing_entity_navigates_fallback():
    """When entity_required but no entity data, returns navigate fallback (not empty modal)."""
    from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

    context = {
        "metadata": {
            "source": "rail_a",
            "intent_hint": "job_insights",
            # no entity_ids at all
        }
    }
    mock_db = MagicMock()
    result = await check_rail_a_capability(
        context=context,
        message="ver insights sem dizer qual vaga",
        company_id="co-1",
        db=mock_db,
    )
    assert result is not None
    # Should navigate to fallback, not open modal (can't open modal without entity)
    assert result.get("ui_action") == "navigate_to"
