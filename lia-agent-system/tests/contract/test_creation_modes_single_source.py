"""Anti-drift sentinel for the job creation-modes capability (ADR-008).

LIA must give ONE truthful answer to "consegue criar uma vaga a partir de uma
existente / de um template / do zero?". This sentinel fails the build if:

  - the registry-derived view stops reporting any of the three modes;
  - SystemPromptBuilder or WizardOrchestrator stop sourcing the shared block;
  - a chat surface reintroduces a hardcoded "Modos de criação" list that could
    diverge from the registries.
"""
from __future__ import annotations

import pathlib

import pytest

from app.shared.capabilities import (
    answer_can_create_question,
    get_creation_modes,
    render_creation_modes_block,
)
from app.shared.capabilities.job_creation_capabilities import CREATION_MODES_HEADING

_EXPECTED_KEYS = {"scratch", "template", "existing"}


def test_all_three_modes_available_against_current_registries():
    modes = {m.key: m for m in get_creation_modes()}
    assert set(modes) == _EXPECTED_KEYS
    for key in _EXPECTED_KEYS:
        assert modes[key].available, f"creation mode '{key}' must be available"
        # provenance: each available mode must be backed by a real registry intent
        assert modes[key].backed_by, f"mode '{key}' has no registry provenance"


def test_render_block_lists_all_three_modes():
    block = render_creation_modes_block()
    assert CREATION_MODES_HEADING in block
    for label_token in ("do zero", "template", "existente"):
        assert label_token.lower() in block.lower()


def test_system_prompt_builder_surfaces_creation_modes():
    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert CREATION_MODES_HEADING in prompt


def test_wizard_orchestrator_surfaces_creation_modes():
    from app.domains.job_creation.orchestrator.wizard_orchestrator import (
        WizardOrchestrator,
    )

    orch = WizardOrchestrator()
    prompt = orch._build_system_prompt({})
    assert CREATION_MODES_HEADING in prompt
    # the wizard must not omit any mode (the original bug: only knew "do zero")
    for label_token in ("template", "existente"):
        assert label_token.lower() in prompt.lower()


@pytest.mark.parametrize(
    "text",
    [
        "consegue criar uma vaga a partir de uma existente?",
        "dá pra criar uma vaga a partir de um template?",
        "você consegue criar uma vaga do zero?",
        "consegue criar uma vaga?",
        "consigo duplicar uma vaga?",
        "tem como clonar uma vaga?",
    ],
)
def test_answer_can_create_question_is_affirmative(text):
    ans = answer_can_create_question(text)
    assert ans.is_capability_question, text
    assert ans.matched_modes, text
    assert ans.answer.lower().startswith("sim"), text


@pytest.mark.parametrize(
    "text",
    [
        "qual o status do funil?",
        "manda um email pro joão",
        "bom dia",
    ],
)
def test_non_create_questions_are_ignored(text):
    ans = answer_can_create_question(text)
    assert not ans.is_capability_question, text


def test_no_divergent_hardcoded_creation_mode_list_in_chat_surfaces():
    """No chat-reachable prompt may hardcode the canonical heading except via
    the shared view (provenance) or this sentinel itself."""
    root = pathlib.Path(__file__).resolve().parents[1].parent  # lia-agent-system/
    app_dir = root / "app"
    allowed = {
        app_dir / "shared" / "capabilities" / "job_creation_capabilities.py",
    }
    offenders: list[str] = []
    for py in app_dir.rglob("*.py"):
        if py in allowed:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        if CREATION_MODES_HEADING in text:
            offenders.append(str(py.relative_to(root)))
    assert not offenders, (
        "Hardcoded creation-modes heading found outside the shared view "
        f"(use render_creation_modes_block instead): {offenders}"
    )
