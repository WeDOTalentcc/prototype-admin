"""
Contract sensor — job_actions.py dispatcher + intents_config.py trio sync.

WHY THIS SENSOR EXISTS
======================
Audit Recovery #5 (2026-05-23) — mesmo padrão Recovery #4: merge incident
02361f41c removeu 3 peças coordenadas:
  - 2 helpers em ``job_actions.py`` (_suggest_salary, _generate_jd_direct)
  - 2 ``elif`` branches em ``execute_job_action``
  - 2 entries em ``intents_config.ACTIONABLE_INTENTS`` (sugerir_salario, gerar_jd)

Pattern: BLOCKING. Trio sync canonical.
"""
from __future__ import annotations

import inspect
import re

from app.orchestrator.action_executor import intents_config
from app.orchestrator.action_handlers import job_actions


# 7 actions canonical do dispatcher pós-Recovery #5.
_CANONICAL_JOB_ACTIONS = {
    "pause_job",
    "close_job",
    "duplicate_job",
    "reopen_job",
    "set_job_urgent",
    "suggest_salary",
    "generate_jd_direct",
}


def _extract_dispatched_action_ids() -> set[str]:
    src = inspect.getsource(job_actions.execute_job_action)
    return set(re.findall(r'action_id\s*==\s*"([^"]+)"', src))


def _extract_intents_config_job_action_ids() -> set[str]:
    return {
        entry["action_id"]
        for entry in intents_config.ACTIONABLE_INTENTS.values()  # type: ignore[attr-defined]
        if entry.get("domain_id") == "job_management"
        and "action_id" in entry
    }


def test_dispatcher_handles_all_canonical_actions():
    """execute_job_action despacha exatamente as 7 actions canonical."""
    dispatched = _extract_dispatched_action_ids()
    assert dispatched == _CANONICAL_JOB_ACTIONS, (
        f"Dispatcher action_ids = {sorted(dispatched)}\n"
        f"Canonical esperado = {sorted(_CANONICAL_JOB_ACTIONS)}\n"
        f"Diff: missing={_CANONICAL_JOB_ACTIONS - dispatched}, "
        f"extra={dispatched - _CANONICAL_JOB_ACTIONS}"
    )


def test_intents_config_lists_recovered_actions():
    """Entries Recovery #5 restauradas devem estar em ACTIONABLE_INTENTS."""
    registered = _extract_intents_config_job_action_ids()
    recovered = {"suggest_salary", "generate_jd_direct"}
    assert recovered.issubset(registered), (
        f"intents_config missing Recovery #5 action_ids: "
        f"{recovered - registered}\n"
        f"Job-domain registered: {sorted(registered)}"
    )


def test_helpers_exist_for_all_dispatched_actions():
    """Cada action_id despachado tem helper `_<action_id>` no módulo."""
    dispatched = _extract_dispatched_action_ids()
    for action in dispatched:
        helper_name = f"_{action}"
        assert hasattr(job_actions, helper_name), (
            f"Dispatcher referencia '{action}' mas helper `{helper_name}` "
            "não existe em job_actions module."
        )
