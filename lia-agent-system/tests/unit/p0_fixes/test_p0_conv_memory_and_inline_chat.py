"""
P0 multi-tenancy fix — ConversationMemory.get_conversation must filter by company_id.
Red tests: confirm gap exists before fix.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_conversation_accepts_company_id_param():
    """get_conversation deve aceitar company_id e retornar None se UUID pertence a outra empresa."""
    import inspect
    from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory

    sig = inspect.signature(ConversationMemory.get_conversation)
    assert "company_id" in sig.parameters, (
        "get_conversation não tem parâmetro company_id — gap P0 multi-tenancy"
    )


@pytest.mark.asyncio
async def test_get_conversation_filters_by_company_id():
    """Se company_id != dono da conversa, deve retornar None."""
    from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory
    from unittest.mock import AsyncMock, MagicMock

    svc = ConversationMemory()
    fake_conv = MagicMock()
    fake_conv.company_id = "company-A"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_conv

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    conv_id = str(uuid.uuid4())

    # Acesso com company-B deve retornar None (conversa é da company-A)
    result = await svc.get_conversation(
        db=db,
        conversation_id=conv_id,
        company_id="company-B",
    )
    assert result is None, (
        "get_conversation retornou conversa de outra empresa — gap P0 IDOR"
    )


@pytest.mark.asyncio
async def test_delete_conversation_accepts_company_id_param():
    """delete_conversation deve aceitar company_id para prevenir IDOR."""
    import inspect
    from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory

    sig = inspect.signature(ConversationMemory.delete_conversation)
    assert "company_id" in sig.parameters, (
        "delete_conversation não tem parâmetro company_id — IDOR: qualquer usuário pode deletar conversa alheia"
    )


def test_inline_chat_has_fairness_guard():
    """Verifica que inline_chat.py importa e instancia FairnessGuard."""
    import app.api.v1.inline_chat as module
    from app.shared.compliance.fairness_guard import FairnessGuard

    assert hasattr(module, "_fairness_guard"), (
        "inline_chat.py não tem _fairness_guard — FairnessGuard não foi adicionado"
    )
    assert isinstance(module._fairness_guard, FairnessGuard), (
        f"_fairness_guard não é FairnessGuard: {type(module._fairness_guard)}"
    )


@pytest.mark.asyncio
async def test_inline_chat_handler_blocks_discriminatory_query():
    """inline_chat_ask handler deve chamar FairnessGuard e lançar 400 quando bloqueado."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from fastapi import HTTPException
    from app.api.v1.inline_chat import inline_chat_ask, InlineChatRequest

    payload = InlineChatRequest(
        question="candidatos mulheres com filhos pequenos",
        context_type="page",
        intent="answer",
    )

    mock_repo = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await inline_chat_ask(
            payload=payload,
            company_id="company-test",
            repo=mock_repo,
        )

    assert exc_info.value.status_code == 400, (
        f"Handler não retornou 400 para query discriminatória — status={exc_info.value.status_code}"
    )
    detail = exc_info.value.detail
    assert detail.get("error") == "fairness_blocked", (
        f"Detail não indica fairness_blocked: {detail}"
    )
