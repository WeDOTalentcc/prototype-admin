"""Golden-prompt snapshot tests (Sprint 2 Phase 3.1 — ADR-028 cutover prep).

Pins the exact byte-content of system prompts assembled via the 3 paths
(SystemPromptBuilder, PromptComposer, agent._get_system_prompt) so that
Phase 3.2-3.4 convergence cannot silently drift LLM behavior.

Update protocol when intentional change:
  1. Run with `UPDATE_SNAPSHOTS=1 pytest tests/shared/prompts/test_golden_prompts.py`
  2. Inspect git diff of `tests/shared/prompts/snapshots/*.txt` carefully
  3. Confirm new content is the intended evolution
  4. Commit snapshots with message documenting WHY the prompt changed

Includes:
- Identity-leak regression test (P0 — Sprint 2 Phase 3.1):
  candidate prompt MUST NOT contain recruiter persona text.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
UPDATE_MODE = os.environ.get("UPDATE_SNAPSHOTS", "").lower() in ("1", "true", "yes")


def _snapshot_path(name: str) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR / f"{name}.txt"


def _assert_snapshot(name: str, actual: str) -> None:
    """Compare `actual` against stored snapshot. Update if UPDATE_SNAPSHOTS=1."""
    path = _snapshot_path(name)

    if UPDATE_MODE or not path.exists():
        path.write_text(actual, encoding="utf-8")
        if not UPDATE_MODE:
            pytest.skip(
                f"Snapshot pinned (first run): {path.name} — "
                f"verify content + commit. Hash: "
                f"{hashlib.sha256(actual.encode()).hexdigest()[:16]}"
            )
        return

    expected = path.read_text(encoding="utf-8")
    if actual != expected:
        # Show first diff line for fast triage
        diff_line = ""
        for i, (a, e) in enumerate(zip(actual, expected)):
            if a != e:
                diff_line = (
                    f"first diff at char {i}: "
                    f"actual={actual[i:i+30]!r} expected={expected[i:i+30]!r}"
                )
                break
        raise AssertionError(
            f"Golden prompt drift: {path.name}\n"
            f"  expected len={len(expected)} sha={hashlib.sha256(expected.encode()).hexdigest()[:16]}\n"
            f"  actual   len={len(actual)} sha={hashlib.sha256(actual.encode()).hexdigest()[:16]}\n"
            f"  {diff_line}\n\n"
            "If intentional, run: UPDATE_SNAPSHOTS=1 pytest tests/shared/prompts/test_golden_prompts.py\n"
            "Then commit the snapshot diff with message documenting WHY the prompt changed."
        )


# ──────────────────────────────────────────────────────────────────────
# Path B — PromptComposer (Sprint 2 Phase 1+2 canonical)
# ──────────────────────────────────────────────────────────────────────


def test_golden_path_b_candidate_self_service():
    """Pin: PromptComposer.for_candidate_self_service() output."""
    from app.shared.prompts.prompt_composer import PromptComposer
    comp = PromptComposer.for_candidate_self_service()
    _assert_snapshot("path_b__candidate_self_service", comp.text)


def test_golden_path_b_kanban_runtime():
    """Pin: PromptComposer.for_domain_runtime() for kanban (Sprint 2 Phase 4)."""
    from app.domains.recruiter_assistant.agents.kanban_system_prompt import (
        KANBAN_DOMAIN_SPECIFIC,
        KANBAN_FEW_SHOT_EXAMPLES,
        KANBAN_REASONING_PROMPT,
    )
    from app.shared.prompts.prompt_composer import PromptComposer
    comp = PromptComposer.for_domain_runtime(
        agent_type="kanban",
        domain_specific=KANBAN_DOMAIN_SPECIFIC,
        few_shot_examples=KANBAN_FEW_SHOT_EXAMPLES,
        reasoning_template=KANBAN_REASONING_PROMPT,
        memory_summary="GOLDEN_TEST_MEMORY",
        stage_context="GOLDEN_TEST_STAGE",
    )
    _assert_snapshot("path_b__kanban_runtime", comp.text)


def test_golden_path_b_wizard_runtime():
    from app.domains.job_management.agents.wizard_system_prompt import (
        WIZARD_DOMAIN_SPECIFIC,
        WIZARD_REASONING_PROMPT,
    )
    from app.shared.prompts.prompt_composer import PromptComposer
    comp = PromptComposer.for_domain_runtime(
        agent_type="wizard",
        domain_specific=WIZARD_DOMAIN_SPECIFIC,
        reasoning_template=WIZARD_REASONING_PROMPT,
        memory_summary="GOLDEN_TEST_MEMORY",
        stage_context="GOLDEN_TEST_STAGE",
    )
    _assert_snapshot("path_b__wizard_runtime", comp.text)


# ──────────────────────────────────────────────────────────────────────
# Path C — Agent._get_system_prompt full assembly (production runtime)
# ──────────────────────────────────────────────────────────────────────


def _make_input(agent_type: str = "test", **ctx):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="GOLDEN_TEST",
        user_id="u_golden",
        company_id="c_golden",
        session_id="s_golden",
        context=ctx,
    )


def test_golden_path_c_candidate_self_service():
    """Pin candidate FULL prompt (post Phase 3.1 identity-leak fix)."""
    from app.domains.candidate_self_service.agents.candidate_react_agent import (
        CandidateSelfServiceAgent,
    )
    agent = CandidateSelfServiceAgent.__new__(CandidateSelfServiceAgent)
    inp = _make_input()
    prompt = agent._get_system_prompt(inp)
    _assert_snapshot("path_c__candidate_self_service__full", prompt)


# ──────────────────────────────────────────────────────────────────────
# P0 regression sentinels — identity-leak (Phase 3.1)
# ──────────────────────────────────────────────────────────────────────


def test_p0_candidate_does_not_leak_recruiter_persona():
    """P0 sentinel: candidate prompt MUST NOT mention recruiter persona text.

    Audit N 2026-05-07 confirmed SystemPromptBuilder was leaking 12k chars
    of recruiter LIA persona to candidates. Phase 3.1 override fixes via
    `_get_system_prompt` in CandidateSelfServiceAgent. Regression risk:
    a future PR removes the override or re-routes through SPB.
    """
    from app.domains.candidate_self_service.agents.candidate_react_agent import (
        CandidateSelfServiceAgent,
    )
    agent = CandidateSelfServiceAgent.__new__(CandidateSelfServiceAgent)
    inp = _make_input()
    prompt = agent._get_system_prompt(inp)

    # The recruiter persona has these telltale phrases
    forbidden_recruiter_phrases = [
        "recrutadora experiente",
        "recrutadora sênior",
        "head de talent acquisition",
        "15+ anos de experiência",
        "domínio profundo de processos seletivos",
    ]
    leaks = [p for p in forbidden_recruiter_phrases if p in prompt]
    assert not leaks, (
        f"IDENTITY LEAK regression: candidate prompt contains recruiter "
        f"persona text: {leaks!r}. Phase 3.1 P0 fix bypassed."
    )

    # AND must contain candidate-appropriate persona
    assert "para você, candidato" in prompt, (
        "Candidate prompt missing candidate-appropriate persona block. "
        "Verify CandidateSelfServiceAgent._get_system_prompt override is wired."
    )


def test_p0_candidate_prompt_compact():
    """P0: candidate prompt should be compact (no 12k recruiter dump).

    Acceptable range: 1000-5000 chars (post-fix is ~1700; allow some growth
    for legitimate evolution, but flag massive bloat).
    """
    from app.domains.candidate_self_service.agents.candidate_react_agent import (
        CandidateSelfServiceAgent,
    )
    agent = CandidateSelfServiceAgent.__new__(CandidateSelfServiceAgent)
    inp = _make_input()
    prompt = agent._get_system_prompt(inp)
    assert 1000 <= len(prompt) <= 5000, (
        f"Candidate prompt size {len(prompt)} outside expected range "
        f"[1000, 5000]. Investigate — may indicate SPB is re-leaking."
    )
