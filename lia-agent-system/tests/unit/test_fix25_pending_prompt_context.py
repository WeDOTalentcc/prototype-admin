"""FIX 25 (2026-04-21) — PendingActionState prompt-context formatter +
enum-aware param extraction.

Closes chat gap: when LIA asked "qual motivo do fechamento?" and user said
"orçamento", the LLM lost context that "orçamento" was the reason slot value
(and asked "qual orçamento?" on the next turn). Two producer-side fixes:

1. PendingActionState.to_prompt_context() — structured block to inject into
   the system prompt on every turn while an action is pending. Makes it
   impossible for the LLM to "forget" what it's collecting.

2. _extract_param_value enum-aware — when the pending param is one with a
   known PT→EN normalizer (close_job.reason), coerce at extraction time so
   collected_params always stores canonical enum values.

Full injection wiring into main_orchestrator system prompt is deferred to
Initiative II (Structured State Machine). FIX 25 ships the formatter +
extraction normalization as the producer-ready building blocks.
"""
from __future__ import annotations

import pytest


def _make_state(**overrides):
    """Helper to build a PendingActionState with sensible defaults."""
    from app.orchestrator.pending_action import PendingActionState

    defaults = dict(
        pending_id="pid-1",
        intent="cancelar_vaga",
        action_id="close_job",
        domain_id="job_management",
        collected_params={"job_id": "v0040"},
        missing_params=["reason"],
        conversation_id="conv-1",
        company_id="co-1",
    )
    defaults.update(overrides)
    return PendingActionState(**defaults)


def test_to_prompt_context_returns_structured_block() -> None:
    """FIX 25: PendingActionState must format itself for system-prompt injection."""
    state = _make_state()
    assert hasattr(state, "to_prompt_context"), (
        "FIX 25: PendingActionState must expose to_prompt_context() method"
    )
    block = state.to_prompt_context()
    assert isinstance(block, str)

    # Key structural elements the LLM needs to continue collection
    low = block.lower()
    assert "close_job" in low or "cancelar_vaga" in low, (
        "FIX 25: block must identify the pending action"
    )
    assert "job_id" in low and "v0040" in low, (
        "FIX 25: block must list already-collected params so LLM knows what not to reask"
    )
    assert "reason" in low, (
        "FIX 25: block must list missing params so LLM knows what to ask for"
    )


def test_to_prompt_context_empty_when_no_state_is_safe() -> None:
    """FIX 25: must not crash on minimal state."""
    state = _make_state(collected_params={}, missing_params=[])
    block = state.to_prompt_context()
    assert isinstance(block, str)
    assert len(block) > 0


def test_extract_param_value_coerces_close_reason_synonyms() -> None:
    """FIX 25: when extracting `reason` param, PT synonyms must coerce to enum."""
    import asyncio

    from app.orchestrator.main_orchestrator import _extract_param_value

    async def _run():
        return await _extract_param_value("orçamento", "reason", [])

    result = asyncio.run(_run())
    assert result == "budget", (
        f"FIX 25: _extract_param_value('orçamento', 'reason') should coerce to "
        f"'budget' (via FIX 22 normalizer). Got {result!r}. Without this, "
        f"collected_params stores raw 'orçamento' and downstream tools see "
        f"the unnormalized value."
    )


def test_extract_param_value_passthrough_for_unknown_param() -> None:
    """FIX 25 regression: non-enum params still return raw message."""
    import asyncio

    from app.orchestrator.main_orchestrator import _extract_param_value

    async def _run():
        return await _extract_param_value("Desenvolvedor Backend", "job_title", [])

    result = asyncio.run(_run())
    assert result == "Desenvolvedor Backend", (
        "FIX 25: params without enum normalizer must pass through raw"
    )


def test_fix25_marker_in_pending_action() -> None:
    """FIX 25 audit marker in pending_action.py."""
    from pathlib import Path

    import app.orchestrator.pending_action as pa

    source = Path(pa.__file__).read_text(encoding="utf-8")
    assert "FIX 25" in source, (
        "FIX 25: pending_action.py must contain FIX 25 marker"
    )
    assert "to_prompt_context" in source


def test_fix25_marker_in_main_orchestrator() -> None:
    """FIX 25 audit marker in main_orchestrator.py for the enum-aware extract."""
    from pathlib import Path

    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "FIX 25" in source, (
        "FIX 25: main_orchestrator.py must contain FIX 25 marker"
    )
