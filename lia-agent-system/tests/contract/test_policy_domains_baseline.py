"""Contract test: WT-2022 sensor app.domains.policy baseline (warn-only).

Pin baseline 2026-05-21 e garante que sensor roda como script. Quando Phase 2+
migration drop violations < baseline, atualizar BASELINE_EXPECTED. Quando = 0,
promover sensor pra --strict + STRICT no CI.

ADR: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2022-policy-domains-migration.md
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


# Baseline confirmado em 2026-05-21 — 39 distinct AST ImportFrom nodes em ~20 arquivos.
# Reduzir conforme migration avança. Subir = REGRESSION (algum caller novo importou legacy).
BASELINE_EXPECTED = 39

# Tolerancia +0 (qualquer aumento = fail). Quando Phase 2 drop count, baixar BASELINE.
TOLERANCE_UPPER = 0


def _repo_root() -> pathlib.Path:
    """Walk up to find lia-agent-system/ root."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "scripts" / "check_no_app_domains_policy_imports.py").exists():
            return parent
    raise RuntimeError("Could not locate lia-agent-system root")


def _sensor_path() -> pathlib.Path:
    return _repo_root() / "scripts" / "check_no_app_domains_policy_imports.py"


def test_sensor_script_exists():
    """Sensor file existe + e Python valido."""
    p = _sensor_path()
    assert p.exists(), f"Sensor ausente em {p} — WT-2022 ADR exige presence"
    # syntax check
    import ast
    ast.parse(p.read_text())


def test_sensor_runs_in_warn_only_mode():
    """Sensor warn-only retorna exit 0 mesmo com violations existentes."""
    sensor = _sensor_path()
    repo = _repo_root().parent  # workspace root onde 'lia-agent-system/app' existe
    result = subprocess.run(
        [sys.executable, str(sensor)],
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    assert result.returncode == 0, (
        f"Sensor warn-only deve retornar 0 (sai!u: {result.returncode})\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_sensor_strict_mode_fails_when_violations_present():
    """Sensor --strict retorna exit 1 quando ha violations (futura promocao)."""
    sensor = _sensor_path()
    repo = _repo_root().parent
    result = subprocess.run(
        [sys.executable, str(sensor), "--strict"],
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    # 39 baseline > 0, ent strict retorna 1
    assert result.returncode == 1, (
        f"Sensor --strict deve retornar 1 com violations (saiu: {result.returncode})"
    )


def test_baseline_is_pinned_and_not_regressing():
    """Count atual de violations <= BASELINE_EXPECTED + TOLERANCE_UPPER.

    Aumentar count = REGRESSION (novo caller importou legacy domain).
    Diminuir count = OK (migration progrediu) — atualizar BASELINE_EXPECTED.
    """
    sensor = _sensor_path()
    repo = _repo_root().parent
    result = subprocess.run(
        [sys.executable, str(sensor)],
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    out = result.stdout
    # Parse "WT-2022: N imports de app.domains.policy detectados"
    import re
    m = re.search(r"WT-2022:\s+(\d+)\s+imports", out)
    assert m is not None, f"Sensor output formato inesperado:\n{out}"
    current = int(m.group(1))
    upper = BASELINE_EXPECTED + TOLERANCE_UPPER
    assert current <= upper, (
        f"REGRESSION WT-2022: {current} imports de app.domains.policy "
        f"(baseline pinned = {BASELINE_EXPECTED}, tolerance = +{TOLERANCE_UPPER}).\n"
        f"Provavel causa: caller novo importou domain deprecated.\n"
        f"Fix: migrar para app.domains.hiring_policy/ (ver ADR-WT-2022-policy-domains-migration.md)\n"
        f"Output:\n{out}"
    )
    if current < BASELINE_EXPECTED:
        # Soft hint para atualizar baseline (nao fail).
        print(
            f"INFO WT-2022: violations={current} < BASELINE_EXPECTED={BASELINE_EXPECTED}. "
            f"Migration progrediu — atualize BASELINE_EXPECTED neste teste."
        )


def test_canonical_hiring_policy_module_present():
    """Sanity: hiring_policy/ canonical existe (target da migration)."""
    root = _repo_root()
    assert (root / "app" / "domains" / "hiring_policy" / "__init__.py").exists()
    assert (root / "app" / "domains" / "hiring_policy" / "domain.py").exists()
    assert (root / "app" / "domains" / "hiring_policy" / "agents" / "policy_react_agent.py").exists()
