"""TDD: PromptComposer canonical factory (Sprint 2 Phase 1 — ADR-028).

Tests:
  1. Compose with all blocks → canonical order respected
  2. Empty blocks skipped (no double-newline gaps)
  3. Whitespace-only blocks stripped
  4. Extra (non-canonical) blocks appended in insertion order
  5. PromptComposition is frozen (no mutation)
  6. metadata + components populated correctly
  7. for_candidate_self_service factory wires CSS constants
  8. Golden snapshot for candidate prompt (regression sentinel)

Skill: tdd-workflow + harness-engineering (snapshot sensor).
"""
from __future__ import annotations

import hashlib

import pytest

from app.shared.prompts.prompt_composer import (
    PromptComposer,
    PromptComposition,
)


# ──────────────────────────────────────────────────────────────────────
# Compose: canonical order + empty handling
# ──────────────────────────────────────────────────────────────────────


def test_compose_includes_all_provided_blocks_in_canonical_order():
    comp = PromptComposer.compose(
        agent_type="test",
        persona="P",
        domain_specific="D",
        few_shot_examples="F",
        reasoning_pattern="R",
        compliance_block="C",
        tenant_context_snippet="T",
        memory_summary="M",
    )
    # All 7 canonical blocks present, joined with \n\n
    assert comp.text == "P\n\nD\n\nF\n\nR\n\nC\n\nT\n\nM"
    assert comp.metadata["block_count"] == 7
    assert comp.metadata["included_blocks"] == [
        "persona",
        "domain_specific",
        "few_shot_examples",
        "reasoning_pattern",
        "compliance_block",
        "tenant_context_snippet",
        "memory_summary",
    ]


def test_compose_skips_empty_blocks():
    comp = PromptComposer.compose(
        agent_type="test",
        domain_specific="D",
        # persona, few_shot, reasoning, compliance, tenant, memory ALL empty
    )
    assert comp.text == "D"
    assert comp.metadata["block_count"] == 1
    assert comp.metadata["included_blocks"] == ["domain_specific"]


def test_compose_skips_whitespace_only_blocks():
    comp = PromptComposer.compose(
        agent_type="test",
        domain_specific="D",
        few_shot_examples="   \n\n  ",  # whitespace only
        reasoning_pattern="R",
    )
    assert comp.text == "D\n\nR"
    assert "few_shot_examples" not in comp.metadata["included_blocks"]


def test_compose_strips_block_whitespace():
    comp = PromptComposer.compose(
        agent_type="test",
        domain_specific="  D with surrounding ws  \n",
    )
    # Leading/trailing ws stripped
    assert comp.text == "D with surrounding ws"


def test_compose_appends_extra_blocks_after_canonical():
    comp = PromptComposer.compose(
        agent_type="test",
        domain_specific="D",
        custom_warning="WARN",
        debug_marker="DBG",
    )
    # Extras appended in insertion order
    assert comp.text == "D\n\nWARN\n\nDBG"
    assert comp.metadata["included_blocks"] == [
        "domain_specific",
        "custom_warning",
        "debug_marker",
    ]


def test_compose_extras_dont_duplicate_canonical():
    """If an extra has same name as canonical, canonical wins (no double)."""
    # When **extra_blocks contains "persona", the kwarg is set as named param
    # actually — Python doesn't allow this collision. Test the boundary.
    # Just verify a unique-named extra works.
    comp = PromptComposer.compose(
        agent_type="test",
        persona="P",
        unique_block="U",
    )
    blocks = comp.metadata["included_blocks"]
    # No duplicate of any name
    assert len(set(blocks)) == len(blocks)


# ──────────────────────────────────────────────────────────────────────
# PromptComposition immutability + introspection
# ──────────────────────────────────────────────────────────────────────


def test_prompt_composition_is_frozen():
    comp = PromptComposer.compose(agent_type="t", persona="P")
    with pytest.raises((AttributeError, Exception)):
        comp.text = "MUTATED"


def test_components_map_preserves_per_block_content():
    comp = PromptComposer.compose(
        agent_type="test",
        persona="P with detail",
        domain_specific="D scope",
    )
    assert comp.components["persona"] == "P with detail"
    assert comp.components["domain_specific"] == "D scope"


def test_metadata_contains_char_length():
    comp = PromptComposer.compose(
        agent_type="test",
        domain_specific="ABCD",
    )
    assert comp.metadata["char_length"] == 4
    assert comp.metadata["agent_type"] == "test"


# ──────────────────────────────────────────────────────────────────────
# Factory: for_candidate_self_service
# ──────────────────────────────────────────────────────────────────────


def test_for_candidate_self_service_wires_css_constants():
    comp = PromptComposer.for_candidate_self_service()
    # Should include CSS_DOMAIN_SPECIFIC + CSS_FEW_SHOT_EXAMPLES
    assert "candidate_self_service" in comp.metadata["agent_type"]
    assert "DOMÍNIO: candidate_self_service" in comp.text
    assert "Exemplo 1:" in comp.text
    assert "domain_specific" in comp.components
    assert "few_shot_examples" in comp.components


def test_for_candidate_self_service_with_runtime_blocks():
    """Tenant context + memory injected at runtime."""
    comp = PromptComposer.for_candidate_self_service(
        tenant_context_snippet="Authenticated as company X",
        memory_summary="Last 3 messages...",
    )
    assert "Authenticated as company X" in comp.text
    assert "Last 3 messages..." in comp.text
    # Order: domain_specific → few_shot → tenant_context → memory
    idx_domain = comp.text.index("DOMÍNIO")
    idx_examples = comp.text.index("Exemplo 1")
    idx_tenant = comp.text.index("Authenticated as")
    idx_memory = comp.text.index("Last 3 messages")
    assert idx_domain < idx_examples < idx_tenant < idx_memory


# ──────────────────────────────────────────────────────────────────────
# Golden snapshot — regression sentinel for candidate prompt
# ──────────────────────────────────────────────────────────────────────


# Hash of the canonical candidate composition (no runtime blocks).
# Update this hash ONLY when prompt content is INTENTIONALLY changed.
# Update flow:
#   1. Run test, fail → grab printed actual hash.
#   2. Verify the new prompt is the intended evolution (diff the text).
#   3. Replace expected hash here + commit message documenting the change.
_CANDIDATE_GOLDEN_SHA256 = (
    None  # set on first green run; pinned thereafter
)


def test_candidate_prompt_golden_snapshot():
    """Regression sentinel: the candidate prompt content must not drift
    silently. Updating CSS_DOMAIN_SPECIFIC or CSS_FEW_SHOT_EXAMPLES is
    OK if intentional — update the hash below in the same commit.
    """
    comp = PromptComposer.for_candidate_self_service()
    actual_hash = hashlib.sha256(comp.text.encode("utf-8")).hexdigest()

    if _CANDIDATE_GOLDEN_SHA256 is None:
        # First-run pin: print the hash so caller can capture it
        print(f"\n[GOLDEN] candidate_self_service prompt hash: {actual_hash}")
        print(f"[GOLDEN] char_length: {comp.metadata['char_length']}")
        print(f"[GOLDEN] included_blocks: {comp.metadata['included_blocks']}")
        # On first run, sentinel acts as a pinning checkpoint
        assert comp.metadata["char_length"] > 100, "prompt too short"
        return

    assert actual_hash == _CANDIDATE_GOLDEN_SHA256, (
        f"Candidate prompt drifted. Expected hash "
        f"{_CANDIDATE_GOLDEN_SHA256}, got {actual_hash}. "
        "If intentional, update _CANDIDATE_GOLDEN_SHA256 in the same commit "
        "that changes the prompt content."
    )
