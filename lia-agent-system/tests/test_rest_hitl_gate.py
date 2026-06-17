"""
Sensor — gate HITL dormente no path REST do modal Mover-para (transition/execute).
Camada 2 (Unitário BE — pytest, sem DB).

Contexto (AUD-4, auditoria 2026-06-10): o endpoint transition/execute dispara
feedback ao candidato sem gate fail-closed. O mecanismo de chat (_hitl_approved
ContextVar) NAO serve aqui (transporte REST nunca seta o ContextVar). O gate
correto para REST usa um campo explicito de aprovacao no request.

Invariantes:
- Default (LIA_HITL_GATE off) -> rest_hitl_blocks SEMPRE False (zero regressao).
- Gate on + acao lia_auto + nao aprovado -> bloqueia (segura dispatch).
- Gate on + aprovado -> nao bloqueia.
- Gate on + acao != lia_auto (just_move/manual) -> nao bloqueia (nada a disparar).
"""
import pytest

from app.shared.hitl.hitl_approval_context import rest_hitl_blocks


class TestRestHitlBlocks:

    def test_gate_off_never_blocks(self, monkeypatch):
        monkeypatch.delenv("LIA_HITL_GATE", raising=False)
        assert rest_hitl_blocks(action="lia_auto", approved=False) is False
        assert rest_hitl_blocks(action="lia_auto", approved=True) is False

    def test_gate_on_blocks_unapproved_lia_auto(self, monkeypatch):
        monkeypatch.setenv("LIA_HITL_GATE", "on")
        assert rest_hitl_blocks(action="lia_auto", approved=False) is True

    def test_gate_on_allows_approved(self, monkeypatch):
        monkeypatch.setenv("LIA_HITL_GATE", "on")
        assert rest_hitl_blocks(action="lia_auto", approved=True) is False

    def test_gate_on_ignores_non_dispatch_actions(self, monkeypatch):
        monkeypatch.setenv("LIA_HITL_GATE", "on")
        assert rest_hitl_blocks(action="just_move", approved=False) is False
        assert rest_hitl_blocks(action="manual", approved=False) is False
        assert rest_hitl_blocks(action="", approved=False) is False
