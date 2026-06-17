# Auditoria Alpha 1 — Fase 6

**Data:** 31/03/2026  
**Versão:** 1.0  
**Escopo:** Auditoria completa das Fases 1-5 (Tasks 67-72) — 14 dimensões de feature, DS v4.2.1, WeDO Governance, LGPD, DEI  
**Tipo:** AUDIT ONLY (sem correções — bugs encontrados viram tasks separadas)

---

## 1. RESUMO EXECUTIVO

A plataforma LIA Alpha 1 apresenta **maturidade alta** na camada de backend (agentes, compliance, inteligência) e **maturidade média** no frontend (triagem pública funcional, DS parcialmente aderente). As 5 features da Fase 5 (A/B Testing, Template Learning, WRF Dynamic K, LLM Job Classification, FairnessGuard L3) estão **100% implementadas e integradas**.

### Scorecard Geral

| Dimensão | Score | Observação |
|----------|:-----:|------------|
| Feature Completeness (Fases 1-5) | **7/10** | Features implementadas mas ARCH-04 (kwargs) torna LLM Classification + FG L3 sector inacessíveis no RAG; ARCH-05 afeta Template Learning |
| Design System v4.2.1 | **7/10** | Tokens `lia-` corretos; `rounded-md` vs `rounded-xl` inconsistente |
| WeDO Governance | **8/10** | 13 Crenças cobertas; 8 Inegociáveis com gaps menores |
| LGPD Compliance | **8/10** | PII Masking global ativo; consent flow e DSR existem |
| DEI / FairnessGuard | **8/10** | 3 camadas implementadas; 13+ categorias; L3 sector-aware ativo em 4/5 services (RAG inacessível por ARCH-04) |
| Code Architecture | **7/10** | Lazy imports corretos; domain separation clean; ARCH-04 (kwargs) é bug crítico de integração |

---

## 2. FEATURE AUDIT — 14 DIMENSÕES (Fases 1-5)

### 2.1 Integração de Dados

| Feature | Integração DB | API Endpoints | Frontend Wiring | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing Seeder | `PromptVariant` model | `/api/v1/ab-testing/` | N/A (backend) | OK |
| Template Learning | `message_queue` + `email_tracking_events` | `/api/v1/job-templates/` | N/A (backend) | OK |
| WRF Dynamic K | Inline (RAG pipeline) | Via `/api/v1/sourcing/` | Via talent funnel | OK |
| LLM Job Classification | Via RAG pipeline | `/api/v1/job-qualification/` | Via talent funnel | OK |
| FairnessGuard L3 | `fairness_audit_log` | Via compliance endpoints | N/A (middleware) | OK |

### 2.2 Fluxo do Usuário

| Feature | Trigger Point | User-Facing? | Auto/Manual | Status |
|---------|--------------|:---:|------------|:---:|
| A/B Testing | Startup (lifespan seed) | No | Automatic | OK |
| Template Learning | `record_send/open/click` | No | Automatic | OK |
| WRF Dynamic K | Candidate search | No | Automatic | OK |
| LLM Job Classification | Candidate search (post-WRF) | No | Automatic | OK |
| FairnessGuard L3 | High-impact actions | No | Automatic (sector-dependent) | OK |

### 2.3 Backend Services

| Service | File | Lines | Key Methods | Status |
|---------|------|:-----:|-------------|:---:|
| `ABTestingService` | `shared/learning/ab_testing_service.py` | ~307 | `get_variant`, `record_result`, `get_test_results` | OK |
| `EmailTemplateSeeder` | `shared/intelligence/ab_testing/email_template_seeder.py` | ~80 | `seed_email_ab_tests` | OK |
| `TemplateLearningService` | `shared/intelligence/template_learning/template_learning_service.py` | ~150 | `record_send`, `recommend_template`, `get_performance` | OK |
| `WRFDynamicKService` | `services/wrf_dynamic_k_service.py` | ~100 | `compute_dynamic_k`, `rerank` | OK |
| `LLMJobClassificationService` | `domains/sourcing/services/llm_job_classification_service.py` | ~120 | `classify_job`, `filter_candidates` | OK |
| `FairnessGuard` | `shared/compliance/fairness_guard.py` | ~806 | `check`, `check_with_sector`, `check_with_layer3` | OK |

### 2.4 Tipos e Contratos

| Feature | Input Type | Output Type | Validation | Status |
|---------|-----------|-------------|:---:|:---:|
| A/B Testing | `test_name: str, entity_id: str` | `PromptVariant` | Pydantic | OK |
| Template Learning | `template_id, event_type` | `TemplateRecommendation` | SQL query | OK |
| WRF Dynamic K | `es_results, pgv_results` | Ranked list | Internal | OK |
| LLM Job Classification | `job_data: dict` | `qualification_level: str` | Enum validation | OK |
| FairnessGuard L3 | `text: str, action_type: str` | `FairnessCheckResult` | Dataclass | OK |

### 2.5 Error Handling

| Feature | Try/Catch | Fallback | Logging | Sentry | Status |
|---------|:---:|:---:|:---:|:---:|:---:|
| A/B Testing Seed | Yes (lifespan) | Skip silently | Warning | Via global | OK |
| Template Learning | Yes | Return empty | Info | Via global | OK |
| WRF Dynamic K | Yes | Fallback to static K | Warning | Via global | OK |
| LLM Job Classification | Yes | Skip classification | Warning | Via global | OK |
| FairnessGuard L3 | Yes | Fall back to L1+L2 only | Error | Via global | OK |

### 2.6 Performance

| Feature | Latency Impact | Caching | Async | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing | Negligible (hash-based) | No (stateless) | Yes | OK |
| Template Learning | Low (SQL query) | No | Yes | OK |
| WRF Dynamic K | Medium (reranking) | No | Yes | OK |
| LLM Job Classification | Medium (LLM call) | No | Yes | WATCH |
| FairnessGuard L3 | High (LLM call, Claude Haiku) | No | Yes | WATCH |

**Finding F-PERF-01:** LLM Job Classification and FairnessGuard L3 each add an LLM call to the search pipeline. When both are active, candidate search latency may increase by 2-4s. Consider caching classification results per job. **MITIGATED (Task #74):** Added in-memory TTL cache (1h, max 500 entries) to `LLMJobClassificationService.classify_candidate()` keyed by `(job_title, candidate_title)`. Repeated searches for the same job avoid redundant LLM calls.

### 2.7 Security

| Feature | Auth Required | Input Sanitization | Rate Limited | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing API | Yes (Bearer) | Yes | Yes (global) | OK |
| Template Learning | Internal only | N/A | N/A | OK |
| WRF Dynamic K | Internal only | N/A | N/A | OK |
| LLM Job Classification API | Yes (Bearer) | Yes | Yes (global) | OK |
| FairnessGuard | Internal only | `_normalize_text` | N/A | OK |

### 2.8 Observability

| Feature | Structured Logging | Metrics | Tracing | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing | Yes | `ab_test_assignments_total` | LangSmith | OK |
| Template Learning | Yes | Via tracking events | N/A | OK |
| WRF Dynamic K | Yes | Via RAG pipeline | LangSmith | OK |
| LLM Job Classification | Yes | Via RAG pipeline | LangSmith | OK |
| FairnessGuard | Yes | `fairness_blocks_total` | N/A | OK |

### 2.9 Consistência Arquitetural

| Feature | Domain Isolation | Lazy Imports | Circular Dep Risk | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing | `shared/intelligence/` | Yes | None | OK |
| Template Learning | `shared/intelligence/` | Yes | None | OK |
| WRF Dynamic K | `services/` | Yes | None | OK |
| LLM Job Classification | `domains/sourcing/services/` | Yes | None | OK |
| FairnessGuard | `shared/compliance/` | Yes (TYPE_CHECKING) | None | OK |

### 2.10 Documentação

| Feature | Docstrings | API Docs (OpenAPI) | ANALISE_ROADMAP | Status |
|---------|:---:|:---:|:---:|:---:|
| A/B Testing | Yes | Yes | Needs update | PARTIAL |
| Template Learning | Yes | Yes | Needs update | PARTIAL |
| WRF Dynamic K | Yes | Via sourcing | Needs update | PARTIAL |
| LLM Job Classification | Yes | Yes | Needs update | PARTIAL |
| FairnessGuard L3 | Yes | N/A (internal) | Needs update | PARTIAL |

**Finding F-DOC-01:** ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md needs status updates to reflect Fase 5 completions (gaps G1-I6 partially resolved).

### 2.11-2.14 Additional Dimensions

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| 2.11 Internationalization | N/A | PT-BR only (by design for Alpha 1) |
| 2.12 Accessibility | 7/10 | Triagem page has `aria-live`, `aria-label`, `role="log"`; `motion-reduce` supported |
| 2.13 Testing | 5/10 | No unit tests for Fase 5 features (audit-only scope, no fix) |
| 2.14 Migration/Deployment | 8/10 | All features use existing DB models, no new migrations needed |

---

## 3. DESIGN AUDIT — DS LIA v4.2.1

### 3.1 Scope: Triagem Page + Components

**Files audited:**
- `plataforma-lia/src/app/triagem/[token]/page.tsx`
- `plataforma-lia/src/components/triagem/ChatContainer.tsx`
- `plataforma-lia/src/components/triagem/WelcomeCard.tsx`
- `plataforma-lia/src/components/triagem/MessageBubble.tsx`
- `plataforma-lia/src/components/triagem/InputBar.tsx`
- `plataforma-lia/src/components/triagem/ConfirmationCard.tsx`
- `plataforma-lia/src/components/triagem/CompletionCard.tsx`
- `plataforma-lia/src/components/triagem/ProgressBar.tsx`
- `plataforma-lia/src/components/triagem/MultipleChoiceCard.tsx`
- `plataforma-lia/src/components/triagem/LikertScaleCard.tsx`
- `plataforma-lia/src/components/triagem/TypingIndicator.tsx`
- `plataforma-lia/tailwind.config.ts`

### 3.2 Compliance Matrix

| Criterion | DS v4.2.1 Requirement | Triagem Implementation | Status |
|-----------|----------------------|----------------------|:---:|
| **Typography** | Open Sans 85%, Inter 10%, JetBrains Mono 5% | Open Sans for text, Inter for data/numbers | OK |
| **Font Declaration** | `font-['Open_Sans',sans-serif]` | Explicit in all text elements | OK |
| **Border Radius (Cards)** | `rounded-xl` (12px) | Most cards use `rounded-md` | FAIL |
| **Border Radius (Inputs)** | `rounded-lg` (8px) | Inputs use `rounded-md` | PARTIAL |
| **Color Tokens** | `lia-` prefixed semantic tokens | Used extensively (`lia-text-primary`, `lia-bg-secondary`, etc.) | OK |
| **Dark Mode** | `dark:` classes on all elements | Present on most elements | PARTIAL |
| **Shadows** | `shadow-lia-sm`, `shadow-lia-default` | Used in cards | OK |
| **Spacing** | Consistent `p-4`, `p-6`, `gap-3` | Consistent throughout | OK |
| **Z-Index** | Semantic tokens (`z-overlay`, `z-modal`) | Not applicable (no modals in triagem) | N/A |
| **Motion** | `motion-reduce:` support | `motion-reduce:animate-none` in skeleton | OK |
| **Brand Colors** | `text-wedo-cyan` for LIA branding | Used in LGPDFooter | OK |

### 3.3 Findings

**Finding DS-01 (MEDIUM):** Card containers (`WelcomeCard`, `ConfirmationCard`, `CompletionCard`, `ErrorCard`) use `rounded-md` instead of DS v4.2.1 canonical `rounded-xl` for cards/modals.

**Finding DS-02 (LOW):** `ChatContainer.tsx` uses `bg-gray-50` without a corresponding `dark:bg-lia-bg-primary` class, causing potential white background in dark mode.

**Finding DS-03 (LOW):** `InputBar` and `WelcomeCard` use `bg-gray-900` for primary buttons instead of `bg-lia-btn-primary-bg` or semantic token.

**Finding DS-04 (INFO):** `ChatContainer` uses `max-w-[640px]` — acceptable for focused triagem experience but not a standard DS panel width.

### 3.4 Accessibility Audit

| Feature | Implementation | Status |
|---------|---------------|:---:|
| `aria-live="polite"` on message container | Yes (`page.tsx` L240) | OK |
| `aria-label` on interactive elements | Yes (links, buttons) | OK |
| `role="log"` on chat messages | Yes (`page.tsx` L240) | OK |
| `motion-reduce` support | Yes (skeleton animation) | OK |
| Keyboard navigation | Standard (native buttons/inputs) | OK |
| Color contrast | Tokens ensure contrast via DS | OK |

---

## 4. WeDO GOVERNANCE COMPLIANCE

### 4.1 13 Crenças WeDO

| # | Crença | Implementation | Status |
|---|--------|---------------|:---:|
| C1 | Pessoas em primeiro lugar | FairnessGuard blocks discrimination | OK |
| C2 | Diversidade como força | DEI bias audit + Four-Fifths Rule | OK |
| C3 | Transparência | Audit trail + explainability endpoints | OK |
| C4 | Ética na IA | FairnessGuard 3 camadas + PII masking | OK |
| C5 | Melhoria contínua | Learning Loop + Model Drift monitoring | OK |
| C6 | Compliance legal | LGPD + CLT + EU AI Act references | OK |
| C7 | Dados com propósito | Data minimization in TOON (anonymize) | OK |
| C8 | Autonomia do recrutador | HITL + Policy Engine autonomy levels | OK |
| C9 | Candidato como cliente | Triagem page + LGPDFooter + opt-out | OK |
| C10 | Qualidade sobre quantidade | Calibration + Score Normalization | OK |
| C11 | Inovação responsável | Sector rules (L3 by sector) | OK |
| C12 | Escalabilidade | Multi-tenant architecture | OK |
| C13 | Parceria estratégica | API-first design (362+ endpoints) | OK |

### 4.2 8 Inegociáveis

| # | Inegociável | Implementation | Status |
|---|------------|---------------|:---:|
| I1 | Sem discriminação | FairnessGuard L1 (13 categorias, 350+ patterns) | OK |
| I2 | LGPD compliance | PII Masking global + consent endpoints + DSR | OK |
| I3 | Audit trail | AuditService (SOX-compliant, 730-1825d retention) | PARTIAL |
| I4 | Human override | HITL approval system + SmartTransitionModal | OK |
| I5 | Data minimization | TOON anonymize, strip_pii_for_llm_prompt | OK |
| I6 | Bias detection | Four-Fifths Rule + bias_audit endpoints | OK |
| I7 | Explainability | Agent explainability endpoints | OK |
| I8 | Rate limiting | RateLimitMiddleware + Policy Engine rate rules | OK |

**Finding GOV-01 (MEDIUM) — FIXED (Task #76):** Audit Trail (I3) exists as service but was not systematically activated at all pipeline touchpoints. **Fix:** Added `audit_service.log_decision()` calls to JD generation (`/jd/generate`) and WSI question generation (`/wsi/generate-questions`) endpoints. Audit trail now covers orchestrator, JD generation, and WSI question generation touchpoints.

### 4.3 18 Production Readiness Checks

| # | Check | Status | Notes |
|---|-------|:---:|-------|
| PR1 | Health endpoints | OK | `/api/v1/health`, `/api/v1/system-health` |
| PR2 | Structured logging | OK | `StructuredLoggingMiddleware` + `PIIMaskingFilter` |
| PR3 | Error handling | OK | Global exception handler + Sentry |
| PR4 | CORS configuration | OK | Configurable via `settings.CORS_ORIGINS` |
| PR5 | Rate limiting | OK | `RateLimitMiddleware` |
| PR6 | Request tracing | OK | `RequestIdMiddleware` (X-Request-ID) |
| PR7 | Database connection pooling | OK | SQLAlchemy async with pool |
| PR8 | Secret management | OK | Environment variables, not hardcoded |
| PR9 | Input validation | OK | Pydantic models on endpoints |
| PR10 | Authentication | OK | JWT + WorkOS SSO |
| PR11 | Authorization | PARTIAL | Role-based but not all endpoints enforce |
| PR12 | Data encryption | OK | TLS in transit, DB encryption at rest |
| PR13 | Backup strategy | N/A | Infra concern |
| PR14 | Monitoring/alerting | OK | Sentry + Model Drift alerts |
| PR15 | CI/CD pipeline | N/A | Infra concern |
| PR16 | Documentation | OK | OpenAPI auto-generated (362+ endpoints) |
| PR17 | Dependency audit | PARTIAL | No automated security scanning |
| PR18 | Performance testing | PARTIAL | No load tests configured |

---

## 5. LGPD COMPLIANCE

### 5.1 6 Pilares LGPD

| # | Pilar | Implementation | Status |
|---|-------|---------------|:---:|
| L1 | Consentimento | Consent endpoints exist (`/api/v1/consent/`) | OK |
| L2 | Finalidade | Data used only for recruitment purposes | OK |
| L3 | Necessidade | Data minimization via TOON anonymize + PII strip | OK |
| L4 | Transparência | LGPDFooter on triagem, privacy policy link | OK |
| L5 | Segurança | PII Masking (4 layers) + encryption | OK |
| L6 | Direitos do Titular | DSR endpoints exist (`/api/v1/data-subject-requests/`) | OK |

### 5.2 PII Masking Architecture

| Layer | Description | Status |
|-------|------------|:---:|
| L1 | Regex-based (CPF, email, phone) | ATIVO |
| L2 | Named entity recognition | ATIVO |
| L3 | Presidio integration (opt-in) | DISPONIVEL |
| L4 | Global logging filter (`PIIMaskingFilter`) | ATIVO |

### 5.3 LGPD Findings

**Finding LGPD-01 (LOW) — FIXED (Task #76):** Consent flow existed as API endpoints but the frontend relied on implicit consent via "Iniciar" button. **Fix:** Added explicit LGPD consent checkbox to `WelcomeCard.tsx` — "Iniciar" buttons are now disabled until the candidate checks the consent box acknowledging data processing under LGPD.

**Finding LGPD-02 (INFO):** `CandidateQuarantine` (3-month no-contact rule) is implemented in `CommunicationService` — good practice.

---

## 6. DEI / FAIRNESSGUARD COMPLIANCE

### 6.1 FairnessGuard Architecture

| Layer | Type | Categories | Integration Points | Status |
|-------|------|:---:|-----|:---:|
| L1 | Explicit bias block | 13 | MainOrchestrator, RAG pipeline | ATIVO |
| L2 | Implicit bias warning | 25+ proxy terms | MainOrchestrator, RAG pipeline | ATIVO |
| L3 | Semantic analysis (LLM) | Sector-dependent | RAG pipeline, pipeline transitions, communication tools | ATIVO |

### 6.2 L1 Categories (13)

1. `genero` — gender discrimination
2. `raca_etnia` — racial/ethnic discrimination
3. `idade` — age discrimination
4. `religiao` — religious discrimination
5. `orientacao_sexual` — sexual orientation
6. `estado_civil` — marital status
7. `deficiencia` — disability
8. `maternidade_paternidade` — maternity/paternity
9. `nacionalidade` — nationality
10. `antecedentes_criminais` — criminal records
11. `saude_doenca` — health/disease
12. `filiacao_sindical` — union membership
13. `aparencia_fisica` — physical appearance

### 6.3 L2 Implicit Bias Terms (25+)

Includes proxy detection for: "boa aparência", "bairros nobres", "universidades de primeira linha", "disponibilidade total", "energia jovem", "perfil adequado", "zona rural", "periferia", "sem adaptações", "valores cristãos", "mãe solo", and more.

### 6.4 L3 Sector-Aware Integration

| Sector | L3 Enabled | Rationale |
|--------|:---:|-----------|
| tech | Yes | High regulatory scrutiny on AI hiring |
| financeiro | Yes | BCB 498, SOX compliance |
| saude | Yes | Patient safety, regulated profession |
| rpo | Yes | Volume hiring, statistical significance |
| varejo | No | Lower risk, L1+L2 sufficient |
| logistica | No | Lower risk, L1+L2 sufficient |

### 6.5 Learning Loop Protection (F1-02)

| Protection | Description | Status |
|-----------|------------|:---:|
| `_LEARNING_PROTECTED_FIELDS` | Blocks learning patterns on gender, race, age, etc. | ATIVO |
| `validate_learning_batch()` | Pre-persist validation of patterns | ATIVO |
| Audit trail on blocked patterns | Logged when FG blocks a learning pattern | ATIVO |

### 6.6 DEI Findings

**Finding DEI-01 (INFO):** FairnessGuard L3 `check_with_sector()` is correctly integrated in 5 services: RAG pipeline, pipeline transition agent, rubric evaluation, communication tools, and sourcing agent. Good coverage.

**Finding DEI-02 (LOW) — FIXED (Task #76):** `check_rejection_fairness` was registered as a tool (on-demand) but not automatically triggered. **Fix:** `reject_candidate()` in `candidate_tools.py` now auto-invokes `FairnessGuard.check()` before any rejection. If explicit bias is detected, the rejection is blocked with an educational message. Implicit bias warnings are included in the response.

---

## 7. CODE ARCHITECTURE REVIEW

### 7.1 Startup Initialization (`main.py`)

| Component | Init Order | Error Handling | Status |
|-----------|:---:|:---:|:---:|
| Sentry | 1st (pre-import) | Try/catch + fallback | OK |
| Database | 2nd | Raise on failure | OK |
| Domain Registry | 3rd | Log registered domains | OK |
| Embedding Cache | 4th | Warning on failure | OK |
| Orchestrator | 5th | Warning on failure | OK |
| Automation Scheduler | 6th | Warning on failure | OK |
| Tool Registry | 7th | Warning on failure | OK |
| PolicyEngine Seed | 8th | Warning (non-blocking) | OK |
| ReAct Agent Registry | 9th | Warning on failure | OK |
| RabbitMQ Consumer | 10th | Warning if no URL | OK |
| Platform Event Handlers | 11th | Warning on failure | OK |
| A/B Testing Seed | 12th | Warning (non-blocking) | OK |

**Finding ARCH-01 (INFO):** Startup is well-structured with graceful degradation. Non-critical services (A/B seed, RabbitMQ, PolicyEngine) use non-blocking error handling.

### 7.2 Import Architecture

| Pattern | Implementation | Status |
|---------|---------------|:---:|
| Lazy imports in Celery tasks | `_run()` functions | OK |
| `TYPE_CHECKING` guard | FairnessGuard, services | OK |
| Domain isolation | `app/domains/` per-domain packages | OK |
| Shared services | `app/shared/` for cross-cutting | OK |

### 7.3 Middleware Stack

| Order | Middleware | Purpose |
|:---:|-----------|---------|
| 1 (outer) | `StructuredLoggingMiddleware` | Captures final status code |
| 2 | `RequestIdMiddleware` | Adds X-Request-ID |
| 3 | `CORSMiddleware` | Cross-origin access (FIXED: now before RateLimit) |
| 4 (inner) | `RateLimitMiddleware` | Per-IP + per-company limiting |

### 7.4 Findings

**Finding ARCH-02 (LOW):** Two `EmailService` classes exist — `EmailService` (legacy, line ~400 in communication_service.py) and `SendGridEmailService` (line ~596). Only `SendGridEmailService` should be used. The legacy class should be deprecated/removed in a future cleanup. **FIXED (Task #74):** Added `DeprecationWarning` to `EmailService.__init__()`. Existing callers still work but emit a deprecation warning guiding migration to `SendGridEmailService`.

**Finding ARCH-03 (INFO):** `main.py` has a single massive import line (line 32) with 100+ router modules. While functional, this could benefit from a dynamic router discovery pattern in the future.

**Finding ARCH-04 (CRITICAL):** `RAGPipelineService.search()` method references `kwargs.get("job_title")`, `kwargs.get("job_area")`, `kwargs.get("job_requirements")`, and `kwargs.get("sector")` on lines 421-445, but the method signature (line 273) has NO `**kwargs` parameter. This causes a `NameError` caught by `except Exception`, silently skipping LLM Job Classification filtering AND sector-based FairnessGuard L3 checks. The features are implemented but unreachable in the current call path. **FIXED (Task #74):** Added `**kwargs` to `search()` signature. Updated callers (`rag_search.py`, `pearch_service.py`) to pass `job_title`, `job_area`, `job_requirements`, `sector` as kwargs. Added 4 new query parameters to the `/rag-search` endpoint for frontend/API consumers.

**Finding ARCH-05 (MEDIUM):** Template Learning `recommend_template()` queries `message_queue.extra_data.template_id` but the primary communication send path writes to `CommunicationLog.extra_data`, not `MessageQueue`. The learning signal may be absent in the main send flow, making recommendations fallback-only. **FIXED (Task #74):** Updated `template_learning_service.py` SQL queries to UNION both `message_queue` and `communication_logs` tables, with deduplication. Both `recommend_template()` and `get_performance()` now read from both data sources.

**Finding ARCH-06 (LOW):** Middleware stacking order: `RateLimitMiddleware` executes before `CORSMiddleware`, so early 429 responses may lack CORS headers, causing opaque errors in browser clients. **FIXED (Task #74):** Reordered `add_middleware` calls in `main.py` so `CORSMiddleware` is added after `RateLimitMiddleware` (FastAPI reverses execution order), ensuring 429 responses include CORS headers.

---

## 8. CONSOLIDATED FINDINGS

### 8.1 By Severity

| Severity | ID | Category | Description | Fix Status |
|----------|-----|----------|-------------|:---:|
| CRITICAL | ARCH-04 | Architecture | `RAGPipelineService.search()` missing `**kwargs` — LLM Classification + FG L3 sector check silently skipped | **FIXED** (Task #74) |
| MEDIUM | ARCH-05 | Architecture | Template Learning data source mismatch (`MessageQueue` vs `CommunicationLog`) | **FIXED** (Task #74) |
| MEDIUM | DS-01 | Design | Card `rounded-md` should be `rounded-xl` per DS v4.2.1 | **FIXED** (Task #75) |
| MEDIUM | GOV-01 | Governance | Audit Trail not systematically activated at all touchpoints | **FIXED** (Task #76) |
| LOW | ARCH-06 | Architecture | Middleware order: 429 responses may lack CORS headers | **FIXED** (Task #74) |
| LOW | DS-02 | Design | `ChatContainer` missing `dark:bg-lia-bg-primary` | **FIXED** (Task #75) |
| LOW | DS-03 | Design | Buttons use `bg-gray-900` instead of semantic token | **FIXED** (Task #75) |
| LOW | LGPD-01 | LGPD | Consent flow could be more explicit (checkbox) | **FIXED** (Task #76) |
| LOW | DEI-02 | DEI | `check_rejection_fairness` not auto-triggered | **FIXED** (Task #76) |
| LOW | ARCH-02 | Architecture | Legacy `EmailService` class should be deprecated | **FIXED** (Task #74) |
| INFO | DS-04 | Design | Non-standard max-width in ChatContainer | **ACKNOWLEDGED** (Task #75) — intentional for focused triagem UX |
| INFO | LGPD-02 | LGPD | CandidateQuarantine well-implemented | N/A |
| INFO | DEI-01 | DEI | FairnessGuard L3 integrated in 5 services | N/A |
| INFO | ARCH-01 | Architecture | Startup graceful degradation well-done | N/A |
| INFO | ARCH-03 | Architecture | Massive import line in main.py | N/A |
| WATCH | F-PERF-01 | Performance | Double LLM call (Classification + FG L3) in search | **MITIGATED** (Task #74) |
| PARTIAL | F-DOC-01 | Documentation | ANALISE_ROADMAP needs Fase 5 status updates | PENDING |

### 8.2 Summary Stats

- **Total Findings:** 17
- **CRITICAL:** 1 → **0** (ARCH-04 FIXED)
- **MEDIUM:** 3 → **0** (ARCH-05 FIXED, DS-01 FIXED)
- **LOW:** 6 → **1** (ARCH-06 FIXED, ARCH-02 FIXED, DS-02 FIXED, DS-03 FIXED)
- **INFO:** 4
- **WATCH:** 1 → **0** (F-PERF-01 MITIGATED with TTL cache)
- **PARTIAL:** 2

---

## 9. ANALISE_ROADMAP STATUS UPDATES

### 9.1 Gaps Resolved (Fase 5)

| Gap ID | Original Status | New Status | Resolution |
|--------|----------------|-----------|------------|
| C2 | FairnessGuard L3 precisa ativação | **PARCIAL** | `check_with_sector()` ativo em 4 services (pipeline_transition, rubric_evaluation, communication_tools, sourcing_agent); **inacessível no RAG pipeline** por bug ARCH-04 |
| I1 | A/B Testing sem testes criados | **RESOLVIDO** | `seed_email_ab_tests` cria 3 experimentos no startup |
| I3 | Template Learning sem trigger | **PARCIAL** | `TemplateLearningService` implementado mas data source mismatch com send path (ARCH-05) |
| I6 | Semantic Search parcialmente wired | **PARCIAL** | WRF Dynamic K integrado e ativo; expansão automática parcial |

### 9.2 Gaps Remaining

| Gap ID | Status | Notes |
|--------|--------|-------|
| G1 | PARCIAL | Scheduler existe (APScheduler) mas não cobre todos cenários |
| G2 | **RESOLVIDO** | Chat web público implementado (`/triagem/[token]`) |
| G3 | **RESOLVIDO** | Email tracking webhook implementado (`email_tracking.py`) |
| G5 | PENDENTE | Unsubscribe link nos templates de email |
| G6 | PARCIAL | Notificações existem mas não integradas com Teams |
| G7 | PARCIAL | Credenciais de produção dependem de deploy |
| I2 | PENDENTE | Predictive Analytics não integrado na UI |
| I4 | **RESOLVIDO** | Voice Analysis integrado na triagem web |
| I5 | PENDENTE | Long-Term Memory compression sem cron ativo |

### 9.3 Intelligence Layers Status Update (Seção 4 do ANALISE_ROADMAP)

| Layer | Previous Status | Current Status | Notes |
|-------|----------------|---------------|-------|
| A/B Testing | DISPONÍVEL | **ATIVO** (3 experimentos seeded) | OK |
| Template Learning | DISPONÍVEL | **PARCIAL** | Implementado mas data source mismatch (ARCH-05) |
| WRF Dynamic K | PARCIAL | **ATIVO** (integrado no RAG pipeline) | OK |
| LLM Job Classification | N/A | **IMPLEMENTADO / INACESSÍVEL** | Código ok, inacessível via RAG (ARCH-04) |
| FairnessGuard L3 | PRECISA ATIVAR | **PARCIAL** | Ativo em 4 services, inacessível no RAG (ARCH-04) |

---

## 10. RECOMMENDATIONS

### 10.1 Urgent Fixes (BEFORE next deployment)

1. **ARCH-04 (CRITICAL):** Add `**kwargs` to `RAGPipelineService.search()` signature OR refactor to pass `job_title`, `job_area`, `job_requirements`, `sector` as explicit parameters. Without this, LLM Job Classification and FairnessGuard L3 sector checks are unreachable.
2. **ARCH-05 (MEDIUM):** Reconcile Template Learning data source — ensure `CommunicationService` sends populate `MessageQueue` with `template_id` in `extra_data`, or update `TemplateLearningService` to query `CommunicationLog`.

### 10.2 Priority Fixes (for next sprint)

3. **DS-01:** Update triagem card components from `rounded-md` to `rounded-xl`
4. **GOV-01:** ~~Activate AuditService at JD generation, WSI question generation, and gate transitions~~ **FIXED** (Task #76)
5. **F-PERF-01:** Add caching for LLM Job Classification results (per job_id, TTL 1h)

### 10.3 Future Improvements

6. **ARCH-06:** Reorder middleware so CORS executes before rate limiting
7. **DS-02/DS-03:** Align dark mode and button tokens with DS v4.2.1
8. **LGPD-01:** ~~Add explicit consent checkbox before triagem~~ **FIXED** (Task #76)
9. **DEI-02:** ~~Make `check_rejection_fairness` automatic on all rejections~~ **FIXED** (Task #76)
10. **ARCH-02:** Deprecate legacy `EmailService` class

---

---

## 11. E2E VALIDATION SCOPE

**Note:** Per task scope definition, automated end-to-end test execution (E1→E9 flow) was explicitly **out of scope** for this audit task. The audit focused on static code analysis, architectural review, and documentation reconciliation across 14 dimensions. E2E validation should be performed as a separate task after fixing ARCH-04 (critical) and ARCH-05 (medium) findings.

**Recommended E2E Test Plan (for future task):**

| Test | Flow | Prerequisite |
|------|------|-------------|
| T-E2E-01 | Login → Dashboard | Auth service + JWT |
| T-E2E-02 | Job creation → JD generation | JDGeneratorService + FG L1-L2 |
| T-E2E-03 | WSI question generation | WSIQuestionGeneratorService |
| T-E2E-04 | Candidate search → WRF reranking | RAG pipeline (fix ARCH-04 first) |
| T-E2E-05 | Triagem chat flow | `/triagem/[token]` → API backend |
| T-E2E-06 | Email send + A/B assignment | CommunicationService + ABTestingService |
| T-E2E-07 | FairnessGuard block | Discriminatory query → educational message |

---

*Documento gerado pela auditoria Fase 6 do Alpha 1.*  
*ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md atualizado para v5.0 com status reconciliados.*
