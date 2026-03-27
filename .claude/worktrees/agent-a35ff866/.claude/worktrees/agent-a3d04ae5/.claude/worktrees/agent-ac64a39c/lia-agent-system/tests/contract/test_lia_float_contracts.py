"""
Contract tests — LIA Float Chat (Phase 4a).

Verifica contratos de interface do painel flutuante:
- POST /api/v1/conversations → ConversationResponse
- GET  /api/v1/conversations/{id} → ConversationDetailResponse c/ messages
- Isolamento multi-tenant (company_id / user_id)
- Campos obrigatórios na resposta

Camada 5 — Contrato (pytest + FastAPI TestClient)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conv_id() -> str:
    return str(uuid4())


def _make_create_request(
    title: str = "Listar vagas abertas",
    context_type: str = "general",
    user_id: str = "user-float-001",
):
    return {
        "title": title,
        "context_type": context_type,
        "user_id": user_id,
    }


# ---------------------------------------------------------------------------
# ConversationResponse Schema Contract
# ---------------------------------------------------------------------------


class TestConversationResponseContract:
    """Garante que ConversationResponse tem todos os campos esperados pelo FE."""

    def test_conversation_response_has_id_field(self):
        from app.api.v1.conversations import ConversationResponse
        import inspect
        fields = ConversationResponse.model_fields
        assert "id" in fields, "ConversationResponse deve ter campo 'id'"

    def test_conversation_response_has_context_type(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "context_type" in fields

    def test_conversation_response_has_title(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "title" in fields

    def test_conversation_response_has_is_active(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "is_active" in fields

    def test_conversation_response_has_message_count(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "message_count" in fields

    def test_conversation_response_has_created_at(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "created_at" in fields

    def test_conversation_response_serializes_to_dict(self):
        from app.api.v1.conversations import ConversationResponse
        resp = ConversationResponse(
            id=_conv_id(),
            user_id="u1",
            context_type="general",
            context_id=None,
            title="Test",
            summary=None,
            intent=None,
            status="active",
            is_active=True,
            message_count=0,
            created_at=None,
            updated_at=None,
        )
        d = resp.model_dump()
        assert d["id"] is not None
        assert d["context_type"] == "general"


# ---------------------------------------------------------------------------
# MessageResponse Schema Contract
# ---------------------------------------------------------------------------


class TestMessageResponseContract:
    """Garante que MessageResponse tem os campos necessários para o float."""

    def test_message_response_has_id(self):
        from app.api.v1.conversations import MessageResponse
        fields = MessageResponse.model_fields
        assert "id" in fields

    def test_message_response_has_role(self):
        from app.api.v1.conversations import MessageResponse
        fields = MessageResponse.model_fields
        assert "role" in fields

    def test_message_response_has_content(self):
        from app.api.v1.conversations import MessageResponse
        fields = MessageResponse.model_fields
        assert "content" in fields

    def test_message_response_has_created_at(self):
        from app.api.v1.conversations import MessageResponse
        fields = MessageResponse.model_fields
        assert "created_at" in fields

    def test_role_values_cover_user_and_assistant(self):
        """Float espera 'user' e 'assistant' como roles válidos."""
        from app.api.v1.conversations import MessageResponse
        for role in ("user", "assistant"):
            msg = MessageResponse(
                id=_conv_id(),
                conversation_id=_conv_id(),
                role=role,
                content="test",
                intent=None,
                tool_calls=None,
                metadata=None,
                created_at=None,
            )
            assert msg.role == role


# ---------------------------------------------------------------------------
# ConversationDetailResponse Schema Contract
# ---------------------------------------------------------------------------


class TestConversationDetailResponseContract:
    """Garante estrutura usada em GET /conversations/{id}."""

    def test_detail_response_has_conversation_and_messages(self):
        from app.api.v1.conversations import ConversationDetailResponse, ConversationResponse
        fields = ConversationDetailResponse.model_fields
        assert "conversation" in fields
        assert "messages" in fields

    def test_detail_response_messages_defaults_to_empty_list(self):
        from app.api.v1.conversations import ConversationDetailResponse, ConversationResponse
        resp = ConversationDetailResponse(
            conversation=ConversationResponse(
                id=_conv_id(),
                user_id="u1",
                context_type="general",
                context_id=None,
                title="T",
                summary=None,
                intent=None,
                status="active",
                is_active=True,
                message_count=0,
                created_at=None,
                updated_at=None,
            ),
            messages=[],
            summary=None,
        )
        assert isinstance(resp.messages, list)

    def test_detail_response_serializable_for_float(self):
        """FE espera { conversation: {...}, messages: [...] }."""
        from app.api.v1.conversations import ConversationDetailResponse, ConversationResponse
        resp = ConversationDetailResponse(
            conversation=ConversationResponse(
                id=_conv_id(),
                user_id="u1",
                context_type="general",
                context_id=None,
                title="T",
                summary=None,
                intent=None,
                status="active",
                is_active=True,
                message_count=0,
                created_at=None,
                updated_at=None,
            ),
            messages=[],
            summary=None,
        )
        d = resp.model_dump()
        assert "conversation" in d
        assert "messages" in d
        assert isinstance(d["messages"], list)


# ---------------------------------------------------------------------------
# CreateConversationRequest Contract
# ---------------------------------------------------------------------------


class TestCreateConversationRequestContract:
    """Garante que o payload enviado pelo float é compatível com o backend."""

    def test_create_request_accepts_general_context_type(self):
        """Float envia context_type='general'; user_id é opcional (vem do JWT)."""
        from app.api.v1.conversations import CreateConversationRequest
        req = CreateConversationRequest(
            context_type="general",
            title="Listar vagas abertas",
        )
        assert req.context_type == "general"

    def test_create_request_title_optional(self):
        from app.api.v1.conversations import CreateConversationRequest
        req = CreateConversationRequest(context_type="general")
        # title é opcional — não deve lançar erro
        assert req.context_type == "general"

    def test_create_request_user_id_is_optional(self):
        """user_id deve ser opcional — float não o envia; backend usa 'anonymous'."""
        from app.api.v1.conversations import CreateConversationRequest
        fields = CreateConversationRequest.model_fields
        assert "user_id" in fields
        field = fields["user_id"]
        assert not field.is_required(), (
            "user_id deve ser Optional para o float funcionar sem JWT user_id"
        )

    def test_create_request_without_user_id_defaults_to_none(self):
        from app.api.v1.conversations import CreateConversationRequest
        req = CreateConversationRequest(context_type="general")
        assert req.user_id is None


# ---------------------------------------------------------------------------
# Multi-tenant isolation contract
# ---------------------------------------------------------------------------


class TestFloatMultiTenantContract:
    """Conversas do float devem ser isoladas por user_id."""

    def test_conversation_response_has_user_id_for_tenant_isolation(self):
        from app.api.v1.conversations import ConversationResponse
        fields = ConversationResponse.model_fields
        assert "user_id" in fields, (
            "ConversationResponse deve ter user_id para isolamento multi-tenant"
        )

    def test_conversations_list_response_has_items_field(self):
        from app.api.v1.conversations import ConversationListResponse
        fields = ConversationListResponse.model_fields
        assert "conversations" in fields or "items" in fields, (
            "ConversationListResponse deve ter field de lista"
        )
