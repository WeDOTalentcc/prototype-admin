"""
Testes unitários para AgentQualityEvaluator — Sprint J1.

Cobertura:
- sampling rate: 0.5 > RATE → retorna None
- sampling rate: 0.01 < RATE → chama evaluate_response
- shadow mode: falha silenciosa
- overall_score = média das métricas
- 5 métricas presentes no resultado
- _persist chamado com db
- _persist não chamado sem db
- _judge fallback 0.5 em falha LLM
- _judge clamp 0.0–1.0
- trend: insufficient_data < 4 amostras
- trend: improving / degrading / stable
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_evaluator():
    from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
    return AgentQualityEvaluator()


class TestSamplingRate:

    @pytest.mark.asyncio
    async def test_skipped_when_random_above_rate(self):
        svc = _make_evaluator()
        with patch("random.random", return_value=0.5):
            result = await svc.evaluate_if_sampled(
                agent_id="wizard", user_message="m", agent_response="r",
                context={}, company_id="c1",
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluated_when_sampled(self):
        svc = _make_evaluator()
        from app.domains.ai.services.agent_quality_evaluator import EvaluationResult
        with patch("random.random", return_value=0.01):
            with patch.object(svc, "evaluate_response", new_callable=AsyncMock) as m:
                m.return_value = EvaluationResult(
                    agent_id="wizard", company_id="c1",
                    session_id=None, scores={}, overall_score=0.8
                )
                result = await svc.evaluate_if_sampled(
                    agent_id="wizard", user_message="m", agent_response="r",
                    context={}, company_id="c1",
                )
        assert result is not None

    @pytest.mark.asyncio
    async def test_shadow_mode_exception_ignored(self):
        svc = _make_evaluator()
        with patch("random.random", return_value=0.01):
            with patch.object(svc, "evaluate_response", side_effect=RuntimeError("fail")):
                result = await svc.evaluate_if_sampled(
                    agent_id="wizard", user_message="m", agent_response="r",
                    context={}, company_id="c1",
                )
        assert result is None


class TestEvaluateResponse:

    @pytest.mark.asyncio
    async def test_overall_is_average(self):
        svc = _make_evaluator()
        with patch.object(svc, "_judge", return_value=0.8):
            with patch.object(svc, "_persist", new_callable=AsyncMock):
                with patch.object(svc, "_send_to_langsmith", new_callable=AsyncMock):
                    r = await svc.evaluate_response(
                        agent_id="pipeline", user_message="m", agent_response="r",
                        context={}, company_id="c1",
                    )
        assert r.overall_score == pytest.approx(0.8, abs=0.01)

    @pytest.mark.asyncio
    async def test_five_metrics_present(self):
        from app.domains.ai.services.agent_quality_evaluator import EVAL_METRICS
        svc = _make_evaluator()
        with patch.object(svc, "_judge", return_value=0.7):
            with patch.object(svc, "_persist", new_callable=AsyncMock):
                with patch.object(svc, "_send_to_langsmith", new_callable=AsyncMock):
                    r = await svc.evaluate_response(
                        agent_id="sourcing", user_message="m", agent_response="r",
                        context={}, company_id="c1",
                    )
        for metric in EVAL_METRICS:
            assert metric in r.scores

    @pytest.mark.asyncio
    async def test_persist_called_with_db(self):
        svc = _make_evaluator()
        db = AsyncMock()
        with patch.object(svc, "_judge", return_value=0.9):
            with patch.object(svc, "_persist", new_callable=AsyncMock) as mp:
                with patch.object(svc, "_send_to_langsmith", new_callable=AsyncMock):
                    await svc.evaluate_response(
                        agent_id="wizard", user_message="m", agent_response="r",
                        context={}, company_id="c1", db=db,
                    )
        mp.assert_called_once()
        assert mp.call_args[0][1] == db

    @pytest.mark.asyncio
    async def test_persist_not_called_without_db(self):
        svc = _make_evaluator()
        with patch.object(svc, "_judge", return_value=0.5):
            with patch.object(svc, "_persist", new_callable=AsyncMock) as mp:
                with patch.object(svc, "_send_to_langsmith", new_callable=AsyncMock):
                    await svc.evaluate_response(
                        agent_id="wizard", user_message="m", agent_response="r",
                        context={}, company_id="c1", db=None,
                    )
        mp.assert_not_called()


class TestJudge:

    @pytest.mark.asyncio
    async def test_fallback_on_import_error(self):
        svc = _make_evaluator()
        with patch("anthropic.AsyncAnthropic", side_effect=ImportError):
            score = await svc._judge("q", "u", "a")
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_clamp_above_one(self):
        svc = _make_evaluator()
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[MagicMock(text="1.5")])
        )
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            score = await svc._judge("q", "u", "a")
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_valid_score_returned(self):
        svc = _make_evaluator()
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[MagicMock(text="0.75")])
        )
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            score = await svc._judge("q", "u", "a")
        assert score == pytest.approx(0.75)


class TestTrend:

    def _e(self, score):
        e = MagicMock()
        e.overall_score = score
        return e

    def test_insufficient_data(self):
        from app.api.v1.agent_quality import _classify_trend
        assert _classify_trend([self._e(0.8)] * 3) == "insufficient_data"

    def test_improving(self):
        from app.api.v1.agent_quality import _classify_trend
        evals = [self._e(0.5), self._e(0.5), self._e(0.9), self._e(0.9)]
        assert _classify_trend(evals) == "improving"

    def test_degrading(self):
        from app.api.v1.agent_quality import _classify_trend
        evals = [self._e(0.9), self._e(0.9), self._e(0.5), self._e(0.5)]
        assert _classify_trend(evals) == "degrading"

    def test_stable(self):
        from app.api.v1.agent_quality import _classify_trend
        evals = [self._e(0.8), self._e(0.8), self._e(0.82), self._e(0.81)]
        assert _classify_trend(evals) == "stable"
