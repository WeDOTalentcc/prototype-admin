"""
Testes unitários para WebSocket message schemas (Sprint H — coverage gate 40%).

Cobertura:
  - WSUserMessage, WSPingMessage, WSAbortMessage (cliente → servidor)
  - WSConnectedMessage, WSThinkingMessage, WSTokenMessage,
    WSResponseMessage, WSErrorMessage, WSPongMessage (servidor → cliente)
"""
import pytest

pytestmark = pytest.mark.easy
from pydantic import ValidationError

from app.shared.websocket.ws_message_schemas import (
    WSUserMessage,
    WSPingMessage,
    WSAbortMessage,
    WSConnectedMessage,
    WSThinkingMessage,
    WSTokenMessage,
    WSResponseMessage,
    WSErrorMessage,
    WSPongMessage,
)


# ---------------------------------------------------------------------------
# Cliente → Servidor
# ---------------------------------------------------------------------------

class TestWSUserMessage:

    def test_minimal_valid(self):
        msg = WSUserMessage(content="Olá LIA")
        assert msg.content == "Olá LIA"
        assert msg.type == "message"
        assert msg.domain == "recruiter_assistant"
        assert msg.context == {}

    def test_with_context_and_domain(self):
        msg = WSUserMessage(
            content="criar vaga",
            domain="wizard",
            context={"stage": "details", "job_id": "j-1"},
        )
        assert msg.domain == "wizard"
        assert msg.context["stage"] == "details"

    def test_content_required(self):
        with pytest.raises(ValidationError):
            WSUserMessage()  # type: ignore — content obrigatório

    def test_serializable(self):
        msg = WSUserMessage(content="test")
        d = msg.model_dump()
        assert d["type"] == "message"
        assert "content" in d


class TestWSPingMessage:

    def test_type_is_ping(self):
        msg = WSPingMessage()
        assert msg.type == "ping"

    def test_serializable(self):
        assert WSPingMessage().model_dump()["type"] == "ping"


class TestWSAbortMessage:

    def test_type_is_abort(self):
        assert WSAbortMessage().type == "abort"


# ---------------------------------------------------------------------------
# Servidor → Cliente
# ---------------------------------------------------------------------------

class TestWSConnectedMessage:

    def test_fields(self):
        msg = WSConnectedMessage(session_id="sess-1", domain="wizard")
        assert msg.type == "connected"
        assert msg.session_id == "sess-1"
        assert msg.domain == "wizard"

    def test_timestamp_default_empty(self):
        msg = WSConnectedMessage(session_id="s", domain="d")
        assert msg.timestamp == ""

    def test_custom_timestamp(self):
        msg = WSConnectedMessage(session_id="s", domain="d", timestamp="2026-01-01T00:00:00Z")
        assert "2026" in msg.timestamp


class TestWSThinkingMessage:

    def test_type_is_thinking(self):
        assert WSThinkingMessage().type == "thinking"

    def test_job_id_optional(self):
        msg = WSThinkingMessage()
        assert msg.job_id is None

    def test_with_job_id(self):
        msg = WSThinkingMessage(job_id="celery-task-123")
        assert msg.job_id == "celery-task-123"


class TestWSTokenMessage:

    def test_content_required(self):
        with pytest.raises(ValidationError):
            WSTokenMessage()  # type: ignore

    def test_valid_token(self):
        msg = WSTokenMessage(content="Olá")
        assert msg.content == "Olá"
        assert msg.type == "token"

    def test_serializable(self):
        d = WSTokenMessage(content="chunk").model_dump()
        assert d["content"] == "chunk"
        assert d["type"] == "token"


class TestWSResponseMessage:

    def test_minimal(self):
        msg = WSResponseMessage(content="Resposta final")
        assert msg.content == "Resposta final"
        assert msg.type == "message"
        assert msg.confidence == 0.7
        assert msg.actions == []
        assert msg.navigation is None

    def test_with_all_fields(self):
        msg = WSResponseMessage(
            content="Vaga criada",
            confidence=0.95,
            actions=[{"type": "navigate", "path": "/vagas/1"}],
            navigation={"path": "/vagas"},
            state_updates={"job_id": "j-1"},
            domain="wizard",
            source="celery_worker",
        )
        assert msg.confidence == 0.95
        assert len(msg.actions) == 1
        assert msg.domain == "wizard"
        assert msg.source == "celery_worker"

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            WSResponseMessage(content="test", confidence=1.5)  # > 1.0

    def test_content_required(self):
        with pytest.raises(ValidationError):
            WSResponseMessage()  # type: ignore


class TestWSErrorMessage:

    def test_message_required(self):
        with pytest.raises(ValidationError):
            WSErrorMessage()  # type: ignore

    def test_valid_error(self):
        msg = WSErrorMessage(message="Internal server error")
        assert msg.type == "error"
        assert msg.message == "Internal server error"
        assert msg.code is None

    def test_with_code(self):
        msg = WSErrorMessage(message="Unauthorized", code="AUTH_REQUIRED")
        assert msg.code == "AUTH_REQUIRED"


class TestWSPongMessage:

    def test_type_is_pong(self):
        assert WSPongMessage().type == "pong"

    def test_serializable(self):
        assert WSPongMessage().model_dump()["type"] == "pong"
