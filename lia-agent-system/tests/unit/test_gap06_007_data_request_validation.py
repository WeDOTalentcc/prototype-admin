"""
GAP-06-007 — Data Request Form Validation (P1)

Tests:
  - test_missing_required_field_returns_422
  - test_invalid_email_format_rejected
  - test_valid_request_accepted
  - test_extra_fields_forbidden
  - test_invalid_notification_channel_rejected
  - test_invalid_phone_format_rejected
  - test_valid_phone_formats_accepted
  - test_candidate_id_existence_check (unit-level: mocked)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Import the schema directly (no FastAPI app needed for schema-level tests)
# ---------------------------------------------------------------------------

def get_schema():
    import sys, importlib
    # Isolate import path issues by importing directly
    from app.api.v1.data_request import CreateDataRequestRequest
    return CreateDataRequestRequest


class TestCreateDataRequestRequestSchema:
    """Schema-level validation tests — no DB, no FastAPI needed."""

    def test_missing_required_field_returns_422(self):
        """candidate_id is required; omitting it raises ValidationError."""
        schema = get_schema()
        with pytest.raises(ValidationError) as exc_info:
            schema()  # no candidate_id
        errors = exc_info.value.errors()
        fields = [e["loc"][0] for e in errors]
        assert "candidate_id" in fields

    def test_valid_minimal_request_accepted(self):
        """A request with only candidate_id (all defaults) is valid."""
        schema = get_schema()
        req = schema(candidate_id=uuid4())
        assert req.candidate_id is not None
        assert req.send_notification is True
        assert req.notification_channels is None
        assert req.contact_email is None
        assert req.contact_phone is None

    def test_extra_fields_forbidden(self):
        """WeDoBaseModel extra='forbid': unknown fields raise ValidationError."""
        schema = get_schema()
        with pytest.raises(ValidationError) as exc_info:
            schema(candidate_id=uuid4(), unknown_field="bad")
        errors = exc_info.value.errors()
        extra_errors = [e for e in errors if e["type"] == "extra_forbidden"]
        assert len(extra_errors) == 1, f"Expected extra_forbidden error, got: {errors}"

    def test_invalid_email_format_rejected(self):
        """contact_email must be a valid email address."""
        schema = get_schema()
        with pytest.raises(ValidationError) as exc_info:
            schema(candidate_id=uuid4(), contact_email="not-an-email")
        errors = exc_info.value.errors()
        email_errors = [e for e in errors if "contact_email" in str(e["loc"])]
        assert len(email_errors) >= 1, f"Expected email validation error, got: {errors}"

    def test_valid_email_accepted(self):
        """A proper email address is accepted in contact_email."""
        schema = get_schema()
        req = schema(candidate_id=uuid4(), contact_email="candidato@empresa.com.br")
        assert req.contact_email == "candidato@empresa.com.br"

    def test_invalid_notification_channel_rejected(self):
        """Unknown channel name raises ValidationError with clear message."""
        schema = get_schema()
        with pytest.raises(ValidationError) as exc_info:
            schema(candidate_id=uuid4(), notification_channels=["sms"])  # sms not valid
        errors = exc_info.value.errors()
        channel_errors = [e for e in errors if "notification_channels" in str(e["loc"])]
        assert len(channel_errors) >= 1, f"Expected channel validation error, got: {errors}"
        # Error message should mention invalid channel
        assert "invalid_channel" in str(errors) or "sms" in str(errors)

    def test_valid_notification_channels_accepted(self):
        """All four valid channels are accepted."""
        schema = get_schema()
        for channel in ("email", "whatsapp", "voice", "web"):
            req = schema(candidate_id=uuid4(), notification_channels=[channel])
            assert req.notification_channels == [channel]

    def test_invalid_phone_format_rejected(self):
        """contact_phone with invalid format raises ValidationError."""
        schema = get_schema()
        with pytest.raises(ValidationError) as exc_info:
            schema(candidate_id=uuid4(), contact_phone="abc-invalid")
        errors = exc_info.value.errors()
        phone_errors = [e for e in errors if "contact_phone" in str(e["loc"])]
        assert len(phone_errors) >= 1, f"Expected phone validation error, got: {errors}"
        assert "invalid_phone_format" in str(errors)

    def test_valid_phone_formats_accepted(self):
        """Brazilian phone formats are accepted."""
        schema = get_schema()
        valid_phones = [
            "+55 11 91234-5678",
            "(11) 91234-5678",
            "11912345678",
            "11 91234-5678",
        ]
        for phone in valid_phones:
            req = schema(candidate_id=uuid4(), contact_phone=phone)
            assert req.contact_phone is not None, f"Phone {phone!r} was rejected"

    def test_expiration_days_bounds(self):
        """expiration_days must be between 1 and 90."""
        schema = get_schema()
        with pytest.raises(ValidationError):
            schema(candidate_id=uuid4(), expiration_days=0)
        with pytest.raises(ValidationError):
            schema(candidate_id=uuid4(), expiration_days=91)
        # boundaries are accepted
        req_min = schema(candidate_id=uuid4(), expiration_days=1)
        req_max = schema(candidate_id=uuid4(), expiration_days=90)
        assert req_min.expiration_days == 1
        assert req_max.expiration_days == 90


class TestCandidateIdExistenceCheckAtHandlerLevel:
    """
    Unit tests for the handler-level candidate_id existence gate.

    These tests use mocks so no real DB is needed.
    The handler raises HTTP 422 when candidate is not found in the tenant.
    """

    @pytest.mark.asyncio
    async def test_candidate_not_found_returns_422(self):
        """Handler returns 422 with candidate_not_found when candidate absent."""
        from fastapi import HTTPException

        # Mock the repository to return None (candidate absent)
        with patch(
            "app.domains.candidates.repositories.candidate_repository.CandidateRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "app.domains.communication.services.data_request_service.data_request_service.create_data_request",
            new_callable=AsyncMock,
        ) as mock_create:
            from app.api.v1.data_request import create_data_request
            from app.api.v1.data_request import CreateDataRequestRequest

            db = AsyncMock()
            company_id = str(uuid4())
            request = CreateDataRequestRequest(candidate_id=uuid4())

            with pytest.raises(HTTPException) as exc_info:
                await create_data_request(request=request, db=db, company_id=company_id)

            assert exc_info.value.status_code == 422
            detail = exc_info.value.detail
            assert isinstance(detail, list)
            assert detail[0]["error"] == "candidate_not_found"
            assert detail[0]["field"] == "candidate_id"
            # Ensure create_data_request was NOT called (fail-closed before side effect)
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_candidate_found_proceeds_to_create(self):
        """Handler proceeds when candidate exists in the tenant."""
        from unittest.mock import MagicMock, AsyncMock, patch
        from uuid import uuid4

        mock_candidate = MagicMock()
        mock_data_request = MagicMock()
        mock_data_request.id = uuid4()
        mock_data_request.candidate_id = uuid4()
        mock_data_request.vacancy_id = None
        mock_data_request.template_id = None
        mock_data_request.token = "tok123"
        from app.models.data_request import DataRequestStatus
        mock_data_request.status = DataRequestStatus.PENDING
        mock_data_request.fields_requested = []
        mock_data_request.fields_completed = []
        from app.models.data_request import TriggerType
        mock_data_request.trigger_type = TriggerType.MANUAL
        mock_data_request.trigger_stage = None
        mock_data_request.is_blocking = False
        from datetime import datetime, timedelta
        mock_data_request.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_data_request.completion_percentage = 0.0
        mock_data_request.sent_via_email = False
        mock_data_request.sent_via_whatsapp = False
        mock_data_request.reminder_count = 0
        mock_data_request.first_accessed_at = None
        mock_data_request.last_accessed_at = None
        mock_data_request.completed_at = None
        mock_data_request.created_at = datetime.utcnow()
        mock_data_request.updated_at = datetime.utcnow()

        with patch(
            "app.domains.candidates.repositories.candidate_repository.CandidateRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_candidate,
        ), patch(
            "app.domains.communication.services.data_request_service.data_request_service.create_data_request",
            new_callable=AsyncMock,
            return_value=mock_data_request,
        ) as mock_create, patch(
            "app.domains.communication.services.data_request_service.data_request_service.send_notification",
            new_callable=AsyncMock,
        ):
            from app.api.v1.data_request import create_data_request
            from app.api.v1.data_request import CreateDataRequestRequest

            db = AsyncMock()
            db.refresh = AsyncMock()
            company_id = str(uuid4())
            request = CreateDataRequestRequest(candidate_id=uuid4(), send_notification=False)

            response = await create_data_request(request=request, db=db, company_id=company_id)

            # create_data_request was called — candidate found, gate passed
            mock_create.assert_called_once()
