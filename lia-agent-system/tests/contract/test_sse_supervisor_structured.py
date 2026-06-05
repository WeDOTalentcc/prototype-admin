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


def test_keepalive_on_long_silence(monkeypatch):
    # Silencio prolongado do orchestrator (ex: WSI ~100s sem token) deve emitir
    # keepalive e NAO abortar com 'stream timeout' antes do hard cap.
    result = types.SimpleNamespace(
        content="ok", success=True, needs_params=False, needs_confirmation=False
    )

    class _SlowOrch:
        async def process(self, ctx, db, streaming_callback=None):
            await asyncio.sleep(0.25)
            return result

    monkeypatch.setattr(chat_mod, "get_main_orchestrator", lambda: _SlowOrch())
    chunks = asyncio.run(
        _collect(
            chat_mod._sse_via_orchestrator(
                "conv-1", "wsi longo", [], _FakeRepo(), _conv(), company_id="c1",
                keepalive_after_s=0.05, hard_timeout_s=5.0,
            )
        )
    )
    assert any(": keepalive" in c for c in chunks), (
        "silencio prolongado deve emitir keepalive (502 fix)")
    assert any("[DONE]" in c for c in chunks), "deve completar, nao abortar por timeout"
    assert not any('"stream timeout"' in c or "'stream timeout'" in c for c in chunks)
    assert any(f.get("token") == "ok" for f in _frames(chunks))


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


def test_build_supervisor_context_maps_conversation_and_view_context():
    # Fase 2 item 6: helper puro que monta o UniversalContext para rotear a bolha
    # pelo MainOrchestrator. conversation_id mapeado; view_context = context da bolha.
    ctx = chat_mod._build_supervisor_context(
        content="oi",
        context={"foo": "bar", "tenant_context_snippet": "T"},
        company_id="c1",
        user_id="u1",
        conversation_id="conv-9",
    )
    assert ctx.conversation_id == "conv-9"
    assert ctx.company_id == "c1"
    assert ctx.view_context == {"foo": "bar", "tenant_context_snippet": "T"}
    assert ctx.tenant_context_snippet == "T"


# ---------------------------------------------------------------------------
# Task #1090 — ws_stage_payload no SSE (canonical-fix: serializar no produtor
# unico, nao por transporte). Sem isso, o painel do wizard nao abre no chat-page
# e a IA "mente" que abriu. Mirror do evento WS (agent_chat_ws.py:1228) e do
# REST (chat.py message_metadata.ws_stage_payload).
# ---------------------------------------------------------------------------

_WIZARD_PAYLOAD = {
    "type": "wizard_stage",
    "thread_id": "t",
    "stage": "jd_gate",
    "job_vacancy_id": "job-1",
    "data": {"foo": "bar"},
}


def _wizard_stage_frames(frames):
    """Frames SSE que carregam o sinal do painel do wizard."""
    return [f for f in frames if f.get("type") == "wizard_stage" or "ws_stage_payload" in f]


def test_sse_carries_ws_stage_payload_chatpage_path(monkeypatch):
    # emit_structured=False (chat-page): o sinal do painel DEVE chegar mesmo assim.
    result = types.SimpleNamespace(
        content="Vamos criar a vaga", success=True,
        structured_data={"ws_stage_payload": dict(_WIZARD_PAYLOAD)},
        needs_params=False, needs_confirmation=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch, msg="criar vaga")
    wiz = _wizard_stage_frames(frames)
    assert wiz, (
        "REGRESSAO: SSE deve carregar ws_stage_payload (sinal que abre o painel "
        "do wizard). Sem ele o painel nao abre e a IA mente 'painel aberto'. "
        "Ver canonical-fix: serializar no produtor unico (serialize_message), "
        "nao por transporte."
    )
    assert wiz[0].get("stage") == "jd_gate"
    assert wiz[0].get("job_vacancy_id") == "job-1"
    # token streaming preservado (ADITIVO): conteudo continua chegando.
    assert any(f.get("token") == "Vamos criar a vaga" for f in frames)


def test_sse_carries_ws_stage_payload_bubble_path(monkeypatch):
    # emit_structured=True (bolha): tambem carrega ws_stage_payload (objetivo).
    result = types.SimpleNamespace(
        content="Vamos criar a vaga", success=True,
        structured_data={"ws_stage_payload": dict(_WIZARD_PAYLOAD)},
        needs_params=False, needs_confirmation=False,
    )
    frames = _run(_FakeOrch(result), monkeypatch, emit_structured=True, msg="criar vaga")
    wiz = _wizard_stage_frames(frames)
    assert wiz, (
        "REGRESSAO: SSE (bolha) deve carregar ws_stage_payload. "
        "Ver canonical-fix: serializar no produtor unico, nao por transporte."
    )
    # Na bolha o payload viaja DENTRO do frame `message` estruturado
    # (serialize_message anexa ws_stage_payload); no chat-page e um frame
    # dedicado top-level. Aceita ambos os shapes.
    f = wiz[0]
    nested = f.get("ws_stage_payload") or f
    assert nested.get("stage") == "jd_gate"


def test_sse_no_spurious_wizard_frame_when_absent(monkeypatch):
    # Regressao: ChatResponse normal (sem ws_stage_payload) NAO emite frame wizard
    # espurio e segue streaming token + [DONE] como antes.
    result = types.SimpleNamespace(
        content="texto normal", success=True, structured_data=None,
        needs_params=False, needs_confirmation=False,
    )
    monkeypatch.setattr(chat_mod, "get_main_orchestrator", lambda: _FakeOrch(result))
    chunks = asyncio.run(
        _collect(
            chat_mod._sse_via_orchestrator(
                "conv-1", "oi", [], _FakeRepo(), _conv(), company_id="c1",
            )
        )
    )
    frames = _frames(chunks)
    assert not _wizard_stage_frames(frames), (
        "sem ws_stage_payload nao deve emitir frame wizard espurio")
    assert any(f.get("token") == "texto normal" for f in frames)
    assert any("[DONE]" in c for c in chunks)
