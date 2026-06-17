"""TDD: Sprint 2 Phase 4 — runtime placeholder substitution (Audit G defect).

Verifies that:
1. PromptComposer.for_domain_runtime() formats {memory_summary} and
   {stage_context} placeholders with runtime values
2. KanbanReActAgent._get_runtime_domain_instructions() substitutes from
   input.context (vs static class-attr with empty placeholders)
3. Fallback to static DOMAIN_INSTRUCTIONS works on error
4. Empty input.context yields fallback memory string ("Nenhuma memoria...")

Skill: tdd-workflow + harness-engineering.
"""
from __future__ import annotations

import pytest

from app.shared.prompts.prompt_composer import PromptComposer


# ──────────────────────────────────────────────────────────────────────
# PromptComposer.for_domain_runtime
# ──────────────────────────────────────────────────────────────────────


def test_for_domain_runtime_substitutes_memory_summary():
    template = "ReAct loop. Memory: {memory_summary}. Stage: {stage_context}."
    comp = PromptComposer.for_domain_runtime(
        agent_type="test",
        reasoning_template=template,
        memory_summary="Last 3 messages: hi, ok, done",
        stage_context="onboarding",
    )
    assert "Memory: Last 3 messages: hi, ok, done" in comp.text
    assert "Stage: onboarding" in comp.text


def test_for_domain_runtime_uses_fallback_when_memory_empty():
    template = "Memory: {memory_summary}. Stage: {stage_context}."
    comp = PromptComposer.for_domain_runtime(
        agent_type="test",
        reasoning_template=template,
        memory_summary="",
        stage_context="x",
    )
    assert "Nenhuma memoria de trabalho" in comp.text
    assert "Stage: x" in comp.text


def test_for_domain_runtime_handles_extra_placeholders_gracefully():
    """If template has UNEXPECTED placeholders, log + pass through (not crash)."""
    template = "Foo: {memory_summary}. Bar: {unknown_placeholder}."
    comp = PromptComposer.for_domain_runtime(
        agent_type="test",
        reasoning_template=template,
        memory_summary="hello",
    )
    # Should NOT crash — fallback returns template as-is or partially formatted
    assert comp.text is not None


def test_for_domain_runtime_combines_all_blocks():
    comp = PromptComposer.for_domain_runtime(
        agent_type="test",
        domain_specific="DOMAIN",
        few_shot_examples="EXAMPLES",
        reasoning_template="Memory: {memory_summary} Stage: {stage_context}",
        memory_summary="MEM",
        stage_context="STAGE",
    )
    # Order: domain_specific → few_shot → reasoning_pattern (formatted)
    idx_domain = comp.text.index("DOMAIN")
    idx_examples = comp.text.index("EXAMPLES")
    idx_reasoning = comp.text.index("Memory: MEM")
    assert idx_domain < idx_examples < idx_reasoning


# ──────────────────────────────────────────────────────────────────────
# KanbanReActAgent — runtime substitution end-to-end
# ──────────────────────────────────────────────────────────────────────


def _make_agent():
    """Construct KanbanReActAgent (skips __init__ heavy setup if possible)."""
    from app.domains.recruiter_assistant.agents.kanban_react_agent import (
        KanbanReActAgent,
    )
    return KanbanReActAgent.__new__(KanbanReActAgent)  # bypass __init__


def _make_input(context: dict | None = None):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="test",
        user_id="u1",
        company_id="c1",
        session_id="s1",
        context=context or {},
    )


def test_kanban_runtime_substitution_with_full_context():
    """Phase 4 contract: input.context with memory + stage → prompt has them."""
    agent = _make_agent()
    inp = _make_input(
        context={
            "memory_summary": "User asked about pipeline yesterday",
            "stage_context": "Triagem CV ativa",
        }
    )
    result = agent._get_runtime_domain_instructions(inp)
    assert "User asked about pipeline yesterday" in result
    assert "Triagem CV ativa" in result


def test_kanban_runtime_substitution_with_empty_context():
    """Empty context → fallback memory string + empty stage."""
    agent = _make_agent()
    inp = _make_input(context={})
    result = agent._get_runtime_domain_instructions(inp)
    # Fallback string should appear since memory_summary was empty
    assert "Nenhuma memoria de trabalho" in result


def test_kanban_runtime_substitution_no_empty_placeholder_baked_in():
    """Phase 4 fix proof: with real context, the prompt should NOT contain
    the literal `{memory_summary}` or `{stage_context}` placeholder."""
    agent = _make_agent()
    inp = _make_input(
        context={
            "memory_summary": "real memory",
            "stage_context": "real stage",
        }
    )
    result = agent._get_runtime_domain_instructions(inp)
    assert "{memory_summary}" not in result
    assert "{stage_context}" not in result


def test_kanban_static_class_attr_still_present_for_backward_compat():
    """Class-attr DOMAIN_INSTRUCTIONS preserved (legacy fallback path)."""
    from app.domains.recruiter_assistant.agents.kanban_react_agent import (
        KanbanReActAgent,
    )
    assert KanbanReActAgent.DOMAIN_INSTRUCTIONS, (
        "Static DOMAIN_INSTRUCTIONS should still exist for fallback"
    )
    # The static version has placeholder bake-in — check the legacy
    # behavior is preserved (even though it's now overridden at runtime)
    assert isinstance(KanbanReActAgent.DOMAIN_INSTRUCTIONS, str)
