"""TDD (2026-06-13): effective_domain_for_scope — pina que o card "Foco em Vaga"
do chat usa domain_hint explícito do FE como scope hint no caminho federado.

Raiz do fix: no caminho LIA_FEDERATED_PRIMARY, CascadedRouter é pulado e
resolved_domain retorna "auto". O scope_for_context recebia "auto" → GLOBAL
em vez de JOB_TABLE. Fix: preferir metadata.domain_hint quando presente.

view_context.py tem zero deps de app — import direto via importlib para
evitar cascade do app.orchestrator.__init__ (CascadedRouter → lia_pii/lia_llm).
"""
from __future__ import annotations
import importlib.util
import sys
import types


def _load_view_context():
    """Carrega view_context.py diretamente, sem acionar app.orchestrator.__init__."""
    # Stub packages para impedir __init__ cascade
    for pkg in ["app", "app.orchestrator", "app.orchestrator.context"]:
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)
    import pathlib
    _root = pathlib.Path(__file__).parents[3] / "lia-agent-system" / "app" / "orchestrator" / "context" / "view_context.py"
    spec = importlib.util.spec_from_file_location(
        "app.orchestrator.context.view_context", str(_root)
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["app.orchestrator.context.view_context"] = mod
    spec.loader.exec_module(mod)
    return mod


_vc = _load_view_context()
effective_domain_for_scope = _vc.effective_domain_for_scope


# ── RED → GREEN (2026-06-13) ──────────────────────────────────────────────────

def test_job_hint_wins_over_auto():
    """Foco em Vaga + caminho federado resolve job_management, não auto."""
    ctx = {"metadata": {"domain_hint": "job_management", "source": "rail_a"}}
    assert effective_domain_for_scope(ctx, "auto") == "job_management"


def test_talent_hint_wins_over_recruiter_assistant():
    """Foco em Candidato resolve talent_pool, não recruiter_assistant."""
    ctx = {"metadata": {"domain_hint": "talent_pool", "source": "rail_a"}}
    assert effective_domain_for_scope(ctx, "recruiter_assistant") == "talent_pool"


def test_no_hint_falls_back_to_resolved():
    """Conversa Geral (sem domain_hint) preserva resolved_domain."""
    ctx = {"metadata": {"source": "rail_a"}}
    assert effective_domain_for_scope(ctx, "job_management") == "job_management"


def test_none_context_falls_back_to_resolved():
    """Sem contexto (fallback defensivo) preserva resolved_domain."""
    assert effective_domain_for_scope(None, "talent_pool") == "talent_pool"


def test_empty_hint_falls_back_to_resolved():
    """domain_hint vazio não é válido — cai no resolved_domain."""
    ctx = {"metadata": {"domain_hint": "", "source": "rail_a"}}
    assert effective_domain_for_scope(ctx, "job_management") == "job_management"


def test_conversa_geral_no_hint_gives_none():
    """Sem hint e sem domain resolve None → scope_for_context defaulta GLOBAL."""
    ctx = {"metadata": {"source": "rail_a"}}
    assert effective_domain_for_scope(ctx, None) is None


def test_both_none_gives_none():
    assert effective_domain_for_scope(None, None) is None
