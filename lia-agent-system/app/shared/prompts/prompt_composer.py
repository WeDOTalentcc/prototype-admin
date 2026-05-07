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

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


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
            compliance_block=PromptComposer.compliance_blocks_for("candidate_self_service"),
            tenant_context_snippet=tenant_context_snippet,
            memory_summary=memory_summary,
        )

    # ── Sprint 2 Phase 3.3 — Compliance YAML loaders ──────────────────────
    # Audit M 2026-05-07: ComplianceDomainPrompt's `get_system_prompt()`
    # was dead code (zero callers in react_agent path). LGPD/fairness/bias/
    # audit YAML content NEVER reached the LLM. This block reactivates that
    # content via PromptComposer's `compliance_block` slot.

    _COMPLIANCE_YAML_CACHE: dict | None = None
    _GUARDRAILS_YAML_CACHE: dict | None = None

    # Variant classification (mirrors ComplianceDomainPrompt._DECISION_DOMAINS,
    # ._COMMUNICATION_DOMAINS — kept in sync).
    _DECISION_DOMAINS = frozenset({
        "pipeline", "pipeline_transition", "cv_screening", "sourcing",
        "autonomous", "talent_pool", "recruiter_assistant", "kanban",
        "talent", "jobs_mgmt",
    })
    _COMMUNICATION_DOMAINS = frozenset({
        "communication", "onboarding",
    })

    @staticmethod
    def _load_compliance_yaml() -> dict:
        """Load compliance_block.yaml (cached after first load)."""
        if PromptComposer._COMPLIANCE_YAML_CACHE is None:
            import os
            try:
                import yaml
                here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                path = os.path.join(here, "..", "prompts", "shared", "compliance_block.yaml")
                with open(os.path.normpath(path)) as f:
                    PromptComposer._COMPLIANCE_YAML_CACHE = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.warning("[PromptComposer] compliance_block.yaml load failed: %s", exc)
                PromptComposer._COMPLIANCE_YAML_CACHE = {}
        return PromptComposer._COMPLIANCE_YAML_CACHE

    @staticmethod
    def _load_guardrails_yaml() -> dict:
        if PromptComposer._GUARDRAILS_YAML_CACHE is None:
            import os
            try:
                import yaml
                here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                path = os.path.join(here, "..", "prompts", "shared", "guardrails_block.yaml")
                with open(os.path.normpath(path)) as f:
                    PromptComposer._GUARDRAILS_YAML_CACHE = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.warning("[PromptComposer] guardrails_block.yaml load failed: %s", exc)
                PromptComposer._GUARDRAILS_YAML_CACHE = {}
        return PromptComposer._GUARDRAILS_YAML_CACHE

    @staticmethod
    def _classify_agent_variant(agent_type: str) -> str:
        """Return 'decision', 'communication', or 'operational' for agent_type.

        Mirrors ComplianceDomainPrompt classification — kept in sync.
        """
        if agent_type in PromptComposer._DECISION_DOMAINS:
            return "decision"
        if agent_type in PromptComposer._COMMUNICATION_DOMAINS:
            return "communication"
        return "operational"

    @staticmethod
    def compliance_blocks_for(agent_type: str) -> str:
        """Sprint 2 Phase 3.3: assemble compliance + guardrails for an agent_type.

        Reactivates the LGPD/fairness/bias/audit YAML content that was
        baked into `ComplianceDomainPrompt.get_system_prompt()` (dead
        code per Audit M 2026-05-07) so it reaches the LLM via
        `PromptComposer.compose(compliance_block=...)`.

        Variant selection (mirror of CDP):
        - "decision" agents (pipeline, cv_screening, sourcing, autonomous,
          talent_pool, recruiter_assistant, kanban, talent, jobs_mgmt):
          full compliance (lgpd + fairness + bias + audit + defensive)
        - "communication" agents (communication, onboarding):
          lgpd + fairness only
        - "operational" agents (wizard, automation, analytics,
          ats_integration, scheduling): lgpd only

        Universal guardrails (identity/hallucination/prompt_security/
        multi_tenancy/negation) appended for ALL agents.

        Returns empty string on YAML load failure (graceful degradation —
        agent still functions, sensor `check_protected_attributes_yaml`
        flags missing YAML at startup).
        """
        compliance = PromptComposer._load_compliance_yaml()
        guardrails = PromptComposer._load_guardrails_yaml()
        variant = PromptComposer._classify_agent_variant(agent_type)
        v_blocks = compliance.get(variant, {})

        parts: list[str] = []
        # Compliance variant blocks
        for key in ("lgpd", "fairness", "bias", "audit"):
            block = v_blocks.get(key, "")
            if block and block.strip():
                parts.append(block.strip())
        defensive = compliance.get("defensive", "")
        if defensive and defensive.strip():
            parts.append(defensive.strip())

        # Universal guardrails (all agents)
        universal = guardrails.get("universal", {})
        for key in ("identity", "hallucination", "prompt_security",
                    "multi_tenancy", "negation"):
            block = universal.get(key, "")
            if block and block.strip():
                parts.append(block.strip())

        # Autonomy variant
        autonomy_variant = guardrails.get("autonomy", {}).get(variant, "")
        if autonomy_variant and autonomy_variant.strip():
            parts.append(autonomy_variant.strip())

        return "\n\n".join(parts)

    @staticmethod
    def for_domain_runtime(
        agent_type: str,
        *,
        domain_specific: str = "",
        few_shot_examples: str = "",
        reasoning_template: str = "",
        memory_summary: str = "",
        stage_context: str = "",
        tenant_context_snippet: str = "",
        memory_summary_fallback: str = "Nenhuma memoria de trabalho disponivel (primeira interacao).",
    ) -> PromptComposition:
        """Sprint 2 Phase 4: compose with REASONING_PROMPT template formatted at runtime.

        Fixes the empty-placeholder defect (Audit G): legacy class-attr
        DOMAIN_INSTRUCTIONS used `REASONING_PROMPT.format(memory_summary="",
        stage_context="")` at class-load time, baking empty values forever.

        This method takes the UNFORMATTED template and runtime values,
        applying `.format()` only when invoked. Agents that override
        `_get_runtime_domain_instructions(input)` should call this.

        Args:
            agent_type: identifier for sensor/audit metadata.
            domain_specific: the agent's `*_DOMAIN_SPECIFIC` constant.
            few_shot_examples: the agent's `*_FEW_SHOT_EXAMPLES` constant.
            reasoning_template: UNFORMATTED `*_REASONING_PROMPT` template
                (with literal `{memory_summary}` and `{stage_context}`
                placeholders).
            memory_summary: runtime memory string (e.g. from
                input.context.get("memory_summary", "")).
            stage_context: runtime stage string.
            memory_summary_fallback: text used when memory_summary is empty
                (matches legacy `get_<domain>_system_prompt` pattern).
            tenant_context_snippet: runtime tenant info.

        Returns:
            PromptComposition with runtime-formatted reasoning block.
        """
        formatted_reasoning = ""
        if reasoning_template:
            try:
                formatted_reasoning = reasoning_template.format(
                    memory_summary=memory_summary or memory_summary_fallback,
                    stage_context=stage_context or "",
                )
            except (KeyError, IndexError) as exc:
                # Template has unexpected placeholders — log + pass through
                import logging
                logging.getLogger(__name__).warning(
                    "[PromptComposer] reasoning_template format failed for %s: %s",
                    agent_type, exc,
                )
                formatted_reasoning = reasoning_template

        return PromptComposer.compose(
            agent_type=agent_type,
            domain_specific=domain_specific,
            few_shot_examples=few_shot_examples,
            reasoning_pattern=formatted_reasoning,
            compliance_block=PromptComposer.compliance_blocks_for(agent_type),
            tenant_context_snippet=tenant_context_snippet,
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
