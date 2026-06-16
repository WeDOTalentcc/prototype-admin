# Diagnóstico Completo — Plataforma LIA
**Data:** Abril 2026 | **Score atual:** 94/100 | **Verificado contra codebase real**

---

## PARTE 1 — STATUS DOS ITENS DO EXCALIDRAW

### ✅ OPORTUNIDADES — Status Atual

| # | Item | Status | Evidência |
|---|------|--------|-----------|
| 1 | Crew Delegation Fase 3: AgentBus | ✅ Implementado | `app/shared/agents/agent_bus.py` — delegation funcional entre domínios |
| 2 | RAGAS evals Blocking em CI/CD | ✅ Implementado | Golden datasets por domínio, LLM-as-judge |
| 3 | OpenTelemetry full coverage | ✅ Implementado | `app/shared/observability/` — 6 Prometheus counters |
| 4 | Prompt versioning + A/B testing | ✅ Implementado | `app/shared/prompt_experiment.py` + `intelligence/ab_testing_service.py` |
| 5 | Event-driven arch (Kafka/NATS) | ⏳ Pendente | Ainda usa chamadas síncronas inter-domínio. Sem message broker nativo |
| 6 | Vector Store scaling (pgvector→Pinecone) | ⏳ Pendente | Usa `pgvector` nativo. Adequado para volume atual, escala limitada |
| 7 | AI Disclosure + HITL badges | ✅ Task #125 | Headers com badges EU AI Act implementados |
| 8 | Cost Dashboard granular | ✅ Implementado | `TenantBudget` + alertas por agente |
| 9 | Agent Studio & Marketplace | ✅ Implementado | `app/domains/agent_studio/` |
| 10 | Voice Abstraction + LLM Factory | ✅ Task #119 | `app/domains/voice/` — Gemini Live Audio |
| 11 | Deep Audit + Playwright | ✅ Task #131 | `PRODUCT_READINESS_AUDIT_REPORT.md` — 94/100 |
| 12 | Pipeline UX Cards + DS v4.2.2 | ✅ Implementado | Kanban cards redesenhados, Design System aplicado |

**Resultado: 10/12 concluídos. 2 pendentes (infra de escala).**

### ⚠️ GAPS POTENCIAIS — Status Atual

| # | Item | Status | Detalhe |
|---|------|--------|---------|
| 1 | Observabilidade e2e OpenTelemetry | ✅ Expandida | Counters, tracing, structured logging |
| 2 | Guardrails custo/token por request | ⚠️ Parcial | `TenantBudget` é por rota, não por request individual |
| 3 | A/B testing de prompts | ✅ Ativo | `prompt_experiment.py` com registro de métricas |
| 4 | RAG chunking (recursive vs current) | ⚠️ Pendente | Usa abordagem simples, sem recursive/semantic chunking |
| 5 | HITL UI + badges aprovações | ✅ Task #125 | Implementado no header |
| 6 | Crew Delegation Fase 3 | ✅ Funcional | AgentBus com delegação inter-agente |
| 7 | RAGAS Blocking CI/CD | ✅ Golden datasets | Por domínio |
| 8 | Streaming WebSocket + SSE | ✅ Implementado | Fallback para edge cases |

**Resultado: 6/8 resolvidos. 2 parciais (custo granular + RAG chunking).**

---

## PARTE 2 — OPORTUNIDADES DE OTIMIZAÇÃO

### 🔴 CRÍTICO — Domínios Stub (Alto Impacto)

**Problema:** Dos 56 domínios, ~23 são scaffolding puro (4 arquivos: `__init__.py`, `dependencies.py`, `repositories/`, `__pycache__/`). Infla métricas artificialmente.

**Domínios Stub:**
`admin_settings`, `agent_memory`, `approvals`, `bulk_actions`, `candidate_lists`, `company_culture`, `consent`, `data_subject`, `email_templates`, `goals`, `health_check`, `job_vacancies_analytics`, `journey_mapping`, `notifications`, `observability`, `recruitment_journey`, `saas_metrics`, `shared_searches`, `tasks`, `technical_tests`, `triagem`, `trust_center`, `workforce`

**Recomendação:** Consolidar em categorias:
- **CRUD puro** → mover para `app/shared/repositories/` (não é domínio)
- **Sub-domínios** → absorver no domínio pai (ex: `email_templates` → `communication`)
- **Resultado esperado:** ~30 domínios reais em vez de 56

### 🔴 CRÍTICO — Serviços em Migração Parada

**Problema:** O sistema está "mid-migration" entre `app/services/` (169 arquivos) e `app/domains/*/services/`. Existem:
- ~34 shims em `app/services/` que importam de `app/domains/`
- ~82 shims em `app/domains/` que importam de `app/services/`
- Nenhuma fonte de verdade clara

**Recomendação:** Completar a migração:
1. Definir `app/domains/*/services/` como fonte de verdade
2. Mover lógica restante de `app/services/` para domínios
3. Manter `app/services/` apenas para shims de compatibilidade (temporários)
4. Deadline: eliminar `app/services/` em 2 sprints

### 🟡 IMPORTANTE — Orchestrator Complexity

**Problema:** 2 arquivos "god object":
- `cascaded_router.py`: 792 linhas
- `main_orchestrator.py`: 779 linhas
- `intent_router.py`: **DEAD CODE** — marcado como legacy, substituído pelo CascadedRouter

**Padrões duplicados:**
- Regex patterns em 3 lugares: `FastRouter.DOMAIN_PATTERNS`, `IntentRouter.INTENT_TO_AGENT_TYPE`, `action_executor/intents_config.py`
- Domain mappings duplicados em `cascaded_router.py`, `intent_router.py`, `orchestrator.py`

**Recomendação:**
1. **Remover `intent_router.py`** (dead code confirmado)
2. Extrair tiers do CascadedRouter em classes separadas (`LLMResolver`, `CacheResolver`, etc.)
3. Centralizar regex em `PatternRegistry` único
4. Mover domain mappings para `DomainRegistry`

### 🟡 IMPORTANTE — Shared Layer Duplications

**Duplicações encontradas:**
1. **Cache duplo:** `cache_strategy.py` (business logic) + `resilience/cache_manager_service.py` (3-layer engine) — namespaces diferentes para mesma coisa (`SKILL_CATALOG` vs `SKILLS_SUGGESTIONS`)
2. **Encryption dupla:** `encryption.py` (arquivo) + `encryption/` (diretório) coexistem
3. **Policy lookup:** `policy_helper.py` + `policy_middleware.py` — lógica de fallback duplicada
4. **Intelligence overlap:** Múltiplos `*_benchmark_service.py` que poderiam ser unificados

### 🟡 IMPORTANTE — Libs com Integração Incompleta

**3 libs prontas mas não conectadas:**
- `lia_contexts`: 9 domain contexts definidos mas não importados (0 refs externas)
- `lia_auth`: Poucas referências (só `secrets_provider.py`)
- `lia_orchestrator`: Só aparece em 1 arquivo de teste

**Recomendação:** Completar a integração ou remover para reduzir confusão

### 🟡 IMPORTANTE — Inconsistências de Agentes

**Padrões mistos:**
1. **Tool definition dupla:** Tools definidos em `app/domains/*/tools/` E redefinidos em `app/domains/*/agents/*_tool_registry.py`
2. **Routing inconsistente:** `SourcingReActAgent` usa routing por tool-selection (LLM decide), enquanto `cv_screening` usa stage-based filtering (determinístico)
3. **Legacy imports:** Alguns agentes ainda importam de `lia_agents_core.react_loop` (path legacy) apesar da "migração concluída"

**Recomendação:** Padronizar padrão de agente:
- Tool registry único por domínio
- Escolher entre tool-selection vs stage-filtering (ou documentar quando usar cada um)
- Eliminar imports legacy

---

## PARTE 3 — ANÁLISE DO RAILS/ATS BACKEND

### Estrutura Atual

| Componente | Quantidade |
|-----------|------------|
| Models | 101 |
| DB Tables (schema.rb) | 12 |
| Migrations | 85 |
| Controllers | 24 |
| Services | 6 |
| Serializers | 15 |
| Workers | 2 |

### 🔴 Gap Crítico: 101 Models vs 12 Tables

**Problema maior:** Existem 101 models Ruby mas apenas 12 tabelas no `schema.rb`. Isso significa que ~89 models (88%) não têm tabelas correspondentes no banco. As migrations existem (85 arquivos) mas aparentemente não foram executadas contra o schema.

**As 12 tabelas existentes:**
`accounts`, `applies`, `candidates`, `jobs`, `messages`, `permissions`, `role_permissions`, `roles`, `selective_processes`, `user_permissions`, `user_roles`, `users`

**Models sem tabela (exemplos):**
`company_hiring_policy`, `ai_credits_balance`, `audit_log`, `candidate_education`, `candidate_experience`, `interview`, `talent_pool`, `recruitment_campaign`, `big_five_question`, `consent_record`, `data_subject_request`, `email_template`, etc.

**Impacto:** A LIA (Python/FastAPI) tem serviços que tentam acessar esses dados. Se as tabelas não existem no PostgreSQL de produção, essas funcionalidades são fantasma.

### 🟡 Arquitetura Multi-tenant

- Usa **Apartment gem** (`ros-apartment`) para multi-tenancy por schema
- Search via **Searchkick + Elasticsearch**
- Queue: **Sidekiq** (Redis) + **Sneakers** (RabbitMQ/Bunny)
- Auth: JWT + BCrypt

### 🟡 Integração LIA ↔ Rails

**Questão central:** Como a LIA Python se conecta ao PostgreSQL do Rails?
- O Rails usa multi-tenancy por schema (Apartment)
- A LIA precisa respeitar os schemas por tenant
- Os services Python (SQLAlchemy) precisam apontar para as mesmas tabelas
- **Risco:** models Python e models Ruby podem estar dessincronizados

---

## PARTE 4 — RECOMENDAÇÕES PRIORIZADAS

### Sprint 1 (Imediato)
1. ❌ **Remover `intent_router.py`** — dead code confirmado
2. 🗂 **Consolidar domínios stub** — reduzir de 56 para ~30
3. 🔧 **Executar migrations Rails** — criar as 89 tabelas faltantes
4. 🧹 **Eliminar shims de serviços** — completar migração services

### Sprint 2 (Próximo)
5. 📦 **Unificar cache** — merge `cache_strategy.py` + `cache_manager_service.py`
6. 🔨 **Refatorar orchestrator** — extrair tiers em classes separadas
7. 🔗 **Conectar libs órfãs** — `lia_contexts`, `lia_auth`, `lia_orchestrator`
8. 🛠 **Padronizar tool registries** — um por domínio, eliminar duplas

### Sprint 3 (Futuro)
9. 📡 **Event-driven** — avaliar NATS/Redis Streams para inter-domínio
10. 🔍 **RAG chunking** — implementar recursive/semantic chunking
11. 💰 **Guardrails per-request** — granularizar `TenantBudget`
12. 📊 **Vector store** — avaliar migração pgvector quando volume justificar

---

## PARTE 5 — MÉTRICAS REAIS vs REPORTADAS

| Métrica | Reportada | Real | Delta |
|---------|-----------|------|-------|
| Domínios | 56 | ~30 reais + ~23 stubs + 3 micro-actions | Inflar em ~86% |
| Services | 169 (app/services/) | ~135 reais + ~34 shims | ~20% são shims |
| API Files | 304 | 304 | ✅ Correto |
| Orchestrator | 33 files (1.2MB) | 33 (mas 1 é dead code) | ~3% dead |
| Libs | 10 | 7 ativas + 3 não-conectadas | 30% pendentes |
| Rails Models | 101 | 12 com tabela | 88% sem backing DB |

---

*Diagnóstico gerado em Abril 2026 por análise automatizada do codebase Replit + repo GitHub WeDOTalentcc/ats-api-copia*
