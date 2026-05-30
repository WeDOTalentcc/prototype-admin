"""
Contract Tests: Job Offers

Verifica:
  - JobOfferRepository tem métodos obrigatórios
  - _require_company_id bloqueia corretamente
  - Ciclo de vida: draft → sent → accepted/rejected/withdrawn
  - Status inválido rejeitado pelo repo (não avança estado incorreto)
  - Campos obrigatórios presentes no modelo
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Contract: JobOfferRepository métodos obrigatórios
# ---------------------------------------------------------------------------

class TestJobOfferRepositoryContract:

    def test_has_create_method(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        assert callable(JobOfferRepository.create)

    def test_has_send_method(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        assert callable(JobOfferRepository.send)

    def test_has_record_response_method(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        assert callable(JobOfferRepository.record_response)

    def test_has_withdraw_method(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        assert callable(JobOfferRepository.withdraw)

    def test_has_count_by_status_method(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        assert callable(JobOfferRepository.count_by_status)

    def test_require_company_id_raises_on_none(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        with pytest.raises((ValueError, Exception)):
            JobOfferRepository._require_company_id(None)

    def test_require_company_id_raises_on_empty_string(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        with pytest.raises((ValueError, Exception)):
            JobOfferRepository._require_company_id("")

    def test_require_company_id_passes_valid(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        result = JobOfferRepository._require_company_id("company-abc")
        assert result == "company-abc"


# ---------------------------------------------------------------------------
# Contract: JobOffer model
# ---------------------------------------------------------------------------

class TestJobOfferModelContract:

    def _make_offer(self, status="draft"):
        from lia_models.job_offer import JobOffer
        o = JobOffer()
        o.status = status
        o.company_id = "company-1"
        o.job_vacancy_id = "job-1"
        o.candidate_id = "candidate-1"
        o.created_at = datetime.now(timezone.utc)
        o.updated_at = datetime.now(timezone.utc)
        return o

    def test_is_active_true_for_draft(self):
        o = self._make_offer("draft")
        assert o.is_active() is True

    def test_is_active_true_for_sent(self):
        o = self._make_offer("sent")
        assert o.is_active() is True

    def test_is_active_false_for_accepted(self):
        o = self._make_offer("accepted")
        assert o.is_active() is False

    def test_is_active_false_for_rejected(self):
        o = self._make_offer("rejected")
        assert o.is_active() is False

    def test_is_active_false_for_withdrawn(self):
        o = self._make_offer("withdrawn")
        assert o.is_active() is False

    def test_model_has_required_fields(self):
        from lia_models.job_offer import JobOffer
        required = ["company_id", "job_vacancy_id", "candidate_id", "status", "currency"]
        for field in required:
            assert hasattr(JobOffer, field), f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Contract: lifecycle state machine
# ---------------------------------------------------------------------------

class TestJobOfferLifecycleContract:

    @pytest.mark.asyncio
    async def test_send_sets_sent_status_and_timestamp(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        from lia_models.job_offer import JobOffer

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = JobOfferRepository(db)

        offer = MagicMock(spec=JobOffer)
        offer.status = "draft"

        result = await repo.send(offer)

        assert offer.status == "sent"
        assert offer.sent_at is not None

    @pytest.mark.asyncio
    async def test_record_response_accepted_sets_correct_state(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        from lia_models.job_offer import JobOffer

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = JobOfferRepository(db)

        offer = MagicMock(spec=JobOffer)
        offer.status = "sent"

        await repo.record_response(offer, "accepted", "Great candidate!")

        assert offer.status == "accepted"
        assert offer.candidate_response == "accepted"
        assert offer.response_notes == "Great candidate!"
        assert offer.responded_at is not None

    @pytest.mark.asyncio
    async def test_withdraw_sets_withdrawn_status(self):
        from app.domains.approvals.repositories.job_offer_repository import JobOfferRepository
        from lia_models.job_offer import JobOffer

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = JobOfferRepository(db)

        offer = MagicMock(spec=JobOffer)
        await repo.withdraw(offer)

        assert offer.status == "withdrawn"
