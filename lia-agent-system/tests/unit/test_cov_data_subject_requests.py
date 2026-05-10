"""Coverage tests for app/schemas/data_subject_requests.py — Pydantic models."""
import pytest
from app.schemas.data_subject_requests import (
    DataSubjectRequestAssign,
    DataSubjectRequestComplete,
    DataSubjectRequestCreate,
    DataSubjectRequestListResponse,
    DataSubjectRequestPublicCreate,
    DataSubjectRequestPublicTrack,
    DataSubjectRequestReject,
    DataSubjectRequestResponse,
    DataSubjectRequestStats,
    DataSubjectRequestVerifyIdentity,
)


class TestDataSubjectRequestCreate:
    def test_basic(self):
        m = DataSubjectRequestCreate(
            company_id="co-001",
            subject_name="Ana Silva",
            subject_email="ana@example.com",
            subject_identifier="cand-001",
            request_type="access",
            description="I want to see my data",
        )
        assert m.company_id == "co-001"
        assert m.request_type == "access"
        assert m.subject_name == "Ana Silva"

    def test_deletion_request(self):
        m = DataSubjectRequestCreate(
            company_id="co-002",
            subject_name="Carlos",
            subject_email="carlos@test.com",
            subject_identifier="cand-002",
            request_type="deletion",
            description="Please delete all my data",
            source_channel="email",
        )
        assert m.request_type == "deletion"
        assert m.source_channel == "email"

    def test_correction_request(self):
        m = DataSubjectRequestCreate(
            company_id="co-003",
            subject_name="Maria",
            subject_email="maria@test.com",
            subject_identifier="cand-003",
            request_type="correction",
            description="Please correct my data",
        )
        assert m.request_type == "correction"


class TestDataSubjectRequestResponse:
    def test_basic(self):
        m = DataSubjectRequestResponse(
            id="req-001",
            company_id="co-001",
            request_type="access",
            status="pending",
            subject_name="Ana",
            subject_email="ana@example.com",
            subject_identifier="cand-001",
            description="Request description",
            source_channel="web",
        )
        assert m.id == "req-001"
        assert m.status == "pending"
        assert m.source_channel == "web"

    def test_completed(self):
        m = DataSubjectRequestResponse(
            id="req-002",
            company_id="co-001",
            request_type="erasure",
            status="completed",
            subject_name="Carlos",
            subject_email="carlos@test.com",
            subject_identifier="cand-002",
            description="Erasure request",
            source_channel="email",
        )
        assert m.status == "completed"


class TestDataSubjectRequestListResponse:
    def test_empty(self):
        m = DataSubjectRequestListResponse(requests=[], total=0, skip=0, limit=20)
        assert m.requests == []
        assert m.total == 0

    def test_with_items(self):
        req = DataSubjectRequestResponse(
            id="r1", company_id="co-001", request_type="access",
            status="pending", subject_name="Ana",
            subject_email="ana@example.com", subject_identifier="s1",
            description="desc", source_channel="web",
        )
        m = DataSubjectRequestListResponse(requests=[req], total=1, skip=0, limit=20)
        assert m.total == 1

    def test_pagination(self):
        m = DataSubjectRequestListResponse(requests=[], total=100, skip=20, limit=10)
        assert m.skip == 20
        assert m.limit == 10


class TestDataSubjectRequestAssign:
    def test_basic(self):
        m = DataSubjectRequestAssign(assigned_to="dpo@company.com")
        assert m.assigned_to == "dpo@company.com"

    def test_another(self):
        m = DataSubjectRequestAssign(assigned_to="privacy-team@co.com")
        assert m.assigned_to == "privacy-team@co.com"


class TestDataSubjectRequestComplete:
    def test_basic(self):
        m = DataSubjectRequestComplete(
            response="Your data has been provided in the attached file."
        )
        assert m.response == "Your data has been provided in the attached file."

    def test_erasure_complete(self):
        m = DataSubjectRequestComplete(
            response="All personal data has been deleted from our systems.",
        )
        assert "deleted" in m.response


class TestDataSubjectRequestReject:
    def test_basic(self):
        m = DataSubjectRequestReject(
            rejection_reason="Unable to verify identity"
        )
        assert m.rejection_reason == "Unable to verify identity"

    def test_another(self):
        m = DataSubjectRequestReject(
            rejection_reason="Request type not applicable for this data category"
        )
        assert m.rejection_reason is not None


class TestDataSubjectRequestPublicCreate:
    def test_basic(self):
        m = DataSubjectRequestPublicCreate(
            id="req-001",
            status="pending",
            request_type="access",
        )
        assert m.id == "req-001"
        assert m.status == "pending"

    def test_erasure(self):
        m = DataSubjectRequestPublicCreate(
            id="req-002",
            status="submitted",
            request_type="erasure",
        )
        assert m.request_type == "erasure"


class TestDataSubjectRequestPublicTrack:
    def test_basic(self):
        m = DataSubjectRequestPublicTrack(
            id="req-001",
            status="in_progress",
            request_type="access",
        )
        assert m.status == "in_progress"

    def test_completed(self):
        m = DataSubjectRequestPublicTrack(
            id="req-003",
            status="completed",
            request_type="portability",
        )
        assert m.status == "completed"


class TestDataSubjectRequestVerifyIdentity:
    def test_basic(self):
        m = DataSubjectRequestVerifyIdentity(
            identity_verification_method="email_confirmation",
            verified=True,
        )
        assert m.identity_verification_method == "email_confirmation"
        assert m.verified is True

    def test_not_verified(self):
        m = DataSubjectRequestVerifyIdentity(
            identity_verification_method="document_upload",
            verified=False,
        )
        assert m.verified is False


class TestDataSubjectRequestStats:
    def test_empty(self):
        m = DataSubjectRequestStats()
        assert m is not None

    def test_with_values(self):
        m = DataSubjectRequestStats(
            total_requests=50,
            pending_count=10,
            completed_count=35,
            rejected_count=5,
            avg_resolution_days=5.2,
        )
        assert m.total_requests == 50
        assert m.avg_resolution_days == pytest.approx(5.2)
