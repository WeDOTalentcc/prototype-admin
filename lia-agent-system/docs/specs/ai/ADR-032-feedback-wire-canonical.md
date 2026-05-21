# ADR-032: Feedback Wire Canonical Pattern (T-10)

**Status:** Aprovado 2026-05-20 (Fase 1)
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-10)
**Relaciona:** ADR-019-v2 (services consolidation), T-11 (RLHF Anthropic), training_data_service

## Contexto

V4 audit confirmou que Learning Loop infra existe (5+ services, A/B testing, training_data_service). Mas:
- 5-7 agentic domains (54%) sem learning wire substancial além do cross-cutting workflow.py
- 2 in-memory leaks (cv_screening + job_creation `CalibrationFeedback`)
- **Training data pipeline STARVING:** `training_data_service` consome `InteractionFeedback` mas ZERO callers escreviam lá

## Decisão

### Taxonomia canonical de 6 services + métodos

| Evento | Service | Método | Persistência |
|---|---|---|---|
| Recrutador corrige campo IA (skill, salary, seniority) | `feedback_learning_service` | `record_feedback()` | `SuggestionFeedback` + **MIRROR `InteractionFeedback`** ✓ |
| Vaga fecha (hired/closed/canceled) | `feedback_learning_service` | `record_outcome()` | `JobOutcome` |
| Decisão atômica (advisory accept/reject) | `feedback_learning_service` | `record_feedback()` | + mirror automatic |
| Signal contínuo (stage transition, score) | `ml_feedback_service` | `record_signal()` | `MLFeedbackSignal` |
| Template/prompt A/B variant performance | `ab_testing_service` | `record_metric()` | `ABTestMetric` |
| Telemetria pós-execução domain | `learning_loop_service` | `record_interaction()` | `LearnedPattern` (já wirado em `workflow.py:201`) |

### Mirror writer canonical (T-10 Fase 1 — ESTE COMMIT)

`feedback_learning_service.record_feedback` agora ALSO persiste em `InteractionFeedback`:
- Desbloqueia `training_data_service` (RLHF/DPO pipeline) que estava starving
- Fail-open: mirror falha não interrompe SuggestionFeedback canonical
- Mapeamento: field/suggested/accepted → rating(0/1) + user_message + lia_response

### Invariantes obrigatórios em todo call site

1. `company_id` SEMPRE de `Depends(require_company_id)` ou `RuntimeContext` — NUNCA de payload
2. Fail-open: wrap em `try/except` + `logger.warning("[FeedbackWire:<domain>] ...")` — feedback nunca derruba caminho crítico
3. Lazy import dentro do try (evita circular import)
4. Mirror automático para training data via `record_feedback`

### Audit log fields obrigatórios (LGPD)

- `tenant_id` (= company_id), `domain_id`, `action_id`
- `actor`: `"recruiter:<user_id>"` ou `"agent:<agent_id>"`
- `original` (LLM output), `final` (human-corrected), `delta_metric`
- `timestamp` UTC
- `consent_basis` (LGPD Art. 7 base legal)

## Roadmap (T-10 Fases)

| Fase | Sprint | Escopo |
|---|---|---|
| **1 (ESTE)** | 3 | Mirror writer + sensor warn-only + ADR-032 |
| 2 | 4 | Wirar 4 P0 gaps: pipeline, hiring_policy, ats_integration, automation |
| 3 | 4-5 | Migrate in-memory CalibrationFeedback: cv_screening + job_creation → persistente |
| 4 | 5+ | sourcing, communication, interview_scheduling, agent_studio (P1-P2) |

## Sensor

`scripts/check_feedback_wire.py` (modo WARN-ONLY):
- R1: agentic domain com método mutativo (db.commit, API external) sem feedback call vizinho → suggest service+método baseado no nome (`*_override*` → record_correction; `*_close*` → record_outcome)
- R2: stub direto de in-memory feedback (NÃO usar `CalibrationFeedback` singleton)

## Consequências

**Positivas:**
- Training data pipeline desbloqueado (RLHF prep T-11 viable)
- Feedback canonical único (não duplicação shared/domains)
- Audit trail LGPD completo
- Sensor previne novos agentic domains sem feedback wire

**Negativas:**
- 4 P0 gaps ainda sem wire (T-10 Fase 2)
- 2 in-memory leaks ainda perdem data em restart (T-10 Fase 3)
- Sensor warn-only — drift possível até Fase 4 BLOCKING

## Referências

- PLANO_ACAO_REPLIT_V3 T-10
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md Fase A descobriu training data starving
- training_data_service.py (consumer downstream)
- feedback_learning_service.py (canonical writer + mirror)
- feedback_service.py:73 (InteractionFeedback writer)
- workflow.py:201 (cross-cutting learning_loop.record_interaction wire)
