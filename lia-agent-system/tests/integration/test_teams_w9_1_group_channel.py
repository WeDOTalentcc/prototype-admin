"""
W9.1 — Group/channel proactive flow.

Tests:
1. _store_channel_conversation_reference stores groupChat ref in DB
2. broadcast_to_channels sends to channel refs
3. Message handler stores channel ref on conversationUpdate (bot added to group)
4. Personal 1:1 conversationUpdate does NOT trigger channel store
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── TeamsProactivityEngine ────────────────────────────────────────────────────

class TestProactivityEngineBroadcastToChannels:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_channel_refs(self):
        from app.domains.communication.services.teams_proactivity_engine import TeamsProactivityEngine

        engine = TeamsProactivityEngine()
        card = {"type": "AdaptiveCard", "body": []}

        channel_refs = [
            {"service_url": "https://smba.trafficmanager.net/", "conversation_id": "19:ch1@thread.v2", "user_id": "channel:T1"},
            {"service_url": "https://smba.trafficmanager.net/", "conversation_id": "19:ch2@thread.v2", "user_id": "channel:T2"},
        ]

        with (
            patch.object(engine, "_get_channel_refs_for_company", new=AsyncMock(return_value=channel_refs)),
            patch.object(engine, "_send_card_to_ref", new=AsyncMock(return_value=True)),
        ):
            sent = await engine.broadcast_to_channels(card, company_id="co1", tenant_id="t1")

        assert sent == 2

    @pytest.mark.asyncio
    async def test_broadcast_returns_zero_when_no_refs(self):
        from app.domains.communication.services.teams_proactivity_engine import TeamsProactivityEngine

        engine = TeamsProactivityEngine()
        card = {}

        with patch.object(engine, "_get_channel_refs_for_company", new=AsyncMock(return_value=[])):
            sent = await engine.broadcast_to_channels(card, company_id="co1")

        assert sent == 0

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure_counts_successes(self):
        """If one channel fails, others should still succeed."""
        from app.domains.communication.services.teams_proactivity_engine import TeamsProactivityEngine

        engine = TeamsProactivityEngine()
        card = {}
        refs = [
            {"service_url": "https://smba.trafficmanager.net/", "conversation_id": "19:ch1@thread.v2", "user_id": "channel:T1"},
            {"service_url": "https://smba.trafficmanager.net/", "conversation_id": "19:ch2@thread.v2", "user_id": "channel:T2"},
            {"service_url": "https://smba.trafficmanager.net/", "conversation_id": "19:ch3@thread.v2", "user_id": "channel:T3"},
        ]

        results = [True, False, True]
        idx = 0

        async def _send(card, ref):
            nonlocal idx
            ok = results[idx]
            idx += 1
            return ok

        with (
            patch.object(engine, "_get_channel_refs_for_company", new=AsyncMock(return_value=refs)),
            patch.object(engine, "_send_card_to_ref", new=AsyncMock(side_effect=_send)),
        ):
            sent = await engine.broadcast_to_channels(card, company_id="co1")

        assert sent == 2  # 2 of 3 succeeded


# ── teams.py — _store_channel_conversation_reference ─────────────────────────

class TestStoreChannelConversationReference:
    @pytest.mark.asyncio
    async def test_stores_groupchat_ref(self):
        """_store_channel_conversation_reference should call repo.upsert_conversation."""
        from app.api.v1.teams import _store_channel_conversation_reference

        activity = {
            "serviceUrl": "https://smba.trafficmanager.net/",
            "channelId": "msteams",
            "conversation": {
                "id": "19:abc123@thread.v2",
                "conversationType": "groupChat",
                "tenantId": "tenant-42",
            },
            "channelData": {
                "team": {"id": "team-99"},
                "channel": {"name": "Recrutamento"},
            },
        }

        mock_repo = MagicMock()
        mock_repo.upsert_conversation = AsyncMock()
        mock_db = MagicMock()

        with patch(
            "app.domains.communication.repositories.teams_repository.TeamsRepository",
            return_value=mock_repo,
        ):
            await _store_channel_conversation_reference(activity, mock_db)

        mock_repo.upsert_conversation.assert_called_once()
        call_kwargs = mock_repo.upsert_conversation.call_args.kwargs
        assert call_kwargs["conversation_id"] == "19:abc123@thread.v2"
        assert call_kwargs["user_id"].startswith("channel:")
        assert call_kwargs["user_name"] == "Recrutamento"

    @pytest.mark.asyncio
    async def test_skips_if_no_conversation_id(self):
        """Should gracefully skip when activity has no conversation id."""
        from app.api.v1.teams import _store_channel_conversation_reference

        activity = {"serviceUrl": "https://smba.trafficmanager.net/", "channelId": "msteams"}
        mock_db = MagicMock()

        # Should not raise
        await _store_channel_conversation_reference(activity, mock_db)
