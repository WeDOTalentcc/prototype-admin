"""Contract tests: PII/grant fields gate in company_users.update_user.

Task A7-BE — TDD tests:
  - recruiter cannot set pii_field_visibility (403)
  - admin can set pii_field_visibility + can_view_salary (persisted)
  - admin with invalid pii_field_visibility key rejected (422)
"""
import json
import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.auth.models import UserRole
from app.auth.schemas import UserManagementUpdate
from app.api.v1.company_users import update_user


def _target_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="t@x.com",
        permissions=[],
        role=UserRole.recruiter,
    )


def _repo(target):
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=target)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=target)
    return repo


@pytest.mark.asyncio
async def test_recruiter_cannot_set_pii_field_visibility():
    target = _target_user()
    recruiter = SimpleNamespace(id=uuid.uuid4(), role=UserRole.recruiter)
    with pytest.raises(HTTPException) as exc_info:
        await update_user(
            user_id=str(target.id),
            data=UserManagementUpdate(pii_field_visibility={"cpf": False}),
            user_repo=_repo(target),
            current_user=recruiter,
            company_id=str(uuid.uuid4()),
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_set_pii_and_grants_persisted():
    target = _target_user()
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.admin)
    repo = _repo(target)

    with patch("app.api.v1.company_users.AuditService") as mock_audit_cls:
        mock_audit_cls.return_value.log_action = AsyncMock()
        await update_user(
            user_id=str(target.id),
            data=UserManagementUpdate(pii_field_visibility={"cpf": False}, can_view_salary=True),
            user_repo=repo,
            current_user=admin,
            company_id=str(uuid.uuid4()),
        )

    assert repo.update.called, "repo.update should have been called"
    # Extract the payload passed to repo.update (second positional arg)
    call_args = repo.update.call_args
    if call_args.args and len(call_args.args) >= 2:
        called_payload = call_args.args[1]
    else:
        called_payload = call_args.kwargs.get("data", call_args.kwargs.get("update_data", {}))
    assert called_payload.get("pii_field_visibility") == {"cpf": False}
    assert called_payload.get("can_view_salary") is True


@pytest.mark.asyncio
async def test_admin_invalid_pii_field_rejected():
    target = _target_user()
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.admin)
    with pytest.raises(HTTPException) as exc_info:
        await update_user(
            user_id=str(target.id),
            data=UserManagementUpdate(pii_field_visibility={"not_a_field": False}),
            user_repo=_repo(target),
            current_user=admin,
            company_id=str(uuid.uuid4()),
        )
    assert exc_info.value.status_code == 422
