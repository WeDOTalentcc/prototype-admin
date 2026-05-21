# ADR-RLHF-001: Custom Claude fine-tune via AWS Bedrock (T-11)

**Status:** Aprovado 2026-05-21 (T-11 Fase B.1 — Foundation)
**Decisor:** Paulo Moraes (aprovou D-T11-1=A, D-T11-2=A, D-T11-3=A)
**Relaciona:** ADR-LGPD-002 (training data transfer), ADR-032 (feedback wire),
ADR-031-v3 (FairnessGuard L3), T-21+T-21b (anonymizer canonical),
T-13 (per-tenant YAML), T-19 (Thompson sampling)

## Contexto

Pipeline canonical de fine-tuning de modelo Claude usando feedback dos
recrutadores capturado via `InteractionFeedback` + `FeedbackLearningService`
(T-10 Fase 1-4 done). Pré-T-11:

- ✅ T-21 done: `TrainingDataAnonymizer` canonical (LGPD Art. 12 §1 + Art. 33)
- ✅ T-21b done: anonymizer wired em 3 export_* methods (sensor BLOCKING)
- ✅ T-10 Fase 4: feedback wired (5/6 outcomes)
- ✅ TRAINING_PERSONA v2.0 versionado (intencionalmente desacoplado runtime)
- ⏳ T-21c: frontend consent UI granular opt-in (P1 backlog)
- 🚫 T-21d: DPA Anthropic legal signature (pending)
- 🚫 T-11: pipeline canonical (este ADR)

Pre-audit Fase A (`T11_FASE_A_AUDIT_2026-05-21.md`) revelou:
1. **Anthropic SDK 0.76.0 NÃO tem fine_tunes attribute** (confirmação via dir())
2. **Único caminho canonical Claude fine-tune = AWS Bedrock** (partnership exclusiva)
3. **Claude 3 Haiku ONLY** fine-tunable (não Sonnet/Opus) US West Oregon
4. **InteractionFeedback é do recrutador** (user_id), não candidato (candidate_id absent)
5. **GRANULAR_PURPOSE_MAP** sem `"training_data"` purpose (gap canonical)
6. **list_quality_feedback** sem consent filter (gap canonical)

## Decisão

### 1. Provider canonical = AWS Bedrock Claude 3 Haiku (D-T11-1=A)

**Razões:**
- Único caminho oficial Anthropic-blessed pra fine-tune Claude
- LIA já é "Claude-flavored" em todos prompts (persona preservada)
- Anthropic reporta +9.9% accuracy Haiku custom vs Sonnet base
- AWS partnership estabelecida pra Bedrock service

**Trade-offs aceitos:**
- Vendor lock-in duplo (Anthropic via AWS)
- DPA dupla (Anthropic + AWS Bedrock)
- Region US West Oregon exclusivo (LGPD Art. 33)
- Custom model lives in WeDOTalent AWS account
- Inference via `boto3.client("bedrock-runtime")`, não anthropic SDK
- Haiku custom (não Sonnet) — performance gap mitigated por Anthropic +9.9% reported

### 2. Multi-tenant strategy = Global WeDOTalent MVP (D-T11-2=A)

**Modelo canonical:** `WeDO-Haiku-v1` (single fine-tuned model)
- Treina com feedback de TODOS tenants opt-in (consent_type='training_data')
- Cross-tenant pattern learning canonical
- Custo: 1 modelo Bedrock training + storage + inference

**Per-tenant (Opção B) fica como enterprise SKU futuro:**
- Custom model per Fortune 500 tenant
- Custo: N modelos Bedrock × N tenants (caro)
- Upsell quando demanda enterprise validada

### 3. Eval framework = BLEU/exact match + ThompsonSampler A/B (D-T11-3=A)

**Gate quantitativo (Fase B.4):**
- Held-out 10% feedback samples como golden eval set
- Métricas: BLEU, exact match rate, custom WeDOTalent score
- Promotion gate: modelo custom DEVE passar threshold > base Haiku

**Bandit live (após deploy):**
- A/B test custom vs base Haiku via T-19 ThompsonSampler
- FairnessConstraint gate (T-19 ADR-AB-001) ANTES de promote winner
- Statistical significance + Bayesian convergence

### 4. Consent canonical = training_data purpose granular

Aplicado em **T-11 Fase B.1.1 (este sprint):**

```python
# app/domains/lgpd/services/granular_consent_service.py
GRANULAR_PURPOSE_MAP = {
    ...,
    "training_data": "TRAINING_DATA",  # T-11 B.1.1
}

BLOCKING_PURPOSES = {..., "training_data"}  # T-11 B.1.1 — revoke cascata
```

Próximo (T-11 Fase B.1.2 backlog): wire `list_quality_feedback` filter consent.

### 5. Pipeline canonical (alvo Fase B.2-B.4)

```
[Recrutador feedback]                           [LGPD Art. 6/12]
  ↓ InteractionFeedback                                ↓
  ↓ T-10 mirror writer                                 ↓
[FeedbackLearningService.record_feedback]              ↓
  ↓                                                    ↓
[training_data_service.export_*]                       ↓
  ↓ filter quality + consent_type='training_data'      ↓
  ↓ T-21 TrainingDataAnonymizer (PII strip L1-4)       ↓
[anonymized JSONL]  ←─────────────────────────────────┘
  ↓
[bedrock_uploader] (S3 upload us-west-2)
  ↓
[bedrock_fine_tuner] (Bedrock customization job)
  ↓ 12-24h training
[BedrockClaudeLLMProvider model_id ARN]
  ↓
[eval_runner.py] BLEU/exact match vs base Haiku
  ↓ pass gate
[model_promoter] → LLM factory wire (custom model ARN)
  ↓
[Production inference via boto3 bedrock-runtime]
  ↓ A/B test ThompsonSampler (T-19) + FairnessGuard L3
[Winner promoted via auto_promote_winner (com FairnessConstraint gate)]
```

### 6. AWS Bedrock specs canonical

| Item | Valor |
|------|-------|
| Modelo base | `claude-3-haiku-20240307` |
| Region | `us-west-2` (Oregon) |
| Custom model ARN | `arn:aws:bedrock:us-west-2:<ACCOUNT>:custom-model/<MODEL>` |
| Training format | JSONL (1 sample/line) |
| Context length | Até 32K tokens |
| Sample format | `{"system": "...", "messages": [{"role": "user", ...}, {"role": "assistant", ...}]}` |
| Training cost | ~$50-200/M tokens (depende tier) |
| Inference cost | ~$0.50-3/M tokens base (custom premium markup) |
| Storage cost | ~$1.95/mês per custom model |
| Training time | 8-24h típico |

## Plano canonical Fase B (sequential)

### Fase B.1 — Foundation legal+compliance (3-4d) [PARCIALMENTE DONE]

- ✅ **B.1.1** — Add `"training_data"` em `GRANULAR_PURPOSE_MAP` + `BLOCKING_PURPOSES`
- ⏳ **B.1.2** — Criar `CompanyTrainingConsent` model + migration alembic
  (alternativa: estender `LGPDConsent` ou usar `ConsentRecord` com candidate_id sentinel)
- ⏳ **B.1.3** — Wire `FeedbackRepository.list_quality_feedback` filter consent_records
- ⏳ **B.1.4** — Sensor `check_consent_filter_training_data.py` BLOCKING
- ✅ **B.1.5** — ADR-RLHF-001 (este documento)

### Fase B.2 — Bedrock provider canonical (5-7d) [BLOQUEADO até AWS account]

- B.2.1 — Criar `app/shared/providers/llm_bedrock_claude.py`
- B.2.2 — Adapter messages → Bedrock body format
- B.2.3 — Wire em `LLMProviderFactory` (4o provider canonical)
- B.2.4 — Smoke test invoke `claude-3-haiku` base model via Bedrock
- B.2.5 — Sensor `check_bedrock_provider_canonical.py`

### Fase B.3 — Fine-tune pipeline (6-8d) [BLOQUEADO até B.2]

- B.3.1 — `app/shared/intelligence/fine_tune/bedrock_uploader.py` (S3 + JSONL)
- B.3.2 — `bedrock_fine_tuner.py` (job invoke + tracking)
- B.3.3 — `job_tracker.py` (cron sync status)
- B.3.4 — `model_promoter.py` (ARN → LLM factory wire)
- B.3.5 — End-to-end test (100 samples → Haiku custom)

### Fase B.4 — Eval + deploy (4-6d) [BLOQUEADO até B.3]

- B.4.1 — `eval_runner.py` BLEU + exact match canonical
- B.4.2 — Golden eval set (held-out 10%)
- B.4.3 — A/B integration ThompsonSampler T-19
- B.4.4 — Promotion gate (threshold pass = wire em LLM factory)
- B.4.5 — Sensor `check_finetune_eval_pass.py` BLOCKING

## Dependências externas (não-código, paralelo)

| Item | Status | Owner |
|------|--------|-------|
| T-21d DPA Anthropic signature | ⏳ Pending | Legal team |
| DPA AWS Bedrock signature | ⏳ Pending | Legal team |
| AWS account setup us-west-2 Bedrock | ⏳ Pending | DevOps |
| AWS IAM roles + Bedrock permissions | ⏳ Pending | DevOps |
| T-21c frontend consent UI | ⏳ Pending | Frontend team |

## Consequências

**Positivas:**
- Diferencial competitivo Fortune 500 (modelo custom WeDOTalent)
- Persona LIA canonical preservada (Claude-flavored em todos prompts)
- +9.9% accuracy reportada (Anthropic Haiku custom benchmark)
- Pipeline LGPD-safe (T-21 anonymizer + consent filter + AWS DPA + ANPD §3)
- Alinhado com canonical Anthropic+AWS partnership

**Negativas:**
- Vendor lock-in duplo (Anthropic via AWS)
- DPA dupla complexity (Anthropic + AWS Bedrock)
- Setup AWS account + DPA = ~2 semanas legal+ops antes de iniciar B.2
- Haiku (não Sonnet) — trade-off canonical Anthropic-enforced
- Custom model storage AWS = $1.95/mês per modelo

**Riscos:**
- Anthropic muda Haiku → Sonnet → Opus fine-tune support roadmap (low)
- AWS Bedrock service changes pricing (medium)
- LIA prompt drift entre TRAINING_PERSONA v2.0 e lia_persona.yaml runtime (mitigated via versioning)
- Modelo custom regredir vs base (mitigated via eval gate B.4.4)

## Mitigation canonical

1. **Persona drift:** `TRAINING_PERSONA_VERSION` + `TRAINING_PERSONA_UPDATED_AT` em `training_persona.py` enforce
2. **Eval regression:** Promotion gate threshold canonical (BLOCKING sensor B.4.5)
3. **Consent revoke:** training_data em BLOCKING_PURPOSES (revoke cascata)
4. **Cost overrun:** Bedrock budget alert + manual override gate em production deploy

## Próximas decisões pendentes

| Decisão | Quando | Owner |
|---------|--------|-------|
| AWS region multi-presence (futuro Sao Paulo Bedrock?) | Quando AWS lançar sa-east-1 Bedrock | Paulo + DevOps |
| Per-tenant SKU enterprise pricing | Quando 5+ Fortune 500 demandarem | Paulo + Sales |
| Vision capability adoption (Bedrock roadmap) | Quando Anthropic anunciar Haiku vision custom | Roadmap |

## Referências

- [Finetuning Claude 3 Haiku on Bedrock — Anthropic Cookbook](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [Fine-tune Claude 3 Haiku in Amazon Bedrock — Anthropic News](https://www.anthropic.com/news/fine-tune-claude-3-haiku)
- [AWS Bedrock model customization docs](https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html)
- T11_FASE_A_AUDIT_2026-05-21.md (este sprint Fase A canonical)
- ADR-LGPD-002 (training data transfer T-21)
- ADR-032 (feedback wire canonical T-10)
- ADR-AB-001 (Thompson + FairnessGate T-19)
- LGPD Lei 13.709/2018 Art. 6, 7, 12 §1, 18, 20, 33
- ANPD Guia de Anonimização §3 (irreversibilidade canonical)
- EU AI Act 2024 Art. 10(5) (special-category processing for bias)
