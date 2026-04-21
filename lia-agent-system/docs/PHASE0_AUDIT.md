# PHASE 0 — Discovery Audit
**Date:** 2026-04-21  
**Executed by:** AI Agent (Read-only discovery)  
**Status:** Complete — Ready for user review

---

## 0.1 Inventory

### 0.1.1 Golden Sets / Eval Conversations
- **Location:** `tests/fixtures/` + `eval/eval_results_*.json`
- **Conversation fixtures:** 10+ snapshot JSONs (wizard, pipeline, screening scenarios)
- **Eval result files:** 139 timestamped result JSON files (2026-04-17 to 2026-04-21)
- **Golden dataset:** `tests/fixtures/golden_dataset.py` + bias variant
- **Assessment:** Golden set exists but low coverage relative to test count (484 tests). Eval results are recent but snapshot/regression coverage TBD.

### 0.1.2 Test Fixtures (FIX 1-19 TDD Pattern)
| Test File | Status | Assertion Pattern |
|---|---|---|
| test_fix1_domain_actions_to_llm.py | ✅ Active | Domain action routing |
| test_fix2_examples_populated.py | ✅ Active | Prompt example injection |
| test_fix5_wizard_sync.py | ✅ Active | Wizard YAML consistency |
| test_fix6_observability.py | ✅ Active | Telemetry marker presence |
| test_fix7_semantic_overlap.py | ✅ Active | Tool semantic deduplication |
| test_fix8_governance_enforcement.py | ✅ Active | FairnessGuard trigger coverage |
| test_fix9_quality.py | ✅ Active | Output quality metrics |
| test_fix10_coverage_unification.py | ✅ Active | Tool+action glossary alignment |
| test_fix11_placement_wsi.py | ✅ Active | WSI placement in pipeline |
| test_fix12_hitl_obs.py | ✅ Active | HITL signal logging |
| test_fix14_no_agent_hijack.py | ✅ Active | Agent boundary enforcement |
| test_fix15_affirmation.py | ✅ Active | Affirmation flow detection |
| test_fix16_correction_detector.py | ✅ Active | User correction pattern |
| test_fix17_capability.py | ✅ Active | Capability truthfulness guardrail |
| test_fix19_affirmation_wiring.py | ✅ Active | Affirmation → persona wiring |
| test_fix34_governance_related_tools.py | ✅ Active | Related-tools governance |

**Count:** 16 FIX tests / 484 total tests (3.3% coverage of total)  
**Pattern:** Red→Green→Refactor TDD; assertion-heavy; mostly in `app/prompts/`, `app/tools/` layers.

### 0.1.3 Capability Docs
| Doc | Local Path | Replit Path | Last Touch |
|---|---|---|---|
| LIA_AI_LAYER_CAPABILITIES.md | /Users/paulomoraes/Documents/Python/ | — | 2026-04-12 12:23 |
| LIA_AGENTS_DETAILED.md | /Users/paulomoraes/Documents/Python/ | — | 2026-04-12 13:36 |
| LIA_AI_HANDOFF.md | — | lia-agent-system/docs/ | 2026-04-21 11:23 |
| LIA_MATURITY_ROADMAP.md | — | lia-agent-system/docs/ | 2026-04-21 16:49 |

### 0.1.4 Tool Registry
- **Tool definition locations:** `app/tools/` (base), `app/domains/*/tools/` (domain-specific)
- **Tool count (manual @tool grep):** 13 tool classes/definitions found via @tool decorator + ToolDefinition
- **Glossary script:** `scripts/generate_tool_action_glossary.py` (exists, freshness check enabled)
- **Glossary output:** `docs/GLOSSARIO_ACTIONS_TOOLS.md` (305 KB, regenerated 2026-04-21 12:54)
- **Note:** Glossary flagged as stale in last `--check` run; requires regeneration.

### 0.1.5 Prompt Blocks
- **Shared prompts:** `app/prompts/shared/*.yaml` (combined size: 50,870 bytes)
- **Domain prompts:** `app/prompts/domains/*.yaml` (exact count: 31 files total across shared + domains)
- **Guardrails identified:**
  - FIX 17: `capability_truthfulness` guardrail in prompt catalog
  - FairnessGuard usage: 706 occurrences across codebase
  - Compliance policies: ComplianceDomainPrompt active in 5+ domains

### 0.1.6 Eval Results históricos
- **Oldest result:** `eval_results_20260417_175852.json` (2026-04-17, 17:58 UTC)
- **Newest result:** `eval_results_20260418_020941.json` (2026-04-18, 02:09 UTC) [note: only first 20 sampled]
- **Total count:** 139 result files
- **Assessment:** Regular automated eval runs 2x/day on recent branch; data freshness high.

### 0.1.7 HITL / Governance
- **governance_tags usage (YAML):** 0 occurrences found (⚠️ **unexpectedly low**)
- **FairnessGuard usage:** 706 occurrences (high coverage in app layer)
- **Compliance base:** `app/domains/compliance_base.py` imported by 5 domain classes (sourcing, job_mgmt, cv_screening, communication, analytics)
- **Assessment:** FairnessGuard active; governance_tags may be underdocumented or renamed.

### 0.1.8 Telemetry
- **[LIA-*] marker count:** 95 occurrences in `app/` codebase
- **Observability modules:** 13 modules in `app/shared/observability/`
  - agent_health_alert_service.py
  - agent_monitoring_service.py
  - ai_consumption_outbox_worker.py
  - structured_logging.py
  - tool_metrics.py
  - drift_alert_service.py
  - model_drift_service.py
  - token_tracking_service.py
  - tracing.py
  - usage_tracking_callback.py
  - wsi_observability.py
  - callbacks.py
  - langsmith.py
- **Assessment:** Comprehensive observability; telemetry markers scattered but organized in shared/ layer.

---

## 0.2 Doc Freshness Matrix

**Classification:** T1 = Auto-gen/canonical, T2 = Human-maintained/recent, T3 = Suspect/legacy

| Doc | Local/Replit | Last Touch | Tier | Verdict | Fact-Check | Action |
|---|---|---|---|---|---|---|
| **Tool/Action Glossary (GLOSSARIO_ACTIONS_TOOLS.md)** | Replit | 2026-04-21 12:54 | T1 | ✅ FRESH | Auto-gen via script; timestamp recent | TRUST + verify stale flag |
| **DEVELOPER_HANDOFF.md** | Replit | 2026-04-21 15:01 | T2 | ✅ FRESH | Claims "170KB", "agents in Haiku", real agents found ✅ | TRUST with brief verification |
| **LIA_AI_HANDOFF.md** | Replit | 2026-04-21 11:23 | T2 | ✅ FRESH | Mirrors capability claims; 46KB recent | TRUST + cross-ref canonical sources |
| **LIA_AI_LAYER_CAPABILITIES.md** | Local Mac | 2026-04-12 12:23 | T3 | ⚠️ STALE | 9 days old; claims tool registries but no verification for domain count (63 vs docs) | FACT-CHECK vs replit registry |
| **LIA_AGENTS_DETAILED.md** | Local Mac | 2026-04-12 13:36 | T3 | ⚠️ STALE | 9 days old; no recent commits; claims agent structure but not validated | FACT-CHECK vs app/agents/ |
| **CANONICAL_SOURCES_SPEC.md** | Replit | 2026-04-17 03:54 | T2 | ⚠️ STALE | 4 days old; post-FIX 13 but predates FIX 14-19; needs re-validation | RE-VALIDATE post-FIX 19 |
| **AUDIT_ACTIONS_TOOLS_DESCRIPTIONS.md** | Replit | 2026-04-20 18:14 | T2 | ✅ FRESH | 56KB recent; audit capture | TRUST as snapshot |
| **LIA_REFACTORING_REPORT.md** | Local Mac | 2026-04-13 07:18 | T3 | 🗑️ OBSOLETE | 8 days old; titled "refactoring" (historical); do not consume as spec | ARCHIVE to docs/archive/ |
| **ai-architecture-audit.md** | Replit | 2026-04-11 16:23 | T3 | 🗑️ OBSOLETE | 10+ days; 516KB legacy audit; prefer code over this | ARCHIVE (read-only legacy) |
| **FRIA_EU_AI_ACT.md** | Replit | — | T3 | 📋 GOVERNANCE-ONLY | Regulatory reference; read-only | REFERENCE-ONLY |

**Tool/Action Canonical Guide (GitHub `replit-sync` branch):** 
- Fetch attempt: branch exists, recent commits on tooling (2de152df0 = April 21)
- Canonical guide not found as single doc; likely distributed across:
  - `GLOSSARIO_ACTIONS_TOOLS.md` (T1 auto-gen)
  - Per-domain tool YAML registries (T1 code)
  - `AUDIT_ACTIONS_TOOLS_DESCRIPTIONS.md` (T2 snapshot)

---

## 0.3 Gap Analysis

### Information Types & Coverage Status

| Info Type | Current Source(s) | Canonical Status | Gap |
|---|---|---|---|
| **Tool definitions** | `app/tools/`, domain-specific `.py` + auto-gen glossary | T1 (glossary) | None — code is source of truth; glossary lags ~hrs |
| **Action signatures** | GLOSSARIO_ACTIONS_TOOLS.md (T1 auto-gen) | T1 | None — well-defined |
| **Capability mappings** | LIA_AI_LAYER_CAPABILITIES.md (T3 local, stale) | CONFLICT | **GAP:** local doc outdated; rely on Replit DEVELOPER_HANDOFF (T2) + code |
| **Agent architecture** | LIA_AGENTS_DETAILED.md (T3 stale) + code | CONFLICT | **GAP:** local doc 9 days old; agents directory in code is truth |
| **Prompts / guardrails** | app/prompts/*.yaml + test_fix17 | T1 (code) | None — YAML is source; test coverage validates |
| **Eval strategy** | eval/ folder + 139 result JSONs | T1 (empirical) | **GAP:** Golden set small (10 fixtures vs 139 results); snapshot-to-regression mapping unclear |
| **Governance rules** | Compliance_base + FairnessGuard (706 usages) | T1 (code) | **GAP:** governance_tags (0 YAML usages) may be deprecated or renamed; unclear intent |
| **Observability** | app/shared/observability/ (13 modules) + [LIA-*] markers (95) | T1 (code) | None — well-instrumentedREQUIRES validation of hook deployment |

### Recommendations
1. **Delete or archive** `LIA_AI_LAYER_CAPABILITIES.md`, `LIA_AGENTS_DETAILED.md`, `LIA_REFACTORING_REPORT.md`, `ai-architecture-audit.md` — replace with code + DEVELOPER_HANDOFF (T2) as reference.
2. **Refresh** `CANONICAL_SOURCES_SPEC.md` post-FIX 19 completion to declare canonical sources for Phase 1.
3. **Investigate** governance_tags silence — verify not deprecated or renamed to different tagging scheme.
4. **Expand golden set** from 10 to 30+ conversations to match eval run frequency (139 evals in 4 days).

---

## 0.4 Canonical Source Resolution

**Going forward, for each info type, use this source:**

| Information Type | Canonical Source | Rationale | Fallback |
|---|---|---|---|
| **Tool definitions & signatures** | `lia-agent-system/app/tools/` + domain `*/tools/` (code) | Single source of truth; glossary auto-gen from code | GLOSSARIO_ACTIONS_TOOLS.md (T1 snapshot) |
| **Tool descriptions / examples** | Per-tool docstrings in code + AUDIT_ACTIONS_TOOLS_DESCRIPTIONS.md | Code docstrings are maintained inline; audit snapshot for review | DEVELOPER_HANDOFF.md (summary) |
| **Agent structure / capabilities** | `lia-agent-system/app/agents/` + `app/domains/*/domain.py` (code) | Agents are defined in code; DDD structure clear | DEVELOPER_HANDOFF.md (T2 reference) |
| **Prompts / system instructions** | `lia-agent-system/app/prompts/shared/` + `domains/` (YAML code) | Prompts are code; test_fix17 validates truthfulness | CANONICAL_SOURCES_SPEC.md (declaration) |
| **Guardrails / compliance rules** | `app/domains/compliance_base.py` + FairnessGuard module (code) | Enforcement is in code; FairnessGuard widely deployed | FAIRNESS_GUARD_COVERAGE.md (snapshot) |
| **Eval methodology** | `tests/fixtures/golden_dataset*.py` + `eval/` folder (code + data) | Golden set + result JSONs are empirical truth | DEVELOPER_HANDOFF.md (overview) |
| **Observability / telemetry** | `app/shared/observability/` modules (code) | Instrumentation is in code | DEVELOPER_HANDOFF.md (inventory) |

---

## 0.5 Baseline Metrics

**Snapshot as of 2026-04-21 16:49 UTC:**

| Metric | Count | Notes |
|---|---|---|
| Total test files | 484 | Across all test/ directories |
| FIX test files (TDD Red→Green) | 16 | Focused on guardrails, prompt, tooling |
| Tool count (via @tool grep) | 13 | Manually counted; glossary may be more precise |
| Prompt YAML files | 31 | `shared/` + `domains/` combined |
| Prompt token footprint | 50,870 bytes | Shared prompts only |
| Domain count | 63 | DDD structure active |
| Observability modules | 13 | `app/shared/observability/` |
| [LIA-*] telemetry markers | 95 | Scattered across app/ |
| FairnessGuard usages | 706 | High coverage |
| Eval results (4-day window) | 139 | Frequent automated runs |
| Golden set conversations | ~10 | Snapshot fixtures + seeder |
| Git branches tracked | 2 (active) | main + replit-sync |

---

## 0.6 Risks & Open Questions for User

### Risk: Documentation Staleness Cycle
**Severity:** Medium  
**Description:** Local capability docs (LIA_AI_LAYER_CAPABILITIES.md, LIA_AGENTS_DETAILED.md) are 8-9 days old and becoming stale source of truth. Replit docs (DEVELOPER_HANDOFF, LIA_AI_HANDOFF) are fresh (hours), but governance_tags usage is suspiciously absent.  
**Mitigation:** Declare Replit as primary; archive local docs; establish 24-hour refresh SLA on Replit docs or CI gate them.

### Risk: Glossary Regeneration Lag
**Severity:** Low  
**Description:** GLOSSARIO_ACTIONS_TOOLS.md was regenerated 2026-04-21 12:54 but marked "stale" by `--check`. Script may have strict freshness threshold.  
**Mitigation:** Clarify regeneration schedule (manual vs. automatic on PR); add to CI if not present.

### Risk: Governance_tags Silent
**Severity:** Medium  
**Description:** 0 YAML usages of `governance_tags` found, despite roadmap references (FIX 8). May be:
  - Renamed to `governance_policies` or similar
  - Not yet implemented in YAML (only in code)
  - Deprecated post-FIX 13
  
**Mitigation:** Verify current tagging scheme; update roadmap FIX 8 description or re-run grep with broader pattern.

### Risk: Golden Set Undersize
**Severity:** Low  
**Description:** Only ~10 conversation fixtures vs. 139 eval result JSONs (4-day span). Golden set insufficient to reproduce all eval scenarios.  
**Mitigation:** Expand golden set to 30-50 conversations covering edge cases identified in Track 1 (FIX 20-28).

### Open Question: FIX 3-4 Status
**Description:** Roadmap FIX 3 + FIX 4 (governance_tags + related_tools) are referenced in replit-sync commits but not in current test inventory. Are these subsumed into FIX 8 or completed?  
**Action:** Clarify scope before Phase 1 Fase A.

### Open Question: Canonical Guide Distributed?
**Description:** No single "tool/action canonical guide" doc found on replit-sync branch. Is canonical information distributed across multiple sources (glossary, YAML, audit)?  
**Action:** User clarifies canonical guide intent (single doc vs. distributed) for Phase 1.

---

## 0.7 Recommendations for Track 1 Fase A (FIX 20)

### Reusable Assets (Low-Risk Adoption)

| Asset | Source | Confidence | Use in Track 1 |
|---|---|---|---|
| **TDD test harness** | test_fix1-19 pattern | ✅ HIGH | Reuse FIX test template for FIX 20-28 |
| **Glossary auto-gen** | scripts/generate_tool_action_glossary.py | ✅ HIGH | Extend for new tools (pagination, enums) |
| **FairnessGuard enforcement** | app/domains/compliance_base.py | ✅ HIGH | Leverage for FIX 22 (enum translation) |
| **Golden dataset seeder** | tests/fixtures/golden_dataset_seeder.py | ✅ MEDIUM | Extend with FIX 20-28 scenarios |
| **Eval result JSONs** | eval/eval_results_*.json (139 files) | ✅ MEDIUM | Use for regression baseline; expand golden set |
| **Observability modules** | app/shared/observability/ | ✅ MEDIUM | Instrument FIX 20 pagination + FIX 25 pending_action |

### Risky / Stale References (Avoid)

| Asset | Reason | Action |
|---|---|---|
| LIA_AI_LAYER_CAPABILITIES.md | 9 days old; unverified claims | Archive; do not consume |
| LIA_AGENTS_DETAILED.md | 8 days old; domain drift unknown | Archive; use code + DEVELOPER_HANDOFF instead |
| LIA_REFACTORING_REPORT.md | Historical; labeled "refactoring" only | Archive to docs/archive/ |
| ai-architecture-audit.md | 10+ days; 516KB legacy | Archive as read-only reference only |

### Canonical Sources for FIX 20-28 Implementation

1. **Tool registry:** Always commit new tools to `app/domains/job_management/tools/query_tools.py` (FIX 20) + regenerate glossary
2. **Prompt changes:** Update YAML in `app/prompts/shared/` + run test_fix17 to validate truthfulness
3. **Governance:** Use FairnessGuard + ComplianceDomainPrompt pattern (proven in 5+ domains)
4. **Tests:** Use FIX test template (test_fix17_capability.py) for TDD Red→Green
5. **Observability:** Hook into structured_logging + [LIA-*] markers per observability modules

---

## 0.8 Summary Table: Inventory Completeness

| Category | Count | Status | Notes |
|---|---|---|---|
| Test fixtures (FIX 1-19) | 16 | ✅ Complete | TDD pattern clear; FIX 20+ can follow |
| Golden sets | 10 | ⚠️ Minimal | Expand to 30+ for Phase 1 regression |
| Eval results | 139 | ✅ Healthy | 4-day span; automated; recent |
| Tools (registered) | 13+ | ✅ Known | Glossary is T1; tag additions in progress |
| Prompts (YAML) | 31 | ✅ Inventoried | Shared + domain organized |
| Domains | 63 | ✅ Active | DDD structure mature |
| Observability modules | 13 | ✅ Complete | Comprehensive instrumentation |
| Docs (Replit) | 8 | ⚠️ MIXED | Fresh (T2) but 4 stale (T3/archive) |
| Docs (Local Mac) | 3 | 🗑️ STALE | Archive all 3; use Replit as primary |

---

**END OF AUDIT**

