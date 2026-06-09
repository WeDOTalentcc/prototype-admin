"""
Integration Tests — Tenant scope for v1 Tasks API endpoints.

Verifica que /api/v1/tasks/ respeita o caller autenticado:
- 401 quando nao ha auth (com `_is_dev_environment` patched).
- `?user_id=` query parameter is IGNORED for non-admin (service is
  called with caller's own id, not the spoofed one).
- Admin pode passar `?user_id=outro` para monitoramento.
- GET /tasks/{id} retorna 403 quando o task pertence a outro usuario.

NOTA P0 schema gap: o modelo `Task` NAO tem coluna `company_id` —
tenant scope esta sendo aplicado via `assigned_to_user_id` (per-user
ownership) ate a migration ser adicionada. Quando `Task.company_id`
existir, trocar para `validate_company_access(...)`.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(user_id: str, company_id: str = "company-A", role: str = "user") -> MagicMock:
    """Create a User-like mock for dependency injection."""
    u = MagicMock(spec=User)
    u.id = user_id
    u.email = f"{user_id}@{company_id}.test"
    u.company_id = company_id
    u.role = role
    u.is_active = True
    u.can_access_company = lambda cid: cid == company_id
    return u


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def tasks_app():
    """FastAPI app with only the tasks router (and a stub repo)."""
    from app.api.v1.tasks import router
    from app.repositories.dependencies import get_tasks_repo

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Stub repo whose async methods return empty lists / summary.
    repo = MagicMock()
    repo.db = MagicMock()
    repo.get_pending_tasks = AsyncMock(return_value=[])
    repo.get_task_summary = AsyncMock(return_value={
        "pending": 0, "in_progress": 0, "completed": 0,
        "overdue": 0, "critical": 0, "total_active": 0,
    })
    repo.get_tasks_due_today = AsyncMock(return_value=[])
    repo.get_overdue_tasks = AsyncMock(return_value=[])
    repo.get_task = AsyncMock(return_value=None)

    app.dependency_overrides[get_tasks_repo] = lambda: repo
    app.state._stub_repo = repo
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTasksTenantScope:
    """P0 fix: ?user_id= cannot be spoofed by non-admins."""

    def test_no_auth_returns_401(self, tasks_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(tasks_app, raise_server_exceptions=False)
            response = client.get("/api/v1/tasks/")
        assert response.status_code == 401

    def test_user_id_query_ignored_for_non_admin(self, tasks_app):
        """Non-admin passing ?user_id=other → service receives caller's own id."""
        caller = _user("user-self", role="recruiter")
        tasks_app.dependency_overrides[get_current_user_or_demo] = lambda: caller

        client = TestClient(tasks_app, raise_server_exceptions=False)
        response = client.get("/api/v1/tasks/", params={"user_id": "user-other"})
        assert response.status_code == 200

        repo = tasks_app.state._stub_repo
        repo.get_pending_tasks.assert_awaited()
        kwargs = repo.get_pending_tasks.await_args.kwargs
        assert kwargs.get("user_id") == "user-self", (
            f"non-admin spoofed user_id was forwarded to service: {kwargs}"
        )
        tasks_app.dependency_overrides.clear()

    def test_admin_can_query_other_user(self, tasks_app):
        """Admin passing ?user_id=other → service receives that other id."""
        admin = _user("user-admin", role="admin")
        tasks_app.dependency_overrides[get_current_user_or_demo] = lambda: admin

        client = TestClient(tasks_app, raise_server_exceptions=False)
        response = client.get("/api/v1/tasks/", params={"user_id": "user-other"})
        assert response.status_code == 200

        repo = tasks_app.state._stub_repo
        repo.get_pending_tasks.assert_awaited()
        kwargs = repo.get_pending_tasks.await_args.kwargs
        assert kwargs.get("user_id") == "user-other", (
            f"admin override not honored: {kwargs}"
        )
        tasks_app.dependency_overrides.clear()

    def test_cross_tenant_item_returns_403(self, tasks_app):
        """
        GET /tasks/{id} for a task assigned to another user → 403.

        NOTE: Since Task model has no company_id (P0 schema gap),
        we enforce tenant scope via per-user ownership.
        """
        caller = _user("user-self", role="recruiter")
        tasks_app.dependency_overrides[get_current_user_or_demo] = lambda: caller

        # Stub task assigned to a different user — caller should be denied.
        other_task = MagicMock()
        other_task.assigned_to_user_id = "user-other"
        other_task.confirmed_by = None
        other_task.to_dict = lambda: {"id": "task-1", "assigned_to_user_id": "user-other"}

        repo = tasks_app.state._stub_repo
        repo.get_task = AsyncMock(return_value=other_task)

        client = TestClient(tasks_app, raise_server_exceptions=False)
        response = client.get("/api/v1/tasks/11111111-1111-1111-1111-111111111111")
        assert response.status_code == 403
        tasks_app.dependency_overrides.clear()
