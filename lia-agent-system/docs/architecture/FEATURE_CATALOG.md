# WeDOTalent AI Feature Catalog
**Versão:** 2026-06-17
**Objetivo:** Guia completo de todas as funcionalidades com IA da plataforma WeDOTalent — entrada, fluxo, status e pontos de extensão. Voltado para desenvolvedores que precisam entender, replicar ou estender features existentes.

## Status Legend
- 🟢 **Live** — Funcional em produção, totalmente fiado de ponta a ponta
- 🟡 **Partial** — Implementado mas com gaps (uma perna do loop ausente, ghost settings, flag dormant)
- 🔴 **Ghost** — Definido/registrado mas sem consumidor real ativo no caminho de produção

---

## Table of Contents

| # | Feature | Status |
|---|---------|--------|
| F-01 | Chat Routing & Federation — CascadedRouter + recruiter_copilot | 🟢 |
| F-02 | AI Persona Customization per Tenant | 🟢 |
| F-03 | Company AI Field Toggles (lia_field_toggles) | 🟢 |
| F-04 | Job Wizard — Intake Derivation & Company Data Injection | 🟢 |
| F-05 | BigFive Department Learning Loop | 🟢 |
| F-06 | JD Similar History — Vector Embedding Learning | 🟡 |
| F-07 | ATS / JD Import with NLP Parsing | 🟢 |
| F-08 | Salary Benchmark with Provenance | 🟡 |
| F-09 | WSI Screening Flow (Work Style Inventory) | 🟢 |
| F-10 | Eligibility Questions Flow | 🟢 |
| F-11 | Inline Chat (Text Selection / Hover / BTW) | 🟢 |
| F-12 | Comparative Candidate Analysis (D9) | 🟢 |
| F-13 | Task Planner / Plan-and-Execute | 🔴 |
| F-14 | HITL (Human-in-the-Loop) Gates | 🟡 |
| F-15 | FairnessGuard Integration | 🟢 |
| F-16 | Voice Data Collection (Twilio + Gemini Live) | 🟢 |
| F-17 | Agent Studio — Custom & Marketplace Agents | 🟢 |
| F-18 | Digital Twin Agents | 🟡 |
| F-19 | Proactive Layer & Autonomous Alerts | 🟡 |
| F-20 | PII Field Visibility by Role | 🟢 |
| F-21 | WSI Question Effectiveness Learning Loop | 🟡 |
| F-22 | Calibration Event Learning | 🟢 |
| F-23 | A/B Testing for Email Templates | 🟢 |
| F-24 | Implicit Feedback from Chat Behavior | 🟢 |
| F-25 | Job Creation Wizard Orchestrator | 🟢 |
| F-26 | Sourcing / Talent Search | 🟢 |
| F-27 | Offer Concierge Flow | 🟢 |
| F-28 | Slash Commands in Unified Chat | 🟢 |
| F-29 | Reasoning / Activity Display | 🟢 |
| F-30 | Token Budget & Rate Limiting | 🟢 |

---

## F-01 · Chat Routing & Federation — CascadedRouter + recruiter_copilot

**Status:** 🟢 Live
**Business Value:** Routes every recruiter message to the correct specialist agent or cached response without requiring manual domain selection. With LIA_FEDERATED_PRIMARY=true (active in dev), a single omniscient agent handles all recruiter pages, eliminating the old split-brain between kanban and talent views.

**Entry Point:** `app/api/v1/agent_chat_sse.py:488` (SSE handler, understanding phase emission before routing)

**Trigger:** POST `/api/v1/chat/{session_id}/stream` from any recruiter chat surface (unified-chat, kanban lateral panel, talent funnel panel, wizard)

**Key Files:**
- `app/api/v1/agent_chat_sse.py` — SSE transport, FairnessGuard pre-check, budget gate, routing decision
- `app/orchestrator/routing/cascaded_router.py` — 8-tier routing pipeline, singleton `get_router()`
- `app/orchestrator/routing/fast_router.py` — Tier 4: regex/keyword matching
- `app/orchestrator/routing/llm_cascade.py` — Tier 5: Haiku→Sonnet→Opus LLM classification
- `app/orchestrator/memory/memory_resolver.py` — Tier 0: pronoun/reference resolution
- `app/orchestrator/services/rail_a_hint_override.py` — FE-H03 domain_hint short-circuit
- `app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py` — Federated agent (35 tools)
- `app/orchestrator/execution/main_orchestrator.py` — Supervisor path (LIA_BUBBLE_VIA_SUPERVISOR)

**Data Flow:**
```
POST /chat/{session_id}/stream
  → [1] FairnessGuard.check(message) — HTTP 400 if discriminatory
  → [2] check_budget(company_id) — SSE budget_exhausted if exceeded
  → [3] detect HITL approval (approve_pending_id in body?)
  → [4] if domain=='wizard' → WizardOrchestrator path
  → [5] if LIA_FEDERATED_PRIMARY=true → RecruiterCopilotReActAgent (35 tools)
  → [6] elif LIA_BUBBLE_VIA_SUPERVISOR → MainOrchestrator.process()
  → [7] else → CascadedRouter.route():
       Tier 0: memory_resolver (pronoun resolution, per session_id)
       Rail A: try_hint_route (domain_hint from FE metadata)
       Tier 1: LRU in-process MD5 cache
       Tier 2: Redis distributed cache
       Tier 3: VectorSemanticCache (pgvector cosine >= 0.85)
       Tier 4: FastRouter (regex/keyword)
       Tier 5: LLM Cascade (Haiku→Sonnet→Opus)
       Tier 8 fallback: clarification_needed (option chips to FE)
  → RouteResult → domain agent → SSE frames (thinking/token/tool_started/message)
```

**Key Details:**
- **LIA_FEDERATED_PRIMARY=true** is active in `.env` line 182. In this mode CascadedRouter is repurposed as *scope provider* (dynamic ~15 tools/turn for cost), not agent selector.
- **LIA_BUBBLE_VIA_SUPERVISOR** status unknown in current `.env` grep — check before toggling.
- Tier 6 (AutonomousReActAgent cross-domain fallback) was **removed** Sprint 12.3-B. No `AUTONOMOUS_REACT_AGENT` env set in prod.
- Rail A hint short-circuits all tiers when FE sends `domain_hint` in SSE request `context` metadata.
- SSE keepalive every 15s of silence via `_drain_queue_with_keepalive` prevents 502 on long operations (WSI question generation can take ~100s).
- Wizard session-pin was removed from router (Task #1080) — now lives in SSE/WS handlers.
- Router stats available: `_stats` dict tracking hits per tier.
- `_pii_identity_cache` in `agent_chat_sse.py` with TTL=300s caches PII identity resolution to avoid redundant DB calls per turn.

**Related Features:** F-03, F-14, F-15, F-25, F-29, F-30

---

## F-02 · AI Persona Customization per Tenant

**Status:** 🟢 Live
**Business Value:** Allows each company to name their AI assistant (e.g., "Sofia") and set its conversational tone, making the platform feel branded without exposing LGPD/ethics guardrails to modification.

**Entry Point:** `app/api/v1/company_ai_persona.py` (client-facing REST), `app/api/v1/admin_prompts.py` (staff YAML editing)

**Trigger:** PUT `/api/v1/company-ai-persona` by authenticated recruiter (client tab "Personalidade da IA"); PUT `/api/v1/admin/prompts/tenant-overrides/{path}` by wedotalent_admin only

**Key Files:**
- `app/domains/persona/services/ai_persona_validator.py` — single source of truth for name + tone validation
- `app/domains/persona/services/ai_persona_service.py` — read/update with audit trail
- `app/domains/persona/services/tenant_persona_validator.py` — YAML-level validation (admin only)
- `app/shared/prompts/system_prompt_builder.py` — `_append_ai_persona_override()` injects at line ~75
- `plataforma-lia/src/components/settings/AiPersonaPanel.tsx` — client UI
- `plataforma-lia/src/hooks/company/use-ai-persona.ts` — canonical FE hook

**Data Flow:**
```
Client PUT /api/v1/company-ai-persona {name, tone}
  → ai_persona_validator.validate_persona(name, tone)
       Name: 2-20 chars, alphanum+PT-BR accents, blocklist (claude/chatgpt/gemini etc.)
       Tone: must be in CANONICAL_AI_TONES (6 values: profissional/amigavel/formal/casual/formal_amigavel/empatico)
  → ai_persona_service.update_ai_persona()
       Write: CompanyHiringPolicy.communication_rules.ai_persona = {name, tone}  (PT-BR, for chat)
       Sync:  communication_rules.lia_tone = TONE_PT_TO_EN_LEGACY[tone]          (EN, for outbound)
       Audit: AuditService.log_decision(action='ai_persona_update', prev, next)
  → SystemPromptBuilder.build(ai_persona={name, tone})
       _append_ai_persona_override() appends "Override Persona" + "Tom Customizado" sections
       lia_persona.yaml base is NEVER mutated — append-only pattern
```

**Key Details:**
- `DEFAULT_AI_NAME='LIA'`, `DEFAULT_AI_TONE='profissional'`. Cold-start tenants receive these without a DB row.
- `CANONICAL_AI_TONES` tuple has exactly 6 values. Adding a new tone requires commit to validator AND mirror in `use-ai-persona.ts` (TS canonical types).
- Brand blocklist uses substring case-insensitive: catches 'MyClaude', 'GPT-4 Pro', etc. Defined as `_RESERVED_BRAND_TOKENS`.
- `lia_persona.yaml` base contains LGPD/fairness/anti-bias ethics blocks that are **immutable by clients**. Override only appends, never replaces.
- Admin staff editing via YAML (`admin_prompts.py`) is role-gated to `UserRole.wedotalent_admin`. Client only sees the name+tone subset.
- **CONSENT_QUESTION in voice plugins** (`DataCollectionVoicePlugin`) must never use `ai_persona.name` as controller name — hardcoded 'WeDOTalent' per LGPD Art. 7/9.
- Sensors: `tests/contract/test_ai_persona_*.py` (67+ tests).

**Related Features:** F-03, F-09, F-16

---

## F-03 · Company AI Field Toggles (lia_field_toggles)

**Status:** 🟢 Live
**Business Value:** Allows companies to control which of their 34 configured data fields (mission, values, tech_stack, EVP, etc.) the AI agents consume when building prompts. Toggles field injection without removing data from the DB.

**Entry Point:** `app/shared/services/lia_agent_context_builder.py` — `build_company_agent_context()`

**Trigger:** Called by ~25 agent/service files whenever they build a system prompt that should include company configuration context.

**Key Files:**
- `libs/models/lia_models/lia_field_toggles.py` — SQLAlchemy model (table: `lia_field_toggles`), `DEFAULT_FIELD_TOGGLES` (34 fields, all default True), `FIELD_FALLBACK_CONFIG`
- `app/domains/cv_screening/services/lia_field_config_service.py` — `LiaFieldConfigService`: filters active fields, enriches with per-field recruiter instructions
- `app/shared/services/lia_agent_context_builder.py` — `build_company_agent_context()`: cross-domain shim (~25 consumers)
- `app/domains/ai/services/context_aggregator_service.py` — `AggregatedContext.lia_filtered_prompt` populated on load
- `plataforma-lia/src/components/settings/LiaFieldsConfigPanel.tsx` — UI: 34 toggles + instruction text areas

**Data Flow:**
```
Agent builds system prompt
  → build_company_agent_context(company_id, db, job_context?)
       → LiaFieldConfigService.get_filtered_fields(company_id)
            Query lia_field_toggles WHERE company_id AND is_active=True
            Apply DEFAULT_FIELD_TOGGLES for cold-start tenants
       → For each active field: fetch CompanyCultureProfile value
            If field has lia_instructions set → append "_Instrução do recrutador: ..._"
       → Returns markdown sections:
            "Campos Configurados pela Empresa"    (active, has data)
            "Campos com Dados Alternativos"       (active, using fallback strategy)
            "Campos Indisponíveis"                (toggle OFF)
            "Instruções Específicas do Recrutador"
  → Injected into system prompt as context block
```

**Key Details:**
- Toggle controls **AI DATA CONSUMPTION only**, not UI visibility. Field data persists in DB regardless.
- 34 fields with `skip` fallback strategy (informational-only): `trade_name`, `industry`, `website`, `mission`, `vision`, `values`, `engineering_culture`, `company_big_five`, `growth_opportunities`, `dei_initiatives`, `sustainability`, `social_impact`, `evp_bullets`, etc.
- `FIELD_FALLBACK_CONFIG` maps each `field_key` to ordered fallback strategy list: `['job_history', 'market_benchmark', 'role_inference', 'skip']`.
- Context aggregator integration: `context_aggregator_service.py` populates `AggregatedContext.lia_filtered_prompt` on load and appends via `to_prompt_context()`. Existing callers of `ContextAggregatorService.get_full_context` get filtering **automatically**.
- REST API: `GET/PATCH /api/v1/companies/{company_id}/learning-loops-config` also governs adjacent learning toggles.
- Audit 2026-05-21 closed P0-1: before this service, all 34 toggles were inert (no agents read them).

**Related Features:** F-02, F-04, F-25

---

## F-04 · Job Wizard — Intake Derivation & Company Data Injection

**Status:** 🟢 Live
**Business Value:** Pre-fills wizard fields with intelligent suggestions derived from company configuration and the job title/email, reducing manual data entry and keeping company-wide salary bands and culture data consistent across vacancies.

**Entry Point:** `app/domains/job_creation/nodes/intake.py:297` — `intake_node()` execution with `_derive_intake_suggestions()` at line 155

**Trigger:** First step of Job Creation Wizard when recruiter initiates a new vacancy

**Key Files:**
- `app/domains/job_creation/nodes/intake.py` — `_derive_intake_suggestions()` (line 155), `_infer_from_title()`, `_derive_name_from_email()`
- `app/domains/job_creation/orchestrator/wizard_orchestrator.py` — `WizardOrchestrator.process_turn()`
- `app/domains/job_creation/services/wizard_session_service.py:987` — LIA_WIZARD_ORCHESTRATOR flag check
- `app/domains/job_creation/services/bigfive_service.py:187` — `get_blend_weights()` for BigFive injection at bigfive_node
- `app/shared/services/lia_agent_context_builder.py` — company context injected into system prompt

**Data Flow:**
```
Recruiter starts wizard
  → WizardSessionService checks LIA_WIZARD_ORCHESTRATOR=1 → WizardOrchestrator path
  → intake_node(state):
       _derive_intake_suggestions(title, email):
         seniority ← _infer_from_title(title) if confidence >= 0.8 (SENIORITY_DISPLAY_NAMES mapping)
         manager_name ← _derive_name_from_email(email prefix)
         Returns (seniority, seniority_inferred=True, manager_name, name_suggested=True)
       Flags: seniority_inferred=True, name_suggested=True → FE renders as editable suggestion
  → build_company_agent_context() injected into system prompt
       → LiaFieldConfigService filters 34 toggles for this company
       → mission/values/tech_stack/etc. as context
  → At bigfive_node: BigFiveDepartmentService.get_blend_weights() blends dept history
  → salary_node: match_from_bands() resolves company salary bands → pre-fills salary range
```

**Key Details:**
- Derivation uses **real signals only** (title text, email prefix) — never fabricates from LLM parametric knowledge without signal. `name_suggested=True` flag tells FE to render as suggestion, not confirmed value.
- Seniority inference threshold: `confidence >= 0.8` prevents low-confidence overrides.
- Manager name from email: `_derive_name_from_email(email_prefix)` at line 45 of intake.py.
- Salary band inheritance: `match_from_bands()` in `crud.py` resolves `company_salary_bands` without N+1 queries. Source tagged as `source=company_salary_band`, `inherited=True`.
- Wizard stages: `intake → jd_enrichment → jd_gate → bigfive → competency → wsi_questions → eligibility → salary → configure_publish → review`.
- Legacy LangGraph nodes (`nodes/publish.py`, `nodes/review.py`, `nodes/calibration.py`) are **tombstoned** with `RuntimeError` when `RAILS_API_URL` is absent (which it is in dev).

**Related Features:** F-03, F-05, F-25

---

## F-05 · BigFive Department Learning Loop

**Status:** 🟢 Live
**Business Value:** Over time, biases WSI behavioral question targets toward the OCEAN personality profile of previously successful (hired) candidates in the same department and seniority, improving candidate-role fit prediction per company.

**Entry Point:** `app/domains/communication/services/transition_dispatch_service.py:1035` — `_record_bigfive_hire()` inside `_hook_conclusion_hired()`

**Trigger:** `action_behavior='conclusion_hired'` platform event dispatched when a candidate is moved to the hired stage

**Key Files:**
- `app/domains/communication/services/transition_dispatch_service.py` — `_hook_conclusion_hired()` (line 815), `_record_bigfive_hire()` (line 1069)
- `app/domains/job_creation/services/bigfive_service.py` — `BigFiveDepartmentService`: `record_hire()` (line 304), `get_blend_weights()` (line 187)
- `app/domains/job_creation/nodes/bigfive.py` — `bigfive_node()`: reads `get_blend_weights()` for WSI rank_traits
- `libs/models/lia_models/bigfive_department_profiles.py` — `bigfive_department_profiles` table

**Data Flow:**
```
Candidate moved to conclusion_hired
  → TransitionDispatchService.dispatch() → _hook_conclusion_hired()
  → _record_bigfive_hire(candidate_id, vacancy_id, company_id):
       Read LiaOpinion.behavioral_analysis['ocean_traits'] (OCEAN floats 0-1, from WSI)
       → BigFiveDepartmentService.record_hire(company_id, dept, seniority, ocean_traits)
            Welford online algorithm: updates running mean+variance for 5 OCEAN traits
            Temporal decay: lambda=0.05 applied to existing samples
            Writes to bigfive_department_profiles table
            Gate: MIN_DEPT_SAMPLES=10 (ADR-LGPD-001: anonymization threshold)
  --- Later, on next job creation ---
  → bigfive_node → BigFiveDepartmentService.get_blend_weights(company_id, dept, seniority)
       If sample_count < 10: returns None (gate refuses profile)
       If available: returns BigFiveBlend {llm=0.40, onet=0.20, culture=0.15, dept_history=0.25}
  → rank_traits target biased toward dept historical OCEAN profile
```

**Key Details:**
- **Toggle gate:** `learning_loops.bigfive_department_history` (default **OFF**, opt-in). Loaded by `load_learning_loops_toggles()` from `CompanyHiringPolicy.automation_rules`.
- **LGPD compliance:** `MIN_DEPT_SAMPLES=10` gate implements ADR-LGPD-001 — aggregate with N>=10 qualifies as anonymous per ANPD Guia §3 + Art. 12 §1. Individual erasure (LGPD Art. 18) does NOT require recompute.
- **Precondition:** `LiaOpinion.behavioral_analysis['ocean_traits']` must exist — only present if WSI screening ran and `handlers_screening` persisted OCEAN results.
- **Fail-soft:** `_record_bigfive_hire` is wrapped in try/except — a failure never blocks the hire flow.
- **Blend formula:** 4-layer blend: LLM suggestions 40% + O*NET norms 20% + CompanyCulture 15% + Dept History 25%.
- Full LGPD documentation in docstring of `_hook_conclusion_hired` (cites Art. 12 §1, ANPD Guia §3, Resolução CD/ANPD nº 2/2022, EU AI Act Art. 10(5)).
- Sensor: `tests/unit/test_p0_3_min_samples_gate.py` — rejects regression of MIN_DEPT_SAMPLES threshold.

**Related Features:** F-09, F-22, F-25

---

## F-06 · JD Similar History — Vector Embedding Learning

**Status:** 🟡 Partial
**Business Value:** When a recruiter starts a new job creation wizard, suggests structurally similar past job descriptions, reducing time writing JDs for recurring roles.

**Entry Point:** `app/domains/job_creation/services/jd_similar_service.py:184` — `find_similar()`

**Trigger (write):** Job published event → `platform_event_handlers.handle_job_published` → `JdSimilarService.record_jd_if_enabled()`. Hire → `_hook_conclusion_hired` → `JdSimilarService.mark_filled()`.
**Trigger (read):** Wizard startup calls `find_similar(title, company_id, limit=5)`.

**Key Files:**
- `app/domains/job_creation/services/jd_similar_service.py` — `JdSimilarService`: `find_similar()` (line 184), `record_jd_if_enabled()` (line 252), `record_jd()` (line 352), `mark_filled()` (line 418)
- `app/shared/services/embedding_service.py` — `EmbeddingService` (Gemini provider)
- `libs/models/lia_models/jd_similar_history.py` — `jd_similar_history` table (`Vector(1536)`)
- `app/api/v1/automation/event_handlers/platform_event_handlers.py` — `handle_job_published` wiring

**Data Flow:**
```
Job published event
  → JdSimilarService.record_jd_if_enabled(job_id, company_id):
       Check toggle: learning_loops.jd_similar_suggestion (default ON)
       _build_embedding_text(title, jd_enriched) — concatenates title+responsibilities+requirements
       _redact_pii(text) — strips CPF/email/phone before embedding
       EmbeddingService.embed(text) → 768-dim Gemini vector (KNOWN MISMATCH: DB expects 1536-dim)
       If len(embedding) != 1536: service REJECTS (fail-open, logs warning)
       Else: INSERT INTO jd_similar_history (company_id, job_id, title, embedding, ...)

Hire event
  → JdSimilarService.mark_filled(job_id): UPDATE jd_similar_history SET filled_at=now(), time_to_fill_days=N

Wizard startup
  → JdSimilarService.find_similar(title, company_id, limit=5):
       pgvector cosine similarity search on jd_similar_history
       Returns list of {job_id, title, similarity_score, filled_in_days?}
```

**Key Details:**
- **Known dimension mismatch:** `ANTHROPIC_API_KEY` is set in Replit but `OPENAI_API_KEY` is blank. `EmbeddingService` uses Gemini provider which produces **768-dim** vectors. The `jd_similar_history` table column is `Vector(1536)`. Service explicitly rejects non-1536 embeddings → **actual embedding writes silently fail in dev**. This is documented in `docs/architecture/AI_LAYER_TREE.md §8.3`.
- **Toggle:** `learning_loops.jd_similar_suggestion` (default ON). Loaded by `load_learning_loops_toggles()`.
- PII redaction before embedding: `_redact_pii(text)` uses regex to strip CPF/email/phone patterns (line 98).
- `_normalize_title()` at line 161 normalizes job title for consistent text building.
- `record_jd_fire_and_forget()` (line 472) is a thread+asyncio fire-and-forget wrapper for non-blocking publish flow.

**Related Features:** F-04, F-05, F-07

---

## F-07 · ATS / JD Import with NLP Parsing

**Status:** 🟢 Live
**Business Value:** Imports job descriptions from external ATS platforms (Gupy, Pandapé, Merge) or uploaded files, extracts structured fields (skills, responsibilities, seniority, benefits, salary) via NLP, and seeds the job creation workflow, eliminating manual re-entry.

**Entry Point:** `app/domains/job_management/services/jd_import_service.py:166` — `JDImportService.import_jd()`

**Trigger:** POST from ATS sync webhooks (`external_webhooks.py`) or manual import via job management UI

**Key Files:**
- `app/domains/job_management/services/jd_import_service.py` — `JDImportService`: `import_jd()` (line 166), `parse_jd()` (line 510), `_mirror_to_job_vacancy()` (line 318), `_detect_seniority()` (line 574), `_extract_technical_skills()` (line 590)
- `app/domains/job_management/services/jd_enrichment_service.py` — post-import AI enrichment
- `app/api/v1/job_vacancies/_shared.py` — FairnessGuard wired at line 619 for JD save
- `app/domains/ats_integration/domain.py` — `ATSIntegrationDomain` (sync_candidate, sync_job, bulk_sync)

**Data Flow:**
```
ATS webhook / import request
  → JDImportService.import_jd(jd: ImportedJobDescription):
       parse_jd(jd):
         _normalize_title(title) → canonical title
         _detect_seniority(title, description) → (seniority, confidence)
         _extract_technical_skills(text) → [{name, level, required}]
         _extract_behavioral_competencies(text) → [{name, category}]
         _extract_responsibilities(text) → [str]
         _extract_benefits(text) → [str]
         _compute_quality_score(jd_data) → float 0-1
       _apply_parsed_data(jd, parsed) → populates ImportedJobDescription fields
       _mirror_to_job_vacancy(db, jd):
         Creates JobVacancy with status='Rascunho', job_source='ats_importada'
         Phase 4J: populates analytics lifecycle classifier fields
       FairnessGuard.check(jd_text) in _shared.py:619 — raises HTTP 422 if discriminatory
       _update_skill_catalog(skills) — adds new skills to company catalog (async)
```

**Key Details:**
- Parsed result: `ParsedJD` dataclass at line 40 of jd_import_service.py.
- `_classify_job_lifecycle_stage` returns `'ats_importada'` when status='Rascunho' and `is_ats_import=True` flag set (line 409-424).
- Seniority detection: `_detect_seniority(title, description)` at line 574 — regex + keyword matching, returns `(seniority, confidence)` tuple.
- FairnessGuard is wired in the JD save path (`_shared.py:619`) and also in `jd_import.py:133` for bulk imports.
- `get_jd_import_service()` factory at line 840.

**Related Features:** F-06, F-15, F-25

---

## F-08 · Salary Benchmark with Provenance

**Status:** 🟡 Partial
**Business Value:** Provides market salary ranges for roles during job creation wizard, with explicit sourcing — either real web data (SerpAPI) or LLM estimation labeled clearly as unverified.

**Entry Point:** `app/domains/analytics/services/market_benchmark_service.py` — `search_salary_benchmark()`

**Trigger:** Salary wizard step in job creation; direct call from `/api/v1/lia-assistant/_shared.py` salary recommendation endpoint; `CompensationAnalysisService`

**Key Files:**
- `app/domains/analytics/services/market_benchmark_service.py` — `MarketBenchmarkService`: `search_salary_benchmark()`, `_estimate_with_llm()`, `combine_with_internal()`
- `app/api/v1/lia_assistant/_shared.py` — salary recommendation endpoint (read path)
- `app/domains/analytics/services/compensation_analysis_service.py` — consumer
- `tests/contract/test_salary_benchmark_provenance.py` — provenance sensor

**Data Flow:**
```
Salary step in wizard / LIA salary assistant
  → MarketBenchmarkService.search_salary_benchmark(role, location, seniority):
       if SERP_API_KEY present:
         fetch SerpAPI → parse salary data from Glassdoor/LinkedIn results
         source = real web data, confidence = 'medium'
       else (dev — SERP_API_KEY absent):
         _estimate_with_llm(role, location, seniority):
           Returns {min, max, median, sources_found=[], llm_fallback=True}
           source = 'estimativa_sem_busca', confidence = 'low', unverified=True
       combine_with_internal(benchmark, company_salary_bands)
       → Returns SalaryBenchmark {min, max, median, source, confidence, unverified flag}
  → Wizard/FE displays with explicit label "Estimativa não verificada — sem dados de mercado reais"
```

**Key Details:**
- `SERP_API_KEY` is **NOT set** in `.env` — all benchmark calls in dev fall through to LLM estimation.
- **Provenance anti-pattern fixed (2026-06-03):** Previously, LLM was asked to fill `sources_found` with real domain names (Glassdoor, etc.) even for hallucinated figures. Now `sources_found=[]` and `llm_fallback=True` when SERP absent.
- **Provenance rule:** Never cite Glassdoor/Robert Half/etc. for numbers derived from LLM parametric knowledge only.
- In-memory TTL cache: 24h to avoid repeated API calls for the same role.
- Sensor: `tests/contract/test_salary_benchmark_provenance.py` — asserts that absence of SERP_API_KEY produces `unverified=True`, no real source domains in `sources_found`.

**Related Features:** F-04, F-25

---

## F-09 · WSI Screening Flow (Work Style Inventory)

**Status:** 🟢 Live
**Business Value:** Conducts a structured behavioral screening interview with candidates (web or voice) using WSI methodology (Bloco A: F1-F6), scoring OCEAN traits and producing a ranked shortlist with explainable scores and Dreyfus/Bloom classification.

**Entry Point:** `app/domains/recruitment/services/triagem_session_service/lifecycle.py:209` — `create_session()`

**Trigger:** Recruiter triggers screening from kanban pipeline; or candidate follows application link that activates screening session

**Key Files:**
- `app/domains/recruitment/services/triagem_session_service/lifecycle.py` — `create_session()` (line 209), `start_session()` (line 321), `complete_session()` (line 426)
- `app/domains/recruitment/services/triagem_session_service/eligibility_phase.py` — eligibility phase before WSI
- `app/domains/cv_screening/services/wsi_service/score_calculator.py` — `calculate()` (line 15), `_aggregate_ocean_traits()` (line 120)
- `app/domains/cv_screening/services/wsi_service/question_generator.py` — WSI question generation
- `app/domains/cv_screening/services/wsi_service/report_generator.py` — report generation
- `app/domains/cv_screening/services/eligibility_verification_service.py` — canonical eligibility parser
- `app/api/v1/cv_screening/wsi.py` — REST endpoints for session management

**Data Flow:**
```
create_session(candidate_id, vacancy_id, company_id):
  → Build session with eligibility metadata, block structure (WSI blocks F1-F6)
  → Welcome message with TTS audio_base64 if voice mode

start_session(session_id):
  → ConsentCheckerService.check_candidate_consent(purpose='ai_screening')
       FAIL-CLOSED: if consent missing → session blocked (since 2026-06-05 audit)
  → If eligibility active: → eligibility_phase
       EligibilityVerificationService.get_eligibility_questions_from_job()
       (answers tagged wsi_block=999 — excluded from WSI scoring)
  → If eligibility passed: → first WSI block

Per message (candidate answer):
  → ResponseAnalyzer scores answer per behavioral dimension
  → FairnessGuard check on candidate text (implicit bias detection)
  → next question or block advance

complete_session(session_id):
  → WsiDeterministicScorer.calculate_percentiles() — score all blocks
  → _aggregate_ocean_traits(responses) → OCEAN floats 0-1
  → WSIResult with ocean_traits stored in LiaOpinion.behavioral_analysis
  → DreyfusClassifier.classify() — skill proficiency (Novice→Expert)
  → BloomClassifier.classify() — cognitive level
  → report_generator.generate() → structured report with scores + explanations
```

**Key Details:**
- Eligibility answers carry `wsi_block=999` sentinel — `complete_session` scorer filters these out from WSI scoring.
- OCEAN traits stored in `LiaOpinion.behavioral_analysis['ocean_traits']` — consumed downstream by F-05 (BigFive dept learning) and F-22 (calibration).
- Voice mode: `wsi_voice_orchestrator.py` + `WSIVoicePlugin` (plugin_name='wsi_screening').
- `check_candidate_consent` is **fail-closed** since 2026-06-05 audit — exception blocks session start.
- Sensor: `tests/contract/test_eligibility_producer_contract.py` (13 tests) + `tests/unit/test_eligibility_phase.py` (7 tests).

**Related Features:** F-05, F-10, F-16, F-21

---

## F-10 · Eligibility Questions Flow

**Status:** 🟢 Live
**Business Value:** Eliminatory pre-screening questions (work model, location, availability, legal requirements) that auto-block incompatible candidates before costly WSI screening, with humanized 2x reconsideration flow and talent-pool fallback.

**Entry Point:** `app/domains/cv_screening/services/eligibility_verification_service.py` — `get_eligibility_questions_from_job()`

**Trigger:** `start_session()` in triagem lifecycle when `session.metadata_json['eligibility']` is present; also in WhatsApp conversation flow via `conversation_manager`

**Key Files:**
- `app/schemas/eligibility_question_item.py` — `EligibilityQuestionItem` (canonical shape: `{id, question, question_type, options, is_eliminatory, expected_answer, category, order}`)
- `app/domains/cv_screening/services/eligibility_verification_service.py` — `get_eligibility_questions_from_job()` (single canonical producer), `ReconsiderationResult` StrEnum
- `app/domains/recruitment/services/triagem_session_service/eligibility_phase.py` — web flow consumer
- `app/domains/communication/services/conversation_manager.py` — WhatsApp flow consumer

**Data Flow:**
```
Session start with eligibility configured
  → EligibilityVerificationService.get_eligibility_questions_from_job(vacancy_id, db):
       Reads JobVacancy.eligibility_questions JSONB
       model_validator(before) in EligibilityQuestionItem normalizes 4 legacy shapes:
         wizard shape: {required_answer: 'yes'|'no'}
         edit-vacancy: {disqualify_on_fail, expected_answer}
         catalog:      {eliminatory, eliminatoryAnswer}
         extractor:    {question_text, is_eliminatory}
       → [EligibilityQuestionItem, ...]

Per candidate answer:
  → EligibilityVerificationService.check_answer(question, answer, reconsideration_count):
       If is_eliminatory and answer != expected_answer:
         if reconsideration_count < 2: → ReconsiderationResult.NEEDS_RECONSIDERATION
             RECONSIDERATION_TEMPLATES[category] provides warning+confirmation+talent_pool text
         else: → ReconsiderationResult.MAX_RECONSIDERATIONS_REACHED
               → candidate added to talent pool (FairnessGuard CLT 373-A)
               → session ends (eliminated)
       else: → ReconsiderationResult.PASSED

Answer tagged wsi_block=999 → excluded from WSI scoring in complete_session()
```

**Key Details:**
- `get_eligibility_questions_from_job()` is the **ONLY** canonical parser. Never read `job.eligibility_questions` JSONB directly.
- **4 legacy shapes** are normalized at load time via `EligibilityQuestionItem` Pydantic `model_validator(mode='before')`.
- **category** enum: `work_model / location / availability / legal / default` — maps to `RECONSIDERATION_TEMPLATES` dict for humanized retry messages.
- Reconsideration max = 2 per conversation (hardcoded). After that, talent pool is offered.
- FairnessGuard wired inside producer: CLT 373-A / LGPD Art. 20 — eliminatory questions based on protected class attributes are blocked.
- `wsi_block=999` sentinel is critical — do not remove or change without updating `complete_session` scorer filter.

**Related Features:** F-09, F-15

---

## F-11 · Inline Chat (Text Selection / Hover / BTW)

**Status:** 🟢 Live
**Business Value:** Lets recruiters ask one-shot questions about selected text on any page, hover over candidate/job entities for context, or submit page-level queries — all without interrupting their current workflow.

**Entry Point:** `app/api/v1/inline_chat.py` — POST `/api/v1/inline-chat/ask`

**Trigger:** (1) User selects text on any page → toolbar popover appears → submit; (2) Hover on entity card; (3) BTW (by-the-way) query triggered from page-level context; (4) `/pt/*/` Next.js route via proxy

**Key Files:**
- `app/api/v1/inline_chat.py` — `InlineChatRequest`, endpoint registered at `routes.py:676`
- `plataforma-lia/src/components/inline-chat/GlobalSelectionChat.tsx` — mounted in `DeferredLayoutClients.tsx` (dynamic import)
- `plataforma-lia/src/hooks/useInlineChatSubmit.ts` — submits to `/api/backend-proxy/inline-chat/ask`
- `plataforma-lia/src/hooks/useTextSelection.ts` — detects text selection and fires popover
- `plataforma-lia/src/app/api/backend-proxy/inline-chat/ask/route.ts` — proxy with 20s timeout

**Data Flow:**
```
User selects text → useTextSelection detects selection
  → GlobalSelectionChat shows toolbar popover
  → useInlineChatSubmit.submit({context_type, context_data, intent, text, question}):
       POST /api/backend-proxy/inline-chat/ask (Next.js proxy, 20s timeout)
       → POST /api/v1/inline-chat/ask (FastAPI)
            FairnessGuard.check(question) — HTTP 400 if discriminatory
            resolve context:
              text_selection: context_data = selected text
              candidate: CandidateRepository.get_full_profile(candidate_id, company_id)
              job: JobVacancyRepository.get(job_id, company_id)
            LLM call via get_provider_for_tenant() — raises 503 on failure (no silent fallback)
            intent routing:
              'answer': factual answer about context
              'suggest_rewrite': gender-neutral rewrite of selected text
              'defer': store for later (saves to session context)
       → Returns {answer, context_used, suggested_rewrite?}
  → Rendered in popover / toolbar
```

**Key Details:**
- **No persistent state** — each call is fully independent (no session memory).
- `suggest_rewrite` intent generates gender-neutral rewrites for JD text selection.
- `company_id` isolation enforced in `candidate` context via `CandidateRepository.get_full_profile(candidate_id, company_id)`.
- `get_provider_for_tenant()` raises 503 (not silent fallback) on LLM provider failure.
- Proxy timeout: 20s (configured in route.ts).
- FE component is dynamically imported with `ssr: false` to prevent hydration issues.

**Related Features:** F-01, F-15

---

## F-12 · Comparative Candidate Analysis (D9)

**Status:** 🟢 Live
**Business Value:** Side-by-side comparison of 2-4 candidates with scenario-adaptive weighted scoring — adjusting weights based on what data is available (full WSI, CV only, or no-job context), enabling data-driven shortlist decisions.

**Entry Point:** `app/api/v1/candidate_compare.py` — POST `/api/v1/candidates/compare`

**Trigger:** (1) "Compare Candidates" button in KanbanPageModalsExtra; (2) chat workflow intent `compare_candidates` via recruiter_copilot tool

**Key Files:**
- `app/api/v1/candidate_compare.py` — endpoint (registered `routes.py:321`)
- `app/domains/cv_screening/services/candidate_comparison_service.py` — `CandidateComparisonService`, `ScenarioWeights`
- `plataforma-lia/src/components/kanban/CandidateCompareModal.tsx` — FE modal
- `plataforma-lia/src/hooks/use-candidate-compare.ts` — FE hook
- `plataforma-lia/src/app/api/backend-proxy/candidates/compare/route.ts` — proxy
- `plataforma-lia/src/components/kanban/KanbanPageModalsExtra.tsx` — renders modal

**Data Flow:**
```
Recruiter selects 2-4 candidates → "Compare" button
  → CandidateCompareModal opens → use-candidate-compare hook
  → POST /api/backend-proxy/candidates/compare → /api/v1/candidates/compare
       get_verified_company_id() — tenant isolation (no X-Company-ID header bypass)
       CandidateComparisonService.compare(candidate_ids, job_id?):
         Detect scenario:
           A (all screened with WSI): rubricas 40% + WSI 25% + BigFive 15% + prerequisites 10% + history 10%
           B (CV only):               rubricas 60% + prerequisites 20% + history 20%
           C (no job context):        history 50% + completeness 30% + recency 20%
         Score each candidate per dimension
         Generate comparison narrative via LLM (strength/gap per dimension)
       → Returns {candidates: [{id, scores, narrative}], scenario_used, weights}
  → CandidateCompareModal renders side-by-side table with radar chart
```

**Key Details:**
- `ScenarioWeights` dataclass defines the 3 weight sets. Scenario auto-detected from data availability.
- `ComparativeAnalysisService` in `interview_intelligence` domain handles WSI cohort analysis separately (different from this service).
- Accessible via recruiter chat: `compare-candidates` intent in federated agent FEDERATION_SPEC.
- `get_verified_company_id()` (from `app/shared/tenant_guard`) prevents X-Company-ID header bypass (Regra 6, ADR R4).

**Related Features:** F-09, F-01

---

## F-13 · Task Planner / Plan-and-Execute

**Status:** 🔴 Ghost (from UI perspective)
**Business Value:** Multi-step task decomposition for complex recruiting workflows — intended to break down "hire 5 engineers by Q3" into subtasks with dependencies, durations, and agent assignments.

**Entry Point:** `app/api/v1/task_planner.py` — POST `/api/v1/task-planner/decompose`

**Trigger:** No confirmed FE trigger. Backend fully registered and reachable.

**Key Files:**
- `app/api/v1/task_planner.py` — endpoints: `/decompose`, `/tasks`, `/prioritize`, `/dag/build`, `/execution-plans`
- `app/domains/automation/agents/automation_react_agent.py` — `AutomationReActAgent` (decompose backend)
- `app/orchestrator/services/plan_orchestration_service.py` — `PlanOrchestrationService.execute()`
- `app/shared/execution/plan_progress_mapper.py` — progress event mapping
- `plataforma-lia/src/lib/api/api.generated.ts:15324-15433` — FE types generated (stubs only)

**Data Flow:**
```
[Backend fully wired]
POST /api/v1/task-planner/decompose {task_description, context}
  → FairnessGuard.check(task_description)
  → AutomationReActAgent.decompose(task):
       LLM breaks task into subtasks with dependencies, durations, agent_type
       PlannedTaskRepository.save(subtasks)
  → Returns {plan_id, subtasks, dag}

[FE gap]
NO frontend component or hook calls the decompose/tasks/prioritize endpoints.
NO proxy route under /api/backend-proxy/task-planner/.
planProgressSteps state in lia-float-context IS passed to context BUT has zero rendering consumers.
```

**Key Details:**
- FE type stubs exist in `api.generated.ts` lines 15324-15433 but no hook or component imports/uses them.
- `plan_progress` events arrive at FE via WS, update `planProgressSteps` state, but nothing renders them.
- Backend FairnessGuard wired at decompose endpoint (Fix C3 2026-06-14).
- To promote to Live: need (a) proxy route, (b) FE component consuming `chatPlanProgressSteps`, (c) slash command or button entry point.

**Related Features:** F-01, F-28

---

## F-14 · HITL (Human-in-the-Loop) Gates

**Status:** 🟡 Partial — Backend fully implemented and tested; gate is **dormant** (LIA_HITL_GATE off)
**Business Value:** Prevents irreversible AI actions (closing jobs, sending bulk emails, rejecting candidates) from executing without explicit recruiter confirmation, catching AI mistakes before they reach candidates.

**Entry Point:** `app/shared/hitl/hitl_approval_context.py` — `hitl_preflight()` (ContextVar gate)

**Trigger:** Recruiter sends a message that triggers a gated tool; agent returns `approval_required` SSE event; recruiter approves → `approve_pending_id` replayed in next SSE request

**Key Files:**
- `app/shared/hitl/hitl_approval_context.py` — `hitl_preflight()`, `hitl_gate_enabled()`, `_hitl_approved` ContextVar
- `app/domains/cv_screening/services/hitl_service.py` — `HITLService` (canonical durable producer)
- `app/api/v1/agent_chat_sse.py:211` — emits `approval_required` SSE frame; line 218 — `_detect_hitl_approval`
- `plataforma-lia/src/components/transition/TransitionChatPanel.tsx` — `sendApproval` FE wiring
- `plataforma-lia/src/components/modals/UniversalTransitionModal.tsx` — also has `sendApproval`

**Data Flow:**
```
[When LIA_HITL_GATE=on]
Agent calls gated tool (e.g., close_job)
  → hitl_preflight(tool_name):
       hitl_gate_enabled() reads LIA_HITL_GATE env — if OFF, returns None (passthrough)
       If ON: check _hitl_approved ContextVar
         If not set → return {needs_confirmation: True, tool_name, message}
  → Agent returns needs_confirmation → SSE emits approval_required {pending_id, tool, summary}
  → FE renders confirmation card with Confirm/Cancel buttons
  → Recruiter clicks Confirm → sendApproval(pending_id)
  → Next SSE request includes approve_pending_id
  → _detect_hitl_approval(approve_pending_id):
       HITLService.get_and_mark_approved(pending_id, company_id)
       Set _hitl_approved ContextVar = True
  → Tool re-executes with approved ContextVar → proceeds
```

**Key Details:**
- **LIA_HITL_GATE is COMMENTED OUT** in `.env` line 186 — gate is dormant, zero regression.
- **7 tools gated** (as of commit `8dea17558`): `close_job`, `send_email`, `send_whatsapp`, `bulk_send`, `reject_candidate`, `bulk_update_stage`, `publish_job`.
- Two parallel HITL mechanisms: (1) `hitl_preflight` ContextVar for SSE/federated path; (2) supervisor's own HITL via `intents_config` + Phase 0 action_handlers (NOT double-gated).
- `HITLService` (durable DB record) is distinct from `hitl_preflight` (lightweight ContextVar gate). The durable one mints pending_action records; the ContextVar gates per-call.
- `app/services/hitl_service.py` is a compatibility shim re-exporting from canonical `app/domains/cv_screening/services/hitl_service.py`.
- 31 backend tests verify the full loop. To activate: set `LIA_HITL_GATE=on` in `.env`.

**Related Features:** F-01, F-09, F-27

---

## F-15 · FairnessGuard Integration

**Status:** 🟢 Live
**Business Value:** Automatically blocks discriminatory queries (gender, race, age, religion, marital status, pregnancy, appearance) across all recruiter text inputs before they reach the LLM or database, with educational messages citing CLT 373-A and LGPD Art. 20.

**Entry Point:** `app/shared/compliance/fairness_guard.py` — `FairnessGuard.check(text)`

**Trigger:** All recruiter free-text inputs before LLM invocation or DB write. 13+ surfaces wired.

**Key Files:**
- `app/shared/compliance/fairness_guard.py` — `FairnessGuard`: `check()`, `log_check()`, `IMPLICIT_BIAS_TERMS` (~35 PT-BR), `IMPLICIT_BIAS_TERMS_EN` (~40 EN)
- `app/shared/compliance/fairness_guard_middleware.py` — `_fairness_pre_check()` mixin for domain agents
- `app/domains/compliance_base.py` — `ComplianceDomainPrompt` base class (all domains inherit)
- `app/api/v1/agent_chat_sse.py` — LIA-P03 pre-check at SSE entry
- `app/api/v1/candidate_search/search.py:134` and `archetypes.py:1234` — Funil search
- `plataforma-lia/src/hooks/useCandidatesExecuteSearch.ts` — FE dual display (banner amber + LIA bubble)

**Data Flow:**
```
Any recruiter text input
  → FairnessGuard.check(text):
       EXPLICIT_BIAS_PATTERNS regex (gender/race/age/religion/marital/pregnancy/appearance)
       IMPLICIT_BIAS_TERMS dict (PT-BR ~35 terms + EN ~40 terms)
       Returns FairnessCheckResult {is_blocked, blocked_terms, category, educational_message}
  → If is_blocked:
       log_check(session_id, company_id, recruiter_id) — writes FairnessAuditLog row
         FairnessAuditLog.session_id populated (Fix A 2026-06-14)
         FairnessPolicyViolation.correlation_id = session_id (Fix D 2026-06-14)
       Raise HTTP 400 {error: 'fairness_blocked', fairness_blocked: True,
                       educational_message, category, blocked_terms}
  → FE: if _errBody?.error === 'fairness_blocked':
       Banner amber inline (role="alert", ShieldAlert icon, dismiss)
       LIA bubble in lateral panel (setChatMessages type='lia')
```

**Key Details:**
- **100% coverage confirmed** (audit 2026-06-14): all direct agent endpoints have FairnessGuard.
- Prometheus counter: `lia_fairness_blocks_total{category}`.
- Domain agents inherit via `ComplianceDomainPrompt` base — `_fairness_pre_check()` mixin auto-calls `log_check()` with company_id/recruiter_id.
- Legal citations: CLT Art. 373-A, CF Art. 5, Lei 9.029/95, LGPD Art. 20.
- Audit query: `SELECT * FROM fairness_audit_log WHERE session_id = '<session_id>'`.
- **To add a new text input surface:** call `_fg = FairnessGuard(); result = _fg.check(text)` before LLM/DB; if `result.is_blocked` raise HTTP 400 with the canonical dict above; call `_fg.log_check()` with session_id.
- Sensors: `test_fairness_candidate_search.py` (4), `test_fairness_audit_trail.py` (11), `test_fairness_session_correlation.py` (11).

**Related Features:** F-01, F-09, F-10, F-11

---

## F-16 · Voice Data Collection (Twilio + Gemini Live)

**Status:** 🟢 Live
**Business Value:** Collects candidate data (DataRequest fields) via outbound voice calls using LIA's voice persona, with LGPD verbal consent, multi-channel fallback (portal + WhatsApp for fields not collectible by voice), and per-tenant monthly call budget.

**Entry Point:** `app/domains/communication/services/data_request_voice_service.py` — `DataRequestVoiceService.start_collection()`

**Trigger:** Manual trigger from recruiter "Request Data via Voice" action or automated communication pipeline

**Key Files:**
- `app/domains/voice/plugins/data_collection_voice_plugin.py` — `DataCollectionVoicePlugin` (plugin_name='data_collection')
- `app/domains/voice/plugins/wsi_voice_plugin.py` — `WSIVoicePlugin` (plugin_name='wsi_screening')
- `app/domains/voice/plugins/studio_voice_plugin.py` — `StudioVoicePlugin` (plugin_name='studio')
- `app/domains/communication/services/data_request_voice_service.py` — orchestration + budget gate
- `app/domains/cv_screening/services/wsi_voice_orchestrator.py` — WSI voice flow

**Data Flow:**
```
DataRequestVoiceService.start_collection(company_id, candidate_id, request_id):
  [1] Validate data request fields
  [2] ConsentCheckerService — LGPD consent gate (fail-closed)
  [3] _check_voice_budget(company_id) → Redis key 'voice_calls:{company_id}:YYYY-MM'
        If calls_this_month >= VOICE_CALLS_MONTHLY_DEFAULT_LIMIT (100):
          Return status='voice_collection_budget_exceeded' (never fake-success)
        If Redis unavailable → (True, 0) FAIL-OPEN (Redis down != all calls blocked)
  [4] orchestrator.initiate_call(candidate_phone, plugin='data_collection')
        DataCollectionVoicePlugin.on_session_initiated():
          build_collection_script() — ordered list of voice-collectible fields
          CONSENT_QUESTION (hardcoded literal — NEVER parameterize with ai_name)
          _build_recording_notice(ai_name) — per-tenant info notice (ok to personalize)
        get_next_question() — sequential cursor
        on_session_finalized(transcript) — extract + normalize answers
  [5] _increment_voice_calls(company_id) — ONLY on orch_status=='initiated'
  → Returns {collected, needs_followup, portal_fallback_fields}
```

**Key Details:**
- **CONSENT_QUESTION is a hardcoded literal** — 'WeDOTalent' is the legal data controller (LGPD Art. 7/9). Never substitute `ai_persona.name` here. Sensor: `test_voice_wording_persona.py::test_consent_question_is_lgpd_literal`.
- **Budget:** `VOICE_CALLS_MONTHLY_DEFAULT_LIMIT=100` (~$6.50/month/tenant), Redis TTL=33 days. Fail-OPEN on Redis unavailability.
- **3 plugin taxonomy:** `data_collection` / `wsi_screening` / `studio` — differentiated by `plugin_name` field read by `voice_screening_orchestrator.py`.
- `_build_recording_notice(ai_name)` uses per-tenant ai_name (informational, not legal) — OK to personalize.
- Sensor: `tests/unit/test_voice_call_budget.py` (14 tests): under/at/over limit, fail-open Redis, increment-only-on-initiated.

**Related Features:** F-02, F-09, F-30

---

## F-17 · Agent Studio — Custom & Marketplace Agents

**Status:** 🟢 Live
**Business Value:** Lets advanced users (recruiters or WeDOTalent staff) create custom AI agents with configurable tools, publish them to a marketplace, and install from marketplace — extending platform capabilities without code changes.

**Entry Point:** `app/domains/agent_studio/domain.py` — `AgentStudioDomain` (@register_domain)

**Trigger:** Recruiter uses Agent Studio tab in platform; or MainOrchestrator routes to agent_studio domain

**Key Files:**
- `app/domains/agent_studio/domain.py` — `AgentStudioDomain`, actions catalog
- `app/domains/agent_studio/custom_agent_runtime.py` — `CustomAgentRuntime` (TenantAwareAgentMixin + LangGraphReActBase)
- `app/domains/agent_studio/platform_tools_loader.py` — loads `platform_tools.yaml` (single source of truth)
- `app/api/v1/agent_studio/agent_deployments.py` — deployment management + background_task_update events
- `app/domains/registry.py:_YamlDomainProxy` — tenant YAML as DomainPrompt-compatible proxy

**Data Flow:**
```
Recruiter creates custom agent:
  → create_custom_agent(name, description, tools_subset, system_prompt_yaml)
  → CustomAgentRuntime.get_or_create_runtime(agent_id):
       Loads platform_tools.yaml → available tools
       Caches runtime per agent_id
       Enforces P0-2 review gate: new agent = status='pending_review'
       Dry-run mode via _DRY_RUN ContextVar:
         Write tools → _DRY_RUN_WOULD_DO list
         Read tools → execute normally
  → Publish to marketplace → publish_to_marketplace(agent_id)
       Sets status='published' after wedotalent_admin review
  → Install from marketplace → install_from_marketplace(template_id, company_id)
       Quota check + FairnessGuard on template metadata
       Creates per-company AgentTemplate row
  → DomainRegistry.get_domain_for_company(domain_id, company_id, db):
       Resolves AgentTemplate YAML override per tenant
       _YamlDomainProxy wraps YAML as DomainPrompt-compatible instance
```

**Key Details:**
- `HITL_REQUIRED_TOOLS` loaded from `platform_tools.yaml` — write tools intercepted in dry-run.
- **P0-2 review gate:** marketplace-installed agents stay at `REVIEW_STATUS_PENDING='pending_review'` until `wedotalent_admin` approves.
- `_DRY_RUN` ContextVar: enables safe "what would this agent do?" preview mode.
- `PII+Audit callbacks` wired in `CustomAgentRuntime`.
- Background task updates emitted via `agent_deployments.py:266` for async deployment progress.
- `model_override` optional field on custom agents (can specify different LLM).

**Related Features:** F-01, F-15, F-14

---

## F-18 · Digital Twin Agents

**Status:** 🟡 Partial
**Business Value:** Captures expert (SME) reasoning patterns from audio recordings and uses them to evaluate candidates — enabling consistent assessment at scale using the same criteria an experienced interviewer would apply.

**Entry Point:** `app/domains/digital_twin/domain.py:67` — `execute_action()` dispatches to `_handle_create_twin()`, `_handle_evaluate_with_twin()`, etc.

**Trigger:** Agent Studio action or direct domain call; no standalone ReActAgent

**Key Files:**
- `app/domains/digital_twin/domain.py` — `DigitalTwinDomain` (Micro-Action, no `agents/` subdirectory)
- `app/domains/digital_twin/services/digital_twin_service.py` — (structure present, methods for RAG few-shot evaluation)
- `app/domains/digital_twin/services/audio_indexer_service.py` — indexes expert audio recordings

**Data Flow:**
```
Create twin:
  _handle_create_twin(expert_id, audio_urls, role_context):
    → AudioIndexerService.index_audio(urls) → transcription + embeddings
    → Build RAG few-shot examples from expert reasoning patterns
    → Store DigitalTwin record with expert profile + embeddings

Evaluate with twin:
  _handle_evaluate_with_twin(candidate_id, twin_id, criteria):
    → Load twin embeddings + few-shot examples
    → RAG retrieval: find most similar evaluation examples from twin
    → LLM call: "Given expert reasoning pattern [examples], evaluate candidate [CV/WSI]"
    → Returns {score, reasoning, confidence, citations_from_expert}

Index audio:
  _handle_index_twin_audio(twin_id, audio_url):
    → Transcribe → extract decision patterns → update RAG store
```

**Key Details:**
- **Micro-Action domain** (7 files, no `agents/` subdirectory). `execute_action()` handles routing inline.
- No tool registry — direct dispatch from `execute_action()` to `_handle_*` methods.
- Classified as `high_impact=True`, `fairness_action_type=screening` — ComplianceDomainPrompt enforces FairnessGuard pre/post.
- No `capabilities.yaml` configured for routing — must be called explicitly.
- Domain has actions: `create_twin`, `evaluate_with_twin`, `list_twins`, `index_twin_audio`, `deactivate_twin`.

**Related Features:** F-09, F-17

---

## F-19 · Proactive Layer & Autonomous Alerts

**Status:** 🟡 Partial
**Business Value:** Proactively notifies recruiters of pipeline events (inactive candidates, no-shows, expiring vacancies, pipeline bottlenecks) on a schedule, reducing manual monitoring burden.

**Entry Point:** `app/domains/automation/services/automation_scheduler.py:40` — `AutomationScheduler` (APScheduler, started at `app/main.py:527`)

**Trigger:** APScheduler cron jobs, started at application boot (`automation_scheduler.start()` at main.py line 527, stopped at line 775)

**Key Files:**
- `app/domains/automation/services/automation_scheduler.py` — `AutomationScheduler` with all scheduled jobs
- `app/domains/automation/services/autonomous_agent_service.py:310` — `create_proactive_action()` / `_execute_proactive_action()`
- `app/domains/automation/services/prediction_action_bridge.py:136` — `create_proactive_actions()`
- `app/domains/recruiter_assistant/domain.py:740` — `_handle_proactive_alerts()`
- `app/domains/communication/services/teams_bot.py:174` — `send_proactive_message()` (Teams integration)

**Data Flow:**
```
AutomationScheduler (APScheduler, boot-registered):
  check_inactive_candidates():     candidates with no activity > threshold → notification
  check_interview_no_shows():      no-show detection → recruiter alert
  send_interview_reminders():      pre-interview reminders to candidates/interviewers
  check_expiring_vacancies():      vacancies near deadline → recruiter alert
  cleanup_stale_reminders():       housekeeping
  auto_complete_expired_screenings(): time-boxed WSI sessions
  run_pipeline_monitor():          pipeline health check via PipelineMonitor
  run_proactive_alerts():          general alerts to active companies
  run_teams_proactive_checks():    Teams-connected companies
  run_proactive_detection():       AutonomousAgentService.create_proactive_action()
  run_learning_automation():       learning loop housekeeping
  run_lgpd_cleanup():              LGPD retention policy enforcement
  _run_autonomous_actions():       AutonomousAgentService._execute_proactive_action()
```

**Key Details:**
- **Scheduler is live and started at boot** — `automation_scheduler.start()` at `main.py:527`.
- Known ghost services (per MEMORY.md census 2026-06-09): `AutonomousActionsEngine`, `TeamsProactivityEngine` have no confirmed trigger.
- **Digest frequency (briefingFrequency):** only backend (daily/2x/weekly/monthly). UI setting is a **ghost** — endpoint deprecated, not consumed.
- Teams proactive messages use `send_proactive_message()` (teams_bot.py:174).
- `run_job_now(job_id)` at line 1106 allows manual trigger of any scheduled job via API.

**Related Features:** F-01, F-22

---

## F-20 · PII Field Visibility by Role

**Status:** 🟢 Live
**Business Value:** Granular per-field per-user (and per-role) control over which PII fields (CPF, email, phone, salary) are visible in candidate profiles, ensuring compliance and least-privilege data access without removing data from the platform.

**Entry Point:** `libs/lia-pii/lia_pii/masking.py` — `mask_pii_outbound()`, `resolve_pii_field_visibility()`

**Trigger:** Every candidate profile serialization in `candidates_crud.py`; every outbound message; every chat response involving candidate data (via ContextVar)

**Key Files:**
- `app/shared/pii_masking.py` — retrocompat shim re-exporting from `libs/lia-pii/lia_pii/masking.py`
- `app/shared/rbac/pii_field_catalog.py` — shim re-exporting from `libs/lia-pii/lia_pii/field_catalog.py`
- `libs/lia-pii/lia_pii/masking.py` — `mask_pii_outbound()`, `strip_pii_for_llm_prompt()`, `PIIMaskingFilter`
- `libs/lia-pii/lia_pii/field_catalog.py` — `GATEABLE_PII_FIELDS`, `SENSITIVE_FIELDS`, `SALARY_FIELDS`, `VACANCY_FIELDS`, `ALL_CONFIGURABLE_FIELDS`
- `libs/lia-pii/lia_pii/pii_field_resolver.py` — `resolve_pii_field_visibility()`: user > role > legacy > default=visible
- `plataforma-lia/src/components/settings/user-form/PiiVisibilityMatrix.tsx` — tri-state UI (Inherited/See/Hide)
- `plataforma-lia/src/components/settings/role-defaults/` — role-level defaults UI

**Data Flow:**
```
Candidate profile request by recruiter
  → candidates_crud.py serialization
  → For each PII field (CPF, email, phone, RG, salary, etc.):
       resolve_pii_field_visibility(field, user_id, role, company_id):
         Check user-level override first
         Fall back to role-level default
         Fall back to legacy can_view_* permission
         Default: visible (back-compat)
  → mask_pii_outbound(field, value, visibility):
       If visibility='hidden' → masked (****)
       If visibility='visible' → passthrough (Art. 7 II — recruiter has legitimate interest)

Chat path (SSE + WS):
  → strip_pii_for_llm_prompt(text):
       Resolve-then-strip pattern:
         CPF/email/phone/name → resolve to UUID first (entity resolution preserved)
         Then strip: LLM vendor never sees raw identifier
  → Logs: mask_pii (PIIMaskingFilter) — always masked, immutable
```

**Key Details:**
- **3-layer ADR-LGPD-002 architecture:** (1) Recruiter sees passthrough default; (2) LLM vendor gets minimized (resolve-then-strip); (3) Logs always masked.
- `app/shared/pii_masking.py` and `app/shared/rbac/pii_field_catalog.py` are **retrocompat shims** (~50 consumers). New code should import from `lia_pii` library directly.
- Tri-state matrix in UI: Inherited / See / Hide per field per user.
- Role-defaults endpoint: `GET /api/v1/pii-visibility/role-defaults`.
- VACANCY_FIELDS: salary visibility on job postings, separately gated (commit 6f49ccbf5 + ca25d24993b6).

**Related Features:** F-01, F-15

---

## F-21 · WSI Question Effectiveness Learning Loop

**Status:** 🟡 Partial — toggle default OFF; write path active; read path active but requires toggle enabled
**Business Value:** Over time, identifies which behavioral question topics (skills_probed) best discriminate between hired and rejected candidates in a department, improving WSI question quality and hiring predictiveness.

**Entry Point:** `app/domains/job_creation/services/wsi_effectiveness_service.py` — `record_question_outcome()`

**Trigger (write):** `transition_dispatch_service._record_wsi_outcomes_for_candidate()` on `conclusion_hired` and on rejection screening events.
**Trigger (read):** `WsiEffectivenessService.select_priority_skills()` called in wizard WSI question generation.

**Key Files:**
- `app/domains/job_creation/services/wsi_effectiveness_service.py` — `WsiEffectivenessService`: `record_question_outcome()`, `select_priority_skills()`, `_compute_discrimination_score()`
- `app/domains/job_creation/repositories/wsi_effectiveness_repository.py` — `WsiEffectivenessRepository`
- `app/domains/communication/services/transition_dispatch_service.py` — `_record_wsi_outcomes_for_candidate()`
- Table: `wsi_question_effectiveness`

**Key Details:**
- **Toggle gate:** `learning_loops.wsi_question_effectiveness` (default **OFF**, opt-in).
- `MIN_SAMPLES_FOR_DISCRIMINATION=20` — prevents use until N>=20 per skill per dept.
- `adverse_impact >= 0.10` → `fairness_blocked=True` for that skill (disparate impact proxy).

**Related Features:** F-05, F-09, F-22

---

## F-22 · Calibration Event Learning

**Status:** 🟢 Live
**Business Value:** Tracks explicit (thumbs up/down) and implicit (stage advances/rejects) recruiter feedback on AI decisions, surfacing divergences between LIA scores and actual recruiter judgment for model quality monitoring.

**Entry Point:** `app/domains/analytics/services/calibration_service.py` — `record_explicit_feedback()`, `record_implicit_feedback()`

**Trigger:** (1) Explicit: POST `/api/v1/calibration/feedback`; (2) Implicit: `candidates_crud.py` stage change

**Key Files:**
- `app/domains/analytics/services/calibration_service.py` — `CalibrationService`
- `app/domains/analytics/repositories/calibration_repository.py` — `CalibrationRepository` (13 methods)
- `app/api/v1/calibration.py` — REST endpoints
- `app/api/v1/calibration_dashboard_v2.py` — calibration dashboard endpoints

**Key Details:**
- **Does NOT auto-adjust model weights** — CalibrationWeight model exists but weight adjustments require explicit `apply_suggestions` endpoint call.
- Tables: `calibration_events`, `calibration_suggestions`, `calibration_weights`.
- `ModelDriftService` monitors 4 drift dimensions on-demand.
- `ConfidencePolicyService` depends on `CalibrationEvent` data to tighten/loosen auto-approve thresholds.

**Related Features:** F-05, F-21

---

## F-23 · A/B Testing for Email Templates

**Status:** 🟢 Live
**Business Value:** Improves communication effectiveness by automatically routing candidates to the best-performing email variant using multi-armed bandit (Thompson sampling).

**Entry Point:** `app/shared/learning/ab_testing_service.py` — `ABTestingService`

**Trigger (read/select):** `template_service.py` calls `ABTestingService` to select the winning variant on send.
**Trigger (write/update):** `app/api/v1/email_tracking.py` receives open/click/reply webhooks.

**Key Details:**
- Thompson sampling via Beta distribution — no fixed exploration rate needed.
- `BanditPosteriorRepository` persists Beta parameters (alpha, beta) per template+variant.
- Weekly digest via `weekly_digest_service.py` exposes A/B performance.

**Related Features:** F-24

---

## F-24 · Implicit Feedback from Chat Behavior

**Status:** 🟢 Live
**Business Value:** Harvests learning signals from recruiter chat behavior (regenerating responses, correcting outputs, ignoring answers) without requiring explicit feedback actions.

**Entry Point:** `app/shared/learning/implicit_feedback_service.py` — `capture_regeneration()`, `capture_correction_delta()`, `capture_abandonment()`

**Trigger:** POST `/api/v1/lia-feedback/regenerate` or `/api/v1/lia-feedback/correction` from FE

**Key Details:**
- All 3 signals route through `FairnessGuard` before persisting.
- **Fail-open:** any learning failure never blocks the core chat handshake.
- `FeedbackService.record_implicit_negative()` demotes matching `learning_patterns` rows.

**Related Features:** F-22, F-23

---

## F-25 · Job Creation Wizard Orchestrator

**Status:** 🟢 Live
**Business Value:** Guides recruiters through AI-assisted conversational job creation in a single stateful LLM brain instead of a rigid multi-step form.

**Entry Point:** `app/domains/job_creation/services/wizard_session_service.py:987` — LIA_WIZARD_ORCHESTRATOR=1 check

**Trigger:** Recruiter starts new job creation via chat `/criar vaga` command, wizard button, or `start_creation_from_source` federated tool

**Key Files:**
- `app/domains/job_creation/orchestrator/wizard_orchestrator.py:374` — `WizardOrchestrator.process_turn()`
- `app/domains/job_creation/orchestrator/wizard_tools.py` — deterministic tool implementations
- `app/domains/job_creation/orchestrator/wizard_tool_registry.py` — `TOOL_DEFINITIONS`, `STAGE_TOOLS` allowlist

**Key Details:**
- **LIA_WIZARD_ORCHESTRATOR=1** active in dev `.env`. Legacy LangGraph nodes tombstoned with `RuntimeError` when `RAILS_API_URL` absent.
- `STAGE_TOOLS` allowlist prevents LLM from jumping wizard stages out of order.
- `wizard_empty_reply_fallback_total` Prometheus counter for observability.

**Related Features:** F-03, F-04, F-05, F-08, F-10, F-15

---

## F-26 · Sourcing / Talent Search

**Status:** 🟢 Live
**Business Value:** Multi-channel talent search combining internal database (pgvector semantic), external sources (Pearch AI, Apify, LinkedIn), boolean query generation, profile enrichment, and archetype-based searching.

**Entry Point:** `app/domains/sourcing/agents/sourcing_react_agent.py:86` — `SourcingReActAgent`

**Key Files:**
- `app/domains/sourcing/agents/sourcing_react_agent.py` — `SourcingReActAgent`
- `app/api/v1/candidate_search/search.py:134` — FairnessGuard wired; Funil search endpoint
- `app/api/v1/candidate_search/archetypes.py:1234` — FairnessGuard wired; archetype search
- `app/api/v1/rag_search.py` — RAG-based semantic candidate search (pgvector)

**Key Details:**
- FairnessGuard wired in 2 Funil entry points: `search.py:134` + `archetypes.py:1234`.
- FE Funil dual display on block: banner amber + LIA bubble.
- pgvector setup: `setup_pgvector` at `core/database.py:1069`.

**Related Features:** F-01, F-12, F-15, F-20

---

## F-27 · Offer Concierge Flow

**Status:** 🟢 Live
**Business Value:** Manages the full offer letter lifecycle with HITL gate on send and hard approval gate for companies with `manager_approval_for_offer` policy.

**Entry Point:** `app/domains/offer/domain.py:26` — `OfferDomain` (@register_domain)

**Key Files:**
- `app/domains/offer/agents/offer_concierge_agent.py:38` — `OfferConciergeAgent`
- `app/domains/offer/services/offer_service.py` — `check_can_send()`, `mark_sent()`

**Key Details:**
- **Hard gate pattern (canonical):** `check_can_send()` raises `PermissionError` subclass BEFORE any side effect. `mark_sent()` also enforces (defense-in-depth).
- `manager_approval_for_offer` policy toggle has a real consumer.

**Related Features:** F-14, F-15

---

## F-28 · Slash Commands in Unified Chat

**Status:** 🟢 Live
**Business Value:** Quick shortcuts for common recruiter actions directly in the chat input.

**Entry Point:** `plataforma-lia/src/components/unified-chat/slash-commands.ts` — `SLASH_COMMANDS` array (single source of truth)

**Key Details:**
- `/buscar` bare handled **entirely client-side** via `BUSCAR_BARE_REGEX` — no backend roundtrip.
- `/nova-conversa` is in `EXECUTE_ONLY_COMMAND_IDS` — executes immediately.
- `normalizeCommand()` for fuzzy matching (handles `/Criar Vaga` → `/criar vaga`).

**Related Features:** F-01, F-25

---

## F-29 · Reasoning / Activity Display

**Status:** 🟢 Live
**Business Value:** Shows recruiters a live feed of what the AI is doing (tool calls, reasoning phases) during complex operations.

**Entry Point:** `app/orchestrator/execution/agentic_loop.py:343` — `_emit_phase('understanding')`

**Key Files:**
- `app/orchestrator/execution/agentic_loop.py` — emit reasoning_step phases
- `libs/agents-core/lia_agents_core/streaming_callback.py` — emits via `_sse_frame_sink` ContextVar
- `plataforma-lia/src/components/chat/AgentActivityTimeline.tsx` — renders timeline

**Key Details:**
- Full `reasoning_step` phases only available with `LIA_WS_ASTREAM=on`.
- Activity labels in `activity-labels.ts` are i18n tokens.

**Related Features:** F-01, F-25

---

## F-30 · Token Budget & Rate Limiting

**Status:** 🟢 Live
**Business Value:** Prevents runaway LLM costs by enforcing per-tenant daily token budgets with plan-based tiers.

**Entry Point:** `app/domains/credits/services/token_budget_service.py` — `check_budget()`, `increment_usage()`

**Plan tiers:**

| Plan | Daily Budget |
|------|-------------|
| starter | 10,000 tokens |
| pro | 100,000 tokens |
| business | 500,000 tokens |
| enterprise | unlimited (-1) |

**Key Details:**
- Fail-open on Redis unavailability (budget check skipped, logs WARNING).
- Dev bypass: `_is_unlimited_dev_tenant` frozenset, **only active when `APP_ENV=development`**.
- `budget_exhausted` SSE event emitted at `agent_chat_sse.py:684`.

**Related Features:** F-01, F-16

---

## Architecture Cross-Reference

### Domain Registration Pattern
All 23 domains use `@register_domain` decorator from `app/domains/registry.py`. The decorator:
1. Enforces `ComplianceDomainPrompt` inheritance (**LIA-C01**, raises `TypeError` if violated)
2. Registers in `_DOMAIN_REGISTRY` singleton
3. Enables per-tenant YAML override via `_YamlDomainProxy` (Agent Studio)

### Agent Implementation Pattern
All 16 canonical ReAct agents use the triple-mixin:
```python
class MyAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    @register_agent('domain_id')
    ...
```

### Multi-Tenancy Invariants
- `company_id` **always from JWT** via `Depends(require_company_id)` or `get_verified_company_id()`
- **Never from payload, header, or LLM-generated arg**
- ContextVar `_current_company_id` in `app/middleware/auth_enforcement.py`

### Learning Loop Toggle Gates
All learning loops are per-tenant, governed by `load_learning_loops_toggles()`:
- `enabled=True` (master), `jd_similar_suggestion=True`, `bigfive_company_culture=True` — default ON
- `bigfive_department_history=False`, `wsi_question_effectiveness=False` — default OFF (opt-in)

### Active Environment Flags (dev, branch feat/benefits-prv-canonical)
| Flag | Value | Effect |
|------|-------|--------|
| `LIA_WIZARD_ORCHESTRATOR` | `1` | Activates WizardOrchestrator (F-25) |
| `LIA_FEDERATED_PRIMARY` | `true` (line 182) | RecruiterCopilotReActAgent as primary chat (F-01) |
| `LIA_HITL_GATE` | commented out | HITL gates dormant (F-14) |
| `RAILS_API_URL` | absent | Rails nodes tombstoned |
| `APP_ENV` | `development` | Dev tenant budget bypass active |
| `SERP_API_KEY` | absent | Salary benchmark → LLM estimation only (F-08) |

---

*Reference: `docs/architecture/AI_LAYER_TREE.md` (canonical architecture doc), `app/domains/DOMAIN_CATALOG.md` (domain registry). All paths relative to `/home/runner/workspace/lia-agent-system/` (Replit SSH replit-wedo-0405, branch feat/benefits-prv-canonical).*
