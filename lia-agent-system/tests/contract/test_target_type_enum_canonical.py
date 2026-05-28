"""Onda 2 B4 — sensor check_target_type_enum_canonical.py contract tests.

3 testes obrigatórios:
1. Enum tem os 4 valores canonical
2. Não há definições duplicadas (introspection AST)
3. Sensor check_target_type_enum_canonical.py exit 0
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR = REPO_ROOT / "scripts" / "check_target_type_enum_canonical.py"


def test_canonical_enum_has_exactly_four_values():
    """DeploymentTargetType deve ter EXATOS 4 valores canonical."""
    from lia_models.agent_deployment import DeploymentTargetType

    values = {v.value for v in DeploymentTargetType}
    assert values == {"job", "talent_pool", "pipeline_stage", "candidate_list"}, (
        f"DeploymentTargetType drift: {values}"
    )


def test_no_duplicate_target_type_classes_in_app_layer():
    """Não há classe Enum redeclarando target_type canonical em app/ ou libs/."""
    import ast

    canonical_values = {"job", "talent_pool", "pipeline_stage", "candidate_list"}
    canonical_path = (
        REPO_ROOT / "libs" / "models" / "lia_models" / "agent_deployment.py"
    )

    duplicates: list[tuple[str, str]] = []
    scan_dirs = [REPO_ROOT / "app", REPO_ROOT / "libs"]
    for base in scan_dirs:
        for path in base.rglob("*.py"):
            if "/__pycache__/" in path.as_posix():
                continue
            if path == canonical_path:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                values: set[str] = set()
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        if (
                            len(stmt.targets) == 1
                            and isinstance(stmt.targets[0], ast.Name)
                            and isinstance(stmt.value, ast.Constant)
                            and isinstance(stmt.value.value, str)
                        ):
                            values.add(stmt.value.value)
                overlap = values & canonical_values
                if len(overlap) >= 2:
                    duplicates.append((path.as_posix(), node.name))

    assert duplicates == [], (
        f"Drift detected — classes redeclaram target_type canonical: {duplicates}"
    )


def test_sensor_exits_zero():
    """O sensor B4 deve passar em baseline 0 (canonical estavel)."""
    assert SENSOR.exists(), f"Sensor não encontrado: {SENSOR}"
    result = subprocess.run(
        [sys.executable, str(SENSOR)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"Sensor falhou (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
