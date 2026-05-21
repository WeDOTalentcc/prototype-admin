"""Coverage tests for app/schemas/offer.py — Pydantic models."""
import pytest
from datetime import datetime
from uuid import UUID
from app.schemas.offer import (
    OfferBonusVariable,
    OfferCancelRequest,
    OfferDraftCreate,
    OfferDraftUpdate,
    OfferDraftResponse,
    OfferSendAutoRequest,
    OfferSendAutoResponse,
    OfferPrepareManualResponse,
)

_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440001")
_UUID2 = UUID("550e8400-e29b-41d4-a716-446655440002")
_UUID3 = UUID("550e8400-e29b-41d4-a716-446655440003")
_DT = datetime(2024, 6, 1, 12, 0)


class TestOfferBonusVariable:
    def test_basic(self):
        from decimal import Decimal
        m = OfferBonusVariable(type="performance", value=Decimal("5000.00"))
        assert m.type == "performance"
        assert m.value == Decimal("5000.00")

    def test_commission(self):
        from decimal import Decimal
        m = OfferBonusVariable(type="commission", value=Decimal("2000.00"))
        assert m.type == "commission"


class TestOfferCancelRequest:
    def test_empty(self):
        m = OfferCancelRequest()
        assert m is not None

    def test_with_reason(self):
        m = OfferCancelRequest(reason="Candidate withdrew")
        assert m.reason == "Candidate withdrew"


class TestOfferDraftCreate:
    def test_basic(self):
        m = OfferDraftCreate(candidate_id="cand-001", job_id=_UUID2)
        assert m.candidate_id == "cand-001"
        assert m.job_id == _UUID2

    def test_optional_fields(self):
        m = OfferDraftCreate(candidate_id="cand-002", job_id=_UUID1)
        # Check model is valid and optional fields are accessible
        assert m is not None


class TestOfferDraftUpdate:
    def test_empty(self):
        m = OfferDraftUpdate()
        assert m is not None

    def test_salary_update(self):
        """Sprint F.4 #42 canonical-remap: wire-level field names are still
        accepted as validation aliases, but the resulting Python attribute
        uses the canonical column name (``salary``, not ``offered_salary``).
        """
        from decimal import Decimal
        # Legacy wire names still accepted on input (validation_alias).
        m = OfferDraftUpdate(offered_salary=Decimal("12000.00"), offered_salary_currency="BRL")
        # Attribute uses canonical column names.
        assert m.salary == Decimal("12000.00")
        assert m.currency == "BRL"


class TestOfferDraftResponse:
    def test_basic(self):
        m = OfferDraftResponse(
            id=_UUID1,
            company_id="co-001",
            candidate_id="cand-001",
            job_id=_UUID2,
            job_data_snapshot={"title": "Backend Dev"},
            candidate_data_snapshot={"name": "Ana Silva"},
            status="draft",
            created_by_user_id="user-001",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.id == _UUID1
        assert m.status == "draft"
        assert m.job_data_snapshot["title"] == "Backend Dev"

    def test_sent_status(self):
        m = OfferDraftResponse(
            id=_UUID2,
            company_id="co-002",
            candidate_id="cand-002",
            job_id=_UUID1,
            job_data_snapshot={},
            candidate_data_snapshot={},
            status="sent",
            created_by_user_id="user-002",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.status == "sent"


class TestOfferSendAutoRequest:
    def test_empty(self):
        m = OfferSendAutoRequest()
        assert m is not None


class TestOfferSendAutoResponse:
    def test_basic(self):
        m = OfferSendAutoResponse(
            offer_id=_UUID1,
            status="sent",
            email_log_id=_UUID2,
            sent_at=_DT,
            message="Email sent successfully",
        )
        assert m.offer_id == _UUID1
        assert m.status == "sent"
        assert m.message == "Email sent successfully"


class TestOfferPrepareManualResponse:
    def test_basic(self):
        m = OfferPrepareManualResponse(
            offer_id=_UUID1,
            template_id=_UUID2,
            subject_pre_filled="Job Offer — Backend Dev",
            body_pre_filled="<p>Dear Candidate,</p>",
            variables={"name": "Ana", "salary": "R$12.000"},
            message="Ready to send",
        )
        assert m.offer_id == _UUID1
        assert m.variables["name"] == "Ana"
        assert m.subject_pre_filled == "Job Offer — Backend Dev"
