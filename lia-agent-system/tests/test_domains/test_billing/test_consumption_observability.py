import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.billing.services.consumption_tracking_service import (
    PRICING_TABLE,
    ConsumptionTrackingService,
)
from app.domains.billing.services.consumption_logger import (
    ConsumptionAuditLogger,
    CONSUMPTION_LOG_RETENTION_DAYS,
)
from lia_models.external_api_consumption import (
    ExternalApiConsumption,
    ExternalApiOperation,
    ExternalApiProvider,
)


class TestModelExtensions:

    def test_llm_provider_exists(self):
        assert ExternalApiProvider.LLM == "llm"
        assert ExternalApiProvider.APIFY == "apify"
        assert ExternalApiProvider.PEARCH == "pearch"

    def test_llm_inference_operation_exists(self):
        assert ExternalApiOperation.LLM_INFERENCE == "llm_inference"

    def test_model_has_new_fields(self):
        record = ExternalApiConsumption(
            company_id="test",
            provider="llm",
            operation="llm_inference",
            pipeline_id=None,
            search_session_id="sess-123",
            actor_id="curious_coder/linkedin-search",
            tokens_input=1000,
            tokens_output=500,
            model_name="claude-3-sonnet",
            cost_usd=0.01,
            cost_brl=0.055,
            exchange_rate=5.50,
            success=True,
        )
        assert record.tokens_input == 1000
        assert record.tokens_output == 500
        assert record.model_name == "claude-3-sonnet"
        assert record.actor_id == "curious_coder/linkedin-search"
        assert record.search_session_id == "sess-123"

    def test_to_dict_includes_new_fields(self):
        record = ExternalApiConsumption(
            company_id="test",
            provider="llm",
            operation="llm_inference",
            model_name="gpt-4o",
            tokens_input=500,
            tokens_output=200,
            cost_usd=0.005,
            cost_brl=0.0275,
            exchange_rate=5.50,
            success=True,
        )
        d = record.to_dict()
        assert "tokens_input" in d
        assert "tokens_output" in d
        assert "model_name" in d
        assert "pipeline_id" in d
        assert "search_session_id" in d
        assert "actor_id" in d


class TestLLMCostCalculation:

    def test_calculate_claude_sonnet_cost(self):
        cost = ConsumptionTrackingService.calculate_llm_cost(
            "claude-3-sonnet", 1000, 500
        )
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert abs(cost - expected) < 0.0001

    def test_calculate_gpt4o_mini_cost(self):
        cost = ConsumptionTrackingService.calculate_llm_cost(
            "gpt-4o-mini", 2000, 1000
        )
        expected = (2000 / 1000) * 0.00015 + (1000 / 1000) * 0.0006
        assert abs(cost - expected) < 0.0001

    def test_unknown_model_uses_default(self):
        cost = ConsumptionTrackingService.calculate_llm_cost(
            "unknown-model-v99", 1000, 500
        )
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert abs(cost - expected) < 0.0001

    def test_zero_tokens(self):
        cost = ConsumptionTrackingService.calculate_llm_cost("claude-3-sonnet", 0, 0)
        assert cost == 0.0


class TestRecordLLMCall:

    @pytest.mark.asyncio
    async def test_record_llm_call_success(self):
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            record = await ConsumptionTrackingService.record_llm_call(
                db=mock_db,
                company_id="company-1",
                user_id="user-1",
                model_name="claude-3-sonnet",
                tokens_input=1000,
                tokens_output=500,
                response_time_ms=2500,
            )

            assert record.provider == "llm"
            assert record.operation == "llm_inference"
            assert record.model_name == "claude-3-sonnet"
            assert record.tokens_input == 1000
            assert record.tokens_output == 500
            assert record.success is True
            assert record.cost_usd > 0
            mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_llm_call_with_explicit_cost(self):
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            record = await ConsumptionTrackingService.record_llm_call(
                db=mock_db,
                company_id="company-1",
                user_id="user-1",
                model_name="custom-model",
                tokens_input=500,
                tokens_output=200,
                cost_usd=0.05,
            )

            assert record.cost_usd == 0.05

    @pytest.mark.asyncio
    async def test_record_llm_call_failure(self):
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            record = await ConsumptionTrackingService.record_llm_call(
                db=mock_db,
                company_id="company-1",
                user_id=None,
                model_name="gpt-4o",
                tokens_input=100,
                tokens_output=0,
                success=False,
                error_message="Rate limit exceeded",
            )

            assert record.success is False
            assert record.result_status == "fail"
            assert record.error_message == "Rate limit exceeded"


class TestRecordPipelineCall:

    @pytest.mark.asyncio
    async def test_record_pipeline_stages(self):
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        stages = [
            {"operation": "apify_search", "cost_usd": 0.02, "success": True, "response_time_ms": 2000},
            {"operation": "profile_scrape", "cost_usd": 0.01, "success": True, "response_time_ms": 500},
            {"operation": "email_finder", "cost_usd": 0.01, "success": False, "response_time_ms": 300, "error_message": "timeout"},
        ]

        records = await ConsumptionTrackingService.record_pipeline_call(
            db=mock_db,
            company_id="company-1",
            user_id="user-1",
            pipeline_id="550e8400-e29b-41d4-a716-446655440000",
            stages=stages,
            total_cost_usd=0.04,
        )

        assert len(records) == 3
        assert mock_db.add.call_count == 3
        assert records[0].operation == "apify_search"
        assert records[2].success is False


class TestPricingTable:

    def test_apify_prices_exist(self):
        assert PRICING_TABLE["apify"]["enrich"] == 0.01
        assert PRICING_TABLE["apify"]["apify_search"] == 0.02
        assert PRICING_TABLE["apify"]["profile_scrape"] == 0.01
        assert PRICING_TABLE["apify"]["email_finder"] == 0.01

    def test_pearch_prices_exist(self):
        assert PRICING_TABLE["pearch"]["search"] == 1

    def test_llm_prices_exist(self):
        assert "claude-3-sonnet" in PRICING_TABLE["llm"]
        assert "gpt-4o" in PRICING_TABLE["llm"]
        assert "gemini-1.5-pro" in PRICING_TABLE["llm"]

    def test_get_operation_price(self):
        assert ConsumptionTrackingService.get_operation_price("apify", "enrich") == 0.01
        assert ConsumptionTrackingService.get_operation_price("unknown", "op") is None


class TestTenantBudgets:

    def setup_method(self):
        ConsumptionTrackingService._tenant_budgets.clear()

    def test_set_and_get_tenant_budget(self):
        ConsumptionTrackingService.set_tenant_budget("company-1", "apify", 200.0)
        assert ConsumptionTrackingService.get_tenant_budget("company-1", "apify") == 200.0

    def test_default_budget_when_no_tenant_config(self):
        budget = ConsumptionTrackingService.get_tenant_budget("no-config-company", "apify")
        assert budget > 0

    def test_multiple_categories(self):
        ConsumptionTrackingService.set_tenant_budget("company-2", "apify", 50.0)
        ConsumptionTrackingService.set_tenant_budget("company-2", "llm", 300.0)
        assert ConsumptionTrackingService.get_tenant_budget("company-2", "apify") == 50.0
        assert ConsumptionTrackingService.get_tenant_budget("company-2", "llm") == 300.0


class TestConsumptionAuditLogger:

    def test_log_operation_returns_record(self):
        record = ConsumptionAuditLogger.log_operation(
            company_id="company-1",
            user_id="user-1",
            operation="enrich",
            provider="apify",
            cost_usd=0.01,
            success=True,
            duration_ms=500,
        )
        assert record["event"] == "consumption_operation"
        assert record["company_id"] == "company-1"
        assert record["cost_usd"] == 0.01
        assert record["success"] is True
        assert record["retention_days"] == CONSUMPTION_LOG_RETENTION_DAYS
        assert "timestamp" in record

    def test_log_operation_with_llm_fields(self):
        record = ConsumptionAuditLogger.log_operation(
            company_id="company-1",
            user_id="user-1",
            operation="llm_inference",
            provider="llm",
            cost_usd=0.005,
            success=True,
            model_name="claude-3-sonnet",
            tokens_input=1000,
            tokens_output=500,
        )
        assert record["model_name"] == "claude-3-sonnet"
        assert record["tokens_input"] == 1000
        assert record["tokens_output"] == 500

    def test_log_budget_alert(self):
        record = ConsumptionAuditLogger.log_budget_alert(
            company_id="company-1",
            category="apify",
            current_spend_usd=105.0,
            budget_usd=100.0,
            usage_percentage=105.0,
        )
        assert record["event"] == "budget_alert"
        assert record["category"] == "apify"
        assert record["usage_percentage"] == 105.0

    def test_log_invoice_generated(self):
        record = ConsumptionAuditLogger.log_invoice_generated(
            company_id="company-1",
            year=2026,
            month=4,
            total_usd=150.0,
            total_brl=825.0,
            line_count=50,
        )
        assert record["event"] == "invoice_generated"
        assert record["period"] == "2026-04"
        assert record["line_count"] == 50

    def test_retention_days_default(self):
        assert CONSUMPTION_LOG_RETENTION_DAYS == 730


class TestBudgetAlertPerCategory:

    def setup_method(self):
        ConsumptionTrackingService._budget_alerts_sent.clear()
        ConsumptionTrackingService._tenant_budgets.clear()

    @pytest.mark.asyncio
    async def test_budget_alert_checks_correct_category(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 150.0
        mock_db.execute = AsyncMock(return_value=mock_result)

        ConsumptionTrackingService.set_tenant_budget("company-1", "apify", 100.0)

        await ConsumptionTrackingService._check_budget_alert(mock_db, "company-1", "apify")

        now = datetime.utcnow()
        month_key = f"company-1:apify:{now.year}-{now.month:02d}"
        assert month_key in ConsumptionTrackingService._budget_alerts_sent

    @pytest.mark.asyncio
    async def test_separate_alerts_per_category(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 600.0
        mock_db.execute = AsyncMock(return_value=mock_result)

        await ConsumptionTrackingService._check_budget_alert(mock_db, "company-1", "llm")

        now = datetime.utcnow()
        llm_key = f"company-1:llm:{now.year}-{now.month:02d}"
        apify_key = f"company-1:apify:{now.year}-{now.month:02d}"
        assert llm_key in ConsumptionTrackingService._budget_alerts_sent
        assert apify_key not in ConsumptionTrackingService._budget_alerts_sent
