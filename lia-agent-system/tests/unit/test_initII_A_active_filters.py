"""Initiative II.A (2026-04-21) — active_filters + pending_action injection
into SystemPromptBuilder memory block.

Closes state-management gap: ConversationState.active_filters is populated by
workflow.py:266 but never rendered into the system prompt. Consequence:
  Turn 1: 'quantas vagas abertas' → LLM filters status=Ativa → 0 results
  Turn 2: 'liste todas' → LLM has no memory of previous filter → 20 results

Canonical-fix (producer-side): SystemPromptBuilder.build() enriches the
'Memória da Conversa' block with active_filters when present, and a new
'Ação Pendente' block when PendingActionState is in flight.

Tests structural — render + format. Runtime validation via smoke test.
"""
from __future__ import annotations


def test_active_filters_rendered_when_present() -> None:
    """II.A: build() must include active_filters in Memória da Conversa."""
    from app.shared.memory.conversation_state import ConversationState
    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    state = ConversationState(
        company_id="co-1",
        active_filters={"status": "Ativa", "department": "Engenharia"},
    )
    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-1",
        conversation_state=state,
    )
    assert "Filtros ativos" in prompt or "filtros ativos" in prompt, (
        "II.A: build() must render active_filters in memory block"
    )
    assert "Ativa" in prompt and "Engenharia" in prompt, (
        "II.A: filter values must appear in rendered block"
    )


def test_active_filters_empty_does_not_add_empty_block() -> None:
    """II.A regression: empty filters must not add empty section."""
    from app.shared.memory.conversation_state import ConversationState
    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    state = ConversationState(company_id="co-1", active_filters={})
    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-1",
        conversation_state=state,
    )
    assert "Filtros ativos:" not in prompt and "Filtros ativos\n" not in prompt


def test_pending_action_rendered_when_passed() -> None:
    """II.A: build() must render pending_action when caller passes it."""
    from app.orchestrator.pending_action import PendingActionState
    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    pending = PendingActionState(
        pending_id="pid-A",
        intent="cancelar_vaga",
        action_id="close_job",
        domain_id="job_management",
        collected_params={"job_id": "v0040"},
        missing_params=["reason"],
        conversation_id="c1",
        company_id="co-1",
    )
    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-1",
        pending_action=pending,
    )
    assert "Ação Pendente" in prompt or "pending" in prompt.lower(), (
        "II.A: build() must emit an Ação Pendente section when pending_action passed"
    )
    assert "close_job" in prompt and "v0040" in prompt, (
        "II.A: pending_action block must include action_id + collected params"
    )
    assert "reason" in prompt.lower(), (
        "II.A: pending_action block must list missing params"
    )


def test_pending_action_none_does_not_add_block() -> None:
    """II.A regression: no pending_action → no section."""
    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-1",
    )
    assert "Ação Pendente" not in prompt, (
        "II.A: must not render Ação Pendente section when pending_action is None"
    )


def test_initII_A_marker_in_builder() -> None:
    """II.A audit marker for traceability."""
    from pathlib import Path

    import app.shared.prompts.system_prompt_builder as spb

    source = Path(spb.__file__).read_text(encoding="utf-8")
    assert "Initiative II.A" in source or "II.A" in source, (
        "II.A: system_prompt_builder.py must contain II.A marker"
    )


def test_build_signature_accepts_pending_action_kwarg() -> None:
    """II.A: build() signature must accept pending_action kwarg."""
    import inspect

    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    sig = inspect.signature(SystemPromptBuilder.build)
    assert "pending_action" in sig.parameters, (
        "II.A: SystemPromptBuilder.build must accept pending_action kwarg"
    )
    assert sig.parameters["pending_action"].default is None, (
        "II.A: pending_action default must be None (backward compat)"
    )
