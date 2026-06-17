"""Sensor — Bug 1: path REST (/api/v1/chat → ChatAdapter → MainOrchestrator)
deve propagar o texto CRU (_raw_user_message) até o wizard, igual WS/SSE.

Sem isto, a captura determinística do email do gestor recebia [EMAIL REMOVIDO]
(mascarado) e falhava silenciosamente — painel "Email do gestor" vazio mesmo
após o recrutador informar o email. Regressão a proteger.
"""
from __future__ import annotations
import pytest


@pytest.mark.medium
def test_chat_adapter_forwards_raw_user_message_to_ctx_extra():
    """ChatAdapter encaminha _raw_user_message do page_context para ctx.extra."""
    from app.orchestrator.context.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=object())  # _build_context não usa o orch
    ctx = adapter._build_context(
        user_message="gestor é paulo [EMAIL REMOVIDO]",  # mascarado (como o LLM vê)
        user_id="u1",
        company_id="c1",
        conversation_id="conv1",
        page_context={"_raw_user_message": "gestor é paulo paulo.moraes@x.com"},
    )
    assert ctx.extra.get("_raw_user_message") == "gestor é paulo paulo.moraes@x.com"


@pytest.mark.medium
def test_chat_adapter_no_raw_when_absent():
    """Sem _raw_user_message no page_context, ctx.extra não inventa a chave."""
    from app.orchestrator.context.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=object())
    ctx = adapter._build_context(
        user_message="oi",
        user_id="u1",
        company_id="c1",
        conversation_id="conv1",
        page_context={},
    )
    assert "_raw_user_message" not in ctx.extra


@pytest.mark.medium
def test_ctx_extra_dict_copy_carries_raw():
    """main_orchestrator faz dict(ctx.extra) → a chave sobrevive ao wiz_context."""
    from app.orchestrator.context.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=object())
    ctx = adapter._build_context(
        user_message="x",
        user_id="u1",
        company_id="c1",
        conversation_id="conv1",
        page_context={"_raw_user_message": "joao@y.com"},
    )
    wiz_context = dict(ctx.extra or {})  # espelha main_orchestrator.py:1825
    assert wiz_context.get("_raw_user_message") == "joao@y.com"
