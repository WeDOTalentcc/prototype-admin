"""Contract test: schema-sync RecruitmentStage TS<->TS sensor smoke.

Baseline 2026-05-21 — sensor exit 0 (sem drift). Estes testes asseguram:
1. Sensor roda sem TypeError/ImportError
2. Output continua estavel (sem regressao silenciosa de drift)

Quando sensor virar blocking (ratchet baseline = 0 mantido por N sprints),
estes testes ja validam a invariant.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# __file__ = lia-agent-system/tests/contract/test_schema_sync_baseline.py
# parents[0]=contract, [1]=tests, [2]=lia-agent-system, [3]=repo root (workspace)
REPO_ROOT = Path(__file__).resolve().parents[3]
SENSOR = REPO_ROOT / "lia-agent-system/scripts/check_schema_sync_recruitment_stage.py"


def _run_sensor() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SENSOR)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )


def test_schema_sync_sensor_runs_clean():
    """Sensor existe, parse-eh, e retorna exit code 0 (warn-only)."""
    assert SENSOR.exists(), f"Sensor nao encontrado em {SENSOR}"
    result = _run_sensor()
    assert result.returncode == 0, (
        f"Sensor exit code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_schema_sync_baseline_zero_drift():
    """Baseline 2026-05-21: zero drift. Regressao = field novo num lado sem espelho."""
    result = _run_sensor()
    output = result.stdout + result.stderr
    if "schema-sync" in output.lower() and "issue" in output.lower():
        # Drift detectado -> mensagem precisa ter contexto (transitional)
        assert "FE_LEGACY" in output or "FE_CANONICAL" in output or "ADAPTER" in output, (
            "Drift reportado mas sem contexto FE_LEGACY/FE_CANONICAL/ADAPTER.\n"
            f"Output: {output}"
        )
    else:
        assert "OK:" in output, f"Esperado 'OK:' no output. Got: {output}"


def test_schema_sync_no_critical_pairings_broken():
    """Adapter pairings (displayName<->display_name, stageOrder<->order,
    stageType<->type) DEVEM estar consistentes. Sem isso normalizeStageFromHook
    produz undefined."""
    result = _run_sensor()
    output = result.stdout + result.stderr
    # ADAPTER DRIFT = quebra critica do contrato adapter
    assert "ADAPTER DRIFT" not in output, (
        "Adapter pairings broken — normalizeStageFromHook vai retornar undefined.\n"
        f"Output: {output}"
    )
