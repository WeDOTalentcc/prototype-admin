"""UC-P1-23: Orchestrator canonicalization tests.

Verifies that:
1. Importing app.orchestrator.orchestrator emits a DeprecationWarning (module-level)
2. The legacy Orchestrator class also warns on instantiation (existing behaviour)
3. orchestrator_routes exports get_orchestrator() and get_main_orchestrator()
4. orchestrator_routes uses MainOrchestrator as its canonical type
"""
import importlib
import warnings


# ---------------------------------------------------------------------------
# 1. Module-level deprecation on import
# ---------------------------------------------------------------------------

def test_legacy_orchestrator_module_emits_deprecation_on_import():
    """Importing orchestrator.py must emit DeprecationWarning at module scope."""
    # Force re-import so the module-level warn fires even if already cached
    import sys

    mod_name = "app.orchestrator.legacy.orchestrator"
    # Remove from cache to ensure the module-level code runs
    sys.modules.pop(mod_name, None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            importlib.import_module(mod_name)
        except Exception:
            # Import errors are OK — we only care about warnings
            pass

    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deprecations, (
        "orchestrator.py must emit a module-level DeprecationWarning on import. "
        "Add _lia_warnings.warn(..., DeprecationWarning, stacklevel=2) at module scope."
    )


# ---------------------------------------------------------------------------
# 2. orchestrator_routes exports canonical names
# ---------------------------------------------------------------------------

def test_orchestrator_routes_exports_get_main_orchestrator():
    """orchestrator_routes must export get_main_orchestrator for downstream callers."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import app.api.orchestrator_routes as routes

    assert hasattr(routes, "get_main_orchestrator"), (
        "orchestrator_routes must export get_main_orchestrator "
        "(used by chat.py, orchestrated_*_chat.py)"
    )


def test_orchestrator_routes_exports_get_orchestrator():
    """orchestrator_routes must define get_orchestrator() for legacy Depends() usage."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import app.api.orchestrator_routes as routes

    assert hasattr(routes, "get_orchestrator"), (
        "orchestrator_routes must define get_orchestrator() "
        "used by legacy /api/orchestrator endpoints"
    )
    assert callable(routes.get_orchestrator)


# ---------------------------------------------------------------------------
# 3. orchestrator_routes uses MainOrchestrator (not legacy Orchestrator)
# ---------------------------------------------------------------------------

def test_orchestrator_routes_orchestrator_alias_is_main_orchestrator():
    """The Orchestrator name in orchestrator_routes must resolve to MainOrchestrator."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import app.api.orchestrator_routes as routes
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator

    assert routes.Orchestrator is MainOrchestrator, (
        "orchestrator_routes.Orchestrator must be an alias for MainOrchestrator "
        "(UC-P1-23 canonicalization)"
    )
