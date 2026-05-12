"""Unit tests for eval_runner.gate_check + record_gate_run (T-E gate).

Garante que a semântica do gate é estável:
- pass quando histórico não acumulou N runs (warm-up)
- fail quando última N rodadas têm score médio < threshold em algum agente
- fail quando cobertura de inventário < 80% nas últimas N rodadas
- pass após recuperação (scores voltam acima do threshold)
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from eval.eval_runner import gate_check, record_gate_run

DATASET = "eval/golden/tenant_context.jsonl"

# 16-agent canonical inventory (espelha sentinel T-D + gate)
FULL_INVENTORY = {
    "analytics", "ats_integration", "automation", "autonomous",
    "candidate_self_service", "communication", "company_settings",
    "cv_screening_pipeline", "hiring_policy", "jobs_management", "kanban",
    "talent_funnel", "sourcing", "talent_pool", "pipeline_transition",
    "wizard",
}


@pytest.fixture
def hist_path(tmp_path: Path) -> str:
    return str(tmp_path / ".gate_history.json")


def _record_full_run(hist: str, score: float) -> None:
    record_gate_run(DATASET, {a: score for a in FULL_INVENTORY}, hist)


def test_gate_passes_when_no_history(hist_path):
    assert gate_check(DATASET, history_path=hist_path) == 0


def test_gate_passes_when_warming_up(hist_path):
    _record_full_run(hist_path, 0.50)
    assert gate_check(DATASET, consecutive_runs=2, history_path=hist_path) == 0


def test_gate_fails_on_consecutive_low_scores(hist_path):
    _record_full_run(hist_path, 0.50)
    _record_full_run(hist_path, 0.60)
    assert gate_check(DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path) == 1


def test_gate_passes_after_recovery(hist_path):
    _record_full_run(hist_path, 0.50)
    _record_full_run(hist_path, 0.60)
    _record_full_run(hist_path, 0.95)
    _record_full_run(hist_path, 0.97)
    assert gate_check(DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path) == 0


def test_gate_fails_on_low_inventory_coverage(hist_path):
    record_gate_run(DATASET, {"wizard": 0.95}, hist_path)
    record_gate_run(DATASET, {"wizard": 0.95}, hist_path)
    assert gate_check(DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path) == 1


def test_gate_isolates_dataset(hist_path):
    record_gate_run("other.jsonl", {a: 0.10 for a in FULL_INVENTORY}, hist_path)
    record_gate_run("other.jsonl", {a: 0.10 for a in FULL_INVENTORY}, hist_path)
    assert gate_check(DATASET, history_path=hist_path) == 0


def test_record_gate_run_caps_history_at_50(hist_path):
    for i in range(60):
        _record_full_run(hist_path, 0.90)
    data = json.loads(Path(hist_path).read_text())
    assert len(data["runs"]) == 50


# ─── Task #999: dataset-aware inventory ────────────────────────────────────
# The Settings golden (company_settings_prefill.jsonl) only covers the
# `company_settings` ReActAgent. Before #999 the gate hardcoded the 16-agent
# T-D inventory for every dataset, so the Settings gate would FAIL the 80%
# coverage rule the moment it had real data. Lock in the fix: single-agent
# datasets must derive expected agents from the JSONL itself and pass when
# their lone agent scores above threshold for N consecutive runs.

CSP_DATASET = "eval/golden/company_settings_prefill.jsonl"


def test_settings_gate_passes_with_single_agent_above_threshold(hist_path):
    record_gate_run(CSP_DATASET, {"company_settings": 0.95}, hist_path)
    record_gate_run(CSP_DATASET, {"company_settings": 0.97}, hist_path)
    assert gate_check(
        CSP_DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path
    ) == 0


def test_settings_gate_fails_when_company_settings_regresses(hist_path):
    record_gate_run(CSP_DATASET, {"company_settings": 0.50}, hist_path)
    record_gate_run(CSP_DATASET, {"company_settings": 0.60}, hist_path)
    assert gate_check(
        CSP_DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path
    ) == 1


def test_tenant_context_gate_still_requires_full_inventory(hist_path):
    # Sentinela: o dataset T-D canônico mantém a regra de 16 agentes.
    record_gate_run(DATASET, {"company_settings": 0.95}, hist_path)
    record_gate_run(DATASET, {"company_settings": 0.95}, hist_path)
    assert gate_check(
        DATASET, threshold=0.85, consecutive_runs=2, history_path=hist_path
    ) == 1
