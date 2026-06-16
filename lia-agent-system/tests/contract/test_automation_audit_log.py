"""
Z.3 — Contract test: automation execute paths emit canonical audit_logs.

LGPD Art. 9 + EU AI Act Art. 13 require an audit trail for every automated
decision. AutomationService.trigger_automation and .test_automation must call
audit_service.log_decision for each executed/skipped/errored/simulated run,
with PII redacted from reasoning/metadata.

Pinned 2026-05-26 (Z.3 audit wire).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domains.automation.services.automation_service import (
    AutomationService,
    _mask_trigger_data_for_audit,
)


# ---------------------------------------------------------------------------
# Unit tests — _mask_trigger_data_for_audit (PII redaction helper)
# ---------------------------------------------------------------------------


def test_mask_trigger_data_redacts_explicit_pii_keys():
    """candidate_email / candidate_phone / candidate_name → ***REDACTED***."""
    raw = {
        "candidate_id": "uuid-1",  # not PII (UUID per LGPD Art. 5 V)
        "candidate_email": "joao@example.com",
        "candidate_phone": "+5511999999999",
        "candidate_name": "João Silva",
        "vacancy_id": "uuid-2",
        "stage": "screening",
    }
    masked = _mask_trigger_data_for_audit(raw)

    assert masked["candidate_email"] == "***REDACTED***"
    assert masked["candidate_phone"] == "***REDACTED***"
    assert masked["candidate_name"] == "***REDACTED***"
    # Non-PII fields preserved
    assert masked["candidate_id"] == "uuid-1"
    assert masked["vacancy_id"] == "uuid-2"
    assert masked["stage"] == "screening"


def test_mask_trigger_data_masks_freeform_pii_in_strings():
    """Free-form string fields run through mask_pii (catches inline emails/phones)."""
    raw = {
        "custom_message": "Contate o candidato em maria@empresa.com.br",
    }
    masked = _mask_trigger_data_for_audit(raw)
    assert "maria@empresa.com.br" not in masked["custom_message"]
    assert "***EMAIL***" in masked["custom_message"]


def test_mask_trigger_data_handles_none_and_empty():
    assert _mask_trigger_data_for_audit(None) == {}
    assert _mask_trigger_data_for_audit({}) == {}


def test_mask_trigger_data_preserves_numeric_and_bool():
    raw = {"score": 0.87, "approved": True, "retries": 3, "none_val": None}
    masked = _mask_trigger_data_for_audit(raw)
    assert masked["score"] == 0.87
    assert masked["approved"] is True
    assert masked["retries"] == 3
    assert masked["none_val"] is None


# ---------------------------------------------------------------------------
# Contract tests — trigger_automation wires audit_service.log_decision
# ---------------------------------------------------------------------------


@pytest.fixture
def svc():
    return AutomationService()


@pytest.fixture
def fake_automation():
    a = MagicMock()
    a.id = uuid4()
    a.name = "Test automation"
    a.action_type = "send_email"
    a.action_config = {}
    a.conditions = [{"field": "stage", "op": "eq", "value": "screening"}]
    a.is_active = True
    a.last_executed_at = None
    a.execution_count = 0
    return a


@pytest.mark.asyncio
async def test_trigger_automation_logs_audit_on_success(svc, fake_automation):
    """Successful execution emits decision='success', decision_type='automation_executed'."""
    fake_db = AsyncMock()
    company_id = str(uuid4())

    with patch(
        "app.domains.automation.services.automation_service.CommunicationAutomationRepository"
    ) as repo_cls, patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit, patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=True)
    ), patch.object(
        svc, "evaluate_conditions", AsyncMock(return_value=True)
    ), patch.object(
        svc, "execute_action", AsyncMock(return_value={"status": "sent"})
    ), patch.object(
        svc, "_log_execution", AsyncMock()
    ):
        repo_cls.return_value.list_active_for_trigger = AsyncMock(
            return_value=[fake_automation]
        )
        mock_audit.log_decision = AsyncMock()

        await svc.trigger_automation(
            trigger_type="candidate_stage_changed",
            trigger_data={
                "candidate_id": "cid-1",
                "candidate_email": "leak@example.com",
                "vacancy_id": "vid-1",
            },
            company_id=company_id,
            db=fake_db,
        )

        assert mock_audit.log_decision.await_count == 1
        kwargs = mock_audit.log_decision.await_args.kwargs
        assert kwargs["company_id"] == company_id
        assert kwargs["agent_name"] == "automation_engine"
        assert kwargs["decision_type"] == "automation_executed"
        assert kwargs["decision"] == "success"
        assert kwargs["candidate_id"] == "cid-1"
        assert kwargs["job_vacancy_id"] == "vid-1"

        # PII never leaks into reasoning
        reasoning_blob = " ".join(kwargs["reasoning"])
        assert "leak@example.com" not in reasoning_blob
        assert "***REDACTED***" in reasoning_blob or "***EMAIL***" in reasoning_blob


@pytest.mark.asyncio
async def test_trigger_automation_logs_audit_on_cooldown_skip(svc, fake_automation):
    fake_db = AsyncMock()
    with patch(
        "app.domains.automation.services.automation_service.CommunicationAutomationRepository"
    ) as repo_cls, patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit, patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=False)
    ):
        repo_cls.return_value.list_active_for_trigger = AsyncMock(
            return_value=[fake_automation]
        )
        mock_audit.log_decision = AsyncMock()

        await svc.trigger_automation(
            trigger_type="candidate_stage_changed",
            trigger_data={"candidate_id": "cid-1"},
            company_id=str(uuid4()),
            db=fake_db,
        )

        assert mock_audit.log_decision.await_count == 1
        kwargs = mock_audit.log_decision.await_args.kwargs
        assert kwargs["decision_type"] == "automation_skipped"
        assert kwargs["decision"] == "skipped"
        assert any("cooldown_active" in r for r in kwargs["reasoning"])


@pytest.mark.asyncio
async def test_trigger_automation_logs_audit_on_conditions_skip(svc, fake_automation):
    fake_db = AsyncMock()
    with patch(
        "app.domains.automation.services.automation_service.CommunicationAutomationRepository"
    ) as repo_cls, patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit, patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=True)
    ), patch.object(
        svc, "evaluate_conditions", AsyncMock(return_value=False)
    ):
        repo_cls.return_value.list_active_for_trigger = AsyncMock(
            return_value=[fake_automation]
        )
        mock_audit.log_decision = AsyncMock()

        await svc.trigger_automation(
            trigger_type="candidate_stage_changed",
            trigger_data={"candidate_id": "cid-1"},
            company_id=str(uuid4()),
            db=fake_db,
        )

        assert mock_audit.log_decision.await_count == 1
        kwargs = mock_audit.log_decision.await_args.kwargs
        assert kwargs["decision_type"] == "automation_skipped"
        assert any("conditions_not_met" in r for r in kwargs["reasoning"])


@pytest.mark.asyncio
async def test_trigger_automation_logs_audit_on_error_with_review_flag(
    svc, fake_automation
):
    """Errored execution → decision_type='automation_failed', human_review_required=True."""
    fake_db = AsyncMock()
    with patch(
        "app.domains.automation.services.automation_service.CommunicationAutomationRepository"
    ) as repo_cls, patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit, patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=True)
    ), patch.object(
        svc, "evaluate_conditions", AsyncMock(return_value=True)
    ), patch.object(
        svc,
        "execute_action",
        AsyncMock(side_effect=RuntimeError("downstream failure: bob@example.com")),
    ), patch.object(
        svc, "_log_execution", AsyncMock()
    ):
        repo_cls.return_value.list_active_for_trigger = AsyncMock(
            return_value=[fake_automation]
        )
        mock_audit.log_decision = AsyncMock()

        await svc.trigger_automation(
            trigger_type="candidate_stage_changed",
            trigger_data={"candidate_id": "cid-1"},
            company_id=str(uuid4()),
            db=fake_db,
        )

        assert mock_audit.log_decision.await_count == 1
        kwargs = mock_audit.log_decision.await_args.kwargs
        assert kwargs["decision_type"] == "automation_failed"
        assert kwargs["decision"] == "error"
        assert kwargs["human_review_required"] is True
        # PII in exception text must be masked
        reasoning_blob = " ".join(kwargs["reasoning"])
        assert "bob@example.com" not in reasoning_blob


@pytest.mark.asyncio
async def test_test_automation_logs_audit_for_dry_run(svc, fake_automation):
    """Dry-run also emits canonical audit row (decision_type='automation_simulated')."""
    fake_db = AsyncMock()
    with patch.object(
        svc, "get_automation", AsyncMock(return_value=fake_automation)
    ), patch.object(
        svc, "evaluate_conditions", AsyncMock(return_value=True)
    ), patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=True)
    ), patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit:
        mock_audit.log_decision = AsyncMock()

        result = await svc.test_automation(
            automation_id=str(fake_automation.id),
            company_id=str(uuid4()),
            test_data={
                "candidate_id": "tc-1",
                "candidate_email": "leak@example.com",
                "vacancy_id": "tv-1",
            },
            db=fake_db,
        )

        assert result["success"] is True
        assert mock_audit.log_decision.await_count == 1
        kwargs = mock_audit.log_decision.await_args.kwargs
        assert kwargs["decision_type"] == "automation_simulated"
        assert kwargs["decision"] in ("would_execute", "would_skip")
        # PII in test_data must not leak
        reasoning_blob = " ".join(kwargs["reasoning"])
        assert "leak@example.com" not in reasoning_blob


@pytest.mark.asyncio
async def test_audit_failure_does_not_break_automation_flow(svc, fake_automation):
    """audit_service.log_decision raising must NOT break the user flow."""
    fake_db = AsyncMock()
    with patch(
        "app.domains.automation.services.automation_service.CommunicationAutomationRepository"
    ) as repo_cls, patch(
        "app.domains.automation.services.automation_service._audit_service"
    ) as mock_audit, patch.object(
        svc, "_check_cooldown", AsyncMock(return_value=True)
    ), patch.object(
        svc, "evaluate_conditions", AsyncMock(return_value=True)
    ), patch.object(
        svc, "execute_action", AsyncMock(return_value={"status": "sent"})
    ), patch.object(
        svc, "_log_execution", AsyncMock()
    ):
        repo_cls.return_value.list_active_for_trigger = AsyncMock(
            return_value=[fake_automation]
        )
        mock_audit.log_decision = AsyncMock(side_effect=Exception("audit DB down"))

        # Must not raise — audit failure is logged but swallowed.
        result = await svc.trigger_automation(
            trigger_type="candidate_stage_changed",
            trigger_data={"candidate_id": "cid-1"},
            company_id=str(uuid4()),
            db=fake_db,
        )
        assert result["automations_executed"] == 1
