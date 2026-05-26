"""Sprint 7C Part 1 v2 — sensor #10 dispatch_has_audit baseline test.

Garante que o sensor canonical:
- detecta nosso novo dispatch_pool_agent_assignment_task com audit (OK)
- exit 0 (warn-only Part 1 v2; promote BLOCKING após Part 1.5)
- output útil pra LLM (file:line + instrução de fix)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


SENSOR = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_dispatch_has_audit.py"


def test_sensor_exists_and_executable():
    assert SENSOR.exists(), f"Sensor não encontrado: {SENSOR}"
    assert SENSOR.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")


def test_sensor_new_dispatch_pool_agent_has_audit():
    """Novo dispatch_pool_agent_assignment_task NÃO aparece em violations."""
    proc = subprocess.run(
        ["python3", str(SENSOR)],
        capture_output=True,
        text=True,
        cwd=SENSOR.parent.parent.parent,
    )
    # warn-only sempre exit 0 nesta sprint
    assert proc.returncode == 0
    # nosso novo dispatch tem audit canonical, não deve aparecer
    assert "dispatch_pool_agent_assignment_task" not in proc.stdout
