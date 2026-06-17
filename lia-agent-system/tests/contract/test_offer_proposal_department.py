"""
Camada 3 Item 3 contract sensor (2026-05-22): per-department approver routing.

This pins three contracts now that ``OfferProposal.department_id`` is a real
column (migration 172) instead of a ``getattr(proposal, "department_id", None)``
phantom property:

  1. ``OfferProposal.department_id`` is a declared SQLAlchemy column.
  2. ``OfferService.check_can_send`` reads ``proposal.department_id``
     **directly** (no getattr fallback) and passes it to
     ``_has_eligible_approver_for_amount``.
  3. Backward-compat: offers WITHOUT a department_id (NULL) still resolve
     via the company-wide approver path.

Strategy: pure-unit, mock-driven. We mock
``_has_eligible_approver_for_amount`` to capture the actual ``department_id``
argument the service forwards. No DB required — the contract is at the
service layer.

Audit anchor:
  ~/Documents/wedotalent_audit_2026-05-21/menu_configuracoes_inteligencia_agentes.md
  (Camada 2-D: per-department approver routing depends on this column).
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.offer.services.offer_service import (
    NoEligibleApproverForAmountError,
    OfferService,
)


def _make_service_with(
    *,
    department_id: uuid.UUID | str | None,
    salary: Decimal | None = Decimal("8500.00"),
    approval_required: bool = False,
    proposal_approval_request_id: uuid.UUID | None = None,
    eligible_amount_ok: bool = True,
    min_interviews_before_offer: int = 0,
    completed_interviews_count: int = 99,
    approvers_configured: int = 1,
) -> tuple[OfferService, MagicMock, MagicMock]:
    """Build an OfferService instance with all repos mocked.

    Returns (service, proposal, has_eligible_approver_mock). The third
    return is the AsyncMock injected over
    ``_has_eligible_approver_for_amount`` so each test can assert on the
    exact ``(company_id, department_id, salary)`` triple the service
    forwarded.
    """
    db = MagicMock()

    proposal = MagicMock()
    proposal.id = uuid.uuid4()
    proposal.company_id = "co-1"
    proposal.status = "draft"
    proposal.approval_request_id = proposal_approval_request_id
    proposal.candidate_id = uuid.uuid4()
    proposal.sent_via = []
    proposal.salary = salary
    # Canonical: department_id is now a real attribute (not getattr fallback).
    proposal.department_id = department_id

    offer_repo = MagicMock()
    offer_repo.get_by_id = AsyncMock(return_value=proposal)

    policy = MagicMock()
    policy.screening_rules = {"manager_approval_for_offer": approval_required}
    policy.pipeline_rules = {
        "min_interviews_before_offer": min_interviews_before_offer,
    }
    policy_repo = MagicMock()
    policy_repo.get_by_company = AsyncMock(return_value=policy)

    # Interview-count query (Gate 2 — kept inert).
    db.execute = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar = MagicMock(return_value=completed_interviews_count)
    db.execute.return_value = result_mock

    svc = OfferService(db)
    svc._repo = offer_repo

    approver_repo = MagicMock()
    approvers_list = [MagicMock() for _ in range(approvers_configured)]
    approver_repo.list_for_company = AsyncMock(return_value=approvers_list)
    svc._approver_repo = approver_repo
    notifier = MagicMock()
    notifier.notify_pending_approvers_for_offer = AsyncMock(
        return_value={
            "approvers_notified": [str(uuid.uuid4()) for _ in range(approvers_configured)],
            "approvers_skipped_email_only": [],
            "count": approvers_configured,
            "no_approvers_configured": approvers_configured == 0,
        }
    )
    svc._approval_notifier = notifier

    import app.domains.offer.services.offer_service as mod
    mod.HiringPolicyRepository = MagicMock(return_value=policy_repo)

    # Stub the amount-routing gate so we can inspect its kwargs.
    has_eligible_mock = AsyncMock(return_value=eligible_amount_ok)
    svc._has_eligible_approver_for_amount = has_eligible_mock

    return svc, proposal, has_eligible_mock


def test_offer_proposal_has_department_id_column():
    """Camada 3 Item 3 / R1: the column must exist as a real SQLAlchemy
    Column (not getattr-only). Detects regression where migration 172 is
    reverted but the service still expects the attribute."""
    from lia_models.offer_proposal import OfferProposal

    cols = {c.name for c in OfferProposal.__table__.columns}
    assert "department_id" in cols, (
        "OfferProposal.department_id column missing. Migration 172 was "
        "expected to add it. Check alembic/versions/172_offer_proposal_department.py."
    )

    dept_col = OfferProposal.__table__.columns["department_id"]
    assert dept_col.nullable is True, (
        "department_id must be nullable for backward compatibility — "
        "existing offer_proposals rows have NULL."
    )
    fks = list(dept_col.foreign_keys)
    assert len(fks) == 1, "department_id must have exactly one foreign key."
    assert fks[0].column.table.name == "departments", (
        "department_id FK must point to departments.id."
    )


@pytest.mark.asyncio
async def test_check_can_send_forwards_real_department_id():
    """R2: the service reads proposal.department_id directly and forwards
    it to the amount-routing helper. No getattr fallback."""
    dept_id = uuid.uuid4()
    svc, _proposal, has_eligible_mock = _make_service_with(
        department_id=dept_id,
        salary=Decimal("12000.00"),
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")
    # has_eligible_approver_for_amount called once with our department_id
    has_eligible_mock.assert_awaited_once()
    args, kwargs = has_eligible_mock.await_args
    # Positional order: company_id, department_id, salary
    assert args[0] == "co-1"
    assert args[1] == dept_id, (
        f"Expected department_id={dept_id} forwarded to amount-routing, "
        f"got {args[1]!r}. Service may have regressed to getattr fallback."
    )
    assert args[2] == Decimal("12000.00")


@pytest.mark.asyncio
async def test_check_can_send_backward_compat_offer_without_department_id():
    """R3: offers with department_id=None (e.g. legacy rows pre-migration
    172, or offers created without a department) still flow through and
    use the company-wide approver path."""
    svc, _proposal, has_eligible_mock = _make_service_with(
        department_id=None,
        salary=Decimal("5000.00"),
    )
    # Should NOT raise — None department_id is valid (company-wide).
    await svc.check_can_send(uuid.uuid4(), "co-1")
    has_eligible_mock.assert_awaited_once()
    args, _ = has_eligible_mock.await_args
    assert args[1] is None, (
        "department_id=None must be forwarded as-is so the helper can "
        "select company-wide approvers (WHERE department_id IS NULL)."
    )


@pytest.mark.asyncio
async def test_check_can_send_raises_when_no_eligible_approver_for_department():
    """Companion: when no approver covers the salary for the chosen
    department, the gate fires. Confirms the routing is wired end-to-end."""
    svc, _proposal, _ = _make_service_with(
        department_id=uuid.uuid4(),
        salary=Decimal("99999.00"),
        eligible_amount_ok=False,
    )
    with pytest.raises(NoEligibleApproverForAmountError) as exc:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    assert "Departamentos" in str(exc.value) or "Aprovadores" in str(exc.value)
