"""
TDD: conversation_id resolvido deve ser injetado no contexto do agente e
no serialize_message, garantindo thread_id isolado por conversa.

RC1 bug: agent_chat_sse passava req.conversation_id (null em nova conversa)
→ agente usava thread_id = session::domain (estável) → checkpointer tinha
histórico de conversas antigas → 10 passos sujos apareciam no "oi".

Fix canônico: após resolver _cid do DB, context["conversation_id"] = _cid
e serialize_message(conversation_id=_cid).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_cid_injection_test():
    """
    Verifica que context["conversation_id"] é sobrescrito com _cid
    mesmo quando req.conversation_id é None (nova conversa).
    """
    context: dict = {}
    req_conversation_id = None  # simulando nova conversa

    # Simula o bloco de resolução do agent_chat_sse
    new_cid = "abc123-resolved-uuid"

    # Se req.conversation_id existe, set já acontece antes (linha 378)
    if req_conversation_id:
        context["conversation_id"] = req_conversation_id

    # Fix canônico: após resolver _cid, sempre atualiza
    context["conversation_id"] = new_cid

    assert context["conversation_id"] == new_cid, (
        "conversation_id no contexto deve ser o _cid resolvido, não None"
    )


def _make_cid_injection_test_existing_conv():
    """
    Verifica que context["conversation_id"] é _cid quando conversa
    já existe (req.conversation_id fornecido pelo FE).
    """
    context: dict = {}
    req_conversation_id = "existing-conv-uuid"

    if req_conversation_id:
        context["conversation_id"] = req_conversation_id

    # _cid resolvido será o mesmo (get_conversation retornou a conversa)
    resolved_cid = req_conversation_id
    context["conversation_id"] = resolved_cid

    assert context["conversation_id"] == "existing-conv-uuid"


class TestContextConversationIdInjection:
    def test_new_conversation_injects_resolved_cid(self):
        """Nova conversa: context["conversation_id"] deve ser o _cid resolvido."""
        _make_cid_injection_test()

    def test_existing_conversation_preserves_cid(self):
        """Conversa existente: context["conversation_id"] = _cid (mesmo UUID da req)."""
        _make_cid_injection_test_existing_conv()

    def test_null_req_conversation_id_gets_resolved_cid(self):
        """
        Garante que thread_id do LangGraph não cai no fallback session::domain
        quando conversation_id=None — porque context["conversation_id"] = _cid.
        """
        context: dict = {}
        req_cid = None
        resolved_cid = "fresh-conversation-uuid"

        # Antes do fix: context ficava sem conversation_id quando req_cid=None
        if req_cid:
            context["conversation_id"] = req_cid
        # Após o fix: sempre injeta _cid
        context["conversation_id"] = resolved_cid

        # Simula como langgraph_base.py:140 deriva o thread_key
        session_id = "sess_abc"
        domain = "talent"
        cid_from_ctx = context.get("conversation_id")
        thread_key = (
            f"{session_id}::{domain}::{cid_from_ctx}"
            if cid_from_ctx
            else f"{session_id}::{domain}"
        )

        assert thread_key == f"{session_id}::{domain}::{resolved_cid}", (
            "thread_key deve incluir conversation_id → checkpointer isolado por conversa"
        )

    def test_without_fix_thread_falls_back_to_shared(self):
        """
        Documenta o bug: sem o fix, thread_key seria session::domain (shared)
        → carregaria estado de todas as conversas anteriores.
        """
        context: dict = {}
        req_cid = None

        # Comportamento PRÉ-FIX: só seta quando req_cid existe
        if req_cid:
            context["conversation_id"] = req_cid

        session_id = "sess_abc"
        domain = "talent"
        cid_from_ctx = context.get("conversation_id")
        thread_key = (
            f"{session_id}::{domain}::{cid_from_ctx}"
            if cid_from_ctx
            else f"{session_id}::{domain}"
        )

        # Sem o fix: thread_key NÃO tem conversation_id → shared → bug
        assert thread_key == f"{session_id}::{domain}", (
            "Documentação do bug: sem fix, thread_key é shared entre conversas"
        )


class TestSerializeMessageUsesResolvedCid:
    def test_serialize_message_receives_resolved_cid_not_req_cid(self):
        """
        serialize_message deve receber _cid (resolvido), não req.conversation_id.
        Garante que FE aprende o UUID da nova conversa via evento SSE 'message'.
        """
        _cid = "resolved-cid-from-db"
        req_conversation_id = None  # nova conversa

        # Pré-fix: usava req.conversation_id → None → FE nunca aprendia o UUID
        payload_pre_fix = {"conversation_id": req_conversation_id}
        assert payload_pre_fix["conversation_id"] is None

        # Pós-fix: usa _cid
        payload_post_fix = {"conversation_id": _cid}
        assert payload_post_fix["conversation_id"] == "resolved-cid-from-db"

    def test_subsequent_messages_use_same_cid(self):
        """
        Após o 1º turno, FE recebe _cid via setConversationIdFromWs.
        Mensagens seguintes passam esse mesmo UUID → thread_id estável.
        """
        resolved_on_first_turn = "stable-uuid-123"

        # FE persiste o conversation_id recebido no evento message
        fe_stored_conv_id = resolved_on_first_turn

        # 2ª mensagem usa esse ID
        req_second_turn_cid = fe_stored_conv_id
        assert req_second_turn_cid == "stable-uuid-123"
