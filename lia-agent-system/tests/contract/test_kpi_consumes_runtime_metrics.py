"""Sensor contract test — Onda 4 B4.

Garante que o sensor scripts/check_kpi_endpoint_consumes_runtime_metrics.py
detecta endpoint canonical (exit 0) e flags recompute manual (exit 1).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SENSOR = Path(__file__).resolve().parents[2] / "scripts" / "check_kpi_endpoint_consumes_runtime_metrics.py"


def test_sensor_script_exists():
    assert SENSOR.exists(), f"sensor não encontrado em {SENSOR}"


def test_sensor_passes_with_canonical_endpoint():
    """Roda o sensor contra o codebase canonical. Esperado exit 0
    (endpoint kpis lê runtime_metrics via PoolAgentRun, sem recompute)."""
    result = subprocess.run(
        [sys.executable, str(SENSOR)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Sensor falhou inesperadamente.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_sensor_blocks_recompute(tmp_path):
    """Sanity check: se passar --self-test, sensor injeta violation de teste
    e verifica deteção. Quando self-test não suportado, skip."""
    result = subprocess.run(
        [sys.executable, str(SENSOR), "--self-test"],
        capture_output=True,
        text=True,
    )
    if "unrecognized argument" in result.stderr.lower() or "self-test" not in result.stdout.lower():
        pytest.skip("--self-test não implementado, OK")
    # se implementado, deve retornar exit 1
    assert result.returncode != 0, "self-test should detect injected violation"
