# ADR-008 — Capability Single Source of Truth (creation modes)

**Status:** Accepted (2026-06-05)
**Deciders:** Paulo (founder), Task #1322
**Related:** ADR-001 Multi-Agent Architecture, ADR-002 Graph-vs-ReAct,
`replit.md` > Contratos críticos (Wizard de criação de vaga),
`app/shared/prompts/system_prompt_builder.py` (G3/G6 derivation)

## Context

The recruiter chat (LIA) gave **contradictory answers** to the same self-knowledge
question: *"você consegue criar uma vaga a partir de uma existente / de um
template / do zero?"*. Depending on which agent answered, the reply ranged from
"sim, claro" to "não consigo, sou só um assistente de texto".

Root cause is **prompt drift**, not a missing capability. All three creation
modes already exist in the codebase:

| Mode             | Where it lives (registry / service)                                                |
|------------------|------------------------------------------------------------------------------------|
| from scratch     | wizard canônico (`create_job` / `guided_wizard`)                                   |
| from template    | wizard seed (`start_creation_from_source` `source_type=template`) + `job_management` `create_from_template` / `apply_template` |
| from existing    | `job_management` `duplicate_job` / `clone_job` (clone completo via `JobCloneService`) |

But the **claims** about those capabilities were duplicated across surfaces:

- `SystemPromptBuilder` derives a "Capabilities — Ações" block from
  `tool_registry` + `app/tools/categories.py` (G6) — good, but the three
  *creation modes* were never spelled out as a coherent answer.
- `WizardOrchestrator._SYSTEM_PROMPT_BASE` is **hardcoded** and never mentioned
  template/clone, so the wizard "didn't know" it could start from an existing
  vacancy.
- `wizard_meta_question_helper` (LLM) answered "consegue X?" with no grounded
  capability context, so it could hallucinate either way.

Every place that re-states "what LIA can do" is a drift risk: registries say one
thing, prompts say another.

## Decision

Adopt a **single source of truth for capability claims**, derived (read-only)
from the existing registries — **no new hand-maintained registry**.

1. **Aggregated read-only view** —
   `app/shared/capabilities/job_creation_capabilities.py` derives the three job
   creation modes and their *truthful* availability by reading the registries
   that already encode them (`job_management/config/capabilities.yaml`
   intent_keywords, the `app/tools` registry, `app/tools/categories.py`). It is
   tenant-aware (an optional allowed-tool set scopes the modes). It NEVER invents
   a capability: a mode is only reported as available if a real intent/tool backs
   it.

2. **Prompts consume the view** — `SystemPromptBuilder` injects a single
   "Modos de criação de vaga" block (rendered from the view) into its capability
   section, and `WizardOrchestrator` appends the same rendered block to its system
   prompt instead of relying on hardcoded creation claims. One render function,
   one wording, everywhere.

3. **Meta-handler answers from the view** — the "consegue X?" path
   (`wizard_meta_question_helper`) receives the rendered block so the LLM answers
   from grounded truth, and a pure helper `answer_can_create_question(text)`
   exists for deterministic / test use.

4. **Anti-drift sentinel** — a contract test asserts that (a) the view reports
   all three modes as available against the current registries, and (b) both
   `SystemPromptBuilder` and `WizardOrchestrator` surface the registry-derived
   block (no agent hardcodes a divergent "modos de criação" list).

## Consequences

- One truthful answer regardless of which surface (orchestrator, wizard, meta)
  handles the question.
- Adding/removing a creation mode is a registry edit; the prompts and the meta
  answer update automatically; the sentinel fails loudly if a mode is silently
  dropped or a hardcoded list is reintroduced.
- The view is **derivation, not duplication** — it imports from the registries at
  runtime, so it cannot diverge from them by construction.

## Out of scope

- Rewriting the wizard functional flow (15 nodes / 4 HITL gates stay as-is).
- Creating new business capabilities — clone/template/duplicate already exist.
- Wiring `start_creation_from_source` `source_type=vacancy` end-to-end (today it
  honestly offers the template path; the *existing-vacancy* mode is fully served
  by `job_management` `duplicate_job` / `clone_job`). Tracked as a follow-up.
- Plan & Execute behavior — creation is ALWAYS and ONLY the canonical wizard.
