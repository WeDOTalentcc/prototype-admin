"""
Tests — F2-04: Dead Letter Queue para Celery.

Cobre:
  1.  push_failure() retorna entry_id quando Redis disponível
  2.  push_failure() retorna None (fail-safe) quando Redis indisponível
  3.  push_failure() aplica PII masking nos kwargs
  4.  list_entries() retorna entradas da fila
  5.  list_entries() retorna [] quando Redis falha
  6.  list_queues() retorna filas com entradas
  7.  queue_size() retorna tamanho correto
  8.  clear() remove entradas e retorna contagem
  9.  clear() retorna 0 quando Redis indisponível
  10. summary() agrega tamanhos de todas as filas
  11. LIATask base class declarada no celery_app
  12. admin_dlq router registrado no main.py
  13. _mask_pii() mascara campos sensíveis
  14. KNOWN_QUEUES contém as 5 filas esperadas
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.resilience.dlq_service import (
    DLQService,
    KNOWN_QUEUES,
    _queue_key,
    dlq_service,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_redis_mock(llen_return=0):
    redis = AsyncMock()
    redis.lpush = AsyncMock(return_value=1)
    redis.ltrim = AsyncMock()
    redis.expire = AsyncMock()
    redis.sadd = AsyncMock()
    redis.lrange = AsyncMock(return_value=[])
    redis.smembers = AsyncMock(return_value=set())
    redis.llen = AsyncMock(return_value=llen_return)
    redis.delete = AsyncMock()
    redis.srem = AsyncMock()
    redis.lrem = AsyncMock()
    redis.__aenter__ = AsyncMock(return_value=redis)
    redis.__aexit__ = AsyncMock(return_value=False)
    return redis


def _make_exc():
    return ValueError("DB connection timeout")


# ── 1. push_failure() com Redis disponível ────────────────────────────────────

@pytest.mark.asyncio
async def test_push_failure_returns_entry_id():
    svc = DLQService()
    redis_mock = _make_redis_mock()

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ), patch.object(svc, "_notify_if_critical", AsyncMock()):
        entry_id = await svc.push_failure(
            task_name="drift.run_batch",
            queue="onboarding_low",
            args=[],
            kwargs={"company_id": "c-001"},
            exc=_make_exc(),
            tb="Traceback ...",
            retries=3,
        )

    assert entry_id is not None
    assert len(entry_id) == 36  # UUID format
    redis_mock.lpush.assert_called_once()
    redis_mock.ltrim.assert_called_once()


# ── 2. push_failure() fail-safe quando Redis indisponível ─────────────────────

@pytest.mark.asyncio
async def test_push_failure_returns_none_when_redis_unavailable():
    svc = DLQService()

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=None),
    ):
        entry_id = await svc.push_failure(
            task_name="drift.run_batch",
            queue="onboarding_low",
            args=[],
            kwargs={},
            exc=_make_exc(),
        )

    assert entry_id is None


# ── 3. PII masking nos kwargs ─────────────────────────────────────────────────

def test_mask_pii_masks_sensitive_keys():
    masked = DLQService._mask_pii({
        "company_id": "c-001",
        "email": "user@example.com",
        "password": "secret123",
        "token": "abc.def.ghi",
        "candidate_name": "João Silva",
    })
    assert masked["company_id"] == "c-001"
    assert masked["email"] == "***"
    assert masked["password"] == "***"
    assert masked["token"] == "***"
    assert masked["candidate_name"] == "João Silva"


def test_mask_pii_recurses_into_dicts():
    masked = DLQService._mask_pii({
        "data": {"cpf": "123.456.789-00", "name": "Maria"}
    })
    assert masked["data"]["cpf"] == "***"
    assert masked["data"]["name"] == "Maria"


# ── 4. list_entries() retorna entradas ────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_entries_returns_parsed_entries():
    svc = DLQService()
    entry = {
        "entry_id": "abc-123", "task_name": "drift.run_batch",
        "queue": "onboarding_low", "args": [], "kwargs": {},
        "exception_type": "ValueError", "exception_msg": "err",
        "traceback": "", "retries": 3, "company_id": "c-001",
        "failed_at": "2026-03-19T10:00:00+00:00",
    }
    redis_mock = _make_redis_mock()
    redis_mock.lrange = AsyncMock(return_value=[json.dumps(entry)])

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        entries = await svc.list_entries("onboarding_low", limit=10)

    assert len(entries) == 1
    assert entries[0]["entry_id"] == "abc-123"


# ── 5. list_entries() retorna [] quando Redis falha ───────────────────────────

@pytest.mark.asyncio
async def test_list_entries_returns_empty_on_redis_failure():
    svc = DLQService()

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(side_effect=Exception("Redis down")),
    ):
        entries = await svc.list_entries("onboarding_low")

    assert entries == []


# ── 6. list_queues() retorna filas com entradas ───────────────────────────────

@pytest.mark.asyncio
async def test_list_queues_returns_queues_with_entries():
    svc = DLQService()
    redis_mock = _make_redis_mock()
    redis_mock.smembers = AsyncMock(return_value={"onboarding_low", "sourcing_high"})

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        queues = await svc.list_queues()

    assert "onboarding_low" in queues
    assert "sourcing_high" in queues


# ── 7. queue_size() retorna tamanho correto ───────────────────────────────────

@pytest.mark.asyncio
async def test_queue_size_returns_correct_count():
    svc = DLQService()
    redis_mock = _make_redis_mock(llen_return=7)

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        size = await svc.queue_size("sourcing_high")

    assert size == 7


# ── 8. clear() remove entradas ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clear_removes_entries_and_returns_count():
    svc = DLQService()
    redis_mock = _make_redis_mock(llen_return=5)

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        removed = await svc.clear("onboarding_low")

    assert removed == 5
    redis_mock.delete.assert_called_once_with(_queue_key("onboarding_low"))
    redis_mock.srem.assert_called_once_with("dlq:index", "onboarding_low")


# ── 9. clear() retorna 0 quando Redis indisponível ────────────────────────────

@pytest.mark.asyncio
async def test_clear_returns_zero_when_redis_unavailable():
    svc = DLQService()

    with patch(
        "app.shared.resilience.dlq_service._get_redis",
        AsyncMock(return_value=None),
    ):
        removed = await svc.clear("onboarding_low")

    assert removed == 0


# ── 10. summary() agrega tamanhos ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summary_aggregates_queue_sizes():
    svc = DLQService()

    async def _fake_list_queues():
        return ["onboarding_low", "sourcing_high"]

    async def _fake_queue_size(queue):
        return {"onboarding_low": 3, "sourcing_high": 1}.get(queue, 0)

    with patch.object(svc, "list_queues", _fake_list_queues), \
         patch.object(svc, "queue_size", _fake_queue_size):
        result = await svc.summary()

    assert result["total_entries"] == 4
    assert result["queues"]["onboarding_low"] == 3
    assert result["queues"]["sourcing_high"] == 1


# ── 11. LIATask base class declarada no celery_app ────────────────────────────

def test_lia_task_base_class_defined():
    from lia_config.celery_app import LIATask
    from celery import Task
    assert issubclass(LIATask, Task)
    assert hasattr(LIATask, "on_failure")
    assert LIATask.abstract is True


# ── 12. admin_dlq router registrado no main.py ───────────────────────────────

def test_admin_dlq_router_registered():
    import inspect
    import app.main as main_module
    src = inspect.getsource(main_module)
    assert "admin_dlq" in src
    assert "admin_dlq_router" in src


# ── 13. _mask_pii() não mascara campos não-sensíveis ─────────────────────────

def test_mask_pii_preserves_non_sensitive():
    masked = DLQService._mask_pii({
        "job_id": "job-123",
        "company_id": "c-456",
        "batch_size": 100,
    })
    assert masked["job_id"] == "job-123"
    assert masked["company_id"] == "c-456"
    assert masked["batch_size"] == 100


# ── 14. KNOWN_QUEUES contém as 5 filas esperadas ─────────────────────────────

def test_known_queues_contains_all_queues():
    expected = {"sourcing_high", "evaluation_normal", "vagas_normal", "onboarding_low", "celery"}
    assert expected == set(KNOWN_QUEUES)
