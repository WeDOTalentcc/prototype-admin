"""P1-6: Contract sensor for lia_tone / ai_persona.tone divergence detection.

Per CLAUDE.md "lia_tone canonical precedence":
  - Outbound messages (email/WhatsApp to candidates): lia_tone wins.
  - Chat system prompt: ai_persona.tone wins.
  - Divergence = silent configuration inconsistency the recruiter cannot see.

Two sensor sites:
  1. Write-time (ai_persona_service.update_ai_persona): fires when a prior
     lia_tone value differs from the translated EN of the new ai_persona.tone.
     Catches: legacy ai_config.py endpoint wrote lia_tone independently, then
     recruiter updates persona via the canonical panel.
  2. Read-time (communication_dispatcher.dispatch_message): fires when lia_tone
     stored in DB differs from ai_persona.tone translated to EN. Catches:
     persistent configs where the two paths diverged before canonical sync existed.

Both sensors are warn-only (no gate, no raise). Logging format uses the key
"lia_tone_divergence" so Grafana/CloudWatch filters can count incidents.
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.persona.services import ai_persona_service
from app.domains.persona.services.ai_persona_validator import (
    DEFAULT_AI_NAME,
    DEFAULT_AI_TONE,
    TONE_PT_TO_EN_LEGACY,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_policy(communication_rules: dict | None) -> MagicMock:
    policy = MagicMock()
    policy.communication_rules = communication_rules if communication_rules is not None else {}
    return policy


def _make_repo(policy: MagicMock | None, *, create_returns=None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=policy)
    repo.create_if_missing = AsyncMock(return_value=create_returns or policy or _make_policy({}))
    repo.flush = AsyncMock()
    return repo


def _install_repo_mock(repo: MagicMock) -> None:
    import app.domains.persona.services.ai_persona_service as svc_mod
    svc_mod.HiringPolicyRepository = MagicMock(return_value=repo)


# ---------------------------------------------------------------------------
# Write-time sensor: ai_persona_service
# ---------------------------------------------------------------------------

class TestWriteTimeSensor:
    """ai_persona_service.update_ai_persona emits lia_tone_divergence warning
    when prior lia_tone (EN) differs from the translated new ai_persona.tone."""

    @pytest.mark.asyncio
    async def test_logs_warning_when_prior_lia_tone_diverges(self, caplog):
        """Prior lia_tone='friendly' + new tone='formal' (EN: 'formal') → diverge → warn."""
        policy = _make_policy({
            "ai_persona": {"name": "Sofia", "tone": "amigavel"},
            "lia_tone": "friendly",  # EN value set by legacy path
        })
        repo = _make_repo(policy, create_returns=policy)
        _install_repo_mock(repo)

        with caplog.at_level(logging.WARNING, logger="app.domains.persona.services.ai_persona_service"):
            await ai_persona_service.update_ai_persona(
                "co-test", MagicMock(), name=None, tone="formal",
            )

        assert any("lia_tone_divergence" in r.message for r in caplog.records), (
            "Expected 'lia_tone_divergence' warning not found in log records. "
            f"Records: {[r.message for r in caplog.records]}"
        )

    @pytest.mark.asyncio
    async def test_no_warning_when_tones_are_consistent(self, caplog):
        """Prior lia_tone='friendly' + new tone='amigavel' (EN: 'friendly') → match → no warn."""
        policy = _make_policy({
            "ai_persona": {"name": "Sofia", "tone": "formal"},
            "lia_tone": "friendly",  # already matches amigavel→friendly
        })
        repo = _make_repo(policy, create_returns=policy)
        _install_repo_mock(repo)

        with caplog.at_level(logging.WARNING, logger="app.domains.persona.services.ai_persona_service"):
            await ai_persona_service.update_ai_persona(
                "co-test", MagicMock(), name=None, tone="amigavel",
            )

        divergence_logs = [r for r in caplog.records if "lia_tone_divergence" in r.message]
        assert not divergence_logs, (
            f"Unexpected lia_tone_divergence warning for consistent tones: {divergence_logs}"
        )

    @pytest.mark.asyncio
    async def test_no_warning_when_no_prior_lia_tone(self, caplog):
        """Cold-start tenant (no lia_tone yet) → no warning (nothing to diverge from)."""
        policy = _make_policy({
            "ai_persona": {"name": "LIA", "tone": DEFAULT_AI_TONE},
            # lia_tone absent — new tenant
        })
        repo = _make_repo(policy, create_returns=policy)
        _install_repo_mock(repo)

        with caplog.at_level(logging.WARNING, logger="app.domains.persona.services.ai_persona_service"):
            await ai_persona_service.update_ai_persona(
                "co-new", MagicMock(), name=None, tone="profissional",
            )

        divergence_logs = [r for r in caplog.records if "lia_tone_divergence" in r.message]
        assert not divergence_logs, (
            f"Unexpected lia_tone_divergence warning for cold-start tenant: {divergence_logs}"
        )

    @pytest.mark.asyncio
    async def test_write_time_sensor_resolves_divergence(self, caplog):
        """After the warning is logged, rules['lia_tone'] is set to the new canonical EN value.
        The sensor logs + resolves — does not leave DB in diverged state."""
        policy = _make_policy({
            "ai_persona": {"name": "Sofia", "tone": "amigavel"},
            "lia_tone": "formal",  # stale value
        })
        repo = _make_repo(policy, create_returns=policy)
        _install_repo_mock(repo)

        await ai_persona_service.update_ai_persona(
            "co-test", MagicMock(), name=None, tone="profissional",
        )

        # After write, lia_tone must be updated to EN equivalent of "profissional"
        expected_en = TONE_PT_TO_EN_LEGACY["profissional"]  # "professional"
        assert policy.communication_rules["lia_tone"] == expected_en, (
            f"lia_tone not resolved after divergence. Expected {expected_en!r}, "
            f"got {policy.communication_rules.get('lia_tone')!r}"
        )

    @pytest.mark.asyncio
    async def test_warning_includes_both_tone_values(self, caplog):
        """Warning message must include prior_lia_tone and the new EN tone for diagnostics."""
        policy = _make_policy({
            "ai_persona": {"name": "Sofia", "tone": "amigavel"},
            "lia_tone": "formal",
        })
        repo = _make_repo(policy, create_returns=policy)
        _install_repo_mock(repo)

        with caplog.at_level(logging.WARNING, logger="app.domains.persona.services.ai_persona_service"):
            await ai_persona_service.update_ai_persona(
                "co-test", MagicMock(), name=None, tone="amigavel",
            )

        # "formal" diverges from amigavel→"friendly"
        warn_msgs = [r.message for r in caplog.records if "lia_tone_divergence" in r.message]
        assert warn_msgs, "No lia_tone_divergence warning emitted"
        msg = warn_msgs[0]
        assert "formal" in msg, f"Prior lia_tone 'formal' not in warning: {msg!r}"
        assert "friendly" in msg or "amigavel" in msg, (
            f"New tone not visible in warning: {msg!r}"
        )


# ---------------------------------------------------------------------------
# Read-time sensor: communication_dispatcher
# ---------------------------------------------------------------------------

class TestReadTimeSensor:
    """CommunicationDispatcher.dispatch_message emits lia_tone_divergence
    when the stored lia_tone (EN) differs from ai_persona.tone normalized to EN."""

    def _make_dispatcher(self):
        from app.domains.communication.services.communication_dispatcher import (
            CommunicationDispatcher,
        )
        return CommunicationDispatcher()

    def _make_policy_obj(self, communication_rules: dict):
        policy = MagicMock()
        policy.communication_rules = communication_rules
        return policy

    @pytest.mark.asyncio
    async def test_read_time_logs_warning_on_divergence(self, caplog):
        """lia_tone='formal' + ai_persona.tone='amigavel' (EN: 'friendly') → diverge → warn."""
        dispatcher = self._make_dispatcher()
        policy = self._make_policy_obj({
            "lia_tone": "formal",
            "ai_persona": {"name": "Sofia", "tone": "amigavel"},
        })

        with caplog.at_level(logging.WARNING):
            with patch(
                "app.domains.communication.services.communication_dispatcher.get_policy_for_company",
                new=AsyncMock(return_value=policy),
            ):
                with patch(
                    "app.domains.communication.services.communication_dispatcher.resolve_policy_value",
                    side_effect=lambda p, *keys, default=None: (
                        p.communication_rules.get(keys[-1], default)
                        if keys else default
                    ),
                ):
                    with patch.object(dispatcher, "send_email", return_value={"success": True, "message_id": "x"}):
                        await dispatcher.dispatch_message(
                            company_id="co-test",
                            recipient_email="candidate@example.com",
                            message="Hello",
                            db=MagicMock(),
                        )

        assert any("lia_tone_divergence" in r.message for r in caplog.records), (
            f"Expected 'lia_tone_divergence' warning. Records: {[r.message for r in caplog.records]}"
        )

    @pytest.mark.asyncio
    async def test_read_time_no_warning_when_tones_match(self, caplog):
        """lia_tone='friendly' + ai_persona.tone='amigavel' (EN: 'friendly') → match → no warn."""
        dispatcher = self._make_dispatcher()
        policy = self._make_policy_obj({
            "lia_tone": "friendly",
            "ai_persona": {"name": "Sofia", "tone": "amigavel"},
        })

        with caplog.at_level(logging.WARNING):
            with patch(
                "app.domains.communication.services.communication_dispatcher.get_policy_for_company",
                new=AsyncMock(return_value=policy),
            ):
                with patch(
                    "app.domains.communication.services.communication_dispatcher.resolve_policy_value",
                    side_effect=lambda p, *keys, default=None: (
                        p.communication_rules.get(keys[-1], default)
                        if keys else default
                    ),
                ):
                    with patch.object(dispatcher, "send_email", return_value={"success": True, "message_id": "x"}):
                        await dispatcher.dispatch_message(
                            company_id="co-test",
                            recipient_email="candidate@example.com",
                            message="Hello",
                            db=MagicMock(),
                        )

        divergence_logs = [r for r in caplog.records if "lia_tone_divergence" in r.message]
        assert not divergence_logs, f"Unexpected warning for matching tones: {divergence_logs}"

    @pytest.mark.asyncio
    async def test_read_time_no_warning_when_ai_persona_absent(self, caplog):
        """Legacy config without ai_persona field — no ai_persona.tone to compare → no warn."""
        dispatcher = self._make_dispatcher()
        policy = self._make_policy_obj({
            "lia_tone": "professional",
            # ai_persona absent — legacy config
        })

        with caplog.at_level(logging.WARNING):
            with patch(
                "app.domains.communication.services.communication_dispatcher.get_policy_for_company",
                new=AsyncMock(return_value=policy),
            ):
                with patch(
                    "app.domains.communication.services.communication_dispatcher.resolve_policy_value",
                    side_effect=lambda p, *keys, default=None: (
                        p.communication_rules.get(keys[-1], default)
                        if keys else default
                    ),
                ):
                    with patch.object(dispatcher, "send_email", return_value={"success": True, "message_id": "x"}):
                        await dispatcher.dispatch_message(
                            company_id="co-test",
                            recipient_email="candidate@example.com",
                            message="Hello",
                            db=MagicMock(),
                        )

        divergence_logs = [r for r in caplog.records if "lia_tone_divergence" in r.message]
        assert not divergence_logs, (
            f"Unexpected warning for legacy config (no ai_persona): {divergence_logs}"
        )

    @pytest.mark.asyncio
    async def test_read_time_no_false_positive_for_default_professional(self, caplog):
        """profissional→professional: both lia_tone and ai_persona.tone at defaults
        must NOT trigger warning (the most common state for new tenants)."""
        dispatcher = self._make_dispatcher()
        policy = self._make_policy_obj({
            "lia_tone": "professional",
            "ai_persona": {"name": "LIA", "tone": "profissional"},
        })

        with caplog.at_level(logging.WARNING):
            with patch(
                "app.domains.communication.services.communication_dispatcher.get_policy_for_company",
                new=AsyncMock(return_value=policy),
            ):
                with patch(
                    "app.domains.communication.services.communication_dispatcher.resolve_policy_value",
                    side_effect=lambda p, *keys, default=None: (
                        p.communication_rules.get(keys[-1], default)
                        if keys else default
                    ),
                ):
                    with patch.object(dispatcher, "send_email", return_value={"success": True, "message_id": "x"}):
                        await dispatcher.dispatch_message(
                            company_id="co-test",
                            recipient_email="candidate@example.com",
                            message="Hello",
                            db=MagicMock(),
                        )

        divergence_logs = [r for r in caplog.records if "lia_tone_divergence" in r.message]
        assert not divergence_logs, (
            "False positive: profissional/professional (same tone, different locale) "
            f"should NOT trigger divergence. Records: {divergence_logs}"
        )
