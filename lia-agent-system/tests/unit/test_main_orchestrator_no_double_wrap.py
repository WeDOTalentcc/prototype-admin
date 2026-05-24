"""Bug B regression tests — get_main_orchestrator must not double-wrap.

Uses mock legacy Orchestrator (with process_request) registered via the
registry. Confirms the canonical fix (fallback reads registry directly,
not via get_orchestrator which returns MainOrchestrator).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def _register_mock_legacy():
    """Register a mock legacy Orchestrator (with process_request method)
    in the registry, save/restore around the test, reset singleton."""
    import app.orchestrator.execution.main_orchestrator as mo
    from app.orchestrator.execution import registry

    saved_legacy = registry._orchestrator_instance
    saved_main = mo._main_orchestrator_instance

    mock_legacy = MagicMock(name="LegacyOrchestrator")
    mock_legacy.process_request = MagicMock(return_value={"success": True})
    registry._orchestrator_instance = mock_legacy
    mo._main_orchestrator_instance = None

    yield mock_legacy

    registry._orchestrator_instance = saved_legacy
    mo._main_orchestrator_instance = saved_main


def test_get_main_orchestrator_wraps_registered_legacy(_register_mock_legacy):
    """RED if get_main_orchestrator double-wraps. Inner must be the
    registered legacy instance (with process_request), not a MainOrchestrator."""
    import app.orchestrator.execution.main_orchestrator as mo

    instance = mo.get_main_orchestrator()
    inner = instance._orchestrator

    assert not isinstance(inner, type(instance)), (
        f"Double-wrap detected: MainOrchestrator wraps another MainOrchestrator. "
        f"Inner type was {type(inner).__name__}. "
        f"_route_with_tenant_llm:1453 would hit AttributeError 'process_request' "
        f"because MainOrchestrator does not expose that method — only legacy "
        f"Orchestrator does."
    )
    assert inner is _register_mock_legacy, (
        "Inner orchestrator must be the legacy instance registered in the "
        "registry, not a re-fetched one."
    )
    assert hasattr(inner, "process_request"), (
        "Inner orchestrator missing process_request — would trigger the "
        "AttributeError swallowed by main_orchestrator.process catch-all."
    )


def test_get_main_orchestrator_idempotent_singleton(_register_mock_legacy):
    """Calling twice returns the same singleton."""
    import app.orchestrator.execution.main_orchestrator as mo

    a = mo.get_main_orchestrator()
    b = mo.get_main_orchestrator()
    assert a is b, "get_main_orchestrator must return the singleton instance"
    # Confirm not double-wrapped after the second call either.
    assert not isinstance(a._orchestrator, type(a))


def test_get_main_orchestrator_raises_loud_when_legacy_missing():
    """If legacy is not registered, the fallback must raise RuntimeError —
    not silently produce a broken wrapper or recurse infinitely."""
    import app.orchestrator.execution.main_orchestrator as mo
    from app.orchestrator.execution import registry

    saved = registry._orchestrator_instance
    saved_main = mo._main_orchestrator_instance
    registry._orchestrator_instance = None
    mo._main_orchestrator_instance = None

    try:
        with pytest.raises(RuntimeError, match="Legacy Orchestrator not registered"):
            mo.get_main_orchestrator()
    finally:
        registry._orchestrator_instance = saved
        mo._main_orchestrator_instance = saved_main
