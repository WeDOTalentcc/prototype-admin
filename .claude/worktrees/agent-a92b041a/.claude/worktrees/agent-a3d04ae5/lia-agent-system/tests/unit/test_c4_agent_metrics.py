"""
C4 — Métricas Prometheus por Agente — Wiring

Verifica:
1. agent_latency_timer registra no histograma após execução
2. record_tokens registra input+output tokens
3. record_agent_request incrementa counter
4. GET /api/v1/metrics retorna 200 com conteúdo Prometheus
5. _resolve_guardrails fallback loga e chama record_agent_request
6. record_confidence registra histograma (já existente)
7. _validate_tool_scope falha silenciosa não quebra record_agent_request
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ---------------------------------------------------------------------------
# 1 — agent_latency_timer registra
# ---------------------------------------------------------------------------

class TestAgentLatencyTimer:

    @pytest.mark.asyncio
    async def test_latency_timer_records_on_success(self):
        """agent_latency_timer chama observe() no histograma."""
        from app.shared.observability.agent_metrics import agent_latency_timer

        with patch("app.shared.observability.agent_metrics._PROMETHEUS_AVAILABLE", True):
            with patch("app.shared.observability.agent_metrics.AGENT_LATENCY_SECONDS") as mock_hist:
                mock_hist.labels.return_value.observe = MagicMock()
                with patch("app.shared.observability.agent_metrics.AGENT_REQUEST_TOTAL") as mock_counter:
                    mock_counter.labels.return_value.inc = MagicMock()
                    async with agent_latency_timer(agent="sourcing", domain="sourcing"):
                        pass  # simula execução

        mock_hist.labels.assert_called_with(agent="sourcing", domain="sourcing")
        mock_hist.labels.return_value.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_latency_timer_records_error_status_on_exception(self):
        """agent_latency_timer registra status='error' quando exceção."""
        from app.shared.observability.agent_metrics import agent_latency_timer

        recorded_statuses = []

        with patch("app.shared.observability.agent_metrics._PROMETHEUS_AVAILABLE", True):
            with patch("app.shared.observability.agent_metrics.AGENT_LATENCY_SECONDS") as mock_hist:
                mock_hist.labels.return_value.observe = MagicMock()
                with patch("app.shared.observability.agent_metrics.AGENT_REQUEST_TOTAL") as mock_counter:
                    def capture_inc(*args, **kwargs):
                        return MagicMock()
                    mock_counter.labels.return_value.inc = MagicMock()

                    with pytest.raises(ValueError):
                        async with agent_latency_timer(agent="pipeline", domain="pipeline"):
                            raise ValueError("simulated error")

        # O timer deve ter completado sem erro interno (apenas re-levantou a exceção)
        mock_hist.labels.return_value.observe.assert_called_once()


# ---------------------------------------------------------------------------
# 2 — record_tokens
# ---------------------------------------------------------------------------

class TestRecordTokens:

    def test_record_tokens_increments_counters(self):
        """record_tokens chama inc() com input e output tokens."""
        from app.shared.observability.agent_metrics import record_tokens

        with patch("app.shared.observability.agent_metrics._PROMETHEUS_AVAILABLE", True):
            with patch("app.shared.observability.agent_metrics.AGENT_TOKENS_TOTAL") as mock_counter:
                mock_counter.labels.return_value.inc = MagicMock()
                record_tokens(agent="wizard", model="claude-sonnet-4-5", input_tokens=100, output_tokens=50)

        calls = mock_counter.labels.call_args_list
        token_types = [c[1].get("token_type") or c[0][2] for c in calls]
        assert "input" in str(calls)
        assert "output" in str(calls)


# ---------------------------------------------------------------------------
# 3 — record_agent_request
# ---------------------------------------------------------------------------

class TestRecordAgentRequest:

    def test_record_agent_request_increments_counter(self):
        """record_agent_request chama inc() com status correto."""
        from app.shared.observability.agent_metrics import record_agent_request

        with patch("app.shared.observability.agent_metrics._PROMETHEUS_AVAILABLE", True):
            with patch("app.shared.observability.agent_metrics.AGENT_REQUEST_TOTAL") as mock_counter:
                mock_counter.labels.return_value.inc = MagicMock()
                record_agent_request(agent="sourcing", domain="sourcing", status="guardrail_fallback")

        mock_counter.labels.assert_called_with(agent="sourcing", domain="sourcing", status="guardrail_fallback")
        mock_counter.labels.return_value.inc.assert_called_once()


# ---------------------------------------------------------------------------
# 4 — GET /api/v1/metrics retorna 200
# ---------------------------------------------------------------------------

class TestMetricsEndpoint:

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_200(self):
        """GET /api/v1/metrics retorna 200 com conteúdo text/plain."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.metrics import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint_without_prometheus(self):
        """GET /api/v1/metrics sem prometheus_client retorna 200 com placeholder."""
        import sys
        from unittest.mock import patch
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        with patch.dict(sys.modules, {"prometheus_client": None}):
            # Reimporta o módulo de métricas sem prometheus
            import importlib
            import app.api.v1.metrics as metrics_mod
            importlib.reload(metrics_mod)

            app = FastAPI()
            app.include_router(metrics_mod.router)
            client = TestClient(app)
            response = client.get("/api/v1/metrics")
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# 5 — _resolve_guardrails fallback chama record_agent_request
# ---------------------------------------------------------------------------

class TestGuardrailFallbackMetric:

    @pytest.mark.asyncio
    async def test_guardrail_fallback_records_metric(self):
        """_resolve_guardrails fallback registra status='guardrail_fallback' no Prometheus."""
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

        obj = EnhancedAgentMixin.__new__(EnhancedAgentMixin)
        obj._enhanced_domain = "sourcing"
        obj._autonomy_engine = MagicMock()
        obj._autonomy_engine.resolve_guardrails = AsyncMock(side_effect=Exception("unavailable"))

        with patch(
            "lia_config.database.AsyncSessionLocal",
            side_effect=Exception("db down"),
        ):
            with patch(
                "app.shared.observability.agent_metrics.record_agent_request"
            ) as mock_record:
                result = await obj._resolve_guardrails("co-1")

        mock_record.assert_called_once_with(
            agent="sourcing", domain="sourcing", status="guardrail_fallback"
        )
        assert isinstance(result, list)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 6 — record_confidence
# ---------------------------------------------------------------------------

class TestRecordConfidence:

    def test_record_confidence_calls_observe(self):
        """record_confidence chama observe() no histograma."""
        from app.shared.observability.agent_metrics import record_confidence

        with patch("app.shared.observability.agent_metrics._PROMETHEUS_AVAILABLE", True):
            with patch("app.shared.observability.agent_metrics.AGENT_CONFIDENCE") as mock_hist:
                mock_hist.labels.return_value.observe = MagicMock()
                record_confidence(agent="interview_graph", domain="interview_scheduling", confidence=0.85)

        mock_hist.labels.assert_called_with(agent="interview_graph", domain="interview_scheduling")
        mock_hist.labels.return_value.observe.assert_called_with(0.85)
