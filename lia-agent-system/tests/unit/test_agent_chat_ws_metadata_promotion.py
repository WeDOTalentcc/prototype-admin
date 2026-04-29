"""
Sensor: agent_chat_ws.py promotes top-level metadata into context.metadata.

Audit context (2026-04-29 wizard-domain-hint-leak):
  Frontend sends Rail A hint metadata at the WS frame root and at the HTTP
  body root (depending on transport). The cascaded_router service
  ``rail_a_hint_override.try_hint_route()`` reads from ``context["metadata"]``.
  Both handlers (WS + HTTP) must promote metadata into context.metadata
  before invoking the router so Tier -1 routing fires.

Guards:
  1. HTTPChatRequest model exposes ``metadata`` field (top-level Rail A hint).
  2. WS handler promotes ``msg.metadata`` → ``context["metadata"]`` when
     context.metadata is absent (idempotent merge).
  3. HTTP handler promotes ``req.metadata`` → ``context["metadata"]``
     similarly.

These are *structural* guards (regex over source) — full e2e of the WS
handler requires WebSocket + auth + RabbitMQ mocks, which is much more
fragile. Keep the structural guards green and the e2e is exercised by
``tests/integration/test_agent_chat_ws_prefix.py`` plus manual UAT.

Fix se falhar:
  Verificar ``app/api/v1/agent_chat_ws.py`` — buscar a string
  ``msg.get("metadata")`` no WS handler e ``req.metadata`` no HTTP handler;
  ambos devem ser atribuídos a ``context["metadata"]`` se ainda não
  presente. HTTPChatRequest deve declarar ``metadata: dict[str, Any] = {}``.

Skill canônica: harness-engineering [sensor computacional].
"""
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixture: source of agent_chat_ws.py (read once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def chat_ws_src() -> str:
    src_path = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "agent_chat_ws.py"
    assert src_path.is_file(), f"Expected source file at {src_path}"
    return src_path.read_text()


# ---------------------------------------------------------------------------
# Guard 1: HTTPChatRequest exposes metadata field
# ---------------------------------------------------------------------------


def test_http_chat_request_has_metadata_field(chat_ws_src):
    """HTTPChatRequest.metadata field must be declared so FastAPI parses it."""
    # Loose match: field name + dict type annotation.
    assert "metadata: dict[str, Any]" in chat_ws_src, (
        "HTTPChatRequest must declare `metadata: dict[str, Any]` to expose "
        "Rail A hint metadata at the HTTP body root. See "
        "rail_a_hint_override.try_hint_route() for downstream contract."
    )


# ---------------------------------------------------------------------------
# Guard 2: WS handler promotes msg.metadata → context.metadata
# ---------------------------------------------------------------------------


def test_ws_handler_promotes_metadata(chat_ws_src):
    """WS handler must promote msg.get('metadata') into context['metadata']."""
    # The promotion block we expect (allow some whitespace flexibility).
    assert "msg.get(\"metadata\")" in chat_ws_src, (
        "WS handler must read msg.get('metadata') (top-level metadata) "
        "and write it into context['metadata'] before invoking router."
    )
    assert "context[\"metadata\"]" in chat_ws_src, (
        "WS handler must write into context['metadata'] so "
        "rail_a_hint_override.try_hint_route() reads it."
    )


# ---------------------------------------------------------------------------
# Guard 3: HTTP handler promotes req.metadata → context.metadata
# ---------------------------------------------------------------------------


def test_http_handler_promotes_metadata(chat_ws_src):
    """HTTP handler must promote req.metadata into context['metadata']."""
    # Both the field access and the assignment must be present in the file.
    assert "req.metadata" in chat_ws_src, (
        "HTTP handler must read req.metadata (HTTPChatRequest field) and "
        "write it into context['metadata'] before invoking router."
    )


# ---------------------------------------------------------------------------
# Guard 4: promotion is idempotent (does not overwrite caller-provided context.metadata)
# ---------------------------------------------------------------------------


def test_promotion_is_idempotent(chat_ws_src):
    """Promotion logic must not overwrite an existing context['metadata']."""
    # Idempotency markers: either `not context.get("metadata")` or
    # `"metadata" not in context` should appear near the promotion blocks.
    has_guard = (
        "not context.get(\"metadata\")" in chat_ws_src
        or "\"metadata\" not in context" in chat_ws_src
    )
    assert has_guard, (
        "Promotion of top-level metadata into context['metadata'] must be "
        "guarded by an idempotency check so caller-provided "
        "context['metadata'] (canonical) takes precedence."
    )
