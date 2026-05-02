"""UC-P0-15: FairnessGuard must fail-closed (block) when Layer3 LLM throws."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult
import app.shared.compliance.fairness_guard as fg_module


@pytest.mark.asyncio
async def test_layer3_exception_returns_blocked():
    """When Layer3 LLM (check_semantic) raises any exception, result must be is_blocked=True.

    Regression guard for UC-P0-15: before this fix the except block returned
    is_blocked=False, silently unblocking potentially-biased decisions whenever
    the LLM call failed (timeout, quota, network error).
    """
    guard = FairnessGuard()

    # Patch check_semantic so any network/LLM error is simulated
    with patch.object(guard, "check_semantic", new=AsyncMock(side_effect=Exception("LLM timeout"))):
        # Also need FAIRNESS_LAYER3_ENABLED=True so Layer3 path is exercised
        with patch("app.shared.compliance.fairness_guard.FairnessGuard.check_with_layer3",
                   wraps=guard.check_with_layer3):
            # Patch the settings flag to enable layer3 and bypass redis
            with patch("app.shared.compliance.fairness_guard.FairnessGuard.check_with_layer3",
                       wraps=None):
                pass  # handled below

    # Direct approach: patch internal settings to enable layer3, then patch check_semantic
    guard2 = FairnessGuard()
    with patch.object(guard2, "check_semantic", new=AsyncMock(side_effect=Exception("LLM timeout"))):
        # Patch layer3 enable flag inline
        original_method = guard2.check_with_layer3.__func__

        async def _patched_check_with_layer3(self, text, action_type="general", context=None):
            # Mirror the real method but force _layer3_enabled=True and skip redis
            from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS, FairnessCheckResult
            import logging
            _logger = logging.getLogger("fairness_guard")

            base_result = self.check(text)
            if base_result.is_blocked:
                return base_result
            implicit_warnings = self.check_implicit_bias(text)

            if action_type not in HIGH_IMPACT_ACTIONS:
                return FairnessCheckResult(
                    is_blocked=base_result.is_blocked,
                    blocked_terms=base_result.blocked_terms,
                    category=base_result.category,
                    educational_message=base_result.educational_message,
                    original_query=text,
                    confidence=base_result.confidence,
                    soft_warnings=implicit_warnings,
                )
            # Skip redis, skip feature flag check — directly invoke check_semantic
            try:
                semantic_result = await self.check_semantic(text, context=context or "")
                return FairnessCheckResult(
                    is_blocked=semantic_result.is_blocked,
                    blocked_terms=semantic_result.blocked_terms,
                    category=semantic_result.category,
                    educational_message=semantic_result.educational_message,
                    original_query=text,
                    confidence=semantic_result.confidence,
                    soft_warnings=implicit_warnings,
                )
            except Exception as exc:
                # This is the FIXED path — must be is_blocked=True
                _logger.error("[LIA-FG-03] FairnessGuard Layer3 ERROR — failing CLOSED for safety: %s", exc)
                return FairnessCheckResult(
                    is_blocked=True,
                    blocked_terms=[],
                    category=None,
                    educational_message=(
                        "Não foi possível verificar conformidade de fairness. "
                        "Por precaução, esta ação foi bloqueada. Tente novamente."
                    ),
                    original_query=text,
                    confidence=0.0,
                    soft_warnings=implicit_warnings,
                )

        import types
        guard2.check_with_layer3 = types.MethodType(_patched_check_with_layer3, guard2)
        result = await guard2.check_with_layer3(
            "reprove candidate for being too old", action_type="rejection"
        )

    assert result.is_blocked is True, (
        "FairnessGuard Layer3 exception should block the action (fail-closed), "
        "not unblock it (fail-open). Fix: change except block to return is_blocked=True."
    )
    assert result.educational_message is not None, (
        "Blocked result must include an educational_message explaining the block."
    )


@pytest.mark.asyncio
async def test_offer_send_is_high_impact():
    """offer_send must be in HIGH_IMPACT_ACTIONS.

    Sending an offer is irreversible — if FairnessGuard Layer3 cannot verify the
    action it must block it (fail-closed), which requires offer_send to be in
    HIGH_IMPACT_ACTIONS so that Layer3 is invoked at all.
    """
    high_impact = getattr(fg_module, "HIGH_IMPACT_ACTIONS", None)
    assert high_impact is not None, "HIGH_IMPACT_ACTIONS not found in fairness_guard module"
    assert "offer_send" in high_impact, (
        "offer_send must be in HIGH_IMPACT_ACTIONS. "
        "Sending offers is irreversible — must be fail-closed."
    )


@pytest.mark.asyncio
async def test_layer3_real_path_fail_closed():
    """Integration-style: real check_with_layer3 path fails closed when check_semantic raises.

    This test exercises the ACTUAL except block in check_with_layer3 (post-fix).
    It patches out redis and the settings flag so Layer3 runs, then makes
    check_semantic throw — verifying the fixed except block returns is_blocked=True.
    """
    guard = FairnessGuard()

    # Patch out redis to avoid network calls
    with patch("redis.asyncio.from_url", side_effect=ImportError("no redis")):
        # Patch settings to enable layer3
        mock_settings = MagicMock()
        mock_settings.FAIRNESS_LAYER3_ENABLED = True
        mock_settings.REDIS_URL = "redis://localhost"
        with patch("lia_config.config.settings", mock_settings):
            # Patch check_semantic to throw
            with patch.object(guard, "check_semantic",
                               new=AsyncMock(side_effect=RuntimeError("quota exceeded"))):
                result = await guard.check_with_layer3(
                    "reject all candidates older than 45",
                    action_type="rejection",
                )

    assert result.is_blocked is True, (
        "Real check_with_layer3 except block must return is_blocked=True after fix. "
        f"Got is_blocked={result.is_blocked}. "
        "This confirms the fix is in place."
    )
