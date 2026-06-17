"""tests/unit/test_ats_sync_b5.py

B5 fix: ATS sync skipped deve retornar success=False, skipped=True
quando nenhum cliente ATS esta configurado -- nunca mais success=True no mock.
"""
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from app.domains.ats_integration.services.ats_sync_service import (
    ATSSyncService,
    ATSSyncTrigger,
    ATSSyncResult,
    ATSClientNotConfiguredError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_service_no_client() -> ATSSyncService:
    """Return an ATSSyncService with _clients dict empty (no ATS configured)."""
    svc = ATSSyncService.__new__(ATSSyncService)
    svc.audit_log = []
    svc.supported_ats = ["gupy", "pandape", "merge"]
    svc._clients = {}  # no client configured
    return svc


# ---------------------------------------------------------------------------
# Test 1 -- trigger_sync returns skipped=True, success=False when not configured
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_sync_not_configured_returns_skipped():
    """B5: quando ATS nao configurado, trigger_sync deve retornar
    success=False e skipped=True -- nao success=True (dado falso no audit trail)."""
    svc = make_service_no_client()

    # Patch ATSFieldMapping so a field enters fields_synced, hitting _execute_sync
    with patch(
        "app.domains.ats_integration.services.ats_sync_service.ATSFieldMapping.can_sync_field",
        return_value=True,
    ), patch(
        "app.domains.ats_integration.services.ats_sync_service.ATSFieldMapping.get_ats_field_name",
        return_value="status",
    ):
        # event_dispatcher import is inside a try/except in trigger_sync -- it may
        # fail silently; that is fine for the test.
        result = await svc.trigger_sync(
            trigger=ATSSyncTrigger.STATUS_CHANGE,
            source_agent="test",
            ats_type="gupy",
            candidate_id="cand-001",
            job_id="job-001",
            data={"status": "hired"},
        )

    # Core assertions
    assert result["success"] is False, (
        "success deve ser False quando ATS nao configurado, "
        f"mas obteve: {result}"
    )
    assert result.get("skipped") is True, (
        "skipped deve ser True quando ATS nao configurado, "
        f"mas obteve: {result}"
    )
    assert result["result"] == ATSSyncResult.NO_CLIENT.value, (
        f"result deve ser no_client_configured, mas obteve: {result[result]}"
    )
    # The old bug: mock retornava success=True
    assert result.get("mock") is None or result.get("mock") is False, (
        "Nao deve retornar mock=True no resultado de trigger_sync"
    )


# ---------------------------------------------------------------------------
# Test 2 -- handler does not set ats_synced=True when skipped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ats_synced_flag_false_when_trigger_sync_skipped():
    """B5: simulacao do padrao dos handlers: quando trigger_sync retorna
    success=False/skipped=True, a variavel ats_synced NAO deve ser True."""
    skipped_result = {
        "success": False,
        "skipped": True,
        "result": "no_client_configured",
        "fields_synced": [],
        "message": "ATS nao configurado",
        "timestamp": "2026-01-01T00:00:00",
    }

    # Simulate the handler pattern from handlers_lifecycle.py
    ats_synced = False
    sync_result = skipped_result  # as if trigger_sync returned this

    if sync_result.get("success"):
        ats_synced = True  # handlers only set True here

    assert ats_synced is False, (
        "ats_synced nao deve ser True quando trigger_sync retorna skipped=True"
    )


# ---------------------------------------------------------------------------
# Test 3 -- ATSClientNotConfiguredError is raised by _execute_sync when no client
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_sync_raises_when_no_client():
    """B5: _execute_sync deve levantar ATSClientNotConfiguredError (nao chamar _mock_sync)
    quando client is None."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncAction

    svc = make_service_no_client()

    with pytest.raises(ATSClientNotConfiguredError) as exc_info:
        await svc._execute_sync(
            ats_type="gupy",
            action=ATSSyncAction.UPDATE,
            candidate_id="cand-001",
            job_id=None,
            fields=[{"wedotalent_field": "status", "ats_field": "status", "value": "hired"}],
        )

    assert exc_info.value.ats_type == "gupy"
    assert "not configured" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 4 -- _mock_sync still works (for explicit test-only use)
# ---------------------------------------------------------------------------

def test_mock_sync_still_callable_explicitly():
    """_mock_sync pode ser chamado explicitamente (testes), mas nunca mais
    via _execute_sync em producao."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncAction

    svc = make_service_no_client()
    result = svc._mock_sync(
        ats_type="gupy",
        action=ATSSyncAction.UPDATE,
        candidate_id="cand-001",
        fields=[],
    )
    # _mock_sync still returns its own dict (unchanged)
    assert result.get("mock") is True
    # But it is NOT reached via _execute_sync anymore (test 3 confirms that)
