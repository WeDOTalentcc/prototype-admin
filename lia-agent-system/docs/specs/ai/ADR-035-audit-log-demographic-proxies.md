# ADR-035: Audit Log Demographic Proxies + Fairness Decisions Schema (T-20)

**Status:** Aprovado 2026-05-20 (preventivo U4 reviewer)
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-20)
**Relaciona:** ADR-031-v3 (FairnessGuard L3), ADR-LGPD-001, T-19 (A/B Thompson fairness constraint)

## Contexto

Reviewer U4 (Sprint 2 review independente): "F4 (NYC LL144, EU AI Act) é opcional adiado. Mas LL144 exige schema de tracking de demographic data **estruturado desde o início**. Se F1-F3 não estruturarem audit log com demographic proxies, F4 vira refactor não migration."

Paulo aprovou U4 — audit schema deve entrar em F1, antes de F4 ativar.

Audit existente (`audit_logs` table) cobre AI decisions com `fairness_flags`, `criteria_ignored`, `human_override` mas NÃO tem campos estruturados para:

- Demographic proxies (inferred only, consent-gated)
- Fairness check result detalhado (L1/L2/L3 outputs)
- Variant A/B test usado
- Framework de compliance aplicável
- 4/5ths rule pass/fail
- Decision outcome estruturado
- Candidate ID hash (LGPD-safe)

## Decisão

Migration `144_t20_audit_demographic_proxies.py` adiciona 8 columns:

| Coluna | Tipo | Propósito |
|---|---|---|
| `demographic_proxies` | JSONB | Inferred only + consent-gated. Schema: `{inferred_gender, inferred_age_bracket, inferred_race, consent_level, inference_method}` |
| `fairness_check_result` | JSONB | L1 (regex), L2 (implicit_bias), L3 (LLM semantic) outputs |
| `variant_used` | VARCHAR(100) | A/B test variant if applicable |
| `applicable_frameworks` | JSONB | Array: `["LGPD", "EU_AI_ACT", "NYC_LL144", "CO_SB205", "CA_FEHA"]` |
| `current_rule_compliance` | BOOLEAN | 4/5ths rule pass/fail (NYC LL144) |
| `decision_outcome` | VARCHAR(50) | `approved|rejected|escalated|reviewed_by_human` |
| `candidate_id_hash` | VARCHAR(64) | SHA-256 one-way (LGPD-safe) |
| `audit_metadata` | JSONB | Extensible (consent_basis, request_id, etc) |

### demographic_proxies schema canonical

```json
{
  "inferred_gender": "f|m|nb|unk",
  "inferred_age_bracket": "18-24|25-34|35-44|45-54|55-64|65+",
  "inferred_race": "decl-self|inferred|null",
  "consent_level": "opt-in|inferred-only|declined",
  "inference_method": "name|location|declared|disabled"
}
```

**Quando `consent_level=declined`**, todos os campos demographic devem ser `null`.

### Compliance frameworks

| Framework | Quando aplicar | Trigger |
|---|---|---|
| **LGPD** (sempre) | Toda decisão automatizada com PII | Default em `applicable_frameworks` |
| **EU AI Act Annex III item 4** | Recrutamento high-risk system | Tenant com `eu_residency=true` |
| **NYC LL144** | AEDT bias audit annual | Tenant com `nyc_compliance=true` |
| **CO SB205** | Colorado AI Act 2026 | Tenant com `colorado_compliance=true` |
| **CA FEHA** | California Fair Employment AI provisions | Tenant com `ca_compliance=true` |

## Indexes

- `ix_audit_logs_frameworks` (GIN em JSONB) — queries por framework
- `ix_audit_logs_decision_outcome` — analytics por outcome
- `ix_audit_logs_candidate_id_hash` — DSAR cross-reference (LGPD Art. 18)
- `ix_audit_logs_rule_compliance` — NYC LL144 4/5ths rule report

## Sensor canonical

`scripts/check_audit_log_completeness.py` (WARN-ONLY inicial):

| Regra | Descrição |
|---|---|
| **R1** | `audit_writer.write_decision()` em agentic services DEVE passar `demographic_proxies` (ou `# AUDIT-NO-DEMO: <reason>`) |
| **R2** | `applicable_frameworks` DEVE incluir `LGPD` por default (mínimo Brasil) |
| **R3** | Decisões human-impacting (rejection/shortlist) DEVEM ter `fairness_check_result` |

Promover BLOCKING após T-20b (Sprint 5+): wire demographic capture em 3-5 paths críticos.

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-20 (este)** | 4 | Migration + sensor warn-only + ADR-035 |
| T-20b | 5+ | Wire demographic_proxies capture em cv_screening, sourcing, recruiter_assistant |
| T-20c | 6+ | Bias audit annual report generator (NYC LL144) |
| T-20d | 12+ | Frontend opt-in UI (consent_level) |

## Consequências

**Positivas:**
- F4 LL144/EU AI Act ativa sem refactor — schema ready
- LGPD Art. 20 (explicabilidade) audit trail estruturado
- DSAR (Art. 18) queries via candidate_id_hash
- Sensor previne novas decisões sem demographic context

**Negativas:**
- 8 columns nullable inicial (backfill incremental T-20b)
- ~120 audit decision sites precisarão atualização (Sprint 5+)

## Referências

- Reviewer U4 (Sprint 2): "F4 schema desde início"
- PLANO_ACAO_REPLIT_V3 T-20 (Reviewer C4 push)
- ADR-031-v3 (FairnessGuard L3 cross-sector)
- NYC LL144 Local Law 144 (2023): https://rules.cityofnewyork.us/wp-content/uploads/2023/04/DCWP-NOA-for-Use-of-Automated-Employment-Decisionmaking-Tools-2.pdf
- EU AI Act 2024 Annex III item 4 (recrutamento high-risk)
- LGPD Art. 20 (direito a revisão de decisão automatizada)
