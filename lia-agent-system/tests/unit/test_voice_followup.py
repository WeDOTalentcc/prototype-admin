"""
Voz #1 — auto follow-up via a NON-voice channel for the fields the voice call
did not collect.

After ``DataCollectionVoicePlugin.on_session_finalized`` persists the valid
voice answers, it fires a best-effort follow-up (reusing the canonical
``DataRequestService.send_notification``) for the fields still missing
(``needs_followup`` ∪ ``portal_fallback_fields``).

Tested:
- follow-up fires once with NON-voice channels for needs_followup fields;
- portal_fallback fields also trigger follow-up;
- everything collected → NO follow-up;
- consent DENIED → NO follow-up (followup_reason="consent_denied");
- send_notification raising → finalize still returns, followup_error recorded;
- channel resolution from DataRequestConfig booleans (voice never present).

SSH note: heavy deps are mocked / not imported at module top. The plugin's
follow-up imports DataRequestService LAZILY inside the helper, so we patch that
module path. No real DB / orchestrator is loaded.
"""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@dataclass
class _FakeSession:
    session_id: str = "sess-fu"
    candidate_id: str = "cand-1"
    company_id: str = "co-1"
    job_id: str | None = None
    job_title: str = "Coleta de dados"
    metadata: dict | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def _make_plugin(data_request_id="dr-1", require_consent=False):
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    return DataCollectionVoicePlugin(
        fields=[],
        data_request_id=data_request_id,
        require_verbal_consent=require_consent,
    )


def _patch_service(config=None, send_side_effect=None):
    """Patch the lazily-imported DataRequestService.

    Returns (ctx, service_instance). ``config`` controls the booleans returned
    by get_or_create_config; ``send_side_effect`` lets a test make
    send_notification raise.
    """
    cfg = config or MagicMock(
        send_email_notification=True, send_whatsapp_notification=True
    )
    service = MagicMock()
    service.get_or_create_config = AsyncMock(return_value=cfg)
    if send_side_effect is not None:
        service.send_notification = AsyncMock(side_effect=send_side_effect)
    else:
        service.send_notification = AsyncMock(return_value={"email": {"success": True}})
    service_cls = MagicMock(return_value=service)
    ctx = patch(
        "app.domains.communication.services.data_request_service.DataRequestService",
        service_cls,
    )
    return ctx, service


# ── TEST 1 — needs_followup + consent granted → follow-up fired once ────────
@pytest.mark.asyncio
async def test_followup_fires_for_needs_followup_non_voice_channels():
    plugin = _make_plugin()
    ctx, service = _patch_service()
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["phone"],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    service.send_notification.assert_awaited_once()
    args = service.send_notification.await_args
    channels = args.args[2] if len(args.args) > 2 else args.kwargs["channels"]
    assert "voice" not in channels
    assert channels == ["email", "whatsapp"]
    assert result["followup_triggered"] is True
    assert result["followup_fields"] == ["phone"]


# ── TEST 2 — portal_fallback fields also count ──────────────────────────────
@pytest.mark.asyncio
async def test_followup_fires_for_portal_fallback_fields():
    plugin = _make_plugin()
    ctx, service = _patch_service()
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=[],
            portal_fallback_fields=["doc_upload"],
            consent_granted=True,
        )

    service.send_notification.assert_awaited_once()
    assert result["followup_triggered"] is True
    assert "doc_upload" in result["followup_fields"]


# ── TEST 3 — everything collected → NO follow-up ────────────────────────────
@pytest.mark.asyncio
async def test_no_followup_when_all_collected():
    plugin = _make_plugin()
    ctx, service = _patch_service()
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=[],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    service.send_notification.assert_not_awaited()
    assert result["followup_triggered"] is False
    assert result["followup_reason"] == "all_collected"


# ── TEST 4 — consent DENIED → NO follow-up even if remaining exist ──────────
@pytest.mark.asyncio
async def test_no_followup_when_consent_denied():
    plugin = _make_plugin()
    ctx, service = _patch_service()
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["cpf"],
            portal_fallback_fields=["doc_upload"],
            consent_granted=False,
        )

    service.send_notification.assert_not_awaited()
    assert result["followup_triggered"] is False
    assert result["followup_reason"] == "consent_denied"


# ── TEST 5 — send_notification raises → finalize survives, error recorded ───
@pytest.mark.asyncio
async def test_followup_error_does_not_propagate():
    plugin = _make_plugin()
    ctx, service = _patch_service(send_side_effect=RuntimeError("smtp down"))
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["phone"],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    # No exception propagated; error surfaced explicitly (anti-silent-fallback).
    assert result["followup_triggered"] is False
    assert "smtp down" in result["followup_error"]


# ── TEST 6 — channel resolution from config booleans; voice never present ───
@pytest.mark.asyncio
async def test_channel_resolution_whatsapp_only():
    plugin = _make_plugin()
    cfg = MagicMock(send_email_notification=False, send_whatsapp_notification=True)
    ctx, service = _patch_service(config=cfg)
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["phone"],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    args = service.send_notification.await_args
    channels = args.args[2] if len(args.args) > 2 else args.kwargs["channels"]
    assert channels == ["whatsapp"]
    assert "voice" not in channels
    assert result["followup_channels"] == ["whatsapp"]


@pytest.mark.asyncio
async def test_channel_resolution_neither_defaults_email():
    plugin = _make_plugin()
    cfg = MagicMock(send_email_notification=False, send_whatsapp_notification=False)
    ctx, service = _patch_service(config=cfg)
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["phone"],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    args = service.send_notification.await_args
    channels = args.args[2] if len(args.args) > 2 else args.kwargs["channels"]
    assert channels == ["email"]  # always reach the candidate somehow
    assert "voice" not in channels


# ── TEST 8 — no data_request_id → no follow-up (nothing to point to) ────────
@pytest.mark.asyncio
async def test_no_followup_without_data_request_id():
    plugin = _make_plugin(data_request_id=None)
    ctx, service = _patch_service()
    with ctx:
        result = await plugin._trigger_followup_for_remaining(
            session=_FakeSession(),
            db=MagicMock(),
            needs_followup=["phone"],
            portal_fallback_fields=[],
            consent_granted=True,
        )

    service.send_notification.assert_not_awaited()
    assert result["followup_triggered"] is False
    assert result["followup_reason"] == "no_data_request"
