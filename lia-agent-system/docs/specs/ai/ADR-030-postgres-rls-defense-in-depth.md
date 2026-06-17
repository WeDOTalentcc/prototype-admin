# ADR-030 — Postgres Row-Level Security (RLS) como Defense-in-Depth Multi-Tenancy

**Status**: Superseded by ADR-030 v2 (2026-05-06 — v1 had factual errors; see ADR-030-v2-postgres-rls-baseline-and-gaps.md)
**Data**: 2026-05-06
**Contexto**: Audit revelou multi-tenancy 100% dependente de app layer (sem fallback DB)
**Sprint**: Q2 Canonical Refactor (Sprint 0)

---

## Contexto

Sistema atual tem multi-tenancy enforcement spread em **5 camadas app-layer**:

1. `app/middleware/auth_enforcement.py` — JWT decode + ContextVar set
2. `app/tools/executor.py:397` — `if requires_company_id and not ctx.company_id: reject`
3. Repositories `_require_company_id()` (apenas 6 repos têm)
4. Direct SQL: `WHERE company_id = ...` (44 arquivos com pattern)
5. Prompt instruction: TENANT_ISOLATION_BLOCK (resolvido tactically esta sessão)

### Problema crítico

**Sem Row-Level Security (RLS) no Postgres**, qualquer bug em qualquer das 5 camadas → vazamento de tenant data. Verificado via audit:

```
$ find . -name "*.sql" | xargs grep -l "ROW LEVEL SECURITY"
(empty)
```

**0 RLS policies em produção.** Padrão enterprise (Auth0, Stripe, Supabase) tem RLS como CAMADA FINAL — mesmo se app falhar, DB bloqueia query cross-tenant.

### Anti-pattern atual

```python
# Service típico:
async def get_jobs(db, company_id: str):
    return await db.execute(
        select(JobVacancy).where(JobVacancy.company_id == company_id)
    )

# Bug hipotético: dev esquece o WHERE
async def get_jobs_buggy(db):
    return await db.execute(select(JobVacancy))  # ← retorna TODAS empresas!
```

Sem RLS, o bug acima retorna dados de todos os tenants. Com RLS, Postgres bloqueia.

---

## Decisão

### 1. **Habilitar RLS nas 10 tabelas multi-tenant críticas**

Tabelas alvo (Sprint 4):
- `job_vacancies`
- `candidates`
- `vacancy_candidates` (link)
- `wsi_sessions`
- `wsi_results`
- `screening_question_sets`
- `interviews`
- `audit_logs`
- `talent_pools`
- `messages` (chat history)

### 2. **Pattern canonical RLS**

```sql
-- Migration alembic 107_enable_rls_multi_tenant.sql

ALTER TABLE job_vacancies ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_select ON job_vacancies
    FOR SELECT
    USING (company_id::text = current_setting('app.current_tenant', true));

CREATE POLICY tenant_isolation_modify ON job_vacancies
    FOR ALL
    USING (company_id::text = current_setting('app.current_tenant', true))
    WITH CHECK (company_id::text = current_setting('app.current_tenant', true));
```

### 3. **App-side: setar `app.current_tenant` por session**

`app/core/database.py:get_tenant_db` já tem hook. Adicionar:

```python
async def get_tenant_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    company_id = getattr(request.state, "company_id", "")
    
    async with AsyncSessionLocal() as session:
        # Set Postgres session variable for RLS policies
        if company_id:
            await session.execute(
                text("SET LOCAL app.current_tenant = :tenant"),
                {"tenant": str(company_id)},
            )
        yield session
```

### 4. **Bypass para superadmin / system tasks**

Algumas operações precisam cross-tenant (admin reports, migrations). Pattern:

```python
# Para operações cross-tenant (raro):
async with AsyncSessionLocal() as session:
    await session.execute(text("SET LOCAL app.current_tenant = ''"))
    # Now SELECT/INSERT cross-tenant work, com auditoria explícita
    ...
```

Tabela `audit_logs` para registrar todo bypass.

### 5. **Testing strategy**

Tests obrigatórios:
- `test_rls_blocks_cross_tenant_select` — empresa A não vê dados B
- `test_rls_blocks_cross_tenant_insert` — empresa A não pode inserir como B
- `test_rls_admin_bypass_audited` — admin path registra bypass
- `test_rls_migration_idempotent` — alembic up/down preserva data

### 6. **Sensor harness**

Sensor `check_table_has_rls_policy.py` — verifica que toda tabela com `company_id` em schema tem `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.

Inicialmente warn-only durante migration. Blocking após todas 10 tabelas habilitadas.

---

## Migration plan (Sprint 4)

| Task | Esforço | Skill |
|---|---|---|
| Alembic migration: enable RLS em 10 tabelas | 4h | `/canonical-fix` |
| Update `get_tenant_db` para SET LOCAL | 2h | `/production-quality:modules:backend-quality` |
| Tests RLS coverage (10 tabelas × 2 tests) | 8h | `/tdd-workflow` |
| Bypass pattern para admin paths | 3h | `/security-review` |
| Sensor `check_table_has_rls_policy` | 2h | `/harness-engineering` |
| Smoke test E2E em staging | 4h | manual |
| Rollback plan + docs | 2h | docs |
| **Total** | **~25h** | |

---

## Consequências

### Positivas
- ✅ Defense in depth at DB layer (fallback se app layer falhar)
- ✅ Bug hipotético "esqueceu WHERE company_id" → bloqueado
- ✅ Compliance LGPD reforçada (segregação física via DB)
- ✅ Alinha com Auth0, Stripe, Supabase patterns
- ✅ ADR-001 violations (44 SQL inline) ficam mais seguras mesmo sem refator

### Negativas
- ⚠️ Performance overhead pequeno (~5-10% em queries com RLS)
- ⚠️ Debugging mais complexo (queries falham silenciosamente se ctx faltando)
- ⚠️ Rollback complicado se migrations já populadas
- ⚠️ Testing infra precisa de fixture per-tenant

### Reversibilidade
Migration alembic up/down pode habilitar/desabilitar RLS sem perda de dados. Custo de rollback: baixo durante 1ª semana após deploy; médio depois.

---

## Métricas de sucesso

- 10 tabelas críticas com RLS ativo
- 0 cross-tenant data leaks em smoke test
- Bypass admin auditado em `audit_logs`
- Sensor `check_table_has_rls_policy` blocking
- Performance: P95 query time +<10ms
- Tests: 20+ RLS-specific tests green

---

## Referências

- Postgres RLS docs: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Auth0 multi-tenancy patterns
- Stripe Connect tenant isolation
- ADR-001 (Repository Pattern) — complementar
- CLAUDE.md REGRA 1 (multi-tenancy)
