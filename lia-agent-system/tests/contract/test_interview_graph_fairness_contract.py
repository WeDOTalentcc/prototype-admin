"""
Contract sensor — InterviewGraph FairnessGuard wrappers (output check).

WHY THIS SENSOR EXISTS
======================
Audit Recovery #8 (2026-05-23) descobriu que o merge incident 02361f41c
removeu silenciosamente o FairnessGuard OUTPUT check em interview scheduling:
  - ``_fairness_check_and_regenerate`` (top-level function)
  - ``_wrap_node_with_fairness`` (node wrapper)
  - ``_apply_fairness_guard_to_response`` (post-graph safety net)
  - ``_FAIRNESS_GUARDED_NODES`` (constant — 4 nodes que produzem texto)
  - Integration em ``_build_langgraph`` (wrap nodes)
  - Integration em ``invoke`` (post-graph check)

22 dias sem block em output. Compliance gap CRÍTICO:
- EU AI Act Art. 9 (Risk Management) + Art. 12 (Record-keeping pra IA high-risk)
- LGPD Art. 20 (direito de explicação de decisão automatizada)
- Sistema de scheduling podia produzir texto discriminatório pra candidatos
  sem block.

Input check (mensagem entrando do candidato) sempre esteve OK em
``interview_scheduling_nodes.py`` — mas OUTPUT check (mensagem saindo da IA)
foi removido. Compliance exige AMBOS.

Pattern: BLOCKING. Output fairness NUNCA pode regredir.
"""
from __future__ import annotations

import inspect

import importlib

# Workaround: ``from app.domains.interview_scheduling.agents import interview_graph``
# importa a SINGLETON INSTANCE (last line do módulo: ``interview_graph = InterviewGraph()``)
# em vez do próprio módulo. Usamos importlib pra forçar referência ao module.
interview_graph = importlib.import_module(
    "app.domains.interview_scheduling.agents.interview_graph"
)


def test_fairness_check_and_regenerate_exists():
    """Função top-level canonical de fairness check deve existir."""
    assert hasattr(interview_graph, "_fairness_check_and_regenerate"), (
        "_fairness_check_and_regenerate ausente. Compliance gap crítico — "
        "EU AI Act Art. 12 + LGPD Art. 20. Restaurar."
    )
    assert callable(interview_graph._fairness_check_and_regenerate), (
        "_fairness_check_and_regenerate não é callable."
    )


def test_wrap_node_with_fairness_exists():
    """Decorator-style wrapper canonical pra nodes."""
    assert hasattr(interview_graph, "_wrap_node_with_fairness"), (
        "_wrap_node_with_fairness ausente. Sem ele, FairnessGuard não é "
        "aplicado em outputs dos nodes."
    )


def test_fairness_guarded_nodes_constant_exists():
    """Lista canonical de nodes que produzem texto candidate-bound."""
    assert hasattr(interview_graph, "_FAIRNESS_GUARDED_NODES"), (
        "_FAIRNESS_GUARDED_NODES constant ausente. Sem ela, _build_langgraph "
        "não sabe quais nodes envolver com fairness wrap."
    )
    guarded = interview_graph._FAIRNESS_GUARDED_NODES  # type: ignore[attr-defined]
    assert isinstance(guarded, tuple), "_FAIRNESS_GUARDED_NODES deve ser tuple."
    assert len(guarded) >= 4, (
        f"_FAIRNESS_GUARDED_NODES tem {len(guarded)} nodes; canonical mínimo: 4 "
        "(collector, validator, executor, response_planner)."
    )


def test_build_langgraph_wraps_guarded_nodes():
    """``_build_langgraph`` deve invocar ``_wrap_node_with_fairness``."""
    src = inspect.getsource(interview_graph.InterviewGraph._build_langgraph)  # type: ignore[attr-defined]
    assert "_wrap_node_with_fairness" in src, (
        "_build_langgraph NÃO usa _wrap_node_with_fairness. "
        "Output fairness NÃO está sendo aplicado nos nodes — gap compliance."
    )
    assert "_FAIRNESS_GUARDED_NODES" in src, (
        "_build_langgraph não consulta _FAIRNESS_GUARDED_NODES."
    )


def test_invoke_calls_apply_fairness_guard_to_response():
    """``invoke`` deve chamar ``_apply_fairness_guard_to_response`` post-graph."""
    src = inspect.getsource(interview_graph.InterviewGraph.invoke)  # type: ignore[attr-defined]
    assert "_apply_fairness_guard_to_response" in src, (
        "InterviewGraph.invoke NÃO chama _apply_fairness_guard_to_response. "
        "Defense-in-depth post-graph removida. Restaurar."
    )


def test_fairness_check_imports_canonical_middleware():
    """Função deve usar ``fairness_guard_middleware.check_fairness`` canonical."""
    src = inspect.getsource(interview_graph._fairness_check_and_regenerate)  # type: ignore[attr-defined]
    assert "fairness_guard_middleware" in src, (
        "_fairness_check_and_regenerate não importa fairness_guard_middleware. "
        "Canonical SSOT do FairnessGuard."
    )
    assert "audit_service" in src, (
        "_fairness_check_and_regenerate não invoca audit_service.log_decision. "
        "Block decisions DEVEM ser auditadas (EU AI Act Art. 12)."
    )
