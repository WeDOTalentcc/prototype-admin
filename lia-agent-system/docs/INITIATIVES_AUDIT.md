# Initiatives Audit — Pre-Track 2 Deep Dive

**Date:** 2026-04-21 | **Author:** Agent Audit (canonical-fix + harness-engineering-lia + production-quality)  
**Scope:** 3 Initiatives (I, II, VI) from LIA Maturity Track 2  
**Status:** Ready for user decision

---

## 0. Methodology

Applied skills: canonical-fix, harness-engineering-lia, production-quality.  
Code inspection: Read-only audit of tool registry, conversation state, pending action, LLM cascade, eval infrastructure, CI/CD.

---

## 1. Initiative I — Grounded Capability System

### 1.1 Producer Identification

- **Tool registry** → app/tools/registry.py (190 lines; ToolDefinition with name, description, parameters_schema, governance_tags, related_tools, side_effects)
- **Tool metadata** → app/tools/tool_registry_metadata.yaml (2836 lines; 98 tools registered with full schema)
- **Persona/capability advertisement** → Prose in app/prompts/shared/*.yaml; NO structured capability enumeration
- **Existing glossary** → scripts/generate_tool_action_glossary.py auto-generates JSON from tool_registry_metadata.yaml (good baseline)
- **Capability cards stub** → app/prompts/catalog/ exists but empty

### 1.2 Gap Analysis vs Target

**Target:** Formal YAML catalog (capabilities/*.yaml) with schema {id, title, user_phrasing[], tools[], example_input, example_output, preconditions[], success_metric}. Persona renders cards instead of prose. CI guard validates each capability maps to ≥1 real tool.

**Gaps:**
1. No card schema defined
2. Persona prose-only; no structured capability enum
3. No capability↔tool bidirectional link
4. No CI guard for coverage
5. Glossary output not integrated into prompt system

### 1.3 Proposed Canonical-Fix Path

**Step 1:** Create capability card schema  
File: app/prompts/catalog/capabilities.yaml  
Schema: id, title, user_phrasing[], tools[], example_input, example_output, preconditions[], success_metric  

**Step 2:** Refactor persona to reference capability IDs  
File: app/prompts/shared/lia_persona.yaml  
Change: replace prose list with structured capability_ids block  

**Step 3:** Add CI guard script  
File: scripts/check_capability_coverage.py  
Logic: for each tool in tool_registry_metadata.yaml, verify appears in ≥1 capability card  

**Blast radius:** Persona changes (1 file), new YAML schema (pure data), new CI script (non-blocking)

### 1.4 Harness Classification

| Component | Guide/Sensor | Comp/Infer |
|-----------|-------------|-----------|
| Capability.yaml schema | Guide | Computational |
| Persona refactor | Sensor | Computational |
| SystemPromptBuilder card injection | Sensor | Computational |
| CI guard script | Sensor | Computational |

All computational → ideal for reuse and testing.

### 1.5 Reuse Opportunities

1. Tool registry metadata (2836 lines, 98 tools well-documented) → reuse directly
2. Auto-glossary script → adapt to output capability cards
3. SystemPromptBuilder (existing {actions_context} injection point) → leverage for card rendering
4. YAML loading patterns (app/tools/tool_registry_loader.py) → reuse for capability.yaml
5. Test fixtures (eval/eval_cases.yaml, 200+ cases) → sample for capability coverage tests

### 1.6 Risks

**P0:** Stale capability cards if not auto-generated. Mitigation: make generate_tool_action_glossary.py output cards at build time.  
**P0:** Capability hallucination reintroduced if cards not validated against tool schemas. Mitigation: CI guard + example_input/output must match tool parameters_schema.  
**P1:** Multi-language support deferred to UI phase. Multi-language: thread examples through YAML i18n keys.  
**P1:** LGPD in examples. Mitigation: sanitize or use synthetic personas in public cards (production-quality/compliance-risk review).  
**P2:** Token bloat if all 50+ cards injected per prompt. Mitigation: cache card definitions; use prompt caching.

---

## 2. Initiative II — Structured State Machine (4 Slots)

### 2.1 Producer Identification

- **ConversationState** → app/shared/memory/conversation_state.py (dataclass, 14 existing slots including active_filters, last_entity, pagination_cursor)
- **PendingActionState** → app/orchestrator/pending_action.py (11.3 KB; FIX 25 stub; to_prompt_context() exists but NOT called)
- **System prompt assembly** → app/orchestrator/llm_cascade.py (lines 65-150; NO ConversationState injection today)
- **Main orchestrator** → app/orchestrator/main_orchestrator.py (74.7 KB; decision hub)
- **Memory resolver** → app/orchestrator/memory_resolver.py (14.4 KB; populates some ConversationState slots)

### 2.2 Gap Analysis vs Target

**Target:** 4 formal slots injected into system prompt at EACH turn: pending_action, active_filters, last_entity, workflow_context.

**Gaps:**
1. No workflow_context slot in ConversationState
2. pending_action.to_prompt_context() not called from main_orchestrator
3. No injection point in llm_cascade for ConversationState
4. last_entity exists but not fully populated by MemoryResolver
5. active_filters sticky but not re-announced at each turn

### 2.3 Proposed Canonical-Fix Path

**Step 1:** Add workflow_context slot to ConversationState  
File: app/shared/memory/conversation_state.py  
New field: workflow_context: dict[str, Any] | None with subfields: workflow_id, step, total_steps, elapsed_turns, last_action_intent  

**Step 2:** Add to_prompt_context() on ConversationState  
Aggregate: pending_action + active_filters + last_entity + workflow_context into single markdown block  

**Step 3:** Inject state block into SystemPromptBuilder  
File: app/orchestrator/llm_cascade.py (lines 65-150)  
Add parameter: conversation_state: ConversationState | None  
Inject after base system prompt, BEFORE action context  

**Step 4:** Wire main_orchestrator to pass ConversationState to llm_cascade  
File: app/orchestrator/main_orchestrator.py (before llm_cascade.run() call)  
Load state from PostgreSQL; pass as parameter  

**Step 5:** Populate last_entity and workflow_context in MemoryResolver  
Extract last_entity from parsed user message  
Track workflow_context from action outcomes  

**Blast radius:** ConversationState (backward-compatible, optional fields), SystemPromptBuilder (well-scoped injection), MemoryResolver (2-3 new extraction patterns), main_orchestrator (1 parameter pass)

### 2.4 Harness Classification

| Component | Guide/Sensor | Comp/Infer |
|-----------|-------------|-----------|
| workflow_context slot | Sensor | Computational |
| to_prompt_context() aggregation | Guide | Computational |
| State injection into system prompt | Sensor | Computational |
| last_entity extraction | Sensor | Inferential |
| workflow_context population | Sensor | Inferential |

Recommendation: Split change — computational parts (slots, injection) first; inferential (entity resolution) second with heavier testing.

### 2.5 Reuse Opportunities

1. PendingActionState infrastructure (DB persistence, to_prompt_context() stub) → reuse directly
2. ConversationState schema (14 slots; add 2 new optional fields) → reuse
3. MemoryResolver patterns (already extracts active_filters, last_entity) → extend
4. SystemPromptBuilder ({actions_context} injection point) → leverage
5. Test fixtures (eval/eval_cases.yaml, workflow scenarios) → test state transitions

### 2.6 Risks

**P0:** Context window bloat. Measure token count; use prompt caching; fallback to Haiku if over budget.  
**P0:** State corruption on concurrency (in-memory cache vs DB desync). Use PostgreSQL advisory locks or version field.  
**P1:** Pronoun resolution edge cases. Fallback to null if confidence low.  
**P1:** Workflow context explosion if every action sets it. Only set for multi-step workflows.  
**P1:** LGPD in state injection (last_entity {id: candidate_id} leaks PII). Redact ID in logs; only inject to LLM.  
**P2:** Backward compatibility (old DB records missing workflow_context). Alembic migration with default null.

---

## 3. Initiative VI — Continuous LLM-as-Judge Eval

### 3.1 Producer Identification

- **Eval runner** → eval/eval_runner.py (32.1 KB; executes 200+ test cases from eval_cases.yaml)
- **Eval cases** → eval/eval_cases.yaml (73 KB; 200+ golden conversations)
- **Eval judge** → eval/eval_judge.py (6.5 KB; Claude-based scorer; 5 dimensions in JUDGE_PROMPT)
- **Eval results** → eval/eval_results_*.json (145+ files, Apr 18-21; latest: 118 KB)
- **Eval report** → eval/eval_report.py (14.7 KB; generates HTML + summary)
- **CI/CD** → .github/workflows/ci.yml (5.4 KB; runs pytest/ruff/coverage; NO eval trigger today)

### 3.2 Gap Analysis vs Target

**Target:** Golden set 100-200 conversations. Judge scoring 5 dimensions (grounding, clarity, actionability, tone, safety). Trigger: each PR in app/prompts/ or app/orchestrator/. Dashboard drift tracking.

**Gaps:**
1. No CI trigger for evals
2. Judge prompt hardcoded; no separate eval config
3. Golden set mixing (unit tests + golden conversations)
4. Dimension mismatch (JUDGE_PROMPT scores differently)
5. No PII handling (real data in eval_results_*.json)
6. No drift dashboard
7. No structured metric export

### 3.3 Proposed Canonical-Fix Path (phased)

**Phase 1: Foundation**

**Step 1:** Refactor eval_judge.py to accept dimension config  
File: eval/eval_judge_config.yaml (new)  
Schema: dimensions: [grounding, clarity, actionability, tone, safety] with scoring_rubric, examples  

**Step 2:** Separate golden set into unit + E2E  
Split eval_cases.yaml:  
- eval_cases_unit.yaml (schema validation, tool parameters)  
- eval_cases_golden.yaml (100-150 realistic conversations, synthetic personas)  

**Step 3:** Add CI integration  
File: .github/workflows/eval.yml (new) or extend ci.yml  
Trigger: on PRs to app/prompts/, app/orchestrator/  
Non-blocking initially (warning only)  

**Phase 2: Production-grade**

**Step 4:** Redaction pipeline  
File: eval/redaction.py (new)  
Redact: candidate names, emails, phone, CPF, manager names  
Apply to eval_results_*.json before commit  

**Step 5:** Structured metric export  
File: eval/export_metrics.py (new)  
Read eval_results_*.json → Parquet per date  
Schema: case_id, dimensions (5 scores), verdict, timestamp  
Enable time-series analysis + drift detection  

**Step 6:** Dashboard skeleton  
File: eval/dashboard.py (new, Plotly/Streamlit)  
Metrics: score distribution, dimension trends, verdict breakdown  

**Blast radius:** New config files (additive), CI workflow (non-blocking), redaction (applied on next run), dashboard (standalone)

### 3.4 Harness Classification

| Component | Guide/Sensor | Comp/Infer |
|-----------|-------------|-----------|
| eval_judge dimension config | Guide | Computational |
| Judge Claude scoring | Sensor | Inferential |
| Golden set sourcing | Sensor | Computational |
| Redaction pipeline | Guide | Computational |
| Drift detection | Sensor | Computational |
| Dashboard | Sensor | Computational |

**Recommendation:** Judge scoring (inferential, good) + dimension config + redaction + drift detection (computational, safe).

### 3.5 Reuse Opportunities

1. eval_judge.py (already calls Anthropic SDK correctly) → parameterize prompt
2. eval_cases.yaml (200+ cases) → reuse for golden set, filter unit tests
3. Test patterns (tests/unit/test_fix*.py pytest) → eval runner outputs pytest-compatible JSON
4. Anthropic SDK (already in requirements.txt) → leverage for judge calls
5. CI infrastructure (.github/workflows/ci.yml pattern) → extend with new workflow
6. Logging/telemetry (app/ has [LIA-*] tags) → reuse in eval context

### 3.6 Risks

**P0:** Cost explosion (200 cases × multi-judge). Mitigation: judge sampled cases initially (20-30); expand incrementally. Use Haiku for triage, Sonnet for disputes.  
**P0:** eval_results_*.json bloat (145+ × 100KB = 14.5 MB). Mitigation: .gitignore eval_results_*.json; store in artifact bucket or keep last 3 days.  
**P1:** Golden set staleness (if cases not updated on tool schema changes). Mitigation: version eval_cases.yaml; tag with tool versions; regenerate on registry changes.  
**P1:** Judge prompt brittleness (phrasing changes shift scores). Mitigation: freeze judge prompt for baseline; track changes separately.  
**P1:** CI queue overload (eval per PR + nightly). Mitigation: queue eval jobs; prioritize user-triggered over scheduled.  
**P2:** Model version changes shift judge scores (Sonnet 3.5 → 4). Mitigation: A/B test on canary; document model version.  
**P2:** I18n in judge (Portuguese cases, English judge). Mitigation: judge prompt matches case language.

---

## 4. Canonical Source Resolution (Post-Initiatives)

| Component | Current Source | Post-Initiative | Rationale |
|-----------|---|---|---|
| Capabilities | Prose (lia_persona.yaml) | app/prompts/catalog/capabilities.yaml | Structured, versioned, CI-validated |
| Capability→Tool | Manual | capabilities.yaml (tools field) | Bidirectional link enforced |
| State machine (4 slots) | Scattered ConversationState | Consolidated in conversation_state.py | Single definition |
| Pending action context | Stub (unused) | Injected in system prompt | Live in prompt assembly |
| Eval rubric | Inline (eval_judge.py) | eval/eval_judge_config.yaml | Configurable, versioned |
| Golden conversations | Mixed eval_cases.yaml | eval/eval_cases_golden.yaml | Curated, privacy-safe |

---

## 5. Recommended Execution Order

**ORDER: II → I → VI** (not I → II → VI)

**Rationale:**
- **II first (State Machine):** Lowest risk, highest reuse. ConversationState already defined, PendingActionState already coded, LLMCascade has injection points. Foundation for I + VI.
- **I second (Capability Catalog):** Medium risk. Depends on II. Needs tool_registry_metadata.yaml (already complete, 98 tools). Unlocks VI judge validation.
- **VI last (Eval Harness):** Highest value, depends on I + II. Runs in background; non-blocking after II.

**Timeline:**
- II: 1-2 weeks
- I: 1 week
- VI: 2 weeks
- **Total: 4-5 weeks (non-blocking after II)**

---

## 6. Open Questions (User Decision Required)

### Initiative I

**Q1:** Auto-generate cards from tool_registry_metadata.yaml or manual author?  
Recommendation: Hybrid — auto-generate structure; manual override of title/user_phrasing/examples for top 20.

**Q2:** Inline cards in chat or separate menu?  
Recommendation: Inline (leverages system prompt injection); Option B deferred to Initiative IV.

**Q3:** Multi-language support?  
Recommendation: Portuguese only (MVP); infrastructure language-agnostic for migration later.

### Initiative II

**Q1:** Auto-populate workflow_context from action intents or explicit registration?  
Recommendation: Explicit registration initially; auto-inference after >50 real workflows.

**Q2:** State injection in system prompt or tool context?  
Recommendation: System prompt (FIX 25-compliant); benchmark later if token cost prohibitive.

**Q3:** How deep should last_entity resolution go?  
Recommendation: Shallow (nouns + direct references, regex-based); LLM handles edge cases.

### Initiative VI

**Q1:** Eval judge per-PR or nightly batch?  
Recommendation: Hybrid — per-PR on sampled cases (20-30); nightly full run for metrics.

**Q2:** PII tolerance in eval results?  
Recommendation: Strict (all redacted); synthetic personas only. Compliant with LGPD; reduces incident risk.

**Q3:** Deterministic (same eval = same score) or accept variance?  
Recommendation: Deterministic baseline (fixed seed, temp 0); Option B later for variance analysis.

### Cross-initiative

**Q1:** Staggered (II → I → VI) or together?  
Recommendation: Staggered (allows feedback loops; easier debugging).

**Q2:** CI guard catch drift auto or flag for review?  
Recommendation: Warning initially; strict gate after >2 weeks.

---

## 7. Summary Table

| Initiative | Producer Files | Existing Code | New Code | Risk | Timeline |
|---|---|---|---|---|---|
| I | tool_registry_metadata.yaml | tool registry (98 tools) | capabilities.yaml + CI guard | P1 (drift) | 1 week |
| II | ConversationState + llm_cascade | state (14 slots), pending stub | +2 slots, injection, extraction | P0 (bloat) | 1-2 weeks |
| VI | eval/ + .github/workflows/ | eval_judge, cases (200+), runner | config + CI trigger + redaction | P0 (cost) | 2 weeks |

---

## 8. Audit Manifest

**Files inspected (read-only):**
- app/tools/registry.py (190 lines)
- app/tools/tool_registry_metadata.yaml (2836 lines, 98 tools)
- app/shared/memory/conversation_state.py (excerpt: 50+ lines)
- app/orchestrator/pending_action.py (excerpt: 80 lines)
- app/orchestrator/llm_cascade.py (excerpt: 150 lines)
- eval/eval_judge.py (excerpt: 100 lines)
- eval/eval_cases.yaml (73 KB, 200+ cases)
- .github/workflows/ci.yml (5.4 KB full)
- docs/LIA_MATURITY_ROADMAP.md (full, 400+ lines)

**Metrics:**
- 98 tools registered
- 200+ eval test cases
- 145+ eval result JSONs (Apr 18-21)
- 0 capability cards in production
- 14 existing ConversationState slots; 4 planned (2 new)
- 1 PendingActionState stub (unused)

---

**Status:** Ready for user review. Awaiting decisions on Q1-Q3 + execution order confirmation.  
**Sign-off:** canonical-fix + harness-engineering-lia + production-quality

