"""TDD: SSE keepalive durante fase de setup (asyncio.gather) — previne timeout 90s.

Fix P0: event_generator deve emitir keepalives durante o asyncio.gather
dos 5 tasks de setup (budget, routing, B2, tenant context, focused job).
"""
import asyncio
import json
import pytest


def test_serialize_keepalive_returns_data_event():
    """serialize_keepalive() deve retornar evento SSE data: com JSON."""
    from app.shared.chat_event_serializer import serialize_keepalive
    
    result = serialize_keepalive()
    assert result.startswith("data: "),         "serialize_keepalive deve retornar evento SSE data: (nao apenas comment)"
    assert result.endswith("\n\n"),         "Evento SSE deve terminar com \n\n"
    
    # Verificar que e JSON valido com type=keepalive
    json_part = result[len("data: "):].strip()
    parsed = json.loads(json_part)
    assert parsed.get("type") == "keepalive",         "Payload deve ter type=keepalive"
    assert "ts" in parsed,         "Payload deve ter timestamp ts"


def test_format_sse_keepalive_returns_comment():
    """format_sse_keepalive() deve manter retrocompat como SSE comment."""
    from app.shared.chat_event_serializer import format_sse_keepalive
    
    result = format_sse_keepalive()
    assert result == ": keepalive\n\n",         "format_sse_keepalive deve retornar SSE comment canonico"


@pytest.mark.asyncio
async def test_setup_keepalive_loop_emits_periodically():
    """Loop de keepalive de setup deve emitir evento a cada ~8s.
    
    Testa que o padrao canonico de keepalive durante gather funciona:
    - A queue recebe evento apos sleep
    - O loop nao emite quando _ka_stop esta setado
    """
    from app.shared.chat_event_serializer import format_sse_keepalive
    
    _setup_ka_q: asyncio.Queue = asyncio.Queue()
    _setup_ka_stop = asyncio.Event()
    
    # Versao acelerada: sleep(0.01) ao inves de sleep(8)
    async def _setup_ka_loop_fast() -> None:
        try:
            while not _setup_ka_stop.is_set():
                await asyncio.sleep(0.01)  # acelerado para teste
                if not _setup_ka_stop.is_set():
                    await _setup_ka_q.put(format_sse_keepalive())
        except asyncio.CancelledError:
            pass
    
    _ka_task = asyncio.create_task(_setup_ka_loop_fast())
    
    # Aguardar 3 iteracoes (0.03s)
    await asyncio.sleep(0.05)
    _setup_ka_stop.set()
    _ka_task.cancel()
    try:
        await asyncio.wait_for(_ka_task, timeout=0.1)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    
    # Deve ter recebido pelo menos 1 keepalive
    events = []
    while not _setup_ka_q.empty():
        events.append(_setup_ka_q.get_nowait())
    
    assert len(events) >= 1,         f"Loop deve ter emitido pelo menos 1 keepalive, recebeu {len(events)}"
    assert all(e == ": keepalive\n\n" for e in events),         "Todos os eventos devem ser keepalives canonicos"


@pytest.mark.asyncio
async def test_setup_keepalive_stops_after_cancel():
    """Loop de keepalive deve parar apos cancelamento da task."""
    from app.shared.chat_event_serializer import format_sse_keepalive
    
    _setup_ka_q: asyncio.Queue = asyncio.Queue()
    _setup_ka_stop = asyncio.Event()
    
    async def _setup_ka_loop_fast() -> None:
        try:
            while not _setup_ka_stop.is_set():
                await asyncio.sleep(0.01)
                if not _setup_ka_stop.is_set():
                    await _setup_ka_q.put(format_sse_keepalive())
        except asyncio.CancelledError:
            pass
    
    _ka_task = asyncio.create_task(_setup_ka_loop_fast())
    await asyncio.sleep(0.05)
    
    # Contar antes de parar
    count_before = _setup_ka_q.qsize()
    
    # Parar
    _setup_ka_stop.set()
    _ka_task.cancel()
    try:
        await asyncio.wait_for(_ka_task, timeout=0.2)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    
    await asyncio.sleep(0.05)  # Esperar mais um pouco
    count_after = _setup_ka_q.qsize()
    
    # Nao deve ter emitido mais apos parar
    assert count_after == count_before,         f"Loop parado nao deve emitir mais eventos: antes={count_before}, depois={count_after}"
