# AI Fact Sheet — Ranking and Shortlist

*Last updated: 2026-04-23 | Language: EN | [Versão em português](./ranking-shortlist-fact-sheet-pt.md)*

## 1. Purpose

Ranking and Shortlist consolidates candidates in a job, presents them ordered by match (based on WSI + recruiter calibration), and generates proactive insights about pipeline health (pool size, aggregated demographic diversity, gaps vs. requirements). The final decision of who enters the shortlist is **always made by the human recruiter** — LIA organizes and suggests.

## 2. Inputs

- Candidate list in the job (result of sourcing + CV screening)
- Updated WSI scores (when available)
- Recruiter calibration (`CalibrationWeight`, if configured)
- Job requirements (`job_vacancy`)
- Recruiter preference history (when available)

## 3. Outputs

- Ordered list by score (rank 1..N)
- Main pool narrative (2-3 conversational sentences)
- Highlights (max. 5 positive points)
- Concerns (max. 5 attention points) — e.g., "small pool", "low average score"
- Action recommendations (max. 4)
- Proactive question anticipating next action
- Aggregated metrics: average score, pool size, contact coverage (phone, email)

## 4. Model and Architecture

- **Base LLM model:** `claude-sonnet-4-5` (Anthropic)
- **Canonical domain YAML:** combination of `sourcing.yaml` (96L, version `2.0`) + `recruiter_assistant.yaml` (187L, version `2.0`)
- **Specific variant:** `proactive_insights` in `agent_prompts.yaml` — generates structured narrative
- **Agent:** shared between `RecruiterAssistantAgent` and `SourcingAgent` by context
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="proactive_insights")`

## 5. Protected Attributes — Coverage

- 14 protected attributes via `protected_attributes.yaml` and FairnessGuard L1+L2+L3
- Ranking **never uses protected attributes as criteria** — only technical competencies and WSI score
- Aggregated diversity metrics (% gender, % race/ethnicity) may be reported **at the pool aggregate**, never associated with individual candidates in output
- `compliance_block.yaml` section `decision.bias` has specific guidance on avoiding "cultural fit" as ranking proxy

## 6. Accuracy and Fairness Metrics

→ See section 6 of `eu-ai-act-technical-documentation-en.md` — consolidated metrics. Ranking/Shortlist monitors **group representativeness** (Gender × Race/Ethnicity × Disability) to detect systemic ranking bias (e.g., women consistently at rank > 10). DI ratio target ≥ 0.80. Next independent bias audit: Q3/2026.

## 7. Known Limitations

- **Scoring quality dependence:** ranking is only as good as the WSI score feeding it — if cv_screening fails, ranking inherits the error.
- **Small pool (<10 candidates):** insights may be statistically misleading — feature alerts explicitly.
- **No external lookup:** doesn't actively search new candidates (that's Sourcing's responsibility) — works only with existing pool in the job.
- **Optional calibration:** without `CalibrationWeight`, uses 70% technical / 30% behavioral defaults — may not reflect company's desired profile.

## 8. Human Oversight (HITL)

- **Mandatory:** final shortlist is **exclusively** human decision — LIA suggests, recruiter confirms
- **Mandatory:** confirmation for sharing shortlist with manager
- **Mandatory:** auditable reasoning per candidate in ranking
- **Recommended:** if top-5 average score < 60%, feature suggests search refinement instead of premature shortlisting
- **Recommended:** if pool has systemic bias (low representation of group), feature asks confirmation and suggests expansion

## 9. Candidate Rights

- **Ranking notification:** candidate is **not notified of their ranking position** (internal operational data). If discarded by not entering shortlist, receives communication via Pipeline Transition with LGPD + Art. 86 notice.
- **Explainability:** endpoint `/api/v1/candidate/decisions/explain` shows objective criteria evaluated, **without revealing numeric rank or raw scoring**.
- **Human review:** through deployer client's formal channel.
- **Contestation:** 30 days from discard notification (Art. 86 + LGPD Art. 20).

## 10. Contacts

- **Compliance:** compliance@wedotalent.cc
- **Support:** support@wedotalent.cc
- **Privacy (DPO):** dpo@wedotalent.cc

---

*Canonical source: `app/prompts/domains/sourcing.yaml` + `recruiter_assistant.yaml` + `agent_prompts.yaml` (variant `proactive_insights`) + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invention.*
