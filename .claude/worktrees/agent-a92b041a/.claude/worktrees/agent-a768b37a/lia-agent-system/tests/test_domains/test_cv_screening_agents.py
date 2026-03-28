"""
Tests for CV Screening — nova arquitetura Sprint 5.

Cobre:
- CVScreeningBatchService: importação, thresholds, _determine_recommendation, _calculate_wsi_score
- PipelineReActAgent: importável
- FairnessGuard Layer 3: callable e presente no rubric_evaluation_service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCVScreeningBatchServiceImport:
    """CVScreeningBatchService importável do domínio correto."""

    def test_service_importable(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        assert callable(run_batch)

    def test_score_thresholds_defined(self):
        import app.domains.cv_screening.services.cv_screening_batch_service as m
        assert hasattr(m, "_SCORE_THRESHOLDS")
        thresholds = m._SCORE_THRESHOLDS
        assert "auto_approve" in thresholds
        assert "review" in thresholds

    def test_wsi_weights_defined(self):
        import app.domains.cv_screening.services.cv_screening_batch_service as m
        assert m._WSI_TECHNICAL_WEIGHT == 0.70
        assert m._WSI_BEHAVIORAL_WEIGHT == 0.30


class TestCVScreeningScoreCalculation:
    """Cálculo correto de recomendações e scores WSI."""

    def test_recommendation_advance(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _determine_recommendation
        assert _determine_recommendation(80.0) == "avançar"
        assert _determine_recommendation(75.0) == "avançar"

    def test_recommendation_review(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _determine_recommendation
        assert _determine_recommendation(65.0) == "revisao"
        assert _determine_recommendation(55.0) == "revisao"

    def test_recommendation_reject(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _determine_recommendation
        assert _determine_recommendation(40.0) == "rejeitar"
        assert _determine_recommendation(0.0) == "rejeitar"

    def test_wsi_score_high_rubric(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _calculate_wsi_score
        result = _calculate_wsi_score(90.0)
        assert result["wsi_score"] > 0
        assert result["classification"] in ("Excelente", "Alto", "Médio", "Regular", "Baixo")
        assert result["technical_score"] == 90.0

    def test_wsi_score_low_rubric(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _calculate_wsi_score
        result = _calculate_wsi_score(20.0)
        assert result["classification"] in ("Regular", "Baixo")

    def test_wsi_score_fields_present(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import _calculate_wsi_score
        result = _calculate_wsi_score(70.0)
        assert "wsi_score" in result
        assert "technical_score" in result
        assert "behavioral_score" in result
        assert "classification" in result


class TestFairnessGuardLayer3:
    """FairnessGuard Layer 3 integrado e callable."""

    def test_fairness_guard_check_semantic_callable(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        import asyncio
        guard = FairnessGuard()
        assert callable(guard.check_semantic)
        assert asyncio.iscoroutinefunction(guard.check_semantic)

    def test_fairness_guard_present_in_rubric_evaluation_service(self):
        """FairnessGuard deve proteger o rubric_evaluation_service (Sessões A-C)."""
        import inspect
        # app/services/rubric_evaluation_service.py é um shim (from ... import *).
        # A implementação real está no domínio cv_screening.
        import app.domains.cv_screening.services.rubric_evaluation_service as m
        source = inspect.getsource(m)
        assert "FairnessGuard" in source or "fairness" in source.lower(), \
            "rubric_evaluation_service deve integrar FairnessGuard"


class TestPipelineReActAgentImport:
    """PipelineReActAgent importável — substituto canônico de triagem."""

    def test_agent_importable(self):
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        assert agent is not None

    def test_agent_domain_name(self):
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        assert agent.domain_name in ("pipeline", "cv_screening")
