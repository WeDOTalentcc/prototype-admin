"""Coverage tests for candidate_comparison_service.py — dataclasses and pure methods."""
import pytest
from app.domains.candidates.services.candidate_comparison_service import (
    ComparisonScenario,
    ScenarioWeights,
    DimensionScore,
    CandidateComparisonResult,
)


class TestComparisonScenario:
    def test_has_three_scenarios(self):
        scenarios = list(ComparisonScenario)
        assert len(scenarios) == 3

    def test_scenario_a_value(self):
        assert ComparisonScenario.SCENARIO_A == "scenario_a"

    def test_scenario_b_value(self):
        assert ComparisonScenario.SCENARIO_B == "scenario_b"

    def test_scenario_c_value(self):
        assert ComparisonScenario.SCENARIO_C == "scenario_c"


class TestScenarioWeights:
    def test_scenario_a_weights_sum_to_1(self):
        w = ScenarioWeights.for_scenario_a()
        d = w.to_dict()
        total = sum(d.values())
        assert abs(total - 1.0) < 0.001

    def test_scenario_b_weights_sum_to_1(self):
        w = ScenarioWeights.for_scenario_b()
        d = w.to_dict()
        total = sum(d.values())
        assert abs(total - 1.0) < 0.001

    def test_scenario_c_weights_sum_to_1(self):
        w = ScenarioWeights.for_scenario_c()
        d = w.to_dict()
        total = sum(d.values())
        assert abs(total - 1.0) < 0.001

    def test_scenario_a_has_wsi(self):
        w = ScenarioWeights.for_scenario_a()
        assert w.wsi > 0

    def test_scenario_b_no_wsi(self):
        w = ScenarioWeights.for_scenario_b()
        assert w.wsi == 0.0

    def test_scenario_c_has_recency(self):
        w = ScenarioWeights.for_scenario_c()
        assert w.recency > 0

    def test_to_dict_excludes_zeros(self):
        w = ScenarioWeights.for_scenario_b()
        d = w.to_dict()
        assert "wsi" not in d  # wsi=0 excluded
        assert "big_five" not in d

    def test_to_dict_includes_nonzero(self):
        w = ScenarioWeights.for_scenario_a()
        d = w.to_dict()
        assert "rubricas" in d
        assert "wsi" in d


class TestDimensionScore:
    def test_basic_construction(self):
        ds = DimensionScore(
            dimension="wsi",
            score=0.8,
            weight=0.25,
            weighted_score=0.2,
        )
        assert ds.dimension == "wsi"
        assert ds.score == 0.8
        assert ds.weight == 0.25

    def test_details_optional(self):
        ds = DimensionScore("rubricas", 0.75, 0.4, 0.3)
        assert ds.details is None

    def test_with_details(self):
        ds = DimensionScore("rubricas", 0.75, 0.4, 0.3, details="good match")
        assert ds.details == "good match"


class TestCandidateComparisonResult:
    @pytest.fixture
    def result(self):
        return CandidateComparisonResult(
            comparison_id="cmp-001",
            winner="candidate-a",
            winner_name="João Silva",
            confidence=0.85,
            scenario=ComparisonScenario.SCENARIO_A,
            scenario_description="Screened candidates",
            methodology_used=["rubrics", "wsi"],
            data_completeness={"c1": {"wsi": True}, "c2": {"wsi": False}},
            weights_used={"rubricas": 0.4, "wsi": 0.25},
            dimension_comparison={},
            candidate_scores={"c1": 0.85, "c2": 0.70},
            analysis="Candidate A performed better overall",
            scenarios_recommendation=[],
            generated_at="2026-05-10T12:00:00",
        )

    def test_to_dict_basic_fields(self, result):
        d = result.to_dict()
        assert d["comparison_id"] == "cmp-001"
        assert d["winner"] == "candidate-a"
        assert d["winner_name"] == "João Silva"

    def test_to_dict_confidence_rounded(self, result):
        d = result.to_dict()
        assert d["confidence"] == 0.85

    def test_to_dict_scenario_is_value(self, result):
        d = result.to_dict()
        assert d["scenario"] == "scenario_a"

    def test_to_dict_candidate_scores_rounded(self, result):
        d = result.to_dict()
        scores = d["candidate_scores"]
        assert scores["c1"] == 0.85
        assert scores["c2"] == 0.7

    def test_to_dict_none_winner_allowed(self):
        r = CandidateComparisonResult(
            comparison_id="cmp-002",
            winner=None, winner_name=None,
            confidence=0.5,
            scenario=ComparisonScenario.SCENARIO_C,
            scenario_description="Tie",
            methodology_used=[],
            data_completeness={},
            weights_used={},
            dimension_comparison={},
            candidate_scores={},
            analysis="",
            scenarios_recommendation=[],
            generated_at="2026-05-10",
        )
        d = r.to_dict()
        assert d["winner"] is None
