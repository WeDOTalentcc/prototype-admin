import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.sourcing.services.apify_search_service import (
    APIFY_SEARCH_FALLBACK_ENABLED,
    ApifySearchService,
    SearchPipelineResult,
)
from app.shared.resilience.circuit_breaker import (
    APIFY_SEARCH_CIRCUIT,
    CircuitBreakerError,
    CircuitState,
    PEARCH_CIRCUIT,
)


class TestApifySearchCircuitBreaker:

    def setup_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def teardown_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def test_apify_search_circuit_exists(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "apify_search" in ALL_CIRCUITS
        assert ALL_CIRCUITS["apify_search"] is APIFY_SEARCH_CIRCUIT

    def test_apify_search_circuit_config(self):
        assert APIFY_SEARCH_CIRCUIT.config.failure_threshold == 3
        assert APIFY_SEARCH_CIRCUIT.config.recovery_timeout == 120.0
        assert APIFY_SEARCH_CIRCUIT.config.timeout == 300.0

    def test_circuit_separate_from_enrichment(self):
        from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT
        assert APIFY_SEARCH_CIRCUIT is not APIFY_CIRCUIT
        assert APIFY_SEARCH_CIRCUIT.name == "apify_search"
        assert APIFY_CIRCUIT.name == "apify"

    def test_slo_defined(self):
        from app.shared.resilience.circuit_breaker import CIRCUIT_BREAKER_SLOS
        slo = CIRCUIT_BREAKER_SLOS.get("apify_search")
        assert slo is not None
        assert slo["tier"] == "low"
        assert slo["availability_target"] == 0.95

    def test_degraded_response_defined(self):
        from app.shared.resilience.circuit_breaker import get_degraded_response
        msg = get_degraded_response("apify_search")
        assert "Apify" in msg
        assert "indisponível" in msg


class TestFallbackDecision:

    def setup_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def teardown_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def test_fallback_not_triggered_when_pearch_healthy(self):
        assert PEARCH_CIRCUIT.state != CircuitState.OPEN
        should_fallback = (
            PEARCH_CIRCUIT.state == CircuitState.OPEN
            and APIFY_SEARCH_CIRCUIT.state != CircuitState.OPEN
        )
        assert should_fallback is False

    def test_fallback_triggered_when_pearch_open(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()

        should_fallback = (
            PEARCH_CIRCUIT.state == CircuitState.OPEN
            and APIFY_SEARCH_CIRCUIT.state != CircuitState.OPEN
        )
        assert should_fallback is True

    def test_fallback_blocked_when_both_open(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()
        APIFY_SEARCH_CIRCUIT._state = CircuitState.OPEN
        APIFY_SEARCH_CIRCUIT._last_failure_time = time.time()

        should_fallback = (
            PEARCH_CIRCUIT.state == CircuitState.OPEN
            and APIFY_SEARCH_CIRCUIT.state != CircuitState.OPEN
        )
        assert should_fallback is False

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        for _ in range(3):
            await APIFY_SEARCH_CIRCUIT.record_failure()

        assert APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self):
        APIFY_SEARCH_CIRCUIT._state = CircuitState.OPEN
        APIFY_SEARCH_CIRCUIT._last_failure_time = time.time()

        with pytest.raises(CircuitBreakerError):
            await APIFY_SEARCH_CIRCUIT.call(AsyncMock(return_value="ok"))


class TestConsumptionTracking:

    @pytest.mark.asyncio
    async def test_record_apify_search_call(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            record = await ConsumptionTrackingService.record_apify_search_call(
                db=mock_db,
                company_id="test-company",
                user_id="test-user",
                operation="apify_search",
                cost_usd=0.05,
                success=True,
                pipeline_id="test-pipeline-id",
                response_time_ms=5000,
            )

            assert record.provider == "apify"
            assert record.operation == "apify_search"
            assert record.cost_usd == 0.05
            assert record.success is True
            mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_failed_search_call(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            record = await ConsumptionTrackingService.record_apify_search_call(
                db=mock_db,
                company_id="test-company",
                user_id=None,
                operation="apify_search",
                cost_usd=0.02,
                success=False,
                error_message="Search actor timeout",
            )

            assert record.success is False
            assert record.result_status == "fail"
            assert record.error_message == "Search actor timeout"


class TestOperationEnums:

    def test_new_operations_exist(self):
        from lia_models.external_api_consumption import ExternalApiOperation

        assert ExternalApiOperation.APIFY_SEARCH == "apify_search"
        assert ExternalApiOperation.PROFILE_SCRAPE == "profile_scrape"
        assert ExternalApiOperation.EMAIL_FINDER == "email_finder"

    def test_existing_operations_unchanged(self):
        from lia_models.external_api_consumption import ExternalApiOperation

        assert ExternalApiOperation.ENRICH == "enrich"
        assert ExternalApiOperation.SEARCH == "search"
        assert ExternalApiOperation.REVEAL_EMAIL == "reveal_email"
        assert ExternalApiOperation.REVEAL_PHONE == "reveal_phone"
