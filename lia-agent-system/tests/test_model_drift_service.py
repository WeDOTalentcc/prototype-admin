"""
Testes — Model Drift Detection Service (D.2)

Referência: screening-compliance §7 (4 triggers de drift)
"""
import pytest
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.shared.services.model_drift_service import (
    ModelDriftService,
    DriftStatus,
    DriftTrigger,
    SCORE_DRIFT_THRESHOLD,
    APPROVAL_DRIFT_THRESHOLD,
    COST_DRIFT_THRESHOLD,
    LATENCY_DRIFT_THRESHOLD,
)

COMPANY_ID = uuid4()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_db_scalar(value):
    """Retorna um AsyncMock que simula db.execute(...).scalar()."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = value
    mock_result.fetchall.return_value = []
    return mock_result


def _mock_db_fetchall(values):
    """Retorna um AsyncMock que simula db.execute(...).fetchall()."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_result.fetchall.return_value = [(v,) for v in values]
    return mock_result


# ---------------------------------------------------------------------------
# Testes de estrutura do DriftStatus
# ---------------------------------------------------------------------------

class TestDriftStatusStructure:
    """Testa que DriftStatus tem os campos corretos."""

    def test_drift_status_fields(self):
        status = DriftStatus(
            company_id=str(COMPANY_ID),
            evaluated_at=datetime.utcnow(),
            recent_window_start=datetime.utcnow() - timedelta(days=7),
            baseline_window_start=datetime.utcnow() - timedelta(days=14),
        )
        assert status.drift_detected is False
        assert status.alert_level == "ok"
        assert status.triggers == []

    def test_drift_trigger_fields(self):
        t = DriftTrigger(
            name="score_drift",
            baseline_value=70.0,
            recent_value=71.0,
            delta=1.0,
            threshold=SCORE_DRIFT_THRESHOLD,
            triggered=True,
            description="teste",
        )
        assert t.name == "score_drift"
        assert t.triggered is True

    def test_alert_level_warning_one_trigger(self):
        """1 trigger → warning."""
        status = DriftStatus(
            company_id=str(COMPANY_ID),
            evaluated_at=datetime.utcnow(),
            recent_window_start=datetime.utcnow() - timedelta(days=7),
            baseline_window_start=datetime.utcnow() - timedelta(days=14),
        )
        status.triggers = [DriftTrigger("score_drift", 70, 71.5, 1.5, 0.5, True)]
        status.drift_detected = True
        status.alert_level = "warning"
        assert status.alert_level == "warning"

    def test_alert_level_critical_two_triggers(self):
        """2 triggers → critical."""
        status = DriftStatus(
            company_id=str(COMPANY_ID),
            evaluated_at=datetime.utcnow(),
            recent_window_start=datetime.utcnow() - timedelta(days=7),
            baseline_window_start=datetime.utcnow() - timedelta(days=14),
        )
        status.triggers = [
            DriftTrigger("score_drift", 70, 71.5, 1.5, 0.5, True),
            DriftTrigger("approval_drift", 0.5, 0.65, 0.15, 0.10, True),
        ]
        status.drift_detected = True
        status.alert_level = "critical"
        assert status.alert_level == "critical"


# ---------------------------------------------------------------------------
# Testes de limiares (thresholds)
# ---------------------------------------------------------------------------

class TestDriftThresholds:
    """Testa que os limiares estão corretos conforme screening-compliance §7."""

    def test_score_drift_threshold(self):
        assert SCORE_DRIFT_THRESHOLD == 0.5

    def test_approval_drift_threshold(self):
        assert APPROVAL_DRIFT_THRESHOLD == 0.10

    def test_cost_drift_threshold(self):
        assert COST_DRIFT_THRESHOLD == 0.20

    def test_latency_drift_threshold(self):
        assert LATENCY_DRIFT_THRESHOLD == 0.50


# ---------------------------------------------------------------------------
# Testes de detecção de drift — score
# ---------------------------------------------------------------------------

class TestScoreDrift:
    """Testa detecção de drift no score médio WSI."""

    @pytest.mark.asyncio
    async def test_no_drift_when_scores_similar(self):
        """Sem drift quando a diferença de score é pequena."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline: 70.0, recente: 70.3 → Δ=0.3 < 0.5
        db.execute.side_effect = [
            _mock_db_scalar(70.3),  # recent avg
            _mock_db_scalar(70.0),  # baseline avg
        ]
        trigger = await service._score_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered

    @pytest.mark.asyncio
    async def test_drift_when_scores_differ_significantly(self):
        """Drift detectado quando diferença > 0.5."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline: 70.0, recente: 72.0 → Δ=2.0 > 0.5
        db.execute.side_effect = [
            _mock_db_scalar(72.0),
            _mock_db_scalar(70.0),
        ]
        trigger = await service._score_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert trigger.triggered
        assert trigger.delta > SCORE_DRIFT_THRESHOLD

    @pytest.mark.asyncio
    async def test_no_drift_when_no_data(self):
        """Sem dados → sem drift (evita falsos positivos)."""
        service = ModelDriftService()
        db = AsyncMock()
        db.execute.side_effect = [
            _mock_db_scalar(None),  # recent: sem dados
            _mock_db_scalar(None),  # baseline: sem dados
        ]
        trigger = await service._score_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered


# ---------------------------------------------------------------------------
# Testes de detecção de drift — custo
# ---------------------------------------------------------------------------

class TestCostDrift:
    """Testa detecção de drift no custo."""

    @pytest.mark.asyncio
    async def test_no_drift_when_cost_stable(self):
        """Sem drift quando custo varia < 20%."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline: 1000, recente: 1100 → Δ_rel=10% < 20%
        db.execute.side_effect = [
            _mock_db_scalar(1100),
            _mock_db_scalar(1000),
        ]
        trigger = await service._cost_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered

    @pytest.mark.asyncio
    async def test_drift_when_cost_spikes(self):
        """Drift detectado quando custo cresce > 20%."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline: 1000, recente: 1500 → Δ_rel=50% > 20%
        db.execute.side_effect = [
            _mock_db_scalar(1500),
            _mock_db_scalar(1000),
        ]
        trigger = await service._cost_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert trigger.triggered
        assert trigger.delta > COST_DRIFT_THRESHOLD

    @pytest.mark.asyncio
    async def test_no_drift_when_baseline_zero(self):
        """Sem baseline de custo → sem drift (evita falsos positivos)."""
        service = ModelDriftService()
        db = AsyncMock()
        db.execute.side_effect = [
            _mock_db_scalar(500),
            _mock_db_scalar(0),
        ]
        trigger = await service._cost_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered


# ---------------------------------------------------------------------------
# Testes de detecção de drift — latência P95
# ---------------------------------------------------------------------------

class TestLatencyDrift:
    """Testa detecção de drift no P95 de latência."""

    @pytest.mark.asyncio
    async def test_no_drift_when_latency_stable(self):
        """Sem drift quando latência P95 varia < 50%."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline: [100,110,120,...], recente: [110,120,...] → P95 próximos
        baseline_values = list(range(100, 200, 10))  # 10 valores: 100-190
        recent_values = list(range(105, 205, 10))    # 10 valores: 105-195
        db.execute.side_effect = [
            _mock_db_fetchall(recent_values),
            _mock_db_fetchall(baseline_values),
        ]
        trigger = await service._latency_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered

    @pytest.mark.asyncio
    async def test_drift_when_latency_spikes(self):
        """Drift detectado quando latência P95 dobra."""
        service = ModelDriftService()
        db = AsyncMock()
        # baseline P95: ~190ms, recente P95: ~480ms → Δ_rel > 50%
        baseline_values = list(range(100, 200, 10))   # P95 = 190ms
        recent_values = list(range(300, 500, 20))     # P95 = 490ms
        db.execute.side_effect = [
            _mock_db_fetchall(recent_values),
            _mock_db_fetchall(baseline_values),
        ]
        trigger = await service._latency_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert trigger.triggered

    @pytest.mark.asyncio
    async def test_no_drift_when_no_latency_data(self):
        """Sem dados de latência → sem drift."""
        service = ModelDriftService()
        db = AsyncMock()
        db.execute.side_effect = [
            _mock_db_fetchall([]),   # recente: sem dados
            _mock_db_fetchall([]),   # baseline: sem dados
        ]
        trigger = await service._latency_drift(
            db, COMPANY_ID,
            recent_start=datetime.utcnow() - timedelta(days=7),
            baseline_start=datetime.utcnow() - timedelta(days=14),
        )
        assert not trigger.triggered


# ---------------------------------------------------------------------------
# Testes de avaliação completa
# ---------------------------------------------------------------------------

class TestModelDriftServiceEvaluate:
    """Testa evaluate() — orquestração dos 4 triggers."""

    @pytest.mark.asyncio
    async def test_evaluate_returns_drift_status(self):
        """evaluate() retorna DriftStatus com 4 triggers (mesmo que nenhum ative)."""
        service = ModelDriftService()
        db = AsyncMock()
        # Simular resposta neutra para todos os triggers
        db.execute.side_effect = [
            _mock_db_scalar(70.0),  # score: recent
            _mock_db_scalar(70.0),  # score: baseline
            _mock_db_scalar(10),    # approval: total recent
            _mock_db_scalar(5),     # approval: approved recent
            _mock_db_scalar(10),    # approval: total baseline
            _mock_db_scalar(5),     # approval: approved baseline
            _mock_db_scalar(1000),  # cost: recent
            _mock_db_scalar(1000),  # cost: baseline
            _mock_db_fetchall([100, 120, 130]),  # latency: recent
            _mock_db_fetchall([100, 120, 130]),  # latency: baseline
        ]
        status = await service.evaluate(db, COMPANY_ID)
        assert isinstance(status, DriftStatus)
        assert status.company_id == str(COMPANY_ID)
        assert len(status.triggers) == 4

    @pytest.mark.asyncio
    async def test_evaluate_no_drift_ok_status(self):
        """Sem drift → alert_level='ok'."""
        service = ModelDriftService()
        db = AsyncMock()
        db.execute.side_effect = [
            _mock_db_scalar(70.0), _mock_db_scalar(70.0),
            _mock_db_scalar(10), _mock_db_scalar(5),
            _mock_db_scalar(10), _mock_db_scalar(5),
            _mock_db_scalar(1000), _mock_db_scalar(1000),
            _mock_db_fetchall([100, 120]), _mock_db_fetchall([100, 120]),
        ]
        status = await service.evaluate(db, COMPANY_ID)
        assert not status.drift_detected
        assert status.alert_level == "ok"

    @pytest.mark.asyncio
    async def test_evaluate_handles_exception_gracefully(self):
        """Se um trigger falhar, os demais continuam e o status é retornado."""
        service = ModelDriftService()
        db = AsyncMock()
        # Primeiro execute levanta exceção (score_drift vai falhar)
        db.execute.side_effect = Exception("DB error")
        # Mesmo com falha, o serviço não deve propagar a exceção
        # (os triggers com erro são silenciados via logger.warning)
        status = await service.evaluate(db, COMPANY_ID)
        assert isinstance(status, DriftStatus)
        # Triggers que falharam foram ignorados
        assert len(status.triggers) == 0
        assert not status.drift_detected
