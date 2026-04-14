# DUPLICATION_DIVERGENCE_MAP — P13 Forensic Audit
## Codebase: `/home/runner/workspace/lia-agent-system` | Date: 2026-04-14
## Auditor: Claude Sonnet 4.6 | Method: Exhaustive static analysis, SSH grep, file reads

---

## 1. EXECUTIVE SUMMARY

**Total Concerns Audited:** 10 (A–J)  
**Total Canonical Implementations Identified:** 12  
**Total Divergences Found:** 92+ (confirmed file:line citations)  
**Total Silent Failure Paths:** 17+ confirmed  
**PII Leaks in Logs:** 7 confirmed  
**Critical LGPD Violation:** 1 (pgvector embeddings never deleted on right-to-erasure)

### Top 5 Critical Findings

| # | Concern | Finding | Severity |
|---|---------|---------|----------|
| 1 | J: Error Handling | `AgentError` adopted in <1% of 4,858 exception blocks; 16+ silent catches in production paths including policy evaluation bypass (`pipeline_policy.py:71`) and WSI evaluation bypass (`wsi/evaluation.py:300`); raw `str(e)` leakage to API clients | CRÍTICO |
| 2 | H: LLM Configuration | Two parallel LLM provider layers; 8 hardcoded temperature values; 14+ hardcoded max_tokens values; 5 different Gemini API key env var names; Claude model version skew (`claude-3-5-sonnet-20241022` at `system_health.py:75` vs `claude-sonnet-4-6` everywhere else) | CRÍTICO |
| 3 | F: Memory/Context | 5 coexisting incompatible memory systems (SQL ConversationMemory, WorkingMemoryService, LongTermMemoryService, in-process MemoryResolver, ConversationStateStore); 5 different history truncation values (5/6/10/20/30) across 12 call sites; 9 domain agents fully disconnected from orchestrator memory | CRÍTICO |
| 4 | E: Compliance/LGPD | pgvector embeddings are never deleted when LGPD Art. 18-VI right-to-erasure is invoked — zero matches for any vector deletion path across entire codebase | CRÍTICO |
| 5 | D: Audit/Logging | 7 PII leaks to logger.info() (email, name, phone) in `job_vacancy_service.py` and `handlers_lifecycle.py`; 25+ domain files with zero logging | HIGH |

---

## 2. ENTROPY INDEX

### Per-Concern Scores

| Concern | Score | Classification |
|---------|-------|----------------|
| A: Fairness | 25/100 | Saudável |
| B: LIA Persona | 72/100 | Entrópico |
| C: Bias Detection | 42/100 | Atenção |
| D: Audit/Logging | 48/100 | Atenção |
| E: Compliance/LGPD | 55/100 | Atenção |
| F: Memory/Context | 82/100 | Caótico |
| G: Orchestration | 72/100 | Entrópico |
| H: LLM Configuration | 88/100 | Caótico |
| I: Input Validation | 61/100 | Entrópico |
| J: Error Handling | 91/100 | Caótico |

### Overall Platform Entropy

**(25+72+42+48+55+82+72+88+61+91) / 10 = 63.6 / 100**

**Classification: ENTRÓPICO**

> 0–20 Canônico | 21–40 Saudável | 41–60 Atenção | **61–80 Entrópico** | 81–100 Caótico

Three concerns reach Caótico (F, H, J). Three are Atenção (C, D, E). The platform has a stable compliance surface (A, C) but critical architectural fragmentation in runtime concerns.

---

## 3. CONCERN-BY-CONCERN ANALYSIS

---

### CONCERN A: FAIRNESS — Entropy 25/100 (Saudável)

**Canonical:** 1 (`app/shared/compliance/fairness_guard.py`)  
**Divergences:** 5

#### A.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| FairnessGuard L1/L2/L3 | `fairness_guard.py:503` | Canonical runtime block | — | CANONICAL |
| Middleware wrapper | `fairness_guard_middleware.py` | Wraps canonical cleanly | `fairness_guard.py` | OK (delegate) |
| Guardrail DB rule | `guardrails_seed.py:34-35` | Hardcoded text list, no FG call | `DISCRIMINATORY_CATEGORIES` | HARDCODED |
| Guardrail API rule | `guardrails.py:196-197` | Repeated protected list | `fairness_guard.py` DISCRIMINATORY_CATEGORIES | HARDCODED |
| Onboarding instruction | `onboarding_prompts.py:25` | Plain text "NUNCA discriminar" — no runtime enforcement | No FairnessGuard call | VERBAL |
| Sourcing error message | `sourcing_react_agent.py:263` | Custom wording vs FG `educational_message` | `fairness_guard.py` educational messages | VERBAL |

#### A.3 — Dependency Graph

```
CANONICAL:
  app/shared/compliance/fairness_guard.py
    └── DISCRIMINATORY_CATEGORIES (single source of truth)
    └── FairnessGuard.check() → L1 regex → L2 implicit → L3 semantic
          ^ imported correctly by:
          ├── fairness_guard_middleware.py (wraps cleanly)
          │     ^ used by: jd_generation.py, check_fairness() callers
          ├── interview_notes.py:44
          ├── ml_predictions.py:154 (inline import)
          ├── lia_assistant/insights.py:301 (inline import)
          └── sourcing/*_tool_registry.py (6 registries, correct)

DIVERGENT (not connected to FG at runtime):
  guardrails_seed.py:34-35  → DB guardrails table (text only, no FG)
  guardrails.py:196-197     → Repeats protected list manually
  onboarding_prompts.py:25  → Plain text instruction
  sourcing_react_agent.py:263 → Custom inline message
```

---

### CONCERN B: LIA PERSONA — Entropy 72/100 (Entrópico)

**Canonical:** 1 (`app/prompts/shared/lia_persona.yaml` via `SystemPromptBuilder`)  
**Divergences:** 22+

#### B.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `lia_persona.yaml` | `prompts/shared/lia_persona.yaml` | Full canonical persona | — | CANONICAL |
| `SOURCING_SYSTEM_PROMPT` | `sourcing_system_prompt.py:126` | Complete re-definition of LIA persona in Python | `lia_persona.yaml` | REIMPLEMENTACAO |
| `WIZARD_SYSTEM_PROMPT` | `wizard_system_prompt.py:148` | Complete re-definition of LIA persona in Python | `lia_persona.yaml` | REIMPLEMENTACAO |
| onboarding framing | `onboarding_orchestrator.py:311` | "Eu sou uma assistente pessoal" — not senior recruiter | `lia_persona.yaml` (senior recruiter) | CONFLITANTE |
| onboarding wording | `onboarding_orchestrator.py:514` | No diacritics, different wording | `lia_persona.yaml` | CONFLITANTE |
| voice greeting | `voice_interview_state_machine.py:177` | Hardcoded greeting, no persona depth | `lia_persona.yaml` | HARDCODED |
| email footer | `email_providers/base.py:24,34` | Static LIA description | `lia_persona.yaml` | HARDCODED |
| email template | `communication_templates.py:84,1200` | Static LIA description (2 instances) | `lia_persona.yaml` | HARDCODED |
| task planner sub-persona | `task_planner.py:46` | "Task Planner da LIA" mini-persona | `lia_persona.yaml` | REIMPLEMENTACAO |
| routing prompt | `llm_cascade.py:26` | "roteador de intencoes" — no LIA identity | `lia_persona.yaml` | REIMPLEMENTACAO |
| WSI questions | `api/v1/wsi/questions.py:166` | "Voce e um especialista em recrutamento" | `lia_persona.yaml` | REIMPLEMENTACAO |
| WSI reports | `api/v1/wsi/reports.py:248` | "especialista em entrevistas comportamentais" | `lia_persona.yaml` | REIMPLEMENTACAO |
| archetypes | `candidate_search/archetypes.py:1162,1280` | Generic expert (×2) | `lia_persona.yaml` | REIMPLEMENTACAO |
| company culture | `api/v1/company.py:426,701,865` | Generic expert (×3) | `lia_persona.yaml` | REIMPLEMENTACAO |
| email templates | `api/v1/email_templates.py:735,828` | Generic expert (×2) | `lia_persona.yaml` | REIMPLEMENTACAO |
| wsi compact | `wsi_compact_pipeline.py:116` | "especialista usando metodologia WSI" | `lia_persona.yaml` | REIMPLEMENTACAO |
| JD generator | `jd_generator_service.py:228,374,436` | Multiple "especialista" variants (×3) | `lia_persona.yaml` | REIMPLEMENTACAO |
| DB seed persona | `api/v1/guardrails.py:202` | Persona fragment in DB seed | `lia_persona.yaml` | HARDCODED |

#### B.3 — Dependency Graph

```
CANONICAL:
  app/prompts/shared/lia_persona.yaml
    └── loaded by app/shared/prompts/system_prompt_builder.py
          ^ used correctly by:
              chat.py:691, interview_notes.py:544,946,
              lia_assistant/*, candidate_search/misc_search.py:313,
              orchestrator.py:290, cascaded_router.py:67,
              onboarding_orchestrator.py:497 (partial)

REIMPLEMENTACOES (disconnected from YAML):
  sourcing/agents/sourcing_system_prompt.py:126 → sourcing_react_agent.py
  job_management/agents/wizard_system_prompt.py:148 → wizard_react_agent.py
  services/voice_interview_state_machine.py:177 → standalone
  services/onboarding_orchestrator.py:311,421,514 → partial (also uses builder at :497)
  orchestrator/task_planner.py:46 → standalone LLM call
  orchestrator/llm_cascade.py:26 → routing LLM call
  12+ API/service files with "Voce e um especialista..." → anonymous LLM calls
```

---

### CONCERN C: BIAS DETECTION — Entropy 42/100 (Atenção)

**Canonical:** 2 (`bias_audit_service.py` for Four-Fifths; `audit_service.py` for PROTECTED_CRITERIA)  
**Divergences:** 5

#### C.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `FOUR_FIFTHS_THRESHOLD` | `bias_audit_service.py:49` | = 0.80 | — | CANONICAL |
| `FOUR_FIFTHS_THRESHOLD` (duplicate) | `admin_compliance_fairness.py:41` | = 0.80 (same value, separate file) | `bias_audit_service.py:49` | REIMPLEMENTACAO |
| `_compute_four_fifths()` | `admin_compliance_fairness.py:139-198` | Independent AIR calculation | `BiasAuditService.compute_adverse_impact()` | REIMPLEMENTACAO |
| `PROTECTED_CRITERIA` | `audit_service.py:38` | 10-item list | — | CANONICAL |
| `DISCRIMINATORY_CATEGORIES` | `fairness_guard.py:133` | 19 categories, different taxonomy | `audit_service.PROTECTED_CRITERIA` | CONFLITANTE |
| Verbal protected list | `guardrails_seed.py:34` | Text "genero, raca..." | `audit_service.PROTECTED_CRITERIA` | HARDCODED |
| Partial list | `guardrails_seed.py:97` | Only 3 attributes (genero, etnia, idade) | `audit_service.PROTECTED_CRITERIA` | INCOMPLETA |

#### C.3 — Dependency Graph

```
CANONICAL BIAS:
  app/shared/services/bias_audit_service.py
    ├── FOUR_FIFTHS_THRESHOLD = 0.80
    ├── assert_four_fifths_rule() → admin_bias_audit.py:30,35 (correct)
    └── BiasAuditService.compute_adverse_impact()

DUPLICATE (REIMPLEMENTACAO):
  app/api/v1/admin_compliance_fairness.py
    ├── FOUR_FIFTHS_THRESHOLD = 0.80 (own copy — silent divergence risk)
    └── _compute_four_fifths() (own implementation)

CANONICAL PROTECTED ATTRS (10 items):
  app/shared/compliance/audit_service.py:38
    └── PROTECTED_CRITERIA → sourcing_react_agent.py,
        wsi_interview_graph.py, communication_react_agent.py, agent_chat_ws.py

PARALLEL TAXONOMY (19 categories):
  app/shared/compliance/fairness_guard.py:133
    └── DISCRIMINATORY_CATEGORIES → fairness_guard_middleware.py → multiple endpoints

DISCONNECTED VERBAL:
  guardrails_seed.py:34,97 → DB only (text, no runtime link to either taxonomy)
```

---

### CONCERN D: AUDIT/LOGGING — Entropy 48/100 (Atenção)

**Canonical:** 1 (`app/shared/compliance/audit_service.py` + shim)  
**Divergences:** 7+

#### D.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `AuditService` | `shared/compliance/audit_service.py` | AI governance logging | — | CANONICAL |
| Shim | `shared/services/audit_service.py` | Re-exports canonical | `audit_service.py` | OK (delegate) |
| `job_audit_service` | `job_management/services/job_audit_service.py` | Job-specific audit, not connected to AuditService | `AuditService` | REIMPLEMENTACAO |
| PII: email in log | `job_vacancy_service.py:54` | `logger.info(f"...{result['email']}")` | LGPD data minimization | CONFLITANTE |
| PII: email in log | `job_vacancy_service.py:477` | `logger.info(f"...{recruiter_email}")` | LGPD data minimization | CONFLITANTE |
| PII: name+email | `job_vacancy_service.py:573-574` | `logger.info(f"Manager: {manager_name} ({manager_email})")` | LGPD data minimization | CONFLITANTE |
| PII: phone in log | `handlers_lifecycle.py:185` | `logger.info(f"WhatsApp sent to {candidate_phone}")` | LGPD data minimization | CONFLITANTE |
| PII: phone in log | `handlers_lifecycle.py:473` | Same pattern (×2) | LGPD data minimization | CONFLITANTE |
| PII: phone in log | `handlers_lifecycle.py:523` | Same pattern (×3) | LGPD data minimization | CONFLITANTE |
| Import via shim (routing drift) | `automation/_shared.py:22`, `services/__init__.py:60`, `weekly_digest_service.py:344` | Via shim (functionally OK but inconsistent) | Direct canonical import | VERBAL |
| No logging — 25+ files | sourcing/*_tool_registry.py, wizard_system_prompt.py, and 23 others | Completely silent execution | Audit trail requirement | AUSENTE |

#### D.3 — Dependency Graph

```
CANONICAL:
  app/shared/compliance/audit_service.py (AuditService)
    ^ direct imports (17+ files): jd_generation.py, pipeline.py,
      communication.py, scheduling.py, auth.py, interviews.py,
      agent_chat_ws.py, onboarding.py, sourcing_react_agent.py,
      wsi_interview_graph.py, communication_react_agent.py, etc.
    ^ via shim (app/shared/services/audit_service.py):
        automation/_shared.py:22
        services/__init__.py:60
        weekly_digest_service.py:344

PARALLEL (REIMPLEMENTACAO):
  app/domains/job_management/services/job_audit_service.py
    → job_vacancies/lifecycle.py:114,116,630,659,716,745

PII LEAKS (LGPD violation):
  job_vacancy_service.py:54,477,573-574 → logger.info (email, name+email)
  handlers_lifecycle.py:185,473,523 → logger.info (phone)

NO LOGGING (AUSENTE — 25+ files):
  sourcing/*_tool_registry.py (engagement, enrich, planner, search)
  wizard_system_prompt.py, sourcing_system_prompt.py
  job_management/agents/stage_context.py
  template_learning_service.py, job_analytics_prompt_service.py
  wizard_analytics_service.py, job_stage_config.py, and others
```

---

### CONCERN E: COMPLIANCE/LGPD — Entropy 55/100 (Atenção)

**Canonical:** 2 (`lgpd_cleanup_service.py` + `consent_checker_service.py`)  
**Divergences:** 6

#### E.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `lgpd_cleanup_service` | `domains/lgpd/services/lgpd_cleanup_service.py` | `RETENTION_DAYS` canonical dict | — | CANONICAL |
| `consent_checker_service` | `domains/lgpd/services/consent_checker_service.py` | Canonical consent check | — | CANONICAL |
| Inline consent creation | `api/v1/observability.py:310-320` | Creates consent record directly via repo, no service layer | `ConsentCheckerService` | REIMPLEMENTACAO |
| `ConsentRepository` | `domains/consent/repositories/consent_repository.py` | Different consent store path | `lgpd consent_checker_service` | CONFLITANTE |
| pgvector embeddings | All cleanup code | Embeddings survive right-to-erasure (ZERO deletion paths found) | LGPD Art. 18-VI | AUSENTE |
| Per-company retention | `admin_settings.py:86,88` | Configurable `data_retention_days` — NOT wired to `RETENTION_DAYS` | `RETENTION_DAYS` dict | CONFLITANTE |
| Audit retention policies | `audit_logs.py:147` | DB-backed retention policies, separate mechanism | `RETENTION_DAYS` dict | CONFLITANTE |

#### E.3 — Dependency Graph

```
CANONICAL CONSENT:
  app/domains/lgpd/services/consent_checker_service.py
    ^ via shim: shared/services/consent_checker_service.py
        → rubric_evaluation.py:27
        → candidates/_shared.py:42
        → wsi_interview_graph.py:306
        → voice_screening_orchestrator.py:72

PARALLEL CONSENT (CONFLITANTE):
  app/domains/consent/repositories/consent_repository.py
    → consent_management.py:17 (separate API, different data path)
  app/api/v1/observability.py:310-320 (inline, no service layer)

CANONICAL RETENTION:
  app/domains/lgpd/services/lgpd_cleanup_service.py
    └── RETENTION_DAYS dict (covers: rejected, withdrawn, chat_messages,
        interview_data, interview_notes, screening_logs, ai_logs, ai_decision_logs)
    ^ via shim: shared/services/lgpd_cleanup_service.py
        → api/v1/lgpd_compliance.py (erasure endpoint)
        → api/v1/admin_lgpd.py (admin view)

PARALLEL RETENTION (CONFLITANTE):
  admin_settings.py:86,88 → per-company override (not connected to RETENTION_DAYS)
  audit_logs.py:147 → DB-backed retention policies (separate mechanism)

CRITICAL AUSENTE:
  pgvector embedding tables → NOT covered by any deletion/erasure path
  (right-to-erasure invocations leave vector representations intact)
```

---

### CONCERN F: MEMORY/CONTEXT — Entropy 82/100 (Caótico)

**Canonical:** 1 (`app/domains/recruiter_assistant/services/conversation_memory.py`)  
**Divergences:** 11

#### F.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `ConversationMemory` singleton | `conversation_memory.py:849` | SQL-backed persistence | `WorkingMemoryService` (external pkg) | CONFLITANTE |
| `WorkingMemoryService` (×9 agents) | multiple `*_react_agent.py:47` | External pkg, unknown storage backend | `ConversationMemory` | CONFLITANTE |
| History limit=5 | `wizard.py:201` | Drops context after 5 turns | Limit=10 (canonical in orchestrator) | HARDCODED |
| History limit=6 | `jobs_management_assistant_service.py:60` | Drops context after 6 turns | Limit=10 (canonical) | HARDCODED |
| History limit=20 | `chat.py:856` | Retains 2× more context than peers | Limit=10 elsewhere | HARDCODED |
| History limit=30 | `conversation_memory.py:588,693` | 3× more than API history limit | API sends history[-10:] | CONFLITANTE |
| `LongTermMemoryService` | `jobs/tasks/memory.py:33` | Background async compaction | Not connected to ConversationMemory | INCOMPLETA |
| `orchestrator/memory_resolver.py` | `orchestrator/memory_resolver.py:1` | Pronoun resolution (Tier-0, regex) | `shared/memory_resolver.py` (action/intent tracking) | REIMPLEMENTACAO |
| `shared/memory_resolver.py` | `shared/memory_resolver.py:1` | Action/intent history — SAME CLASS NAME, different purpose | `orchestrator/memory_resolver.py` | REIMPLEMENTACAO |
| `ConversationStateStore` | `shared/memory/conversation_state.py:184` | Third state container | `ConversationMemory` | REIMPLEMENTACAO |
| `llm_service=None` silent skip | `main_orchestrator.py:862` | No summary generation when `llm_service=None` | `ConversationMemory` expects `llm_service` | INCOMPLETA |

#### F.3 — Dependency Graph

```
API Layer
  conversational.py:39 ──────→ ConversationMemory (direct instantiation)
  wizard.py:201 ─────────────→ ConversationMemory (history[-5:])
  agent_chat_ws.py:840,857 ──→ raw history[-10:] (NO memory service)

Orchestrator Layer
  main_orchestrator.py:862 ──→ ConversationMemory (skips silently if error)
  orchestrator.py:417 ───────→ ConversationMemory (state_manager + direct)
  orchestrator/memory_resolver.py → WorkingMemoryService (lazy import)
  shared/memory_resolver.py ──→ in-process only (no external storage)

Domain Agents (all 9 — fully disconnected from orchestrator memory):
  sourcing_react_agent.py:91 ────→ WorkingMemoryService (lia_agents_core)
  wizard_react_agent.py:47 ──────→ WorkingMemoryService
  pipeline_react_agent.py:47 ────→ WorkingMemoryService
  communication_react_agent.py:44→ WorkingMemoryService
  analytics_react_agent.py:39 ───→ WorkingMemoryService
  ats_integration_react_agent.py:44 → WorkingMemoryService
  automation_react_agent.py:37 ──→ WorkingMemoryService
  jobs_mgmt_react_agent.py:48 ───→ WorkingMemoryService
  talent_react_agent.py:48 ──────→ WorkingMemoryService

Background Jobs:
  jobs/tasks/memory.py:33 ───→ LongTermMemoryService (lia_agents_core)

DISCONNECTED SYSTEMS:
  WorkingMemoryService ≠ ConversationMemory (different backends, no sync)
  LongTermMemoryService ≠ ConversationMemory (no compaction bridge)
  ConversationStateStore ≠ any of the above
```

---

### CONCERN G: ORCHESTRATION — Entropy 72/100 (Entrópico)

**Canonical:** 1 (`main_orchestrator.py` + `CascadedRouter`)  
**Divergences:** 8

#### G.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `orchestrator.py` (legacy) | multiple | Still active, receives production traffic | `main_orchestrator.py` | CONFLITANTE |
| `enhanced_intent_classifier.py` | `domains/ai/services/enhanced_intent_classifier.py:358` | Standalone LLM intent routing | `CascadedRouter` Tier 5 | REIMPLEMENTACAO |
| `action_executor/executor.py` | `orchestrator/action_executor/executor.py:8` | "Dead code" still imported and exists | Removed action handlers | INCOMPLETA |
| `orchestrator.py` LLM calls | `orchestrator.py` (all LLM calls) | No timeout protection | `agentic_loop.py:117` (30s timeout) | AUSENTE |
| `agentic_loop.py` lazy init | `agentic_loop.py:30` | `_llm_service=None`, singleton risk | DI pattern in `orchestrator.py` | CONFLITANTE |
| `StateGraph WSI` | `wsi_interview_graph.py:937` | Custom TypedDict schema | Standard dict in `interview_graph.py` | INCOMPLETA |
| LangGraph `StateGraph Interview` | `interview_graph.py:133` | Conditional TypedDict | `job_creation/graph.py` uses typed State | INCOMPLETA |
| Manual LangChain chains | `orchestrator.py:444`, `analytics/services:496,820` | `prompt\|llm` pattern | StateGraph/ReAct pattern | REIMPLEMENTACAO |

#### G.3 — Dependency Graph

```
HTTP/WS Request
     │
     ├─→ main_orchestrator.py ──→ CascadedRouter (Tiers 0-6) ──→ DomainAgent
     │         │                      Tier 0: MemoryResolver
     │         │                      Tier 1: LRU in-process
     │         │                      Tier 2: Redis hash
     │         │                      Tier 3: VectorSemanticCache (pgvector)
     │         │                      Tier 4: FastRouter (regex)
     │         │                      Tier 5: LLMCascadeRouter
     │         │                      Tier 6: AutonomousReActAgent
     │         └──→ orchestrator.py (LEGACY, parallel path — NO TIMEOUT)
     │                    └──→ TaskPlanner → LLM (no timeout)
     │
     ├─→ agent_chat_ws.py ──→ CascadedRouter OR direct DomainAgent
     │
     └─→ sourcing_orchestrator.py ──→ SourcingReActAgent (bypasses main)
         pipeline_orchestrator.py ──→ PipelineReActAgent (bypasses main)

LangGraph StateGraphs (independent, not routed through CascadedRouter):
  job_wizard_graph.py ──→ StateGraph (standalone)
  wsi_interview_graph.py ──→ StateGraph (standalone)
  interview_graph.py ──→ StateGraph (standalone)
  job_creation/graph.py ──→ StateGraph (standalone)

ORPHANED:
  domains/ai/services/enhanced_intent_classifier.py:358 → standalone intent classifier
```

---

### CONCERN H: LLM CONFIGURATION — Entropy 88/100 (Caótico)

**Canonical:** 1 (`LLMService` via `settings.LLM_DEFAULT_TEMPERATURE` / `settings.LLM_MAX_TOKENS`)  
**Divergences:** 10+

#### H.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `LLMService` (langchain) | `domains/ai/services/llm.py` | `ChatAnthropic`/`ChatOpenAI` wrappers | `ClaudeLLMProvider` (direct SDK) | CONFLITANTE |
| `ClaudeLLMProvider` | `shared/providers/llm_claude.py` | Direct Anthropic SDK, `temperature=0.7` default | `LLMService` | CONFLITANTE |
| temperature 0.0–0.8 across 14 sites | See table below | 8 distinct hardcoded values | `settings.LLM_DEFAULT_TEMPERATURE` | HARDCODED |
| max_tokens 80–4096 across 14+ sites | See table below | 14+ distinct hardcoded values | `settings.LLM_MAX_TOKENS` | HARDCODED |
| `claude-3-5-sonnet-20241022` | `system_health.py:75` | Old naming format (SDK v0.x) | `claude-sonnet-4-6` everywhere else | CONFLITANTE |
| `gemini-2.0-flash-exp` | `gemini_voice.py:380` | Experimental model in production | `gemini-2.5-flash` canonical | HARDCODED |
| `gpt-4o` hardcoded | `domains/ai/services/llm.py:163` | Inside canonical `LLMService` class | Should read from settings | HARDCODED |
| `os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")` direct | `llm.py:74`, `wsi/_shared.py:14`, `llm_claude.py:46` | Bypasses settings layer | `settings.AI_INTEGRATIONS_*` | CONFLITANTE |
| `os.getenv("ANTHROPIC_API_KEY")` | `system_health.py:74,378` | Different env var name | `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | CONFLITANTE |
| 5 Gemini API key env var names | `system_health.py`, `admin_platform.py:204`, `llm.py` | `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_GEMINI_API_KEY`, `AI_INTEGRATIONS_GEMINI_API_KEY`, `AI_INTEGRATIONS_GEMINI_BASE_URL` | Single canonical env var name | CONFLITANTE |
| `LLMService()` new instance per loop | `agentic_loop.py:41` | Fresh instance on every ReAct loop | Singleton pattern in orchestrator | CONFLITANTE |

**Hardcoded temperature inventory:**  
0.0 (`question_generator.py:428`), 0.1 (`question_generator.py:150`, `infer_behavior_service.py:162`, `enhanced_intent_classifier.py:358`), 0.2 (`interpret_context_llm_service.py:111`), 0.3 (`kanban_assistant_service.py:86`, `jd_enrichment.py:242`), 0.7 (10+ files), 0.75 (`question_generator.py:633,701`), 0.8 (`question_generator.py:821`)

**Hardcoded max_tokens inventory:**  
80 (`jobs_management_prompts.py:114`), 100 (`kanban_assistant_service.py:86`), 300 (×3), 500 (`main_orchestrator.py:704`), 512 (`wsi/questions.py:199`), 800 (×2), 1000 (×2), 1024 (`wsi/evaluation.py:351`), 2048 (`chat.py:705`), 4000 (`jd_enrichment.py:245`), 4096 (provider defaults)

#### H.3 — Dependency Graph

```
Provider Level (2 PARALLEL SYSTEMS — CONFLITANTE):
  LLMService (langchain)              ClaudeLLMProvider (direct SDK)
    ├─ ChatAnthropic                     ├─ anthropic.Anthropic (temperature=0.7)
    ├─ ChatOpenAI (gpt-4o hardcoded)     ├─ GeminiLLMProvider (temperature=0.7)
    └─ google.genai.Client               └─ OpenAILLMProvider (temperature=0.7)
         │                                        │
    llm_service singleton               LLMProviderFactory (shared/providers)
         │                                        │
    ├─ orchestrator.py                  ├─ wsi/_shared.py
    ├─ main_orchestrator.py             ├─ experience_highlights.py
    ├─ api/v1/lia_assistant/            └─ vector_semantic_cache.py
    └─ domain services

DISCONNECTED:
  agentic_loop.py:41 → creates NEW LLMService() per call (not singleton)
  LLMCascadeRouter → uses llm_service singleton
  VectorSemanticCache → uses LLMProviderFactory (different layer)
```

---

### CONCERN I: INPUT VALIDATION — Entropy 61/100 (Entrópico)

**Canonical:** 1 (Pydantic v2 `Field` with constraints)  
**Divergences:** 8

#### I.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `InterviewSchedulingState` (schemas/) | `app/schemas/interview_scheduling_state.py:17` | Pydantic model, version A | Domain version | CONFLITANTE |
| `InterviewSchedulingState` (domains/) | `domains/interview_scheduling/schemas/interview_scheduling_state.py:17` | Pydantic model, version B (identical name) | Schemas version | CONFLITANTE |
| Chat `message: str` no limit | `orchestrated_talent_chat.py:23`, `orchestrated_job_chat.py:24`, `wizard_smart_orchestrator.py:188`, `orchestrated_jobs_management.py:73` | No `max_length` constraint → LLM | `navigation_intent.py:20` has `max_length=2000` | AUSENTE |
| `@validator` (Pydantic v1) | `api/v1/skills_catalog.py:82,88,110,112,187,194` | Old validation API | `@field_validator` (Pydantic v2) | CONFLITANTE |
| `min_items=1` (Pydantic v1) | `async_endpoints.py:37,133` | Deprecated v1 constraint | `min_length=1` in v2 | CONFLITANTE |
| `except Exception: pass` in validation | `pipeline_policy.py:71`, `wsi/evaluation.py:300` | Swallows validation errors silently | Pydantic raises by default | INCOMPLETA |
| Cross-field consent check | `consent_management.py:406` | Manual `if/else` cross-field logic | `@model_validator` Pydantic pattern | REIMPLEMENTACAO |
| Untyped `context: dict` | `candidate_search/misc_search.py:276` | `context: dict[str, Any] | None` — no schema | Typed schemas everywhere else | AUSENTE |

#### I.3 — Dependency Graph

```
Validation Layers (3 incompatible versions coexisting):

  Pydantic v2 (canonical — most endpoints):
    └─ Field(min_length=, max_length=, ge=, le=)
    └─ @field_validator (sparse adoption)

  Pydantic v1 (legacy — mixed in):
    └─ @validator → skills_catalog.py (6 call sites)
    └─ min_items= → async_endpoints.py:37,133

  Manual post-Pydantic checks:
    └─ if not x: raise HTTPException → analysis.py, consent_management.py
    └─ except Exception: pass → pipeline_policy.py:71, wsi/evaluation.py:300 (SILENT)

  Rails ActiveRecord (ats-api-copia only — more rigorous, DB-enforced):
    └─ validates :field, presence: true

SCHEMA DUPLICATION (CONFLITANTE):
  app/schemas/interview_scheduling_state.py:17
         ↕ same class name, potential drift
  app/domains/interview_scheduling/schemas/interview_scheduling_state.py:17

UNVALIDATED HIGH-RISK PATHS:
  orchestrated_talent_chat → message: str (no limit) → LLM
  orchestrated_job_chat → message: str (no limit) → LLM
  wizard_smart_orchestrator → message: str (no limit) → LLM
  orchestrated_jobs_management → message: str (no limit) → LLM
```

---

### CONCERN J: ERROR HANDLING — Entropy 91/100 (Caótico)

**Canonical:** 1 (`AgentError` + `AgentErrorCode` in `shared/robustness/error_handling.py`)  
**Adoption rate of canonical:** ~2 files out of hundreds (<1%)  
**Divergences:** 10+

#### J.2 — Divergence Matrix

| Reference | File:Line | Behavior | Diverges From | Divergence Type |
|-----------|-----------|----------|---------------|-----------------|
| `AgentError` (defined, unused) | `shared/robustness/error_handling.py:67` | Canonical base class | Used in ~2 files only | INCOMPLETA |
| 24+ domain exception classes | VoiceServiceError, MultimodalServiceError, GraphAPIError hierarchy, WSIValidationError, etc. | Custom exceptions NOT extending `AgentError` | `AgentError` canonical | REIMPLEMENTACAO |
| `HTTPException(500, detail=str(e))` | `briefing.py:44,64` | Raw internal exception string exposed to client | Should sanitize `detail` | VERBAL |
| `HTTPException(400, detail=str(e))` | `voice.py:115,169,232` | Raw exception string to client (×3) | Sanitized error messages | VERBAL |
| Dict `{"success": False, "error": str(e)}` | `orchestrator.py:289,328` | Non-HTTP dict response format | `HTTPException` convention | CONFLITANTE |
| Dict format in action handlers | `analytics actions:165,269,360` | Same dict format | `HTTPException` convention | CONFLITANTE |
| `except Exception: pass` (silent) | `pipeline_policy.py:71-72` | Policy evaluation bypass — no log | Should raise or log + respond | AUSENTE |
| `except Exception: pass` (silent) | `wsi/evaluation.py:300-301` | WSI evaluation skipped — no log | Should raise or log + respond | AUSENTE |
| `except Exception: pass` (silent) | `conversational.py:246-247,348-349` | Memory write silently skipped (×2) | Should log at WARNING | AUSENTE |
| `except Exception: pass` (silent) | `twilio_voice.py:513-514` | Voice event silently lost | Should log | AUSENTE |
| `except Exception: pass` (silent) | `platform_event_handlers.py:272-273` | Platform event silently lost | Should log | AUSENTE |
| `except Exception: pass` (silent) | `orchestrator/pending_action.py:86` | State save silently fails | Should log | AUSENTE |
| `except Exception: pass` (silent) | `orchestrator/policy_engine.py:129,188,193` | Policy check bypass (×3) | Should raise | AUSENTE |
| Celery retry max=2 | `jobs/tasks/agents.py:12` | 2 retries | `webhook_tasks.py` max=3 | CONFLITANTE |
| Manual retry for-loop | `wsi/reports.py:309` | `for attempt in range(1, 4)` | Should use `tenacity` | REIMPLEMENTACAO |
| `simulated="simulated"` (string) | `resend_provider.py:87`, `mailgun_provider.py:100` | String status value | `simulated=False` boolean in action handlers | CONFLITANTE |

#### J.3 — Dependency Graph

```
Exception Hierarchy (FRAGMENTED):

  Canonical (UNDERUSED — <1% adoption):
    AgentError (shared/robustness/error_handling.py:67)
      └─ used by: ~2 files only
      └─ AgentErrorCode (StrEnum) : defined, rarely referenced

  Domain-Specific (24+ classes, NOT extending AgentError):
    VoiceServiceError → TranscriptionError, SynthesisError
    MultimodalServiceError → ImageAnalysisError, VideoAnalysisError, DocumentAnalysisError
    GraphAPIError → 5 subclasses
    PolicyDenied, PolicyApprovalRequired
    WSIValidationError, TransitionError, CycleDetectedError
    RequestBudgetExceededError, EncryptionKeyMissingError
    TwilioVoiceError, OpenMicError, DeepgramError
    GeminiLiveAudioError, VoiceScreeningOrchestratorError
    RailsCompanyResolutionError

HTTP Response Formats (3 INCOMPATIBLE):
  FastAPI HTTPException (status.HTTP_xxx) → API consumers (canonical)
  HTTPException (numeric 500/400) → admin.py, briefing.py, voice.py
  {"success": False, "error": "..."} → orchestrator.py, analytics actions

Retry Strategies (3 INCOMPATIBLE):
  Celery @task(max_retries=2) → jobs/tasks/agents.py
  Celery @task(max_retries=3, countdown=60) → jobs/webhook_tasks.py
  Manual for-loop range(1,4) → wsi/reports.py:309
  (No tenacity library usage found anywhere)

Silent Failure Paths (16+ confirmed):
  pipeline_policy.py:71 → pass (POLICY BYPASS)
  wsi/evaluation.py:300 → pass (EVALUATION SKIP)
  conversational.py:246-247,348-349 → pass (MEMORY NOT WRITTEN ×2)
  policy_engine.py:129,188,193 → pass (POLICY CHECK BYPASS ×3)
  twilio_voice.py:513-514 → pass (VOICE EVENT LOST)
  platform_event_handlers.py:272-273 → pass (PLATFORM EVENT LOST)
  pending_action.py:86 → pass (STATE SAVE LOST)
  contact.py:185-186 → pass (CONTACT UPDATE LOST)
  search.py:239-240 → pass (SEARCH STEP LOST)
  jobs_ws.py:151-152,156-157 → pass (WS CLEANUP ×2)
  insights.py:322-323 → logger.debug (COMPLIANCE CHECK SKIPPED)
  wsi_async.py:155-156 → logger.debug (REDIS UPDATE LOST)
  wizard_smart_orchestrator.py:538-539 → logger.debug (DRAFT AUTOSAVE LOST)
```

---

## 4. MASTER DIVERGENCE MATRIX

Combined all-concerns table, sorted by severity:

| Severity | Concern | Reference | File:Line | Diverges From | Divergence Type |
|----------|---------|-----------|-----------|---------------|-----------------|
| CRÍTICO | E | pgvector embeddings never deleted | All cleanup code | LGPD Art. 18-VI right-to-erasure | AUSENTE |
| CRÍTICO | J | `policy_engine.py` silent catches | `policy_engine.py:129,188,193` | Policy must evaluate | AUSENTE |
| CRÍTICO | J | `pipeline_policy.py` silent catch | `pipeline_policy.py:71-72` | Policy must evaluate | AUSENTE |
| CRÍTICO | J | `AgentError` ~1% adoption | codebase-wide (4,858 except blocks) | `shared/robustness/error_handling.py:67` | INCOMPLETA |
| CRÍTICO | H | Claude model version skew | `system_health.py:75` (`claude-3-5-sonnet-20241022`) | `claude-sonnet-4-6` everywhere else | CONFLITANTE |
| CRÍTICO | H | Two parallel LLM abstraction layers | `llm.py` vs `shared/providers/llm_*.py` | Single canonical provider | CONFLITANTE |
| CRÍTICO | F | 5 incompatible memory systems | SQL + WorkingMemory + LongTerm + in-process + ConversationState | `ConversationMemory` canonical | CONFLITANTE |
| CRÍTICO | F | Domain agents disconnected from orchestrator memory | All `*_react_agent.py:47` (×9) | `ConversationMemory` | CONFLITANTE |
| HIGH | D | PII email in logs | `job_vacancy_service.py:54,477,573-574` | LGPD data minimization | CONFLITANTE |
| HIGH | D | PII phone in logs | `handlers_lifecycle.py:185,473,523` | LGPD data minimization | CONFLITANTE |
| HIGH | B | `SOURCING_SYSTEM_PROMPT` in Python | `sourcing_system_prompt.py:126` | `lia_persona.yaml` | REIMPLEMENTACAO |
| HIGH | B | `WIZARD_SYSTEM_PROMPT` in Python | `wizard_system_prompt.py:148` | `lia_persona.yaml` | REIMPLEMENTACAO |
| HIGH | G | Legacy orchestrator (no LLM timeout) | `orchestrator.py` (all LLM calls) | `agentic_loop.py:117` 30s timeout | AUSENTE |
| HIGH | J | Raw `str(e)` to API clients | `briefing.py:44,64`, `voice.py:115,169,232` | Sanitized error messages | VERBAL |
| HIGH | I | Chat message inputs unvalidated | `orchestrated_talent_chat.py:23`, `orchestrated_job_chat.py:24`, `wizard_smart_orchestrator.py:188`, `orchestrated_jobs_management.py:73` | `navigation_intent.py` `max_length=2000` | AUSENTE |
| HIGH | J | `wsi/evaluation.py` silent catch | `wsi/evaluation.py:300-301` | Evaluation must not be skipped | AUSENTE |
| HIGH | J | `conversational.py` memory write silent | `conversational.py:246-247,348-349` | Memory must be persisted | AUSENTE |
| HIGH | H | 5 Gemini API key env var names | `system_health.py`, `admin_platform.py:204` | `AI_INTEGRATIONS_GEMINI_API_KEY` | CONFLITANTE |
| HIGH | F | History truncation: 5 different values | `wizard.py:201`(5), `jobs_mgmt.py:60`(6), `chat.py:856`(20), `conversation_memory.py:588,693`(30) | `orchestrator.py:417`(10) | HARDCODED |
| MEDIUM | C | `FOUR_FIFTHS_THRESHOLD` duplicate | `admin_compliance_fairness.py:41` | `bias_audit_service.py:49` | REIMPLEMENTACAO |
| MEDIUM | C | `_compute_four_fifths()` duplicate | `admin_compliance_fairness.py:139-198` | `BiasAuditService.compute_adverse_impact()` | REIMPLEMENTACAO |
| MEDIUM | E | Two consent stacks | `domains/consent/repositories/consent_repository.py` | `consent_checker_service.py` | CONFLITANTE |
| MEDIUM | E | Inline consent creation | `observability.py:310-320` | `ConsentCheckerService` | REIMPLEMENTACAO |
| MEDIUM | E | Per-company retention not wired | `admin_settings.py:86,88` | `RETENTION_DAYS` dict | CONFLITANTE |
| MEDIUM | G | Legacy orchestrator still active | `orchestrator.py` | `main_orchestrator.py` | CONFLITANTE |
| MEDIUM | G | Orphaned intent classifier | `enhanced_intent_classifier.py:358` | `CascadedRouter` Tier 5 | REIMPLEMENTACAO |
| MEDIUM | D | `job_audit_service` parallel track | `job_management/services/job_audit_service.py` | `AuditService` | REIMPLEMENTACAO |
| MEDIUM | I | `InterviewSchedulingState` duplicated | `schemas/interview_scheduling_state.py:17` AND `domains/interview_scheduling/schemas/.../17` | Single schema | CONFLITANTE |
| MEDIUM | J | 24+ domain exceptions not extending `AgentError` | VoiceServiceError hierarchy, MultimodalServiceError, GraphAPIError, etc. | `AgentError` base | REIMPLEMENTACAO |
| MEDIUM | J | 3 incompatible HTTP response formats | `HTTPException(status.)`, `HTTPException(500)`, `{"success":False}` | Single format | CONFLITANTE |
| MEDIUM | H | `temperature` 8 hardcoded values | 14 distinct file:line sites | `settings.LLM_DEFAULT_TEMPERATURE` | HARDCODED |
| MEDIUM | H | `max_tokens` 14+ hardcoded values | 14+ distinct file:line sites | `settings.LLM_MAX_TOKENS` | HARDCODED |
| MEDIUM | B | 12+ "Voce e um especialista" prompts | `wsi/questions.py:166`, `wsi/reports.py:248`, `archetypes.py:1162,1280`, `company.py:426,701,865`, `email_templates.py:735,828`, `jd_generator_service.py:228,374,436`, etc. | `lia_persona.yaml` ethical guidelines | REIMPLEMENTACAO |
| LOW | A | Guardrail DB rules not linked to FG | `guardrails_seed.py:34-35,97` | `DISCRIMINATORY_CATEGORIES` | HARDCODED |
| LOW | A | Onboarding plain-text fairness rule | `onboarding_prompts.py:25` | `FairnessGuard` runtime check | VERBAL |
| LOW | D | 25+ domain files with no logging | sourcing/*_tool_registry.py + 21 others | Audit trail requirement | AUSENTE |
| LOW | C | Partial protected attributes list | `guardrails_seed.py:97` (3 items only) | `audit_service.PROTECTED_CRITERIA` (10 items) | INCOMPLETA |
| LOW | F | `MemoryResolver` name collision | `orchestrator/memory_resolver.py` vs `shared/memory_resolver.py` | Different purposes, same name | REIMPLEMENTACAO |
| LOW | J | Celery retry inconsistency | `agents.py:12` max=2 vs `webhook_tasks.py` max=3 | Consistent retry policy | CONFLITANTE |
| LOW | I | Pydantic v1/v2 mixing | `skills_catalog.py:82` `@validator`, `async_endpoints.py:37` `min_items=` | Pydantic v2 canonical | CONFLITANTE |

---

## 5. PRIORITY ACTION LIST

Top 10 remediation actions ordered CRÍTICO → HIGH → MEDIUM → LOW:

---

### ACTION 1 — CRÍTICO | Effort: M
**Add pgvector embedding deletion to LGPD erasure path**

- File: `app/domains/lgpd/services/lgpd_cleanup_service.py`
- Fix: In `schedule_deletion_for_candidate()`, after deleting relational data, issue a DELETE against all pgvector embedding tables (candidate embeddings, RAG document vectors) scoped by `candidate_id`. Add to `RETENTION_DAYS` dict a `"embeddings"` key. Verify via `app/tests/test_lgpd_compliance_gaps.py`.
- Risk if unresolved: LGPD Art. 18-VI violation — right-to-erasure not honored for vector representations.

---

### ACTION 2 — CRÍTICO | Effort: L
**Eliminate silent catches on policy and evaluation paths**

- Files: `app/orchestrator/policy_engine.py:129,188,193` | `app/api/v1/pipeline_policy.py:71-72` | `app/api/v1/wsi/evaluation.py:300-301`
- Fix: Replace all `except Exception: pass` with `except Exception as e: logger.error(...); raise` or a structured `AgentError`. Policy evaluation and WSI scoring must NEVER silently fail. Silent bypass creates an exploitable path to skip compliance checks.
- Risk if unresolved: Policy rules can be bypassed in production with no trace in audit logs.

---

### ACTION 3 — CRÍTICO | Effort: L
**Adopt `AgentError` as the universal exception base across all 24+ domain exception classes**

- Files: `app/shared/robustness/error_handling.py:67` (canonical) + all domain exception files
- Fix: All custom exceptions (`VoiceServiceError`, `MultimodalServiceError`, `GraphAPIError` hierarchy, `WSIValidationError`, `PolicyDenied`, etc.) must inherit from `AgentError`. Standardize HTTP response format to `HTTPException` with `status.HTTP_xxx` constants. Remove raw `str(e)` in `detail=` — replace with sanitized message + log full exception internally.
- Risk if unresolved: 4,858 exception blocks, 16+ silent catches, 3 incompatible response formats — impossible to build consistent error monitoring.

---

### ACTION 4 — CRÍTICO | Effort: M
**Fix Claude model version skew and consolidate LLM configuration to settings**

- Files: `app/api/v1/system_health.py:75` (change `claude-3-5-sonnet-20241022` → `claude-sonnet-4-6`) | `app/domains/ai/services/llm.py:163` (remove hardcoded `gpt-4o`) | all 14 temperature hardcoded sites | all 14+ max_tokens hardcoded sites
- Fix: Introduce `settings.LLM_TEMPERATURE_PRECISE` (0.0–0.2), `settings.LLM_TEMPERATURE_CREATIVE` (0.7–0.8), `settings.LLM_TEMPERATURE_DEFAULT` (0.3–0.5). Replace all hardcoded values. Consolidate 5 Gemini API key env var names to a single `AI_INTEGRATIONS_GEMINI_API_KEY`.
- Risk if unresolved: Model version skew causes inconsistent behavior in production. Ungoverned temperature/token values make LLM outputs non-deterministic and unauditable.

---

### ACTION 5 — HIGH | Effort: M
**Mask PII in all logger.info() calls (LGPD compliance)**

- Files: `app/domains/job_management/services/job_vacancy_service.py:54,477,573,574` | `app/api/v1/automation/event_handlers/handlers_lifecycle.py:185,473,523`
- Fix: Replace `{email}`, `{name}`, `{phone}` in log strings with masked versions: `email[:3]***@domain.com`, `phone[-4:]***`. Or use a `mask_pii()` utility. These are `logger.info()` calls — PII goes into application logs that may be shipped to third-party observability platforms.
- Risk if unresolved: LGPD violation — personal data in application logs constitutes unauthorized processing.

---

### ACTION 6 — HIGH | Effort: M
**Migrate ReAct agent system prompts to SystemPromptBuilder**

- Files: `app/domains/sourcing/agents/sourcing_system_prompt.py:126` | `app/domains/job_management/agents/wizard_system_prompt.py:148`
- Fix: Replace `SOURCING_SYSTEM_PROMPT` and `WIZARD_SYSTEM_PROMPT` Python constants with calls to `SystemPromptBuilder.build(domain="sourcing", ...)` and `SystemPromptBuilder.build(domain="wizard", ...)` referencing `lia_persona.yaml`. The 12+ "Voce e um especialista" prompts in task-specific LLM calls should at minimum include the `ethical_guidelines` section from `lia_persona.yaml`.
- Risk if unresolved: Sourcing and wizard agents operate with a different LIA identity and ethics policy than the rest of the platform.

---

### ACTION 7 — HIGH | Effort: S
**Add max_length validation to all chat/orchestration message inputs**

- Files: `app/api/v1/orchestrated_talent_chat.py:23` | `app/api/v1/orchestrated_job_chat.py:24` | `app/api/v1/wizard_smart_orchestrator.py:188` | `app/api/v1/orchestrated_jobs_management.py:73`
- Fix: Add `message: str = Field(..., min_length=1, max_length=10000)` to each request schema. Reference pattern: `app/api/v1/navigation_intent.py:20` which uses `max_length=2000`.
- Risk if unresolved: Unbounded chat inputs can be used to inject oversized prompts or exhaust LLM context windows.

---

### ACTION 8 — MEDIUM | Effort: S
**Eliminate `FOUR_FIFTHS_THRESHOLD` duplicate and merge `_compute_four_fifths()`**

- Files: `app/api/v1/admin_compliance_fairness.py:41,139-198`
- Fix: Remove `FOUR_FIFTHS_THRESHOLD = 0.80` from `admin_compliance_fairness.py` — import from `bias_audit_service.py`. Remove `_compute_four_fifths()` — call `BiasAuditService.compute_adverse_impact()` instead.
- Risk if unresolved: If the threshold value changes in one place, the admin dashboard silently uses a stale value.

---

### ACTION 9 — MEDIUM | Effort: L
**Consolidate the three parallel memory systems**

- Files: `app/domains/recruiter_assistant/services/conversation_memory.py` (canonical) | All `*_react_agent.py:47` (×9) | `app/orchestrator/memory_resolver.py` | `app/shared/memory/conversation_state.py`
- Fix: Define a `MemoryAdapter` interface in `app/shared/memory/`. Implement `ConversationMemoryAdapter` wrapping the existing SQL system. Migrate all domain ReAct agents from `WorkingMemoryService` to use this adapter. Standardize history truncation to a single constant `HISTORY_WINDOW = 10` imported from `app/core/config.py`.
- Risk if unresolved: Context from orchestrator-level conversations is invisible to domain agents. Agents cannot build on prior decisions. Users experience amnesia across agent handoffs.

---

### ACTION 10 — MEDIUM | Effort: M
**Consolidate dual consent stacks and wire `admin_settings.data_retention_days` to `RETENTION_DAYS`**

- Files: `app/api/v1/observability.py:310-320` | `app/domains/consent/repositories/consent_repository.py` | `app/api/v1/admin_settings.py:86,88`
- Fix: Replace inline consent creation in `observability.py:310-320` with a call to `ConsentCheckerService`. Audit whether `consent_repository.py` and `consent_checker_service.py` serve different data models — if not, consolidate to one. Wire `admin_settings.data_retention_days` override to actually modify the `RETENTION_DAYS` dict at runtime (or document clearly that it's a separate DB-level config).
- Risk if unresolved: Two consent stacks can produce divergent consent records for the same candidate. LGPD audit trail becomes unreliable.

---

*Report generated by P13 Forensic Audit synthesis pass — 2026-04-14*
*Sources: P13_A_CONCERNS.md (Concerns A–E) + P13_B_CONCERNS.md (Concerns F–J)*
*All file:line citations verified by sub-agents via exhaustive SSH grep and file reads on live codebase*
