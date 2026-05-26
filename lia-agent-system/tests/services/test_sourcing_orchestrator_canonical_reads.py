"""Sprint 7B-3a Part 2 — Layers 1+2 canonical reads + signal write tests.

RED tests asserting that:
- orchestrator.process_feedback reads CustomAgent (filtered by category='sourcing')
- signal CREATE/COUNT/LIST use custom_agent_id (não agent_id legacy)
- field access via runtime_metrics for counters
- get_calibration_candidates reads CustomAgent
- legacy SourcingAgent imports gone from orchestrator
"""
from __future__ import annotations

import pathlib

ORCH_PATH = pathlib.Path(__file__).resolve().parents[2] / "app" / "services" / "sourcing_agent_orchestrator.py"


def _src() -> str:
    return ORCH_PATH.read_text()


def test_process_feedback_queries_custom_agent_not_sourcing_agent():
    """Test 1 (Layer 1 read): process_feedback line ~99/103 must select CustomAgent."""
    src = _src()
    # Should NOT have `select(SourcingAgent).where(SourcingAgent.id == agent_id)` standalone
    assert "select(SourcingAgent).where(SourcingAgent.id == agent_id)" not in src, (
        "process_feedback ainda usa select(SourcingAgent) legacy. "
        "Migrar para select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.category == 'sourcing')"
    )
    # Should have CustomAgent + category='sourcing' filter
    assert "CustomAgent.category" in src, (
        "Filtro CustomAgent.category == 'sourcing' ausente — read canonical não migrado"
    )


def test_process_feedback_field_access_via_runtime_metrics():
    """Test 2: counters acessados via runtime_metrics, não como columns diretas."""
    src = _src()
    # Pattern canonical para increment: agent.runtime_metrics["profiles_viewed"] = ... or .get
    # Legacy: agent.profiles_viewed = (agent.profiles_viewed or 0) + 1
    assert "agent.profiles_viewed = (agent.profiles_viewed or 0) + 1" not in src, (
        "profiles_viewed ainda acessado como column direta. "
        "Usar runtime_metrics dict pattern."
    )
    assert "agent.calibration_v += 1" not in src, (
        "calibration_v += 1 ainda como column direta. Migrar pra runtime_metrics."
    )
    assert "runtime_metrics" in src, (
        "Padrão runtime_metrics ausente no orchestrator"
    )


def test_signal_write_uses_custom_agent_id():
    """Test 3 (Layer 2 write): SourcingAgentSignal(...) deve usar custom_agent_id=."""
    src = _src()
    # No occurrences of agent_id=agent_id em construção de Signal
    # The signal block has agent_id=agent_id legacy — should be custom_agent_id=agent_id
    # Find the signal construction
    assert "custom_agent_id=" in src, (
        "Signal write não usa custom_agent_id= canonical"
    )
    # And the legacy EXEMPT marker should be GONE (Part 2 removes)
    assert "SOURCING-SIGNAL-LEGACY-EXEMPT" not in src, (
        "EXEMPT marker Part 1.5 transitional ainda presente — remover em Part 2"
    )


def test_get_calibration_candidates_queries_custom_agent():
    """Test 4 (Layer 1 read): get_calibration_candidates select CustomAgent."""
    src = _src()
    assert "select(SourcingAgent).where(SourcingAgent.id == agent_id)" not in src
    # Look for the multi-line stmt around line 202
    assert "stmt = select(SourcingAgent)" not in src, (
        "get_calibration_candidates ainda monta stmt via SourcingAgent legacy"
    )


def test_get_agent_timeline_signals_via_custom_agent_id():
    """Test 5 (Layer 2 read): timeline filter SourcingAgentSignal.custom_agent_id."""
    src = _src()
    assert ".where(SourcingAgentSignal.agent_id == agent_id)" not in src, (
        "Signal LIST filter ainda usa agent_id legacy"
    )
    assert "SourcingAgentSignal.custom_agent_id" in src, (
        "Signal LIST/COUNT canonical filter custom_agent_id ausente"
    )


def test_no_legacy_sourcing_agent_import_in_orchestrator_reads():
    """Bonus: imports de SourcingAgent (model) — só create_agent (Layer 3) pode reter.

    Layer 1+2 sites devem ter sumido. Validation que esta sub-sprint moveu o agulha.
    Após Part 2 esperar ~1-2 imports remanescentes (create_agent + opcional shim),
    enquanto pre-Part 2 são 5.
    """
    src = _src()
    legacy_count = src.count("from lia_models.sourcing_agent import SourcingAgent")
    # Pre-Part 2: 5 sites. Post-Part 2 Layer 1+2: deve cair pra <=2 (apenas create_agent L55)
    assert legacy_count <= 2, (
        f"Esperado <=2 imports SourcingAgent (apenas create_agent Layer 3); encontrado {legacy_count}"
    )
