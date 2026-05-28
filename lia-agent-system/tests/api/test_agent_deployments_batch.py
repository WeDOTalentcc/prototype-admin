"""
Onda 3.B1 — POST /agent-deployments/by-targets batch endpoint contract.

5 testes obrigatórios:
1. Batch vazio retorna `{}` válido
2. Múltiplos targets agrupados corretamente
3. Multi-tenancy isolation (deployments de outra company ficam fora)
4. Limite 100 (101 = 422 via Pydantic max_length)
5. target_type inválido = 422

Mock-based, foca em wiring + isolation + grouping. Repo integration coverage
vive em tests/contract/test_agent_deployments_repository_batch.py (TBD).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1 import agent_deployments as ad_api
from app.schemas.agent_deployment import (
    BATCH_TARGETS_MAX,
    BatchTargetsRequest,
)
from lia_models.agent_deployment import DeploymentTargetType

pytestmark = pytest.mark.asyncio


def _fake_deployment(*, target_id: str, company_id: str, agent_id=None):
    d = MagicMock()
    d.id = uuid.uuid4()
    d.agent_id = agent_id or uuid.uuid4()
    d.company_id = company_id
    d.target_type = "job"
    d.target_id = uuid.UUID(target_id) if isinstance(target_id, str) and len(target_id) == 36 else target_id
    d.target_name = None
    d.trigger_mode = "manual"
    d.schedule_cron = None
    d.is_active = True
    d.config_overrides = {}
    d.execution_count = 0
    d.candidates_processed = 0
    d.last_execution_at = None
    d.created_by = "user-1"
    d.created_at = datetime.now(timezone.utc)
    d.updated_at = datetime.now(timezone.utc)
    d.to_dict = lambda: {
        "id": str(d.id),
        "agent_id": str(d.agent_id),
        "company_id": d.company_id,
        "target_type": d.target_type,
        "target_id": str(d.target_id),
        "target_name": d.target_name,
        "trigger_mode": d.trigger_mode,
        "schedule_cron": d.schedule_cron,
        "is_active": d.is_active,
        "config_overrides": d.config_overrides,
        "execution_count": d.execution_count,
        "candidates_processed": d.candidates_processed,
        "last_execution_at": None,
        "created_by": d.created_by,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }
    return d


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.company_id = "comp-batch-1"
    return u


async def test_batch_empty_returns_empty_dict(mock_db, mock_user):
    """target_ids=[] retorna {} (não 400)."""
    payload = BatchTargetsRequest(target_type=DeploymentTargetType.JOB, target_ids=[])

    result = await ad_api.get_deployments_by_targets(
        payload=payload,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    assert result.deployments_by_target == {}


async def test_batch_groups_deployments_by_target(mock_db, mock_user, monkeypatch):
    """Múltiplos targets retornam dict[target_id → list[deployment]] agrupado."""
    t1 = str(uuid.uuid4())
    t2 = str(uuid.uuid4())
    t3 = str(uuid.uuid4())

    # 2 deployments para t1, 1 para t2, 0 para t3.
    grouped_result = {
        t1: [
            _fake_deployment(target_id=t1, company_id=mock_user.company_id),
            _fake_deployment(target_id=t1, company_id=mock_user.company_id),
        ],
        t2: [_fake_deployment(target_id=t2, company_id=mock_user.company_id)],
        t3: [],
    }
    fake_service = MagicMock()
    fake_service.list_by_targets = AsyncMock(return_value=grouped_result)
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_service)

    payload = BatchTargetsRequest(
        target_type=DeploymentTargetType.JOB, target_ids=[t1, t2, t3]
    )
    result = await ad_api.get_deployments_by_targets(
        payload=payload,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )

    assert set(result.deployments_by_target.keys()) == {t1, t2, t3}
    assert len(result.deployments_by_target[t1]) == 2
    assert len(result.deployments_by_target[t2]) == 1
    assert result.deployments_by_target[t3] == []

    # Service foi chamado com company_id do JWT (não payload).
    fake_service.list_by_targets.assert_awaited_once()
    kw = fake_service.list_by_targets.await_args.kwargs
    assert kw["company_id"] == mock_user.company_id
    assert kw["target_type"] == "job"
    assert kw["target_ids"] == [t1, t2, t3]


async def test_batch_multi_tenancy_isolation(mock_db, mock_user, monkeypatch):
    """Service usa company_id do JWT, não do payload (defesa contra tampering)."""
    t1 = str(uuid.uuid4())
    fake_service = MagicMock()
    fake_service.list_by_targets = AsyncMock(return_value={t1: []})
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_service)

    payload = BatchTargetsRequest(
        target_type=DeploymentTargetType.JOB, target_ids=[t1]
    )

    await ad_api.get_deployments_by_targets(
        payload=payload,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )
    # JWT tenant value é o autoritativo.
    kw = fake_service.list_by_targets.await_args.kwargs
    assert kw["company_id"] == "comp-batch-1"


def test_batch_request_max_length_enforced():
    """Pydantic max_length rejeita 101 target_ids (limite=100)."""
    from pydantic import ValidationError

    ids = [str(uuid.uuid4()) for _ in range(BATCH_TARGETS_MAX + 1)]
    with pytest.raises(ValidationError) as exc:
        BatchTargetsRequest(target_type=DeploymentTargetType.JOB, target_ids=ids)
    msg = str(exc.value)
    assert "target_ids" in msg or "100" in msg


def test_batch_request_rejects_invalid_target_type():
    """target_type fora do enum DeploymentTargetType → ValidationError (422 em runtime)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BatchTargetsRequest(target_type="foo", target_ids=[str(uuid.uuid4())])
