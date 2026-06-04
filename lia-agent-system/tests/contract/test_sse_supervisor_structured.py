"""Fase 2 consolidacao bolha->supervisor.

Cobre o produtor `_sse_via_orchestrator` (chat.py) em duas frentes:
  1. Bug latente: ler `ChatResponse.content` (nao `.message`) no fallback sem-streaming.
  2. emit_structured=True: serializar os campos ricos do ChatResponse (message com
     actions/fairness, clarification via needs_params, approval_required via
     needs_confirmation) para paridade com a bolha (agent_chat_sse/ws).
  3. emit_structured default (False): chat-page permanece intocado (sem frames novos).

Deterministico: o MainOrchestrator e mockado (nao precisa de checkpointer/domain agents,
roda headless). Estilo sync + asyncio.run para nao depender de asyncio_mode do pytest.
"""
import asyncio
import json
import types

from app.api.v1 import chat as chat_mod


class _FakeOrch:
    def __init__(self, response, stream_events=None):
        self._response = response
        self._stream_events = stream_events or []

    async def process(self, ctx, db, streaming_callback=None):
        if streaming_callback:
            for ev in self._stream_events:
                await streaming_callback(ev)
        return self._response


class _FakeRepo:
    db = object()

    async def add_ai_message(self, *a, **k):
        return None

    async def commit(self):
        return None


def _conv():
    return types.SimpleNamespace(id="conv-1")


async def _collect(gen):
    out = []
    async for chunk in gen:
        out.append(chunk)
    return out


def _frames(chunks):
    """Parse 'data: {...}' frames into dicts (skip [DONE] / keepalive comments)."""
    frames = []
    for c in chunks:
        for line in c.splitlines():
            if line.startswith("data: "):
                payload = line[len("data: "):]
                if payload.strip() == "[DONE]":
                    continue
                frames.append(json.loads(payload))
    return frames


def _run(orch, monkeypatch, **kwargs):
    monkeypatch.setattr(chat_mod, "get_main_orchestrator", lambda: orch)
    chunks = asyncio.run(
        _collect(
            chat_mod._sse_via_orchestrator(
                "conv-1", kwargs.pop("msg", "oi"), [], _FakeRepo(), _conv(),
                company_id="c1", **kwargs,
            )
        )
    )
    return _frames(chunks)


def test_done_reads_content_not_message(monkeypatch):
    # Bug latente: result tem .content (ChatResponse main_orchestrator.py:168), nao .message.
    result = types.SimpleNamespace(content="resposta final", success=True)
    frames = _run(_FakeOrch(result), monkeypatch)  # sem streaming de tokens
    assert any(f.get("token") == "resposta final" for f in frames), (
        "fallback sem-streaming deve emitir ChatResponse.content como token")


def test_structured_message_emitted(monkeypatch):
    result = types.SimpleNamespace(
        content="aqui estao as vagas", success=True,
        actions=[{"label": "Ver vaga", "action": "open_job"}],
        fairness_warnings=["evite vies"], conversation_id="conv-1",
        needs_params=False, needs_confirmation=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch, emit_structured=True, msg="listar vagas")
    msg = [f for f in frames if f.get("type") == "message"]
    assert msg, "emit_structured=True deve emitir um frame type=message"
    assert msg[0]["actions"] == [{"label": "Ver vaga", "action": "open_job"}]
    assert msg[0]["fairness_warnings"] == ["evite vies"]


def test_clarification_emitted(monkeypatch):
    result = types.SimpleNamespace(
        content="Para qual vaga?", success=True, needs_params=True,
        suggested_prompts=["Dev Backend", "Designer"], needs_confirmation=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch, emit_structured=True, msg="ranquear")
    clar = [f for f in frames if f.get("type") == "clarification"]
    assert clar, "needs_params=True deve emitir clarification"
    assert clar[0]["options"] == ["Dev Backend", "Designer"]


def test_approval_required_emitted(monkeypatch):
    result = types.SimpleNamespace(
        content="Confirmar envio da oferta?", success=True, needs_confirmation=True,
        pending_action_id="pa-1", action_type="send_offer", needs_params=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch, emit_structured=True, msg="enviar oferta")
    appr = [f for f in frames if f.get("type") == "approval_required"]
    assert appr, "needs_confirmation=True deve emitir approval_required"
    assert appr[0]["pending_id"] == "pa-1"


def test_chatpage_path_unchanged(monkeypatch):
    # emit_structured default (False): chat-page intocado -> sem frames estruturados novos.
    result = types.SimpleNamespace(
        content="texto", success=True, actions=[{"x": 1}],
        needs_params=False, needs_confirmation=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch)
    assert not any(
        f.get("type") in ("message", "clarification", "approval_required") for f in frames
    ), "sem emit_structured, chat-page nao deve receber frames estruturados novos"
