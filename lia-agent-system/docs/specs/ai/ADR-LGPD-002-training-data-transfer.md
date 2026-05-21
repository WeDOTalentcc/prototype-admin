# ADR-LGPD-002: Training Data Cross-Border Transfer (T-21)

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-21, fix Reviewer C4)
**Bloqueia:** T-11 RLHF Anthropic fine-tune pipeline
**Relaciona:** ADR-LGPD-001 (aggregates), ADR-032 (feedback wire), T-10 Fase 1 (mirror writer)

## Contexto

T-10 Fase 1 desbloqueou `InteractionFeedback` mirror writer — training data pipeline
deixou de estar starving e agora capta correções/feedback de usuários.

T-11 propõe upload desse dataset para **Anthropic fine-tuning API (US)** para
RLHF/DPO. Cross-border data transfer **DEVE** cumprir LGPD Art. 33 + Art. 12 §1.

Reviewer C4 (Sprint 2 V2 review): "Training data crossing fronteira sem LGPD
Art. 33 evidência. ADR-LGPD-002 explicit + anonymizer obrigatório".

## Estado pré-T-21

```
InteractionFeedback (DB)
  → _get_quality_feedback()  [filter rating ≥4]
  → export_openai_format() / export_anthropic_format() / export_dpo_pairs()
  → list[dict] com {user_message, lia_response, correction}  ← PII RAW
  → caller serializa JSON → upload (gap T-11 bloqueado)
```

`user_message`/`lia_response`/`correction` são strings raw com possível CPF,
email, nome, telefone do candidato. Upload direto → **LGPD Art. 33 violation**.

## Decisão

### 1. Base legal canonical

| Artigo LGPD | Aplicação |
|---|---|
| **Art. 7 §I** | Consentimento explícito opt-in granular do candidato para training data |
| **Art. 12 §1** | Anonimização irreversível (SHA-256 hash + PII strip) ANTES de cross-border |
| **Art. 33 §I** | Transferência internacional permitida para cumprir contrato/serviço |
| **Art. 18** | DSAR cascade: candidato pode pedir exclusão; training data retém apenas hash + anonymized fragments |

### 2. Anonymizer canonical obrigatório

`app/domains/analytics/services/training_data_anonymizer.py`:

```python
class TrainingDataAnonymizer:
    @staticmethod
    def hash_candidate_id(raw_id) -> str:
        return hashlib.sha256(str(raw_id).encode()).hexdigest()  # one-way

    def anonymize_sample(self, sample: dict) -> dict:
        # 1. PII strip (regex + Presidio NER opt-in) via strip_pii_for_llm_prompt
        # 2. Hash candidate_id (drop raw)
        # 3. Drop free-text identifiers (email, phone, cpf, name, ...)
        # 4. Drop demographic data unless allow_demographic=True
        # 5. Add _anonymization_version + _anonymized_at

    def sanity_check_batch(self, samples) -> None:
        # Re-detect EMAIL/CPF/PHONE patterns
        # Raise AnonymizationError se algum residual

    async def process_batch(self, samples, *, company_id, skip_sanity=False) -> list[dict]:
        # Apply anonymize_sample + sanity_check
        # Returns clean samples ready for cross-border upload
```

### 3. Consent layer (granular opt-in)

`consent_records.consent_type` aceita valor canonical `"training_data"`:
- Candidato opta-in **explicitamente** via UI (frontend T-21b future)
- Filtro em `_get_quality_feedback`: incluir apenas feedback de candidates com
  `consent_records.consent_type='training_data' AND is_active=true AND revoked_at IS NULL`
- Default: **opt-OUT** (candidato precisa optar para incluir seus dados)

### 4. Transfer Impact Assessment (TIA) Anthropic

| Dimensão | Status |
|---|---|
| **Provedor compliance** | Anthropic SOC 2 Type II ✓, ISO 27001 ✓ |
| **DPA bilateral** | **PENDENTE** — bloqueia upload até assinatura |
| **Sub-processadores** | Anthropic Trust Center lista; AWS/GCP US-East |
| **Encryption transit** | TLS 1.3 obrigatório ✓ |
| **Encryption rest** | Anthropic gerencia (AES-256) |
| **Retenção** | Training data retido até modelo de-deployed + 90d |
| **Erasure cascade** | Cláusula contratual obrigatória se DSAR Art. 18 |

**Status atual:** DPA Anthropic **pendente assinatura legal**. T-11 RLHF
**NÃO pode** iniciar antes do DPA. Sensor canonical bloqueia.

### 5. Sensor canonical

`scripts/check_training_data_anonymized.py`:

- Regra: `training_data_service.export_*` métodos DEVEM chamar
  `TrainingDataAnonymizer.process_batch()` ou ter comment `# ANONYMIZER-EXEMPT: <reason>`
- Modo INICIAL: WARN-ONLY
- Promover BLOCKING após T-21b wire em todos export_* methods

### 6. T-21 implementação atual (este commit)

- ✓ `TrainingDataAnonymizer` service canonical criado
- ✓ Sensor `check_training_data_anonymized.py` (warn-only)
- ✓ ADR-LGPD-002 documentado
- ⏳ Wire em `export_*` methods (T-21b sprint próximo)
- ⏳ DPA Anthropic assinatura (legal team)
- ⏳ Consent layer UI frontend (T-21c)

## Consequências

**Positivas:**
- T-11 RLHF unblocked após T-21b + DPA done
- LGPD Art. 12/18/33 compliance via anonymizer + consent
- Sanity check evita data leak por bug do PII stripper
- Audit trail completo via T-20 audit_log

**Negativas:**
- DPA Anthropic bloqueia T-11 até assinatura (caminho crítico legal)
- Sample size training data pode cair drasticamente após opt-in filter (T-21c UI essencial)
- Performance: anonymizer add ~50-100ms por sample em batches grandes (aceitável para batch jobs)

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-21 (este)** | 4 | Anonymizer + sensor + ADR canonical |
| T-21b | 5 | Wire anonymizer em export_openai_format, export_anthropic_format, export_dpo_pairs |
| T-21c | 5+ | Frontend consent UI opt-in granular training_data |
| T-21d | Legal | DPA Anthropic assinatura |
| T-11 | 6+ | RLHF pipeline (UNBLOCKED só após T-21b + T-21d done) |

## Referências

- Reviewer C4 (Sprint 2): "C4 RLHF training data crossing border sem LGPD evidência"
- PLANO_ACAO_REPLIT_V3 T-21
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm
- Anthropic Trust Center: https://trust.anthropic.com/
- `app/shared/pii_masking.py` (canonical PII strip)
- ADR-LGPD-001 (aggregates pattern)
