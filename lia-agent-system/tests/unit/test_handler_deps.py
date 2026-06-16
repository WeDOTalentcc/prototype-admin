"""UC-P1-20: Handler dependency injection — HandlerDeps unit tests."""
import pytest


def test_handler_deps_construction():
    """HandlerDeps can be constructed with identity fields."""
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps

    deps = HandlerDeps(company_id="company-1", user_id="user-1")
    assert deps.company_id == "company-1"
    assert deps.user_id == "user-1"
    assert deps.db is None


def test_handler_deps_defaults():
    """HandlerDeps can be constructed with no arguments (defaults to empty strings)."""
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps

    deps = HandlerDeps()
    assert deps.company_id == ""
    assert deps.user_id == ""
    assert deps.db is None


def test_handler_deps_lazy_loads_services():
    """Private service slots must be None until first access."""
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps

    deps = HandlerDeps(company_id="c1", user_id="u1")
    assert deps._pipeline_service is None, "pipeline_service must be lazy"
    assert deps._fairness_guard is None, "fairness_guard must be lazy"
    assert deps._audit_service is None, "audit_service must be lazy"


def test_handler_deps_with_identity_returns_new_instance():
    """with_identity() returns a new instance, does not mutate the original."""
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps

    original = HandlerDeps(company_id="c1", user_id="u1")
    updated = original.with_identity("c2", "u2")

    assert updated is not original
    assert updated.company_id == "c2"
    assert updated.user_id == "u2"
    # Original unchanged
    assert original.company_id == "c1"
    assert original.user_id == "u1"


def test_handler_deps_with_identity_preserves_db():
    """with_identity() preserves the db reference from the original."""
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps

    class FakeDB:
        pass

    db = FakeDB()
    original = HandlerDeps(db=db, company_id="c1", user_id="u1")
    updated = original.with_identity("c2", "u2")

    assert updated.db is db
