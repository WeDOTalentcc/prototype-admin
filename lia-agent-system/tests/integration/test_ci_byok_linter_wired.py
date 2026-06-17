"""R-009 — verifica que CI workflow contem step bloqueante do BYOK linter.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-325 / R-009.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    assert CI_PATH.exists(), f"CI workflow nao encontrado em {CI_PATH}"
    with CI_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _all_steps(workflow: dict) -> list[dict]:
    steps: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps", []) or []:
            steps.append(step)
    return steps


def _find_byok_steps(workflow: dict) -> list[dict]:
    matches: list[dict] = []
    for step in _all_steps(workflow):
        run = (step.get("run") or "")
        if "scripts/check_llm_factory_enforcement.py" in run:
            matches.append(step)
    return matches


def test_ci_workflow_contains_byok_linter_step() -> None:
    workflow = _load_ci()
    matches = _find_byok_steps(workflow)
    assert matches, (
        "R-009: CI workflow precisa rodar python scripts/check_llm_factory_enforcement.py "
        "em pelo menos um step. Adicione ao job 'lint' ou crie job dedicado."
    )


def test_byok_linter_step_is_blocking() -> None:
    """Step do BYOK linter NAO pode ter || true nem continue-on-error: true."""
    workflow = _load_ci()
    matches = _find_byok_steps(workflow)
    assert matches, "Pre-requisito: step do BYOK linter precisa existir (test_ci_workflow_contains_byok_linter_step)"

    for step in matches:
        run = step.get("run") or ""
        assert "|| true" not in run, (
            f"R-009: step do BYOK linter (name={step.get('name')!r}) tem '|| true' — "
            "remova para tornar o step bloqueante. CI deve falhar em violacao."
        )
        assert step.get("continue-on-error", False) is not True, (
            f"R-009: step do BYOK linter (name={step.get('name')!r}) tem continue-on-error: true — "
            "remova para tornar o step bloqueante."
        )


def test_byok_linter_runs_in_pull_request() -> None:
    """O job que contem o BYOK linter precisa rodar em pull_request (defesa pre-merge)."""
    workflow = _load_ci()
    on_block = workflow.get(True) or workflow.get("on") or {}
    pr_block = on_block.get("pull_request") if isinstance(on_block, dict) else None
    assert pr_block is not None, (
        "R-009: workflow precisa estar configurado para rodar em pull_request."
    )
