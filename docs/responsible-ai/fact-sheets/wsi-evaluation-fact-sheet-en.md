# AI Fact Sheet — WSI Evaluation

*Last updated: 2026-04-23 | Language: EN | [Versão em português](./wsi-evaluation-fact-sheet-pt.md)*

## 1. Purpose

WSI (Workplace Science Index) Evaluation applies scientific methodologies — Bloom Taxonomy, Dreyfus Model, and Big Five — to structured interview transcripts to produce technical-behavioral opinions, side-by-side candidate comparisons, and expertise levels per competency. Used after the interview (initial screening + WSI interview via WhatsApp) to support the human recruiter's final hiring decision.

This feature **does not make autonomous hiring decisions** — every final decision belongs to the human recruiter.

## 2. Inputs

- Complete WSI interview transcript
- WSI questions (framework defined per job + archetype)
- Job context (requirements + seniority level)
- Historical decisions by the same recruiter (optional, for calibration)

## 3. Outputs

- Final WSI score (`wsi_final_score`, 0-100) — internal, NEVER exposed to the candidate
- Bloom levels (1-6) per evaluated competency
- Dreyfus levels (1-5) per evaluated competency
- Big Five traits (O/C/E/A/N) with scores
- Structured opinion in natural language (4-6 paragraphs)
- Side-by-side comparison when multiple candidates evaluated
- Full reasoning in `audit_service.log_decision`

## 4. Model and Architecture

- **Base LLM model (scoring):** `claude-sonnet-4-5` (Anthropic)
- **Linguistic extraction model (Layer 2 — `wsi_layer2_extraction`):** `claude-haiku-4-5-20251001` (Anthropic) — extracts objective signals (paraphrase, first-person, quantification, semantic inflation) feeding the deterministic Layer 1
- **Canonical domain YAML:** `app/prompts/domains/wsi_evaluation.yaml` (82 lines, version `2.0`, `updated_at: 2026-04-07`) + `wsi_layer2_extraction.yaml` (140 lines)
- **Agent:** `WSIEvaluatorAgent` (in `app/domains/wsi_evaluation/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="wsi_evaluator")`

## 5. Protected Attributes — Coverage

- Same coverage of 14 protected attributes via `protected_attributes.yaml` and FairnessGuard L1+L2+L3
- **Layer 2 extraction** has an explicit `scope_out` rule in `wsi_layer2_extraction.yaml`: *"DOES NOT use name, age, gender, race, photo, origin (protected attributes)"*
- **Semantic inflation detection:** grandiose claims without evidence are flagged, not rewarded
- **Prompt injection detection:** candidate responses attempting to manipulate evaluation are detected and flagged

## 6. Accuracy and Fairness Metrics

→ See section 6 of `eu-ai-act-technical-documentation-en.md` — consolidated metrics per feature. WSI Evaluation is one of the monitored features (group: Gender × Age). DI ratio target ≥ 0.80. Next independent bias audit: Q3/2026.

## 7. Known Limitations

- **Transcript quality dependence:** audio noise, automatic transcription errors reduce accuracy.
- **Dreyfus level is an estimate:** expertise classification (Novice → Expert) is approximate — human specialists may disagree in borderline cases.
- **Big Five requires minimum interview length:** very short responses (<30 words) limit behavioral trait detection.
- **Per-company calibration:** scoring can be adjusted by tenant's `CalibrationWeight` — without calibration, uses default weights (70% technical / 30% behavioral).

## 8. Human Oversight (HITL)

- **Mandatory:** `FairnessGuard.check()` before every final scoring
- **Mandatory:** auditable reasoning with `criteria_used`, `score_breakdown`, `subject_id`, `timestamp`
- **Mandatory:** hiring decision is **exclusively** human — LIA produces an opinion, never a verdict
- **Optional:** recruiter can adjust weights per job (via `CalibrationWeight`)
- **Optional:** recruiter can override final score

## 9. Candidate Rights

- **Explainability:** endpoint `/api/v1/candidate/decisions/explain` returns objective criteria (demonstrated Bloom levels, evaluated technical competencies) + transparency about ignored attributes. **NEVER** exposes raw scoring, numeric Big Five traits, or detailed Dreyfus levels.
- **Human review:** through the deployer client's formal compliance channel.
- **Contestation:** 30 days from decision notification (EU AI Act Art. 86 + LGPD Art. 20).
- **Access/deletion:** via `data_subject_request`.

## 10. Contacts

- **Compliance:** compliance@wedotalent.cc
- **Support:** support@wedotalent.cc
- **Privacy (DPO):** dpo@wedotalent.cc

---

*Canonical source: `app/prompts/domains/wsi_evaluation.yaml` + `wsi_layer2_extraction.yaml` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invention.*
