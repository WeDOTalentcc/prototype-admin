"""Contract tests — ADR-WT-2027 BYOK gate skip canonical (Opcao C).

Pins the contract: when tenant has own API key (BYOK active), the canonical
``check_credit_budget`` MUST NOT raise ``AICreditExhausted`` even if
``current_usage >= monthly_limit``. It MUST log + emit metric when an
optional ``byok_soft_cap`` is exceeded, but still NOT raise.

Pure-unit tests with mocked AsyncSession + patched ``is_byok_active`` /
``tenant_llm_context.get_tenant_llm_config``. We DO NOT spin up a real DB
session -- that's an integration concern. This file lives in
``tests/contract/`` because the contract under test is behavioral, not
DB-shape (separately validated by alembic chain tests).

Fix Bug B3: pre-fix, the gate blocked BYOK tenants. UI advertised unmetered,
backend silently blocked. Post-fix, BYOK gate switches to track-only.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.services.ai_credit_gate import (
    AICreditExhausted,
    check_credit_budget,
)
from app.shared.services.byok_detector import is_byok_active


COMPANY_BYOK = "11111111-1111-1111-1111-111111111111"
COMPANY_WEDOPAID = "22222222-2222-2222-2222-222222222222"


def _make_balance_mock(
    *,
    monthly_limit: int = 100_000,
    current_usage: int = 0,
    byok_soft_cap: int | None = None,
):
    """Build a magicmock simulating an AiCreditsBalance row."""
    balance = MagicMock()
    balance.monthly_limit = monthly_limit
    balance.current_usage = current_usage
    balance.byok_soft_cap = byok_soft_cap
    balance.byok_active = False  # gate detects fresh via byok_detector
    return balance


def _make_db_returning(balance):
    """Build an AsyncMock AsyncSession.execute() returning balance row."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=balance)
    db.execute = AsyncMock(return_value=result_mock)
    return db


# ----------------------------------------------------------------------
# is_byok_active tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_byok_detection_returns_true_when_openai_key_set():
    """When tenant has OpenAI key, detector returns (True, 'openai')."""
    fake_config = {
        "providers": {
            "openai": {"api_key": "sk-real-key-12345", "model": "gpt-4o"},
        }
    }
    with patch(
        "app.shared.tenant_llm_context.get_tenant_llm_config",
        new=AsyncMock(return_value=fake_config),
    ):
        active, provider = await is_byok_active(
            None, COMPANY_BYOK, service="voice_realtime"
        )
        assert active is True
        assert provider == "openai"


@pytest.mark.asyncio
async def test_byok_detection_returns_false_when_no_key():
    """No API key configured -> (False, provider)."""
    fake_config = {"providers": {}}
    with patch(
        "app.shared.tenant_llm_context.get_tenant_llm_config",
        new=AsyncMock(return_value=fake_config),
    ):
        active, provider = await is_byok_active(
            None, COMPANY_BYOK, service="anthropic_sdk"
        )
        assert active is False
        assert provider == "anthropic"


@pytest.mark.asyncio
async def test_byok_detection_provider_specific():
    """Anthropic key does NOT count as OpenAI BYOK (per-provider)."""
    fake_config = {
        "providers": {
            "anthropic": {"api_key": "sk-ant-real", "model": "claude-sonnet-4"},
        }
    }
    with patch(
        "app.shared.tenant_llm_context.get_tenant_llm_config",
        new=AsyncMock(return_value=fake_config),
    ):
        active, provider = await is_byok_active(
            None, COMPANY_BYOK, service="voice_realtime"  # openai service
        )
        assert active is False  # no openai key
        assert provider == "openai"

        active2, provider2 = await is_byok_active(
            None, COMPANY_BYOK, service="anthropic_sdk"
        )
        assert active2 is True  # anthropic key IS set
        assert provider2 == "anthropic"


@pytest.mark.asyncio
async def test_byok_detection_ignores_masked_key():
    """Masked key (e.g. 'sk-abc...wxyz' from GET endpoint) is NOT BYOK."""
    fake_config = {
        "providers": {
            "openai": {"api_key": "sk-abcd...wxyz", "model": "gpt-4o"},
        }
    }
    with patch(
        "app.shared.tenant_llm_context.get_tenant_llm_config",
        new=AsyncMock(return_value=fake_config),
    ):
        active, _ = await is_byok_active(None, COMPANY_BYOK, service="voice_realtime")
        assert active is False  # masked key never counts


@pytest.mark.asyncio
async def test_byok_detection_fail_safe_returns_false_on_error():
    """DB / cache error -> (False, provider) (fail-safe WeDo-paid)."""
    with patch(
        "app.shared.tenant_llm_context.get_tenant_llm_config",
        new=AsyncMock(side_effect=RuntimeError("DB outage")),
    ):
        active, provider = await is_byok_active(
            None, COMPANY_BYOK, service="anthropic_sdk"
        )
        assert active is False
        assert provider == "anthropic"


@pytest.mark.asyncio
async def test_byok_detection_unknown_service_returns_false():
    """Service not in _SERVICE_TO_PROVIDER -> assumes WeDo-paid."""
    active, provider = await is_byok_active(
        None, COMPANY_BYOK, service="totally_unknown_xyz"
    )
    assert active is False
    assert provider is None


# ----------------------------------------------------------------------
# check_credit_budget BYOK paths
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_credit_budget_track_only_when_byok():
    """BYOK tenant + usage UNDER limit -> result.byok=True, no raise."""
    balance = _make_balance_mock(monthly_limit=100_000, current_usage=5_000)
    db = _make_db_returning(balance)

    result = await check_credit_budget(
        db,
        COMPANY_BYOK,
        estimated_tokens=1_000,
        service="anthropic_sdk",
        byok_active=True,  # explicit override skips detector
    )

    assert result["byok"] is True
    assert result["remaining"] is None  # unlimited from WeDo perspective
    assert result["current_usage"] == 5_000


@pytest.mark.asyncio
async def test_check_credit_budget_no_raise_when_byok_over_limit():
    """**BUG B3 FIX**: BYOK tenant OVER limit must NOT raise."""
    balance = _make_balance_mock(monthly_limit=10_000, current_usage=20_000)
    db = _make_db_returning(balance)

    # Pre-fix: this would raise AICreditExhausted. Post-fix: track-only.
    result = await check_credit_budget(
        db,
        COMPANY_BYOK,
        estimated_tokens=5_000,
        service="anthropic_sdk",
        byok_active=True,
    )

    assert result["byok"] is True
    # NO exception raised -- this is the contract.


@pytest.mark.asyncio
async def test_check_credit_budget_blocks_when_no_byok_over_limit():
    """WeDo-paid tenant OVER limit -> raises (unchanged behavior)."""
    balance = _make_balance_mock(monthly_limit=10_000, current_usage=20_000)
    db = _make_db_returning(balance)

    with pytest.raises(AICreditExhausted) as exc_info:
        await check_credit_budget(
            db,
            COMPANY_WEDOPAID,
            estimated_tokens=5_000,
            service="anthropic_sdk",
            byok_active=False,
        )
    assert exc_info.value.company_id == COMPANY_WEDOPAID
    assert exc_info.value.service == "anthropic_sdk"


@pytest.mark.asyncio
async def test_soft_cap_emits_metric_when_breached_not_raises():
    """BYOK tenant exceeding soft_cap -> metric emitted, NO raise."""
    balance = _make_balance_mock(
        monthly_limit=10_000,
        current_usage=50_000,
        byok_soft_cap=40_000,  # already breached
    )
    db = _make_db_returning(balance)

    with patch(
        "app.shared.services.ai_credit_gate._emit_soft_cap_breached_metric"
    ) as mock_emit:
        result = await check_credit_budget(
            db,
            COMPANY_BYOK,
            estimated_tokens=1_000,
            service="anthropic_sdk",
            byok_active=True,
        )

    assert result["byok"] is True
    assert result["soft_cap"] == 40_000
    mock_emit.assert_called_once()
    call_args = mock_emit.call_args
    assert call_args.args[0] == COMPANY_BYOK
    assert call_args.kwargs.get("service") == "anthropic_sdk"


@pytest.mark.asyncio
async def test_soft_cap_not_breached_no_metric():
    """BYOK tenant UNDER soft_cap -> no soft-cap metric emitted."""
    balance = _make_balance_mock(
        monthly_limit=10_000,
        current_usage=5_000,
        byok_soft_cap=40_000,
    )
    db = _make_db_returning(balance)

    with patch(
        "app.shared.services.ai_credit_gate._emit_soft_cap_breached_metric"
    ) as mock_emit:
        result = await check_credit_budget(
            db,
            COMPANY_BYOK,
            estimated_tokens=1_000,
            service="anthropic_sdk",
            byok_active=True,
        )

    assert result["byok"] is True
    mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_byok_active_flag_refreshed_on_key_update():
    """refresh_byok_active_flag denormalizes flag from providers_dict."""
    from app.shared.tenant_llm_context import refresh_byok_active_flag

    balance = _make_balance_mock()
    balance.byok_active = False  # start clean
    db = _make_db_returning(balance)
    # flush is awaited by helper
    db.flush = AsyncMock()

    # Case A: real key -> byok_active should flip True
    providers_dict_byok = {
        "anthropic": {"api_key": "sk-ant-real-12345", "model": "claude-sonnet-4"},
    }
    result = await refresh_byok_active_flag(db, COMPANY_BYOK, providers_dict_byok)
    assert result is True
    assert balance.byok_active is True
    db.flush.assert_awaited()

    # Case B: only masked / empty -> byok_active should remain False
    balance.byok_active = True  # simulate previous state
    db.flush.reset_mock()
    providers_dict_masked = {
        "openai": {"api_key": "sk-abc...xyz", "model": "gpt-4o"},
        "gemini": {"api_key": "", "model": "gemini-2.5-flash"},
    }
    result = await refresh_byok_active_flag(db, COMPANY_BYOK, providers_dict_masked)
    assert result is False
    assert balance.byok_active is False

    # Case C: _remove sentinel ignored
    balance.byok_active = True
    providers_dict_remove = {
        "anthropic": {"_remove": True},
    }
    result = await refresh_byok_active_flag(db, COMPANY_BYOK, providers_dict_remove)
    assert result is False
    assert balance.byok_active is False


@pytest.mark.asyncio
async def test_check_credit_budget_unconfigured_tenant_respects_byok():
    """When ai_credits_balance row is missing, BYOK still respected."""
    db = _make_db_returning(None)  # no balance row

    # WeDo-paid path -> unconfigured returns remaining=0 (legacy behavior)
    result_wp = await check_credit_budget(
        db, COMPANY_WEDOPAID, service="anthropic_sdk", byok_active=False
    )
    assert result_wp.get("unconfigured") is True
    assert result_wp["byok"] is False

    # BYOK path -> unconfigured returns byok=True, remaining=None
    result_byok = await check_credit_budget(
        db, COMPANY_BYOK, service="anthropic_sdk", byok_active=True
    )
    assert result_byok.get("unconfigured") is True
    assert result_byok["byok"] is True
    assert result_byok["remaining"] is None
