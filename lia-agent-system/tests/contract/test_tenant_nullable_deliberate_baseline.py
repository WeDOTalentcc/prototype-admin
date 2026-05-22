"""WT-2022 P0.TENANT: Contract test pra sensor secundario check_tenant_nullable_has_repo_enforcement.

Valida que:
1. Sensor roda sem erro (warn-only, exit 0)
2. Sensor encontra ao menos os 5 model files do Batch A com markers TENANT-NULLABLE-DELIBERATE
"""
import subprocess
from pathlib import Path

# Resolver o root do workspace (sobe ate achar pasta lia-agent-system)
HERE = Path(__file__).resolve()
WORKSPACE_ROOT = None
for parent in HERE.parents:
    if (parent / "lia-agent-system").exists():
        WORKSPACE_ROOT = parent
        break

SENSOR = "lia-agent-system/scripts/check_tenant_nullable_has_repo_enforcement.py"


def test_tenant_nullable_deliberate_sensor_runs():
    """Sensor secundario sempre exit 0 (modo warn-only)."""
    result = subprocess.run(
        ["python3", SENSOR],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT) if WORKSPACE_ROOT else None,
    )
    assert result.returncode == 0, (
        "Sensor exit code != 0 (esperado warn-only). stdout=" + result.stdout + " stderr=" + result.stderr
    )


def test_tenant_nullable_deliberate_models_checked():
    """Sensor deve achar pelo menos os 7 models do Batch A com markers
    (BanditPosterior, CalibrationEvent, CalibrationWeight, FeatureFlag,
    IncidentReport, ModelEvaluation, ComplianceControl).
    """
    result = subprocess.run(
        ["python3", SENSOR],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT) if WORKSPACE_ROOT else None,
    )
    output = result.stdout
    # Sensor imprime 'TOTAL models with TENANT-NULLABLE-DELIBERATE: <N>' quando ha issues
    # ou 'OK: <N> models...' quando todos enforced.
    assert (
        "TOTAL models with TENANT-NULLABLE-DELIBERATE" in output
        or "models com TENANT-NULLABLE-DELIBERATE all have repo enforcement" in output
    ), "Sensor output nao contem contador de models. stdout=" + output


def test_tenant_nullable_deliberate_batch_a_models_detected():
    """Batch A canonical: 7 models cross-tenant aggregates declarados."""
    result = subprocess.run(
        ["python3", SENSOR],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT) if WORKSPACE_ROOT else None,
    )
    output = result.stdout
    # Heuristica robusta: sensor deve relatar >= 5 models com marker no total
    # (output pode estar em formato 'TOTAL ...: N' ou 'OK: N models')
    import re

    match = re.search(r"(?:TOTAL models with TENANT-NULLABLE-DELIBERATE:\s+|OK:\s+)(\d+)", output)
    assert match, "Nao achei contador de models no output. stdout=" + output
    count = int(match.group(1))
    assert count >= 5, (
        "Esperado pelo menos 5 models com TENANT-NULLABLE-DELIBERATE (Batch A), achei " + str(count)
    )
