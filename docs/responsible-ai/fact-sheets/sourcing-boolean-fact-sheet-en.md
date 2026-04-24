# AI Fact Sheet — Sourcing and Boolean Search

*Last updated: 2026-04-23 | Language: EN | [Versão em português](./sourcing-boolean-fact-sheet-pt.md)*

## 1. Purpose

Sourcing is responsible for actively searching for candidates — first in the internal database (PostgreSQL), then in external sources (Pearch AI with 190M+ profiles) — generating optimized boolean strings and ranking by relevance to the job. It also conducts initial outreach via WhatsApp/LinkedIn when configured. Goal: **expand the candidate pool impartially**.

## 2. Inputs

- Job requirements (mandatory skills, minimum experience, location, work model)
- Recruiter's search strings (free-form or structured)
- Desired source (local database / Pearch AI / both)
- Additional filters (seniority, languages, availability)

## 3. Outputs

- Optimized boolean string (e.g., `"React" AND "Senior" AND ("TypeScript" OR "Next.js") NOT "Mid"`)
- List of found candidates (ordered by relevance)
- Initial longlist (typically 20-50 candidates)
- Personalized outreach messages (if enabled)
- Result diagnosis (healthy pool? needs broader criteria?)

## 4. Model and Architecture

- **Base LLM model:** `claude-sonnet-4-5` (Anthropic) for boolean string generation and semantic ranking
- **Canonical domain YAML:** `app/prompts/domains/sourcing.yaml` (96 lines, version `2.0`, `updated_at: 2026-03-19`)
- **Agent:** `SourcingAgent` (in `app/domains/sourcing/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="sourcing")`
- **External integration:** Pearch AI API (external database with 190M+ profiles)

## 5. Protected Attributes — Coverage

- 14 protected attributes via `protected_attributes.yaml` and FairnessGuard L1+L2+L3
- **Boolean string is validated before execution** — if it contains discriminatory proxy (e.g., "neighborhood X" as class proxy, "typical name of" as racial proxy), FairnessGuard L1 blocks
- Canonical rule in `sourcing.yaml`: searches are by competency and objective requirement, not demographics
- **`orchestrator.yaml`** (updated 2026-04-23) has explicit rule: *"If input contains protected attributes as filter criteria, classify as intent='compliance_violation'"*

## 6. Accuracy and Fairness Metrics

→ See section 6 of `eu-ai-act-technical-documentation-en.md` — consolidated metrics. Sourcing monitors **queries with proxies** via `fairness_audit_log` — systemic patterns detected are automatically escalated. Next independent bias audit: Q3/2026.

## 7. Known Limitations

- **Database dependence:** candidates must already have consented with LGPD in the local database or be in external sources with appropriate legal basis (Pearch AI is compliant).
- **Complex boolean string:** strings with >10 boolean operators may degrade search performance and be rejected by external provider.
- **Language:** active search works best in PT-BR and EN; less common languages may have reduced coverage.
- **Outreach:** messages are personalized templates, but **do not simulate conversation** with candidate — recruiter must validate each outreach before sending.

## 8. Human Oversight (HITL)

- **Mandatory:** recruiter approves boolean string before external source execution (cost + LGPD)
- **Mandatory:** mass outreach requires explicit confirmation
- **Mandatory:** if FairnessGuard blocks query, recruiter receives educational alert citing applicable law (Brazilian Law 9.029/95, LGPD Art. 20)
- **Optional:** recruiter can review and reorder longlist before passing to CV Screening
- **Minimal automation:** if `AUTONOMIA_LIA` configured as high, feature can activate recurring searches — but always with audit trail

## 9. Candidate Rights

- **Candidate found via active sourcing:** is contacted via outreach with explicit LGPD consent (opt-in) before processing further data.
- **Right to decline:** if candidate declines outreach, is marked as "do-not-contact" in `contact_preferences` — respected in future searches.
- **Explainability:** if candidate asks explanation for why they were contacted, recruiter accesses `audit_service` which records the query + technical criteria used. Endpoint `/api/v1/candidate/decisions/explain` returns this detail in simple language.
- **Deletion:** candidate can request removal from local database via `data_subject_request` (LGPD Art. 18).

## 10. Contacts

- **Compliance:** compliance@wedotalent.cc
- **Support:** support@wedotalent.cc
- **Privacy (DPO):** dpo@wedotalent.cc

---

*Canonical source: `app/prompts/domains/sourcing.yaml` + `app/domains/sourcing/tools/` + `orchestrator.yaml` (updated 2026-04-23) + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invention.*
