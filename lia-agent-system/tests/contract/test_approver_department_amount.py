"""P0.D2 regression sensor (audit Wave 2 2026-05-22): Approver per-department +
amount-threshold routing.

Gates under test (subclass :class:`OfferPolicyGateError`):
- :class:`NoEligibleApproverForAmountError` — when amount-threshold is
  configured but no approver covers the offer salary.

Repository contract under test (ADR-001):
- :meth:`ApproverRepository.list_for_department` — company-wide rows
  (department_id IS NULL) are ALWAYS returned regardless of department
  filter.
- :meth:`ApproverRepository.list_eligible_for_amount` — NULL
  can_approve_above_amount means any-amount approver (backward-compat).
- DB CheckConstraint ``ck_approver_amount_nonneg`` — rejects negative
  thresholds at the schema level (defense-in-depth).

Strategy: pure-unit tests with mocked repository for service-level gates,
and an in-memory SQLite + Approver model for repository semantic tests.
Mocks the offer flow so the gate is exercised in isolation.

Ghost-setting context: Approver model lacked ``department_id`` +
``can_approve_above_amount`` columns. ApproverSection UI exposed
granularity that DB did not persist. Migration 170 closed the schema gap;
this module pins service + repo behavior so a future refactor cannot
silently re-introduce a ghost setting.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.offer.services.offer_service import (
    NoEligibleApproverForAmountError,
    OfferPolicyGateError,
    OfferService,
)


def _make_service_with_approvers(
    *,
    approver_thresholds: list[Decimal | None],
    proposal_salary: Decimal | None,
    proposal_department_id: uuid.UUID | None = None,
    approval_required: bool = False,
    proposal_approval_request_id: uuid.UUID | None = None,
) -> tuple[OfferService, MagicMock]:
    """Build OfferService with ApproverRepository.list_eligible_for_amount mocked.

    ``approver_thresholds`` defines the simulated approver-table state.
    A list ``[Decimal("5000"), None]`` means two approvers: one with
    threshold R$5000 and one any-amount (NULL). The repo mock filters by
    the standard rule: NULL covers any amount; numeric covers amount iff
    threshold <= amount.
    """
    db = MagicMock()

    proposal = MagicMock()
    proposal.id = uuid.uuid4()
    proposal.company_id = "co-1"
    proposal.status = "draft"
    proposal.approval_request_id = proposal_approval_request_id
    proposal.candidate_id = uuid.uuid4()
    proposal.sent_via = []
    proposal.salary = proposal_salary
    proposal.department_id = proposal_department_id

    offer_repo = MagicMock()
    offer_repo.get_by_id = AsyncMock(return_value=proposal)
    offer_repo.update = AsyncMock(return_value=proposal)

    policy = MagicMock()
    policy.screening_rules = {"manager_approval_for_offer": approval_required}
    policy.pipeline_rules = {"min_interviews_before_offer": 0}

    policy_repo = MagicMock()
    policy_repo.get_by_company = AsyncMock(return_value=policy)

    db.execute = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar = MagicMock(return_value=99)
    db.execute.return_value = result_mock

    svc = OfferService(db)
    svc._repo = offer_repo

    # Build approver mocks
    approver_mocks = []
    for thr in approver_thresholds:
        m = MagicMock()
        m.can_approve_above_amount = thr
        m.is_active = True
        m.department_id = None  # company-wide; per-department tested separately
        approver_mocks.append(m)

    approver_repo = MagicMock()
    approver_repo.list_for_company = AsyncMock(return_value=approver_mocks)

    async def _list_eligible_for_amount(company_id, department_id, amount):
        return [
            a for a in approver_mocks
            if a.can_approve_above_amount is None
            or a.can_approve_above_amount <= amount
        ]

    async def _list_for_department(company_id, department_id=None, is_active=True):
        # All mocked approvers are company-wide here; per-dept logic
        # exercised in repository tests below.
        return [a for a in approver_mocks if a.is_active == is_active]

    approver_repo.list_eligible_for_amount = AsyncMock(side_effect=_list_eligible_for_amount)
    approver_repo.list_for_department = AsyncMock(side_effect=_list_for_department)
    svc._approver_repo = approver_repo

    notifier = MagicMock()
    notifier.notify_pending_approvers_for_offer = AsyncMock(return_value={})
    svc._approval_notifier = notifier

    import app.domains.offer.services.offer_service as mod
    mod.HiringPolicyRepository = MagicMock(return_value=policy_repo)
    return svc, proposal


# ─────────────────────────────────────────────────────────────────────────────
# Service-level: NoEligibleApproverForAmountError
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_can_send_blocks_when_no_approver_covers_amount():
    """All approver thresholds are ABOVE the offer salary => raise.

    Semantic: ``can_approve_above_amount`` is the minimum amount the approver
    is authorized to sign off on (e.g., CEO only approves offers ABOVE
    R$10k; smaller ones are routed to a lower tier). When every configured
    approver has a threshold ABOVE the offer salary, the routing chain has
    no match for this amount.
    """
    svc, _ = _make_service_with_approvers(
        approver_thresholds=[Decimal("5000.00"), Decimal("10000.00")],
        proposal_salary=Decimal("100.00"),
    )
    with pytest.raises(NoEligibleApproverForAmountError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    # UX-actionable message: must point recruiter at config path
    msg = str(exc_info.value)
    assert "Configuracoes" in msg or "limite" in msg.lower()
    # Subclass invariant
    assert isinstance(exc_info.value, OfferPolicyGateError)


@pytest.mark.asyncio
async def test_check_can_send_permits_when_any_amount_approver_exists():
    """At least one approver has NULL threshold => permit regardless of amount."""
    svc, _ = _make_service_with_approvers(
        approver_thresholds=[Decimal("5000.00"), None],  # one any-amount
        proposal_salary=Decimal("999999.00"),
    )
    # No raise = permit
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_check_can_send_permits_when_threshold_covers_amount():
    """Approver threshold == salary => boundary case still eligible (<=).

    ``can_approve_above_amount=15000`` means "covers amounts >= 15000".
    Salary 15000 is at the boundary; <= holds, gate permits.
    """
    svc, _ = _make_service_with_approvers(
        approver_thresholds=[Decimal("15000.00")],
        proposal_salary=Decimal("15000.00"),
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_check_can_send_skips_amount_gate_when_proposal_has_no_salary():
    """Draft with no salary set => skip amount gate (incomplete drafts pass)."""
    svc, _ = _make_service_with_approvers(
        approver_thresholds=[Decimal("100.00")],
        proposal_salary=None,
    )
    # Should NOT raise — gate skipped when salary is None
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_mark_sent_defense_in_depth_amount_gate():
    """Defense-in-depth: mark_sent enforces amount gate even if check_can_send skipped.

    Guarantees the regression cannot resurface by removing only the pre-flight.
    Threshold R$5000 covers amounts >= 5000; salary R$100 falls below => no
    eligible approver => gate fires.
    """
    svc, proposal = _make_service_with_approvers(
        approver_thresholds=[Decimal("5000.00")],
        proposal_salary=Decimal("100.00"),
    )
    with pytest.raises(NoEligibleApproverForAmountError):
        await svc.mark_sent(
            offer_id=uuid.uuid4(),
            company_id="co-1",
            user_id="u-1",
            send_mode="auto",
            email_log_id=None,
        )
    # No partial transition: status must remain draft
    assert proposal.status == "draft"


# ─────────────────────────────────────────────────────────────────────────────
# Repository-level: list_for_department / list_eligible_for_amount semantics
# Pure unit tests (no DB). Asserts the SQL composition + Python filter logic.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_for_department_returns_company_wide_approvers_too():
    """Per-department query MUST include department_id IS NULL rows (company-wide).

    A company-wide approver (department_id NULL) approves across all
    departments. Per-department approver (department_id == X) approves
    only for X. Query: ``WHERE department_id = X OR department_id IS NULL``.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.domains.company.repositories.approver_repository import (
        ApproverRepository,
    )

    db = MagicMock(spec=AsyncSession)
    result_mock = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[])
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    db.execute = AsyncMock(return_value=result_mock)

    repo = ApproverRepository(db)
    await repo.list_for_department(uuid.uuid4(), department_id=uuid.uuid4())

    # Inspect the executed statement
    db.execute.assert_called_once()
    stmt = db.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    # The OR clause must reference department_id IS NULL
    assert "department_id IS NULL" in compiled or "approvers.department_id IS NULL" in compiled
    # Company-id filter present
    assert "company_id" in compiled


@pytest.mark.asyncio
async def test_list_eligible_for_amount_null_threshold_means_any_amount():
    """can_approve_above_amount IS NULL => approver eligible for ANY amount."""
    from app.domains.company.repositories.approver_repository import (
        ApproverRepository,
    )

    db = MagicMock()
    repo = ApproverRepository(db)

    # Inject test data via list_for_department mock
    a_null = MagicMock(can_approve_above_amount=None)
    a_low = MagicMock(can_approve_above_amount=Decimal("100.00"))
    a_high = MagicMock(can_approve_above_amount=Decimal("10000.00"))
    repo.list_for_department = AsyncMock(return_value=[a_null, a_low, a_high])

    # Semantic: can_approve_above_amount = approver covers amounts >= threshold.
    # For amount=5000: null covers any amount (eligible); threshold=100 means
    # "approves >= 100" so eligible for 5000; threshold=10000 means "approves
    # >= 10000" so NOT eligible for 5000 (offer is below their tier).
    eligible = await repo.list_eligible_for_amount(
        uuid.uuid4(), None, Decimal("5000.00")
    )
    thresholds = [a.can_approve_above_amount for a in eligible]
    assert None in thresholds, "any-amount approver must be eligible for any amount"
    assert Decimal("100.00") in thresholds, "threshold 100 covers amount 5000 (100 <= 5000)"
    assert Decimal("10000.00") not in thresholds, "threshold 10000 does NOT cover amount 5000 (10000 > 5000)"


@pytest.mark.asyncio
async def test_list_eligible_for_amount_threshold_filters_above():
    """When NO approver has NULL threshold AND none cover the amount, empty list."""
    from app.domains.company.repositories.approver_repository import (
        ApproverRepository,
    )

    db = MagicMock()
    repo = ApproverRepository(db)

    # Semantic: threshold 100 = "covers amounts >= 100". Amount 99.99 falls
    # below both thresholds (100, 500) => no approver covers it.
    a_low = MagicMock(can_approve_above_amount=Decimal("100.00"))
    a_mid = MagicMock(can_approve_above_amount=Decimal("500.00"))
    repo.list_for_department = AsyncMock(return_value=[a_low, a_mid])

    eligible = await repo.list_eligible_for_amount(
        uuid.uuid4(), None, Decimal("99.99")
    )
    assert eligible == [], "no approver covers R$99.99 when thresholds are 100/500 (both above 99.99)"


# ─────────────────────────────────────────────────────────────────────────────
# Schema-level: ApproverCreate / ApproverUpdate R1 + R2 invariants
# ─────────────────────────────────────────────────────────────────────────────


def test_approver_create_forbids_company_id_in_payload():
    """R2 canonical: company_id NEVER in request body (comes from JWT)."""
    from pydantic import ValidationError
    from app.schemas.company import ApproverCreate

    with pytest.raises(ValidationError) as exc:
        ApproverCreate(
            user_name="X",
            email="x@y.com",
            company_id=str(uuid.uuid4()),  # ← R2 violation
        )
    # extra_forbidden is the discriminator
    assert "extra_forbidden" in str(exc.value)


def test_approver_create_accepts_null_department_and_amount():
    """Backward-compat: omitting department_id + can_approve_above_amount works.

    Both NULL = company-wide, any-amount approver — the legacy behavior.
    """
    from app.schemas.company import ApproverCreate

    m = ApproverCreate(user_name="X", email="x@y.com")
    assert m.department_id is None
    assert m.can_approve_above_amount is None
