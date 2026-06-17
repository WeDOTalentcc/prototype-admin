# AI Fact Sheet — Pipeline Transition

*Last updated: 2026-04-23 | Language: EN | [Versão em português](./pipeline-transition-fact-sheet-pt.md)*

## 1. Purpose

Pipeline Transition helps the recruiter move candidates between pipeline stages (sourced → screening → interview → offer), extracting preferences from conversation, consulting relevant data, and suggesting appropriate sub-status. Covers individual and batch movements, with **mandatory fairness validation on rejections**.

This feature **does not execute autonomous transitions without recruiter confirmation** — every candidate-affecting action is explicitly confirmed.

## 2. Inputs

- Recruiter message (intent to move candidate)
- Mentioned candidate(s) — IDs or names
- Current stage + destination stage
- Transition reason (especially for rejections)
- Prior conversation context (memory + current entity)

## 3. Outputs

- Confirmation of action to be executed (stage + sub-status)
- Preferences extraction (date, time, format, channel, urgency)
- Sub-status suggestion via `suggest_sub_status`
- Automatic communication notice (if action triggers candidate message)
- `check_rejection_fairness` result (mandatory on rejections)
- Full audit trail via `audit_service.log_decision`

## 4. Model and Architecture

- **Base LLM model:** `claude-sonnet-4-5` (Anthropic)
- **Canonical domain YAML:** `app/prompts/domains/pipeline_transition.yaml` (98 lines, version `3.0.0`, `updated_at: 2026-04-14`)
- **Agent:** `PipelineTransitionAgent` — uses custom `get_pipeline_system_prompt()` (outside standard `SystemPromptBuilder`)
- **Calibration by company size:** STARTUP / PME / CORPORATE tone adjusts formality (YAML field `company_calibration`)
- **Learning rules:** `get_recruiter_preferences` queries recruiter's patterns and offers proactive suggestions

## 5. Protected Attributes — Coverage

- 14 protected attributes via `protected_attributes.yaml` and FairnessGuard L1+L2+L3
- Canonical rule in `pipeline_transition.yaml` (rule 5 of `behavioral_rules`): *"For rejections: ALWAYS use check_rejection_fairness BEFORE responding"*
- Rule 8 of `behavioral_rules`: *"Use tools proactively when needed"* — includes fairness checking before irreversible actions

## 6. Accuracy and Fairness Metrics

→ See section 6 of `eu-ai-act-technical-documentation-en.md` — consolidated metrics. Pipeline Transition monitors all 14 attributes on transitions with destination `conclusion_rejected` or `shortlist`. DI ratio target ≥ 0.80. Next independent bias audit: Q3/2026.

## 7. Known Limitations

- **Name ambiguity:** if multiple candidates share a first name, feature asks for explicit disambiguation (never assumes).
- **Batch transitions:** maximum 20 candidates simultaneously (avoids cascading failures); above that, recruiter must split.
- **Rejection without reason:** feature blocks rejection lacking a structured reason (prevents hidden bias).
- **Automatic communication:** only triggered if configured in `company_settings`; if disabled, recruiter must communicate manually.

## 8. Human Oversight (HITL)

- **Mandatory:** explicit confirmation on every irreversible action (rejection, final movement, offer)
- **Mandatory:** `check_rejection_fairness` before any-scale rejection
- **Mandatory:** `communication_transparency` — if transition triggers automatic message, recruiter is informed what candidate will receive and can edit
- **Mandatory:** double confirmation for batch transitions
- **Automatic escalation:** if FairnessGuard detects systemic pattern of rejection by protected attribute, alert is emitted for compliance team

## 9. Candidate Rights

- **Automatic communication notification:** when system sends candidate message (e.g., rejection with feedback), communication includes LGPD Art. 20 + EU AI Act Art. 86 notice.
- **Explainability:** endpoint `/api/v1/candidate/decisions/explain` returns transition reason in simple language, objective criteria, and Art. 86 notice.
- **Human review:** candidate can request review through deployer client's formal channel.
- **Contestation:** 30 days from notification.

## 10. Contacts

- **Compliance:** compliance@wedotalent.cc
- **Support:** support@wedotalent.cc
- **Privacy (DPO):** dpo@wedotalent.cc

---

*Canonical source: `app/prompts/domains/pipeline_transition.yaml` + `app/domains/pipeline_transition/` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invention.*
