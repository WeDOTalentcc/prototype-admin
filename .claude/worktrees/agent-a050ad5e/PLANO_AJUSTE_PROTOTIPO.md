# Plano de Ajuste do Protótipo — Base Arquitetural André
> Referência canônica para implementação completa. Atualizar status de cada item conforme implementado.
> Baseado em: análise do documento arquitetural do André (mar/2026) + diagnóstico do protótipo.
> Data início: 07/03/2026

---

## Status Geral

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | AuditCallback + Dual Storage | ✅ Implementado |
| 2 | Orquestrador com Escada de Custo | ✅ Implementado |
| 3 | LangGraph Nativo + ReAct Nativo | ✅ Infraestrutura criada (migração gradual via flag) ✅ ATIVO em produção (08/03/2026) |
| 4 | WebSocket para Chat de Agentes | ✅ Implementado |
| 5 | Celery priority queues + tasks domínio | ✅ Implementado |
| 5b | Settings subcategorização + Secrets provider | ✅ Implementado |
| 6 | UV Monorepo — libs/config, utils, models, audit, messaging, agents-core + apps/* | ✅ Implementado |
| 6c | UV Monorepo — libs/services, libs/contexts (9 domínios), libs/auth | ✅ Implementado |

---

## FASE 1 — AuditCallback + Dual Storage (CRÍTICA)

> Objetivo: toda execução de agente — Graph ou ReAct — produz registro imutável completo.
> Metadados leves → PostgreSQL. Payload completo (prompts, respostas, tool I/O) → S3/arquivo local.
> Nenhum agente precisa saber que está sendo auditado.

### 1.1 Novos arquivos

- [x] `app/shared/compliance/audit_models.py` — dataclasses: `LLMCallRecord`, `ToolCallRecord`, `ExecutionEntry`, `ExecutionAuditRecord`
- [x] `app/shared/compliance/audit_storage.py` — abstração storage: `AuditStorage` (ABC), `LocalFileStorage`, `S3Storage`, `get_audit_storage()`
- [x] `app/shared/compliance/audit_writer.py` — `persist(record, db)` → storage + PG com `ON CONFLICT DO NOTHING`
- [x] `app/shared/compliance/audit_callback.py` — `AuditCallback(BaseCallbackHandler)`: hooks automáticos LangGraph + hooks manuais para react_loop custom
- [x] `app/api/v1/audit_timeline.py` — `GET /api/v1/audit/executions/{execution_id}/timeline` + `GET /api/v1/audit/executions`
- [x] `alembic/versions/025_add_agent_execution_metadata.py` — tabela `audit_execution_metadata`

### 1.2 Arquivos a modificar

- [x] `app/shared/compliance/__init__.py` — exportar `AuditCallback`, `AuditWriter`, `AuditStorage`
- [x] `app/core/config.py` — adicionadas todas as vars de Fase 1 + 2 + 3 + 4 + 5
- [x] `app/main.py` — registrar router `audit_timeline` + `agent_chat_ws`

### 1.3 Injeção do AuditCallback em todos os agentes

- [x] `app/shared/agents/react_loop.py` — instrumentado: `on_chain_start_manual`, `on_llm_call`, `on_tool_call`, `on_chain_end_manual`
- [x] `app/domains/job_management/agents/wizard_react_agent.py`
- [x] `app/domains/cv_screening/agents/pipeline_react_agent.py`
- [x] `app/domains/sourcing/agents/sourcing_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- [x] `app/domains/hiring_policy/agents/policy_react_agent.py`
- [x] `app/domains/pipeline/agents/pipeline_transition_agent.py`
- [x] `app/domains/automation/agents/automation_react_agent.py` — refatorado: padrão correto (available_tools, working_memory_service, AuditCallback, loop.run(message, context, session_id))
- [x] `app/domains/job_management/agents/job_wizard_graph.py` — AuditCallback via `audit_callback=` param em `invoke()` + `_execute_node()`
- [x] `app/domains/cv_screening/agents/wsi_interview_graph.py` — AuditCallback via `audit_callback=` param em `start()`/`submit_response()`/`_run_node()`
- [x] `app/domains/interview_scheduling/agents/interview_graph.py` — AuditCallback via `audit_callback=` param em `invoke()` + `_run_node()` via `_audit_callback`

### 1.4 Configuração de env

- [x] `.env` — adicionadas todas as vars de Fases 1-5

---

## FASE 2 — Orquestrador com Escada de Custo (ALTA)

> Objetivo: toda mensagem conversacional passa pelo orquestrador que resolve pelo tier mais barato possível.
> Tier 0 (memória) → Tier 1 (cache hash Redis) → Tier 2 (regex scoring) → Tier 3 (Haiku→Sonnet).

### 2.1 Novos arquivos

- [x] `app/orchestrator/__init__.py` — atualizado com exports novos
- [x] `app/orchestrator/semantic_cache.py` — cache Redis Tier 1 com TTL `ROUTER_CACHE_TTL`
- [x] `app/orchestrator/tenant_budget.py` — orçamento mensal por tenant (Redis + alertas 80%/100%)
- [x] `app/orchestrator/llm_cascade.py` — escada Haiku→Sonnet→Opus com thresholds configuráveis
- [x] `app/orchestrator/memory_resolver.py` — Tier 0: resolve pronomes/referências via WorkingMemory; integrado no `cascaded_router.route(session_id=)`
- [x] `app/orchestrator/router_prompts.py` — NÃO NECESSÁRIO: `fast_router.py` já cobre 12 domínios com patterns regex completos

### 2.2 Arquivos modificados

- [x] `app/orchestrator/cascaded_router.py` — adicionado Tier 1 Redis + `_route_via_llm_cascade()` + stats `redis_hits`
- [x] `app/core/config.py` — todas as vars adicionadas
- [x] `app/core/celery_app.py` — filas prioritizadas: `sourcing_high`(8), `evaluation_normal`(5), `vagas_normal`(5), `onboarding_low`(3)
- [x] `app/jobs/celery_tasks.py` — tasks `agents.wizard.process_async` e `agents.pipeline.transition_async`

### 2.3 Patterns de domínio para Tier 2 (regex_router)

**✅ JÁ IMPLEMENTADO** em `app/orchestrator/fast_router.py` com `DOMAIN_PATTERNS` cobrindo 12 domínios:
job_management, sourcing, cv_screening, wsi_assessment, interviewing, scheduling,
communication, pipeline_management, analytics, ats_integration, recruiter_assistant, task_planning

---

## FASE 3 — LangGraph Nativo + ReAct Nativo (ALTA)

> Objetivo: migrar de implementações custom (`react_loop.py`, `job_wizard_graph.py`) para LangGraph nativo.
> Vantagens: `PostgresSaver` checkpoints, `.astream()` streaming, callbacks automáticos, human-in-the-loop.
> Migração gradual: um agente por vez. Feature flag `USE_LANGGRAPH_NATIVE`.

### 3.1 Novos arquivos de infraestrutura

- [x] `app/shared/agents/langgraph_base.py` — `LangGraphBase`: StateGraph + AuditCallback via config + lazy compile + `_run_graph()`
- [x] `app/shared/agents/langgraph_react_base.py` — `LangGraphReActBase`: `create_react_agent` + `_process_langgraph()` + `_get_model()` padrão
- [x] `app/shared/agents/timed_tool_node.py` — `TimedToolNode`: wrapper `ToolNode` com métricas Prometheus
- [x] `app/shared/agents/confidence.py` — `compute_confidence()` + `ConfidenceNode` para StateGraph
- [x] `app/shared/agents/checkpointer.py` — `get_checkpointer()`: MemorySaver (dev) / PostgresSaver (prod) com fallback
- [x] `alembic/versions/026_add_langgraph_checkpoint_columns.py` — colunas LangGraph + tabela `agent_checkpoint_writes`

### 3.2 Migração dos agentes Graph (StateGraph nativo)

- [x] `app/domains/job_management/agents/job_wizard_graph.py` — dual-path: `_build_langgraph()` (StateGraph + PostgresSaver + routing nomeado), `_invoke_langgraph()`, `invoke()` despacha por `USE_LANGGRAPH_NATIVE`
- [x] `app/domains/cv_screening/agents/wsi_interview_graph.py` — dual-path: serialização `_wsi_state_to_dict`/`_wsi_state_from_dict`, StateGraph com dispatcher `start`/`submit`, `_start_langgraph()`/`_submit_response_langgraph()`
- [x] `app/domains/interview_scheduling/agents/interview_graph.py` — dual-path: `_build_langgraph()` (TypedDict state), `_invoke_langgraph()`, `invoke()` despacha por `USE_LANGGRAPH_NATIVE`

### 3.3 Migração dos agentes ReAct (LangGraph ReAct nativo)

Padrão dual-path: `process()` → `USE_LANGGRAPH_NATIVE` → `_process_langgraph()` ou `_process_react_loop()` (legado).
Adapter `tool_definition_to_langchain_tool()` converte ToolDefinition → LangChain StructuredTool sem alterar registries.

- [x] `app/domains/job_management/agents/wizard_react_agent.py` — piloto migrado: `LangGraphReActBase`, `_get_tools()`, `_get_system_prompt()`, `_state_to_output()`
- [x] `app/domains/cv_screening/agents/pipeline_react_agent.py`
- [x] `app/domains/sourcing/agents/sourcing_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- [x] `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- [x] `app/domains/hiring_policy/agents/policy_react_agent.py`
- [x] `app/domains/automation/agents/automation_react_agent.py`
- [x] `app/domains/pipeline/agents/pipeline_transition_agent.py`

### 3.4 Ajustes de infraestrutura compartilhada

- [x] `app/shared/agents/react_loop.py` — `tool_definition_to_langchain_tool()` adicionado; legado mantido intacto
- [x] `app/shared/agents/react_agent_registry.py` — `langgraph_native: True` em todos os 9 agentes migrados
- [x] `app/core/config.py` — `USE_LANGGRAPH_NATIVE=False` (feature flag — ativar por agente em staging)
- [x] `app/services/checkpoint_service.py` — `save/restore/delete_checkpoint` viram no-ops quando `USE_LANGGRAPH_NATIVE=True`; `_langgraph_native_active()` verifica o flag em runtime

---

## FASE 4 — WebSocket para Chat de Agentes (ALTA)

> Objetivo: feedback em tempo real durante execução de LLM/agentes via WebSocket.
> Frontend conecta em /ws/chat/{session_id}. Agente publica chunks conforme processa.
> Fluxo: FE → WS Gateway → RabbitMQ → Celery Worker → Agente → RabbitMQ (retorno) → WS Gateway → FE.

### 4.1 WebSocket Manager e schemas

- [x] `app/api/v1/ws_manager.py` — `WebSocketManager`: conexões por session_id, limite por tenant, broadcast, disconnect cleanup
- [x] `app/shared/websocket/ws_message_schemas.py` — schemas Pydantic: WSUserMessage, WSThinkingMessage, WSTokenMessage, WSResponseMessage, WSErrorMessage

### 4.2 Endpoint WebSocket de chat

- [x] `app/api/v1/agent_chat_ws.py` — `/ws/chat/{session_id}`: JWT auth, domain routing, thinking indicator, timeout, conversation history

### 4.3 Messaging (RabbitMQ producer/consumer)

- [x] `app/shared/messaging/__init__.py`
- [x] `app/shared/messaging/message_schemas.py` — `AgentChatMessage`, `AgentResponseMessage`
- [x] `app/shared/messaging/rabbitmq_producer.py` — `publish_chat_message()`, `publish_agent_response()` (aio-pika)
- [x] `app/shared/messaging/rabbitmq_consumer.py` — consumer das filas de resposta por session_id → `ws_manager.send_to_session()`
- [x] `app/shared/messaging/dispatchers.py` — `DomainDispatcher`: decide queue, cria reply_to, publica via producer; fallback para Celery direto
- [x] `app/shared/messaging/celery_config.py` — `DOMAIN_QUEUES`, `ASYNC_DOMAINS`, `SYNC_DOMAINS`, `get_domain_config()`

### 4.4 Celery tasks para execução via fila

- [x] `app/jobs/celery_tasks.py` — tasks adicionadas: `agents.wizard.execute`, `agents.pipeline.execute`, `agents.sourcing.execute`, `agents.screening.execute`, `agents.kanban.execute`, `agents.policy.execute`, `agents.automation.execute`

### 4.5 Streaming nativo (após Fase 3)

- [x] `app/shared/agents/streaming_callback.py` — `StreamingCallback(BaseCallbackHandler)`: `on_llm_new_token()` → `ws_manager.send_to_session()` com buffer configurável
- [x] Streaming integrado nos agentes LangGraph nativos: `_get_model(streaming=True)` + `StreamingCallback` injetado em `_run_graph()` via `_process_langgraph()` — tokens chegam ao WS via `on_llm_new_token` sem alterar a interface `process()` → `AgentOutput`

### 4.6 Modificações em infraestrutura

- [x] `app/core/celery_app.py` — rotas de tasks atualizadas: screening, kanban, automation, policy com filas corretas
- [x] `app/main.py` — RabbitMQ consumer inicializado no lifespan (start no boot, stop no shutdown)
- [x] `app/api/v1/agent_chat_ws.py` — dispatch assíncrono para ASYNC_DOMAINS via DomainDispatcher; unsubscribe no disconnect

---

## FASE 5 — Settings Categorizado + Config Provider (MÉDIA)

> Objetivo: `Settings` flat com 60+ vars → subclasses por domínio. Abstração de secrets para produção.

### 5.1 Refatoração do config

- [x] `app/core/config.py` — dividido em 7 subclasses com herança múltipla (backward compatible):
  - `DatabaseSettings`, `CacheSettings`, `MessagingSettings`, `LLMSettings`,
    `AuditSettings`, `AuthSettings`, `AppSettings`, `IntegrationSettings`
  - `Settings` herda de todas — todos os `settings.<FIELD>` continuam funcionando

### 5.2 Secrets provider

- [x] `app/core/secrets_provider.py` — interface abstrata `SecretsProvider` + `EnvProvider` (default) + `DopplerProvider` (produção) + `get_secrets_provider()`

---

## FASE 6 — UV Monorepo ✅ IMPLEMENTADO

> Objetivo: reestruturar `lia-agent-system` para `apps/` + `libs/` gerenciado por UV.
> Implementado nas sessões de mar/2026 (Fases 6a + 6b).

### 6.1 Estrutura implementada

```
lia-agent-system/
├── pyproject.toml              # UV workspace root ✅
├── uv.lock                     ✅
├── apps/
│   ├── api-vagas/              # Wizard, job management ✅
│   ├── api-funil/              # Pipeline, sourcing, screening, analytics ✅
│   └── api-onboarding/         # Company setup, benefits, culture ✅
└── libs/
    ├── models/                 # SQLAlchemy models (shared) ✅ scaffold
    ├── audit/                  # AuditCallback + AuditWriter (da Fase 1) ✅
    ├── agents-core/            # LangGraph base classes (da Fase 3) ✅
    ├── config/                 # Settings categorizados (da Fase 5) ✅
    ├── messaging/              # Email, Teams, WhatsApp providers ✅
    └── utils/                  # PII masking, dates, text, validators ✅
```

### 6.2 Checklist de migração

- [x] Criar `pyproject.toml` raiz com workspace UV
- [x] Extrair `libs/models/` — scaffold com `lia_models` package
- [x] Extrair `libs/audit/` — `AuditCallback`, `AuditWriter`, `AuditStorage`, `audit_models`
- [x] Extrair `libs/agents-core/` — `LangGraphBase`, `LangGraphReActBase`, `StreamingCallback`, `get_checkpointer`
- [x] Extrair `libs/config/` — `Settings`, `get_db`, `celery_app` + shims em `app/core/`
- [x] Extrair `libs/messaging/` — `send_email` (Resend/SendGrid/Mailgun), `send_teams_message`, `send_whatsapp_message`
- [x] Extrair `libs/utils/` — `mask_pii`, `datetime_helpers`, `skill_classifier`
- [x] Criar `apps/api-vagas/` — FastAPI app, Dockerfile, endpoints de vagas
- [x] Criar `apps/api-funil/` — FastAPI app, Dockerfile, endpoints de pipeline
- [x] Criar `apps/api-onboarding/` — FastAPI app, Dockerfile, endpoints de onboarding
- [x] Criar Dockerfiles individuais por app (com `libs/agents-core` corrigido)
- [x] CI GitHub Actions — backend lint+test+fairness, frontend lint+vitest+build, security audit, docker-build matrix
- [x] `.pth` shims para resolver imports em desenvolvimento (Replit)
- [x] `libs/services/` — BaseRepository, SQLAlchemyRepository, CandidateRepository, JobRepository, etc.
- [x] `libs/contexts/` — wizard (stage_context + system_prompt) e pipeline (stage_context + system_prompt)
- [x] `libs/auth/` — SecretsProvider, EnvProvider, get_secrets_provider + auth dependencies
- [x] `infra/docker-compose.yml` — workers Celery separados por fila (high/normal/low) + Celery Beat + Flower
- [x] `tests/contract/` — 98 contract tests: interface compliance, wizard→pipeline, sourcing→pipeline, multi-tenant isolation, kanban/talent/jobs_mgmt, policy, automation
- [x] 4 falhas pré-existentes corrigidas: `dependency_overrides` nos testes de recruitment_stages + mock `_route_via_llm_cascade` no cascaded router

---

## Inventário Completo de Agentes

Lista de todos os agentes do protótipo. Cada um deve passar por Fase 1 (AuditCallback) e Fase 3 (LangGraph nativo).

| Agente | Arquivo | Tipo | Fase 1 | Fase 3 |
|--------|---------|------|--------|--------|
| WizardReActAgent | `domains/job_management/agents/wizard_react_agent.py` | ReAct | [x] | [x] |
| JobWizardGraph | `domains/job_management/agents/job_wizard_graph.py` | Graph | [x] | [x] |
| PipelineReActAgent | `domains/cv_screening/agents/pipeline_react_agent.py` | ReAct | [x] | [x] |
| WSIInterviewGraph | `domains/cv_screening/agents/wsi_interview_graph.py` | Graph | [x] | [x] |
| SourcingReActAgent | `domains/sourcing/agents/sourcing_react_agent.py` | ReAct | [x] | [x] |
| TalentReActAgent | `domains/recruiter_assistant/agents/talent_react_agent.py` | ReAct | [x] | [x] |
| KanbanReActAgent | `domains/recruiter_assistant/agents/kanban_react_agent.py` | ReAct | [x] | [x] |
| JobsMgmtReActAgent | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | ReAct | [x] | [x] |
| PolicyReActAgent | `domains/hiring_policy/agents/policy_react_agent.py` | ReAct | [x] | [x] |
| AutomationReActAgent | `domains/automation/agents/automation_react_agent.py` | ReAct | [x] | [x] |
| PipelineTransitionAgent | `domains/pipeline/agents/pipeline_transition_agent.py` | ReAct | [x] | [x] |
| InterviewGraph | `domains/interview_scheduling/agents/interview_graph.py` | Graph | [x] | [x] |

---

## Inventário Completo de Services a Verificar/Ajustar

Services que precisam ser revisados em cada fase para garantir integração correta:

| Service | Arquivo | Fase relevante | Status |
|---------|---------|----------------|--------|
| AuditService | `shared/compliance/audit_service.py` | 1 | [x] OK — loga decisões de negócio separado do AuditCallback |
| ReActObserver | `shared/agents/observability.py` | 1 | [x] OK — telemetria por execução via `observer=` no ReActLoop |
| WorkingMemoryService | `shared/agents/working_memory.py` | 2 | [x] OK — usado pelo MemoryResolver e agentes via ReActLoop |
| EmbeddingCacheService | `services/embedding_cache_service.py` | 2 | [x] Corrigido — Redis backend + write-through local; warm-up documentado |
| LLMService | `services/llm.py` | 2, 3 | [x] OK — múltiplos providers, lê settings corretamente |
| CheckpointService | `services/checkpoint_service.py` | 3 | [x] OK — Postgres upsert; coexiste com LangGraph PostgresSaver na Fase 3 |
| WizardOrchestratorService | `domains/job_management/services/wizard_orchestrator_service.py` | 2 | [x] OK — WizardIntent + INTENT_TO_TOOL_MAPPING completo |
| DomainRegistry | `domains/registry.py` | 2 | [x] OK — @register_domain decorator, descoberta dinâmica |
| RateLimitMiddleware | `middleware/rate_limiter.py` | 2 | [x] OK — Redis sliding window com fallback in-memory |
| AutomationScheduler | `services/automation_scheduler.py` | 4 | [x] Corrigido — Redis jobstore (coalesce=True, max_instances=1) para multi-instância |

---

## Novas Variáveis de Ambiente

Todas as envs novas a adicionar no `.env.example` e documentar:

```bash
# Fase 1 — Audit Storage
AUDIT_STORAGE_TYPE=file          # "file" (dev) | "s3" (prod)
AUDIT_STORAGE_BUCKET=            # S3 bucket (prod apenas)
AUDIT_STORAGE_PREFIX=audit       # Prefixo de path no S3
AUDIT_LOCAL_DIR=./audit_logs     # Diretório local (dev)
S3_ACCESS_KEY=                   # AWS access key (prod)
S3_SECRET_KEY=                   # AWS secret key (prod)
S3_REGION=us-east-1              # AWS region

# Fase 2 — Orquestrador
LLM_ROUTER_MODEL=claude-haiku-4-5-20251001       # Modelo barato para roteamento
LLM_AGENT_MODEL=claude-sonnet-4-6                # Modelo capaz para agentes
LLM_ROUTER_TEMPERATURE=0.1
LLM_AGENT_TEMPERATURE=0.3
ROUTER_CONFIDENCE_THRESHOLD=0.80
ROUTER_CACHE_TTL=3600
SEMANTIC_CACHE_TTL=86400
TENANT_TOKEN_BUDGET_DEFAULT=500000               # tokens/mês por empresa
TENANT_TOKEN_BUDGET_ALERT_THRESHOLD=0.80

# Fase 3 — LangGraph
USE_LANGGRAPH_NATIVE=true        # Feature flag para migração gradual

# Fase 4 — WebSocket / Messaging
RABBITMQ_EXCHANGE=rh_platform
RABBITMQ_PREFETCH=1
WS_MAX_CONNECTIONS_PER_TENANT=100

# Fase 5 — Config Provider
SECRETS_PROVIDER=env             # "env" (dev) | "doppler" (prod)
DOPPLER_TOKEN=                   # Token Doppler (prod)
```

---

## Novas Migrations Alembic

| # | Arquivo | O que cria | Fase |
|---|---------|------------|------|
| 025 | `025_add_agent_execution_metadata.py` | Tabela `audit_execution_metadata` | 1 |
| 026 | `026_add_langgraph_checkpoints.py` | Tabelas nativas LangGraph (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`) | 3 |

---

## Convenções de Implementação

- Todo arquivo novo com `"""docstring"""` explicando propósito
- Multi-tenant: `company_id` obrigatório em toda query nova
- Sem breaking changes: backward compatible em todas as fases 1-5
- Feature flags para Fase 3: `USE_LANGGRAPH_NATIVE` permite rollback imediato
- Logs estruturados: `logger = logging.getLogger(__name__)` — sem `print()`
- PII masking: usar `get_masked_logger(__name__)` em services que processam dados de candidatos
- Imports circulares: evitar via injeção de dependência ou imports lazy

---

## Log de Progresso

| Data | Fase | O que foi feito |
|------|------|-----------------|
| 07/03/2026 | — | Plano criado. Revisão profunda do protótipo concluída. |
| 07/03/2026 | 1 | `audit_models.py`, `audit_storage.py`, `audit_writer.py`, `audit_callback.py` criados |
| 07/03/2026 | 1 | Migration 025, `audit_timeline.py`, `compliance/__init__.py` atualizados |
| 07/03/2026 | 1 | `react_loop.py` instrumentado com `on_chain_start_manual`, `on_llm_call`, `on_tool_call`, `on_chain_end_manual` |
| 07/03/2026 | 1 | AuditCallback injetado em 8 agentes ReAct (wizard, pipeline, sourcing, talent, kanban, jobs_mgmt, policy, pipeline_transition) |
| 07/03/2026 | 1 | `.env` atualizado com todas as vars Fase 1-5 |
| 07/03/2026 | 2 | `semantic_cache.py`, `tenant_budget.py`, `llm_cascade.py` criados |
| 07/03/2026 | 2 | `cascaded_router.py` atualizado: Tier 1 Redis + `_route_via_llm_cascade()` |
| 07/03/2026 | 2 | `orchestrator/__init__.py` atualizado com novos exports |
| 07/03/2026 | 2 | `celery_app.py` — filas prioritizadas por domínio adicionadas |
| 07/03/2026 | 2 | `celery_tasks.py` — tasks `agents.wizard.process_async` e `agents.pipeline.transition_async` adicionadas |
| 07/03/2026 | 3 | `langgraph_base.py`, `langgraph_react_base.py`, `timed_tool_node.py`, `confidence.py`, `checkpointer.py` criados |
| 07/03/2026 | 3 | Migration 026 criada (colunas LangGraph + `agent_checkpoint_writes`) |
| 07/03/2026 | 4 | `ws_manager.py` e `agent_chat_ws.py` criados; router registrado em `main.py` |
| 07/03/2026 | 5b | `app/core/secrets_provider.py` criado: `EnvProvider` + `DopplerProvider` + `get_secrets_provider()` |
| 08/03/2026 | 6c | `libs/contexts/` completo: todos os 9 domínios (wizard, pipeline, pipeline_transition, sourcing, kanban, talent, jobs_mgmt, policy, automation) |
| 08/03/2026 | 6c | `libs/services/` (repositories) + `libs/auth/` (SecretsProvider + auth deps) criados |
| 08/03/2026 | QA | Coverage baseline medido (30%), gate `--cov-fail-under=25` no CI |
| 08/03/2026 | QA | 98 contract tests passando (5 arquivos `tests/contract/`) |
| 08/03/2026 | QA | docker-compose: 3 workers Celery por fila + Beat + Flower |
| 08/03/2026 | QA | 4 falhas pré-existentes corrigidas (`dependency_overrides` + mock LLM cascade) |
| 08/03/2026 | Fase 1 (Gaps) | `langgraph-checkpoint-postgres>=2.0.0` confirmado no pyproject.toml |
| 08/03/2026 | Fase 1 (Gaps) | `checkpointer.py` corrigido: WARNING explícito em dev, RuntimeError em produção |
| 08/03/2026 | Fase 1 (Gaps) | Migration 027 criada: tabelas nativas `langgraph_checkpoints`, `langgraph_checkpoint_writes`, `langgraph_checkpoint_blobs` |
| 08/03/2026 | Fase 1 (Gaps) | Suite de regressão `test_langgraph_native_regression.py`: 12 agentes × 3-4 testes cada |
| 08/03/2026 | Fase 1 (Gaps) | `USE_LANGGRAPH_NATIVE=True` ativado em `lia_config/config.py` + `.env.example` atualizado |
| 08/03/2026 | Fase 2 (Gaps) | `vector_semantic_cache.py` — VectorSemanticCache com pgvector cosine similarity (substitui hash MD5) |
| 08/03/2026 | Fase 2 (Gaps) | Migration 028: tabela `routing_cache_vectors` com índice ivfflat |
| 08/03/2026 | Fase 2 (Gaps) | `cascaded_router.py` — 6 tiers + clarification fallback + stats por tier |
| 08/03/2026 | Fase 2 (Gaps) | `agent_interface.py` — `ClarificationOutput` adicionado |
| 08/03/2026 | Fase 2 (Gaps) | `agent_chat_ws.py` — trata `clarification_needed` via WebSocket |
| 08/03/2026 | Fase 3 (Gaps) | `metrics.py` — 5 novas métricas Prometheus: router_tier_hit, router_latency, router_confidence, agent_tool_failures, llm_cost_usd |
| 08/03/2026 | Fase 3 (Gaps) | `cascaded_router.py` instrumentado com métricas por tier |
| 08/03/2026 | Fase 3 (Gaps) | `audit_storage.py` — política de retenção S3 (90d Standard → Glacier → 7 anos SOX) |
| 08/03/2026 | Fase 3 (Gaps) | `celery_tasks.py` — task `audit.apply_lifecycle_policy` + beat schedule mensal |
| 08/03/2026 | Fase 3 (Gaps) | `langgraph.json` + `.langgraph_studio/README.md` para LangGraph Studio |
| 08/03/2026 | Fase 4 (Gaps) | `search_service.py` — SearchBackend abstraction: PostgresSearchBackend + ElasticsearchSearchBackend |
| 08/03/2026 | Fase 4 (Gaps) | `tests/snapshots/` — 6 snapshot fixtures + 6 testes para Wizard e Pipeline agents |
| 08/03/2026 | Fase 4 (Gaps) | `platform_events.py` — PlatformEvent + JobPublished/Closed/CandidateMoved/CompanyConfigured |
| 08/03/2026 | Fase 4 (Gaps) | `platform_event_handlers.py` + `rabbitmq_producer.publish_to_exchange()` |
| 08/03/2026 | Fase 4 (Gaps) | 2056 testes passando (era 1936 antes dos gaps — +120 novos testes)
