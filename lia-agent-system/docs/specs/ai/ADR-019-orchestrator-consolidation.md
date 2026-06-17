# ADR-019 — Orchestrator V1→V2 Consolidation (LIA-D06 Cleanup)

**Status**: Implementation Complete — Awaiting Production Validation (2026-04-26)
**Date**: 2026-04-26
**Owner**: Backend lead (a designar) + Paulo (founder/produto)
**Related**:
- `Documents/Python/ORCHESTRATOR_MIGRATION_MASTER_PLAN.md` (plano mestre)
- `Documents/Python/ORCHESTRATOR_MIGRATION_SPRINT_I.md`
- `Documents/Python/MIGRATION_REGRESSION_BASELINE.md`
- `docs/migrations/orchestrator-v1-references-2026-04-26.md` (canonical inventory)

---

## Context

O `lia-agent-system` mantém dois orchestrators coexistindo desde refatoração arquitetural recente:

- **V1** (`app/orchestrator/orchestrator.py`, 668 LoC) — marcado `LIA-D06: DEPRECATED` desde a v1.X. Ainda serve:
  - 5 endpoints públicos via `app/api/orchestrator_routes.py` (`/api/orchestrator/*`)
  - Fallback `_invoke_orchestrator_legacy()` em `app/api/v1/chat.py:92` (chamado em chat.py:712)
  - Phase 3 fallback em `app/api/v1/lia_assistant/insights.py:380-400`
  - Bridge em `app/domains/communication/services/teams_orchestrator_bridge.py:92` (Microsoft Teams) ⚠️ descoberto em Sprint I
  - Phase 2 do V2 delega ao V1 para roteamento de domínio + ReAct

- **V2** (`app/orchestrator/main_orchestrator.py`, 1532 LoC) — façade orquestradora moderna:
  - 95% lógica própria (FairnessGuard, SecurityPatterns, PendingAction, ActionExecutor, Agentic Loop)
  - 5% delega ao V1 apenas em Phase 2 (60 linhas em `_route_with_tenant_llm`)

### Inventário canônico (Sprint I — AST-based, 2026-04-26)

- **2.559 arquivos Python escaneados**
- **14 arquivos** com referências a V1
- **6 importers estáticos** (3 produção + 3 testes)
- **5 callers de produção** (não 3 como inferido na auditoria inicial — Teams bridge novo)
- **44 method calls** observáveis (7 produção + 4 V1-internal + 33 tests)
- **0 imports dinâmicos** (`importlib.import_module`, `__import__`) — confirmado via AST

### Custos da coexistência

| Custo | Sintoma observável |
|-------|--------------------|
| Bugs ocultos | Comportamento estranho difícil de rastrear (V1 ou V2?) |
| Feature drift | Devs novos colocam lógica no V1 (deprecated) por engano |
| Performance | Toda mensagem em Phase 2 passa por 2 camadas de orquestração |
| Risk surface | Mudança no V1 afeta produção sem avisar (sem testes próprios pré-Sprint I) |

---

## Decision

**Consolidar em V2 (`MainOrchestrator`) como o único orchestrator do `lia-agent-system`**, eliminando V1 ao longo de 5 sprints (4-6 semanas).

### Princípios da consolidação

1. **Código é a fonte da verdade** — qualquer divergência doc × código → atualizar doc
2. **Zero downtime** — preservar 100% do comportamento observável dos flows de produção
3. **Reversibilidade** — cada Sprint deve ter plano de rollback documentado
4. **Multi-tenancy P0** — isolation entre `company_id` deve ser preservada (LGPD, P0 não-negociável)
5. **Sensor before guide** (harness-engineering) — testes existem ANTES de mudar lógica de orquestração

### Estrutura final pretendida

```
app/orchestrator/
├── __init__.py                         (exporta apenas MainOrchestrator)
├── main_orchestrator.py                (V2 — único orchestrator)
├── cascaded_router.py                  (8-tier routing — preservado)
├── chat_adapter.py                     (REST/WS/SSE → MainOrchestrator)
├── action_executor/                    (preservado)
├── action_handlers/                    (preservado)
├── heuristics/                         🆕 (Sprint II.3)
│   ├── technical_response_detector.py  [sensor]
│   └── cv_matching_detector.py         [sensor]
└── services/                           🆕 (Sprint II)
    ├── plan_orchestration_service.py   [guide] — extraído de execute_plan
    ├── fallback_react_service.py       [guide] — extraído de _handle_directly (LIA-A04)
    └── policy_gate_service.py          [guide] — extraído de policy validation
```

`app/orchestrator/orchestrator.py` deletado em Sprint V.

### 5 Sprints

| Sprint | Foco | Duração | Risco |
|--------|------|---------|-------|
| **I** | Discovery + Characterization Tests (rede de segurança) | 1 sem | 🟢 Baixo |
| **II** | Extração de 8 responsabilidades em services dedicados | 2 sem | 🟡 Médio |
| **III** | Migração do V2 para usar os novos services | 1 sem | 🟡 Médio |
| **IV** | Migração dos 5 callers diretos do V1 | 1 sem | 🔴 Alto |
| **V** | Delete V1 + cleanup final | 1-2 dias | 🟢 Baixo |

Detalhes: ver `Documents/Python/ORCHESTRATOR_MIGRATION_MASTER_PLAN.md` Anexo A-E.

---

## Consequences

### Positivas
- **Single source of truth** para orquestração (elimina ambiguidade V1 vs V2)
- **Performance**: 1 camada de orquestração em vez de 2 em Phase 2
- **Observabilidade clara**: spans OTLP de uma única classe
- **Onboarding mais simples**: dev novo lê apenas V2
- **Testabilidade**: services extraídos têm interfaces dedicadas (Sprint II)

### Negativas
- **Esforço**: 4-6 semanas de trabalho focado de backend lead
- **Risco controlado**: 4 flows ALTO RISCO precisam canary 1 semana cada
- **Branch strategy**: 5 branches separadas, 1 ADR por extração no Sprint II

### Neutras
- **Onboarding flow não afetado** — `OnboardingOrchestrator` em `app/services/` é FSM separada (verificado em Sprint I)
- **WSI/Sourcing/Kanban/Wizard não afetados** — usam ReAct agents diretos (verificado em Sprint I)

---

## Alternatives Considered

### Alt 1: Reescrever V2 do zero
**Descartado**. Custo astronômico (1532 LoC + integração com 4 phases). Risco operacional de 1-2 meses. V2 funciona bem em 95% do código — ROI do rewrite é negativo.

### Alt 2: Manter V1 + V2 forever (don't migrate)
**Descartado**. Custos da coexistência crescem com tempo (drift, bugs ocultos, performance). Cada feature nova aumenta risco de ir para V1 por engano.

### Alt 3: Big-bang migration (delete V1 hoje)
**Descartado**. Sem characterization tests (Sprint I), seria cego. 5 callers de produção quebrariam. Estimativa de regressão: 30-40% (alto demais para produção).

### Alt 4 (escolhida): Migration multi-sprint com testes-first
**Escolhida**. Combina:
- Rede de segurança via characterization tests (Sprint I)
- Extração incremental com cada PR isolado (Sprint II)
- Canary com auto-rollback (Sprint III)
- Migração de callers com decisão de produto (Sprint IV)
- Delete final com confiança (Sprint V)

---

## Implementation Notes

### Skills aplicadas

| Skill | Como aplica |
|-------|-------------|
| **production-quality** | P0/P1/P2 em cada PR. P0 (multi-tenancy/LGPD/security) bloqueia merge. |
| **canonical-standards** | Cada extração vai para path canônico. Não criar shims novos. |
| **harness-engineering** | `[guide]` (decide/roteia) vs `[sensor]` (observa/loga). Computacional > inferencial. |
| **feature-impact** | Cada Sprint: % tráfego em risco, plano de rollback, canary stage. |
| **engineering:code-review** | Boy Scout Rule: P2 issues no mesmo PR. P0/P1 fora de escopo reportados. |

### Status Sprint I (em andamento — 2026-04-26)

- [x] Branch `feat/orch-migration-sprint-I` criada
- [x] Tarefa A: Inventário fino (grep + AST + reconciliação canônica) — 14 arquivos identificados
- [x] Tarefa C: 50/52 characterization tests passando (commit `ae2d446d3`)
- [ ] Tarefa B: Baseline metrics de produção — pendente acesso Sentry/Datadog
- [ ] Tarefa D: OTLP instrumentation em V1 + V2 — em construção
- [ ] Tarefa E: `MIGRATION_REGRESSION_BASELINE.md` preenchido — em construção
- [ ] Tarefa F: Este ADR mergeado

### Critérios de sucesso (Definition of Done global)

- [ ] 0 importers diretos de `app.orchestrator.orchestrator` (apenas re-export `__init__.py`)
- [ ] 0 chamadas a `Orchestrator()` factory (apenas `get_main_orchestrator()`)
- [ ] Characterization tests passam 100% durante toda a migração
- [ ] Cobertura E2E para 4+ flows ALTO RISCO ≥ 90%
- [ ] OpenTelemetry traces de cada Phase do V2 visíveis em staging
- [ ] Latência p95 do MainOrchestrator não degrada > 10% pós-migração
- [ ] Este ADR-019 promovido a "Accepted" + selo `Implemented` ao final de Sprint V

---

## Acceptance Criteria — Promotion Gate (Proposed → Accepted)

Este ADR está em status **Proposed** durante Sprints I-IV. Promove a **Accepted** apenas quando TODOS os critérios abaixo estiverem verdes:

### Gates obrigatórios (P0)

1. **Characterization tests 100% pass rate**
   - 50+ testes em `tests/characterization/` passando 3 runs consecutivas (zero flake)
   - Cobertura dos 12 métodos V1 listados em Anexo H do MASTER_PLAN
   - Verificação: `pytest tests/characterization/ --no-cov` retorna 0 failures

2. **Multi-tenancy isolation preservada**
   - Zero vazamento de `company_id` entre tenants em integration tests
   - Audit log mostra `tenant.company_id` em 100% dos eventos pós-migração
   - Property test em produção: 0 violações em 1 semana de canary

3. **LGPD compliance preservada**
   - FairnessGuard ativo em 100% dos prompts de ranking (Sprint III canary)
   - Zero atributos protegidos em spans OTLP (validado via grep diário em staging)
   - Audit trail completo: nenhum drop de evento de compliance

### Gates de qualidade (P1)

4. **Services extraídos com cobertura ≥ 90%**
   - `PlanOrchestrationService`, `FallbackReActService`, `PolicyGateService`
   - Cada um com mínimo 8 unit tests + 2 integration tests
   - Coverage report: ≥ 90% lines, ≥ 80% branches

5. **Canary 100% estável por 1 semana**
   - Sprint III: stages 5% → 25% → 50% → 100% sem rollback automático
   - Após 100%: 7 dias consecutivos sem alertas críticos
   - Métricas observadas: error rate, latência p95, token usage por tenant

6. **Latência preserved**
   - p95 do `MainOrchestrator.process()` não degrada > 10% vs baseline V1
   - Comparação documentada em `docs/migrations/latency-comparison-pre-post.md`
   - Baseline em `MIGRATION_REGRESSION_BASELINE.md` Section 2

### Gates operacionais (P2)

7. **Log review limpo** — ✅ **RESOLVIDO** (Task #861, 2026-04-26)
   - Zero CRITICAL alerts relacionados a "V1/V2 misrouting" em staging por 7 dias
   - Zero "deprecated path used in new code" warnings em CI
   - **N-07 (Wizard observability gap) fechada**: cada nó do `JobCreationGraph`
     emite span `wizard.job_creation.<stage>` via decorador
     `@wizard_traced_node` em `app/shared/observability/span_validation.py`.
     `agent_chat_ws._get_agent` agora aceita `company_id`/`session_id`/`user_id`
     como kwargs e emite span `wizard.agent_chat.get_agent` em todos os 3
     call-sites (WS resume, WS dispatch, HTTP fallback).
     Cobertura: `tests/observability/test_wizard_spans.py` (7 testes) +
     `tests/ci/test_wizard_span_attributes.py` (15 testes — gate AST que
     também verifica que TODOS os call-sites de `_get_agent(...)` propagam
     os kwargs de tenant + verificação runtime dos spans emitidos).
   - **Nota sobre `JOB_CREATION_EXIT` / `JOB_CREATION_ERROR`**: as constantes
     existem em `WizardSpans` mas hoje **não emitem spans separados**;
     sucesso/falha é codificado no campo `status` do mesmo span entry/resume
     (via `finish_span(status="ok"|"error")`). Constantes ficam reservadas
     para uma fase futura (e.g. telemetria de rollback) que crie spans
     dedicados.

8. **OTLP traces visíveis** — ✅ **RESOLVIDO** (Task #861, 2026-04-26)
   - Spans `orchestrator.v2.*` aparecem em Honeycomb/Datadog
   - Atributos obrigatórios (`tenant.company_id`, etc.) presentes em 100% dos spans
   - **N-08 (`validate_span_attributes()` ausente) fechada**: helper publicado em
     `app/shared/observability/span_validation.py`, com 19 testes unitários
     em `tests/observability/test_validate_span_attributes.py` cobrindo:
     happy-path, missing key, valor `None`/string vazia, sentinel "tenant zero"
     (`"0"`/`0`/`"0.0"`/`"None"`/`"null"`), `raise_on_missing=True`, atributos
     extras, atributo proibido por LGPD, mapping aceito sem objeto Span,
     attribute mapping puro, lista `required` customizada (orquestrador), e
     detecção tokenizada case-insensitive (impede falso-positivo `traceback`).
     CI gate em `tests/ci/test_wizard_span_attributes.py` rejeita PRs que
     remover o decorator de qualquer nó ou regredirem o sinal `_get_agent`.

### Sign-off necessário

Para promoção a **Accepted**:
- ✅ Backend lead aprova items 1-6 com evidências (links a dashboards/PRs)
- ✅ Paulo (founder/produto) aprova items 7-8 com sign-off explícito
- ✅ ADR atualizado com data de promoção + commit hash de Sprint III final

### Critérios para rollback completo (abort migration)

Se QUALQUER item abaixo ocorrer durante Sprints III-V, abortar e reverter para status quo:
- Comportamento crítico do V1 não pode ser preservado em V2
- Compliance LGPD em risco (regressão em audit log ou multi-tenancy)
- Stakeholder externo bloqueia (cliente reporta breakage)
- Latência p95 ≥ +20% durante 24h consecutivas

---

## References

- `app/orchestrator/orchestrator.py` (V1 atual, 668 LoC)
- `app/orchestrator/main_orchestrator.py` (V2 atual, 1532 LoC)
- `app/api/orchestrator_routes.py` (5 endpoints públicos legados)
- `tests/characterization/` (rede de segurança Sprint I)
- `tools/migration/ast_orchestrator_inventory.py` (validação canônica)

---

**Histórico de mudanças deste ADR**:
- 2026-04-26 — v1 inicial (Sprint I-F)
- 2026-04-26 — Task #861: N-07 (wizard observability gap) e
  N-08 (`validate_span_attributes()` ausente) marcados como **RESOLVIDO**.
  Itens 7 e 8 do Promotion Gate (P2) atualizados com referência aos
  testes e ao decorador `@wizard_traced_node`.
- _A próxima atualização ocorrerá ao final do Sprint III (canary 100%)._
