"""Sensor de federacao A2 (2026-06-04): zero handoff-morto.

Todo delegate_to_<dominio> do supervisor DEVE mapear a um agente REGISTRADO no
AgentRegistry. Handoff pra dominio inexistente = tool que sempre falha (balde 2
mal-feito). Carrega o registry em runtime (lento ~30s, roda 1x).

Se falhar: ou o agente do dominio sumiu do registry, ou DOMAINS em
app/orchestrator/supervisor/handoff_tools.py tem uma key errada. Corrija a key OU
restaure o @register_agent do dominio.
"""
import pytest


def test_no_dead_handoffs():
    from app.orchestrator.supervisor.handoff_tools import DOMAINS
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    from app.shared.agents.agent_registry import AgentRegistry

    _ensure_agents_loaded()
    registry = AgentRegistry()
    missing = [d for d in DOMAINS if not registry.is_registered(d)]
    assert missing == [], (
        f"[FED] handoffs sem agente registrado (mortos): {missing}. "
        f"Corrija a key em handoff_tools.DOMAINS ou restaure o @register_agent do dominio."
    )
