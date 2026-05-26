"""Agent J — emit canonical event candidate_screened.

Test: voice_screening_orchestrator.finalize_screening (line ~2120) emite
PlatformEvent canonical event_type="candidate_screened" via publish_platform_event
apos session.status="completed" + persist + audit.
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_finalize_screening_emits_candidate_screened():
    """finalize_screening emite candidate_screened canonical apos scoring."""
    from app.domains.voice.services import voice_screening_orchestrator as mod

    company_id = "11111111-1111-1111-1111-111111111111"
    candidate_id = "cand-42"
    session_id = "sess-99"

    session = SimpleNamespace(
        session_id=session_id,
        company_id=company_id,
        candidate_id=candidate_id,
        job_title="QA Engineer",
        status="active",
        started_at=datetime.utcnow(),
        ended_at=None,
        wsi_result=None,
        error=None,
        transcript_segments=[{"text": "ok", "speaker": "candidate"}],
        consent_given=True,
        call_sid=None,
    )

    orchestrator = mod.voice_screening_orchestrator

    fake_db = MagicMock()
    fake_db.commit = AsyncMock()

    wsi_result = {"overall_evaluation": {"overall_score": 87}}
    fake_analyze = AsyncMock(return_value=wsi_result)

    with patch.object(orchestrator, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orchestrator, "persist_session_state", new=AsyncMock()), \
         patch.object(orchestrator, "_store_session", new=AsyncMock()), \
         patch.object(orchestrator, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch.object(orchestrator, "_record_voice_billing", new=AsyncMock()), \
         patch.object(mod, "_WSIVoiceOrchestrator", new=None), \
         patch.object(mod, "_analyze_voice_screening", new=fake_analyze), \
         patch.object(mod, "publish_platform_event", new=AsyncMock(return_value=True)) as mock_emit:
        await orchestrator.finalize_screening(session_id, db=fake_db)

    mock_emit.assert_awaited()
    found = [
        c for c in mock_emit.await_args_list
        if c.args and getattr(c.args[0], "event_type", "") == "candidate_screened"
    ]
    assert len(found) == 1, f"esperava 1 emit candidate_screened, achei {len(found)}"
    event = found[0].args[0]
    assert event.company_id == company_id
    assert event.payload["candidate_id"] == candidate_id
    assert "score" in event.payload
    assert "completed_at" in event.payload
