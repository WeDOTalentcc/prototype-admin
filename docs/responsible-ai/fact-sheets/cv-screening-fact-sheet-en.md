# AI Fact Sheet — CV Screening

*Last updated: 2026-04-23 | Language: EN | [Versão em português](./cv-screening-fact-sheet-pt.md)*

## 1. Purpose

CV Screening analyzes candidate resumes against a job's objective requirements, generating an initial WSI score (70% technical + 30% behavioral) and ranking candidates for shortlisting. The goal is to reduce the recruiter's upfront effort in high-volume scenarios, **without replacing** final human evaluation.

This feature **does not make autonomous rejection or hiring decisions** — every final pipeline decision belongs to the human recruiter.

## 2. Inputs

- Resume text (pasted or extracted from PDF/DOCX by the system)
- Job requirements (`job_vacancy`): mandatory skills, minimum experience, education
- Company settings (`company_settings`): exclusion criteria, LIA autonomy level

## 3. Outputs

- Initial WSI score (`wsi_score_initial`, 0-100) — internal, NEVER exposed to the candidate
- Score breakdown: technical match (%), behavioral score (%)
- Evidence list (criteria met / not met)
- Detected red flags (gaps, date inconsistencies) — internal
- Screening recommendation: `shortlist` / `human review` / `not aligned`
- Auditable reasoning in `audit_service.log_decision`

## 4. Model and Architecture

- **Base LLM model:** `claude-sonnet-4-5` (Anthropic)
- **Canonical domain YAML:** `app/prompts/domains/cv_screening.yaml` (222 lines, version `2.0`, `updated_at: 2026-03-19`)
- **Agent:** `CVScreeningAgent` (in `app/domains/cv_screening/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="cv_screening")`
- **Scoring methodology:** Dynamic Cutoff (threshold recalculated after 30-50 candidates) + Smart Saturation (pipeline pauses if >20 approved)

## 5. Protected Attributes — Coverage

- 14 protected attributes listed in `app/config/protected_attributes.yaml` (version 6)
- **FairnessGuard Layer 1 (regex, 19 categories):** deterministic blocking before the LLM is invoked
- **FairnessGuard Layer 2 (43 PT/EN terms):** implicit bias detection
- **FairnessGuard Layer 3 (semantic LLM, active since 2026-04-23):** semantic classification for high-impact actions
- Canonical rule in `cv_screening.yaml`: *"Never reject a candidate without first checking FairnessGuard"* and *"Completely ignore: name, photo, address, marital status, age, ethnic origin"*

## 6. Accuracy and Fairness Metrics

→ See section 6 of `eu-ai-act-technical-documentation-en.md` — consolidated metrics per feature, with disparate impact ratio status (DI ratio ≥ 0.80 per NYC LL144 four-fifths rule). Next independent bias audit: Q3/2026.

## 7. Known Limitations

- **Dependence on CV text quality:** poorly formatted CVs, scanned documents without clean OCR, or unsupported languages reduce accuracy.
- **Base LLM training bias:** mitigated by FairnessGuard + `compliance_block.yaml`, but not fully eliminable — hence the feature is **assistive, not decisional**.
- **Dynamic Cutoff:** in small volumes (<30 candidates), the threshold may not be calibrated — human review recommended.
- **No portfolio evaluation:** links to GitHub, portfolio, or LinkedIn are not automatically accessed in this layer.

## 8. Human Oversight (HITL)

- **Mandatory:** double confirmation for bulk rejection (>1 candidate simultaneously)
- **Mandatory:** scores in the 60-74% zone → explicitly recommends human review
- **Mandatory:** every rejection passes through `check_rejection_fairness` before being registered
- **Mandatory:** auditable reasoning in `audit_service` for every decision
- **Optional:** recruiter can override any score/recommendation

## 9. Candidate Rights

- **Explainability:** endpoint `/api/v1/candidate/decisions/explain` (candidate JWT) returns objective criteria evaluated + list of IGNORED protected attributes + EU AI Act Art. 86 + LGPD Art. 20 notice.
- **Human review:** candidate can request review through the deployer client's formal compliance channel (configured in `CompanyComplianceSettings.contato_revisao`).
- **Contestation:** recommended 30-day term from decision notification (EU AI Act Art. 86 + LGPD Art. 20).
- **Data access/deletion:** via `data_subject_request` (LGPD Arts. 18 and 15).

## 10. Contacts

- **Compliance:** compliance@wedotalent.cc
- **Support:** support@wedotalent.cc
- **Privacy (DPO):** dpo@wedotalent.cc

---

*Canonical source: `app/prompts/domains/cv_screening.yaml` + `app/domains/cv_screening/` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invention.*
