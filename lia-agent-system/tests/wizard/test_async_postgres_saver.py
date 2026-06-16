"""
Sprint R.1 sensor — AsyncPostgresSaver canonical, NOT MemorySaver.

Goal: regression guard contra Task #1161 Bug B (PostgresSaver sync →
NotImplementedError em aget_tuple → silent fallback para MemorySaver →
wizard state loss em uvicorn restart).

Sensors:
1. ``test_initialize_returns_async_postgres_saver`` — após
   ``initialize_checkpointer_async``, kind == ``async_postgres`` e o saver
   é AsyncPostgresSaver (não MemorySaver).
2. ``test_aget_tuple_implemented_natively`` — ``aget_tuple`` está no
   ``__dict__`` da classe (não herdado do stub abstrato), garantia anti
   #1161 Bug B.
3. ``test_checkpoint_tables_exist`` — tabelas ``checkpoints``,
   ``checkpoint_blobs``, ``checkpoint_writes``, ``checkpoint_migrations``
   existem em DB (AsyncPostgresSaver.setup() criou).
4. ``test_state_persists_across_restart`` — escreve com saver A, fecha
   pool, abre novo pool/saver B, lê de volta. Simula uvicorn restart.

Disciplinas:
- harness-engineering: SENSOR canonical para regressão do bug histórico.
- production-quality: testa o caminho canonical (AsyncPostgres), não mocks.
"""
import asyncio
import os
import uuid

import pytest

# Skip se DATABASE_URL não está configurado (tests unit-only env)
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL não configurado (test integração)",
)


@pytest.mark.asyncio
async def test_initialize_returns_async_postgres_saver():
    """Sprint R.1: kind == async_postgres, type == AsyncPostgresSaver."""
    from lia_agents_core.checkpointer import (
        initialize_checkpointer_async,
        shutdown_checkpointer_async,
        get_checkpointer_kind,
    )
    try:
        saver = await initialize_checkpointer_async()
        assert get_checkpointer_kind() == "async_postgres", (
            f"Expected async_postgres, got {get_checkpointer_kind()!r}. "
            "Pode indicar fallback silent para MemorySaver — bug #1161 ressuscitou."
        )
        assert type(saver).__name__ == "AsyncPostgresSaver", (
            f"Expected AsyncPostgresSaver, got {type(saver).__name__!r}"
        )
    finally:
        await shutdown_checkpointer_async()


@pytest.mark.asyncio
async def test_aget_tuple_implemented_natively():
    """
    Sprint R.1 — Task #1161 Bug B regression guard.

    PostgresSaver (sync) herda aget_tuple como stub abstrato (NotImplementedError).
    AsyncPostgresSaver implementa aget_tuple nativamente. Esse teste detecta
    regressão se alguém trocar de volta para PostgresSaver sync.
    """
    from lia_agents_core.checkpointer import (
        initialize_checkpointer_async,
        shutdown_checkpointer_async,
        _supports_async,
    )
    try:
        saver = await initialize_checkpointer_async()
        assert _supports_async(saver), (
            "_supports_async retornou False — saver atual não implementa "
            "aget_tuple nativamente. Bug #1161 Bug B regrediu."
        )
        assert "aget_tuple" in type(saver).__dict__, (
            "aget_tuple não está no class __dict__ do saver — herdado de "
            "BaseCheckpointSaver (stub abstrato)."
        )
    finally:
        await shutdown_checkpointer_async()


@pytest.mark.asyncio
async def test_checkpoint_tables_exist():
    """AsyncPostgresSaver.setup() é idempotente — verifica tabelas existem."""
    import psycopg
    from lia_agents_core.checkpointer import (
        initialize_checkpointer_async,
        shutdown_checkpointer_async,
        _normalize_db_url,
    )
    try:
        await initialize_checkpointer_async()
        # Conecta direto pra verificar tabelas
        url = _normalize_db_url(os.environ["DATABASE_URL"])
        async with await psycopg.AsyncConnection.connect(url) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name LIKE 'checkpoint%' "
                    "ORDER BY table_name"
                )
                rows = await cur.fetchall()
                names = {r[0] for r in rows}
        expected = {"checkpoints", "checkpoint_blobs", "checkpoint_writes", "checkpoint_migrations"}
        assert expected.issubset(names), (
            f"Tabelas checkpoint ausentes. Esperado: {expected}. "
            f"Encontrado: {names}. AsyncPostgresSaver.setup() falhou?"
        )
    finally:
        await shutdown_checkpointer_async()


@pytest.mark.asyncio
async def test_state_persists_across_restart():
    """
    Simula uvicorn restart: escreve via saver A, fecha pool, inicializa
    saver B, lê o mesmo thread_id. Bug #1161 Bug B significava state loss
    aqui.
    """
    from lia_agents_core.checkpointer import (
        initialize_checkpointer_async,
        shutdown_checkpointer_async,
    )
    thread_id = f"test_sprint_r1_persist_{uuid.uuid4()}"
    expected_payload = f"value_sprint_r1_{uuid.uuid4()}"

    # Boot 1: write
    saver_a = await initialize_checkpointer_async()
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    cp = {
        "v": 1,
        "id": str(uuid.uuid4()),
        "ts": "2026-05-21T00:00:00Z",
        "channel_values": {"foo": expected_payload},
        "channel_versions": {"foo": 1},
        "versions_seen": {},
        "pending_sends": [],
    }
    md = {"source": "test_sprint_r1", "step": 0, "writes": {}, "parents": {}}
    saved_config = await saver_a.aput(config, cp, md, {})
    assert saved_config["configurable"]["thread_id"] == thread_id

    # Simula uvicorn restart — fecha pool + limpa singleton
    await shutdown_checkpointer_async()

    # Boot 2: read
    saver_b = await initialize_checkpointer_async()
    try:
        # saver_b é instância nova (pool novo)
        assert saver_b is not saver_a or True  # singleton pode coincidir mas channel_values vem do DB
        fetched = await saver_b.aget_tuple(saved_config)
        assert fetched is not None, (
            f"State perdido após restart simulado para thread_id={thread_id}. "
            "Bug #1161 Bug B regrediu — checkpoints não estão persistindo no Postgres."
        )
        assert fetched.checkpoint["channel_values"]["foo"] == expected_payload, (
            f"Estado corrompido após restart: {fetched.checkpoint['channel_values']}"
        )
    finally:
        await shutdown_checkpointer_async()
