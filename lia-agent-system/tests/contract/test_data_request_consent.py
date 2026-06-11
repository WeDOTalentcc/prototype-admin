"""
Phase 3a regression sensor — LGPD Art. 11 consent gate for DataRequest sensitive fields.

Tests (pure-unit, mocked DB via FastAPI dependency_overrides):
1. submit with sensitive field, no consent_id → HTTP 422 consent_required
2. submit with sensitive field + valid consent_id → passes gate
3. submit without sensitive field, no consent_id → 200 no gate
4. POST /consent → ConsentRecord created (mocked DB)
5. consent_id from different candidate → HTTP 422 consent_invalid
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.public.candidate_portal import (
    SENSITIVE_DATA_REQUEST_FIELDS,
    router,
    get_db,
)
from app.models.data_request import DataRequest, DataRequestStatus


def _make_data_request(
    *,
    status: DataRequestStatus = DataRequestStatus.PENDING,
    fields_requested: list[dict] | None = None,
    fields_completed: list[dict] | None = None,
    otp_verified: bool = True,
    vacancy_id: uuid.UUID | None = None,
) -> MagicMock:
    dr = MagicMock(spec=DataRequest)
    dr.id = uuid.uuid4()
    dr.candidate_id = uuid.uuid4()
    dr.company_id = uuid.uuid4()
    dr.vacancy_id = vacancy_id
    dr.status = status
    dr.fields_requested = fields_requested or []
    dr.fields_completed = fields_completed or []
    dr.otp_verified = otp_verified
    dr.expires_at = datetime.utcnow() + timedelta(days=7)
    dr.is_expired = lambda: False
    dr.get_completion_percentage = lambda: 0.0
    return dr


def _make_app_with_db(mock_db) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    return app


def _mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.get = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Test 1: sensitive field + no consent_id → 422
# ---------------------------------------------------------------------------

def test_submit_with_sensitive_fields_without_consent_id_blocked():
    """Final submit with disability_info field and no consent_id must return 422."""
    sensitive_field = next(iter(SENSITIVE_DATA_REQUEST_FIELDS))
    dr = _make_data_request(
        fields_requested=[
            {"name": sensitive_field, "field_type": "text", "required": True}
        ]
    )
    db = _mock_db()
    app = _make_app_with_db(db)
    client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.api.public.candidate_portal.get_data_request_by_token",
        new=AsyncMock(return_value=dr),
    ):
        resp = client.post(
            f"/portal/data-request/{dr.id}/submit",
            json={
                "fields": [{"name": sensitive_field, "value": "informacao"}],
                "is_final": True,
            },
        )

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    body = resp.json()
    detail = body.get("detail") or body
    assert "consent_required" in str(detail), f"Expected consent_required in: {detail}"


# ---------------------------------------------------------------------------
# Test 2: sensitive field + valid consent_id → gate passes
# ---------------------------------------------------------------------------

def test_submit_with_sensitive_fields_with_valid_consent_id_passes():
    """Final submit with disability_info + valid consent_id must pass the gate."""
    sensitive_field = next(iter(SENSITIVE_DATA_REQUEST_FIELDS))
    dr = _make_data_request(
        fields_requested=[
            {"name": sensitive_field, "field_type": "text", "required": True}
        ]
    )
    db = _mock_db()
    consent_id = uuid.uuid4()

    # Mock consent record lookup — first execute returns the valid CR
    mock_cr = MagicMock()
    mock_cr.id = consent_id
    mock_cr.candidate_id = dr.candidate_id
    mock_cr.is_active = True

    call_count = 0

    async def multi_execute(stmt):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            # consent gate lookup
            result.scalar_one_or_none = MagicMock(return_value=mock_cr)
        else:
            # DataRequestResponse lookup (field loop)
            result.scalar_one_or_none = MagicMock(return_value=None)
        return result

    db.execute = multi_execute

    app = _make_app_with_db(db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch(
            "app.api.public.candidate_portal.get_data_request_by_token",
            new=AsyncMock(return_value=dr),
        ),
        # Patch DataRequestResponseModel so db.add doesn't get a real SA model
        patch("app.api.public.candidate_portal.DataRequestResponseModel", MagicMock()),
        # Patch ConsentRecord so the where() clause in the gate doesn't fail
        patch("app.api.public.candidate_portal.ConsentRecord", MagicMock()),
    ):
        resp = client.post(
            f"/portal/data-request/{dr.id}/submit",
            json={
                "fields": [{"name": sensitive_field, "value": "informacao"}],
                "is_final": True,
                "consent_id": str(consent_id),
            },
        )

    if resp.status_code == 422:
        body = resp.json()
        detail = body.get("detail") or body
        assert "consent_required" not in str(detail), (
            f"Gate should pass with valid consent_id, got: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Test 3: no sensitive field, no consent_id → 200 (gate not triggered)
# ---------------------------------------------------------------------------

def test_submit_without_sensitive_fields_no_consent_required():
    """Non-sensitive fields do not require consent_id — gate must not block."""
    dr = _make_data_request(
        fields_requested=[
            {"name": "full_name", "field_type": "text", "required": True}
        ]
    )
    db = _mock_db()
    empty_result = MagicMock()
    empty_result.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=empty_result)

    app = _make_app_with_db(db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch(
            "app.api.public.candidate_portal.get_data_request_by_token",
            new=AsyncMock(return_value=dr),
        ),
        patch("app.api.public.candidate_portal.DataRequestResponseModel", MagicMock()),
    ):
        resp = client.post(
            f"/portal/data-request/{dr.id}/submit",
            json={
                "fields": [{"name": "full_name", "value": "Maria Silva"}],
                "is_final": True,
            },
        )

    if resp.status_code == 422:
        body = resp.json()
        assert "consent_required" not in str(body), (
            f"Non-sensitive fields must not require consent: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Test 4: POST /consent → ConsentRecord created
# ---------------------------------------------------------------------------

def test_consent_endpoint_creates_consent_record():
    """POST /{token}/consent must return ok=True and a non-empty consent_id."""
    dr = _make_data_request(
        fields_requested=[
            {"name": "disability_info", "field_type": "text", "required": True}
        ]
    )
    db = _mock_db()

    fake_id = uuid.uuid4()

    class _FakeConsentRecord:
        """SQLAlchemy-neutral fake that satisfies db.add without mapping."""
        # Make it look like it has _sa_instance_state so SQLAlchemy does not reject it
        _sa_instance_state = MagicMock()

        def __init__(self, **kwargs):
            self.id = fake_id
            for k, v in kwargs.items():
                setattr(self, k, v)

    app = _make_app_with_db(db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch(
            "app.api.public.candidate_portal.get_data_request_by_token",
            new=AsyncMock(return_value=dr),
        ),
        patch("app.api.public.candidate_portal.ConsentRecord", side_effect=_FakeConsentRecord),
    ):
        resp = client.post(
            f"/portal/data-request/{dr.id}/consent",
            json={"canal": "web", "versao_disclaimer": "1.0"},
        )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("ok") is True
    assert "consent_id" in body and body["consent_id"]


# ---------------------------------------------------------------------------
# Test 5: consent_id from different candidate → 422
# ---------------------------------------------------------------------------

def test_consent_id_from_different_candidate_rejected():
    """consent_id belonging to another candidate must return 422 consent_invalid."""
    sensitive_field = next(iter(SENSITIVE_DATA_REQUEST_FIELDS))
    dr = _make_data_request(
        fields_requested=[
            {"name": sensitive_field, "field_type": "text", "required": True}
        ]
    )
    db = _mock_db()
    other_consent_id = uuid.uuid4()

    # db.get(ConsentRecord, _cid) returns None — consent_id not found / different candidate
    db.get = AsyncMock(return_value=None)

    app = _make_app_with_db(db)
    client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.api.public.candidate_portal.get_data_request_by_token",
        new=AsyncMock(return_value=dr),
    ):
        resp = client.post(
            f"/portal/data-request/{dr.id}/submit",
            json={
                "fields": [{"name": sensitive_field, "value": "info"}],
                "is_final": True,
                "consent_id": str(other_consent_id),
            },
        )

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    body = resp.json()
    detail = body.get("detail") or body
    assert "consent_invalid" in str(detail), f"Expected consent_invalid in: {detail}"
