"""Contract test — Task E: per-field PII audit on candidate access.

Verifies that _audit_pii_access emits a per-field detail log
(pii_fields_viewed / pii_fields_masked) via AuditService.log_data_access,
in addition to the existing legacy-bucket audit calls.

Note: AuditService is imported locally inside _audit_pii_access, so we patch
at the source module (app.shared.compliance.audit_service.AuditService).
"""
import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def _user(role="manager", can_salary=False, can_sensitive=True, override=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="u@x.com",
        role=role,
        can_view_salary=can_salary,
        can_view_sensitive_pii=can_sensitive,
        pii_field_visibility=override,
    )


_PATCH_TARGET = "app.shared.compliance.audit_service.AuditService"


@pytest.mark.asyncio
async def test_audit_logs_masked_fields():
    """Manager w/ no salary + cpf-hidden role default => cpf + salary-fields masked."""
    captured = {}

    async def _fake_log_data_access(**kwargs):
        d = kwargs.get("details") or {}
        if "pii_fields_masked" in d:
            captured.update(d)

    with patch(_PATCH_TARGET) as MockSvc:
        inst = MockSvc.return_value
        inst.log_data_access = AsyncMock(side_effect=_fake_log_data_access)

        from app.api.v1.candidates.candidates_crud import _audit_pii_access

        await _audit_pii_access(
            _user(role="manager", can_salary=False, can_sensitive=True),
            candidate_id="cand1",
            company_id="co1",
            role_defaults={"manager": {"cpf": False}},
        )

    assert "cpf" in captured.get("pii_fields_masked", []), (
        "cpf should be masked (role_default false)"
    )
    assert "current_salary" in captured.get("pii_fields_masked", []), (
        "current_salary should be masked (legacy bucket can_view_salary=False)"
    )
    assert "date_of_birth" in captured.get("pii_fields_viewed", []), (
        "date_of_birth should be viewed (sensitive bucket True, no override)"
    )


@pytest.mark.asyncio
async def test_audit_per_field_call_uses_correct_kwargs():
    """Verify the per-field call uses canonical AuditService kwargs."""
    calls = []

    async def _capture(**kwargs):
        calls.append(dict(kwargs))

    with patch(_PATCH_TARGET) as MockSvc:
        inst = MockSvc.return_value
        inst.log_data_access = AsyncMock(side_effect=_capture)

        from app.api.v1.candidates.candidates_crud import _audit_pii_access

        user = _user(role="recruiter", can_salary=True, can_sensitive=True)
        await _audit_pii_access(
            user,
            candidate_id="cand-xyz",
            company_id="co-abc",
            role_defaults={},
        )

    per_field_calls = [c for c in calls if "pii_fields_masked" in (c.get("details") or {})]
    assert len(per_field_calls) == 1, f"Expected exactly 1 per-field call, got {per_field_calls}"
    c = per_field_calls[0]
    assert c["resource_type"] == "candidate"
    assert c["resource_id"] == "cand-xyz"
    assert c["company_id"] == "co-abc"
    assert c["action"] == "view_pii_fields"
    assert c["user_email"] == "u@x.com"


@pytest.mark.asyncio
async def test_audit_fully_nonblocking_on_error():
    """Even if AuditService.log_data_access raises, _audit_pii_access swallows it."""
    with patch(_PATCH_TARGET) as MockSvc:
        inst = MockSvc.return_value
        inst.log_data_access = AsyncMock(side_effect=RuntimeError("db gone"))

        from app.api.v1.candidates.candidates_crud import _audit_pii_access

        # Should not raise
        await _audit_pii_access(
            _user(),
            candidate_id="cand1",
            company_id="co1",
            role_defaults=None,
        )


@pytest.mark.asyncio
async def test_audit_preserves_legacy_bucket_calls():
    """Existing action=view_pii bucket calls are preserved alongside the new per-field call."""
    calls = []

    async def _capture(**kwargs):
        calls.append(dict(kwargs))

    with patch(_PATCH_TARGET) as MockSvc:
        inst = MockSvc.return_value
        inst.log_data_access = AsyncMock(side_effect=_capture)

        from app.api.v1.candidates.candidates_crud import _audit_pii_access

        # User with both grants => 2 legacy bucket calls + 1 per-field call = 3 total
        await _audit_pii_access(
            _user(can_salary=True, can_sensitive=True),
            candidate_id="cand1",
            company_id="co1",
            role_defaults={},
        )

    bucket_calls = [c for c in calls if c.get("action") == "view_pii"]
    per_field_calls = [c for c in calls if c.get("action") == "view_pii_fields"]
    assert len(bucket_calls) == 2, f"Expected 2 legacy bucket calls, got {bucket_calls}"
    assert len(per_field_calls) == 1, f"Expected 1 per-field call, got {per_field_calls}"
