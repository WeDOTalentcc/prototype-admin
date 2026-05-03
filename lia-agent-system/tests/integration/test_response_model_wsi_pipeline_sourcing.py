"""R-005 — pin G2 sensor: WSI/pipeline/sourcing routers livres de violacoes.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-201 / R-005.

Achado: o G2 sensor (scripts/check_response_models.py) ja reporta 0 violacoes
para app/api/v1/wsi/, pipeline*.py e sourcing*.py em origin/main. R-005 e'
em essencia um pin de regressao desse estado — qualquer PR que adicione
endpoints nesses paths sem response_model agora falha o teste + sensor G2.

Os ~60 endpoints com response_model faltando em OUTROS paths (custom_agents.py,
digital_twins.py, etc.) ficam como debito Sprint 2/3 (escopo fora do brief).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_g2_sensor() -> tuple[int, str]:
    """Roda scripts/check_response_models.py e retorna (returncode, stdout)."""
    result = subprocess.run(
        ["python3", "scripts/check_response_models.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode, result.stdout + result.stderr


def test_g2_sensor_zero_violations_in_wsi_pipeline_sourcing() -> None:
    """R-005: routers em wsi/pipeline/sourcing nao podem ter @router sem response_model.

    Pin de regressao: estado atual e' 0 violacoes nesses paths (origin/main).
    Qualquer regressao futura aciona este teste alem do G2 sensor.
    """
    _rc, output = _run_g2_sensor()
    target_prefixes = (
        "  app/api/v1/wsi/",
        "  app/api/v1/pipeline",  # pipeline.py, pipeline_*.py
        "  app/api/v1/sourcing",  # sourcing.py, sourcing_*.py
        "  app/api/v1/recruitment_stages/",  # stages_pipeline.py
    )
    offenders = [line for line in output.splitlines() if line.startswith(target_prefixes)]
    assert not offenders, (
        "R-005: regressao em response_model dos routers WSI/pipeline/sourcing:\n"
        + "\n".join(offenders[:20])
        + ("\n... e mais" if len(offenders) > 20 else "")
        + "\nFix: adicionar response_model=YourSchema em cada @router decorator."
    )


def test_g2_sensor_script_exists_and_runs() -> None:
    """R-005: confirma que o sensor G2 esta presente e executavel."""
    sensor = REPO_ROOT / "scripts" / "check_response_models.py"
    assert sensor.exists(), f"R-005: sensor G2 ausente em {sensor}"
    rc, output = _run_g2_sensor()
    # rc pode ser 0 (clean) ou 1 (violacoes em outros paths) — ambos validos.
    assert rc in (0, 1), f"R-005: sensor G2 retornou codigo inesperado: rc={rc}"
    assert (
        "Missing response_model" in output or "OK" in output or rc == 0
    ), f"R-005: output do sensor G2 inesperado: {output[:500]}"
