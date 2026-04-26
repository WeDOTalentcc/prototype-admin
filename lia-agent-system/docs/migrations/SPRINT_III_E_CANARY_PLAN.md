# Sprint III.E — Canary Rollout Plan
## V1 → V2 Service-based Migration via Feature Flags

> **Standalone document**. Pode ser executado lendo APENAS este arquivo +  
> [`MIGRATION_REGRESSION_BASELINE.md`](./MIGRATION_REGRESSION_BASELINE.md)  
> para contexto de produção. Para visão geral da migração, ver  
> [`ORCHESTRATOR_MIGRATION_MASTER_PLAN.md`](./ORCHESTRATOR_MIGRATION_MASTER_PLAN.md).

**Sprint**: III.E (último sub-sprint de Sprint III)  
**Pré-requisito**: Sprint III.A/B/C/D ✅ + BASELINE Section 2 preenchida (Paulo)  
**Status atual**: ⏳ AGUARDANDO baseline metrics de produção  
**Risco**: 🔴 ALTO — afeta 4 flows ALTO RISCO em produção

---

## 1. Objetivo

Habilitar progressivamente os feature flags do Sprint III.B (PlanService) e III.D
(FallbackReAct) em produção, monitorando regressões via OTLP traces (Sprint III.C).

**Default atual**: ambos os flags estão **OFF** (V1 delegation continua).
Sprint III.E faz o rollout controlado por estágios com critérios de auto-rollback.

---

## 2. Pré-requisitos (DEVE estar 100% antes de iniciar)

### 2.1 — BASELINE.md Section 2 preenchida

`docs/migrations/MIGRATION_REGRESSION_BASELINE.md` — preencher Seção 2.x com
métricas reais de staging/produção (últimos 7 dias):

- [ ] **2.1 Latência por flow** (p50/p95/p99)
  - Chat REST, Chat WS, Chat SSE
  - Orchestrated Job/Talent Chat
  - Wizard Job Graph
  - Legacy `/api/orchestrator/process`

- [ ] **2.2 Error rate por flow** (% requests retornando 4xx/5xx)

- [ ] **2.3 Throughput por flow** (RPS médio + peak)

- [ ] **2.4 Token usage top 10 tenants** (tokens/dia)

**Como coletar**: dashboard Sentry, Datadog ou Honeycomb. Período: últimos 7d
em horário de pico. Owner: **Paulo** (precisa acesso a dashboards prod).

### 2.2 — Observabilidade ativa em staging

- [ ] `OTEL_TRACES_ENABLED=true` em staging
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` configurado (ex: `http://jaeger:4318`)
- [ ] Spans aparecem em Jaeger/Honeycomb com nomes canônicos:
  - `orchestrator.v2.process`
  - `orchestrator.v2.phase_2_via_orchestrator`
  - `orchestrator.v2.route_with_tenant_llm`
  - `orchestrator.v2.services.plan.detect`
  - `orchestrator.v2.services.fallback_react.handle`
  - `orchestrator.v1.process_request`

### 2.3 — Alertas em prod

- [ ] PagerDuty/Slack alerts configurados:
  - Error rate > baseline + 1% por 5 min → **auto-rollback**
  - Latência p95 > baseline + 20% por 10 min → **auto-rollback**
  - Audit log drop rate > 0.1% → **manual review**

### 2.4 — DI integração V2 com services

- [ ] Confirmar que `MainOrchestrator` é instanciado com services injetados:

```python
# Em app/api/orchestrator_routes.py ou onde V2 é construído:
from app.orchestrator.services.plan_orchestration_service import (
    PlanOrchestrationService,
)
from app.orchestrator.services.fallback_react_service import FallbackReActService

main_orch = MainOrchestrator(
    orchestrator=v1_orch,  # backward compat
    plan_service=PlanOrchestrationService(plan_detector, plan_executor, ws_manager),
    fallback_react_service=FallbackReActService(llm_service=v1_orch.llm_service),
    # policy_gate_service=...,  # Sprint III.D futuro
)
```

**Atualmente**: V2 é instanciado via `get_main_orchestrator()` em
`app/api/orchestrator_routes.py`. Esta função precisa ser atualizada para
injetar os services. **TODO antes de Sprint III.E**.

---

## 3. Plano de Rollout (4 estágios, ~7 dias)

### Estágio 1: 5% — Day 1

**Ativar**: `LIA_V2_USE_PLAN_SERVICE=true` em 5% dos pods/instâncias

**Métricas a observar (24h)**:
- Span `orchestrator.v2.services.plan.detect` aparece com count > 0
- Error rate dos 5% pods ≤ baseline + 0.5%
- Latência p95 ≤ baseline + 10%
- Audit log integrity 100%

**Decision gate Day 2**:
- ✅ Verde → avançar para 25%
- ⚠️ Amarelo → pausar 24h, investigar
- 🔴 Vermelho → rollback automático

### Estágio 2: 25% — Day 2-3

Ativar PlanService em 25% dos pods. Mesmas métricas.

### Estágio 3: 50% — Day 3-4

Ativar PlanService em 50% dos pods. Adicionar `LIA_V2_USE_FALLBACK_REACT=true`
em **5%** (não 50% — fallback é late-intercept e tem maior surface area de risco).

### Estágio 4: 100% PlanService + 25% FallbackReAct — Day 4-5

PlanService em 100%. FallbackReAct em 25%.

### Estágio 5: 100% ambos — Day 5-7

Ambos em 100%. Monitorar 48h. Se estável → declarar Sprint III completo.

---

## 4. Critérios de Auto-Rollback

Auto-rollback (sem aprovação humana) dispara se:

| Métrica | Limiar | Janela |
|---------|--------|--------|
| Error rate | ≥ baseline + 1% | 5 min consecutivos |
| Latência p95 | ≥ baseline + 20% | 10 min consecutivos |
| Audit log drop | ≥ 0.1% | qualquer |
| Multi-tenant violation | qualquer | imediato |
| LGPD attribute leak (via OTLP) | qualquer | imediato |

**Mecanismo de rollback**:
```bash
# Setar env vars para OFF em todos os pods
kubectl set env deploy/lia-agent LIA_V2_USE_PLAN_SERVICE=false
kubectl set env deploy/lia-agent LIA_V2_USE_FALLBACK_REACT=false
# Restart rolling para aplicar
kubectl rollout restart deploy/lia-agent
```

Ou via feature flag service externo (LaunchDarkly, etc.) — preferível.

---

## 5. Critérios de Manual Review (não bloqueante)

Pause + investigação manual se:

- Error rate ≥ baseline + 0.5%
- Latência p95 ≥ baseline + 10%
- Token usage / tenant ≥ baseline + 5%
- Spans com atributos faltantes (tenant.company_id ausente)

---

## 6. Critérios de Sucesso (DoD do Sprint III.E)

Sprint III.E é **declarado completo** quando:

- [ ] Estágio 5 (100% ambos os flags) estável por **7 dias consecutivos**
- [ ] Zero CRITICAL alerts relacionados aos services
- [ ] Latência p95 do MainOrchestrator não degradou > 10% vs BASELINE
- [ ] Comparação latência ANTES/DEPOIS arquivada em
      `docs/migrations/latency-comparison-pre-post-sprint-iii.md`
- [ ] ADR-019 promovido a status **Accepted**

---

## 7. Riscos identificados + mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Plan detection falso positivo causa loop | Baixa | Médio | `_try_plan_via_service` tem `try/except` retornando None → V1 fallback |
| FallbackReAct dobra latência | Média | Baixo | Late-intercept apenas para technical responses (subset pequeno) |
| Span attributes vazam PII | Baixa | 🔴 ALTO | Pre-commit hook `otlp_lgpd_check.py` previne |
| Multi-tenant cross-talk | Baixa | 🔴 ALTO | Tests cobrem isolation; tenant_id propagation auditado |
| V2 services criados duplicados em concurrent | Eliminada | — | Lazy init resolvido (commit b4e3d20c1) |

---

## 8. Rollback completo (abort migration)

Critérios para abortar Sprint III e voltar para status quo:

- Comportamento crítico do V1 não pode ser preservado em V2
- Compliance LGPD em risco (regressão em audit log ou multi-tenancy)
- Stakeholder externo bloqueia (cliente reporta breakage)
- Latência p95 ≥ +20% durante 24h consecutivas em qualquer estágio

**Mecanismo**: revert dos commits Sprint III.A-D no git, redeploy.

---

## 9. Histórico de execução (preencher durante rollout)

| Estágio | Data início | Data fim | Status | Notas |
|---------|-------------|----------|--------|-------|
| 1 (5%) | _TBD_ | — | — | — |
| 2 (25%) | _TBD_ | — | — | — |
| 3 (50%) | _TBD_ | — | — | — |
| 4 (100/25%) | _TBD_ | — | — | — |
| 5 (100%) | _TBD_ | — | — | — |

---

## 10. Sign-off

Sprint III.E só pode iniciar após sign-off explícito de:

- [ ] **Backend lead**: Pré-requisitos 2.x verificados
- [ ] **Paulo (founder/produto)**: BASELINE Section 2 preenchida
- [ ] **DevOps**: Alertas + auto-rollback configurados

---

**Status atual deste documento**: 📋 PLANO INICIAL  
**Última atualização**: 2026-04-26  
**Próxima ação**: Paulo coleta BASELINE Section 2 metrics
