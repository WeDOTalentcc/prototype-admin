"""
P0 regression sensors — Approval Trigger gates (Sprint 1, 2026-06-21)

Harness: Sensor · Computacional. Pins contract:
  trigger_approval_if_required() creates ApprovalRequest + stamps job.approval_requested_at
  assert_can_publish() blocks publish when approval pending

These tests are RED until approval_trigger_service.py is implemented.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_job(
    *,
    company_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
    approval_requested_at=None,
    approval_status: str = "pendente",
    title: str = "Desenvolvedor Sr",
) -> MagicMock:
    job = MagicMock()
    job.id = job_id or uuid.uuid4()
    job.company_id = str(company_id or uuid.uuid4())
    job.approval_requested_at = approval_requested_at
    job.approval_status = approval_status
    job.approval_requested_by = None
    job.title = title
    return job


def _mock_approver(level: int = 1) -> MagicMock:
    a = MagicMock()
    a.id = uuid.uuid4()
    a.user_id = uuid.uuid4()
    a.user_name = f"Aprovador Nivel {level}"
    a.email = f"aprovador{level}@empresa.com"
    a.level = level
    return a


def _mock_approval_request() -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.approver_name = "Aprovador Nivel 1"
    r.approver_email = "aprovador1@empresa.com"
    r.status = "pending"
    return r


# ── Test 1: trigger creates ApprovalRequest + stamps approval_requested_at ──

@pytest.mark.asyncio
async def test_trigger_creates_approval_request_and_stamps_timestamp():
    """REGRA: trigger DEVE criar ApprovalRequest e setar job.approval_requested_at."""
    db = MagicMock()
    db.flush = AsyncMock()
    job = _mock_job()
    approver = _mock_approver(level=1)
    approval_req = _mock_approval_request()

    with (
        patch(
            "app.domains.job_creation.services.approval_trigger_service.ApproverRepository"
        ) as MockApproverRepo,
        patch(
            "app.domains.job_creation.services.approval_trigger_service.ApprovalsRepository"
        ) as MockApprovalsRepo,
    ):
        mock_approver_repo = AsyncMock()
        mock_approver_repo.list_for_company.return_value = [approver]
        MockApproverRepo.return_value = mock_approver_repo

        mock_approvals_repo = AsyncMock()
        mock_approvals_repo.get_pending_by_target.return_value = []
        mock_approvals_repo.add_and_flush.return_value = approval_req
        MockApprovalsRepo.return_value = mock_approvals_repo

        from app.domains.job_creation.services.approval_trigger_service import (
            trigger_approval_if_required,
        )

        result = await trigger_approval_if_required(
            job,
            requested_by_name="Recrutador",
            requested_by_email="recruiter@empresa.com",
            db=db,
        )

    assert len(result) == 1, "Deve criar 1 ApprovalRequest para 1 aprovador"
    assert job.approval_requested_at is not None, "Deve setar approval_requested_at"
    assert job.approval_requested_by == "recruiter@empresa.com"
    mock_approvals_repo.add_and_flush.assert_called_once()


# ── Test 2: idempotency ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trigger_is_idempotent_when_approval_already_pending():
    """REGRA: chamada dupla NAO deve criar segundo ApprovalRequest."""
    db = MagicMock()
    job = _mock_job()
    approver = _mock_approver(level=1)
    existing_req = _mock_approval_request()

    with (
        patch(
            "app.domains.job_creation.services.approval_trigger_service.ApproverRepository"
        ) as MockApproverRepo,
        patch(
            "app.domains.job_creation.services.approval_trigger_service.ApprovalsRepository"
        ) as MockApprovalsRepo,
    ):
        mock_approver_repo = AsyncMock()
        mock_approver_repo.list_for_company.return_value = [approver]
        MockApproverRepo.return_value = mock_approver_repo

        mock_approvals_repo = AsyncMock()
        mock_approvals_repo.get_pending_by_target.return_value = [existing_req]
        MockApprovalsRepo.return_value = mock_approvals_repo

        from app.domains.job_creation.services.approval_trigger_service import (
            trigger_approval_if_required,
        )

        result = await trigger_approval_if_required(
            job,
            requested_by_name="Recrutador",
            requested_by_email="recruiter@empresa.com",
            db=db,
        )

    assert result == [], "Deve retornar lista vazia (noop idempotente)"
    mock_approvals_repo.add_and_flush.assert_not_called()


# ── Test 3: no approvers = noop ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trigger_noop_when_no_approvers_configured():
    """REGRA: sem aprovadores configurados = sem bloqueio, noop."""
    db = MagicMock()
    job = _mock_job()
    original_ts = job.approval_requested_at

    with patch(
        "app.domains.job_creation.services.approval_trigger_service.ApproverRepository"
    ) as MockApproverRepo:
        mock_approver_repo = AsyncMock()
        mock_approver_repo.list_for_company.return_value = []
        MockApproverRepo.return_value = mock_approver_repo

        from app.domains.job_creation.services.approval_trigger_service import (
            trigger_approval_if_required,
        )

        result = await trigger_approval_if_required(
            job,
            requested_by_name="Recrutador",
            requested_by_email="recruiter@empresa.com",
            db=db,
        )

    assert result == [], "Deve retornar lista vazia"
    assert job.approval_requested_at == original_ts, "Nao deve mutar o job"


# ── Test 4: publish blocked when approval pending ────────────────────────────

@pytest.mark.asyncio
async def test_publish_blocked_when_approval_pending():
    """REGRA: assert_can_publish DEVE levantar ApprovalPendingError se pendente."""
    db = MagicMock()
    job = _mock_job(
        approval_requested_at=datetime(2026, 6, 21, 10, 0),
        approval_status="pendente",
    )
    pending_req = _mock_approval_request()

    with patch(
        "app.domains.job_creation.services.approval_trigger_service.ApprovalsRepository"
    ) as MockApprovalsRepo:
        mock_approvals_repo = AsyncMock()
        mock_approvals_repo.get_pending_by_target.return_value = [pending_req]
        MockApprovalsRepo.return_value = mock_approvals_repo

        from app.domains.job_creation.services.approval_trigger_service import (
            ApprovalPendingError,
            assert_can_publish,
        )

        with pytest.raises(ApprovalPendingError):
            await assert_can_publish(job, db=db)


# ── Test 5: publish allowed when approved ────────────────────────────────────

@pytest.mark.asyncio
async def test_publish_allowed_when_approval_status_aprovada():
    """REGRA: publish OK quando approval_status=aprovada (nao bloqueia)."""
    db = MagicMock()
    job = _mock_job(
        approval_requested_at=datetime(2026, 6, 21, 10, 0),
        approval_status="aprovada",
    )

    from app.domains.job_creation.services.approval_trigger_service import (
        assert_can_publish,
    )

    # Nao deve levantar excecao
    await assert_can_publish(job, db=db)
