"""
R-003.1: garante que sites previamente silent agora loggam.

Sensor harness: detecção via inspeção estática de source code +
verificação que sites compliance usam logger.warning (nunca silent).
"""
import inspect
import logging
import re

import pytest


def _count_logged_excepts(src: str) -> int:
    """Conta blocos `except <Type>:` cuja primeira linha não-vazia é logger.* ."""
    pattern = re.compile(
        r"except\s+[A-Za-z_]\w*(?:\s+as\s+\w+)?:\s*\n\s*(?:#[^\n]*\n\s*)?logger\.(?:debug|info|warning|error|critical)",
    )
    return len(pattern.findall(src))


def _count_silent_excepts(src: str) -> int:
    """Conta blocos `except <Type>:` cuja primeira linha não-vazia é pass/return/continue (sem logger acima)."""
    pattern = re.compile(
        r"except\s+[A-Za-z_]\w*(?:\s+as\s+\w+)?:\s*\n\s*(?:pass|return|continue)\b",
    )
    return len(pattern.findall(src))


def test_action_executor_utils_logs_swallows():
    """Sites em action_executor/utils.py loggam via logger.* nos 3 except Exception."""
    from app.orchestrator.action_executor import utils as utils_module
    src = inspect.getsource(utils_module)
    logged = _count_logged_excepts(src)
    assert logged >= 3, (
        f"action_executor/utils.py deveria ter pelo menos 3 except com logger.*; encontrou {logged}"
    )


def test_pipeline_actions_logs_dateutil_swallow():
    """pipeline_actions.py:82 loggar dateutil parse failure."""
    from app.orchestrator.action_handlers import pipeline_actions
    src = inspect.getsource(pipeline_actions)
    assert "dateutil.parse" in src or "logger.debug" in src
    logged = _count_logged_excepts(src)
    assert logged >= 1, f"pipeline_actions.py deveria ter pelo menos 1 except logged; encontrou {logged}"


def test_main_orchestrator_logs_persist_and_summary_swallows():
    """main_orchestrator.py:395 e :1004 usam logger.warning (perda crítica)."""
    from app.orchestrator.execution import main_orchestrator
    src = inspect.getsource(main_orchestrator)
    # Buscar warnings específicos
    assert "_persist_response failed" in src, "site 395 deveria loggar _persist_response failure"
    assert "update_summary failed" in src, "site 1004 deveria loggar update_summary failure"


def test_orchestrator_logs_summary_swallow():
    """orchestrator.py:329 usa logger.warning para update_summary."""
    from app.orchestrator.legacy import orchestrator
    src = inspect.getsource(orchestrator)
    assert "update_summary failed" in src, "site 329 deveria loggar update_summary failure"


def test_cascaded_router_logs_routing_decisions():
    """cascaded_router.py:454, 680, 758 — 3 sites de routing."""
    from app.orchestrator.routing import cascaded_router
    src = inspect.getsource(cascaded_router)
    # Esperado pelo menos 3 except logged adicionais aos pre-existentes
    logged = _count_logged_excepts(src)
    assert logged >= 3, f"cascaded_router.py deveria ter >=3 except logged; encontrou {logged}"


def test_fairness_guard_swallows_log_warning():
    """Compliance swallows em fairness_guard usam warning (não silent) — LGPD-critical."""
    from app.shared.compliance import fairness_guard
    src = inspect.getsource(fairness_guard)
    # Conta blocos `except` seguidos de logger
    log_in_except = re.findall(
        r"except [A-Z]\w+(?:\s+as\s+\w+)?:\s*\n\s*logger\.(warning|error)",
        src,
    )
    assert len(log_in_except) >= 3, (
        f"fairness_guard deveria ter pelo menos 3 except com logger.warning/error; "
        f"encontrou {len(log_in_except)}"
    )


def test_scoring_safeguards_logs_compliance_swallows():
    """scoring_safeguards.py:152, 162 — coro.close() failures usam logger.warning."""
    from app.shared.compliance import scoring_safeguards
    src = inspect.getsource(scoring_safeguards)
    log_in_except = re.findall(
        r"except [A-Z]\w+(?:\s+as\s+\w+)?:\s*\n\s*logger\.(warning|error)",
        src,
    )
    assert len(log_in_except) >= 2, (
        f"scoring_safeguards deveria ter pelo menos 2 except com logger.warning/error; "
        f"encontrou {len(log_in_except)}"
    )
