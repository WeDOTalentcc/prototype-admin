# ADR-030-v3: RLS HIGH-Priority Batch (T-02 Sprint 1)

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (decisão via PLANO_ACAO_REPLIT_V3 + Sprint Execution Protocol)
**Suplementa:** ADR-030 (Postgres RLS defense-in-depth), ADR-030-v2 (RLS baseline + gaps)
**Relaciona:** ADR-LGPD-001 (aggregates), Migration 068_rls_deny_by_default

## Contexto

ADR-030-v2 documentou baseline RLS em 107 tabelas via migration 068. Auditoria SSH
exaustiva 2026-05-20 (Sprint Execution Protocol Fase A) revelou que o gap real era
muito maior do que documentado:

- **277 tabelas com company_id** (modelo)
- **129 com RLS enabled** (DB live, pre-T-02)
- **176 GAPS** (modelo declara company_id mas DB sem RLS policy)

Plano V3 originalmente listou apenas 4 tabelas em T-02 (subestimou 44x).
Triagem canonical das 176 GAPS:

- **HIGH (51 tabelas):** PII candidato direto + decisões automatizadas LGPD Art. 20 +
  LGPD compliance trail (consent, DSAR, breach)
- **MEDIUM (~80 tabelas):** business data, configs, metrics
- **LOW (~46 tabelas):** logs internos, caches, webhooks

## Problema descoberto

Das 51 HIGH, auditoria DB live (information_schema query) revelou:

- **27 tabelas READY:** TÊM company_id no DB live → RLS direto aplicável
- **24 tabelas com drift modelo↔DB:** modelo declara company_id mas DB NÃO TEM coluna
  (migration de criação da coluna faltou ou foi rolled back)

T-02 Sprint 1 fecha apenas as 27 READY. As 24 com drift viram **T-02b sprint 2**:
exigem ADD COLUMN + backfill via JOIN com parent table.

## Decisão

Migration `139_t02_rls_high_priority.py` aplica RLS deny-by-default em **27 tabelas**:

### 18 NOT NULL (RLS direto sem backfill)
bias_audit_reports, bigfive_department_profiles, consent_versions,
conversation_memories, data_access_logs, data_incidents, data_requests,
data_subject_requests, dpo_registry, ideal_profiles, import_batches,
imported_job_descriptions, interaction_feedback, interview_notes,
learning_patterns, recruiter_decision_feedback, routing_feedback,
wsi_question_effectiveness

### 4 NULLABLE UUID (backfill UUID sentinel)
big_five_role_profiles, fairness_audit_log, incident_reports, model_evaluations

Backfill: `'00000000-0000-0000-0000-000000000001'::uuid` (sentinel default tenant)

### 5 NULLABLE varchar (backfill 'demo_company')
calibration_events, calibration_weights, conversations, ml_model_registry,
teams_conversations

### Policy canonical (cast suporta uuid + varchar)

```sql
CREATE POLICY {table}_tenant_select ON {table}
    FOR SELECT
    USING (company_id::text = app_current_company_id());
```

4 policies por tabela: select, insert (WITH CHECK), update, delete.

### Total

- 27 tables × 4 policies = **108 policies aplicadas**
- 9 NULLABLE → NOT NULL (apos backfill)
- ALTER TABLE ENABLE + FORCE ROW LEVEL SECURITY em todas 27

## Consequências

**Positivas:**
- Compliance LGPD Art. 6/11/20 sobre 27 tabelas críticas (PII direto + decisão automatizada)
- EU AI Act Annex III item 4 melhorado (recrutamento high-risk com defesa em profundidade)
- Cross-tenant data leak prevention via DB enforcement
- Sensor `check_table_has_rls_policy.py` GAPS: 176 → 167 (sensor underreporta — DB live
  mostra 27/27 RLS ativo, discrepância sensor a investigar T-02d)

**Negativas:**
- 9 tabelas tiveram NULLABLE rows backfilled com sentinel (data integrity flag —
  registros pre-backfill agora visíveis apenas ao "demo_company" tenant)
- 24 tabelas HIGH ainda sem RLS (T-02b sprint 2, drift modelo↔DB)
- 125 tabelas MEDIUM/LOW ainda sem RLS (T-02c, sprint 3-4)

**Mitigações:**
- Sentinel data NÃO mistura tenants reais (sentinel é tenant fictício isolado)
- Sensor canonical promovido para BLOCKING em T-14 previne regressão
- T-02b/T-02c queue prioritárias no PLANO_ACAO_REPLIT_V3

## Sensores

- `scripts/check_table_has_rls_policy.py` — existing sensor
  - Atual: WARN-ONLY mode
  - Promover BLOCKING: T-14 sprint 13 (após T-02b + T-02c done)
- **T-02d sprint future:** auditar discrepância sensor (-9 reported vs -27 DB real)

## Verification

```bash
# Sensor canonical
python scripts/check_table_has_rls_policy.py
# Output: 167 GAPS (era 176)

# DB live confirmation
python3 /tmp/check_rls_status.py
# Output: 27/27 RLS enabled, 108 policies total
```

## Testes

Migration aplicada via:
- `alembic upgrade 139_t02_rls_high_priority`
- Current revision: `139_t02_rls_high_priority (head)`
- Idempotente: re-run safe (DROP POLICY IF EXISTS antes de CREATE)

## Roadmap follow-up

| Task | Sprint | Esforço | Escopo |
|---|---|---|---|
| **T-02 (este)** | 1 | 2-3d total | 27 HIGH READY |
| **T-02b** | 2 | 4-6d | 24 HIGH com drift modelo↔DB |
| **T-02c** | 3-4 | 5-7d | 125 MEDIUM/LOW |
| **T-02d** | 13 | 1d | Debug sensor underreport |

## Referências

- PLANO_ACAO_REPLIT_V3 T-02 (escopo original 4, corrigido 51, final Sprint 1: 27)
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md (Fase A pegou o gap)
- ADR-030 (canonical RLS baseline)
- ADR-030-v2 (gaps documentados)
- Migration 068_rls_deny_by_default.py (pattern canonical)
