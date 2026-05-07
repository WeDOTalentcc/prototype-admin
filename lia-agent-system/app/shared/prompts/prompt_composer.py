"""Canonical PromptComposer factory (ADR-028 — Sprint 2 Phase 1).

Single source of truth for assembling LLM system prompts. Replaces
hand-rolled `DOMAIN_INSTRUCTIONS` class-attrs (15 react agents) and
documents the canonical block ordering.

Sprint 2 Phase 1 (this file): minimal API + 1 agent migration
(candidate_self_service — smallest, low blast radius).

Sprint 2 Phase 2+ (planned): converge `SystemPromptBuilder` (264 LOC,
28 importers) and `ComplianceDomainPrompt` (704 LOC, 19 subclasses)
into this composer; migrate remaining 16 agents; golden-prompt
snapshots per agent_type.

Block ordering convention (canonical):
    1. persona (who LIA is)
    2. domain_specific (this agent's scope/proibições)
    3. few_shot_examples (canonical Q/A — optional)
    4. reasoning_pattern (ReAct loop — optional)
    5. compliance_block (LGPD/SOX guards — optional)
    6. tenant_context_snippet (auth/company info — optional, runtime)
    7. memory_summary (last N messages — optional, runtime)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_BLOCK_SEPARATOR = "\n\n"

# Canonical block order — Sprint 2 Phase 1
_CANONICAL_ORDER = (
    "persona",
    "domain_specific",
    "few_shot_examples",
    "reasoning_pattern",
    "compliance_block",
    "tenant_context_snippet",
    "memory_summary",
)


@dataclass(frozen=True, slots=True)
class PromptComposition:
    """Result of composing a system prompt.

    Frozen — callers cannot mutate. Build a new composition via
    PromptComposer.compose() to override.

    Fields:
        text: assembled prompt string (joined with double-newline)
        components: dict[block_name -> block_content] — preserves
            input for snapshot diff + introspection
        metadata: dict for sensor / audit purposes (agent_type,
            included_blocks, etc.)
    """

    text: str
    components: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptComposer:
    """Single canonical entrypoint for system prompt assembly (ADR-028).

    Usage:
        comp = PromptComposer.compose(
            agent_type="candidate_self_service",
            persona=PERSONA_TEXT,
            domain_specific=CSS_DOMAIN_SPECIFIC,
            few_shot_examples=CSS_FEW_SHOT_EXAMPLES,
        )
        # Use the assembled prompt
        agent.system_prompt = comp.text

    Block ordering follows _CANONICAL_ORDER. Empty blocks are skipped
    (no leading/trailing newlines). Caller-supplied blocks not in the
    canonical order are appended in insertion order at the end (preserves
    extensibility).
    """

    @staticmethod
    def compose(
        *,
        agent_type: str,
        persona: str = "",
        domain_specific: str = "",
        few_shot_examples: str = "",
        reasoning_pattern: str = "",
        compliance_block: str = "",
        tenant_context_snippet: str = "",
        memory_summary: str = "",
        **extra_blocks: str,
    ) -> PromptComposition:
        """Assemble a system prompt from named blocks.

        Args:
            agent_type: identifier for sensor/audit metadata.
            persona: who LIA is (top-level).
            domain_specific: scope + proibições for this agent.
            few_shot_examples: canonical Q/A (optional).
            reasoning_pattern: ReAct loop instructions (optional).
            compliance_block: LGPD/SOX guards (optional).
            tenant_context_snippet: runtime tenant info (optional).
            memory_summary: last N messages (optional, runtime).
            **extra_blocks: arbitrary additional blocks; appended in
                insertion order at the end (after canonical blocks).

        Returns:
            PromptComposition with assembled `text` + per-block
            `components` map + `metadata` for introspection.
        """
        all_blocks = {
            "persona": persona,
            "domain_specific": domain_specific,
            "few_shot_examples": few_shot_examples,
            "reasoning_pattern": reasoning_pattern,
            "compliance_block": compliance_block,
            "tenant_context_snippet": tenant_context_snippet,
            "memory_summary": memory_summary,
            **extra_blocks,
        }

        included: list[tuple[str, str]] = []
        # Canonical order first
        for name in _CANONICAL_ORDER:
            value = all_blocks.get(name, "")
            if value and value.strip():
                included.append((name, value.strip()))
        # Extras after, preserving insertion order
        for name, value in extra_blocks.items():
            if name in _CANONICAL_ORDER:
                continue  # already handled
            if value and value.strip():
                included.append((name, value.strip()))

        text = _BLOCK_SEPARATOR.join(content for _, content in included)
        components = {name: content for name, content in included}
        metadata = {
            "agent_type": agent_type,
            "included_blocks": [name for name, _ in included],
            "block_count": len(included),
            "char_length": len(text),
        }

        return PromptComposition(
            text=text,
            components=components,
            metadata=metadata,
        )

    @staticmethod
    def for_candidate_self_service(
        *,
        tenant_context_snippet: str = "",
        memory_summary: str = "",
    ) -> PromptComposition:
        """Sprint 2 Phase 1: canonical composer for candidate_self_service."""
        from app.domains.candidate_self_service.agents.candidate_system_prompt import (
            CSS_DOMAIN_SPECIFIC,
            CSS_FEW_SHOT_EXAMPLES,
        )

        return PromptComposer.compose(
            agent_type="candidate_self_service",
            domain_specific=CSS_DOMAIN_SPECIFIC,
            few_shot_examples=CSS_FEW_SHOT_EXAMPLES,
            tenant_context_snippet=tenant_context_snippet,
            memory_summary=memory_summary,
        )

    @staticmethod
    def for_domain(
        agent_type: str,
        *,
        domain_specific: str = "",
        few_shot_examples: str = "",
        reasoning_pattern: str = "",
        tenant_context_snippet: str = "",
        memory_summary: str = "",
    ) -> PromptComposition:
        """Sprint 2 Phase 2: generic factory for any domain agent.

        Caller pre-formats `reasoning_pattern` (e.g. by calling
        `.format(memory_summary='', stage_context='')` on the
        `*_REASONING_PROMPT` template). This preserves the legacy
        empty-placeholder behavior (see Audit G defect note —
        future Phase 3 fixes by binding placeholders at runtime).

        Args:
            agent_type: identifier for sensor/audit metadata.
            domain_specific: the agent's `*_DOMAIN_SPECIFIC` constant.
            few_shot_examples: the agent's `*_FEW_SHOT_EXAMPLES` constant
                (empty if none).
            reasoning_pattern: pre-formatted REASONING_PROMPT (empty if
                none).
            tenant_context_snippet: runtime tenant info.
            memory_summary: runtime conversation memory.

        Returns:
            PromptComposition with canonical block ordering applied.
        """
        return PromptComposer.compose(
            agent_type=agent_type,
            domain_specific=domain_specific,
            few_shot_examples=few_shot_examples,
            reasoning_pattern=reasoning_pattern,
            tenant_context_snippet=tenant_context_snippet,
            memory_summary=memory_summary,
        )
