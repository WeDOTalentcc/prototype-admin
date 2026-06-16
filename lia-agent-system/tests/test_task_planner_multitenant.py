"""R-019 P0 regression test — company_id must come from JWT, never from request body.

This test suite pins three invariants:

1. Request body Pydantic models must NOT expose a company_id field — the API
   layer must derive it from the JWT/session via get_user_company_id().

2. PlannedTaskRepository._require_company_id() must reject empty/None values
   so that any accidental bypass surfaces loudly at the data-access layer.

3. The get_next_tasks endpoint must include company_id as a Depends parameter
   (derived from User), not as a Query parameter the client can forge.
"""
import pytest


# ---------------------------------------------------------------------------
# Invariant 1: company_id must NOT appear in any request body model
# ---------------------------------------------------------------------------

class TestRequestModelsExcludeCompanyId:
    """Pydantic request body models must not have a company_id field."""

    @staticmethod
    def _fields(model_class):
        if hasattr(model_class, "model_fields"):
            return model_class.model_fields  # Pydantic v2
        return model_class.__fields__       # Pydantic v1

    def test_decompose_task_request_no_company_id(self):
        from app.api.v1.task_planner import DecomposeTaskRequest
        assert "company_id" not in self._fields(DecomposeTaskRequest), (
            "DecomposeTaskRequest must NOT have company_id — "
            "use JWT/Depends(get_current_user_or_demo) instead (R-019 P0)"
        )

    def test_create_planned_task_request_no_company_id(self):
        from app.api.v1.task_planner import CreatePlannedTaskRequest
        assert "company_id" not in self._fields(CreatePlannedTaskRequest), (
            "CreatePlannedTaskRequest must NOT have company_id — "
            "use JWT/Depends(get_current_user_or_demo) instead (R-019 P0)"
        )

    def test_create_execution_plan_request_no_company_id(self):
        from app.api.v1.task_planner import CreateExecutionPlanRequest
        assert "company_id" not in self._fields(CreateExecutionPlanRequest), (
            "CreateExecutionPlanRequest must NOT have company_id — "
            "use JWT/Depends(get_current_user_or_demo) instead (R-019 P0)"
        )


# ---------------------------------------------------------------------------
# Invariant 2: Repository _require_company_id must be fail-closed
# ---------------------------------------------------------------------------

class TestPlannedTaskRepositoryRequiresCompanyId:
    """Repository must reject empty or None company_id at the data layer."""

    def _make_repo(self):
        # Instantiate without a live DB — we only call the static guard
        from app.domains.automation.repositories.planned_task_repository import (
            PlannedTaskRepository,
        )
        return PlannedTaskRepository

    def test_rejects_none(self):
        Repo = self._make_repo()
        with pytest.raises((ValueError, AssertionError)):
            Repo._require_company_id(None)

    def test_rejects_empty_string(self):
        Repo = self._make_repo()
        with pytest.raises((ValueError, AssertionError)):
            Repo._require_company_id("")

    def test_accepts_valid_company_id(self):
        Repo = self._make_repo()
        result = Repo._require_company_id("tenant_abc")
        assert result == "tenant_abc"

    def test_accepts_integer_company_id_coerced_to_str(self):
        """Some Rails tenants use integer IDs — the guard must coerce correctly."""
        Repo = self._make_repo()
        result = Repo._require_company_id(42)
        assert result == "42"


# ---------------------------------------------------------------------------
# Invariant 3: get_next_tasks endpoint does NOT accept company_id as a Query
# ---------------------------------------------------------------------------

class TestGetNextTasksEndpointNoQueryCompanyId:
    """The /next-tasks endpoint must derive company_id from JWT, not Query."""

    def test_no_company_id_query_param(self):
        import inspect
        from app.api.v1.task_planner import get_next_tasks

        sig = inspect.signature(get_next_tasks)
        params = sig.parameters

        # company_id must NOT be a plain Query parameter
        if "company_id" in params:
            # If it exists, it must come from a Depends, not Query
            from fastapi import Query as FastAPIQuery
            param = params["company_id"]
            default = param.default
            # FastAPI Query defaults are Query(...) instances
            assert not isinstance(default, type(FastAPIQuery(None))), (
                "company_id must not be a Query param in get_next_tasks — "
                "inject from JWT via Depends(get_current_user_or_demo) (R-019 P0)"
            )
