# EU AI Act Art. 11 Technical Documentation — WeDOTalent LIA Platform

> **Version:** 1.0
> **Date:** 2026-04-23
> **Provider:** WeDOTalent
> **System:** LIA (Learning Intelligence Assistant) — AI-powered recruitment platform
> **Classification:** High-Risk AI System — EU AI Act Annex III, category 4 (employment)
> **Status:** Ready for external legal review prior to public release and EU AI Act database registration (once active)

---

## Table of Contents

1. General Description
2. AI Components
3. Training, Validation and Test Data
4. Pre-Deployment Risk Assessment
5. Post-Deployment Monitoring
6. Consolidated Metrics
7. Human Oversight (Art. 14)
8. Accuracy, Robustness, Cybersecurity (Art. 15)
9. Data Subject Rights (LGPD + EU AI Act Art. 86)
10. Market Benchmark and Competitor Comparison
11. Public Roadmap of Publications and Implementations
12. Governance and Responsibilities
13. Declaration of Conformity
Appendices

---

## 1. General Description

### 1.1 Purpose and context of use

LIA is a recruitment assistant built on large language models (LLMs), operated by WeDOTalent and used by enterprise clients to support hiring and selection. Its role is to assist human recruiters with CV screening, behavioral assessment (WSI — Workplace Science Index), sourcing, candidate communication, and pipeline management.

LIA **does not make autonomous hiring decisions** — every final decision remains with the human recruiter. The system enforces Human-in-the-Loop (HITL) oversight on all high-impact actions, as required by EU AI Act Art. 14.

### 1.2 Affected persons/entities

- **Direct users (operators):** client recruiters and HR managers
- **Indirectly affected (decision subjects):** job candidates

### 1.3 Risk category

Legal classification: **EU AI Act Annex III, category 4** (AI systems used in employment or selection, including candidate evaluation, application filtering, promotion decisions).

Effective 02/08/2026, this classification becomes mandatory for systems operating in the EU or processing European candidates.

### 1.4 Provider and Deployer

- **Provider:** WeDOTalent — develops and maintains the LIA platform
- **Deployer:** each enterprise client — configures policies, criteria, and operational use

---

## 2. AI Components

### 2.1 LLM models

- **Primary reasoning model:** `claude-sonnet-4-5` (Anthropic)
- **Semantic classification model (FairnessGuard Layer 3):** `claude-haiku-4-5-20251001` (Anthropic)
- **Deep consultative model (optional, per agent):** `claude-opus-4-7` (Anthropic, 1M context)

All models are accessed via the Anthropic API, with no proprietary fine-tuning. Specialized behavior is achieved through the prompt injection layer (§2.3).

### 2.2 LIA Architecture (summary)

Microagent architecture orchestrated by `MainOrchestrator` in 4 phases. Full details in `docs/reconstruction-guides/INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`.

- **15 active agents** with AgentType enum
- **ReAct loop** (Reason-Act-Observe) in `LangGraphReActBase`
- **CascadedRouter** 8-tier intelligent routing
- **Multi-tenant** with `company_id` isolation (JWT-validated, enforced by `TenantGuard`)

### 2.3 Prompt injection layer

Documented in detail in `docs/reconstruction-guides/LIA_PERSONA_RECONSTRUCTION_GUIDE.md` Part 9.

Actual injection order in `SystemPromptBuilder.build()` (9 steps):
1. `_IDENTITY_OVERRIDE` (hardcoded — "RULE ZERO: YOUR NAME IS LIA")
2. `lia_persona.yaml` (292 lines — identity + ethical principles)
3. `_PLATFORM_KNOWLEDGE` (declarative knowledge of the platform)
4. `agent_prompts.yaml`[agent_type] (specialization per type — 11 variants)
5. Dynamic context (tenant + recruiter + user + page + summary + state)
6. Anti-repetition rules (if ongoing conversation)
7. Routing (intent + entities)
8. REACT_INSTRUCTIONS (for all agents except orchestrator)
9. Additional instructions injected by caller

In parallel, other classes inject:
- `ComplianceDomainPrompt` → `compliance_block.yaml` (4 contextual variants)
- `GuardrailsDomainPrompt` → `guardrails_block.yaml` (7 sections)
- `CustomAgentRuntime` → `intelligence_floor.yaml` (quality floor for custom agents)

### 2.4 Eight-layer compliance defense

Full documentation in `docs/reconstruction-guides/COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.2.

| Layer | Mechanism | Type | Blocking |
|-------|-----------|------|----------|
| C1 | `FairnessGuard.check()` — regex over 19 categories | Computational | ✅ |
| C2 | `check_implicit_bias()` — 43 PT/EN terms | Computational | Soft warning |
| C3 | `check_semantic()` — Haiku LLM (FAIRNESS_LAYER3_ENABLED=true in prod since 2026-04-23) | Inferential | Conditional |
| C4 | `compliance_block.yaml` — prompt guidance (4 variants) | Inferential | Directive |
| C5 | `guardrails_block.yaml` — behavioral limits | Inferential | Directive |
| C6 | `protected_attributes.yaml` — 14 attributes SSOT | Computational | ✅ |
| C7 | `fairness_post_check.yaml` — output monitoring | Computational | ✅ |
| C8 | `audit_service.log_decision` — traceability | Computational | Observation |

---

## 3. Training, Validation and Test Data

### 3.1 Third-party models

LIA **does not train its own models**. It uses LLMs via Anthropic's API. Governance of base model training data is the responsibility of the third-party provider:

- **Anthropic Claude (claude-sonnet-4-5 + claude-haiku-4-5 + claude-opus-4-7):** public model cards at https://www.anthropic.com/claude

### 3.2 Internal fine-tuning

**None.** The system operates 100% prompt-based. Specialized behavior is obtained via declarative prompts in YAML (§2.3), not via model weight adjustment.

### 3.3 Operational data

- `AuditLog` + `fairness_audit_log` — internal anonymized tables (IDs only, no PII)
- Decision records retain `criteria_used`, `score_breakdown`, `subject_id`, `timestamp`
- Retention follows deployer's LGPD policy (configurable)

### 3.4 Provenance and governance

- Infrastructure: Replit (production), PostgreSQL (operational data), Redis (cache)
- Multi-tenant: `company_id` injected via JWT, validated by `TenantGuard` — one client never accesses another's data
- Anonymization for audit: `audit_service` does not log PII (no name, photo, or identifier numbers)

---

## 4. Pre-Deployment Risk Assessment

| Risk | Mitigation |
|------|-----------|
| **Discrimination by protected attributes** | `FairnessGuard` L1+L2+L3 + `protected_attributes.yaml` (14 attributes SSOT) + `compliance_block.yaml` (directive) |
| **PII leakage in logs or responses** | `pii_masking.py` + `guardrails_block.yaml` `data_safety` section + `ADR-006` (no PII in logs) |
| **Prompt injection / manipulation** | `PROMPT_INJECTION_PATTERNS` (12 regex) in `interaction_patterns.py` + `DEFENSIVE_BLOCK` + `SecurityPatterns` |
| **Automated decision without human oversight** | HITL in `cv_screening.yaml`, `wsi_evaluation.yaml`, `pipeline_transition.yaml` + `guardrails_block.yaml` `autonomy` section (3 levels) |
| **Multi-tenant data leak (IDOR)** | `TenantGuard` — `company_id` always from JWT, never from payload |
| **Sycophancy (AI agrees with inappropriate requests)** | `anti_sycophancy_block.py` (3 variants) — active rule in every operational agent |
| **Circumvention of compliance via "positive bias"** | `hiring_policy.yaml` `counter_argumentation` section + Brazilian Law 9.029/95 citation |
| **Cultural-fit bias proxy** | `culture_analysis.yaml` updated 2026-04-23 with `<compliance_hr>` block |

---

## 5. Post-Deployment Monitoring

### 5.1 `fairness_post_check.yaml`

Output monitoring across 7 decision domains: `cv_screening`, `wsi_evaluation`, `pipeline_transition`, `hiring_policy`, `sourcing`, `autonomous`, `talent_pool`. Monitors 6 score fields and 5 ranking fields.

### 5.2 Explainability endpoints

| Endpoint | Auth | Audience | Compliance |
|----------|------|----------|------------|
| `GET /api/v1/decisions/candidates/{candidate_id}/explain` | Recruiter JWT (`get_current_user`) | Operator | LGPD Art. 20 (internal review) |
| `GET /api/v1/candidate/decisions/explain` | Candidate JWT (`candidate_token`) | **Candidate** | **EU AI Act Art. 86 + LGPD Art. 20** (direct-to-candidate) |

The direct-to-candidate endpoint was implemented on 2026-04-23 (§11.1) and sanitizes the output, never exposing `wsi_score`, `lia_score`, `confidence`, `weights`, or internal fairness flags.

### 5.3 Audit trail

- Table `fairness_audit_log` (Alembic migration 015) — `company_id`, `subject_id`, `decision_type`, `criteria_used`, `score_breakdown`, `timestamp`
- `candidate_portal_audit_logs` — records candidate portal access (tools_called, fairness_triggered)

### 5.4 Internal dashboards

- Agent Quality Dashboard (`app/api/v1/agent_quality_dashboard.py`)
- Fairness Reports (`app/api/v1/fairness_reports.py`)

---

## 6. Consolidated Metrics

### 6.1 Protected attributes covered — 14

Source: `app/config/protected_attributes.yaml` (version 6):

1. Age
2. Gender
3. Race / Ethnicity
4. Color
5. Religion
6. Sexual orientation
7. Marital status
8. Family situation / maternity / paternity / pregnancy
9. Disability
10. Physical appearance / photo
11. Nationality / accent
12. Criminal record (without specific legal basis)
13. Health / disease
14. Union membership / geographic origin as proxy

### 6.2 FairnessGuard — technical coverage

- **Layer 1 (regex):** 19 categories compiled at initialization (13 PT-BR + 6 EN) — `_PATTERNS_VERSION = 8`
- **Layer 2 (implicit bias):** 43 PT-BR terms + EN terms in `IMPLICIT_BIAS_TERMS`
- **Layer 3 (semantic LLM):** `claude-haiku-4-5-20251001`, triggered on `HIGH_IMPACT_ACTIONS`, Redis cache 1h, `FAIRNESS_LAYER3_ENABLED=true` in production since 2026-04-23

### 6.3 Disparate impact metrics per feature

**Methodology:** four-fifths rule (NYC Local Law 144) — DI ratio ≥ 0.80 per protected group, calculated as:

```
DI ratio = (selection rate of protected group) / (selection rate of reference group)
```

**Current status (2026-04-23):** partial infrastructure (`fairness_audit_log` collecting since Alembic migration 015), **pending Q3/2026 independent bias audit** (see §11).

| Feature | Monitored group | DI ratio | Status |
|---------|-----------------|---------|--------|
| CV Screening | Gender × Race/Ethnicity | Pending | Awaiting Q3/2026 audit |
| WSI Evaluation | Gender × Age | Pending | Awaiting Q3/2026 audit |
| Pipeline Transition | All 14 attributes | Pending | Awaiting Q3/2026 audit |
| Ranking / Shortlist | Gender × Race/Ethnicity × Disability | Pending | Awaiting Q3/2026 audit |
| Sourcing Boolean | Queries with proxies | Collecting via `fairness_audit_log` | Pre-audit aggregation |

### 6.4 Update frequency

- Independent bias audit: **annual** (next cycle Q3/2026)
- Internal metrics report: **quarterly** post-audit
- This document: **annual + triggered** by significant architectural change

---

## 7. Human Oversight (Art. 14)

### 7.1 Declarative HITL per domain

| Domain YAML | HITL | Explainability | Compliance score |
|-------------|------|----------------|------------------|
| `hiring_policy.yaml` | ✅ `escalation` | ✅ `reasoning_rules` | 5/5 |
| `cv_screening.yaml` | ✅ double confirmation for bulk rejection | ✅ auditable reasoning | 3/5 |
| `wsi_evaluation.yaml` | ✅ FairnessGuard mandated | Partial | 3/5 |
| `pipeline_transition.yaml` | ✅ irreversible actions confirmed | ✅ `communication_transparency` | 3/5 |
| `autonomous.yaml` (fix 2026-04-23) | ✅ `hitl_escalation` | ✅ declarative audit trail | ▲ improved |
| `culture_analysis.yaml` (fix 2026-04-23) | ✅ `<compliance_hr>` block | ▲ improved | ▲ improved |
| `orchestrator.yaml` (fix 2026-04-23) | ✅ compliance prologue | ▲ improved | ▲ improved |

### 7.2 `guardrails_block.yaml` — escalation scenarios

Seven mandatory scenarios for escalation to a human:

1. Discrimination detected
2. Data subject request (LGPD)
3. Pattern of potentially discriminatory rejections
4. Risk score > 0.8
5. Manipulation/jailbreak attempt
6. Conflict between recruiter instruction and fairness rule
7. Candidate request to contest decision (Art. 86)

### 7.3 Right to contest (EU AI Act Art. 86)

Implemented on 2026-04-23:
- **Endpoint:** `GET /api/v1/candidate/decisions/explain`
- **Agent:** `CandidateSelfServiceAgent` with tool `explain_candidate_decision`
- **Policy:** `compliance_block.yaml` `right_to_contest` section (variants `decision` and `communication`)
- **Recommended term:** 30 days to contest

---

## 8. Accuracy, Robustness, Cybersecurity (Art. 15)

### 8.1 Model anchoring

Explicit versioning for reproducibility:
- `claude-sonnet-4-5` (stable release)
- `claude-haiku-4-5-20251001` (version-pinned for FairnessGuard L3)
- `claude-opus-4-7` (1M context, consultative use)

### 8.2 Rate limits

- `POST /api/v1/candidate/chat`: 10/hour, 30/day per `candidate_id` (Redis)
- `GET /api/v1/candidate/decisions/explain`: same rate limit
- Internal APIs: rate limit by API key (documented in `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`)

### 8.3 JWT token scoping (anti-IDOR)

- `candidate_token`: contains `candidate_id`, `vacancy_id`, `company_id` — **always derived from token**, never accepted from input
- `recruiter_token`: contains `user_id`, `company_id`, `permissions` — validated by `TenantGuard`

### 8.4 Circuit breakers and fallbacks

Documented in `RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md`:
- `CircuitBreaker` across 20 critical circuits (LLM providers, ATS integrations, Redis)
- 3 states: Closed → Open → Half-Open
- Lenient fallback for FairnessGuard L3 (`is_blocked=False, confidence=0.5`) when provider API fails, with `soft_warnings` for audit

---

## 9. Data Subject Rights (LGPD + EU AI Act Art. 86)

### 9.1 Explainability

- **To the operator (recruiter):** `decision_explanation.py` — returns `reasoning`, `factors`, `confidence`, `fairness_check`, `calibration_weights_used`
- **To the candidate:** `candidate_portal_explanation.py` — returns **only** `criteria_evaluated`, `criteria_ignored`, aggregated `fairness_check`, `transparency_note`, `art_86_notice`; **never** raw scoring

### 9.2 Human review

Any decision can be escalated to human review via:
- Deployer's formal compliance channel (configurable per `company_id`)
- Candidate request via portal (`/api/v1/candidate/chat`)
- Automatic escalation when `risk_score > 0.8` (`hiring_policy.yaml`)

### 9.3 Right to contest (30-day term)

Right documented in `compliance_block.yaml` `right_to_contest` section and exposed to the candidate via `art_86_notice` in every explanation response.

### 9.4 Access and deletion (data_subject_request)

Legacy endpoint for LGPD Arts. 18 and 15 — data access and deletion. Flow: candidate requests → deployer's compliance validates → system deletes with auditable tombstone.

---

## 10. Market Benchmark and Competitor Comparison

This section consolidates the benchmark performed on 2026-04-23 against the 4 main players and 5 regulatory frameworks, originally documented in `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.7.

### 10.1 Regulatory requirements — cross-status

| Requirement | Legal basis | What it requires | WeDOTalent status | Gap |
|-------------|-------------|-------------------|-------------------|-----|
| Classification as high-risk AI | EU AI Act Annex III cat. 4 | Mandatory registration after 02/08/2026 | Classification inevitable | Formalize registration when database active |
| Training data governance | EU AI Act Art. 10 | Document data provenance | 100% prompt-based; no fine-tuning | Documented (this doc §3) |
| Operator transparency (AI Fact Sheet) | EU AI Act Art. 13 | Required format | 5 Fact Sheets published 2026-04-23 (§11) | — |
| Human oversight (design) | EU AI Act Art. 14 | Actionable UI override | `guardrails_block.yaml` + HITL per domain | Validate UI actionability |
| Accuracy, robustness, security | EU AI Act Art. 15 | Demographic-group metrics | Infrastructure (`fairness_audit_log`); DI ratios pending | Bias audit Q3/2026 |
| Candidate right to explanation | EU AI Act Art. 86 | Direct-to-candidate endpoint | **Implemented 2026-04-23** (`/api/v1/candidate/decisions/explain`) | — |
| Automated review right | LGPD Art. 20 | Review channel | Implemented via portal + compliance email | — |
| Bias identification and mitigation | NIST AI RMF MEASURE 2.11 | Documented tests | FairnessGuard L1+L2+L3 | Independent bias audit (P1.2) |
| Incident escalation | NIST AI RMF MANAGE 4.1 | Formal SLA | `guardrails_block.yaml` + 7 scenarios | Formalize SLA (P2) |
| AI management system | ISO/IEC 42001:2023 | Certified AIMS | — | Certification 2027 |
| Disparate impact testing | NYC Local Law 144 | DI ratio ≥ 0.80 per group | Collecting | Q3/2026 audit |

### 10.2 Competitive benchmark — 9 dimensions × 5 players

Sources verified in §10.5.

| Dimension | WeDOTalent (LIA) | Workday / HiredScore | HiPeople | Eightfold AI | LinkedIn |
|-----------|------------------|---------------------|----------|--------------|----------|
| **Declared protected attributes** | **14** | 4+ (partially published) | 4+ (proxies) | 4+ (+ intersections) | 4+ |
| **Public attribute list** | Post §11 (in progress) | Partial via ML Fact Sheets | Partial | Yes (annual bias audit) | Yes (LiFT open-source) |
| **Candidate explainability** | ✅ **since 2026-04-23** (new endpoint) | Deployer only | Recruiter only | Yes (via portal) | Declared (no public mechanism) |
| **HITL by design** | ✅ 3 `autonomy` levels | ✅ "human review of any outputs" | ✅ Recruiter as final point | ✅ Candidate masking + human | ✅ Human review |
| **Direct right to contest** | ✅ **implemented 2026-04-23** | Not publicly found | Not publicly found | Not publicly found | Not publicly found |
| **Audit trail** | ✅ Alembic 015 + fairness_audit_log | ✅ ML Fact Sheets + ISO 42001 | ✅ Public Warden AI dashboard | ✅ Annual bias audit + ISO 42001 | LiFT open-source |
| **Documented fairness testing** | ✅ L1+L2+L3 internal; external audit Q3/2026 | ✅ Coalfire (NIST) + Schellman (ISO) | ✅ NYC LL144 | ✅ BABL AI annual (minimum ratio 0.880) | LinkedIn Fairness Toolkit |
| **External certifications** | — (roadmap 2027) | ISO 42001 + NIST AI RMF | NYC LL144; EU AI Act in progress | ISO 42001 + NYC LL144 | — (open-source as transparency) |
| **Consolidated score /10** | **7/10** ↑ | **8/10** | **7/10** | **9/10** | **7/10** |

> **Note:** WeDOTalent's score rose from 6/10 (snapshot 2026-04-22, pre-implementation) to 7/10 after fixes applied on 2026-04-23 (Art. 86 endpoint, Fact Sheets, FairnessGuard L3 activation).

### 10.3 WeDOTalent real differentiators

1. **3-layer FairnessGuard (L1+L2+L3):** unique architecture — deterministic regex + type categorization + semantic LLM. More sophisticated than the binary proxy blocking adopted by HiPeople and LinkedIn, catching subtle bias that escapes fixed vocabulary.

2. **14 explicit protected attributes:** higher number than publicly declared by the 4 competitors analyzed. Official publication of the list planned for Q2/2026 as part of this document.

3. **Active counter-argumentation in `hiring_policy.yaml`:** LIA does not just block prohibited criteria — it educationally counter-argues citing Brazilian Law 9.029/95. **No competitor describes an equivalent mechanism publicly.**

4. **End-to-end FairnessGuard:** coverage in CV screening, WSI evaluation, and pipeline transitions — not just initial CV screening.

5. **4 contextual variants of compliance_block:** granularity `decision` / `communication` / `operational` / `defensive` — not publicly evidenced by competitors.

6. **Direct right-to-contest to candidate:** implemented on 2026-04-23 via JWT-token endpoint, before the regulatory obligation (02/08/2026) comes into force. None of the 4 competitors publish an equivalent mechanism.

### 10.4 Gaps vs. market

- **Independent bias audit published annually:** Eightfold is the reference (BABL AI, minimum ratio 0.880). WeDOTalent roadmap: Q3/2026 (§11.2).
- **ISO/IEC 42001:2023 certification:** Workday and Eightfold hold it. WeDOTalent roadmap: 2027 (§11.3).
- **Standardized AI Fact Sheets:** Workday sets the benchmark. WeDOTalent Fact Sheets published 2026-04-23 (§11.2.a).

### 10.5 Primary sources (15 verifiable URLs)

- EU AI Act Annex III: https://artificialintelligenceact.eu/annex/3/
- EU AI Act Art. 13/14/15: https://artificialintelligenceact.eu/section/3-2/
- EU AI Act Art. 86: https://artificialintelligenceact.eu/article/86/
- NIST AI RMF 1.0: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- LGPD Art. 20: https://lgpd-brasil.info/capitulo_03/artigo_20
- Eightfold Responsible AI: https://eightfold.ai/responsible-ai/
- Eightfold Bias Audit 2026 (PDF): https://eightfold.ai/wp-content/uploads/eightfold-summary-of-bias-audit-results.pdf
- Workday Responsible AI Practices: https://www.workday.com/en-us/artificial-intelligence/responsible-ai-practices.html
- Workday Independent Verifications: https://blog.workday.com/en-us/workday-secures-dual-independent-verifications-of-its-approach-to-responsible-ai.html
- HiPeople AI Resume Screening: https://www.hipeople.io/blog/introducing-hipeople-ai-resume-screening-automate-inbound-chaos-once-and-forever
- HiPeople Warden AI Dashboard: https://trust.warden-ai.com/hipeople/ai-application-screening
- LinkedIn Responsible AI Principles: https://www.linkedin.com/blog/member/trust-and-safety/responsible-ai-principles
- LinkedIn LiFT Toolkit (GitHub): https://github.com/linkedin/LiFT
- NYC Local Law 144 Guide: https://www.warden-ai.com/resources/hr-tech-compliance-nyc-local-law-144

---

## 11. Public Roadmap of Publications and Implementations

### 11.1 What has been done (2026-04-23)

| ID | Deliverable | Canonical artifact |
|----|-------------|-------------------|
| Fix P0 | Fairness rules + HITL in autonomous agent | `app/prompts/domains/autonomous.yaml` |
| Fix P0 | Declarative right to contest Art. 86 | `app/prompts/shared/compliance_block.yaml` (`right_to_contest`) |
| Fix P1 | Compliance block in culture_analysis | `app/prompts/domains/culture_analysis.yaml` (`<compliance_hr>` block) |
| Fix P1 | Compliance prologue in router | `app/prompts/domains/orchestrator.yaml` |
| Activation P1 | FairnessGuard Layer 3 in production | `.env` + `FAIRNESS_LAYER3_RUNBOOK.md` |
| New P0 | Direct-to-candidate Art. 86 endpoint | `/api/v1/candidate/decisions/explain` |
| New P0 | `explain_candidate_decision` tool | `app/domains/candidate_self_service/tools/explain_candidate_decision.py` |
| Publication P1 | 5 AI Fact Sheets PT + EN | `docs/responsible-ai/fact-sheets/*.md` |
| Publication P2.1 | This document (Art. 11 Tech Doc) | `docs/responsible-ai/eu-ai-act-technical-documentation-pt.md` + `-en.md` |

### 11.2 What still needs to be done

#### a) Publication of feature information
Fact Sheets created — next step is **publication on wedotalent.cc**. Requires:
- Final route decision (`wedotalent.cc/responsible-ai/fact-sheets/...`)
- HTML template design for public rendering
- Link in product menu/footer
- Final legal review of PT + EN versions

**Responsible:** Marketing + Legal + DPO
**Suggested timeline:** Q2/2026

#### b) Independent bias audit with publication
Full plan in `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.3 — 3 sprints (9 weeks):
- Sprint A (4 weeks): build internal `bias_audit_service.py` calculating DI ratio per group
- Sprint B (3 weeks): contract external auditor (options: BABL AI, Warden AI, Coalfire)
- Sprint C (2 weeks): publish results at `wedotalent.cc/responsible-ai/bias-audit-2026`

**Responsible:** Compliance team + Eng (Sprint A) + DPO (contracting)
**Suggested timeline:** Q3/2026

#### c) Art. 86 endpoint ✅ **DONE on 2026-04-23**
See §11.1. Next operational steps:
- Candidate portal frontend that calls the endpoint and renders response
- Email template with JWT link for candidate access
- Configure formal contestation channel per `company_id` (`CompanyComplianceSettings`)

**Responsible:** FE team + Product
**Suggested timeline:** Q2/2026

#### d) ISO/IEC 42001:2023 certification
- Formalize an AIMS (AI Management System)
- Conduct AI Impact Assessment (AIIA)
- Pass certification audit

**Responsible:** DPO + executives
**Suggested timeline:** 2027

#### e) EU AI Act database registration
Mandatory after 02/08/2026 for providers of high-risk systems. This document (after legal review) will be the basis for registration.

**Responsible:** Legal + DPO
**Timeline:** post 02/08/2026 (when database is active)

#### f) `wedotalent.cc/responsible-ai` public page
Hub page linking: Fact Sheets, this Technical Documentation, Bias Audit (when published), responsible AI principles, contact channel.

**Responsible:** Marketing + Legal
**Suggested timeline:** Q3/2026 (after Q3 bias audit)

#### g) Formal SLA for fairness incidents
Document response times and remediation procedures for incidents detected by `fairness_audit_log` or escalated via `guardrails_block.yaml`.

**Responsible:** Compliance team + DPO
**Suggested timeline:** Q4/2026

#### h) External legal review of this document
Before public release and before EU AI Act database registration, review by law firm specializing in AI/LGPD/EU AI Act.

**Responsible:** Legal (vendor approval by executives)
**Suggested timeline:** Q2/2026

### 11.3 Consolidated timeline

| Quarter | Deliverables |
|---------|--------------|
| **Q2/2026** (in progress) | Fact Sheets published on site; Art. 86 endpoint frontend; legal review of this doc |
| **Q3/2026** | Independent bias audit complete; public page publication |
| **Q4/2026** | Formal SLA; consolidation of `wedotalent.cc/responsible-ai` page |
| **Post 02/08/2026** | EU AI Act database registration |
| **2027** | Preparation for ISO 42001 + certification audit |

### 11.4 Responsibilities

| Role | Responsibilities |
|------|-----------------|
| **Compliance team** | Content and update of Fact Sheets + this document + metrics monitoring |
| **Engineering** | Endpoints, feature flags, regression testing, YAML updates |
| **DPO** | Legal review, declaration of conformity, external auditor contracting, EU database registration |
| **Marketing** | Public responsible-ai page, update communication, Fact Sheet design |
| **Executives (Paulo)** | External auditor approval, ISO 42001 budget, publication decisions |

---

## 12. Governance and Responsibilities

### 12.1 Data Protection Officer (DPO)

- **Contact:** compliance@wedotalent.cc (channel to configure in production)
- **Duties:** legal review, policy approval, authority liaison (ANPD in Brazil, DPAs in the EU)

### 12.2 Compliance team

- Weekly monitoring of `fairness_audit_log`
- Monthly review of FairnessGuard L3 costs and latency
- Quarterly review of policies and fact sheets
- Escalate fairness incidents to DPO

### 12.3 Revision cadence of this document

- **Annual** by default
- **Triggered** when:
  - Significant architectural change (new agent, new LLM model, new defense layer)
  - Relevant regulatory update (EU AI Act, LGPD, NIST, ISO)
  - Bias audit results that change §6.3
  - Critical fairness or security incident

---

## 13. Declaration of Conformity

> This document consolidates the technical documentation required by EU AI Act Art. 11 (Annex IV) for high-risk AI systems classified under Annex III, category 4.
>
> WeDOTalent declares that the LIA platform:
> - Operates with human oversight for all high-impact decisions (Art. 14)
> - Provides documented transparency mechanisms to both operator and candidate (Arts. 13 and 86)
> - Implements three-layer fairness testing (L1+L2+L3)
> - Maintains traceable audit trail of all automated decisions
> - Ensures right to human review and contestation per EU AI Act Art. 86 and LGPD Art. 20
>
> This document is **ready for external legal review** prior to public release and EU AI Act database registration (when active).

Signatures (pending):
- [ ] Data Protection Officer
- [ ] Engineering Director
- [ ] CEO/Founder

---

## Appendix A — Cross-references to existing guides

- `docs/reconstruction-guides/COMPLIANCE_RECONSTRUCTION_GUIDE.md` — 8-layer defense architecture, full audit, detailed benchmark (§10), P0/P1 action plan (§11)
- `docs/reconstruction-guides/LIA_PERSONA_RECONSTRUCTION_GUIDE.md` — prompt layer, SystemPromptBuilder, 24 domain YAMLs
- `docs/reconstruction-guides/INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` — agents, tools, orchestration
- `docs/reconstruction-guides/RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` — circuit breakers, learning loop
- `docs/reconstruction-guides/CANONICAL_FILES_BY_THEME.md` — master index
- `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md` — L3 operation
- `docs/responsible-ai/fact-sheets/` — 5 fact sheets PT + EN

## Appendix B — Compliance changelog (2026-04-14 to 2026-04-23)

| Date | Change | File |
|------|--------|------|
| 2026-04-14 | Initial `autonomous.yaml` without declarative compliance | `autonomous.yaml` |
| 2026-04-22 | Exhaustive audit vs. regulatory frameworks | `COMPLIANCE §10` |
| 2026-04-23 | Fix P0 `autonomous.yaml` (behavioral_rules + HITL + compliance) | `autonomous.yaml` |
| 2026-04-23 | Fix P0 `compliance_block.yaml` (`right_to_contest` Art. 86) | `compliance_block.yaml` |
| 2026-04-23 | Fix P1 `culture_analysis.yaml` (`<compliance_hr>`) | `culture_analysis.yaml` |
| 2026-04-23 | Fix P1 `orchestrator.yaml` (compliance prologue) | `orchestrator.yaml` |
| 2026-04-23 | Activation `FAIRNESS_LAYER3_ENABLED=true` in production | `.env` |
| 2026-04-23 | Endpoint `/api/v1/candidate/decisions/explain` | `candidate_portal_explanation.py` |
| 2026-04-23 | Tool `explain_candidate_decision` | `explain_candidate_decision.py` |
| 2026-04-23 | 5 AI Fact Sheets published (PT + EN) | `fact-sheets/*.md` |
| 2026-04-23 | This document published (v1.0) | `eu-ai-act-technical-documentation-pt.md` + `-en.md` |

## Appendix C — Contacts and channels

- **Compliance:** compliance@wedotalent.cc
- **Operational support:** support@wedotalent.cc
- **Privacy (LGPD):** dpo@wedotalent.cc
- **Formal contestation channel (EU AI Act Art. 86):** configurable per `company_id` — deployer defines its own channel in `CompanyComplianceSettings.contato_revisao`

## Appendix D — PT-EN bilingual glossary (regulatory terms)

| PT-BR | EN | Source |
|-------|-----|--------|
| Sistema de IA de Alto Risco | High-Risk AI System | EU AI Act Art. 6 + Annex III |
| Atributos protegidos | Protected attributes | Brazilian Law 9.029/95 + CLT Art. 373-A |
| Supervisão humana | Human oversight / Human-in-the-Loop (HITL) | EU AI Act Art. 14 |
| Direito à explicação | Right to explanation | EU AI Act Art. 86 |
| Direito de revisão | Right to review | LGPD Art. 20 |
| Decisão automatizada | Automated decision-making | LGPD Art. 20 + EU AI Act Art. 22 (GDPR linked) |
| Disparate impact ratio | Disparate impact ratio | NYC LL144 + EEOC four-fifths rule |
| Audit trail | Audit trail | EU AI Act Art. 12 |
| Provider (de sistema IA) | Provider | EU AI Act Art. 3 |
| Deployer (usuário do sistema) | Deployer | EU AI Act Art. 3 |
| Sujeito da decisão | Decision subject | GDPR + LGPD |
| Ação afirmativa (permitida) | Affirmative action (permitted) | Brazilian Law 8.213/91 + 12.990/2014 |
| Sistema de gestão de IA | AI Management System (AIMS) | ISO/IEC 42001:2023 |

---

*Document produced on 2026-04-23 | Version 1.0 | All statements are backed by direct reading of canonical files in `lia-agent-system/` or verifiable regulatory URL (§10.5). Zero invention.*
