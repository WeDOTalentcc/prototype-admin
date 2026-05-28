"""
Onda 3.B3 — POST /custom-agents/{agent_id}/deployments/bulk contract.

5 testes obrigatórios:
1. Bulk cria N deployments (created list)
2. Skip duplicates (target já tem mesmo agente ativo)
3. Limite 50 (51 = ValidationError em runtime, 422)
4. Transação atômica: erro de validação rollback total
5. Audit log emitido ao criar bulk

Decisão de ambiguidade (registrada nesta sessão):
  Adotamos partial success WITH soft-skip / per-target failed list. Razão:
  - duplicates são situação esperada (cliente re-acopla agente em pool
    parcialmente cobrindo targets) → não bloqueia siblings;
  - per-target cap excedido (rare) também é per-target failure;
  - validação que afeta o batch inteiro (agent não existe, cap global)
    → 400 com rollback.
  Created/skipped/failed retornados para UI mostrar feedback granular.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1 import agent_deployments as ad_api
from app.schemas.agent_deployment import (
    BULK_TARGETS_MAX,
    BulkDeploymentRequest,
)
from lia_models.agent_deployment import DeploymentTargetType

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.company_id = "comp-bulk-1"
    return u


def _fake_deployment(*, target_id, agent_id, company_id):
    d = MagicMock()
    d.id = uuid.uuid4()
    d.agent_id = agent_id
    d.company_id = company_id
    d.target_type = "job"
    d.target_id = target_id
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
        "target_name": None,
        "trigger_mode": d.trigger_mode,
        "schedule_cron": None,
        "is_active": True,
        "config_overrides": {},
        "execution_count": 0,
        "candidates_processed": 0,
        "last_execution_at": None,
        "created_by": d.created_by,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }
    return d


async def test_bulk_create_n_targets(mock_db, mock_user, monkeypatch):
    """Bulk cria N deployments quando todos targets são novos."""
    agent_id = str(uuid.uuid4())
    t1, t2, t3 = (str(uuid.uuid4()) for _ in range(3))

    created_deps = [
        _fake_deployment(target_id=uuid.UUID(t), agent_id=uuid.UUID(agent_id), company_id=mock_user.company_id)
        for t in [t1, t2, t3]
    ]
    fake_svc = MagicMock()
    fake_svc.bulk_create_deployments = AsyncMock(return_value=(created_deps, [], []))
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_svc)

    with patch.object(
        ad_api,
        "get_audit_service" if hasattr(ad_api, "get_audit_service") else "logger",
        MagicMock(),
        create=True,
    ):
        body = BulkDeploymentRequest(
            target_type=DeploymentTargetType.JOB,
            target_ids=[t1, t2, t3],
            trigger_mode="manual",
        )
        result = await ad_api.bulk_create_deployments(
            agent_id=agent_id,
            payload=body,
            current_user=mock_user,
            db=mock_db,
            company_id=mock_user.company_id,
        )

    assert len(result.created) == 3
    assert result.skipped == []
    assert result.failed == []
    fake_svc.bulk_create_deployments.assert_awaited_once()
    mock_db.commit.assert_awaited_once()


async def test_bulk_skips_duplicates(mock_db, mock_user, monkeypatch):
    """Targets que já têm este agente são retornados como skipped, não criados."""
    agent_id = str(uuid.uuid4())
    t1, t2 = (str(uuid.uuid4()) for _ in range(2))

    new_dep = _fake_deployment(target_id=uuid.UUID(t1), agent_id=uuid.UUID(agent_id), company_id=mock_user.company_id)
    skipped = [{"target_id": t2, "reason": "duplicate_active_deployment"}]
    fake_svc = MagicMock()
    fake_svc.bulk_create_deployments = AsyncMock(return_value=([new_dep], skipped, []))
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_svc)

    body = BulkDeploymentRequest(
        target_type=DeploymentTargetType.JOB,
        target_ids=[t1, t2],
    )
    result = await ad_api.bulk_create_deployments(
        agent_id=agent_id,
        payload=body,
        current_user=mock_user,
        db=mock_db,
        company_id=mock_user.company_id,
    )

    assert len(result.created) == 1
    assert len(result.skipped) == 1
    assert result.skipped[0].target_id == t2
    assert result.skipped[0].reason == "duplicate_active_deployment"


def test_bulk_max_length_enforced():
    """51 target_ids → Pydantic ValidationError (limite 50)."""
    from pydantic import ValidationError

    ids = [str(uuid.uuid4()) for _ in range(BULK_TARGETS_MAX + 1)]
    with pytest.raises(ValidationError):
        BulkDeploymentRequest(
            target_type=DeploymentTargetType.JOB,
            target_ids=ids,
        )


def test_bulk_min_length_enforced():
    """0 target_ids → Pydantic ValidationError (min_length=1)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BulkDeploymentRequest(
            target_type=DeploymentTargetType.JOB,
            target_ids=[],
        )


async def test_bulk_value_error_triggers_rollback(mock_db, mock_user, monkeypatch):
    """Service raise ValueError (cap excedido) → 400 + rollback."""
    agent_id = str(uuid.uuid4())
    fake_svc = MagicMock()
    fake_svc.bulk_create_deployments = AsyncMock(
        side_effect=ValueError("Bulk would exceed MAX_DEPLOYMENTS_PER_AGENT")
    )
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_svc)

    body = BulkDeploymentRequest(
        target_type=DeploymentTargetType.JOB,
        target_ids=[str(uuid.uuid4())],
    )
    with pytest.raises(HTTPException) as exc:
        await ad_api.bulk_create_deployments(
            agent_id=agent_id,
            payload=body,
            current_user=mock_user,
            db=mock_db,
            company_id=mock_user.company_id,
        )
    assert exc.value.status_code == 400
    mock_db.rollback.assert_awaited()


async def test_bulk_emits_audit_log(mock_db, mock_user, monkeypatch):
    """Bulk creation emite single AuditLog entry via audit_service.log_decision."""
    agent_id = str(uuid.uuid4())
    t1 = str(uuid.uuid4())
    new_dep = _fake_deployment(target_id=uuid.UUID(t1), agent_id=uuid.UUID(agent_id), company_id=mock_user.company_id)

    fake_svc = MagicMock()
    fake_svc.bulk_create_deployments = AsyncMock(return_value=([new_dep], [], []))
    monkeypatch.setattr(ad_api, "agent_deployment_service", fake_svc)

    audit_mock = MagicMock()
    audit_mock.log_decision = AsyncMock()

    with patch(
        "app.shared.compliance.audit_service.get_audit_service",
        return_value=audit_mock,
    ):
        body = BulkDeploymentRequest(
            target_type=DeploymentTargetType.JOB,
            target_ids=[t1],
        )
        await ad_api.bulk_create_deployments(
            agent_id=agent_id,
            payload=body,
            current_user=mock_user,
            db=mock_db,
            company_id=mock_user.company_id,
        )

    audit_mock.log_decision.assert_awaited_once()
    audit_kw = audit_mock.log_decision.await_args.kwargs
    assert audit_kw["company_id"] == mock_user.company_id
    assert audit_kw["action"] == "bulk_deploy_agent"
