# ADR-001 — Repository Pattern (Canonical)

**Status**: Accepted (canonized 2026-05-06; previously phantom — only mentioned in CLAUDE.md memory)
**Data efetiva**: 2026-04-08 (data informal); canonized 2026-05-06
**Última revisão**: 2026-05-06 (Sprint 5 prep)

---

## Contexto

ADR-001 era referenciado em CLAUDE.md memory + commit messages há semanas mas **nunca existiu em `docs/specs/ai/`**. Auditoria F 2026-05-06 descobriu:

- 144 service files com raw SQL inline (`db.execute|sa_text|sqlalchemy.text`)
- 126 service files com `select(Model)` direto
- 839 SQL call sites em services
- Apenas 2.7% dos repos (3/111) chamam `_require_company_id`
- Sensores `check_no_sql_inline_in_services.py` + `check_no_select_in_services.py` claimed em CLAUDE.md memory mas **NÃO EXISTEM** em `feat/benefits-prv-canonical`

Esta ADR canoniza o Repository Pattern + define **Caminho C policy** (legacy frozen, new code clean), aceitando a dívida pré-existente como permanente.

---

## Decisão

### 1. Anatomia canonical

```
Plataforma (FastAPI app)
    └── Domain (job_creation / cv_screening / ...)
        └── API Controller (app/api/v1/*.py)
            └── Service (app/domains/<domain>/services/*.py)
                └── Repository (app/domains/<domain>/repositories/*.py)
                    └── DB / SQLAlchemy
```

### 2. Regras

1. **Services NÃO fazem SQL inline.** Toda query (SELECT/INSERT/UPDATE/DELETE) DEVE ficar em `repositories/`.
2. **Cross-domain reads também via repo:** se `bigfive_service` precisa de `CompanyCultureProfile`, importa `CompanyCultureRepository` — NUNCA `select(CompanyCultureProfile)` direto.
3. **`_require_company_id` em todo método público de repo:** multi-tenancy fail-closed (CLAUDE.md REGRA 1).
4. **Escape hatch documentada:** comentário `# ADR-001-EXEMPT <reason>` na linha rara onde SQL inline é justificado (ex: tabela Rails-owned com schema variável).

### 3. Caminho C policy — legacy frozen (P0 decision)

Auditoria F revelou 144 services + 126 select calls = ~840 hits de dívida pré-existente. **NÃO RATCHETAR**:

- ✅ **Código novo** (qualquer PR pós 2026-05-06): clean — services NÃO podem introduzir SQL inline
- 🟡 **Código existente legacy**: warn-only forever — não força refactor preventivo
- ✅ **Cleanup oportunista**: ao tocar arquivo legacy, mover SQL para repo
- ❌ **NÃO criar** "ADR-001 ratchet" PRs em sourcing/integrations_hub/etc.

Razão: 840 hits = ~80h+ de refactor sem ROI direto. Investir em features. Confiar no sensor warn-only para visibility.

### 4. Sensores (Sprint 5 — atualmente NÃO existem em `feat/benefits-prv-canonical`)

```python
# scripts/check_no_sql_inline_in_services.py (PLANEJADO)
# Detecta `db.execute|text(SELECT...)|sa_text(SELECT...)` em
# app/domains/*/services/*.py
# Mode: warn-only por padrão (Caminho C); --block ao tocar arquivo legacy

# scripts/check_no_select_in_services.py (PLANEJADO)
# Detecta `select(Model)` direto em services
# Mode: warn-only por padrão; --block para arquivos novos
```

**Onde existem hoje**: APENAS em branch `feat/sprint-b-canonical` (commit `4b9526476`, Onda 3.A+B). Branch é local Replit, NÃO pushada. CLAUDE.md memory `project_sprint_b_learning_loops.md` afirma "rodam em pre-commit" mas essa afirmação é específica da branch sprint-b — em `feat/benefits-prv-canonical` (branch ativa) os scripts não existem.

**Sprint 5 task**: criar versões REAIS dos sensores (talvez port de sprint-b-canonical) + canonizar AST-based + warn-only.

### 5. Domains com ZERO repo layer (escopo Sprint 5)

Auditoria F identificou domains que violam ADR-001 estruturalmente:

- `sourcing/` — 20 services, 0 repos
- `recruiter_assistant/` — 13 services, 0 repos (parcial — alguns repos existem)
- `interview_intelligence/` — 6 services, 0 repos
- `talent_intelligence/` — escopo desconhecido
- `modules/` — escopo desconhecido

Sprint 5 backfill: criar `repositories/` por domain, mover queries críticas (não 100%) para fechar P0/P1 routes.

### 6. Multi-tenancy guard (`_require_company_id`)

Todo método público de repo deve começar com:

```python
async def get_jobs_by_status(
    self, *, status: str, company_id: str, db: AsyncSession
) -> list[JobVacancy]:
    self._require_company_id(company_id)  # fail-closed
    # ... rest
```

Sprint 5 audit: lista repos sem guard + adiciona programaticamente.

---

## Estado atual (2026-05-06)

| Métrica | Valor | Target Sprint 5 |
|---|---|---|
| Service files com SQL inline | 144 | Caminho C (não ratchet) |
| Service files com `select(Model)` | 126 | Caminho C |
| Repos com `_require_company_id` | 3/111 (2.7%) | 100% novos; legacy warn-only |
| Sensors `check_no_sql_inline_in_services.py` | NÃO EXISTE em branch ativa | criar Sprint 5 |
| Sensors `check_no_select_in_services.py` | NÃO EXISTE em branch ativa | criar Sprint 5 |
| ADR-001 doc canônico | ❌ phantom | ✅ esta ADR (Sprint 5 partial) |

---

## Consequências

### Positivas
- ✅ ADR-001 deixa de ser fantasma — documento real em `docs/specs/ai/`
- ✅ Caminho C policy formalizada — esquadrão IA não perde tempo em legacy ratcheting
- ✅ Onboarding novo dev fica claro
- ✅ Auditorias futuras têm fonte canônica
- ✅ Sensores Sprint 5 têm scope definido

### Negativas
- ⚠️ Não-determinismo de "quando refactor" — devs decidem caso-a-caso ao tocar legacy
- ⚠️ Sensors blocking podem demorar (Sprint 5 pode ser >40h)
- ⚠️ 144 violações continuam por meses

### Reversibilidade
- Reversibilidade da policy: trivial (mudar de Caminho C → A em outro ADR)
- Reversibilidade dos sensores: trivial (deletar)

---

## Métricas de sucesso

- ✅ ADR documentada em `docs/specs/ai/ADR-001-repository-pattern.md`
- 📋 Sprint 5: criar `check_no_sql_inline_in_services.py` + `check_no_select_in_services.py` (warn-only)
- 📋 Sprint 5: backfill repos em sourcing/recruiter_assistant/interview_intelligence
- 📋 Sprint 5: 100% novos repos com `_require_company_id`
- 📋 Sprint 5: pre-commit hook warn-only ativo

---

## Histórico

- 2026-04-08 (~): citação informal em commit messages e CLAUDE.md memory
- 2026-04-15: referenciada em ARCHITECTURE.md (commit `1a99009e`)
- 2026-05-04: "Caminho C policy" definida em CLAUDE.md memory `project_sprint_b_learning_loops.md`
- 2026-05-05: sensores criados em branch `feat/sprint-b-canonical` (`4b9526476`) — não-pushados
- **2026-05-06: canonized — esta ADR + Q2 Canonical Refactor Sprint 5 plan**

---

## Referências

- CLAUDE.md global (Boy Scout rule + canonical-fix skill)
- ARCHITECTURE.md (ADR-001 referenciada, doc não existia)
- `/tmp/AUDIT-F-SENSORS-REPOS.md` (auditoria 2026-05-06)
- ADR-029 §3 (RuntimeContext) — relacionado a `_require_company_id`
- ADR-030 v2 (Postgres RLS) — defesa em profundidade DB-side
- ADR-006 (No PII in logs) — complementar
