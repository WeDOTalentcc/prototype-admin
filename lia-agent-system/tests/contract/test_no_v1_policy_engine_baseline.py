"""WT-2022 P3.1: Contract test — V1 PolicyEngine baseline stays controlled.

Sensor de regressão: roda ``scripts/check_no_v1_policy_engine.py`` e garante que
o baseline (0 imports fora da allowlist) permanece estável. Quando V1 PolicyEngine
for finalmente deletado (roadmap Q3 2026), trocar para asserção blocking strict.

Skill: harness-engineering [sensor permanente] — protege contra reintrodução de
import V1 fora de paths exempt (build_default_gate, V2 fallback, etc.).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR_SCRIPT = REPO_ROOT / "scripts" / "check_no_v1_policy_engine.py"


def test_v1_policy_engine_imports_under_threshold():
    """Baseline atual = 0 imports V1 fora da allowlist. Nunca deve crescer."""
    assert SENSOR_SCRIPT.exists(), f"sensor missing: {SENSOR_SCRIPT}"

    result = subprocess.run(
        [sys.executable, str(SENSOR_SCRIPT), "--threshold", "0"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, (
        f"WT-2022 P3.1 regression: novos imports V1 PolicyEngine fora da "
        f"allowlist (exit={result.returncode}). Output:\n{result.stdout}\n{result.stderr}"
    )


def test_v1_policy_engine_sensor_warn_only_mode_ok():
    """Modo warn-only retorna 0 mesmo com violations (não-blocking inicial)."""
    result = subprocess.run(
        [sys.executable, str(SENSOR_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"warn-only mode quebrou: exit={result.returncode}\n{result.stdout}\n{result.stderr}"
    )
