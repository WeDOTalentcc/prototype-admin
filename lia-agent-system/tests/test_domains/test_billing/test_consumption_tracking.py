import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

os.environ.setdefault("APIFY_USD_TO_BRL_RATE", "5.50")
os.environ.setdefault("APIFY_MONTHLY_BUDGET_USD", "100.00")


class TestCreditTransactionTypes:

    def test_apify_enrichment_type_exists(self):
        from lia_models.billing import CreditTransactionType
        assert CreditTransactionType.APIFY_ENRICHMENT.value == "apify_enrichment"

    def test_pearch_search_type_exists(self):
        from lia_models.billing import CreditTransactionType
        assert CreditTransactionType.PEARCH_SEARCH.value == "pearch_search"

    def test_existing_types_preserved(self):
        from lia_models.billing import CreditTransactionType
        assert CreditTransactionType.PURCHASE.value == "purchase"
        assert CreditTransactionType.CONSUMPTION.value == "consumption"
        assert CreditTransactionType.REFUND.value == "refund"
        assert CreditTransactionType.BONUS.value == "bonus"
        assert CreditTransactionType.ADJUSTMENT.value == "adjustment"

    def test_action_credit_costs_include_new_types(self):
        from app.domains.credits.services.credit_service import ACTION_CREDIT_COSTS
        assert "pearch_search" in ACTION_CREDIT_COSTS
        assert "apify_enrichment" in ACTION_CREDIT_COSTS


class TestExternalApiConsumptionModel:

    def test_model_creation_apify(self):
        from lia_models.external_api_consumption import ExternalApiConsumption
        record = ExternalApiConsumption(
            company_id="test-company",
            user_id="test-user",
            provider="apify",
            operation="enrich",
            credits_consumed=0,
            cost_usd=0.01,
            cost_brl=0.055,
            exchange_rate=5.50,
            success=True,
            result_status="success",
        )
        assert record.provider == "apify"
        assert record.cost_usd == 0.01
        assert record.cost_brl == 0.055
        assert record.credits_consumed == 0
        assert record.result_status == "success"
        assert record.success is True

    def test_model_creation_pearch_with_credits(self):
        from lia_models.external_api_consumption import ExternalApiConsumption
        record = ExternalApiConsumption(
            company_id="test-company",
            provider="pearch",
            operation="search",
            credits_consumed=40,
            cost_usd=0.0,
            cost_brl=0.0,
            exchange_rate=5.50,
            success=True,
            result_status="success",
        )
        assert record.provider == "pearch"
        assert record.credits_consumed == 40
        assert record.cost_usd == 0.0

    def test_model_failure_records(self):
        from lia_models.external_api_consumption import ExternalApiConsumption
        record = ExternalApiConsumption(
            company_id="test-company",
            provider="apify",
            operation="enrich",
            credits_consumed=0,
            cost_usd=0.01,
            cost_brl=0.055,
            exchange_rate=5.50,
            success=False,
            result_status="fail",
            error_message="Connection timeout",
        )
        assert record.success is False
        assert record.result_status == "fail"
        assert record.error_message == "Connection timeout"

    def test_model_to_dict_includes_new_fields(self):
        from lia_models.external_api_consumption import ExternalApiConsumption
        record = ExternalApiConsumption(
            company_id="test-company",
            provider="pearch",
            operation="search",
            credits_consumed=20,
            cost_usd=0.0,
            cost_brl=0.0,
            exchange_rate=5.50,
            success=True,
            result_status="success",
        )
        d = record.to_dict()
        assert d["company_id"] == "test-company"
        assert d["provider"] == "pearch"
        assert d["credits_consumed"] == 20
        assert d["result_status"] == "success"
        assert "error_message" in d

    def test_provider_enum(self):
        from lia_models.external_api_consumption import ExternalApiProvider
        assert ExternalApiProvider.APIFY.value == "apify"
        assert ExternalApiProvider.PEARCH.value == "pearch"

    def test_operation_enum(self):
        from lia_models.external_api_consumption import ExternalApiOperation
        assert ExternalApiOperation.ENRICH.value == "enrich"
        assert ExternalApiOperation.SEARCH.value == "search"
        assert ExternalApiOperation.REVEAL_EMAIL.value == "reveal_email"
        assert ExternalApiOperation.REVEAL_PHONE.value == "reveal_phone"


class TestConsumptionTrackingService:

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_record_apify_call_creates_record(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0.0
        mock_db.execute.return_value = mock_result

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert", new_callable=AsyncMock):
            record = await ConsumptionTrackingService.record_apify_call(
                db=mock_db,
                company_id="comp-1",
                user_id="user-1",
                candidate_id=str(uuid4()),
                linkedin_url="https://linkedin.com/in/test",
                operation="enrich",
                cost_usd=0.01,
                success=True,
                result_status="success",
            )

        mock_db.add.assert_called_once()
        added_record = mock_db.add.call_args[0][0]
        assert added_record.provider == "apify"
        assert added_record.operation == "enrich"
        assert added_record.cost_usd == 0.01
        assert added_record.cost_brl == round(0.01 * 5.50, 4)
        assert added_record.success is True
        assert added_record.result_status == "success"
        assert added_record.credits_consumed == 0

    @pytest.mark.asyncio
    async def test_record_apify_call_failure_sets_result_status(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0.0
        mock_db.execute.return_value = mock_result

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert", new_callable=AsyncMock):
            record = await ConsumptionTrackingService.record_apify_call(
                db=mock_db,
                company_id="comp-1",
                user_id="user-1",
                candidate_id=None,
                linkedin_url=None,
                operation="enrich",
                cost_usd=0.01,
                success=False,
                result_status="fail",
                error_message="API error",
            )

        added_record = mock_db.add.call_args[0][0]
        assert added_record.success is False
        assert added_record.result_status == "fail"
        assert added_record.error_message == "API error"

    @pytest.mark.asyncio
    async def test_record_pearch_call_stores_credits(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        record = await ConsumptionTrackingService.record_pearch_call(
            db=mock_db,
            company_id="comp-1",
            user_id="user-1",
            operation="search",
            credits_consumed=40,
            success=True,
            result_status="success",
        )

        added_record = mock_db.add.call_args[0][0]
        assert added_record.provider == "pearch"
        assert added_record.operation == "search"
        assert added_record.credits_consumed == 40
        assert added_record.cost_usd == 0.0
        assert added_record.success is True

    @pytest.mark.asyncio
    async def test_record_pearch_call_error_path(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        record = await ConsumptionTrackingService.record_pearch_call(
            db=mock_db,
            company_id="comp-1",
            user_id=None,
            operation="search",
            credits_consumed=0,
            success=False,
            result_status="timeout",
            error_message="Timeout after 120s",
        )

        added_record = mock_db.add.call_args[0][0]
        assert added_record.success is False
        assert added_record.result_status == "timeout"
        assert added_record.credits_consumed == 0


class TestBudgetAlertDedup:

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_budget_alert_fires_when_exceeded(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        ConsumptionTrackingService._budget_alerts_sent.clear()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 150.0
        mock_db.execute.return_value = mock_result

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._budget_alerts_sent", {}):
            with patch("app.domains.analytics.services.activity_service.ActivityService") as MockActivity:
                mock_activity = MagicMock()
                mock_activity.create_activity = AsyncMock()
                MockActivity.return_value = mock_activity

                await ConsumptionTrackingService._check_budget_alert(mock_db, "comp-test")

                mock_activity.create_activity.assert_called_once()
                call_kwargs = mock_activity.create_activity.call_args[1]
                assert call_kwargs["activity_type"] == "budget_alert"
                assert call_kwargs["category"] == "billing"
                assert call_kwargs["extra_data"]["total_usd"] == 150.0

    @pytest.mark.asyncio
    async def test_budget_alert_dedup_prevents_second_alert(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        now = datetime.utcnow()
        month_key = f"comp-test:{now.year}-{now.month:02d}"

        alerts = {month_key: now.isoformat()}
        with patch.object(ConsumptionTrackingService, "_budget_alerts_sent", alerts):
            mock_db.execute = AsyncMock()
            await ConsumptionTrackingService._check_budget_alert(mock_db, "comp-test")
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_budget_not_exceeded_no_alert(self, mock_db):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_result = MagicMock()
        mock_result.scalar.return_value = 50.0
        mock_db.execute.return_value = mock_result

        with patch.object(ConsumptionTrackingService, "_budget_alerts_sent", {}):
            await ConsumptionTrackingService._check_budget_alert(mock_db, "comp-test")
            assert "comp-test" not in str(ConsumptionTrackingService._budget_alerts_sent)


class TestGetMonthlyApifySpend:

    @pytest.mark.asyncio
    async def test_returns_total_from_db(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42.50
        mock_db.execute.return_value = mock_result

        total = await ConsumptionTrackingService.get_monthly_apify_spend(mock_db, "comp-1")
        assert total == 42.50

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_records(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        total = await ConsumptionTrackingService.get_monthly_apify_spend(mock_db, "comp-1")
        assert total == 0.0


class TestConsumptionReportService:

    def _make_mock_db(self, apify_calls=0, apify_success=0, apify_usd=0.0, apify_brl=0.0,
                      pearch_calls=0, pearch_success=0, pearch_credits=0):
        mock_db = AsyncMock()

        apify_row = MagicMock()
        apify_row.total_calls = apify_calls
        apify_row.successful_calls = apify_success
        apify_row.total_cost_usd = apify_usd
        apify_row.total_cost_brl = apify_brl
        apify_result = MagicMock()
        apify_result.one.return_value = apify_row

        pearch_row = MagicMock()
        pearch_row.total_calls = pearch_calls
        pearch_row.successful_calls = pearch_success
        pearch_row.total_cost_usd = 0
        pearch_row.total_cost_brl = 0
        pearch_result = MagicMock()
        pearch_result.one.return_value = pearch_row

        credits_result = MagicMock()
        credits_result.scalar.return_value = pearch_credits

        breakdown_result = MagicMock()
        breakdown_result.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[
            apify_result,
            pearch_result,
            credits_result,
            breakdown_result,
        ])
        return mock_db

    @pytest.mark.asyncio
    async def test_invoice_data_structure(self):
        from app.domains.billing.services.consumption_report_service import ConsumptionReportService

        mock_db = self._make_mock_db()
        data = await ConsumptionReportService.get_invoice_data(mock_db, "comp-1", 2026, 4)

        assert data["period"] == "2026-04"
        assert data["company_id"] == "comp-1"
        assert "apify_calls" in data
        assert "pearch_credits" in data
        assert "total_brl" in data
        assert data["total_brl"] == 0.0

    @pytest.mark.asyncio
    async def test_invoice_data_with_values(self):
        from app.domains.billing.services.consumption_report_service import ConsumptionReportService

        mock_db = self._make_mock_db(
            apify_calls=5, apify_success=4, apify_usd=0.05, apify_brl=0.275,
            pearch_calls=10, pearch_success=8, pearch_credits=80,
        )
        data = await ConsumptionReportService.get_invoice_data(mock_db, "comp-1", 2026, 12)

        assert data["period"] == "2026-12"
        assert data["apify_calls"] == 5
        assert data["apify_cost_usd"] == 0.05
        assert data["pearch_credits"] == 80
        assert data["total_brl"] > 0

    @pytest.mark.asyncio
    async def test_report_by_period_nested_structure(self):
        from app.domains.billing.services.consumption_report_service import ConsumptionReportService
        from datetime import datetime

        mock_db = self._make_mock_db(
            apify_calls=3, apify_success=2, apify_usd=0.03, apify_brl=0.165,
            pearch_calls=5, pearch_success=5, pearch_credits=10,
        )
        start = datetime(2026, 4, 1)
        end = datetime(2026, 5, 1)
        report = await ConsumptionReportService.get_report_by_period(mock_db, "comp-1", start, end)

        assert "apify" in report
        assert "pearch" in report
        assert report["apify"]["total_calls"] == 3
        assert report["pearch"]["total_calls"] == 5
        assert report["pearch"]["total_credits_consumed"] == 10


class TestPearchCreditEstimation:

    def test_basic_search_credits(self):
        from lia_models.pearch import PearchSearchRequest, SearchType
        from app.domains.sourcing.services.pearch_service import PearchService

        svc = PearchService()
        req = PearchSearchRequest(
            query="python developer",
            type=SearchType.FAST,
            limit=20,
            insights=False,
            profile_scoring=False,
            high_freshness=False,
        )
        estimate = svc.estimate_credits(req)
        assert estimate.total_per_candidate == 1
        assert estimate.total_estimated == 20

    def test_full_featured_search_credits(self):
        from lia_models.pearch import PearchSearchRequest, SearchType
        from app.domains.sourcing.services.pearch_service import PearchService

        svc = PearchService()
        req = PearchSearchRequest(
            query="senior engineer",
            type=SearchType.FAST,
            limit=10,
            insights=True,
            profile_scoring=True,
            high_freshness=True,
        )
        estimate = svc.estimate_credits(req)
        assert estimate.total_per_candidate == 5
        assert estimate.total_estimated == 50

    def test_partial_results_credits(self):
        from lia_models.pearch import PearchSearchRequest, SearchType
        from app.domains.sourcing.services.pearch_service import PearchService

        svc = PearchService()
        req = PearchSearchRequest(
            query="test",
            type=SearchType.FAST,
            limit=20,
            insights=True,
            profile_scoring=False,
            high_freshness=False,
        )
        estimate = svc.estimate_credits(req)
        actual_results = 5
        actual_credits = min(
            estimate.total_estimated,
            estimate.total_per_candidate * actual_results,
        )
        assert actual_credits == 10


class TestContactEnrichmentTracking:

    @pytest.mark.asyncio
    async def test_track_apify_uses_unattributed_when_no_company_id(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        mock_db = AsyncMock()

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService.record_apify_call", new_callable=AsyncMock) as mock_record:
            await svc._track_apify_consumption(
                db=mock_db,
                company_id=None,
                user_id="user-1",
                candidate_id=str(uuid4()),
                linkedin_url="https://linkedin.com/in/test",
                operation="enrich",
                cost_usd=0.01,
                success=True,
            )
            mock_record.assert_called_once()
            call_kwargs = mock_record.call_args[1]
            assert call_kwargs["company_id"] == "unattributed"

    @pytest.mark.asyncio
    async def test_track_apify_calls_service_when_company_id_present(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        mock_db = AsyncMock()

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService.record_apify_call", new_callable=AsyncMock) as mock_record:
            await svc._track_apify_consumption(
                db=mock_db,
                company_id="comp-1",
                user_id="user-1",
                candidate_id=str(uuid4()),
                linkedin_url="https://linkedin.com/in/test",
                operation="enrich",
                cost_usd=0.01,
                success=True,
                result_status="no_contact",
            )
            mock_record.assert_called_once()
            call_kwargs = mock_record.call_args[1]
            assert call_kwargs["company_id"] == "comp-1"
            assert call_kwargs["operation"] == "enrich"
            assert call_kwargs["result_status"] == "no_contact"
            assert call_kwargs["cost_usd"] == 0.01

    @pytest.mark.asyncio
    async def test_track_apify_handles_service_error_gracefully(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        mock_db = AsyncMock()

        with patch("app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService.record_apify_call", new_callable=AsyncMock, side_effect=Exception("DB error")):
            await svc._track_apify_consumption(
                db=mock_db,
                company_id="comp-1",
                user_id=None,
                candidate_id=None,
                linkedin_url=None,
                operation="enrich",
                cost_usd=0.01,
                success=False,
            )


class TestEnrichByLinkedinUrlTracking:

    @pytest.mark.asyncio
    async def test_enrich_by_linkedin_url_tracks_success(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        mock_scrape = AsyncMock(return_value={"email": "test@example.com"})
        svc._enrichment_svc = MagicMock()
        svc._enrichment_svc._scrape_linkedin_profile = mock_scrape

        with patch.object(svc, "_track_apify_consumption_fire_and_forget", new_callable=AsyncMock) as mock_track:
            result = await svc.enrich_by_linkedin_url("https://linkedin.com/in/test", company_id="comp-1")
            assert result["success"] is True
            assert result["email"] == "test@example.com"
            mock_track.assert_called_once()
            call_kwargs = mock_track.call_args[1]
            assert call_kwargs["company_id"] == "comp-1"
            assert call_kwargs["success"] is True
            assert call_kwargs["result_status"] == "success"

    @pytest.mark.asyncio
    async def test_enrich_by_linkedin_url_tracks_no_data(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        mock_scrape = AsyncMock(return_value=None)
        svc._enrichment_svc = MagicMock()
        svc._enrichment_svc._scrape_linkedin_profile = mock_scrape

        with patch.object(svc, "_track_apify_consumption_fire_and_forget", new_callable=AsyncMock) as mock_track:
            result = await svc.enrich_by_linkedin_url("https://linkedin.com/in/test")
            assert result["success"] is False
            mock_track.assert_called_once()
            call_kwargs = mock_track.call_args[1]
            assert call_kwargs["company_id"] is None
            assert call_kwargs["success"] is False
            assert call_kwargs["result_status"] == "no_contact"

    @pytest.mark.asyncio
    async def test_enrich_by_linkedin_url_tracks_exception(self):
        from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

        svc = ContactEnrichmentService()
        svc._enrichment_svc = MagicMock()
        svc._enrichment_svc._scrape_linkedin_profile = AsyncMock(side_effect=RuntimeError("API down"))

        with patch.object(svc, "_track_apify_consumption_fire_and_forget", new_callable=AsyncMock) as mock_track:
            result = await svc.enrich_by_linkedin_url("https://linkedin.com/in/test", company_id="comp-2")
            assert result["success"] is False
            mock_track.assert_called_once()
            call_kwargs = mock_track.call_args[1]
            assert call_kwargs["success"] is False
            assert call_kwargs["result_status"] == "fail"


class TestBudgetNotificationType:

    @pytest.mark.asyncio
    async def test_budget_alert_uses_valid_notification_type(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
        from app.services.notification_service import NotificationType

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=150.0)))

        ConsumptionTrackingService._budget_alerts_sent.clear()

        with patch("app.domains.analytics.services.activity_service.ActivityService") as mock_as, \
             patch("app.services.notification_service.NotificationService") as mock_ns:
            mock_as_instance = MagicMock()
            mock_as_instance.create_activity = AsyncMock()
            mock_as.return_value = mock_as_instance
            mock_ns_instance = MagicMock()
            mock_ns_instance.create_notification = AsyncMock()
            mock_ns.return_value = mock_ns_instance

            await ConsumptionTrackingService._check_budget_alert(
                db=mock_db,
                company_id="comp-1",
            )

            mock_ns_instance.create_notification.assert_called_once()
            call_kwargs = mock_ns_instance.create_notification.call_args[1]
            assert call_kwargs["notification_type"] == NotificationType.URGENT


class TestAiConsumptionNonUuidCompanyId:

    @pytest.mark.asyncio
    async def test_record_apify_usage_handles_unattributed(self):
        from app.domains.analytics.services.token_tracking_service import TokenTrackingService

        svc = TokenTrackingService.__new__(TokenTrackingService)

        result = await svc.record_apify_usage(
            company_id="unattributed",
            user_id=None,
            candidate_id=None,
            operation="enrich",
            cost_usd=0.01,
        )
        assert result.get("skipped") is True
        assert result.get("reason") == "non_uuid_company_id"
