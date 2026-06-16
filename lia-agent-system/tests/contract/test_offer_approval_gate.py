"""
P0-2 + P1-9 regression sensor (audit 2026-05-21): company hiring policy gates
must intercept ``OfferService.check_can_send`` AND ``OfferService.mark_sent``.

Gate family under test (all subclass :class:`OfferPolicyGateError`):
- :class:`ManagerApprovalRequiredError` (P0-2) — toggle
  ``pipeline_rules.manager_approval_for_offer``.
- :class:`MinInterviewsNotMetError` (P1-9) — field
  ``pipeline_rules.min_interviews_before_offer`` vs. count of completed
  interviews for the candidate.

Ghost-gate context: both fields were visible in Configurações → Políticas
de Recrutamento but ignored by every write path in ``app/domains/offer/``.
This module pins both gates so any future refactor that drops one fails CI.

Strategy: pure-unit test with mocked repositories and patched Interview
model query. We do NOT spin up a real DB session — that would be an
integration test belonging to ``tests/integration/``. This file lives in
``tests/contract/`` because the contract under test is: "if policy refuses,
the service MUST raise an OfferPolicyGateError BEFORE any side effect."
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.offer.services.offer_service import (
    ManagerApprovalRequiredError,
    MinInterviewsNotMetError,
    NoApproverConfiguredError,
    OfferPolicyGateError,
    OfferService,
)


def _make_service_with(
    *,
    approval_required: bool = False,
    proposal_approval_request_id: uuid.UUID | None = None,
    proposal_status: str = "draft",
    min_interviews_before_offer: int = 0,
    completed_interviews_count: int = 99,
    candidate_id: uuid.UUID | None = None,
    approvers_configured: int = 1,
) -> tuple[OfferService, MagicMock]:
    """Build an OfferService with both repositories and Interview count mocked.

    Returns the service + the proposal mock so callers can assert on side
    effects like ``proposal.status`` post-mark_sent.

    Defaults (``min_interviews_before_offer=0``, ``completed_interviews_count=99``)
    deliberately set min-interviews gate to OFF / never-fires so legacy P0-2
    tests behave identically — only tests that explicitly opt into the new
    P1-9 gate by overriding both params exercise that code path.
    """
    db = MagicMock()

    proposal = MagicMock()
    proposal.id = uuid.uuid4()
    proposal.company_id = "co-1"
    proposal.status = proposal_status
    proposal.approval_request_id = proposal_approval_request_id
    proposal.candidate_id = candidate_id if candidate_id is not None else uuid.uuid4()
    proposal.sent_via = []

    offer_repo = MagicMock()
    offer_repo.get_by_id = AsyncMock(return_value=proposal)
    offer_repo.update = AsyncMock(return_value=proposal)

    policy = MagicMock()
    policy.screening_rules = {}  # manager_approval_for_offer moved to pipeline_rules (fix 2026-05-24)
    policy.pipeline_rules = {
        "manager_approval_for_offer": approval_required,
        "min_interviews_before_offer": min_interviews_before_offer,
    }

    policy_repo = MagicMock()
    policy_repo.get_by_company = AsyncMock(return_value=policy)

    # Mock the SQLAlchemy execute used inside _check_min_interviews_met.
    # The chain is: db.execute(stmt) -> result, result.scalar() -> int.
    db.execute = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar = MagicMock(return_value=completed_interviews_count)
    db.execute.return_value = result_mock

    svc = OfferService(db)
    svc._repo = offer_repo
    # P0.D1 (2026-05-22): inject ApproverRepository mock so the new
    # ``_has_active_approvers`` gate sees the configured count.
    approver_repo = MagicMock()
    approvers_list = [MagicMock() for _ in range(approvers_configured)]
    approver_repo.list_for_company = AsyncMock(return_value=approvers_list)
    svc._approver_repo = approver_repo
    # ApprovalNotificationService mock - records calls; never raises.
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
    # Patch the HiringPolicyRepository constructor inside the service so it
    # returns our mock instance regardless of the db arg.
    import app.domains.offer.services.offer_service as mod
    mod.HiringPolicyRepository = MagicMock(return_value=policy_repo)
    return svc, proposal


@pytest.mark.asyncio
async def test_check_can_send_raises_when_policy_requires_approval_and_no_evidence():
    """The gate fires: policy ON, draft has no approval_request_id."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
    )
    with pytest.raises(ManagerApprovalRequiredError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    # Message must point recruiter at the Configuracoes path so the UX is
    # actionable, not just a refusal.
    assert "Aprovacao Gestor" in str(exc_info.value)
    assert "Politicas de Recrutamento" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_can_send_permits_when_policy_off_even_without_evidence():
    """Policy OFF — sending is free regardless of approval evidence."""
    svc, _ = _make_service_with(
        approval_required=False,
        proposal_approval_request_id=None,
    )
    # Returns None on permit (no exception).
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_check_can_send_permits_when_approval_evidence_present():
    """Policy ON but draft has approval_request_id → permit."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=uuid.uuid4(),
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_mark_sent_blocks_when_policy_requires_approval():
    """Defense-in-depth: even if a caller skipped check_can_send, mark_sent
    also enforces the gate. Guarantees the bug cannot resurface by removing
    the pre-flight check alone."""
    svc, proposal = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
    )
    with pytest.raises(ManagerApprovalRequiredError):
        await svc.mark_sent(
            offer_id=uuid.uuid4(),
            company_id="co-1",
            user_id="u-1",
            send_mode="auto",
            email_log_id=None,
        )
    # Status MUST remain 'draft' — no partial transition.
    assert proposal.status == "draft"


@pytest.mark.asyncio
async def test_mark_sent_proceeds_when_policy_off():
    """Sanity: with policy OFF, mark_sent transitions to 'sent' normally."""
    svc, proposal = _make_service_with(
        approval_required=False,
        proposal_approval_request_id=None,
    )
    # Audit decoration uses a side-effect-free call we let succeed silently.
    # mark_sent calls AuditService().log_decision_in_session inside a try/except
    # so the audit failure does not break the test.
    await svc.mark_sent(
        offer_id=uuid.uuid4(),
        company_id="co-1",
        user_id="u-1",
        send_mode="auto",
        email_log_id=None,
    )
    assert proposal.status == "sent"


# ----------------------------------------------------------------------------
# P1-9 — MinInterviewsNotMetError
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_can_send_raises_when_interviews_below_threshold():
    """Gate fires: policy requires 3 interviews, candidate has 1."""
    svc, _ = _make_service_with(
        min_interviews_before_offer=3,
        completed_interviews_count=1,
    )
    with pytest.raises(MinInterviewsNotMetError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    msg = str(exc_info.value)
    assert "3" in msg
    assert "Minimo de Entrevistas" in msg or "minimo" in msg.lower()


@pytest.mark.asyncio
async def test_check_can_send_permits_when_interviews_meet_threshold():
    """Candidate has exactly the minimum → permit (boundary)."""
    svc, _ = _make_service_with(
        min_interviews_before_offer=2,
        completed_interviews_count=2,
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_check_can_send_permits_when_interviews_exceed_threshold():
    """Candidate has more than the minimum → permit."""
    svc, _ = _make_service_with(
        min_interviews_before_offer=2,
        completed_interviews_count=5,
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_check_can_send_permits_when_threshold_is_zero():
    """Policy field set to 0 = explicit opt-out → gate must not fire even
    with zero completed interviews."""
    svc, _ = _make_service_with(
        min_interviews_before_offer=0,
        completed_interviews_count=0,
    )
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_min_interviews_gate_fails_open_on_db_error():
    """If the count query fails entirely (DB outage), the gate must NOT
    block legitimate offers. The compliance trade-off: prefer false negative
    (offer goes out without enforcement) over false positive (legitimate
    offer blocked) when the infrastructure layer is misbehaving. SRE picks
    up the warning log; the audit trail surfaces the silent skip."""
    svc, _ = _make_service_with(
        min_interviews_before_offer=99,
        completed_interviews_count=0,
    )
    # Force both query paths to fail.
    async def _always_raise(*_a, **_kw):
        raise RuntimeError("simulated db outage")
    svc._db.execute = _always_raise
    # Should NOT raise — fail-open is the documented behavior.
    await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_gate_hierarchy_caught_by_parent_class():
    """LLM tool catches ``OfferPolicyGateError`` to discriminate via
    ``.reason``. Pin that both subclasses are caught by the parent and that
    ``.reason`` is set per the canonical mapping."""
    # P0-2 path
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
    )
    with pytest.raises(OfferPolicyGateError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    assert exc_info.value.reason == "manager_approval_required"

    # P1-9 path
    svc, _ = _make_service_with(
        min_interviews_before_offer=5,
        completed_interviews_count=1,
    )
    with pytest.raises(OfferPolicyGateError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    assert exc_info.value.reason == "min_interviews_not_met"


@pytest.mark.asyncio
async def test_approval_gate_fires_before_interview_gate():
    """When BOTH gates would fire, approval gate raises first (cheaper to
    check, no DB count query needed). Pin order so future refactor cannot
    silently reorder and waste DB queries."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        min_interviews_before_offer=5,
        completed_interviews_count=0,
    )
    with pytest.raises(ManagerApprovalRequiredError):
        await svc.check_can_send(uuid.uuid4(), "co-1")


# ----------------------------------------------------------------------------
# P0.D1 - NoApproverConfiguredError + approver notification dispatch
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_can_send_raises_no_approver_when_table_empty():
    """Policy ON, draft has no approval_request_id, Approver table is empty
    -> NoApproverConfiguredError (NOT ManagerApprovalRequiredError).

    Pins P0.D1: until this gate, the ApproverSection in
    Configuracoes > Departamentos was a ghost setting. The recruiter could
    set manager_approval_for_offer=ON without ever configuring approvers,
    and OfferService would either let offers through or raise the wrong
    error class. We now distinguish: empty approvers table = admin must
    configure first; non-empty + missing approval_request_id = recruiter
    must request approval.
    """
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=0,
    )
    with pytest.raises(NoApproverConfiguredError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    # Message must point at the admin-facing path (Departamentos), not the
    # recruiter-facing one (Politicas de Recrutamento).
    msg = str(exc_info.value)
    assert "Departamentos" in msg
    assert "aprovador" in msg.lower()
    assert exc_info.value.reason == "no_approver_configured"


@pytest.mark.asyncio
async def test_check_can_send_raises_manager_approval_when_approvers_present():
    """Policy ON, no approval_request_id, BUT Approver table has rows.
    Original P0-2 ManagerApprovalRequiredError still fires - the gate
    is downstream of the approver-configured check."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=3,
    )
    with pytest.raises(ManagerApprovalRequiredError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    assert exc_info.value.reason == "manager_approval_required"


@pytest.mark.asyncio
async def test_check_can_send_notifies_approvers_when_gate_fires():
    """When ManagerApprovalRequiredError fires AND approvers are configured,
    the notification dispatch MUST be called exactly once with the
    proposal-derived context. The gate raise must still happen (caller
    still sees the structured error) - notification is a side effect.
    """
    svc, proposal = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=2,
    )
    proposal.candidate_name = "Maria Souza"
    proposal.job_title = "Engenheira de Software Senior"
    proposal.job_vacancy_id = uuid.uuid4()
    proposal.created_by = "recruiter-1"

    with pytest.raises(ManagerApprovalRequiredError):
        await svc.check_can_send(uuid.uuid4(), "co-1")

    svc._approval_notifier.notify_pending_approvers_for_offer.assert_awaited_once()
    kwargs = svc._approval_notifier.notify_pending_approvers_for_offer.await_args.kwargs
    assert kwargs["company_id"] == "co-1"
    assert kwargs["candidate_name"] == "Maria Souza"
    assert kwargs["job_title"] == "Engenheira de Software Senior"
    assert kwargs["requested_by_user_id"] == "recruiter-1"


@pytest.mark.asyncio
async def test_check_can_send_does_not_notify_when_no_approvers():
    """When NoApproverConfiguredError fires (empty table), the notification
    dispatch MUST NOT be called - there is nobody to notify and the helper
    would just no-op anyway. Pin this so a future refactor cannot
    accidentally spam non-existent approvers."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=0,
    )
    with pytest.raises(NoApproverConfiguredError):
        await svc.check_can_send(uuid.uuid4(), "co-1")
    svc._approval_notifier.notify_pending_approvers_for_offer.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_can_send_swallows_notification_dispatch_error():
    """Notification dispatch failures are fail-open: a transient DB error
    in the notifier path must NOT mask the structured ManagerApprovalRequiredError
    the caller depends on. The gate's job is to BLOCK; the notification is
    best-effort enrichment.
    """
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=1,
    )
    async def _boom(**_kw):
        raise RuntimeError("simulated notification DB outage")
    svc._approval_notifier.notify_pending_approvers_for_offer = _boom
    with pytest.raises(ManagerApprovalRequiredError):
        await svc.check_can_send(uuid.uuid4(), "co-1")


@pytest.mark.asyncio
async def test_mark_sent_blocks_with_no_approver_when_table_empty():
    """Defense-in-depth: if a caller skips check_can_send, mark_sent also
    distinguishes NoApproverConfiguredError from ManagerApprovalRequiredError.
    Pin that the empty-approvers branch fires even when reached via the
    state-transition path."""
    svc, proposal = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=0,
    )
    with pytest.raises(NoApproverConfiguredError):
        await svc.mark_sent(
            offer_id=uuid.uuid4(),
            company_id="co-1",
            user_id="u-1",
            send_mode="auto",
            email_log_id=None,
        )
    assert proposal.status == "draft"


@pytest.mark.asyncio
async def test_has_active_approvers_fails_closed_on_repo_error():
    """Repository outage MUST make ``_has_active_approvers`` return False
    (fail-closed). The compliance trade-off documented in the helper docstring:
    blocking a legitimate offer is preferable to letting one out without
    approver signature."""
    svc, _ = _make_service_with(approvers_configured=1)
    async def _boom(*_a, **_kw):
        raise RuntimeError("simulated approver repo outage")
    svc._approver_repo.list_for_company = _boom
    result = await svc._has_active_approvers("co-1")
    assert result is False


@pytest.mark.asyncio
async def test_no_approver_configured_caught_by_parent_class():
    """LLM tool catches ``OfferPolicyGateError`` to discriminate via
    ``.reason``. Pin that the new subclass participates in the family."""
    svc, _ = _make_service_with(
        approval_required=True,
        proposal_approval_request_id=None,
        approvers_configured=0,
    )
    with pytest.raises(OfferPolicyGateError) as exc_info:
        await svc.check_can_send(uuid.uuid4(), "co-1")
    assert exc_info.value.reason == "no_approver_configured"

# ----------------------------------------------------------------------------
# KEY PATH REGRESSION SENSOR — pin que pipeline_rules e nao screening_rules
# (fix 2026-05-24: _requires_manager_approval lia de pipeline_rules)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_approval_reads_from_pipeline_rules_not_screening_rules():
    """Regression pin (2026-05-24): _requires_manager_approval MUST read from
    pipeline_rules.manager_approval_for_offer, NOT screening_rules.

    This test verifies the exact key path by constructing a policy where:
    - pipeline_rules.manager_approval_for_offer = True  (correct location)
    - screening_rules.manager_approval_for_offer = False (old wrong location)

    If the service reads from the wrong dict (screening_rules), the gate does
    NOT fire and the assertion fails — detecting the regression immediately.
    """
    import uuid as _uuid
    import app.domains.offer.services.offer_service as _mod

    svc, _ = _make_service_with(
        approval_required=True,   # placed in pipeline_rules by the fixture
        proposal_approval_request_id=None,
        approvers_configured=1,
    )
    # Sabotage screening_rules so that if the service reads from it, it sees
    # False (no approval required) and the gate would silently pass — the
    # pytest.raises block would then fail, catching the regression.
    policy_mock = _mod.HiringPolicyRepository.return_value.get_by_company.return_value
    policy_mock.screening_rules = {"manager_approval_for_offer": False}
    # pipeline_rules.manager_approval_for_offer remains True (set by fixture)

    with pytest.raises(ManagerApprovalRequiredError):
        await svc.check_can_send(_uuid.uuid4(), "co-1")

