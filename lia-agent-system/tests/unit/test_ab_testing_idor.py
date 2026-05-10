"""
UC-P0-08 — IDOR tests for A/B testing endpoints.

Vulnerability: company_id is accepted from the request body instead of being
extracted from the JWT. An authenticated user from "my_company" can send
company_id="other_company" and contaminate another tenant's data.

Fix: remove company_id from MetricRecord/BusinessMetricRecord schemas; derive it
exclusively from current_user.company_id (JWT) inside each handler.

Test strategy: patch decode_token to return a JWT payload for "my_company",
send a fake Bearer token so the AuthEnforcementMiddleware passes, and then
assert that service.record_metric is called with "my_company" not "other_company".

These tests FAIL before the fix (body company_id used) and PASS after (JWT used).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_or_demo,
    get_current_user_strict,
)

JWT_COMPANY = "my_company"
FAKE_TOKEN = "fake-jwt-token-for-idor-test"
FAKE_USER_UUID = "123e4567-e89b-12d3-a456-426614174000"

# JWT payload that the middleware + endpoint auth deps will accept
FAKE_JWT_PAYLOAD = {
    "sub": FAKE_USER_UUID,
    "type": "access",
    "company_id": JWT_COMPANY,
    "role": "recruiter",
}


def make_mock_db():
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = []
    scalars.first.return_value = None
    result.scalars.return_value = scalars
    result.scalar_one_or_none.return_value = None
    result.scalar.return_value = 0
    result.first.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


def get_mock_db():
    yield make_mock_db()


def get_jwt_user():
    """Mock User object returned by all auth dependencies — company_id comes from JWT."""
    user = MagicMock()
    user.id = FAKE_USER_UUID
    user.company_id = JWT_COMPANY
    user.role = "recruiter"
    user.is_active = True
    user.email = f"recruiter@{JWT_COMPANY}.com"
    return user


@pytest.fixture(scope="module")
def client():
    """
    Single TestClient for the whole module.
    Patches decode_token so the AuthEnforcementMiddleware accepts our fake Bearer token,
    and patches get_current_user/strict so FastAPI deps return the mock user.
    
    Mocks init_db to prevent pool contamination from other tests that used
    asyncio.run() to create asyncpg connections on different event loops.
    """
    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user] = get_jwt_user
    app.dependency_overrides[get_current_active_user] = get_jwt_user
    app.dependency_overrides[get_current_user_or_demo] = get_jwt_user
    app.dependency_overrides[get_current_user_strict] = get_jwt_user

    with patch("app.auth.security.decode_token", return_value=FAKE_JWT_PAYLOAD),          patch("app.main.init_db", new=AsyncMock()):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()


def _auth_headers():
    """Authorization header with fake Bearer token."""
    return {"Authorization": f"Bearer {FAKE_TOKEN}"}


# ── IDOR tests ─────────────────────────────────────────────────────────────

def test_record_metric_uses_jwt_company_id_not_body(client):
    """
    POST /{test_name}/record

    Body sends company_id='other_company'. JWT/session user belongs to 'my_company'.
    service.record_metric MUST be called with company_id='my_company'.

    FAILS before fix (body.company_id passed through) / PASSES after fix (JWT used).
    """
    payload = {
        "variant_name": "control",
        "session_id": "sess-idor-001",
        "company_id": "other_company",   # attacker's forged value
        "metric_name": "conversion",
        "metric_value": 1.0,
    }

    fake_record = MagicMock()
    fake_record.id = "record-uuid-1"

    with patch(
        "app.shared.learning.ab_testing_service.ABTestingService.record_metric",
        new_callable=AsyncMock,
        return_value=fake_record,
    ) as mock_record:
        resp = client.post(
            "/api/v1/ab-tests/idor_test/record",
            json=payload,
            headers=_auth_headers(),
        )

    assert resp.status_code in (200, 201), (
        f"Expected 200/201 after fix, got {resp.status_code}: {resp.text}"
    )
    assert mock_record.called, "service.record_metric was never called"

    ckw = mock_record.call_args.kwargs
    if "company_id" in ckw:
        used = ckw["company_id"]
    else:
        args = mock_record.call_args.args
        # record_metric(self, test_name, variant_name, session_id, company_id, ...)
        used = args[3] if len(args) > 3 else None

    assert used == JWT_COMPANY, (
        f"IDOR DETECTED: service.record_metric called with company_id='{used}'. "
        f"Body supplied 'other_company'; JWT user belongs to '{JWT_COMPANY}'. "
        f"company_id MUST come from the JWT, not the request body."
    )


def test_record_metric_body_without_company_id_accepted(client):
    """
    POST /{test_name}/record WITHOUT company_id in the body.

    BEFORE fix: returns 422 (company_id is a required schema field).
    AFTER fix:  returns 200/201 (company_id comes from JWT, not body).
    """
    payload = {
        "variant_name": "control",
        "session_id": "sess-idor-002",
        # No company_id — after fix this must come from JWT
        "metric_name": "conversion",
        "metric_value": 1.0,
    }

    fake_record = MagicMock()
    fake_record.id = "record-uuid-2"

    with patch(
        "app.shared.learning.ab_testing_service.ABTestingService.record_metric",
        new_callable=AsyncMock,
        return_value=fake_record,
    ):
        resp = client.post(
            "/api/v1/ab-tests/idor_test/record",
            json=payload,
            headers=_auth_headers(),
        )

    assert resp.status_code != 422, (
        "SCHEMA LEAK: endpoint returned 422 — company_id is still a required body field. "
        f"After the fix it must come exclusively from the JWT. Response: {resp.text}"
    )
    assert resp.status_code in (200, 201), (
        f"Expected 200/201 after fix, got {resp.status_code}: {resp.text}"
    )


def test_record_business_metrics_uses_jwt_company_id_not_body(client):
    """
    POST /{test_name}/record-business-metrics

    Same IDOR check for the business-metrics endpoint. Every service.record_metric
    call must use JWT company_id ('my_company'), not body company_id ('other_company').

    FAILS before fix / PASSES after fix.
    """
    payload = {
        "variant_name": "treatment",
        "session_id": "sess-idor-biz-001",
        "company_id": "other_company",   # attacker payload
        "satisfaction_score": 4.5,
    }

    fake_record = MagicMock()
    fake_record.id = "record-biz-1"

    with patch(
        "app.shared.learning.ab_testing_service.ABTestingService.record_metric",
        new_callable=AsyncMock,
        return_value=fake_record,
    ) as mock_record:
        resp = client.post(
            "/api/v1/ab-tests/idor_test/record-business-metrics",
            json=payload,
            headers=_auth_headers(),
        )

    assert resp.status_code in (200, 201), (
        f"Expected 200/201 after fix, got {resp.status_code}: {resp.text}"
    )
    assert mock_record.called, "service.record_metric was never called"

    for idx, single_call in enumerate(mock_record.call_args_list):
        ckw = single_call.kwargs
        if "company_id" in ckw:
            used = ckw["company_id"]
        else:
            args = single_call.args
            used = args[3] if len(args) > 3 else None

        assert used == JWT_COMPANY, (
            f"IDOR DETECTED on call #{idx + 1}: service.record_metric received "
            f"company_id='{used}'. JWT user belongs to '{JWT_COMPANY}'. "
            f"Body 'other_company' must be ignored."
        )
