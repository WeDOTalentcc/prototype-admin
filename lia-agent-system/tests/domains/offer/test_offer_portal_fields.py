"""TDD tests for Migration 266 — offer portal fields (Phase 1).

Validates:
  - OfferProposal model has 6 new fields
  - mark_sent generates candidate_token + acceptance_url when PORTAL_BASE_URL set
  - render_offer_template_variables includes offer_link
  - compute_next_start_date_for_company respects min_notice_days
"""
import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestOfferProposalModelFields:
    """Verifica que os 6 novos campos existem no modelo."""

    def test_model_has_candidate_token(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "candidate_token"), (
            "OfferProposal.candidate_token ausente — rodar migration 266"
        )

    def test_model_has_acceptance_url(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "acceptance_url"), (
            "OfferProposal.acceptance_url ausente — rodar migration 266"
        )

    def test_model_has_candidate_viewed_at(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "candidate_viewed_at")

    def test_model_has_candidate_response_notes(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "candidate_response_notes")

    def test_model_has_negotiation_context_notes(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "negotiation_context_notes")

    def test_model_has_offer_link_sent_at(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        assert hasattr(OfferProposal, "offer_link_sent_at")


class TestMarkSentGeneratesToken:
    """Valida que mark_sent gera token + URL na primeira vez."""

    @pytest.fixture
    def proposal(self):
        from libs.models.lia_models.offer_proposal import OfferProposal
        p = MagicMock(spec=OfferProposal)
        p.status = "draft"
        p.candidate_token = None
        p.acceptance_url = None
        p.approval_request_id = uuid.uuid4()  # approved
        p.sent_via = []
        p.sent_at = None
        p.salary = None
        p.candidate_id = uuid.uuid4()
        p.job_vacancy_id = uuid.uuid4()
        return p

    @pytest.mark.asyncio
    async def test_generates_candidate_token_on_send(self, proposal):
        from app.domains.offer.services.offer_service import OfferService

        svc = OfferService.__new__(OfferService)
        svc._repo = AsyncMock()
        svc._repo.get_by_id = AsyncMock(return_value=proposal)
        svc._repo.update = AsyncMock(side_effect=lambda p: p)
        svc._db = AsyncMock()

        # Mock all the guards that check_can_send would do
        svc._requires_manager_approval = AsyncMock(return_value=False)
        svc._check_min_interviews_met = AsyncMock()
        svc._has_eligible_approver_for_amount = AsyncMock(return_value=True)

        with patch.dict("os.environ", {"PORTAL_BASE_URL": "https://app.wedotalent.cc"}):
            with patch("app.shared.services.audit_service.AuditService") as mock_audit:
                mock_audit.return_value.log_decision_in_session = AsyncMock()
                await svc.mark_sent(
                    offer_id=uuid.uuid4(),
                    company_id="comp-1",
                    user_id="user-1",
                    send_mode="auto",
                )

        # candidate_token was set
        assert proposal.candidate_token is not None, (
            "mark_sent deve gerar candidate_token (uuid) na primeira vez que envia"
        )
        # acceptance_url was set with PORTAL_BASE_URL
        assert proposal.acceptance_url is not None, (
            "mark_sent deve gerar acceptance_url quando PORTAL_BASE_URL está definido"
        )
        assert "portal/proposta/" in proposal.acceptance_url

    @pytest.mark.asyncio
    async def test_does_not_overwrite_existing_token(self, proposal):
        from app.domains.offer.services.offer_service import OfferService

        existing_token = uuid.uuid4()
        proposal.candidate_token = existing_token
        proposal.acceptance_url = f"https://app.wedotalent.cc/portal/proposta/{existing_token}"

        svc = OfferService.__new__(OfferService)
        svc._repo = AsyncMock()
        svc._repo.get_by_id = AsyncMock(return_value=proposal)
        svc._repo.update = AsyncMock(side_effect=lambda p: p)
        svc._db = AsyncMock()
        svc._requires_manager_approval = AsyncMock(return_value=False)
        svc._check_min_interviews_met = AsyncMock()
        svc._has_eligible_approver_for_amount = AsyncMock(return_value=True)

        with patch.dict("os.environ", {"PORTAL_BASE_URL": "https://app.wedotalent.cc"}):
            with patch("app.shared.services.audit_service.AuditService") as mock_audit:
                mock_audit.return_value.log_decision_in_session = AsyncMock()
                await svc.mark_sent(
                    offer_id=uuid.uuid4(),
                    company_id="comp-1",
                    user_id="user-1",
                    send_mode="auto",
                )

        assert proposal.candidate_token == existing_token, (
            "mark_sent NÃO deve sobrescrever candidate_token se já existe"
        )


class TestRenderOfferTemplateVariables:
    """Valida que offer_link está presente nas template vars."""

    def test_offer_link_in_template_vars(self):
        from app.domains.offer.services.offer_service import OfferService
        from libs.models.lia_models.offer_proposal import OfferProposal

        proposal = MagicMock(spec=OfferProposal)
        proposal.salary = None
        proposal.currency = "BRL"
        proposal.start_date = None
        proposal.response_deadline = None
        proposal.job_data_snapshot = {}
        proposal.candidate_data_snapshot = {}
        proposal.acceptance_url = "https://app.wedotalent.cc/portal/proposta/abc-123"
        proposal.custom_clauses = []
        proposal.bonus_pct = None
        proposal.bonus_target = None

        svc = OfferService.__new__(OfferService)
        result = svc.render_offer_template_variables(proposal)

        assert "offer_link" in result, (
            "render_offer_template_variables deve incluir offer_link para templates de email"
        )
        assert result["offer_link"] == "https://app.wedotalent.cc/portal/proposta/abc-123"


class TestComputeNextStartDate:
    """Valida compute_next_start_date_for_company."""

    @pytest.mark.asyncio
    async def test_returns_date_with_min_notice(self):
        from app.domains.offer.services.offer_service import compute_next_start_date_for_company

        mock_db = AsyncMock()
        with patch(
            "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository"
        ) as MockRepo:
            MockRepo.return_value.get_by_company_id = AsyncMock(return_value=None)
            result = await compute_next_start_date_for_company("comp-1", mock_db)

        expected_min = date.today() + timedelta(days=29)  # 30 days notice
        assert result >= expected_min, (
            "compute_next_start_date_for_company deve respeitar min_notice_days=30"
        )

    @pytest.mark.asyncio
    async def test_respects_allowed_start_days(self):
        from app.domains.offer.services.offer_service import compute_next_start_date_for_company

        mock_db = AsyncMock()
        mock_policy = MagicMock()
        mock_policy.offer_rules = {
            "allowed_start_day_of_month": [1, 15],
            "min_notice_days": 7,
            "onboarding_blackout_periods": [],
        }

        with patch(
            "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository"
        ) as MockRepo:
            MockRepo.return_value.get_by_company_id = AsyncMock(return_value=mock_policy)
            result = await compute_next_start_date_for_company("comp-1", mock_db)

        assert result.day in (1, 15), (
            "compute_next_start_date_for_company deve retornar dia em allowed_start_day_of_month=[1,15]"
        )
