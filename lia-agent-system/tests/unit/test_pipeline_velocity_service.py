"""
Unit tests for PipelineVelocityService — Sprint 1B.

Tests the scoring/threshold logic that does NOT require a DB connection.
Integration tests (with DB) are tracked separately.
"""
import pytest
from app.shared.services.pipeline_velocity_service import (
    PipelineVelocityService,
    _threshold_for_stage,
)


# ─── Threshold helpers ────────────────────────────────────────────────────────

class TestThresholdForStage:
    def test_triagem_threshold(self):
        assert _threshold_for_stage("triagem") == 3

    def test_interview_hr_threshold(self):
        assert _threshold_for_stage("interview_hr") == 5

    def test_interview_technical_threshold(self):
        assert _threshold_for_stage("interview_technical") == 7

    def test_offer_threshold(self):
        assert _threshold_for_stage("offer") == 3

    def test_unknown_stage_defaults_to_5(self):
        assert _threshold_for_stage("alguma_etapa_customizada") == 5

    def test_empty_string_defaults_to_5(self):
        assert _threshold_for_stage("") == 5

    def test_case_insensitive(self):
        assert _threshold_for_stage("TRIAGEM") == _threshold_for_stage("triagem")
        assert _threshold_for_stage("Interview_HR") == _threshold_for_stage("interview_hr")


# ─── Overall health logic ─────────────────────────────────────────────────────

class TestOverallHealthLogic:
    """Test the overall_health determination logic inline."""

    def _compute_health(self, bottleneck_count: int) -> str:
        """Mirror the logic in get_velocity_metrics."""
        if bottleneck_count >= 3:
            return "critical"
        elif bottleneck_count > 0:
            return "warning"
        return "healthy"

    def test_no_bottlenecks_is_healthy(self):
        assert self._compute_health(0) == "healthy"

    def test_one_bottleneck_is_warning(self):
        assert self._compute_health(1) == "warning"

    def test_two_bottlenecks_is_warning(self):
        assert self._compute_health(2) == "warning"

    def test_three_or_more_bottlenecks_is_critical(self):
        assert self._compute_health(3) == "critical"
        assert self._compute_health(5) == "critical"


# ─── Service error handling ───────────────────────────────────────────────────

class TestVelocityServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_returns_safe_dict_on_db_error(self):
        """Service deve retornar dict seguro, não estoura, quando DB falha."""
        svc = PipelineVelocityService()
        # Sem DB válido → deve capturar exceção e retornar estrutura vazia
        result = await svc.get_velocity_metrics(vacancy_id="invalid-uuid-xxx")
        assert isinstance(result, dict)
        assert "per_stage" in result
        assert "overall_health" in result
        # overall_health pode ser "healthy" (sem dados) ou "unknown" (erro)
        assert result["overall_health"] in ("healthy", "unknown")

    @pytest.mark.asyncio
    async def test_bottlenecked_returns_list_on_db_error(self):
        """get_bottlenecked_candidates deve retornar lista vazia, não estoura."""
        svc = PipelineVelocityService()
        result = await svc.get_bottlenecked_candidates(company_id="invalid-id-xxx")
        assert isinstance(result, list)
