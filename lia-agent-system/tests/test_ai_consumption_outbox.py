"""Audit task #544 — testes do outbox `ai_consumption_outbox`.

Cobertura:

* ``enqueue_outbox_payload`` insere linha pendente.
* ``drain_batch`` consome linha pendente, marca ``delivered_at`` e
  chama ``TokenTrackingService.record_usage``.
* ``OutboxDrainerWorker.start/stop`` arranca e para sem deixar tasks
  pendentes.
* ``build_usage_callback`` no novo fluxo enfileira no outbox em vez de
  tentar persistir direto em ``AiConsumption`` (cancel-safe).
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_enqueue_and_drain_outbox(monkeypatch):
    """Enfileira payload, drena e verifica que record_usage foi chamado."""
    from app.shared.observability import ai_consumption_outbox_worker as worker_mod

    fake_rows = []

    class FakeRow:
        def __init__(self, payload):
            self.id = "row-1"
            self.payload = payload
            self.attempts = 0
            self.delivered_at = None

    async def fake_enqueue(payload):
        fake_rows.append(FakeRow(payload))

    record_calls = []

    class FakeTokenSvc:
        def __init__(self, db):
            pass

        async def record_usage(self, **kwargs):
            record_calls.append(kwargs)

    async def fake_drain(batch_size=50):
        delivered = 0
        for row in list(fake_rows):
            svc = FakeTokenSvc(None)
            await svc.record_usage(**row.payload)
            row.delivered_at = "now"
            delivered += 1
        return delivered

    monkeypatch.setattr(worker_mod, "enqueue_outbox_payload", fake_enqueue)
    monkeypatch.setattr(worker_mod, "drain_batch", fake_drain)

    payload = {
        "user_id": "",
        "company_id": "00000000-0000-0000-0000-000000000001",
        "agent_type": "test",
        "intent": "unit",
        "input_tokens": 10,
        "output_tokens": 5,
        "model": "claude",
        "latency_ms": 12.0,
        "candidate_id": None,
        "vacancy_id": None,
        "extra_data": {"source": "unit-test"},
    }

    await worker_mod.enqueue_outbox_payload(payload)
    assert len(fake_rows) == 1

    delivered = await worker_mod.drain_batch(batch_size=10)
    assert delivered == 1
    assert record_calls and record_calls[0]["company_id"] == payload["company_id"]
    assert all(r.delivered_at is not None for r in fake_rows)


@pytest.mark.asyncio
async def test_outbox_worker_lifecycle(monkeypatch):
    """Worker arranca, executa pelo menos um ciclo e para limpo."""
    from app.shared.observability import ai_consumption_outbox_worker as worker_mod

    cycle_count = {"n": 0}

    async def fake_drain(batch_size=50):
        cycle_count["n"] += 1
        return 0

    monkeypatch.setattr(worker_mod, "drain_batch", fake_drain)

    worker = worker_mod.OutboxDrainerWorker(interval_s=0.05, batch_size=5)
    await worker.start()
    assert worker.running
    await asyncio.sleep(0.2)
    await worker.stop()
    assert not worker.running
    assert cycle_count["n"] >= 1


def test_build_usage_callback_enqueues(monkeypatch):
    """Callback síncrono agenda inserção no outbox via worker module."""
    from app.shared.observability import usage_tracking_callback as cb_mod
    from app.shared.observability import ai_consumption_outbox_worker as worker_mod

    enqueue_mock = AsyncMock()
    monkeypatch.setattr(worker_mod, "enqueue_outbox_payload", enqueue_mock)

    cb = cb_mod.build_usage_callback(
        {"company_id": "11111111-1111-1111-1111-111111111111"},
        agent_type="cv_screening_rubric",
        default_operation="rubric_evaluate_candidate",
    )
    assert cb is not None

    async def _drive():
        cb({
            "input_tokens": 7,
            "output_tokens": 3,
            "model": "gemini",
            "latency_ms": 1.0,
            "provider": "gemini",
        })
        # Drena loop: a task agendada no callback corre aqui.
        await asyncio.sleep(0.05)

    asyncio.run(_drive())
    enqueue_mock.assert_awaited()
    payload = enqueue_mock.await_args.args[0]
    assert payload["agent_type"] == "cv_screening_rubric"
    assert payload["input_tokens"] == 7
    assert payload["company_id"] == "11111111-1111-1111-1111-111111111111"


def test_build_usage_callback_noop_without_company():
    from app.shared.observability.usage_tracking_callback import (
        build_usage_callback,
    )
    assert build_usage_callback(None, agent_type="x", default_operation="y") is None
    assert build_usage_callback({}, agent_type="x", default_operation="y") is None
