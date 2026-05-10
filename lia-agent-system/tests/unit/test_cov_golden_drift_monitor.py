"""Coverage tests for golden_drift_monitor.py — dataclasses and BaselineManager without file I/O."""
import json
import pytest
from pathlib import Path
from dataclasses import asdict
from unittest.mock import MagicMock, patch
from app.services.golden_drift_monitor import (
    AgentBaseline,
    AgentDriftResult,
    DriftReport,
    BaselineManager,
    GoldenDriftDetector,
    DRIFT_THRESHOLD_WARNING,
    DRIFT_THRESHOLD_CRITICAL,
    AGENTS_TO_MONITOR,
    dispatch_drift_alerts,
)


class TestAgentBaseline:
    def test_basic_instantiation(self):
        b = AgentBaseline(agent="screening", pass_rate=0.85, avg_score=7.5)
        assert b.agent == "screening"
        assert b.pass_rate == pytest.approx(0.85)
        assert b.avg_score == pytest.approx(7.5)

    def test_default_updated_at(self):
        b = AgentBaseline(agent="wizard", pass_rate=0.9, avg_score=8.0)
        assert b.updated_at == ""

    def test_with_updated_at(self):
        b = AgentBaseline(agent="sourcing", pass_rate=0.75, avg_score=7.0, updated_at="2026-05-01")
        assert b.updated_at == "2026-05-01"

    def test_asdict(self):
        b = AgentBaseline(agent="pipeline", pass_rate=0.8, avg_score=6.5)
        d = asdict(b)
        assert d["agent"] == "pipeline"
        assert d["pass_rate"] == pytest.approx(0.8)


class TestAgentDriftResult:
    def test_stable_result(self):
        r = AgentDriftResult(
            agent="screening",
            baseline_pass_rate=0.85,
            current_pass_rate=0.86,
            delta=0.01,
            status="stable",
        )
        assert r.status == "stable"
        assert r.delta == pytest.approx(0.01)

    def test_warning_result(self):
        r = AgentDriftResult(
            agent="wizard",
            baseline_pass_rate=0.90,
            current_pass_rate=0.85,
            delta=-0.05,
            status="warning",
        )
        assert r.status == "warning"
        assert r.delta < 0

    def test_critical_result(self):
        r = AgentDriftResult(
            agent="pipeline",
            baseline_pass_rate=0.80,
            current_pass_rate=0.62,
            delta=-0.18,
            status="critical",
        )
        assert r.status == "critical"

    def test_no_baseline_result(self):
        r = AgentDriftResult(
            agent="sourcing",
            baseline_pass_rate=0.0,
            current_pass_rate=0.75,
            delta=0.0,
            status="no_baseline",
        )
        assert r.status == "no_baseline"


class TestDriftReport:
    def test_defaults(self):
        r = DriftReport(timestamp="2026-05-10T10:00:00Z")
        assert r.overall_status == "stable"
        assert r.agents == []
        assert r.eval_errors == []

    def test_with_agents(self):
        a = AgentDriftResult(
            agent="screening", baseline_pass_rate=0.8, current_pass_rate=0.85,
            delta=0.05, status="stable"
        )
        r = DriftReport(timestamp="2026-05-10T10:00:00Z", agents=[a], overall_status="stable")
        assert len(r.agents) == 1

    def test_with_eval_errors(self):
        r = DriftReport(
            timestamp="2026-05-10T10:00:00Z",
            eval_errors=["Eval runner failed for screening"],
            overall_status="warning",
        )
        assert len(r.eval_errors) == 1


class TestBaselineManager:
    def test_load_returns_empty_when_no_file(self, tmp_path):
        manager = BaselineManager(path=tmp_path / "nonexistent.json")
        result = manager.load()
        assert result == {}

    def test_has_baseline_false_when_no_file(self, tmp_path):
        manager = BaselineManager(path=tmp_path / "nonexistent.json")
        assert manager.has_baseline() is False

    def test_has_baseline_true_when_file_exists(self, tmp_path):
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps({"agents": {}}))
        manager = BaselineManager(path=path)
        assert manager.has_baseline() is True

    def test_save_and_load_roundtrip(self, tmp_path):
        path = tmp_path / "baseline.json"
        manager = BaselineManager(path=path)

        baselines = {
            "screening": AgentBaseline(agent="screening", pass_rate=0.85, avg_score=7.5),
            "wizard": AgentBaseline(agent="wizard", pass_rate=0.90, avg_score=8.0),
        }
        manager.save(baselines)
        assert path.exists()

        loaded = manager.load()
        assert "screening" in loaded
        assert loaded["screening"].pass_rate == pytest.approx(0.85)
        assert loaded["wizard"].avg_score == pytest.approx(8.0)

    def test_load_corrupt_file_returns_empty(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json{{{")
        manager = BaselineManager(path=path)
        result = manager.load()
        assert result == {}

    def test_save_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "baseline.json"
        manager = BaselineManager(path=deep_path)
        manager.save({"screening": AgentBaseline(agent="screening", pass_rate=0.8, avg_score=7.0)})
        assert deep_path.exists()

    def test_saved_file_contains_baseline_date(self, tmp_path):
        path = tmp_path / "baseline.json"
        manager = BaselineManager(path=path)
        manager.save({"w": AgentBaseline(agent="w", pass_rate=0.7, avg_score=6.0)})
        data = json.loads(path.read_text())
        assert "baseline_date" in data
        assert "agents" in data


class TestDriftConstants:
    def test_warning_threshold(self):
        assert DRIFT_THRESHOLD_WARNING == pytest.approx(0.05)

    def test_critical_threshold(self):
        assert DRIFT_THRESHOLD_CRITICAL == pytest.approx(0.15)

    def test_agents_to_monitor_list(self):
        assert isinstance(AGENTS_TO_MONITOR, list)
        assert len(AGENTS_TO_MONITOR) >= 3
        assert "screening" in AGENTS_TO_MONITOR


class TestDispatchDriftAlerts:
    def test_stable_report_no_alerts(self):
        report = DriftReport(timestamp="2026-05-10T10:00:00Z", overall_status="stable")
        # Should not raise
        dispatch_drift_alerts(report)

    def test_warning_report_dispatches(self):
        report = DriftReport(
            timestamp="2026-05-10T10:00:00Z",
            overall_status="warning",
            agents=[
                AgentDriftResult(
                    agent="screening",
                    baseline_pass_rate=0.85,
                    current_pass_rate=0.80,
                    delta=-0.05,
                    status="warning",
                )
            ],
        )
        # Should not raise even if Sentry not configured
        dispatch_drift_alerts(report)

    def test_critical_report_dispatches(self):
        report = DriftReport(
            timestamp="2026-05-10T10:00:00Z",
            overall_status="critical",
            agents=[
                AgentDriftResult(
                    agent="wizard",
                    baseline_pass_rate=0.90,
                    current_pass_rate=0.70,
                    delta=-0.20,
                    status="critical",
                )
            ],
        )
        dispatch_drift_alerts(report)


class TestGoldenDriftDetector:
    def test_instantiation(self):
        detector = GoldenDriftDetector()
        assert detector is not None

    def test_extract_scores_empty_result(self):
        detector = GoldenDriftDetector()
        scores = detector._extract_scores({})
        assert isinstance(scores, dict)
        # All AGENTS_TO_MONITOR should be in scores
        for agent in AGENTS_TO_MONITOR:
            assert agent in scores

    def test_extract_scores_with_results(self):
        detector = GoldenDriftDetector()
        eval_result = {
            "suites": {
                "golden": {
                    "results": [
                        {"passed": True},
                        {"passed": True},
                        {"passed": False},
                        {"passed": True},
                    ]
                }
            }
        }
        scores = detector._extract_scores(eval_result)
        # 3 passed out of 4 = 0.75
        for agent in AGENTS_TO_MONITOR:
            assert scores[agent]["pass_rate"] == pytest.approx(0.75)

    def test_extract_scores_all_passed(self):
        detector = GoldenDriftDetector()
        eval_result = {
            "suites": {
                "golden": {
                    "results": [{"passed": True}, {"passed": True}]
                }
            }
        }
        scores = detector._extract_scores(eval_result)
        for agent in AGENTS_TO_MONITOR:
            assert scores[agent]["pass_rate"] == pytest.approx(1.0)

    def test_extract_scores_no_results(self):
        detector = GoldenDriftDetector()
        eval_result = {"suites": {"golden": {"results": []}}}
        scores = detector._extract_scores(eval_result)
        # total_count = max(0, 1) = 1; passed = 0 → pass_rate = 0.0
        for agent in AGENTS_TO_MONITOR:
            assert scores[agent]["pass_rate"] == pytest.approx(0.0)
