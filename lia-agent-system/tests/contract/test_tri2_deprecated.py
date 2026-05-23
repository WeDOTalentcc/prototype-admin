"""
Tri-2 sensores DEPRECATED legítimos — top 5 P1 audit-before-recovery.

WHY THIS SENSOR EXISTS
======================
Recovery Tri-2 (2026-05-23) auditou top 5 arquivos REGRESSED do RAM. Audit
revelou padrão Recovery-#6 / #10 / #2: 4 dos 5 são DEPRECATED legítimos
coordenados, NÃO regressed:

1. ``settings_progress_repository.py`` — 3 helpers ``count_active_*``
   removidos. Endpoint ``settings_progress.py`` também foi refatorado
   (não chama mais). Cleanup coordenado.
2. ``teams_proactivity_engine.py`` — 2 helpers (broadcast_to_channels +
   _get_channel_refs_for_company) removidos. Único caller é test orphan
   ``tests/integration/test_teams_w9_1_group_channel.py``.
3. ``automation_tools.py`` — ``register_automation_tools`` removido.
   PRE caller (``app/tools/__init__.py``) também foi atualizado e não
   chama mais. Tool registry simplificado.
4. ``market_benchmark_service.py`` — ``_apply_salary_caps`` (private
   helper, zero external callers ever). Provavelmente inlined em refactor.

Apenas ``context_management.py`` foi REGRESSED real (Tri-2 #1 commit).

Esse sensor valida CONSISTÊNCIA dos DEPRECATED — se algum caller orphan
re-aparecer no codebase, sinaliza regressão arquitetural (feature meio-deletada).

Pattern: BLOCKING.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _grep_callers(symbol: str, paths: list[str]) -> list[str]:
    """grep -rln symbol em paths, excluindo __pycache__ e próprio sensor file."""
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["grep", "-rln", f"\\b{symbol}\\b", *paths, "--include=*.py"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    # Self-exclusion: o próprio sensor file menciona os símbolos no docstring/
    # assertion messages — não é caller real.
    return [
        line for line in result.stdout.split("\n")
        if line.strip()
        and "__pycache__" not in line
        and "test_tri2_deprecated.py" not in line
    ]


def test_settings_progress_helpers_no_orphan_callers():
    """
    settings_progress_repository.count_active_* helpers foram DEPRECATED.
    Endpoint ``app/api/v1/settings_progress.py`` não chama mais.

    Onda 4.1 (2026-05-23): test orphan ``test_settings_progress_coverage.py``
    DELETADO (8 tests falhando em CI desde merge incident). Zero callers
    esperados daqui pra frente.
    """
    for sym in ["count_active_alert_configs", "count_active_integrations", "count_active_policies"]:
        callers = _grep_callers(sym, ["app/", "tests/"])
        assert not callers, (
            f"DEPRECATED helper {sym} tem callers orphan: {callers}\n"
            "Endpoint deveria ter sido refatorado consistentemente. Restaurar "
            "helpers OU atualizar callers."
        )


def test_teams_proactivity_helpers_no_orphan_callers():
    """
    broadcast_to_channels + _get_channel_refs_for_company DEPRECATED.

    Onda 4.1 (2026-05-23): test orphan ``test_teams_w9_1_group_channel.py``
    DELETADO. Zero callers esperados.
    """
    for sym in ["broadcast_to_channels", "_get_channel_refs_for_company"]:
        callers = _grep_callers(sym, ["app/", "tests/"])
        assert not callers, (
            f"DEPRECATED helper {sym} tem callers orphan: {callers}\n"
            "Reaparecimento = regressão coordenada."
        )


def test_register_automation_tools_deprecated():
    """
    ``register_automation_tools`` DEPRECATED. ``app/tools/__init__.py``
    foi simplificado e não importa mais. Zero callers esperados.
    """
    callers = _grep_callers("register_automation_tools", ["app/", "tests/"])
    assert not callers, (
        f"DEPRECATED `register_automation_tools` tem callers orphan: {callers}\n"
        "Tool registry foi simplificado em refactor pos-incident. "
        "Restaurar função OU atualizar callers."
    )


def test_apply_salary_caps_deprecated():
    """
    ``_apply_salary_caps`` private helper DEPRECATED. Era usado APENAS por
    self (market_benchmark_service). Provavelmente inlined.
    """
    callers = _grep_callers("_apply_salary_caps", ["app/", "tests/"])
    assert not callers, (
        f"DEPRECATED `_apply_salary_caps` tem callers orphan: {callers}\n"
        "Era private helper (self-only). Refactor inlined-o. "
        "Reaparecimento = regressão."
    )
