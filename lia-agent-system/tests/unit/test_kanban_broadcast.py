"""
Tests for Kanban real-time broadcast (GAP-09-001).

Validates:
1. publish_candidate_stage_change publishes to correct Redis channel
2. Channel naming is company-scoped (multi-tenancy)
3. Fail-open on Redis error
4. Event payload structure
"""
import json
import time
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.api.v1.kanban_broadcast import (
    publish_candidate_stage_change,
    _channel_for_company,
    CHANNEL_PREFIX,
)


class TestChannelNaming:
    def test_channel_includes_company_id(self):
        assert _channel_for_company("company-123") == f"{CHANNEL_PREFIX}:company-123"

    def test_different_companies_different_channels(self):
        ch1 = _channel_for_company("company-A")
        ch2 = _channel_for_company("company-B")
        assert ch1 != ch2

    def test_channel_prefix(self):
        assert CHANNEL_PREFIX == "kanban:broadcast"


class TestPublish:
    @pytest.mark.asyncio
    async def test_publishes_to_correct_channel(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            result = await publish_candidate_stage_change(
                company_id="comp-1",
                candidate_id="cand-1",
                candidate_name="Ana Silva",
                vacancy_id="vac-1",
                from_stage="screening",
                to_stage="interview_hr",
                sub_status="scheduled",
                moved_by_user_id="user-1",
            )

        assert result is True
        mock_redis.publish.assert_called_once()
        channel_arg = mock_redis.publish.call_args[0][0]
        assert channel_arg == "kanban:broadcast:comp-1"

    @pytest.mark.asyncio
    async def test_payload_structure(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            await publish_candidate_stage_change(
                company_id="comp-2",
                candidate_id="cand-2",
                candidate_name="Bruno Costa",
                vacancy_id="vac-2",
                from_stage="sourcing",
                to_stage="screening",
            )

        payload_json = mock_redis.publish.call_args[0][1]
        payload = json.loads(payload_json)

        assert payload["type"] == "candidate_stage_changed"
        assert payload["candidate_id"] == "cand-2"
        assert payload["candidate_name"] == "Bruno Costa"
        assert payload["vacancy_id"] == "vac-2"
        assert payload["from_stage"] == "sourcing"
        assert payload["to_stage"] == "screening"
        assert "ts" in payload
        assert isinstance(payload["ts"], float)

    @pytest.mark.asyncio
    async def test_fail_open_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            result = await publish_candidate_stage_change(
                company_id="comp-3",
                candidate_id="cand-3",
                candidate_name="Carlos",
                vacancy_id="vac-3",
                from_stage="screening",
                to_stage="hired",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_fail_open_on_get_redis_error(self):
        with patch("app.core.redis_client.get_redis", side_effect=Exception("No Redis")):
            result = await publish_candidate_stage_change(
                company_id="comp-4",
                candidate_id="cand-4",
                candidate_name="Diana",
                vacancy_id="vac-4",
                from_stage="sourcing",
                to_stage="screening",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_empty_sub_status_defaults(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            await publish_candidate_stage_change(
                company_id="comp-5",
                candidate_id="cand-5",
                candidate_name="Eva",
                vacancy_id="vac-5",
                from_stage="screening",
                to_stage="interview_hr",
            )

        payload = json.loads(mock_redis.publish.call_args[0][1])
        assert payload["sub_status"] == ""
        assert payload["moved_by"] == ""
