"""Onda 2.5 Init II.D — workflow_context + registry + persona injection."""
from __future__ import annotations


def test_conversation_state_has_workflow_context_field() -> None:
    """II.D: ConversationState exposes workflow_context slot."""
    from app.shared.memory.conversation_state import ConversationState

    cs = ConversationState(company_id="co-test")
    assert hasattr(cs, "workflow_context")
    assert cs.workflow_context is None  # default

    cs2 = ConversationState(
        company_id="co-test",
        workflow_context={"workflow_id": "close_job", "step": "ask_reason"},
    )
    assert cs2.workflow_context is not None
    assert cs2.workflow_context["workflow_id"] == "close_job"


def test_conversation_state_round_trip_via_dict() -> None:
    """II.D: to_dict + from_dict preserves workflow_context."""
    from app.shared.memory.conversation_state import ConversationState

    wf = {"workflow_id": "sourcing_with_filters", "step": "apply_filter", "data": {"skill": "python"}}
    cs = ConversationState(company_id="co-test", workflow_context=wf)

    d = cs.to_dict()
    assert d["workflow_context"] == wf

    cs2 = ConversationState.from_dict(d)
    assert cs2.workflow_context == wf


def test_workflow_registry_has_3_v1_workflows() -> None:
    """II.D: registry ships with close_job, sourcing_with_filters, job_creation_wizard."""
    from app.orchestrator.workflow_registry import list_workflows

    ids = list_workflows()
    for expected in ["close_job", "sourcing_with_filters", "job_creation_wizard"]:
        assert expected in ids, f"II.D: workflow {expected!r} must be registered"


def test_workflow_definition_has_steps() -> None:
    """II.D: each v1 workflow has ordered steps + terminal."""
    from app.orchestrator.workflow_registry import get_workflow

    wf = get_workflow("close_job")
    assert wf is not None
    assert len(wf.steps) >= 3
    assert len(wf.terminal_steps) >= 1


def test_start_workflow_creates_context() -> None:
    """II.D: start_workflow returns properly shaped context dict."""
    from app.orchestrator.workflow_registry import start_workflow

    ctx = start_workflow("close_job", initial_data={"job_id": "v0040"})
    assert ctx is not None
    assert ctx["workflow_id"] == "close_job"
    assert ctx["step"] in {"ask_reason", "collect_role", "initial_search"}  # first step
    assert ctx["data"]["job_id"] == "v0040"
    assert "started_at" in ctx


def test_start_workflow_unknown_returns_none() -> None:
    """II.D: unknown workflow_id returns None (not raise)."""
    from app.orchestrator.workflow_registry import start_workflow

    assert start_workflow("nonexistent_flow") is None


def test_advance_step() -> None:
    """II.D: advance_step moves to next step in sequence."""
    from app.orchestrator.workflow_registry import advance_step, start_workflow

    ctx = start_workflow("close_job")
    original_step = ctx["step"]
    advanced = advance_step(ctx, new_data={"reason": "budget"})
    assert advanced["step"] != original_step
    assert advanced["data"]["reason"] == "budget"


def test_is_complete_terminal_step() -> None:
    """II.D: is_complete true only at terminal step."""
    from app.orchestrator.workflow_registry import is_complete

    assert is_complete({"workflow_id": "close_job", "step": "notified"}) is True
    assert is_complete({"workflow_id": "close_job", "step": "ask_reason"}) is False
    assert is_complete(None) is True  # no workflow = "complete"


def test_render_prompt_context_produces_section() -> None:
    """II.D: render_prompt_context emits a '## Fluxo em Andamento' section."""
    from app.orchestrator.workflow_registry import render_prompt_context

    ctx = {
        "workflow_id": "close_job",
        "step": "confirm",
        "data": {"job_id": "v0040", "reason": "budget"},
    }
    block = render_prompt_context(ctx)
    assert "Fluxo em Andamento" in block
    assert "close_job" in block.lower() or "encerrar" in block.lower()
    assert "confirm" in block


def test_render_empty_context_returns_empty() -> None:
    """II.D: empty/None context → empty render (safe)."""
    from app.orchestrator.workflow_registry import render_prompt_context

    assert render_prompt_context(None) == ""
    assert render_prompt_context({}) == ""


def test_feature_flag_off_disables_workflows() -> None:
    """II.D: LIA_WORKFLOW_CONTEXT_ENABLED=false → start_workflow returns None."""
    import app.orchestrator.workflow_registry as mod

    original = mod._WORKFLOW_CONTEXT_ENABLED
    try:
        mod._WORKFLOW_CONTEXT_ENABLED = False
        assert mod.start_workflow("close_job") is None
        assert mod.render_prompt_context({"workflow_id": "close_job", "step": "ask_reason"}) == ""
    finally:
        mod._WORKFLOW_CONTEXT_ENABLED = original


def test_system_prompt_builder_renders_workflow_section_when_active() -> None:
    """II.D end-to-end: SystemPromptBuilder.build() includes '## Fluxo em Andamento'
    when conversation_state has workflow_context."""
    from app.shared.memory.conversation_state import ConversationState
    from app.shared.prompts.system_prompt_builder import (
        SystemPromptBuilder,
        _load_persona_base,
    )
    _load_persona_base.cache_clear()

    cs_active = ConversationState(
        company_id="co-test",
        workflow_context={
            "workflow_id": "close_job",
            "step": "ask_reason",
            "data": {"job_id": "v0040"},
        },
    )
    prompt_active = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
        conversation_state=cs_active,
    )
    assert "Fluxo em Andamento" in prompt_active, (
        "II.D end-to-end: workflow_context should render in system prompt"
    )

    cs_idle = ConversationState(company_id="co-test")
    prompt_idle = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
        conversation_state=cs_idle,
    )
    assert "Fluxo em Andamento" not in prompt_idle, (
        "II.D: idle conversation_state must NOT render workflow section"
    )


def test_initIID_marker_present() -> None:
    """II.D audit marker for traceability."""
    from pathlib import Path

    import app.orchestrator.workflow_registry as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init II.D" in source, "II.D: workflow_registry must contain marker"
    assert "start_workflow" in source and "advance_step" in source
