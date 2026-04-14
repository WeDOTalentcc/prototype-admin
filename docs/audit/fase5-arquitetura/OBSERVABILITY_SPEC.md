# OBSERVABILITY_SPEC.md — Observability Specification
**Protocolo:** P26  
**Data:** 2026-04-14  
**Arquiteto:** Claude Opus 4.6  
**Baseado em:** P21 (TARGET_ARCHITECTURE), PX03 (INTEGRATIONS), PX06 (DEVOPS_SECURITY)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** P21  
**Alimenta:** P31

---

## GAP ANALYSIS: O QUE EXISTE vs O QUE FALTA

### O que JA EXISTE (surpreendentemente rico)

| Componente | Arquivo | Status | Qualidade |
|-----------|---------|--------|-----------|
| **OTEL Tracing** | `app/shared/tracing.py` | IMPLEMENTADO | ALTA — 105 refs, spans em router, RAG, embedding, HITL, Celery, WS, ReAct |
| **LightweightTracer** (fallback) | `app/shared/tracing.py` | IMPLEMENTADO | BOA — zero deps, compativel com OTEL |
| **Request ID Middleware** | `app/middleware/request_id.py` | IMPLEMENTADO | BOA — UUID por request, propagado em headers |
| **Structured Logging Middleware** | `app/core/logging_middleware.py` | IMPLEMENTADO | BOA — request_id, method, path, status, duration, company_id, tier |
| **JSON Formatter (prod)** | `app/core/logging_config.py` | IMPLEMENTADO | BOA — JSON em prod, human-readable em dev |
| **PII Masking em logs** | `app/shared/pii_masking.py` + `PIIMaskingFilter` | IMPLEMENTADO | BOA — CPF, email, telefone mascarados |
| **AuditCallback** (LangGraph) | `libs/audit/lia_audit/audit_callback.py` | IMPLEMENTADO | BOA — tool calls, tokens por agente |
| **Sentry** (Python + Frontend) | `app/core/sentry.py` + `@sentry/nextjs` | CONFIGURADO (DSN ausente) | BOA — PII scrubbing, graceful degradation |
| **Observability API** | `app/api/v1/observability.py` | IMPLEMENTADO | BOA — AI logs, data access, consent, incidents, bias audit |
| **Drift Detection** | `app/api/v1/drift.py` + `app/jobs/drift_job.py` | IMPLEMENTADO | MEDIA — Celery beat daily, latencia e qualidade |
| **Tenant Budget** | `app/orchestrator/tenant_budget.py` | IMPLEMENTADO | ALTA — Redis, per-request cost tracking |
| **Perf Metrics** | `app/orchestrator/main_orchestrator.py` | IMPLEMENTADO | MEDIA — in-memory dict, avg/p95 |
| **Flower** (Celery) | `docker-compose.yml` | CONFIGURADO | OK — porta 5555 |
| **Health endpoints** | 4 endpoints (`/health`, `/health/detailed`, `/health/langgraph`, `/rails/health`) | IMPLEMENTADO | BOA |

### O que FALTA

| Gap | Severidade | Detalhes |
|-----|-----------|----------|
| **OTEL_EXPORTER_OTLP_ENDPOINT vazio** | CRITICO | Tracing implementado mas nao exporta para nenhum backend |
| **SENTRY_DSN vazio** | CRITICO | Error tracking implementado mas nao envia para Sentry |
| **Sentry ausente no Rails** | ALTO | ats-api-copia nao tem Sentry |
| **Zero metricas Prometheus/OTEL** | ALTO | Prometheus removido, OTEL metrics nao implementado |
| **Zero alerting configurado** | ALTO | Nenhum alerta ativo em producao |
| **Dashboard inexistente** | MEDIO | Observability API existe mas sem UI |
| **Log aggregation ausente** | MEDIO | Logs vao para STDOUT, sem CloudLogging/ELK |
| **Perf metrics efemeros** | MEDIO | In-memory dict, perdem-se no restart |
| **Agent handoff tracing** | MEDIO | Router tracing existe mas handoff entre agentes nao e span explicito |
| **LangSmith desabilitado** | BAIXO | `LANGCHAIN_TRACING_V2=false` por default |

---

## 1. TRACING DISTRIBUIDO

### 1.1 Estado Atual (Sofisticado)

O `app/shared/tracing.py` ja implementa:

```
Cobertura de spans existente:
  CascadedRouter.route() → "router.route" (parent)
    ├── Tier 0: "router.tier0_memory_resolve"
    ├── Tier 1: "router.tier1_lru_cache"
    ├── Tier 2: "router.tier2_redis_cache"
    ├── Tier 3: "router.tier3_vector_cache"
    ├── Tier 4: "router.tier4_fast_router"
    ├── Tier 5: "router.tier5_llm_cascade"
    ├── Tier 6: "router.tier6_autonomous_react"
    └── Fallback: "router.fallback_clarification"

  RAGPipelineService.search() → phases:
    ├── "rag.query_analysis"
    ├── "rag.bm25_search"
    ├── "rag.semantic_search"
    ├── "rag.hybrid_blending"
    ├── "rag.reranking"
    └── "rag.llm_classification"

  EmbeddingService → "embedding.generate", "embedding.batch_generate"
  HITLService → "hitl.request_approval", "hitl.receive_approval"
  Celery tasks → "celery.task_start" (per task)
  DLQService → "dlq.push_failure"
  LearningLoop → "learning.process_feedback"
  WebSocket → "ws.agent_chat"
  ReAct loop → "react.act"
```

### 1.2 Spans Faltantes (Adicionar)

| Span | Parent | Atributos | Prioridade |
|------|--------|-----------|-----------|
| `agent.{domain}.process` | `router.route` | domain_id, agent_class, company_id | ALTO |
| `agent.handoff` | `agent.{source}` | source_agent, target_agent, context_preserved | ALTO |
| `llm.generate` | `agent.{domain}` | model, tokens_in, tokens_out, cost_usd, temperature | ALTO |
| `tool.{tool_name}` | `agent.{domain}` | tool_name, success, duration_ms, output_size | MEDIO |
| `fairness.check` | `agent.{domain}` | is_blocked, soft_warnings_count, categories | MEDIO |
| `calibration.load` | `agent.{domain}` | weights_loaded, tenant_id | BAIXO |
| `rabbitmq.publish` | request | exchange, routing_key, message_type | MEDIO |
| `rabbitmq.consume` | independente | queue, processing_time, success | MEDIO |

### 1.3 Schema de Trace Completo (Alvo)

```
HTTP Request (trace_id = UUID)
  └── "http.request" (span)
      ├── method, path, status_code, duration_ms, company_id, user_id
      └── "orchestrator.process" (span)
          ├── "fairness.pre_check" (span)
          │   └── is_blocked, warnings_count
          ├── "router.route" (span) [JA EXISTE]
          │   ├── tier_resolved, confidence, domain_id
          │   └── "router.tier{N}" (spans) [JA EXISTEM]
          ├── "agent.{domain}.process" (span) [NOVO]
          │   ├── agent_class, domain_id
          │   ├── "llm.generate" (span) [NOVO]
          │   │   └── model, tokens_in, tokens_out, cost_usd
          │   ├── "tool.{name}" (span) [NOVO]
          │   │   └── tool_name, success, duration_ms
          │   └── "fairness.post_check" (span) [NOVO]
          ├── "calibration.record" (span) [NOVO]
          └── "learning.extract" (span) [JA EXISTE]
```

### 1.4 Stack Recomendada

| Opcao | Custo | Complexidade | Recomendacao |
|-------|-------|-------------|-------------|
| **GCP Cloud Trace** | Incluido no GCP | BAIXA | RECOMENDADO para prod (ja no GCP) |
| **Jaeger** (self-hosted) | Free | MEDIA | BOM para staging |
| **Langfuse** (LLM-specific) | Free tier | MEDIA | COMPLEMENTAR para traces LLM |
| **LangSmith** | Pago | BAIXA (ja configurado) | COMPLEMENTAR (habilitar flag) |

**Recomendacao:** GCP Cloud Trace como primary (OTLP export) + Langfuse para traces LLM + LangSmith habilitado em staging.

---

## 2. METRICAS DE AGENTE

### 2.1 Metricas Operacionais (por agente, por hora)

| Metrica | Tipo | Labels | Fonte Atual | Gap |
|---------|------|--------|-------------|-----|
| `lia_agent_invocations_total` | Counter | agent_id, domain, status | perf_metrics (in-memory) | Persistir em OTEL metrics |
| `lia_agent_latency_seconds` | Histogram | agent_id, domain | perf_metrics (in-memory) | Persistir |
| `lia_agent_errors_total` | Counter | agent_id, error_type | Logs | Extrair de logs |
| `lia_llm_tokens_total` | Counter | model, direction (in/out) | TenantBudget (Redis) | JA EXISTE (Redis) |
| `lia_llm_cost_usd` | Counter | model, company_id | TenantBudget (Redis) | JA EXISTE |
| `lia_router_cache_hits_total` | Counter | tier | CascadedRouter | Parcial (in-memory) |
| `lia_tool_calls_total` | Counter | tool_name, status | AuditCallback | JA REGISTRA (logs) |
| `lia_ws_connections_active` | Gauge | company_id | WSManager | In-memory, perdem-se |

### 2.2 Metricas de Qualidade (por agente, diario)

| Metrica | Tipo | Fonte Atual | Gap |
|---------|------|-------------|-----|
| `lia_confidence_score` | Histogram | CascadedRouter | Parcial — registra tier, nao exporta |
| `lia_human_intervention_rate` | Gauge | CalibrationService (explicit_disagree / total) | CALCULA mas nao exporta |
| `lia_task_completion_rate` | Gauge | Nenhuma | NAO EXISTE — precisa definir |
| `lia_fairness_trigger_rate` | Gauge | FairnessGuard logs | Parcial — logs existem |
| `lia_acceptance_rate` | Gauge | CalibrationService | CALCULA (agreement_rate) |
| `lia_escalation_rate` | Gauge | HITL events | Parcial |

### 2.3 Metricas Comportamentais

| Metrica | Tipo | Fonte Atual | Gap |
|---------|------|-------------|-----|
| `lia_tool_distribution` | Histogram | AuditCallback | Registra mas nao agrega |
| `lia_intent_distribution` | Histogram | CascadedRouter | Registra per-request |
| `lia_conversation_length` | Histogram | ConversationMemory | NAO AGREGA |
| `lia_drift_score` | Gauge | drift_job.py | JA CALCULA (Celery beat) |

---

## 3. LOGGING ESTRUTURADO

### 3.1 Estado Atual (Bom)

```json
// Output do StructuredLoggingMiddleware:
{
  "timestamp": "2026-04-14T12:00:00Z",
  "level": "INFO",
  "logger": "lia.request",
  "message": "request",
  "request_id": "uuid",
  "method": "POST",
  "path": "/api/v1/chat/stream",
  "status_code": 200,
  "duration_ms": 1234.5,
  "company_id": "uuid",
  "user_id": "uuid",
  "tier": "agent"
}
```

**PII mascarado:** CPF → [CPF], email → [EMAIL], telefone → [PHONE]

### 3.2 Schema de Log Alvo (Adicionar campos)

```json
{
  "timestamp": "ISO-8601",
  "level": "INFO",
  "logger": "lia.agent",
  "message": "agent_action",
  "trace_id": "uuid",          // NOVO — correlacao com tracing
  "span_id": "uuid",           // NOVO
  "request_id": "uuid",
  "agent_id": "sourcing",
  "action": "tool_call",       // tool_call | llm_call | decision | error | handoff
  "input_summary": "buscar devs Python SP",  // Resumo sem PII
  "output_summary": "3 candidatos encontrados",
  "duration_ms": 456,
  "tokens": {"prompt": 1200, "completion": 350},
  "cost_usd": 0.004,
  "metadata": {
    "model_version": "claude-sonnet-4-6",
    "prompt_version": "sourcing_v2.0",
    "tenant_id": "uuid",
    "vacancy_id": "uuid",
    "tool_name": "search_candidates",
    "confidence": 0.87
  }
}
```

### 3.3 Log Aggregation

| Opcao | GCP Native? | Custo | Recomendacao |
|-------|------------|-------|-------------|
| **GCP Cloud Logging** | SIM | Incluido | RECOMENDADO — logs ja vao para STDOUT, Cloud Run captura automaticamente |
| **ELK Stack** | NAO | Alto (self-hosted) | NAO — over-engineering para o momento |
| **Datadog** | NAO | Pago | FUTURO — quando escala justificar |

---

## 4. ALERTING

### 4.1 Regras de Alerta

**CRITICAL (pagina imediata — PagerDuty/Slack):**

| Alerta | Condicao | Fonte | Acao |
|--------|---------|-------|------|
| ALT-C01 | Error rate > 10% em 5 min | StructuredLoggingMiddleware (status >= 500) | Verificar logs, possivel outage |
| ALT-C02 | Latencia P95 > 30s em 5 min | StructuredLoggingMiddleware (duration_ms) | Verificar LLM provider, Redis, DB |
| ALT-C03 | Agent loop > 10 tool calls sem resolucao | AuditCallback (tool_call count per trace) | CircuitBreaker deve atuar |
| ALT-C04 | Custo/hora > 3x media | TenantBudget (Redis) | Possivel abuse ou prompt injection |
| ALT-C05 | Health endpoint retorna != 200 | /api/v1/health | Uptime monitor externo |

**WARNING (notificacao — Slack/email):**

| Alerta | Condicao | Fonte |
|--------|---------|-------|
| ALT-W01 | Human intervention rate subindo > 5% em 7 dias | CalibrationService |
| ALT-W02 | Quality score caindo > 10% em 7 dias | Drift detection job |
| ALT-W03 | Novo tipo de erro nao categorizado | Log analysis |
| ALT-W04 | Fairness trigger rate > 2x baseline | FairnessGuard logs |
| ALT-W05 | Token budget tenant > 80% | TenantBudget (ja implementado) |
| ALT-W06 | Redis connection refused | Health check |
| ALT-W07 | RabbitMQ connection refused | Health check |

**INFO (dashboard):**

| Alerta | Condicao | Fonte |
|--------|---------|-------|
| ALT-I01 | Distribuicao de intents mudou > 20% | CascadedRouter stats |
| ALT-I02 | Rate limit provider proximo | LLM provider headers |
| ALT-I03 | Custo mensal projetado > budget | TenantBudget |

### 4.2 Implementacao

**Fase 1 (GCP native):** Cloud Monitoring alerting policies baseadas em Cloud Logging metrics.
**Fase 2 (quando escala):** Grafana Cloud ou Datadog.

---

## 5. DASHBOARDS

### 5.1 Dashboard Executivo (PM/Founder)

```
┌─────────────────────────────────────────────┐
│ WeDOTalent LIA — Painel Executivo           │
├──────────────┬──────────────┬───────────────┤
│ Recrutadores │ Interacoes   │ Satisfacao    │
│ Ativos: 12   │ Hoje: 340    │ 4.2/5         │
├──────────────┴──────────────┴───────────────┤
│ Task Completion Rate    ████████░░  82%      │
│ Escalation Rate         ██░░░░░░░░  15%      │
│ Fairness Score          █████████░  94%      │
├─────────────────────────────────────────────┤
│ Custo LLM (mes)  $245  │ Projecao: $310     │
│ Tempo economizado/rec   ~2h/dia              │
└─────────────────────────────────────────────┘
```

### 5.2 Dashboard Tecnico (Engenharia)

```
┌─────────────────────────────────────────────┐
│ LIA Agent Performance                        │
├──────────────┬──────────────┬───────────────┤
│ Requests/min │ Error Rate   │ P95 Latencia  │
│ 12.3         │ 1.2%         │ 4.2s          │
├──────────────┴──────────────┴───────────────┤
│ Por Agente:                                  │
│ Sourcing     ████████  p95=3.1s  err=0.8%   │
│ Wizard       ██████    p95=2.4s  err=0.5%   │
│ Pipeline     █████     p95=1.8s  err=1.1%   │
│ Communic.    ███       p95=1.2s  err=2.3%   │
│ Analytics    ██        p95=0.9s  err=0.3%   │
├─────────────────────────────────────────────┤
│ Router Tiers:                                │
│ T1 LRU:  45%  T2 Redis: 20%  T3 Vector: 8% │
│ T4 Fast: 15%  T5 LLM:   10%  T6 Auto:  2%  │
├─────────────────────────────────────────────┤
│ Custo por Agente (mes):                      │
│ Sourcing: $89  Pipeline: $45  Wizard: $38    │
│ Total: $245   Budget: $500   Usage: 49%      │
├─────────────────────────────────────────────┤
│ Alertas Ativos: 0 CRITICAL  2 WARNING        │
└─────────────────────────────────────────────┘
```

### 5.3 Implementacao de Dashboard

| Opcao | Custo | Tempo | Recomendacao |
|-------|-------|-------|-------------|
| **Frontend interno** (`/configuracoes/agent-quality`) | Free | M (3-5d) | RECOMENDADO — API `observability.py` ja existe |
| **Grafana Cloud** | Free tier | S (1-2d) | BOM para metricas OTEL |
| **GCP Monitoring dashboards** | Incluido | S (1d) | BOM para infra |
| **Langfuse dashboard** | Free tier | S (1d) | BOM para LLM traces |

**Recomendacao:** Combinar frontend interno (produto) + GCP Monitoring (infra) + Langfuse (LLM).

---

## 6. PLANO DE IMPLEMENTACAO (3 Sprints)

### Sprint 1: Ativar o que ja existe (3-5 dias)

| # | Tarefa | Esforco | Impacto |
|---|--------|---------|---------|
| 1 | Configurar `SENTRY_DSN` no Replit e GCP | S (30 min) | Error tracking ativo |
| 2 | Configurar `OTEL_EXPORTER_OTLP_ENDPOINT` para GCP Cloud Trace | S (1h) | Tracing exportando |
| 3 | Habilitar `LANGCHAIN_TRACING_V2=true` em staging | S (15 min) | LLM traces visiveis |
| 4 | Configurar GCP Cloud Logging (ja automatico com Cloud Run) | S (verificar) | Log aggregation |
| 5 | Criar alerting policies no GCP Monitoring (ALT-C01 a C05) | M (1d) | Alertas criticos ativos |
| 6 | Adicionar Sentry gem ao Rails Gemfile | S (30 min) | Error tracking Rails |

### Sprint 2: Expandir traces e metricas (5-7 dias)

| # | Tarefa | Esforco | Impacto |
|---|--------|---------|---------|
| 7 | Adicionar spans `agent.{domain}.process` nos 15 ReAct agents | M (2d) | Visibilidade por agente |
| 8 | Adicionar spans `llm.generate` com tokens/cost | M (1d) | Cost tracking por chamada |
| 9 | Adicionar spans `agent.handoff` entre domains | M (1d) | 61% das falhas rastreadas |
| 10 | Exportar metricas operacionais via OTEL metrics | M (2d) | Dashboards em GCP |
| 11 | Persistir perf_metrics em Redis (nao in-memory) | S (1d) | Metricas sobrevivem restart |

### Sprint 3: Dashboards e alertas avancados (5-7 dias)

| # | Tarefa | Esforco | Impacto |
|---|--------|---------|---------|
| 12 | Criar pagina `/configuracoes/agent-quality` no frontend | M (3d) | Dashboard executivo |
| 13 | Integrar Langfuse para LLM-specific traces | M (1d) | LLM observability |
| 14 | Configurar alertas WARNING (ALT-W01 a W07) | M (1d) | Alertas proativos |
| 15 | Criar GCP Monitoring dashboard (infra) | S (1d) | Dashboard tecnico |
| 16 | Documentar runbooks para cada alerta CRITICAL | M (1d) | Operabilidade |

**Esforco total: ~15-20 dias** para observability enterprise.

---

## RESUMO EXECUTIVO

### Achado principal: Infra existe, falta ATIVAR

O codebase tem uma infra de observability surpreendentemente madura:
- OTEL tracing com 20+ spans definidos — mas `OTEL_EXPORTER_OTLP_ENDPOINT=""` (nao exporta)
- Sentry com PII scrubbing — mas `SENTRY_DSN=""` (nao envia)
- Structured logging com PII masking — mas vai para STDOUT sem aggregation
- CalibrationService calcula human intervention rate — mas sem alerta
- TenantBudget faz cost tracking — mas sem dashboard

**O trabalho nao e construir — e conectar.** Sprint 1 e puramente configuracao.

### Investimento vs Retorno

| Sprint | Esforco | O que ganha |
|--------|---------|-------------|
| Sprint 1 | 3-5 dias | Error tracking, tracing, alertas criticos, log aggregation |
| Sprint 2 | 5-7 dias | Agent-level visibility, cost per LLM call, handoff tracing |
| Sprint 3 | 5-7 dias | Dashboards executivo e tecnico, alertas proativos |

### Custo operacional estimado
- GCP Cloud Trace: incluido no GCP
- GCP Cloud Logging: incluido no GCP
- GCP Cloud Monitoring: incluido no GCP
- Sentry: free tier (10k events/mes)
- Langfuse: free tier (50k observations/mes)
- **Total: ~$0/mes** para o volume atual (tudo nos free tiers do GCP + Sentry + Langfuse)
