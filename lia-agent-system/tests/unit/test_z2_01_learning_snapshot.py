"""
Tests — Z2-01: LearningSnapshotService.

Cobre:
  1. save_snapshot() retorna key quando Redis disponível (mock)
  2. save_snapshot() retorna None (fail-safe) quando Redis indisponível
  3. get_latest_key() retorna última chave do índice
  4. get_latest_key() retorna None quando índice vazio
  5. list_snapshots() retorna lista correta
  6. list_snapshots() retorna [] quando Redis falha
  7. rollback_to_latest() restaura padrões do snapshot (mock DB)
  8. rollback_to_latest() retorna False quando sem snapshots
  9. rollback_to_latest() retorna False (fail-safe) quando DB falha
 10. _update_index() trunca para MAX_SNAPSHOTS
 11. Wiring: learning_loop_service chama save_snapshot antes de _update_pattern
"""
import json
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.shared.learning.learning_snapshot_service import (
    LearningSnapshotService,
    MAX_SNAPSHOTS,
    SNAPSHOT_TTL_SECONDS,
    _snapshot_key,
    _index_key,
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_redis_mock(get_return=None):
    """Retorna um mock de Redis async com suporte a context manager."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=get_return)
    redis.setex = AsyncMock()
    redis.__aenter__ = AsyncMock(return_value=redis)
    redis.__aexit__ = AsyncMock(return_value=False)
    return redis


def _make_pattern_mock(key="salary:dev:senior", pattern_type="salary_preference"):
    p = MagicMock()
    p.pattern_key = key
    p.pattern_type = pattern_type
    p.pattern_value = {"min": 5000, "max": 8000}
    p.sample_size = 10
    p.acceptance_rate = 0.8
    p.confidence = "high"
    p.confidence_score = 0.9
    p.filters = {}
    p.created_at = None
    p.updated_at = None
    return p


# ─── 1. save_snapshot() com Redis disponível ─────────────────────────────────

@pytest.mark.asyncio
async def test_save_snapshot_returns_key_when_redis_available():
    svc = LearningSnapshotService()
    serialized = [
        {
            "pattern_key": "salary:dev:senior",
            "pattern_type": "salary_preference",
            "pattern_value": {"min": 5000},
            "sample_size": 10,
            "acceptance_rate": 0.8,
            "confidence": "high",
            "confidence_score": 0.9,
            "filters": {},
            "created_at": None,
            "updated_at": None,
        }
    ]
    # Mocka _load_patterns para evitar acesso real ao DB/SQLAlchemy
    svc._load_patterns = AsyncMock(return_value=serialized)

    db = AsyncMock()
    redis_mock = _make_redis_mock(get_return=None)

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        key = await svc.save_snapshot("company-001", db)

    assert key is not None
    assert "learning_snapshot:company-001:" in key
    redis_mock.setex.assert_called()


# ─── 2. save_snapshot() fail-safe quando Redis indisponível ──────────────────

@pytest.mark.asyncio
async def test_save_snapshot_returns_none_when_redis_unavailable():
    svc = LearningSnapshotService()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=None),
    ):
        key = await svc.save_snapshot("company-002", db)

    assert key is None


# ─── 3. get_latest_key() retorna última chave ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_latest_key_returns_last_key():
    svc = LearningSnapshotService()
    index = json.dumps(["snap:a", "snap:b", "snap:c"])
    redis_mock = _make_redis_mock(get_return=index)

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        result = await svc.get_latest_key("company-003")

    assert result == "snap:c"


# ─── 4. get_latest_key() retorna None quando índice vazio ─────────────────────

@pytest.mark.asyncio
async def test_get_latest_key_returns_none_when_empty():
    svc = LearningSnapshotService()
    redis_mock = _make_redis_mock(get_return=None)

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        result = await svc.get_latest_key("company-004")

    assert result is None


# ─── 5. list_snapshots() retorna lista ───────────────────────────────────────

@pytest.mark.asyncio
async def test_list_snapshots_returns_list():
    svc = LearningSnapshotService()
    index = json.dumps(["snap:x", "snap:y"])
    redis_mock = _make_redis_mock(get_return=index)

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        result = await svc.list_snapshots("company-005")

    assert result == ["snap:x", "snap:y"]


# ─── 6. list_snapshots() retorna [] quando Redis falha ────────────────────────

@pytest.mark.asyncio
async def test_list_snapshots_returns_empty_on_redis_failure():
    svc = LearningSnapshotService()

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(side_effect=Exception("Redis down")),
    ):
        result = await svc.list_snapshots("company-006")

    assert result == []


# ─── 7. rollback_to_latest() restaura padrões ─────────────────────────────────

@pytest.mark.asyncio
async def test_rollback_restores_patterns():
    svc = LearningSnapshotService()
    company_id = "company-007"

    payload = json.dumps([
        {
            "pattern_key": "salary:dev:senior",
            "pattern_type": "salary_preference",
            "pattern_value": {"min": 5000},
            "sample_size": 10,
            "acceptance_rate": 0.8,
            "confidence": "high",
            "confidence_score": 0.9,
            "filters": {},
        }
    ])

    index = json.dumps([_snapshot_key(company_id, "20260319T120000")])
    idx_redis = _make_redis_mock(get_return=index)
    snap_redis = _make_redis_mock(get_return=payload)

    # get_latest_key usa redis com índice; rollback usa redis com payload
    call_count = 0

    async def _redis_factory():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return idx_redis
        return snap_redis

    db = AsyncMock()
    db.commit = AsyncMock()

    # Mocka _restore_patterns para evitar acesso real ao SQLAlchemy
    svc._restore_patterns = AsyncMock()

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        _redis_factory,
    ):
        result = await svc.rollback_to_latest(company_id, db)

    assert result is True
    svc._restore_patterns.assert_called_once()
    db.commit.assert_called_once()


# ─── 8. rollback_to_latest() retorna False sem snapshots ─────────────────────

@pytest.mark.asyncio
async def test_rollback_returns_false_when_no_snapshots():
    svc = LearningSnapshotService()
    redis_mock = _make_redis_mock(get_return=None)

    db = AsyncMock()

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        AsyncMock(return_value=redis_mock),
    ):
        result = await svc.rollback_to_latest("company-008", db)

    assert result is False


# ─── 9. rollback_to_latest() fail-safe quando DB falha ───────────────────────

@pytest.mark.asyncio
async def test_rollback_returns_false_on_db_failure():
    svc = LearningSnapshotService()
    company_id = "company-009"

    payload = json.dumps([
        {
            "pattern_key": "salary:dev:senior",
            "pattern_type": "salary_preference",
            "pattern_value": {},
            "sample_size": 1,
            "acceptance_rate": None,
            "confidence": None,
            "confidence_score": None,
            "filters": {},
        }
    ])

    index = json.dumps([_snapshot_key(company_id, "20260319T130000")])
    idx_redis = _make_redis_mock(get_return=index)
    snap_redis = _make_redis_mock(get_return=payload)

    call_count = 0

    async def _redis_factory():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return idx_redis
        return snap_redis

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("DB down"))
    db.rollback = AsyncMock()

    with patch(
        "app.shared.learning.learning_snapshot_service._get_redis",
        _redis_factory,
    ):
        result = await svc.rollback_to_latest(company_id, db)

    assert result is False
    db.rollback.assert_called_once()


# ─── 10. _update_index() trunca para MAX_SNAPSHOTS ────────────────────────────

@pytest.mark.asyncio
async def test_update_index_truncates_to_max():
    company_id = "company-010"
    existing = [f"snap:{i}" for i in range(MAX_SNAPSHOTS)]
    redis_mock = _make_redis_mock(get_return=json.dumps(existing))

    await LearningSnapshotService._update_index(redis_mock, company_id, "snap:new")

    call_args = redis_mock.setex.call_args
    stored_index = json.loads(call_args[0][2])
    assert len(stored_index) == MAX_SNAPSHOTS
    assert stored_index[-1] == "snap:new"
    assert "snap:0" not in stored_index  # o mais antigo foi removido


# ─── 11. Wiring: learning_loop_service chama save_snapshot ────────────────────

@pytest.mark.asyncio
async def test_learning_loop_calls_save_snapshot_before_update():
    """Garante que o wiring em learning_loop_service.py está correto."""
    import inspect
    import app.shared.learning.learning_loop_service as llm

    source = inspect.getsource(llm)
    assert "save_snapshot" in source, "save_snapshot não encontrado em learning_loop_service"
    assert "learning_snapshot_service" in source, "import ausente"
    # Garante que save_snapshot vem antes de _update_pattern no mesmo bloco
    snap_pos = source.find("save_snapshot")
    update_pos = source.find("_update_pattern")
    assert snap_pos < update_pos, "save_snapshot deve ser chamado ANTES de _update_pattern"
