# ADR-030 v2 — Postgres RLS — Baseline + Coverage Gaps

**Status**: Accepted (supersedes ADR-030 v1 — proposed but factually incorrect)
**Data**: 2026-05-06
**Sprint**: Q2 Canonical Refactor (Sprint 4 — Defense in Depth)
**Substitui**: ADR-030 v1 (Proposed)

---

## Contexto — correção factual da v1

ADR-030 v1 alegou: **"0 RLS policies em produção"** baseando-se em busca por
arquivos `*.sql`. Auditoria D 2026-05-06 (`/tmp/AUDIT-D-DB-LAYER.md`) provou
que o claim está **factualmente errado**.

**Realidade verificada** (via `grep "ROW LEVEL SECURITY" alembic/versions/*.py`):

| Migration | Status | Cobertura | Notas |
|---|---|---|---|
| `040_add_rls_multi_tenant.py` | deprecated | — | "broken, never executed" (per docstring de 068) |
| **`068_rls_deny_by_default.py`** | **CANONICAL** | **103 tabelas** | deny-by-default; role `lia_app` non-superuser; função `app_current_company_id()`; session var `app.company_id` |
| `079_sox_audit_company_id.py` | active | 1 (sox_audit_logs) | Especialização SOX |
| `102_realign_compensation_policies.py` | active | 1 (compensation_policies) | Compensation domain |

**Total**: ~107 tabelas com RLS. NÃO é zero.

`get_tenant_db` em `app/core/database.py:39-81` **JÁ wira RLS**:
- `SET ROLE lia_app` (non-superuser)
- `set_config('app.company_id', :company_id, true)` (per-session)
- Fail-closed se SET ROLE falhar

---

## Riscos da v1 se executada verbatim

ADR-030 v1 propunha:
- Session var `app.current_tenant` (DIVERGE do canonical `app.company_id`)
- Migration que cria policies em 10 tabelas — **5 das quais já estão em 068**
  (job_vacancies, vacancy_candidates, audit_logs, interviews, talent_pools)
- Resultado: policies duplicadas/conflitantes + breakage em produção

**Decisão**: ADR-030 v1 **superseded**. Esta v2 documenta baseline real +
gaps verdadeiros + plano de extensão sem regressão.

---

## Decisão (v2)

### 1. Baseline canonical (já implementado)

- Session var canonical: `app.company_id` (set via `app/core/database.py:get_tenant_db`)
- Role canonical: `lia_app` (non-superuser, criado em migration 068)
- Função canonical: `app_current_company_id()` — `current_setting('app.company_id', true)`
- Pattern policy canonical (template para extensões):

```sql
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_<table_name>_select ON <table_name>
    FOR SELECT
    USING (company_id::text = app_current_company_id());

CREATE POLICY tenant_isolation_<table_name>_modify ON <table_name>
    FOR ALL
    USING (company_id::text = app_current_company_id())
    WITH CHECK (company_id::text = app_current_company_id());
```

### 2. Gaps reais (5 tabelas multi-tenant SEM RLS)

Confirmados por audit D — não estão em 068 nem em 079/102:

| Tabela | Domain | Risco | Sprint |
|---|---|---|---|
| `candidates` | cv_screening | 🔴 P0 (PII candidato + cross-tenant select sem fallback) | 4 |
| `wsi_sessions` | wsi | 🟡 P1 (sessão de triagem voice/text) | 4 |
| `wsi_results` | wsi | 🟡 P1 (resultado triagem com scores) | 4 |
| `screening_question_sets` | wsi | 🟡 P1 (perguntas customizadas por empresa) | 4 |
| `messages` | unified_chat | 🟡 P1 (chat history) | 4 |

### 3. Migration 118 (próxima livre — confirmado audit D)

Single migration `118_rls_complete_coverage.py` adiciona RLS para os 5 gaps,
seguindo pattern canonical de 068. Idempotente (`IF NOT EXISTS`).

### 4. Bypass admin/superadmin path (NÃO documentado em v1)

Algumas operações precisam cross-tenant: admin reports, migrations, batch
jobs de ML training. Pattern canonical:

```python
# app/shared/admin/cross_tenant_session.py (NOVO em Sprint 4)

@asynccontextmanager
async def cross_tenant_session(reason: str, audit_user_id: str):
    """Yield session with RLS bypass — must be audited via audit_logs.

    Use ONLY for documented cross-tenant operations (admin reports,
    cross-company analytics, migrations). Every entry creates an
    audit_log row with reason + user_id + timestamp.
    """
    async with AsyncSessionLocal() as session:
        # Switch to superuser role for cross-tenant access
        await session.execute(text("SET ROLE postgres"))
        await audit_service.log_cross_tenant_bypass(
            user_id=audit_user_id,
            reason=reason,
            session_id=str(session.bind.url),
        )
        try:
            yield session
        finally:
            await session.execute(text("RESET ROLE"))
```

### 5. Sensor harness — `check_table_has_rls_policy.py` (planejado Sprint 4)

AST-based scanner sobre `libs/models/lia_models/*.py`:
- Coleta toda tabela com coluna `company_id`
- Cross-references com `alembic/versions/*.py` para detectar `ENABLE ROW LEVEL SECURITY`
- Falha se tabela com `company_id` NÃO tem RLS migration

Inicialmente warn-only durante Sprint 4 enquanto migrations são aplicadas.
Promove para `--block` após smoke test em staging.

### 6. Verificação operacional (BLOQUEADA por SSH-only Postgres)

**NÃO É POSSÍVEL** verificar do código se 068 efetivamente aplicou em
staging (cross-tenant code paths em `billing.py` / `observability.py` que
usam `cross_tenant_session_legacy` não falham hoje — pode indicar (a) 068
nunca aplicou, ou (b) bypass não documentado existe).

**Sprint 4 task obrigatório**: SSH staging Postgres + `\dp candidates`
para confirmar RLS state. Se 068 não aplicou, executar antes de migration 118.

---

## Migration plan (Sprint 4)

| Task | Esforço | Skill |
|---|---|---|
| Verificar staging Postgres state (SSH `\dp` em 5 tabelas gap) | 1h | manual |
| Migration 118 RLS para 5 gaps | 4h | `/canonical-fix` |
| `cross_tenant_session` admin bypass + audit | 3h | `/security-review` |
| Tests RLS gaps (5 tabelas × 2 tests) | 4h | `/tdd-workflow` |
| Sensor `check_table_has_rls_policy` (warn) | 2h | `/harness-engineering` |
| Smoke E2E staging | 1h | manual |
| **Total Sprint 4** | **~15h** | (vs ADR-030 v1 que estimou 25h) |

---

## Consequências

### Positivas
- ✅ Defense in depth at DB layer (já existia + completa)
- ✅ Nenhuma policy duplicada (corrige risco da v1)
- ✅ Bypass admin documentado + auditado
- ✅ Sensor previne futuros gaps
- ✅ Performance overhead = mantido (não há mudança em 103 tabelas existentes)

### Negativas
- ⚠️ Sprint 4 depende de verificação SSH staging antes de migration 118
- ⚠️ 5 tabelas gap continuam vulneráveis até migration aplicar

### Reversibilidade
Migration 118 reversível via `op.execute("DROP POLICY ...")` em down().
Bypass admin reversível removendo `cross_tenant_session.py` + chamadas.

---

## Métricas de sucesso

- 5 tabelas gap com RLS ativo (verificável `\dp <table>`)
- 0 cross-tenant data leaks em smoke test
- Bypass admin auditado em `audit_logs`
- Sensor `check_table_has_rls_policy` com 0 findings
- Tests Sprint 4: 10+ green
- Performance P95 query time: +<10ms

---

## Referências

- Migration `068_rls_deny_by_default.py` (canonical baseline)
- `/tmp/AUDIT-D-DB-LAYER.md` (verificação 2026-05-06)
- ADR-030 v1 (superseded)
- Postgres RLS docs: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- ADR-001 (Repository Pattern) — complementar
- ADR-029 §3 (RuntimeContext / `_current_company_id`) — app-layer
