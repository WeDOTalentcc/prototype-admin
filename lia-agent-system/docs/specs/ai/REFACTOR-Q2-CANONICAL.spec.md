# REFACTOR Q2 CANONICAL — SPEC.md

**Sprint master plan**: 4 Sprints + Sprint 0 (governance)
**Branch**: `feat/canonical-refactor-q2` (NOVA — separada da `feat/sprint-b-canonical` ativa)
**Esforço total estimado**: ~104h (Sprint 1: 12h + 2: 36h + 3: 31h + 4: 25h)
**Período sugerido**: Q2 2026 (Mai-Jun-Jul)

---

## Contexto

Audit profunda 2026-05-06 (originada por bug LIA pedindo "ID empresa") expôs anti-patterns sistêmicos que **NÃO** são resolvidos pelo fix tactical aplicado nesta sessão (15 agents corrigidos individualmente).

**Anti-patterns identificados**:
1. **Prompt sprawl**: 18 sources of truth para mesma regra (ADR-028)
2. **Tool registry split**: 2 ToolDefinition classes coexistem (ADR-029)
3. **Sem RLS Postgres**: multi-tenancy 100% app-layer (ADR-030)
4. **`protected_attributes.yaml` AUSENTE**: LGPD/Fairness fail-open (ADR-031)
5. Test infra com 32 testes pre-broken (auth fixture)
6. Logging não consolidado (spread em N modules)

**Esta SPEC** consolida os 4 ADRs em master plan executável.

---

## Princípios canônicos aplicados

Conforme CLAUDE.md global + skills:

| Princípio | Aplicação |
|---|---|
| **Computational > Inferential** (`/harness-engineering`) | Cada Sprint adiciona sensor blocking, não só guideline |
| **Single source of truth** (`/canonical-fix`) | Sprint 2: 18 → 1; Sprint 3: 2 → 1 |
| **Defense in depth** | Sprint 4: app + DB layers para multi-tenancy |
| **TDD red-green-refactor** (`/tdd-workflow`) | Tests primeiro em cada migração |
| **Boy Scout rule** | Cada arquivo tocado, P2 fixed inline |
| **REGRA 1** (multi-tenancy JWT) | Sprint 3 wrapper, Sprint 4 RLS |
| **REGRA 4** (no push) | Paulo manual após cada Sprint approved |
| **REGRA 6** (hot files) | Per-file `git log --since="6 hours"` antes de tocar |

---

## Sprint 0 — Governance (esta sessão, ~3-4h)

### Objetivo
Criar ADRs + SPEC + sensor warn-only ANTES de tocar código.

### Deliverables
- ✅ ADR-028 (Single source of truth prompts)
- ✅ ADR-029 (ToolDefinition unification)
- ✅ ADR-030 (Postgres RLS)
- ✅ ADR-031 (Protected attributes YAML — P0)
- ✅ SPEC.md (este arquivo)
- 🔲 Sensor `check_agent_has_universal_blocks.py` (warn-only)
- 🔲 Wire pre-commit hook
- 🔲 Branch nova `feat/canonical-refactor-q2`

### Skills aplicadas
- `/canonical-fix` — design canonical
- `/tlc-spec-driven` — SPECs antes de código
- `/harness-engineering` — sensor pattern

### Exit criteria
- Paulo aprovou todos 4 ADRs
- Sensor instalado warn-only
- Branch nova existe
- 0 código de production tocado

---

## Sprint 1 — Stabilize + LGPD (~12h, 1 semana)

**Severity**: 🔴 P0 — LGPD compliance gap

### Objetivo
Fechar o gap mais grave: `protected_attributes.yaml` AUSENTE em produção.

### Skills
- `/production-quality:modules:compliance-risk`
- `/security-review`
- `/harness-engineering`

### Tasks

| # | Task | Esforço |
|---|---|---|
| 1.1 | Pesquisar termos discriminatórios PT-BR + EN (LGPD/EEOC refs) | 3h |
| 1.2 | Criar `app/config/protected_attributes.yaml` | 2h |
| 1.3 | JSON Schema validator | 1h |
| 1.4 | Update `protected_attributes.py` loader: fail-fast | 1h |
| 1.5 | Tests TDD: FairnessGuard com YAML (positive + negative) | 3h |
| 1.6 | Sensor `check_protected_attributes_yaml_present` blocking | 1h |
| 1.7 | Smoke E2E staging | 1h |

### Acceptance criteria
- [ ] `app/config/protected_attributes.yaml` existe + valid
- [ ] Backend startup: zero "Failed to load YAML" warnings
- [ ] FairnessGuard tests passando 100%
- [ ] Sensor blocking ativo
- [ ] Smoke E2E: vaga com termo discriminatório → bloqueada

### Compliance gates
- ✅ LGPD Art. 5º + Art. 11
- ✅ Lei 9.029/95
- ✅ EEOC Title VII (US)
- ✅ ADR-006 (No PII in logs)

### Risks
| Risk | Mitigation |
|---|---|
| Vagas existentes flagged como discriminatórias | Audit list + remediation plan separado |
| Schema mudanças quebram FairnessGuard | TDD coverage 100% antes de prod |

---

## Sprint 2 — Prompt Canonical (~36h, 2 semanas)

### Objetivo
18 sources of truth → 1 (PromptComposer factory).

### Skills
- `/create-canonical-agent`
- `/tdd-workflow`
- `/design-patterns`
- `/canonical-fix`

### Tasks

| # | Task | Esforço |
|---|---|---|
| 2.1 | Design `PromptComposer` API + interface | 2h |
| 2.2 | Implementação `PromptComposer` + tests TDD | 4h |
| 2.3 | Refactor `LangGraphReActBase` para usar factory | 3h |
| 2.4 | TDD red-phase: tests assert universal blocks present por agent | 3h |
| 2.5 | Migrate 15 agents (~1.5h cada) | 22h |
|     | • WizardReActAgent (CRÍTICO) | |
|     | • JobsManagementReActAgent | |
|     | • TalentReActAgent + KanbanReActAgent | |
|     | • SourcingReActAgent + 4 sub-agents | |
|     | • CV Screening, Communication, Analytics, ATS, Automation | |
|     | • Policy, Autonomous, TalentPool, CompanySettings, CSS | |
| 2.6 | Eliminate `DOMAIN_INSTRUCTIONS` class-attr (15) | (incluído em 2.5) |
| 2.7 | Backward compat tests (prompt diff < 50 chars) | 4h |
| 2.8 | Sensor blocking: `agent_lacks_universal_blocks` | 1h |
| 2.9 | Boy Scout cleanup any P2 found | (incluído em 2.5) |

### Acceptance criteria
- [ ] 1 source of truth: `PromptComposer` (não mais 18)
- [ ] 0 `DOMAIN_INSTRUCTIONS` class-attr
- [ ] All 15 agents migrated (verified runtime)
- [ ] Backward compat: smoke E2E em 5 agents críticos sem regressão
- [ ] Sensor blocking ratchet ativo
- [ ] TDD coverage 100% on PromptComposer

### Hot file coordination (REGRA 6)
- 15 agent files tocados em 2 semanas
- Antes de cada agent: `git log --since="6 hours" -- <file>`
- Se outro agent commit: PARAR e coordenar com Paulo

### Risks
| Risk | Mitigation |
|---|---|
| Regressão em comportamento LLM | Backward compat tests + smoke E2E manual em 5 agents críticos |
| Hot file collisions | REGRA 6 check + Paulo coordenação |
| Performance overhead PromptComposer | Benchmark P95 < 5ms (já mockável) |

---

## Sprint 3 — Tool Canonical (~31h, 1.5 semanas)

### Objetivo
2 ToolDefinition classes → 1 (canonical: `lia_agents_core`). Tool schemas só user-facing. Runtime context wrapper.

### Skills
- `/canonical-fix`
- `/production-quality:modules:ai-architecture`
- `/tdd-workflow`

### Tasks

| # | Task | Esforço |
|---|---|---|
| 3.1 | Design `RuntimeContext` + `with_runtime_context` decorator | 2h |
| 3.2 | Implementação + tests TDD | 4h |
| 3.3 | Wire middleware: `_current_runtime_ctx.set(...)` | 2h |
| 3.4 | Migrate 20 tools `app/tools/registry.py` → `lia_agents_core` | 8h |
| 3.5 | Field rename: `parameters_schema` → `parameters` | (incluído em 3.4) |
| 3.6 | Migrate 40 handlers para `@with_runtime_context` | 12h |
| 3.7 | Sensor `check_no_tenant_in_tool_schemas` warn → block | 1h |
| 3.8 | Sensor NEW: `check_tool_handlers_use_runtime_context` | 1h |
| 3.9 | Deprecate + delete `app/tools/registry.py:ToolDefinition` | 1h |

### Acceptance criteria
- [ ] 1 ToolDefinition class (not 2)
- [ ] 0 tenant IDs em tool schemas (sensor blocking)
- [ ] 100% handlers usando runtime context decorator
- [ ] Tool schemas só user-facing params
- [ ] 0 regression em behavior dos tools

### Risks
| Risk | Mitigation |
|---|---|
| Tool handlers que dependem de `kwargs.get("company_id")` quebram | Decorator preserva backward compat — fallback para kwargs se decorator não setou |
| 60+ files tocados | Batch por domain, hot file check |

---

## Sprint 4 — Defense in Depth (~25h, 2 semanas)

### Objetivo
Postgres RLS + logging consolidado + test infra repair.

### Skills
- `/security-review`
- `/production-quality:modules:backend-quality`
- `/production-quality:modules:compliance-risk`

### Tasks

| # | Task | Esforço |
|---|---|---|
| 4.1 | Alembic migration: enable RLS em 10 tabelas | 4h |
| 4.2 | Update `get_tenant_db`: `SET LOCAL app.current_tenant` | 2h |
| 4.3 | Tests RLS coverage (10 tabelas × 2 tests = 20) | 8h |
| 4.4 | Bypass pattern para admin paths (audited) | 3h |
| 4.5 | Sensor `check_table_has_rls_policy` warn-only | 2h |
| 4.6 | Logging consolidado em `app/shared/logging/` | 4h |
| 4.7 | Fix 32 broken integration tests (auth fixture) | 8h |
| 4.8 | YAML schema validation (jsonschema) | 3h |
| 4.9 | Smoke E2E staging (CRITICAL) | 4h |
| 4.10 | Rollback plan + docs | 2h |

### Acceptance criteria
- [ ] 10 tabelas críticas com RLS ativo
- [ ] 0 cross-tenant data leaks em smoke test
- [ ] Bypass admin auditado em `audit_logs`
- [ ] 32 broken tests now green
- [ ] Sensor `check_table_has_rls_policy` warn-only initially
- [ ] Logging via single module
- [ ] YAML files validados em CI

---

## Branch Strategy (REGRA 2/3)

```
main (não tocar)
└── feat/sprint-b-canonical (atual — fixes táticos)
└── feat/canonical-refactor-q2 (NOVA — refator estrutural)
    └── sprint-1-protected-attributes
    └── sprint-2-prompt-composer
    └── sprint-3-tool-unified
    └── sprint-4-rls-defense
```

Cada Sprint:
- Sub-branch derivada de `feat/canonical-refactor-q2`
- Após Sprint completo + sensor blocking + smoke E2E: merge em parent branch
- Paulo push manual após approval (REGRA 4)
- 0 push pelo agente

---

## Compliance Gates por Sprint

| Gate | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|---|---|---|---|---|---|
| Multi-tenancy (JWT) | N/A | N/A | ✅ | ✅ | ✅ (RLS) |
| LGPD Art. 5º + 11 | N/A | ✅ (P0) | ✅ | ✅ | ✅ |
| ADR-001 (Repo Pattern) | N/A | N/A | N/A | ✅ | ✅ |
| ADR-006 (No PII logs) | N/A | ✅ | N/A | N/A | ✅ |
| ADR-026 (canonical writes) | N/A | N/A | N/A | N/A | N/A |
| Fairness audit | N/A | ✅ | ✅ | N/A | ✅ |
| Audit log | N/A | ✅ | ✅ | ✅ | ✅ |
| Sensor blocking | warn | block | block | block | block |
| Tests TDD coverage | N/A | 100% | 100% | 100% | 80%+ |

---

## Verificação E2E (cumulativa)

### Pós-Sprint 1 (LGPD)
1. Backend startup zero warnings sobre YAML
2. FairnessGuard bloqueia "preferencialmente homem" em JD
3. EEOC adverse impact funcional

### Pós-Sprint 2 (Prompts)
4. Wizard chat "criar vaga" — ZERO menção a "ID empresa" (regression test)
5. Adicionar agent novo + verify TENANT_ISOLATION presente automaticamente
6. Sensor `agent_lacks_universal_blocks` bloqueia agent sem blocks

### Pós-Sprint 3 (Tools)
7. Tool schemas dump: 0 tenant IDs em qualquer tool
8. Handler test: company_id auto-injected via decorator
9. Sensor `check_no_tenant_in_tool_schemas --block` exit 0

### Pós-Sprint 4 (RLS)
10. Empresa A query empresa B's job_vacancies → 0 rows (RLS bloqueia)
11. Admin bypass logged em `audit_logs`
12. 32 tests pre-broken now passing
13. Smoke E2E staging completo: criar vaga → triagem → hire

---

## Risks (cumulativo)

| Risk | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Regressão LLM behavior | Média | Alto | Backward compat tests + smoke E2E |
| Hot file conflicts agents paralelos | Baixa | Médio | REGRA 6 check + branching strategy |
| RLS performance degradation | Baixa | Médio | Benchmark P95 + index optimization |
| `protected_attributes.yaml` flagging vagas existentes | Alta | Baixo | Audit + remediation plan separado |
| Test infra fixes | Média | Médio | Sprint 4 dedicado |

---

## Success Metrics (final)

Após Sprint 4 complete:

- [ ] **Prompt sources of truth**: 18 → 1
- [ ] **ToolDefinition classes**: 2 → 1
- [ ] **Tool schemas com tenant IDs**: 145 → 0 (sensor blocking)
- [ ] **DOMAIN_INSTRUCTIONS class-attr**: 15 → 0
- [ ] **Postgres RLS**: 0 → 10 tabelas críticas
- [ ] **Sensors blocking**: 6 (era 0)
- [ ] **Tests passing**: 70+ → 100+ (Sprint 4 fix 32 broken)
- [ ] **LGPD compliance**: fail-open → fail-closed
- [ ] **Backend `--reload`**: ✅ ativo (já feito)
- [ ] **ADRs novas**: 4 (028, 029, 030, 031)

---

## Skills invocadas explicitamente

Por Sprint:

| Skill | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|---|---|---|---|---|---|
| `/canonical-fix` | ✅ | | ✅ | ✅ | |
| `/tlc-spec-driven` | ✅ | | | | |
| `/harness-engineering` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/tdd-workflow` | | ✅ | ✅ | ✅ | ✅ |
| `/create-canonical-agent` | | | ✅ | | |
| `/design-patterns` | | | ✅ | | |
| `/security-review` | | ✅ | | | ✅ |
| `/production-quality:modules:compliance-risk` | | ✅ | | | ✅ |
| `/production-quality:modules:ai-architecture` | | | | ✅ | |
| `/production-quality:modules:backend-quality` | | | | | ✅ |
| `/production-quality:modules:canonical-standards` | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Approval gate

Antes de iniciar Sprint 1:

- [ ] Paulo revisou ADR-028
- [ ] Paulo revisou ADR-029
- [ ] Paulo revisou ADR-030
- [ ] Paulo revisou ADR-031 (P0)
- [ ] Paulo revisou esta SPEC
- [ ] Paulo aprovou esforço total ~104h Q2
- [ ] Branch `feat/canonical-refactor-q2` criada

---

## Referências

- Bug origem: sessão Sprint B+ wizard "ID empresa" (2026-05-06)
- ADRs novas: 028, 029, 030, 031
- ADRs existentes: 001 (Repo Pattern), 006 (No PII), 025 (Legacy Decom), 026 (canonical writes), 027 (legacy /api/wsi)
- CLAUDE.md global + project + memories
- Skills: canonical-fix, tlc-spec-driven, harness-engineering, tdd-workflow, create-canonical-agent

---

## Status (atualizar conforme execução)

- [x] Sprint 0 governance — em progresso (esta sessão)
- [ ] Sprint 1 — Stabilize + LGPD (P0)
- [ ] Sprint 2 — Prompt Canonical
- [ ] Sprint 3 — Tool Canonical
- [ ] Sprint 4 — Defense in Depth
