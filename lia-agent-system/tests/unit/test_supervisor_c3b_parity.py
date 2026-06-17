"""Paridade de governanca C3B (2026-06-06): a trilha supervisor (ramo orch do
drain SSE) aplica post_compliance (FactChecker + audit LGPD da saida), igual ao
ramo agente. MainOrchestrator faz FairnessGuard no input mas nao post_compliance
no output -> sem isto a saida do supervisor escapa do factcheck+audit.
"""
from __future__ import annotations


def test_supervisor_orch_branch_applies_post_compliance():
    s = open("app/api/v1/agent_chat_sse.py", encoding="utf-8").read()
    i_orch = s.find('_orch_result") is not None')
    assert i_orch > 0, "ramo orch nao encontrado"
    i_frames = s.find("_orchestrator_result_to_frames", i_orch)
    orch_branch = s[i_orch:i_frames]
    assert "post_compliance" in orch_branch, (
        "ramo supervisor (orch) precisa aplicar post_compliance ANTES de "
        "serializar -> paridade de governanca/audit LGPD com o ramo agente."
    )
