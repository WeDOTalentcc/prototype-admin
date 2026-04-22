"""
FIX 14 — Regression test: onboarding hints must NOT hijack agent_type.

Root cause of bug: main_orchestrator.py previously forced
    _agent_type = "company_settings"
whenever PreConditionChecker emitted an onboarding hint. This broke
multi-turn conversations where user was in another domain (sourcing,
pipeline, etc.) — the agent_type override sent every message to the
company_settings agent regardless of context.

These tests are structural (check source), not behavioral, because the
full orchestrator pipeline is too heavy to instantiate in unit tests.
The FIX 12 tests use the same pattern (structural checks on agentic_loop).
"""
from pathlib import Path


class TestFix14NoAgentHijack:
    def _read_source(self) -> str:
        import app.orchestrator.main_orchestrator as mo
        return Path(mo.__file__).read_text()

    def test_no_hardcoded_agent_type_override_on_onboarding_hint(self):
        """Delegation line `_agent_type = "company_settings"` gated only by
        `if _onboarding_hints_detected:` is REMOVED."""
        src = self._read_source()
        # The exact anti-pattern line must be absent
        anti_pattern = (
            'if _onboarding_hints_detected:\n'
            '                                _agent_type = "company_settings"'
        )
        assert anti_pattern not in src, (
            "FIX 14 REGRESSION: agent_type hijack on onboarding hints is back. "
            "This breaks multi-turn conversations. Onboarding hints should ONLY "
            "be surfaced via _proactive_hints_text in system prompt, never by "
            "overriding agent_type."
        )

    def test_fix14_marker_comment_present(self):
        """Code must carry the FIX 14 marker comment explaining the fix."""
        src = self._read_source()
        assert "FIX 14" in src, (
            "FIX 14 marker missing — file may have been reverted."
        )

    def test_proactive_hints_still_reach_system_prompt(self):
        """The hint-to-prompt path (_proactive_hints_text → extra_instructions)
        must remain intact. This is the legitimate way for hints to reach LIA."""
        src = self._read_source()
        assert "_proactive_hints_text" in src
        assert "extra_instructions=_proactive_hints_text" in src, (
            "Hints are no longer reaching the LLM via extra_instructions. "
            "This means FIX 14 was over-applied — hints must continue flowing "
            "through the prompt so LIA can mention onboarding proactively."
        )

    def test_proactive_hints_payload_still_goes_to_frontend(self):
        """Frontend must still receive hint payload via ctx.extra for rendering."""
        src = self._read_source()
        assert 'ctx.extra["proactive_hints"] = _proactive_hints_payload' in src
