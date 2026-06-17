"""Endpoint tests for /admin/audit-decisions/by-user (Task #366).

Verifies that:
- The route is registered on the app.
- A request with ``actor_user_id`` in the URL ends up calling
  ``audit_service.get_decisions_by_user`` with that exact id and the
  verified company_id from the tenant guard.
- The endpoint returns the audit_logs payload from the service.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch


def _call_endpoint(actor_user_id: str, company_id: str = "co-1") -> dict:
    from app.api.v1.admin_audit_decisions import list_decisions_by_user

    return asyncio.run(list_decisions_by_user(
        actor_user_id=actor_user_id,
        limit=50,
        offset=0,
        date_from=None,
        date_to=None,
        company_id=company_id,
        _user=object(),  # require_admin already enforced by FastAPI
    ))


class TestAdminAuditDecisionsByUser:
    def test_route_is_registered(self):
        from app.api.v1.admin_audit_decisions import router
        paths = {r.path for r in router.routes}
        assert any("/admin/audit-decisions/by-user/" in p for p in paths)

    def test_endpoint_filters_by_actor_user_id(self):
        expected = {
            "audit_logs": [
                {"id": "row-1", "actor_user_id": "user-42",
                 "agent_name": "policy_setup_agent"},
            ],
            "total": 1,
            "limit": 50,
            "offset": 0,
        }
        with patch(
            "app.api.v1.admin_audit_decisions.audit_service.get_decisions_by_user",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = expected
            result = _call_endpoint(actor_user_id="user-42", company_id="co-1")

        assert result == expected
        mock_get.assert_awaited_once()
        kwargs = mock_get.await_args.kwargs
        assert kwargs["company_id"] == "co-1"
        assert kwargs["actor_user_id"] == "user-42"
        assert kwargs["limit"] == 50
        assert kwargs["offset"] == 0

    def test_endpoint_rejects_blank_actor_user_id(self):
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc:
            _call_endpoint(actor_user_id="   ")
        assert exc.value.status_code == 400

    def test_endpoint_requires_admin_role(self):
        """Non-admin users must be rejected with 403 by ``require_admin``.

        The endpoint declares ``Depends(require_admin)``; here we exercise
        that dependency directly with a non-admin user to prove the guard
        rejects them before the audit query runs.
        """
        from fastapi import HTTPException
        from types import SimpleNamespace
        import pytest

        from app.auth.dependencies import require_admin

        non_admin = SimpleNamespace(
            id="user-1",
            is_active=True,
            role="recruiter",  # anything other than admin
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(require_admin(current_user=non_admin))
        assert exc.value.status_code == 403
