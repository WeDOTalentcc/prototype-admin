"""
Tests for ContactEnrichmentService (sourcing).

Tests cover:
- Contact dedup (candidate-level and linkedin_url-level)
- Circuit breaker integration
- Rails sync trigger
- Batch enrichment
- has_contact helper
"""
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate


class _FakeCandidate:
    def __init__(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "name": "Test User",
            "email": None,
            "phone": None,
            "best_personal_email": None,
            "best_business_email": None,
            "linkedin_url": "https://www.linkedin.com/in/testuser",
            "additional_data": None,
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


class TestApifyCircuitBreakerConfig:

    def test_apify_circuit_registered_in_all_circuits(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS, APIFY_CIRCUIT
        assert "apify" in ALL_CIRCUITS
        assert ALL_CIRCUITS["apify"] is APIFY_CIRCUIT

    def test_apify_circuit_config_matches_pearch(self):
        from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT, PEARCH_CIRCUIT
        assert APIFY_CIRCUIT.config.failure_threshold == PEARCH_CIRCUIT.config.failure_threshold
        assert APIFY_CIRCUIT.config.recovery_timeout == PEARCH_CIRCUIT.config.recovery_timeout
        assert APIFY_CIRCUIT.config.success_threshold == PEARCH_CIRCUIT.config.success_threshold
        assert APIFY_CIRCUIT.config.timeout == PEARCH_CIRCUIT.config.timeout

    def test_apify_circuit_in_slos_and_degraded(self):
        from app.shared.resilience.circuit_breaker import (
            CIRCUIT_BREAKER_SLOS, DEGRADED_MODE_RESPONSES,
        )
        assert "apify" in CIRCUIT_BREAKER_SLOS
        assert "apify" in DEGRADED_MODE_RESPONSES


class TestContactEnrichmentHasContact:

    def _svc(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        return ContactEnrichmentService(enrichment_svc=MagicMock())

    def test_has_contact_with_email(self):
        svc = self._svc()
        c = _FakeCandidate(email="a@b.com")
        assert svc._has_contact(c) is True

    def test_has_contact_with_phone(self):
        svc = self._svc()
        c = _FakeCandidate(phone="+5511999")
        assert svc._has_contact(c) is True

    def test_has_contact_with_best_personal_email(self):
        svc = self._svc()
        c = _FakeCandidate(best_personal_email="x@y.com")
        assert svc._has_contact(c) is True

    def test_no_contact(self):
        svc = self._svc()
        c = _FakeCandidate()
        assert svc._has_contact(c) is False


class TestRecentlyEnriched:

    def _svc(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        return ContactEnrichmentService(enrichment_svc=MagicMock())

    def test_not_enriched(self):
        svc = self._svc()
        c = _FakeCandidate(additional_data=None)
        assert svc._recently_enriched(c) is False

    def test_enriched_recently(self):
        svc = self._svc()
        c = _FakeCandidate(additional_data={
            "enrichment": {
                "last_enriched_at": datetime.utcnow().isoformat(),
            }
        })
        assert svc._recently_enriched(c) is True

    def test_enriched_old(self):
        svc = self._svc()
        old = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        c = _FakeCandidate(additional_data={
            "enrichment": {"last_enriched_at": old}
        })
        assert svc._recently_enriched(c) is False


class TestEnrichCandidateContact:

    def _svc(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        mock_enrichment = AsyncMock()
        return ContactEnrichmentService(enrichment_svc=mock_enrichment), mock_enrichment

    def _mock_db(self, candidate):
        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result_mock
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_candidate_not_found(self):
        svc, _ = self._svc()
        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        res = await svc.enrich_candidate_contact(db, uuid4())
        assert res["success"] is False
        assert "not found" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_already_has_contact(self):
        svc, _ = self._svc()
        c = _FakeCandidate(email="exists@mail.com")
        db = self._mock_db(c)

        res = await svc.enrich_candidate_contact(db, c.id)
        assert res["success"] is True
        assert res["already_has_contact"] is True
        assert res["source"] == "existing"

    @pytest.mark.asyncio
    async def test_no_linkedin_url(self):
        svc, _ = self._svc()
        c = _FakeCandidate(linkedin_url=None)
        db = self._mock_db(c)

        res = await svc.enrich_candidate_contact(db, c.id)
        assert res["success"] is False
        assert "linkedin" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_dedup_skip_recently_enriched(self):
        svc, _ = self._svc()
        c = _FakeCandidate(additional_data={
            "enrichment": {"last_enriched_at": datetime.utcnow().isoformat()}
        })
        db = self._mock_db(c)

        res = await svc.enrich_candidate_contact(db, c.id)
        assert res["source"] == "dedup_skip"

    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self):
        svc, _ = self._svc()
        c = _FakeCandidate()
        db = self._mock_db(c)

        with patch("app.domains.sourcing.services.contact_enrichment_service.APIFY_CIRCUIT") as mock_cb:
            mock_cb.is_open = True
            res = await svc.enrich_candidate_contact(db, c.id)
            assert res["success"] is False
            assert "circuit breaker" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_successful_enrichment(self):
        svc, mock_enrich = self._svc()
        c = _FakeCandidate()
        db = self._mock_db(c)

        mock_enrich.enrich_candidate.return_value = {
            "success": True,
            "fields_updated": ["email", "phone"],
        }

        async def refresh_side_effect(obj):
            obj.email = "new@email.com"
            obj.phone = "+5511999"

        db.refresh.side_effect = refresh_side_effect

        with patch("app.domains.sourcing.services.contact_enrichment_service.APIFY_CIRCUIT") as mock_cb:
            mock_cb.is_open = False
            res = await svc.enrich_candidate_contact(db, c.id)

        assert res["success"] is True
        assert res["source"] == "apify"
        assert "email" in res["fields_updated"]
        mock_cb.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrichment_failure_records_circuit_breaker(self):
        svc, mock_enrich = self._svc()
        c = _FakeCandidate()
        db = self._mock_db(c)

        mock_enrich.enrich_candidate.side_effect = Exception("Apify timeout")

        with patch("app.domains.sourcing.services.contact_enrichment_service.APIFY_CIRCUIT") as mock_cb:
            mock_cb.is_open = False
            res = await svc.enrich_candidate_contact(db, c.id)

        assert res["success"] is False
        assert res["source"] == "apify_error"
        mock_cb.record_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_bypasses_dedup(self):
        svc, mock_enrich = self._svc()
        c = _FakeCandidate(additional_data={
            "enrichment": {"last_enriched_at": datetime.utcnow().isoformat()}
        })
        db = self._mock_db(c)

        mock_enrich.enrich_candidate.return_value = {
            "success": True,
            "fields_updated": ["email"],
        }

        async def refresh_side_effect(obj):
            obj.email = "forced@email.com"

        db.refresh.side_effect = refresh_side_effect

        with patch("app.domains.sourcing.services.contact_enrichment_service.APIFY_CIRCUIT") as mock_cb:
            mock_cb.is_open = False
            res = await svc.enrich_candidate_contact(db, c.id, force=True)

        assert res["success"] is True


class TestLinkedInUrlDedup:

    @pytest.mark.asyncio
    async def test_linkedin_url_recently_enriched(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        svc = ContactEnrichmentService(enrichment_svc=MagicMock())

        other_candidate = _FakeCandidate(
            linkedin_url="https://www.linkedin.com/in/testuser",
            additional_data={
                "enrichment": {"last_enriched_at": datetime.utcnow().isoformat()}
            },
        )

        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [other_candidate]
        db.execute.return_value = result_mock

        is_dup = await svc._linkedin_url_recently_enriched(
            db, "https://www.linkedin.com/in/testuser"
        )
        assert is_dup is True

    @pytest.mark.asyncio
    async def test_linkedin_url_not_recently_enriched(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        svc = ContactEnrichmentService(enrichment_svc=MagicMock())

        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute.return_value = result_mock

        is_dup = await svc._linkedin_url_recently_enriched(
            db, "https://www.linkedin.com/in/newuser"
        )
        assert is_dup is False


class TestRailsSync:

    @pytest.mark.asyncio
    async def test_sync_to_rails_disabled(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        svc = ContactEnrichmentService(enrichment_svc=MagicMock())

        c = _FakeCandidate(email="a@b.com")

        with patch.dict("os.environ", {"RAILS_API_URL": ""}, clear=False):
            await svc._sync_to_rails(c, ["email"])

    @pytest.mark.asyncio
    async def test_sync_to_rails_no_fields(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        svc = ContactEnrichmentService(enrichment_svc=MagicMock())
        c = _FakeCandidate()
        await svc._sync_to_rails(c, [])

    @pytest.mark.asyncio
    async def test_sync_to_rails_publishes_event(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        svc = ContactEnrichmentService(enrichment_svc=MagicMock())

        c = _FakeCandidate(email="synced@mail.com", phone="+5511999")

        mock_adapter = AsyncMock()
        mock_adapter.publish_event.return_value = True

        with patch("app.domains.integrations_hub.services.rails_adapter.RAILS_ENABLED", True), \
             patch("app.domains.integrations_hub.services.rails_adapter.CANDIDATE_FORK_TO_RAILS", {"email": "email", "phone": "phone"}), \
             patch("app.domains.integrations_hub.services.rails_adapter.RailsAdapter", return_value=mock_adapter):
            await svc._sync_to_rails(c, ["email", "phone"])

            mock_adapter.publish_event.assert_called_once()
            call_args = mock_adapter.publish_event.call_args
            assert call_args.kwargs.get("event_type") == "candidate.enriched"
            assert call_args.kwargs["data"]["enriched_fields"]["email"] == "synced@mail.com"
            assert call_args.kwargs["data"]["enriched_fields"]["phone"] == "+5511999"
            assert call_args.kwargs["data"]["source"] == "apify_linkedin"


class TestEnrichCandidateContactLinkedInDedup:

    @pytest.mark.asyncio
    async def test_dedup_linkedin_url_blocks_enrichment(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
        mock_enrich = AsyncMock()
        svc = ContactEnrichmentService(enrichment_svc=mock_enrich)

        c = _FakeCandidate(linkedin_url="https://www.linkedin.com/in/dupuser")

        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = c
        scalars_mock = MagicMock()
        other_candidate = _FakeCandidate(
            linkedin_url="https://www.linkedin.com/in/dupuser",
            additional_data={"enrichment": {"last_enriched_at": datetime.utcnow().isoformat()}},
        )
        scalars_mock.all.return_value = [other_candidate]
        result_dup = MagicMock()
        result_dup.scalars.return_value = scalars_mock

        call_count = 0
        async def side_effect_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return result_mock
            return result_dup

        db.execute.side_effect = side_effect_execute

        with patch("app.domains.sourcing.services.contact_enrichment_service.APIFY_CIRCUIT") as mock_cb:
            mock_cb.is_open = False
            res = await svc.enrich_candidate_contact(db, c.id)

        assert res["source"] == "dedup_linkedin_skip"
        mock_enrich.enrich_candidate.assert_not_called()
