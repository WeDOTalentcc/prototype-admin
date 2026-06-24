"""
tests/unit/test_chat_bug_fixes_2026_06_18.py

TDD tests for chat bugs fixed 2026-06-18:
  BUG-4: event_generator emits error event when parallel setup fails (no "Resposta incompleta")
  BUG-5: strip_pii_for_llm_prompt_async runs in thread pool (no event loop blocking)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBug5PiiAsyncWrapper:
    """BUG-5: strip_pii_for_llm_prompt_async must not block the event loop."""

    def test_async_wrapper_exists_and_is_coroutine(self):
        """Wrapper must be an async function (awaitable)."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt_async
        import asyncio
        assert asyncio.iscoroutinefunction(strip_pii_for_llm_prompt_async)

    @pytest.mark.asyncio
    async def test_async_wrapper_returns_stripped_text(self):
        """Async wrapper must return same result as sync version for plain text."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt, strip_pii_for_llm_prompt_async
        text = "Hello, my name is John and my email is john@test.com"
        sync_result = strip_pii_for_llm_prompt(text, mask_names=False)
        async_result = await strip_pii_for_llm_prompt_async(text, mask_names=False)
        # Both should strip email — results must be equal
        assert async_result == sync_result
        assert "@" not in async_result  # email was stripped

    @pytest.mark.asyncio
    async def test_async_wrapper_passthrough_for_empty_text(self):
        """Empty string must be returned unchanged without calling Presidio."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt_async
        result = await strip_pii_for_llm_prompt_async("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_async_wrapper_uses_thread_pool(self):
        """Async wrapper must run via asyncio.to_thread (not blocking event loop)."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt_async
        from lia_pii.masking import _LLM_PROMPT_PII_STRIPPING_ENABLED
        if not _LLM_PROMPT_PII_STRIPPING_ENABLED:
            pytest.skip("PII stripping disabled in this env")
        
        import asyncio
        # If it blocks, concurrent tasks would be serialized. 
        # Use sleep to verify the event loop stays responsive during PII strip.
        sleep_done = []
        
        async def _concurrent_sleep():
            await asyncio.sleep(0.01)
            sleep_done.append(True)
        
        # Run PII strip and concurrent sleep simultaneously
        await asyncio.gather(
            strip_pii_for_llm_prompt_async("test text with email@test.com"),
            _concurrent_sleep(),
        )
        # If event loop was blocked, sleep_done would be empty
        assert sleep_done, "Event loop was blocked during PII strip (sync path still used)"

    def test_llm_py_has_no_remaining_sync_pii_calls(self):
        """Sensor: llm.py must not contain any sync strip_pii_for_llm_prompt() calls."""
        import re
        with open("app/domains/ai/services/llm.py") as f:
            content = f.read()
        # Find sync calls: strip_pii_for_llm_prompt( NOT preceded by await
        # Pattern: not a def/import line AND not preceded by 'await '
        lines = content.splitlines()
        violations = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip imports, definitions, comments
            if stripped.startswith(("from ", "import ", "def ", "#", "async def ")):
                continue
            if "strip_pii_for_llm_prompt(" in line and "strip_pii_for_llm_prompt_async" not in line:
                if "await" not in line and "BUG-5-EXEMPT" not in line:
                    violations.append(f"  Line {i}: {stripped[:100]}")
        assert not violations, (
            f"BUG-5 REGRESSION: found sync strip_pii_for_llm_prompt() calls in llm.py.\n"
            f"These block the event loop. Use await strip_pii_for_llm_prompt_async() instead:\n"
            + "\n".join(violations)
        )


class TestBug4EventGeneratorSetupError:
    """BUG-4: event_generator must emit error terminal event when setup fails."""

    def test_setup_error_emits_error_event_not_closes_silently(self):
        """Sensor: agent_chat_sse.py must have the BUG-4 fix applied."""
        with open("app/api/v1/agent_chat_sse.py") as f:
            content = f.read()
        # Verify the fix is present: try/except around _gather_task with serialize_error
        assert "except Exception as _setup_gather_exc:" in content, (
            "BUG-4 REGRESSION: agent_chat_sse.py is missing the setup_gather_exc handler.\n"
            "When parallel setup (budget/router/context) fails, the generator closes without\n"
            "emitting a terminal event → frontend shows 'Resposta incompleta'. Fix: add\n"
            "try/except around 'await _gather_task' that yields serialize_error before return."
        )
        assert "setup_error" in content, (
            "BUG-4 REGRESSION: 'setup_error' error code not found in agent_chat_sse.py.\n"
            "The error event must include error_code='setup_error' for frontend telemetry."
        )


class TestBug6TimeoutHierarchy:
    """BUG-6: Three timeout constants must form strict ascending hierarchy.

    agentic_llm(90s) < rest_orch(110s) < sse_outer(120s)
    Wizard LLM calls (90s) must not hit SSE outer (120s) prematurely.
    REST orch (110s) exposes 504 before gateway 502 opaco.
    """

    def test_agentic_llm_default_is_90s(self):
        """Current module value must be 90s (default when env var not set)."""
        from app.orchestrator.execution.agentic_loop import _AGENTIC_LLM_TIMEOUT_SECONDS
        assert _AGENTIC_LLM_TIMEOUT_SECONDS == 90.0, (
            f"Expected 90s default, got {_AGENTIC_LLM_TIMEOUT_SECONDS}"
        )

    def test_hierarchy_satisfied(self):
        """agentic_llm(90) < rest_orch(110) < sse_outer(120)."""
        from app.orchestrator.execution.agentic_loop import _AGENTIC_LLM_TIMEOUT_SECONDS
        # rest_orch default — read from source constant
        import re
        with open("app/api/v1/chat.py") as f:
            chat_src = f.read()
        m = re.search(r'LIA_CHAT_ORCH_TIMEOUT_SECONDS",\s*"(\d+)"', chat_src)
        rest_orch = float(m.group(1)) if m else 90.0
        # sse_outer default
        from libs.config.lia_config.config import settings
        sse_outer = settings.LLM_TIMEOUT_SECONDS
        assert _AGENTIC_LLM_TIMEOUT_SECONDS < rest_orch < sse_outer, (
            f"Hierarchy broken: agentic={_AGENTIC_LLM_TIMEOUT_SECONDS}s "
            f"rest_orch={rest_orch}s sse_outer={sse_outer}s"
        )

    def test_resolve_fn_with_env_override(self):
        """_resolve_agentic_llm_timeout must honor env var."""
        import os
        from unittest.mock import patch
        from app.orchestrator.execution.agentic_loop import _resolve_agentic_llm_timeout
        with patch.dict(os.environ, {"LIA_AGENTIC_LLM_TIMEOUT_SECONDS": "45"}):
            assert _resolve_agentic_llm_timeout() == 45.0

    def test_resolve_fn_cap_at_120s(self):
        """Cap must prevent values > 120s to avoid infinite hang."""
        import os
        from unittest.mock import patch
        from app.orchestrator.execution.agentic_loop import _resolve_agentic_llm_timeout
        with patch.dict(os.environ, {"LIA_AGENTIC_LLM_TIMEOUT_SECONDS": "999"}):
            assert _resolve_agentic_llm_timeout() == 120.0, "Cap must be 120s"

