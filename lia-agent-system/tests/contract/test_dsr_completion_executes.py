"""
WT-2022 P2.1 regression sensor (audit 2026-05-21): the DSR completion path
MUST invoke `_execute_dsr_side_effect` BEFORE flipping status to "completed".

Compliance-theater context: prior to the P2.1 fix in
`app/domains/data_subject/repositories/data_subject_repository.py`,
`complete_request` simply set `status="completed"` without executing any
real side-effect (deletion / portability / correction).  An ANPD audit
would see a completed deletion request while PII remained live — a clear
LGPD Art. 18 violation.

This module pins that contract.  Any refactor that drops the
`_execute_dsr_side_effect` call from `complete_request`, removes the
fail-loud raise for missing-candidate deletions, or stops recording the
side-effect dict in `audit_trail`, fails CI.

Strategy: pure-unit test with mocked AsyncSession + patched downstream
executors (`schedule_deletion_for_candidate`, `DsrExportService`).  We do
NOT spin up a real DB session — that would belong to
`tests/integration/`.  This file lives in `tests/contract/` because the
contract under test is: "if `complete_request` runs, the real executor
MUST have been called AND the result recorded in `audit_trail`."
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.data_subject_repository import (
    DataSubjectRepository,
    DsrExecutorFailedError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(*, request_type: str, subject_email: str = "x@y.com"):
    """Build a MagicMock that quacks like a DataSubjectRequest row."""
    req = MagicMock()
    req.id = uuid.uuid4()
    req.company_id = uuid.uuid4()
    req.request_type = request_type
    req.subject_email = subject_email
    req.status = "processing"
    req.sla_deadline = datetime.utcnow() + timedelta(days=15)
    req.audit_trail = []
    return req


def _make_repo_with(*, candidate_found: bool):
    """Build a DataSubjectRepository whose db.execute returns either a
    Candidate-like mock or None depending on `candidate_found`.

    Also stubs out `commit`/`refresh` so the repo's mutation path runs
    without a real session.
    """
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # The repo does `db.execute(select(Candidate)...)`.  The chain is
    # `result = await db.execute(stmt); candidate = result.scalar_one_or_none()`.
    result_mock = MagicMock()
    if candidate_found:
        candidate = MagicMock()
        candidate.id = uuid.uuid4()
        result_mock.scalar_one_or_none = MagicMock(return_value=candidate)
    else:
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result_mock)

    return DataSubjectRepository(db), db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_complete_deletion_calls_schedule_deletion_for_candidate():
    """LGPD Art. 18 VI: deletion side-effect must invoke the real deletion
    scheduler before the request is marked completed.
    """
    repo, _db = _make_repo_with(candidate_found=True)
    req = _make_request(request_type="deletion")
    deletion_at = datetime.utcnow() + timedelta(days=1)

    with patch(
        "app.domains.lgpd.services.lgpd_cleanup_service.schedule_deletion_for_candidate",
        new=AsyncMock(return_value=deletion_at),
    ) as sched_mock:
        result = await repo.complete_request(
            req,
            response="ok",
            evidence_files=[],
            audit_entry={"actor": "admin"},
        )

    assert sched_mock.called, (
        "_execute_dsr_side_effect MUST invoke schedule_deletion_for_candidate "
        "for deletion requests — otherwise we ship compliance theater."
    )
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_complete_deletion_raises_when_no_candidate_found():
    """Fail-loud guard: if a deletion request matches no candidate row, the
    repo MUST raise DsrExecutorFailedError instead of silently marking the
    request as completed.  Without this guard, the ANPD audit log would
    claim deletion when in fact nothing was deleted.
    """
    repo, _db = _make_repo_with(candidate_found=False)
    req = _make_request(request_type="deletion")

    with pytest.raises(DsrExecutorFailedError) as exc_info:
        await repo.complete_request(
            req,
            response="ok",
            evidence_files=[],
            audit_entry={"actor": "admin"},
        )

    # Sanity check: message references the contract being protected.
    assert "deletion" in str(exc_info.value).lower()
    # And the request was NOT marked completed.
    assert req.status != "completed"


@pytest.mark.asyncio
async def test_complete_portability_calls_dsr_export_service():
    """LGPD Art. 18 V (portability) and Art. 18 II (access): both must
    actually invoke DsrExportService.export_candidate_data to materialise
    the candidate payload.
    """
    repo, _db = _make_repo_with(candidate_found=True)
    req = _make_request(request_type="portability")

    fake_export = AsyncMock(return_value={"candidate": {"id": "x"}})
    fake_svc = MagicMock()
    fake_svc.export_candidate_data = fake_export

    with patch(
        "app.domains.lgpd.services.dsr_export_service.DsrExportService",
        return_value=fake_svc,
    ):
        result = await repo.complete_request(
            req,
            response="ok",
            evidence_files=[],
            audit_entry={"actor": "admin"},
        )

    assert fake_export.called, (
        "_execute_dsr_side_effect MUST invoke DsrExportService.export_candidate_data "
        "for portability/access requests — otherwise the subject receives no payload."
    )
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_complete_correction_records_requires_admin_followup():
    """`correction` / `restriction` / `objection` / `explanation` have no
    automated executor.  The contract is: the side-effect dict MUST set
    `requires_admin_followup=True` AND include a `warning` string so the
    ANPD audit trail is honest about the compliance gap.
    """
    repo, _db = _make_repo_with(candidate_found=True)
    req = _make_request(request_type="correction")
    audit_entry = {"actor": "admin"}

    await repo.complete_request(
        req,
        response="ok",
        evidence_files=[],
        audit_entry=audit_entry,
    )

    # The mutated audit_entry carries the side_effect under the agreed key.
    side_effect = audit_entry.get("side_effect")
    assert side_effect is not None, "side_effect MUST be recorded in audit_entry"
    assert side_effect.get("requires_admin_followup") is True, (
        "correction requests MUST flag requires_admin_followup=True so the "
        "audit trail signals the human follow-up needed for LGPD Art. 18 IV."
    )
    assert isinstance(side_effect.get("warning"), str) and side_effect["warning"], (
        "correction requests MUST include a non-empty warning string "
        "explaining that the executor is admin-driven."
    )


@pytest.mark.asyncio
async def test_complete_records_side_effect_in_audit_trail():
    """Universal invariant: regardless of request_type, after
    `complete_request` returns, the audit_entry passed in MUST contain a
    non-empty `side_effect` dict that includes at minimum
    `executor_run_at` and `request_type`.
    """
    repo, _db = _make_repo_with(candidate_found=True)
    req = _make_request(request_type="portability")
    audit_entry = {"actor": "admin"}

    fake_svc = MagicMock()
    fake_svc.export_candidate_data = AsyncMock(return_value={"ok": True})
    with patch(
        "app.domains.lgpd.services.dsr_export_service.DsrExportService",
        return_value=fake_svc,
    ):
        await repo.complete_request(
            req,
            response="ok",
            evidence_files=[],
            audit_entry=audit_entry,
        )

    side_effect = audit_entry.get("side_effect")
    assert isinstance(side_effect, dict) and side_effect, (
        "audit_entry['side_effect'] MUST be a non-empty dict — otherwise "
        "the ANPD trail loses the executor evidence."
    )
    assert "executor_run_at" in side_effect, (
        "side_effect MUST include executor_run_at timestamp."
    )
    assert side_effect.get("request_type") == "portability", (
        "side_effect MUST carry the request_type for cross-reference."
    )
