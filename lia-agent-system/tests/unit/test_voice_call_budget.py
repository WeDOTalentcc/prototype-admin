"""
TDD -- Gap A: Monthly voice-call budget guardrail.

Tests that DataRequestVoiceService.start_collection:
1. Proceeds (calls initiate_call) when budget is under limit.
2. Returns voice_collection_budget_exceeded and does NOT call initiate_call
   when budget is at/over limit.
3. After a successful call, _increment_voice_calls is called.
4. _check_voice_budget is fail-open: Redis unavailable -> (True, 0).
5. _voice_redis_key produces the expected monthly key format.

All service imports are done LAZILY (inside test functions) to avoid triggering
the heavy app.domains.__init__ chain during pytest collection. This mirrors
the pattern used by test_data_request_voice_channel.py.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# -- Helpers ------------------------------------------------------------------

class _FakeDataRequest:
    def __init__(self):
        self.id = uuid.uuid4()
        self.candidate_id = uuid.uuid4()
        self.company_id = uuid.UUID("00000000-0000-4000-a000-000000000042")
        self.fields_requested = [
            {"name": "cpf", "label": "CPF", "field_type": "cpf"},
        ]
        self.fields_completed = []
        self.collection_method = None


class _FakeCandidate:
    def __init__(self):
        self.name = "Test Candidate"


def _make_db(dr):
    """Fake async DB session returning dr then a candidate."""
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = MagicMock()
    db.get = AsyncMock(side_effect=[dr, cand])
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


def _consent_granted_patch():
    """Patch _classify_consent on the service instance to return 'granted'."""
    return patch(
        "app.domains.communication.services.data_request_voice_service"
        ".DataRequestVoiceService._classify_consent",
        AsyncMock(return_value="granted"),
    )


def _budget_allowed_patch(allowed=True, count=0):
    return patch(
        "app.domains.communication.services.data_request_voice_service._check_voice_budget",
        AsyncMock(return_value=(allowed, count)),
    )


def _increment_spy():
    return patch(
        "app.domains.communication.services.data_request_voice_service._increment_voice_calls",
        AsyncMock(return_value=1),
    )


def _fake_orchestrator(orch_status="initiated"):
    fake_session = SimpleNamespace(status=orch_status, session_id="sess-ok")
    mock_orch_instance = MagicMock()
    mock_orch_instance.initiate_call = AsyncMock(return_value=fake_session)
    mock_orch_class = MagicMock(return_value=mock_orch_instance)
    mock_plugin_class = MagicMock(return_value=MagicMock())
    return mock_orch_class, mock_plugin_class, mock_orch_instance


# -- Tests for budget helper functions (lazy-imported so module import runs) --

class TestVoiceRedisKey:
    def test_format_has_three_colon_parts(self):
        from app.domains.communication.services.data_request_voice_service import (
            _voice_redis_key,
        )
        key = _voice_redis_key("abc-123")
        assert key.startswith("voice_calls:abc-123:")
        parts = key.split(":")
        assert len(parts) == 3

    def test_third_part_is_year_month(self):
        from app.domains.communication.services.data_request_voice_service import (
            _voice_redis_key,
        )
        key = _voice_redis_key("abc-123")
        ym = key.split(":")[2]
        assert len(ym) == 7  # "2026-06"
        assert ym[4] == "-"
        int(ym[:4])   # year is numeric
        int(ym[5:])   # month is numeric

    def test_different_company_ids_produce_different_keys(self):
        from app.domains.communication.services.data_request_voice_service import (
            _voice_redis_key,
        )
        assert _voice_redis_key("co-1") != _voice_redis_key("co-2")


def _patch_redis_from_url(return_value=None, side_effect=None):
    """Patch redis.asyncio.from_url on the REAL module (already imported in venv).

    patch.dict sys.modules doesn't work here because ``redis.asyncio`` is
    already cached in sys.modules before the test runs; the ``import`` statement
    inside _check_voice_budget returns the cached real module, not the mock.
    patch.object on the real module patches the attribute in-place.
    """
    import redis.asyncio as _real_aioredis
    if side_effect is not None:
        return patch.object(_real_aioredis, "from_url", side_effect=side_effect)
    return patch.object(_real_aioredis, "from_url", return_value=return_value)


class TestCheckVoiceBudget:
    @pytest.mark.asyncio
    async def test_under_limit_is_allowed(self):
        """count(42) < limit(100) -> (True, 42)"""
        from app.domains.communication.services.data_request_voice_service import (
            _check_voice_budget,
        )
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=b"42")
        mock_r.aclose = AsyncMock()

        with _patch_redis_from_url(return_value=mock_r):
            allowed, count = await _check_voice_budget("co-1", limit=100)
        assert allowed is True
        assert count == 42

    @pytest.mark.asyncio
    async def test_at_limit_is_blocked(self):
        """count(100) >= limit(100) -> (False, 100)"""
        from app.domains.communication.services.data_request_voice_service import (
            _check_voice_budget,
        )
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=b"100")
        mock_r.aclose = AsyncMock()

        with _patch_redis_from_url(return_value=mock_r):
            allowed, count = await _check_voice_budget("co-1", limit=100)
        assert allowed is False
        assert count == 100

    @pytest.mark.asyncio
    async def test_over_limit_is_blocked(self):
        """count(150) > limit(100) -> (False, 150)"""
        from app.domains.communication.services.data_request_voice_service import (
            _check_voice_budget,
        )
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=b"150")
        mock_r.aclose = AsyncMock()

        with _patch_redis_from_url(return_value=mock_r):
            allowed, count = await _check_voice_budget("co-1", limit=100)
        assert allowed is False
        assert count == 150

    @pytest.mark.asyncio
    async def test_redis_unavailable_fail_open(self):
        """Redis unavailable (ConnectionError) -> (True, 0) -- fail open."""
        from app.domains.communication.services.data_request_voice_service import (
            _check_voice_budget,
        )
        with _patch_redis_from_url(side_effect=ConnectionError("Redis down")):
            allowed, count = await _check_voice_budget("co-1")
        assert allowed is True
        assert count == 0

    @pytest.mark.asyncio
    async def test_empty_redis_key_means_zero_calls(self):
        """No key in Redis yet -> 0 calls -> (True, 0)"""
        from app.domains.communication.services.data_request_voice_service import (
            _check_voice_budget,
        )
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=None)
        mock_r.aclose = AsyncMock()

        with _patch_redis_from_url(return_value=mock_r):
            allowed, count = await _check_voice_budget("co-fresh", limit=100)
        assert allowed is True
        assert count == 0


class TestDefaultLimit:
    def test_default_limit_is_100(self):
        """Constant must be 100 (cost guardrail specification)."""
        from app.domains.communication.services.data_request_voice_service import (
            VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
        )
        assert VOICE_CALLS_MONTHLY_DEFAULT_LIMIT == 100


# -- Tests for start_collection budget integration ----------------------------

class TestStartCollectionBudgetGate:
    """Integration: start_collection respects the budget gate."""

    @pytest.mark.asyncio
    async def test_under_budget_proceeds_to_initiate_call(self):
        """Budget under limit -> initiate_call is called -> voice_collection_initiated."""
        from app.domains.communication.services.data_request_voice_service import (
            DataRequestVoiceService,
        )
        dr = _FakeDataRequest()
        db = _make_db(dr)
        mock_orch_class, mock_plugin_class, mock_orch_instance = _fake_orchestrator("initiated")

        import sys as _sys
        _sys.modules["app.domains.voice.plugins.data_collection_voice_plugin"] = MagicMock(
            DataCollectionVoicePlugin=mock_plugin_class
        )
        _sys.modules["app.domains.voice.services.voice_screening_orchestrator"] = MagicMock(
            VoiceCoreOrchestrator=mock_orch_class
        )
        try:
            with _consent_granted_patch(), _budget_allowed_patch(True, 42), _increment_spy() as mock_incr:
                result = await DataRequestVoiceService().start_collection(db, dr.id, "+5511999999999")
        finally:
            _sys.modules.pop("app.domains.voice.plugins.data_collection_voice_plugin", None)
            _sys.modules.pop("app.domains.voice.services.voice_screening_orchestrator", None)

        assert result["status"] == "voice_collection_initiated"
        mock_orch_instance.initiate_call.assert_called_once()
        mock_incr.assert_called_once_with(str(dr.company_id))

    @pytest.mark.asyncio
    async def test_budget_exceeded_blocks_initiate_call(self):
        """Budget at/over limit -> initiate_call NOT called -> voice_collection_budget_exceeded."""
        from app.domains.communication.services.data_request_voice_service import (
            DataRequestVoiceService,
            VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
        )
        dr = _FakeDataRequest()
        db = _make_db(dr)
        mock_orch_class, mock_plugin_class, mock_orch_instance = _fake_orchestrator("initiated")

        import sys as _sys
        _sys.modules["app.domains.voice.plugins.data_collection_voice_plugin"] = MagicMock(
            DataCollectionVoicePlugin=mock_plugin_class
        )
        _sys.modules["app.domains.voice.services.voice_screening_orchestrator"] = MagicMock(
            VoiceCoreOrchestrator=mock_orch_class
        )
        try:
            with _consent_granted_patch(), _budget_allowed_patch(False, 100), _increment_spy() as mock_incr:
                result = await DataRequestVoiceService().start_collection(db, dr.id, "+5511999999999")
        finally:
            _sys.modules.pop("app.domains.voice.plugins.data_collection_voice_plugin", None)
            _sys.modules.pop("app.domains.voice.services.voice_screening_orchestrator", None)

        assert result["status"] == "voice_collection_budget_exceeded"
        assert result["calls_this_month"] == 100
        assert result["limit"] == VOICE_CALLS_MONTHLY_DEFAULT_LIMIT
        assert result["channel"] == "voice"
        assert result["note"] == "monthly_voice_call_limit_reached"
        mock_orch_instance.initiate_call.assert_not_called()
        mock_incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_called_on_successful_initiation(self):
        """When orch_status=initiated, _increment_voice_calls is called exactly once."""
        from app.domains.communication.services.data_request_voice_service import (
            DataRequestVoiceService,
        )
        dr = _FakeDataRequest()
        db = _make_db(dr)
        mock_orch_class, mock_plugin_class, mock_orch_instance = _fake_orchestrator("initiated")

        import sys as _sys
        _sys.modules["app.domains.voice.plugins.data_collection_voice_plugin"] = MagicMock(
            DataCollectionVoicePlugin=mock_plugin_class
        )
        _sys.modules["app.domains.voice.services.voice_screening_orchestrator"] = MagicMock(
            VoiceCoreOrchestrator=mock_orch_class
        )
        try:
            with _consent_granted_patch(), _budget_allowed_patch(True, 5), _increment_spy() as mock_incr:
                await DataRequestVoiceService().start_collection(db, dr.id, "+5511999999999")
        finally:
            _sys.modules.pop("app.domains.voice.plugins.data_collection_voice_plugin", None)
            _sys.modules.pop("app.domains.voice.services.voice_screening_orchestrator", None)

        mock_incr.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_not_called_on_fallback_status(self):
        """When orch_status=fallback (Twilio unavailable), increment NOT called."""
        from app.domains.communication.services.data_request_voice_service import (
            DataRequestVoiceService,
        )
        dr = _FakeDataRequest()
        db = _make_db(dr)
        mock_orch_class, mock_plugin_class, mock_orch_instance = _fake_orchestrator("fallback")

        import sys as _sys
        _sys.modules["app.domains.voice.plugins.data_collection_voice_plugin"] = MagicMock(
            DataCollectionVoicePlugin=mock_plugin_class
        )
        _sys.modules["app.domains.voice.services.voice_screening_orchestrator"] = MagicMock(
            VoiceCoreOrchestrator=mock_orch_class
        )
        try:
            with _consent_granted_patch(), _budget_allowed_patch(True, 10), _increment_spy() as mock_incr:
                result = await DataRequestVoiceService().start_collection(db, dr.id, "+5511999999999")
        finally:
            _sys.modules.pop("app.domains.voice.plugins.data_collection_voice_plugin", None)
            _sys.modules.pop("app.domains.voice.services.voice_screening_orchestrator", None)

        assert result["status"] == "voice_collection_fallback"
        mock_incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_consent_revoked_fires_before_budget_check(self):
        """Consent revoked -> no_consent status; budget check not invoked."""
        from app.domains.communication.services.data_request_voice_service import (
            DataRequestVoiceService,
        )
        dr = _FakeDataRequest()
        db = _make_db(dr)

        with patch(
            "app.domains.communication.services.data_request_voice_service"
            ".DataRequestVoiceService._classify_consent",
            AsyncMock(return_value="revoked"),
        ), _budget_allowed_patch(False, 999) as mock_budget:
            result = await DataRequestVoiceService().start_collection(db, dr.id, "+5511999999999")

        # Consent gate fires before budget gate
        assert result["status"] == "voice_collection_no_consent"
        mock_budget.assert_not_called()
