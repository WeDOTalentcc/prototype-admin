"""
B1 fix — unit tests: handlers_lifecycle uses get_mailgun_email_service,
not the deprecated get_email_service with incompatible signature.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal stubs so we can import the handlers without the full FastAPI app
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_mailgun_service():
    svc = MagicMock()
    svc.send_email = AsyncMock(return_value=MagicMock(success=True, message_id="test-123"))
    return svc


@pytest.fixture()
def hired_request():
    req = MagicMock()
    req.candidate_id = "cand-uuid-001"
    req.vacancy_id = "vac-uuid-001"
    req.company_id = "comp-uuid-001"
    req.candidate_email = "hired@example.com"
    req.candidate_name = "Test Candidate"
    req.job_title = "Engenheiro"
    req.hire_date = None
    req.department = None
    req.notes = None
    req.reviewer_id = None
    req.hiring_manager_email = None
    req.trigger_onboarding = False
    req.notify_team = False
    return req


@pytest.fixture()
def rejected_request():
    req = MagicMock()
    req.candidate_id = "cand-uuid-002"
    req.vacancy_id = "vac-uuid-001"
    req.company_id = "comp-uuid-001"
    req.candidate_email = "rejected@example.com"
    req.candidate_name = "Rejected Candidate"
    req.job_title = "Engenheiro"
    req.rejection_stage = "Triagem"
    req.rejection_reason = "Perfil não adequado"
    req.send_feedback = True
    req.add_to_talent_pool = False
    req.reviewer_id = "reviewer-uuid-001"  # required by human review gate
    return req


# ---------------------------------------------------------------------------
# Test 1 — handle_candidate_hired uses mailgun (correct signature)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_candidate_hired_calls_mailgun(mock_mailgun_service, hired_request):
    """
    B1: handle_candidate_hired must call get_mailgun_email_service(), not
    get_email_service(). The call to send_email must use to_email/subject/body
    kwargs (MailgunEmailService signature), NOT db/template_id/recipient_email
    (deprecated EmailService signature).
    """
    db = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=False)

    module_path = "app.api.v1.automation.event_handlers.handlers_lifecycle"

    with (
        patch(f"{module_path}.get_mailgun_email_service", return_value=mock_mailgun_service),
        patch(f"{module_path}.ensure_company_access", new_callable=AsyncMock),
        patch(f"{module_path}.log_automation_execution", new_callable=AsyncMock),
        patch(f"{module_path}.get_activity_service", return_value=AsyncMock()),
        patch(f"{module_path}.get_ats_sync_service", return_value=AsyncMock()),
        patch(f"{module_path}.get_pipeline_stage_service", return_value=AsyncMock()),
    ):
        from app.api.v1.automation.event_handlers.handlers_lifecycle import handle_candidate_hired
        try:
            await handle_candidate_hired(request=hired_request, db=db, company_id="comp-uuid-001")
        except Exception:
            pass  # we care only about the email call

    # Verify send_email was called with mailgun-compatible kwargs
    assert mock_mailgun_service.send_email.called, "send_email was never called — email not sent"
    call_kwargs = mock_mailgun_service.send_email.call_args

    # Must NOT contain deprecated EmailService positional args (db, template_id)
    all_kwargs = {**call_kwargs.kwargs}
    if call_kwargs.args:
        # Positional: first arg must be to_email string, not a db session
        first_arg = call_kwargs.args[0]
        assert isinstance(first_arg, str), (
            f"B1 FAIL: first positional arg to send_email is not a string (got {type(first_arg)}). "
            "This indicates EmailService (db, template_id, ...) signature is being used instead of "
            "MailgunEmailService (to_email, subject, body)."
        )
    else:
        assert "to_email" in all_kwargs, (
            f"B1 FAIL: send_email called without to_email kwarg. "
            f"Got kwargs: {list(all_kwargs.keys())}. "
            "Likely still using deprecated EmailService signature."
        )
        assert "subject" in all_kwargs, "send_email missing 'subject' kwarg"
        assert "body" in all_kwargs, "send_email missing 'body' kwarg"


# ---------------------------------------------------------------------------
# Test 2 — handle_candidate_rejected uses mailgun (correct signature)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_candidate_rejected_calls_mailgun(mock_mailgun_service, rejected_request):
    """
    B1: handle_candidate_rejected must call get_mailgun_email_service(), not
    get_email_service(). Same signature verification as test 1.
    """
    db = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=False)

    module_path = "app.api.v1.automation.event_handlers.handlers_lifecycle"

    with (
        patch(f"{module_path}.get_mailgun_email_service", return_value=mock_mailgun_service),
        patch(f"{module_path}.ensure_company_access", new_callable=AsyncMock),
        patch(f"{module_path}.log_automation_execution", new_callable=AsyncMock),
        patch(f"{module_path}.get_activity_service", return_value=AsyncMock()),
        patch(f"{module_path}.get_ats_sync_service", return_value=AsyncMock()),
        patch(f"{module_path}.get_pipeline_stage_service", return_value=AsyncMock()),
    ):
        from app.api.v1.automation.event_handlers.handlers_lifecycle import handle_candidate_rejected
        try:
            await handle_candidate_rejected(request=rejected_request, db=db, company_id="comp-uuid-001")
        except Exception:
            pass  # we care only about the email call

    assert mock_mailgun_service.send_email.called, "send_email was never called — rejection email not sent"
    call_kwargs = mock_mailgun_service.send_email.call_args

    all_kwargs = {**call_kwargs.kwargs}
    if call_kwargs.args:
        first_arg = call_kwargs.args[0]
        assert isinstance(first_arg, str), (
            f"B1 FAIL: first positional arg to send_email is not a string (got {type(first_arg)}). "
            "Using deprecated EmailService signature."
        )
    else:
        assert "to_email" in all_kwargs, (
            f"B1 FAIL: send_email called without to_email kwarg. "
            f"Got kwargs: {list(all_kwargs.keys())}."
        )
        assert "subject" in all_kwargs, "send_email missing 'subject' kwarg"
        assert "body" in all_kwargs, "send_email missing 'body' kwarg"


# ---------------------------------------------------------------------------
# Test 3 (regression guard) — get_email_service import is GONE from the module
# ---------------------------------------------------------------------------

def test_get_email_service_not_imported_in_handlers_lifecycle():
    """
    B1 regression guard: handlers_lifecycle must NOT import get_email_service.
    If get_email_service reappears, this test fails immediately.
    """
    import importlib
    import sys

    # Reload to get fresh module state
    mod_name = "app.api.v1.automation.event_handlers.handlers_lifecycle"
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    # We don't actually import (too many deps), just inspect the source
    import inspect, pathlib
    src_path = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/"
        "app/api/v1/automation/event_handlers/handlers_lifecycle.py"
    )
    source = src_path.read_text()
    assert "get_email_service" not in source, (
        "B1 REGRESSION: get_email_service found in handlers_lifecycle.py — "
        "must be replaced with get_mailgun_email_service everywhere."
    )
    assert "get_mailgun_email_service" in source, (
        "B1: get_mailgun_email_service not found in handlers_lifecycle.py"
    )
