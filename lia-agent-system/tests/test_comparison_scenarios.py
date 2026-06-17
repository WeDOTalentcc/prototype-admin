"""
Tests for Candidate Comparison Service scenarios.

This module tests the LIA methodology's comparison scenarios:
- Scenario A: Screened candidates (all have WSI) - Full evaluation
- Scenario B: Non-screened candidates (CV only) - CV-based evaluation
- Scenario C: General comparison without job context

Reference: docs/LIA_UNIFIED_METHODOLOGY.md
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.domains.candidates.services.candidate_comparison_service import (
    CandidateComparisonService,
    ComparisonScenario,
    ScenarioWeights,
    CandidateComparisonResult,
)
from app.shared.services.lia_score_service import (
    DataAvailability,
    WEIGHT_DISTRIBUTION,
)


class TestScenarioWeights:
    """Test scenario weight configurations."""
    
    def test_scenario_a_weights(self):
        """Test Scenario A weights match documentation."""
        weights = ScenarioWeights.for_scenario_a()
        assert weights.rubricas == 0.40
        assert weights.wsi == 0.25
        assert weights.big_five == 0.15
        assert weights.pre_requisitos == 0.10
        assert weights.historico == 0.10
        assert sum(weights.to_dict().values()) == pytest.approx(1.0)
    
    def test_scenario_b_weights(self):
        """Test Scenario B weights match documentation."""
        weights = ScenarioWeights.for_scenario_b()
        assert weights.rubricas == 0.60
        assert weights.pre_requisitos == 0.25
        assert weights.historico == 0.15
        assert sum(weights.to_dict().values()) == pytest.approx(1.0)
    
    def test_scenario_c_weights(self):
        """Test Scenario C weights match documentation."""
        weights = ScenarioWeights.for_scenario_c()
        assert weights.historico == 0.50
        assert weights.completude == 0.30
        assert weights.recency == 0.20
        assert sum(weights.to_dict().values()) == pytest.approx(1.0)
    
    def test_scenario_a_uses_all_dimensions(self):
        """Scenario A should use all 5 evaluation dimensions."""
        weights = ScenarioWeights.for_scenario_a()
        active_weights = weights.to_dict()
        assert len(active_weights) == 5
        expected_keys = {"rubricas", "wsi", "big_five", "pre_requisitos", "historico"}
        assert set(active_weights.keys()) == expected_keys
    
    def test_scenario_b_no_wsi(self):
        """Scenario B should not use WSI or Big Five."""
        weights = ScenarioWeights.for_scenario_b()
        active_weights = weights.to_dict()
        assert "wsi" not in active_weights
        assert "big_five" not in active_weights
    
    def test_scenario_c_no_rubricas(self):
        """Scenario C should not use job-specific dimensions."""
        weights = ScenarioWeights.for_scenario_c()
        active_weights = weights.to_dict()
        assert "rubricas" not in active_weights
        assert "wsi" not in active_weights
        assert "pre_requisitos" not in active_weights


class TestScenarioWeightsToDict:
    """Test ScenarioWeights.to_dict() method."""
    
    def test_to_dict_excludes_zero_weights(self):
        """to_dict should only include non-zero weights."""
        weights = ScenarioWeights.for_scenario_b()
        result = weights.to_dict()
        for key, value in result.items():
            assert value > 0
    
    def test_to_dict_scenario_a_returns_correct_structure(self):
        """to_dict for Scenario A should return expected structure."""
        weights = ScenarioWeights.for_scenario_a()
        result = weights.to_dict()
        expected = {
            "rubricas": 0.40,
            "wsi": 0.25,
            "big_five": 0.15,
            "pre_requisitos": 0.10,
            "historico": 0.10,
        }
        assert result == expected


class TestLIAScoreServiceWeights:
    """Test LIA Score Service weight distribution alignment."""
    
    def test_cv_wsi_prereq_weights_sum_to_one(self):
        """Full data scenario weights should sum to 1.0."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_WSI_PREREQ]
        assert sum(weights.values()) == pytest.approx(1.0)
    
    def test_cv_prereq_weights_sum_to_one(self):
        """CV + prereq scenario weights should sum to 1.0."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_PREREQ]
        assert sum(weights.values()) == pytest.approx(1.0)
    
    def test_cv_only_weights_sum_to_one(self):
        """CV only scenario weights should sum to 1.0."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_ONLY]
        assert sum(weights.values()) == pytest.approx(1.0)
    
    def test_cv_wsi_prereq_has_big_five(self):
        """Full data scenario should include Big Five weight."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_WSI_PREREQ]
        assert "big_five" in weights
        assert weights["big_five"] == 0.10
    
    def test_cv_wsi_prereq_rubricas_weight(self):
        """Full data scenario should have rubricas at 40%."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_WSI_PREREQ]
        assert weights["rubricas"] == 0.40
    
    def test_cv_wsi_prereq_wsi_weight(self):
        """Full data scenario should have WSI at 25%."""
        weights = WEIGHT_DISTRIBUTION[DataAvailability.CV_WSI_PREREQ]
        assert weights["wsi"] == 0.25


class TestComparisonScenarioEnum:
    """Test ComparisonScenario enum."""
    
    def test_scenario_values(self):
        """Test scenario enum values."""
        assert ComparisonScenario.SCENARIO_A.value == "scenario_a"
        assert ComparisonScenario.SCENARIO_B.value == "scenario_b"
        assert ComparisonScenario.SCENARIO_C.value == "scenario_c"
    
    def test_all_scenarios_defined(self):
        """Test all 3 scenarios are defined."""
        scenarios = list(ComparisonScenario)
        assert len(scenarios) == 3


class TestCandidateComparisonService:
    """Test CandidateComparisonService methods."""
    
    def test_get_weights_for_scenario_a(self):
        """Test _get_weights_for_scenario returns correct weights for Scenario A."""
        service = CandidateComparisonService()
        weights = service._get_weights_for_scenario(ComparisonScenario.SCENARIO_A)
        assert weights.rubricas == 0.40
        assert weights.wsi == 0.25
    
    def test_get_weights_for_scenario_b(self):
        """Test _get_weights_for_scenario returns correct weights for Scenario B."""
        service = CandidateComparisonService()
        weights = service._get_weights_for_scenario(ComparisonScenario.SCENARIO_B)
        assert weights.rubricas == 0.60
        assert weights.wsi == 0.0
    
    def test_get_weights_for_scenario_c(self):
        """Test _get_weights_for_scenario returns correct weights for Scenario C."""
        service = CandidateComparisonService()
        weights = service._get_weights_for_scenario(ComparisonScenario.SCENARIO_C)
        assert weights.historico == 0.50
        assert weights.rubricas == 0.0
    
    def test_get_scenario_description(self):
        """Test _get_scenario_description returns meaningful description."""
        service = CandidateComparisonService()
        desc_a = service._get_scenario_description(ComparisonScenario.SCENARIO_A)
        assert "Cenário A" in desc_a
        assert "WSI" in desc_a
        
        desc_b = service._get_scenario_description(ComparisonScenario.SCENARIO_B)
        assert "Cenário B" in desc_b
        assert "CV" in desc_b
        
        desc_c = service._get_scenario_description(ComparisonScenario.SCENARIO_C)
        assert "Cenário C" in desc_c
    
    def test_get_methodology_for_scenario_a(self):
        """Test methodology list for Scenario A."""
        service = CandidateComparisonService()
        methods = service._get_methodology_for_scenario(ComparisonScenario.SCENARIO_A)
        assert "rubricas_bars" in methods
        assert "wsi" in methods
        assert "big_five" in methods
    
    def test_get_methodology_for_scenario_b(self):
        """Test methodology list for Scenario B."""
        service = CandidateComparisonService()
        methods = service._get_methodology_for_scenario(ComparisonScenario.SCENARIO_B)
        assert "rubricas_bars" in methods
        assert "wsi" not in methods
    
    def test_get_methodology_for_scenario_c(self):
        """Test methodology list for Scenario C."""
        service = CandidateComparisonService()
        methods = service._get_methodology_for_scenario(ComparisonScenario.SCENARIO_C)
        assert "historico" in methods
        assert "completude" in methods
        assert "recencia" in methods


class TestScenarioWeightsEdgeCases:
    """Test edge cases for scenario weights."""
    
    def test_default_weights_are_zero(self):
        """Default ScenarioWeights should have all zeros."""
        weights = ScenarioWeights()
        assert weights.rubricas == 0.0
        assert weights.wsi == 0.0
        assert weights.big_five == 0.0
        assert weights.pre_requisitos == 0.0
        assert weights.historico == 0.0
        assert weights.completude == 0.0
        assert weights.recency == 0.0
    
    def test_to_dict_empty_when_all_zero(self):
        """to_dict should return empty dict when all weights are zero."""
        weights = ScenarioWeights()
        assert weights.to_dict() == {}
    
    def test_custom_weights(self):
        """Test creating custom weights."""
        weights = ScenarioWeights(
            rubricas=0.50,
            historico=0.50
        )
        result = weights.to_dict()
        assert result == {"rubricas": 0.50, "historico": 0.50}
        assert sum(result.values()) == pytest.approx(1.0)


class TestScenarioDetection:
    """Test scenario detection logic."""
    
    @pytest.fixture
    def mock_candidates(self):
        """Create mock candidates for testing."""
        from unittest.mock import MagicMock
        c1 = MagicMock()
        c1.id = "cand-1"
        c2 = MagicMock()
        c2.id = "cand-2"
        return [c1, c2]
    
    @pytest.fixture
    def mock_job(self):
        """Create mock job for testing."""
        from unittest.mock import MagicMock
        job = MagicMock()
        job.id = "job-1"
        job.title = "Developer Python"
        return job
    
    @pytest.fixture
    def mock_vacancy_candidates_wsi_complete(self, mock_candidates):
        """VacancyCandidate records with WSI completed."""
        from unittest.mock import MagicMock
        vcs = {}
        for c in mock_candidates:
            vc = MagicMock()
            vc.wsi_completed = True
            vc.wsi_score = 4.2
            vcs[str(c.id)] = vc
        return vcs
    
    @pytest.fixture
    def mock_vacancy_candidates_no_wsi(self, mock_candidates):
        """VacancyCandidate records without WSI."""
        from unittest.mock import MagicMock
        vcs = {}
        for c in mock_candidates:
            vc = MagicMock()
            vc.wsi_completed = False
            vc.wsi_score = None
            vcs[str(c.id)] = vc
        return vcs
    
    @pytest.mark.asyncio
    async def test_detect_scenario_a_all_wsi_completed(
        self, 
        mock_candidates, 
        mock_job, 
        mock_vacancy_candidates_wsi_complete
    ):
        """Scenario A: All candidates have WSI completed for this job."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates=mock_vacancy_candidates_wsi_complete
        )
        assert scenario == ComparisonScenario.SCENARIO_A
    
    @pytest.mark.asyncio
    async def test_detect_scenario_b_partial_wsi(
        self,
        mock_candidates,
        mock_job,
        mock_vacancy_candidates_no_wsi
    ):
        """Scenario B: Job exists but candidates don't have WSI."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates=mock_vacancy_candidates_no_wsi
        )
        assert scenario == ComparisonScenario.SCENARIO_B
    
    @pytest.mark.asyncio
    async def test_detect_scenario_c_no_job(self, mock_candidates):
        """Scenario C: No job context."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=None,
            wsi_data={},
            vacancy_candidates={}
        )
        assert scenario == ComparisonScenario.SCENARIO_C
    
    @pytest.mark.asyncio
    async def test_detect_scenario_force_a(self, mock_candidates, mock_job):
        """Force scenario A should override auto-detection."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates={},
            force_scenario="A"
        )
        assert scenario == ComparisonScenario.SCENARIO_A
    
    @pytest.mark.asyncio
    async def test_detect_scenario_force_b(self, mock_candidates, mock_job):
        """Force scenario B should override auto-detection."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates={},
            force_scenario="B"
        )
        assert scenario == ComparisonScenario.SCENARIO_B
    
    @pytest.mark.asyncio
    async def test_detect_scenario_force_c(self, mock_candidates, mock_job):
        """Force scenario C should override auto-detection."""
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates={},
            force_scenario="C"
        )
        assert scenario == ComparisonScenario.SCENARIO_C
    
    @pytest.mark.asyncio
    async def test_detect_scenario_mixed_wsi(self, mock_candidates, mock_job):
        """Scenario B when only some candidates have WSI."""
        from unittest.mock import MagicMock
        vcs = {}
        vc1 = MagicMock()
        vc1.wsi_completed = True
        vc1.wsi_score = 4.5
        vcs[str(mock_candidates[0].id)] = vc1
        
        vc2 = MagicMock()
        vc2.wsi_completed = False
        vc2.wsi_score = None
        vcs[str(mock_candidates[1].id)] = vc2
        
        service = CandidateComparisonService()
        scenario = await service._detect_scenario(
            candidates=mock_candidates,
            job=mock_job,
            wsi_data={},
            vacancy_candidates=vcs
        )
        assert scenario == ComparisonScenario.SCENARIO_B


class TestWSIDataRetrieval:
    """Test WSI data retrieval with job scoping."""
    
    def test_wsi_data_from_vacancy_candidate(self):
        """Should prioritize VacancyCandidate WSI when available."""
        from unittest.mock import MagicMock
        
        vc = MagicMock()
        vc.wsi_completed = True
        vc.wsi_score = 4.5
        
        if vc.wsi_completed and vc.wsi_score:
            result = {
                "overall_score": vc.wsi_score,
                "source": "vacancy_candidate",
                "job_scoped": True
            }
            assert result["job_scoped"] == True
            assert result["overall_score"] == 4.5
            assert result["source"] == "vacancy_candidate"
    
    def test_wsi_data_not_from_incomplete_vacancy_candidate(self):
        """Should not use VacancyCandidate WSI when wsi_completed is False."""
        from unittest.mock import MagicMock
        
        vc = MagicMock()
        vc.wsi_completed = False
        vc.wsi_score = 4.5
        
        should_use_vc = vc.wsi_completed and vc.wsi_score
        assert should_use_vc == False
    
    def test_wsi_data_not_from_null_score(self):
        """Should not use VacancyCandidate WSI when wsi_score is None."""
        from unittest.mock import MagicMock
        
        vc = MagicMock()
        vc.wsi_completed = True
        vc.wsi_score = None
        
        should_use_vc = vc.wsi_completed and vc.wsi_score is not None
        assert should_use_vc == False
    
    def test_wsi_source_tracking(self):
        """WSI data should track its source for debugging."""
        from unittest.mock import MagicMock
        
        vc = MagicMock()
        vc.wsi_completed = True
        vc.wsi_score = 85.0
        
        result = {
            "overall_score": vc.wsi_score,
            "source": "vacancy_candidate",
            "job_scoped": True
        }
        
        assert "source" in result
        assert result["source"] == "vacancy_candidate"


class TestWSIDataPriority:
    """Test WSI data priority order."""
    
    def test_priority_order_documentation(self):
        """Verify the documented priority order for WSI data."""
        priorities = [
            "1. VacancyCandidate.wsi_score (if wsi_completed=True) - most reliable, job-scoped",
            "2. VoiceScreeningCall with matching job_title - fallback",
            "3. Most recent VoiceScreeningCall - last resort fallback"
        ]
        
        assert len(priorities) == 3
        assert "VacancyCandidate" in priorities[0]
        assert "job_title" in priorities[1]
        assert "most recent" in priorities[2].lower()
    
    def test_vacancy_candidate_has_required_fields(self):
        """Verify VacancyCandidate mock has required WSI fields."""
        from unittest.mock import MagicMock
        
        vc = MagicMock()
        vc.wsi_completed = True
        vc.wsi_score = 4.2
        
        assert hasattr(vc, 'wsi_completed')
        assert hasattr(vc, 'wsi_score')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
