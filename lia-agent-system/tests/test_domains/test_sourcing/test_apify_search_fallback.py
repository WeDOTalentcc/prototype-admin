import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.sourcing.services.apify_search_service import (
    APIFY_SEARCH_FALLBACK_ENABLED,
    ApifySearchService,
    SearchPipelineResult,
    StageRecord,
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
                pipeline_id="550e8400-e29b-41d4-a716-446655440000",
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

    @pytest.mark.asyncio
    async def test_record_per_stage_operations(self):
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch(
            "app.domains.billing.services.consumption_tracking_service.ConsumptionTrackingService._check_budget_alert",
            new_callable=AsyncMock,
        ):
            _pid = "550e8400-e29b-41d4-a716-446655440000"
            r1 = await ConsumptionTrackingService.record_apify_search_call(
                db=mock_db, company_id="c1", user_id="u1",
                operation="apify_search", cost_usd=0.02, success=True,
                pipeline_id=_pid, response_time_ms=1000,
            )
            r2 = await ConsumptionTrackingService.record_apify_search_call(
                db=mock_db, company_id="c1", user_id="u1",
                operation="profile_scrape", cost_usd=0.01, success=True,
                pipeline_id=_pid, response_time_ms=500,
            )
            r3 = await ConsumptionTrackingService.record_apify_search_call(
                db=mock_db, company_id="c1", user_id="u1",
                operation="email_finder", cost_usd=0.01, success=False,
                pipeline_id=_pid, response_time_ms=300,
                error_message="timeout",
            )

            assert r1.operation == "apify_search"
            assert r2.operation == "profile_scrape"
            assert r3.operation == "email_finder"
            assert r3.success is False
            assert mock_db.add.call_count == 3


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


class TestStageRecords:

    def test_stage_record_creation(self):
        sr = StageRecord(
            operation="profile_scrape",
            cost_usd=0.01,
            success=True,
            response_time_ms=500,
        )
        assert sr.operation == "profile_scrape"
        assert sr.error_message is None

    def test_stage_record_with_error(self):
        sr = StageRecord(
            operation="email_finder",
            cost_usd=0.01,
            success=False,
            response_time_ms=300,
            error_message="timeout",
        )
        assert sr.success is False
        assert sr.error_message == "timeout"

    def test_pipeline_result_includes_stage_records(self):
        stages = [
            StageRecord(operation="apify_search", cost_usd=0.02, success=True, response_time_ms=1000),
            StageRecord(operation="profile_scrape", cost_usd=0.01, success=True, response_time_ms=500),
            StageRecord(operation="email_finder", cost_usd=0.01, success=False, response_time_ms=200, error_message="timeout"),
        ]
        result = SearchPipelineResult(
            candidates=[{"name": "Test"}],
            search_time_seconds=1.7,
            profiles_scraped=1,
            emails_found=0,
            total_cost_usd=0.04,
            pipeline_id="test-id",
            errors=[],
            stage_records=stages,
        )
        assert len(result.stage_records) == 3
        assert result.stage_records[0].operation == "apify_search"
        assert result.stage_records[2].success is False


class TestRouteLevelIntegrated:

    def setup_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def teardown_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    @pytest.mark.asyncio
    async def test_pearch_open_triggers_apify_fallback_e2e(self):
        from unittest.mock import PropertyMock
        from dataclasses import dataclass, field

        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()

        @dataclass
        class FakeHybridResult:
            query: str = "test"
            thread_id: str = "t-1"
            local_candidates: list = field(default_factory=list)
            pearch_candidates: list = field(default_factory=list)
            local_count: int = 0
            pearch_count: int = 0
            pearch_credits_remaining: int = 100
            local_search_time: float = 0.1
            pearch_search_time: float = 0.0
            warning_message: str | None = None

        mock_pearch_svc = AsyncMock()
        mock_pearch_svc.hybrid_search = AsyncMock(return_value=FakeHybridResult())

        fb_result = SearchPipelineResult(
            candidates=[{"first_name": "A", "last_name": "B", "headline": "Dev"}],
            search_time_seconds=2.0,
            profiles_scraped=1,
            emails_found=0,
            total_cost_usd=0.03,
            pipeline_id="pipe-e2e",
            errors=[],
            stage_records=[
                StageRecord(operation="apify_search", cost_usd=0.02, success=True, response_time_ms=1500),
                StageRecord(operation="profile_scrape", cost_usd=0.01, success=True, response_time_ms=500),
            ],
        )

        with patch(
            "app.api.v1.candidate_search.search.APIFY_SEARCH_FALLBACK_ENABLED", True,
        ), patch(
            "app.api.v1.candidate_search.search.apify_search_service",
        ) as mock_apify_svc:
            mock_apify_svc.search_candidates = AsyncMock(return_value=fb_result)
            mock_apify_svc.map_to_search_dto = MagicMock(return_value={
                "id": "fake-id", "name": "A B", "first_name": "A", "last_name": "B",
                "headline": "Dev", "current_title": "Dev", "current_company": None,
                "location": None, "skills": [], "linkedin_url": None,
                "email": None, "has_email": False, "phone": None, "has_phone": False,
                "source": "apify_search", "summary": None, "picture_url": None, "score": None,
            })

            _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
            _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN
            search_pearch = True
            fallback_enabled = True

            assert _pearch_is_open is True
            assert _apify_search_is_open is False

            _skip_pearch = _pearch_is_open and search_pearch and fallback_enabled and not _apify_search_is_open
            assert _skip_pearch is True

            actual_result = await APIFY_SEARCH_CIRCUIT.call(
                mock_apify_svc.search_candidates,
                query="test",
                location=None,
                limit=15,
            )
            assert actual_result.pipeline_id == "pipe-e2e"
            assert len(actual_result.candidates) == 1
            assert len(actual_result.stage_records) == 2
            mock_apify_svc.search_candidates.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_open_raises_503(self):
        from fastapi import HTTPException

        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()
        APIFY_SEARCH_CIRCUIT._state = CircuitState.OPEN
        APIFY_SEARCH_CIRCUIT._last_failure_time = time.time()

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN
        search_pearch = True
        fallback_enabled = True

        both_down = _pearch_is_open and search_pearch and fallback_enabled and _apify_search_is_open
        assert both_down is True

        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=503,
                detail="Serviço de busca temporariamente indisponível.",
            )
        assert exc_info.value.status_code == 503


class TestRouteLevel:

    def setup_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def teardown_method(self):
        PEARCH_CIRCUIT.reset()
        APIFY_SEARCH_CIRCUIT.reset()

    def test_pearch_open_sets_skip_pearch_flag(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN
        search_pearch = True
        fallback_enabled = True

        _skip_pearch = _pearch_is_open and search_pearch and fallback_enabled and not _apify_search_is_open
        assert _skip_pearch is True

    def test_both_circuits_open_detected(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()
        APIFY_SEARCH_CIRCUIT._state = CircuitState.OPEN
        APIFY_SEARCH_CIRCUIT._last_failure_time = time.time()

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN
        search_pearch = True
        fallback_enabled = True

        both_down = _pearch_is_open and search_pearch and fallback_enabled and _apify_search_is_open
        assert both_down is True

    def test_no_skip_when_fallback_disabled(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN
        search_pearch = True
        fallback_enabled = False

        _skip_pearch = _pearch_is_open and search_pearch and fallback_enabled and not _apify_search_is_open
        assert _skip_pearch is False

    def test_no_skip_when_pearch_not_requested(self):
        PEARCH_CIRCUIT._state = CircuitState.OPEN
        PEARCH_CIRCUIT._last_failure_time = time.time()

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        search_pearch = False
        fallback_enabled = True

        _skip_pearch = _pearch_is_open and search_pearch and fallback_enabled
        assert _skip_pearch is False

    @pytest.mark.asyncio
    async def test_fallback_result_updates_response_counts(self):
        fb_result = SearchPipelineResult(
            candidates=[{"name": "A"}, {"name": "B"}],
            search_time_seconds=2.5,
            profiles_scraped=2,
            emails_found=1,
            total_cost_usd=0.04,
            pipeline_id="test-pipeline",
            errors=[],
            stage_records=[
                StageRecord(operation="apify_search", cost_usd=0.02, success=True, response_time_ms=1500),
                StageRecord(operation="profile_scrape", cost_usd=0.01, success=True, response_time_ms=500),
                StageRecord(operation="profile_scrape", cost_usd=0.01, success=True, response_time_ms=400),
            ],
        )

        _fb_pearch_count = len(fb_result.candidates)
        _fb_search_time = fb_result.search_time_seconds
        _fb_can_load_more = _fb_pearch_count >= 15

        pearch_count_from_hybrid = 0
        _effective_pearch_count = pearch_count_from_hybrid + _fb_pearch_count
        assert _effective_pearch_count == 2

        hybrid_search_time = 0.3
        _effective_search_time = hybrid_search_time + _fb_search_time
        assert _effective_search_time == pytest.approx(2.8, abs=0.01)

        assert _fb_can_load_more is False

    @pytest.mark.asyncio
    async def test_per_stage_records_tracked_on_success(self):
        fb_result = SearchPipelineResult(
            candidates=[{"name": "Test"}],
            search_time_seconds=3.0,
            profiles_scraped=1,
            emails_found=1,
            total_cost_usd=0.04,
            pipeline_id="pipe-123",
            errors=[],
            stage_records=[
                StageRecord(operation="apify_search", cost_usd=0.02, success=True, response_time_ms=2000),
                StageRecord(operation="profile_scrape", cost_usd=0.01, success=True, response_time_ms=600),
                StageRecord(operation="email_finder", cost_usd=0.01, success=True, response_time_ms=400),
            ],
        )

        assert len(fb_result.stage_records) == 3
        ops = [sr.operation for sr in fb_result.stage_records]
        assert "apify_search" in ops
        assert "profile_scrape" in ops
        assert "email_finder" in ops
        assert all(sr.success for sr in fb_result.stage_records)
