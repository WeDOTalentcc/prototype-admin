# Paralelo Técnico: Plataforma LIA vs recruiter_agent_v5
## Estrutura de IA — Arquitetura, Agentes, Serviços e Arquivos
### com Análise de Mercado, Pros/Contras e Recomendações (baseado em leitura real do GitHub)

> **Objetivo:** Comparar lado a lado o que foi construído em cada sistema em relação à inteligência artificial — orquestração, agentes, subagentes, serviços de ML/IA, memória, fairness, prompts e observabilidade. Cada seção inclui análise de mercado com pros, contras e recomendação fundamentada.
>
> **LIA (Replit):** sistema de produção com 1.259 arquivos Python | **v5 (GitHub WeDOTalent):** sistema ativo com ~820 arquivos Python
>
> **Repositório v5:** `https://github.com/WeDOTalent/recruiter_agent_v5` (privado, acessado em 19/03/2026)
>
> **⚠️ NOTA DE ATUALIZAÇÃO (19/03/2026):** Este documento foi integralmente revisado com leitura direta de todos os arquivos do repositório `WeDOTalent/recruiter_agent_v5`. A versão anterior subestimava significativamente o v5 (tratado como "MVP com ~50 arquivos" quando na verdade tem 820 arquivos, LangGraph, PostgreSQL, 96 testes, 8 domínios, memória por tenant com pgvector, PII filtering, circuit breaker e sistema de auditoria). Todas as seções foram corrigidas.
>
> **Concorrentes de referência usados na análise:** Eightfold AI · Phenom · SeekOut · HireVue · Paradox (Olivia) · Greenhouse · Ashby · SmartRecruiters · Workday · Beamery · hireEZ · Fetcher

---

## Índice

1. [Visão Geral Quantitativa](#1-visão-geral-quantitativa)
2. [Filosofia de Arquitetura](#2-filosofia-de-arquitetura)
3. [Estrutura de Pastas (IA)](#3-estrutura-de-pastas-ia)
4. [Orquestração e Roteamento](#4-orquestração-e-roteamento)
5. [Agentes por Domínio — Infográfico Completo](#5-agentes-por-domínio--infográfico-completo)
6. [Subagentes e Grafos LangGraph](#6-subagentes-e-grafos-langgraph)
7. [Tool Registries (Ferramentas por Agente)](#7-tool-registries-ferramentas-por-agente)
8. [Serviços de IA/ML](#8-serviços-de-iaml)
9. [Memória e Estado](#9-memória-e-estado)
10. [Prompts e Persona](#10-prompts-e-persona)
11. [Fairness e Compliance de IA](#11-fairness-e-compliance-de-ia)
12. [PII e Proteção de Dados](#12-pii-e-proteção-de-dados)
13. [Resiliência e Fallback de LLM](#13-resiliência-e-fallback-de-llm)
14. [Aprendizado e Adaptação](#14-aprendizado-e-adaptação)
15. [Observabilidade de IA](#15-observabilidade-de-ia)
16. [Integrações com LLMs](#16-integrações-com-llms)
17. [Testes de IA](#17-testes-de-ia)
18. [Jobs e Processamento Assíncrono](#18-jobs-e-processamento-assíncrono)
19. [Inventário de Arquivos de IA](#19-inventário-de-arquivos-de-ia)
20. [Plano de Otimização v5 — Passo a Passo](#20-plano-de-otimização-v5--passo-a-passo)
21. [Plano de Otimização LIA — Pendências](#21-plano-de-otimização-lia--pendências)
22. [Mapa de Domínios: Cobertura Cruzada LIA vs v5](#22-mapa-de-domínios-cobertura-cruzada-lia-vs-v5)

---

## 1. Visão Geral Quantitativa

> **Nota:** Números do v5 corrigidos após leitura direta do repositório GitHub (19/03/2026).

| Métrica | Plataforma LIA | recruiter_agent_v5 |
|---|---|---|
| **Total de arquivos Python** | ~1.259 (app/) + 313 testes | ~820 totais (352 em src/ + 96 testes + deploy/docs) |
| **Endpoints de API** | 362 (FastAPI) | REST + WebSocket via FastAPI (`src/api.py`) |
| **Serviços** | 250+ (app/services/ + domains/*/services/) | 51 (src/services/) |
| **Modelos de banco** | 102 modelos SQLAlchemy + 47 migrações | PostgreSQL: `tenant_memories` (pgvector 768d) + `agent_executions` (audit) |
| **Testes** | 313 arquivos, 4.600+ casos | 96 arquivos (tests/) |
| **Domínios de IA** | 13 domínios | 8 domínios (jobs, applies, sourcing, scheduling, evaluation, insights, messaging, autonomous) |
| **Agentes principais** | 12 ReAct + 4 StateGraph + 1 PolicySetup + 6 subagentes Z1 = **23 totais** | 6 pipeline + 9 sourcing subagentes + 8 domain agents (ReAct/LangGraph) + autonomous = ~30 totais |
| **Grafos LangGraph** | 5 (WSI, Interview, Wizard, SourcingEngagement, BaseStateMachine) | 4 (workflow/graph.py, supervisor_graph.py, evaluation/graph.py, scheduling/graph.py) |
| **Ferramentas (tools)** | 163+ tools mapeadas em registries | ~73 tools no autonomous + actions por domínio |
| **APIs externas** | 4 ATS clients + Apify + Hubspot | 51 APIs em YAML (documentation/) |
| **Modelos LLM** | Claude + Gemini + OpenAI (cascade) | Google Gemini (gemini-2.5-flash) primário via `create_tracked_llm()` |
| **Memória persistente** | WorkingMemory + LongTermMemory + PostgreSQL | TenantMemoryStore (PostgreSQL + pgvector, TTL 30 dias) + por-domínio in-session |
| **Cache semântico** | pgvector cosine ≥ 0.92 | `semantic_cache.py` via Redis |
| **Circuit breaker** | 15+ circuits (Claude, Gemini, OpenAI, 5 ATS, Redis, DB...) | `circuit_breaker.py` (global, threshold configurável) |
| **PII filtering** | `pii_masking.py` + Presidio Layer 4 | `pii_filter.py` (CPF, email, phone) + `security.py` (injection) |
| **Filas assíncronas** | Celery + Redis | RabbitMQ + Celery (`celery_app.py`, `celery_worker.py`) |
| **Linhas de código (est.)** | ~130.000+ | ~70.000+ |
| **Multi-tenancy** | Sim — budget + guardrails por empresa | Não (Rails gerencia auth/tenancy) |
| **Deploy em produção** | Sim (Replit + workers Celery) | GCP configurado (`deploy/GCP_DEPLOY_GUIDE.md`) + systemd workers |

### 🔍 Análise de Mercado — Seção 1

**Pros LIA:**
- Volume de código e cobertura de domínio compatível com plataformas enterprise como Greenhouse e SmartRecruiters
- 313 arquivos de teste com 4.600+ casos é um número sólido para o estágio atual
- 362 endpoints cobrem praticamente toda a superfície de um ATS moderno
- Multi-tenancy nativo no agente (não só no backend) é diferencial real

**Contras LIA:**
- 250+ serviços sem hierarquia clara cria confusão sobre onde colocar código novo — duplicação entre `app/services/` (plana) e `domains/*/services/`
- Razão testes/código provavelmente abaixo de 40%

**Pros v5:**
- 820 arquivos cobrindo 8 domínios, com LangGraph, PostgreSQL, memória vetorial, 96 testes, PII filter e circuit breaker — escopo muito maior do que aparenta externamente
- Stack moderna e coesa: Gemini + LangGraph + PostgreSQL/pgvector + Redis + RabbitMQ + Celery
- Auditoria arquitetural interna (docs/ARCHITECTURAL_AUDIT.md) mostra maturidade de engenharia

**Contras v5:**
- Sem multi-tenancy no agente — Rails é o guardião, o v5 é um proxy inteligente
- Sem LGPD compliance formal (consent, DSR, cleanup)
- Sem learning loop — não melhora com o tempo

**O que o mercado faz:** Eightfold AI tem mais de 2.000 arquivos só no core de ML. Ashby tem ~800 arquivos de backend com cobertura de testes acima de 70%. Phenom separou seu sistema em microserviços por domínio desde a série B.

**Recomendação para LIA:** Consolidar hierarquia de serviços, aumentar cobertura de testes para 50%+ nos domínios críticos.
**Recomendação para v5:** Adicionar multi-tenancy no agente (budget por tenant via `tenant_budget.py` similar à LIA), implementar LGPD básico.

---

## 2. Filosofia de Arquitetura

> **Correção (19/03/2026):** O v5 NÃO é "pipeline sequencial linear". Possui HubOrchestrator com CostLadder routing, 4 grafos LangGraph, checkpointing PostgreSQL/MemorySaver e memória por tenant.

| Aspecto | Plataforma LIA | recruiter_agent_v5 |
|---|---|---|
| **Paradigma central** | Plataforma SaaS multi-tenant de produção | Sistema ATS multi-agente com hub orchestration |
| **Padrão de IA** | ReactAgent + LangGraph (grafos por domínio) | Hub→Domain com LangGraph (StateGraph por domínio) |
| **Roteamento** | CascadedRouter 6 tiers + cache semântico | HubPlanner: fast-path regex + CostLadder + LLM |
| **Estado** | WorkingMemory + LongTermMemory + PostgreSQL | Redis (session) + PostgreSQL (tenant_memories) + LangGraph checkpointer |
| **Multi-tenancy** | Sim — budget por tenant, guardrails por empresa | Não (Rails gerencia; v5 usa auth_token por request) |
| **Fairness** | FairnessGuard 3 camadas obrigatório | fairness.py em jobs e sourcing (não obrigatório) |
| **Escalabilidade** | Celery + Redis + workers horizontais | RabbitMQ + Celery + workers horizontais |
| **Observabilidade** | LangSmith + OTEL + métricas customizadas | audit_callback + llm_tracking + react_observer |
| **Aprendizado contínuo** | Learning Loop + A/B testing + ML feedback | feedback/tracker.py (sem loop automático) |
| **LLM primário** | Claude (Haiku/Sonnet/Opus) | Google Gemini (gemini-2.5-flash) |

### 🔍 Análise de Mercado — Seção 2

**Por que o v5 não é "pipeline sequencial"?**

O v5 tem **3 camadas de orquestração**:
1. `HubOrchestrator` (`src/hub/orchestrator.py`) — sessão, planejamento, execução
2. `DomainOrchestrator` (`src/domains/orchestrator.py`) — bridge hub→domain com audit e checkpointing
3. `DomainWorkflow` (`src/domains/workflow.py`) — LangGraph: intent → execute → format

O "pipeline" de 6 agentes (`src/agents/`) é apenas o **fluxo original (legacy)** — o sistema principal usa o hub multi-domain.

**Por que a complexidade de arquitetura é diferente:**

```
LIA:                                   v5:
6 tiers (Tier 0→5) + domínios         3 camadas (Hub → Domain → Domain Workflow)
+ 13 domínios                          + 8 domínios
+ FairnessGuard mandatório             + fairness por domínio (opt-in)
+ multi-tenancy                        + auth por token (Rails gerencia)
+ learning loop                        + feedback tracker
```

**Pros LIA:**
- ReactAgent + LangGraph é o padrão atual da indústria
- Multi-tenancy com budget por empresa é diferencial real
- Fairness obrigatória coloca a LIA à frente de HireVue

**Contras LIA:**
- Com 6 tiers de orquestração, um bug em produção pode ter múltiplas causas — debugging mais complexo
- Anthropic avisa: "comece com um único agente antes de ir para multi-agente"

**Pros v5:**
- 3 camadas são mais fáceis de debugar que 6 tiers
- LangGraph nativo por domínio desde o início — arquitetura mais limpa

**Contras v5:**
- Sem multi-tenancy no agente — se dois tenants têm comportamentos diferentes, não há como personalizar no v5
- Sem fairness obrigatória — em produção, risco legal real

**O que o mercado faz:** Paradox (Olivia) usa pipeline conversacional deliberadamente simples. Eightfold usa orquestração mais próxima do v5 (hub→domain). A tendência é manter complexidade proporcional ao problema.

**Recomendação para v5:** Documentar as 3 camadas formalmente (ADR — Architecture Decision Record). Adicionar guardrail de multi-tenancy no HubOrchestrator: passar `tenant_id` via context e bloquear acesso cross-tenant.

---

## 3. Estrutura de Pastas (IA)

### Plataforma LIA — `lia-agent-system/app/`

```
app/
├── orchestrator/                    ← ROTEAMENTO CENTRAL DE IA (18 arquivos)
│   ├── cascaded_router.py           ← 6-tier router (principal)
│   ├── fast_router.py               ← Tier 4: regex/keyword
│   ├── semantic_cache.py            ← Tier 3: pgvector
│   ├── vector_semantic_cache.py     ← Implementação vetorial
│   ├── llm_cascade.py               ← Tier 5: Claude→Gemini→GPT
│   ├── memory_resolver.py           ← Tier 0: resolve referências
│   ├── main_orchestrator.py         ← Entry point principal
│   ├── intent_router.py             ← Classificação de intenção
│   ├── action_executor.py           ← Execução de ações
│   ├── task_planner.py              ← Planejamento de tarefas
│   ├── policy_engine.py             ← Engine de políticas
│   ├── state_manager.py             ← Gestão de estado
│   ├── tenant_budget.py             ← Budget por tenant
│   └── navigation_intent.py        ← Intents de navegação
│
├── domains/                         ← 13 DOMÍNIOS DE NEGÓCIO
│   ├── analytics/agents/
│   ├── ats_integration/agents/
│   ├── automation/agents/
│   ├── communication/agents/
│   ├── cv_screening/agents/         ← incl. wsi_interview_graph.py
│   ├── hiring_policy/agents/
│   ├── interview_scheduling/agents/ ← incl. interview_graph.py
│   ├── job_management/agents/       ← incl. job_wizard_graph.py
│   ├── pipeline/agents/
│   │   └── subagents/               ← Z1: 3 subagentes
│   ├── recruiter_assistant/agents/
│   │   └── subagents/               ← Z1: 3 subagentes
│   ├── sourcing/agents/
│   ├── policy/agents/               ← PolicyAgent canônico
│   └── talent_intelligence/         ← 13º domínio (Y-series)
│
├── shared/                          ← INFRA COMPARTILHADA DE IA (28+ arquivos)
│   ├── agents/                      ← Base classes
│   │   ├── langgraph_react_base.py
│   │   ├── working_memory.py
│   │   ├── long_term_memory.py
│   │   ├── autonomy_engine.py
│   │   ├── confidence.py
│   │   ├── proactive_worker.py
│   │   └── react_loop.py
│   ├── compliance/                  ← FAIRNESS + AUDITORIA
│   │   ├── fairness_guard.py        ← 3 camadas obrigatórias
│   │   ├── fact_checker.py
│   │   ├── audit_callback.py
│   │   └── audit_service.py
│   ├── learning/                    ← APRENDIZADO
│   │   └── learning_snapshot_service.py
│   ├── resilience/                  ← RESILIÊNCIA
│   │   ├── circuit_breaker.py       ← 15+ circuits
│   │   └── dlq_service.py           ← Dead Letter Queue Redis
│   ├── tracing.py                   ← OpenTelemetry OTLP
│   └── pii_masking.py               ← CPF, email + Presidio
│
├── services/                        ← SERVIÇOS (250+)
└── prompts/                         ← PROMPTS (YAML + Python)
    ├── shared/lia_persona.yaml
    └── domains/
```

---

### recruiter_agent_v5 — `src/` (lido do GitHub 19/03/2026)

```
src/
├── api.py                           ← FastAPI entry point
├── celery_app.py                    ← Celery configuration
│
├── agents/                          ← PIPELINE PRINCIPAL (6 agentes — fluxo original)
│   ├── intent_analyzer.py           ← Classifica intenção (RAG + Gemini)
│   ├── api_planner.py               ← Planeja chamadas API (51 YAMLs)
│   ├── api_executor.py              ← Executa chamadas HTTP
│   ├── plan_validator.py            ← Valida resultado
│   ├── data_processor.py            ← Estrutura dados
│   └── answer_formatter.py          ← Formata resposta
│
├── hub/                             ← CAMADA DE SESSÃO E ORQUESTRAÇÃO
│   ├── orchestrator.py              ← HubOrchestrator (sessão, planejamento, execução)
│   ├── planner.py                   ← HubPlanner (fast-path + CostLadder + LLM)
│   ├── supervisor_graph.py          ← LangGraph supervisor (domínio→router)
│   ├── supervisor_state.py          ← TypedDict do estado supervisor
│   ├── session.py                   ← ConversationSession (Redis)
│   └── domain_agent_node.py        ← Bridge hub→domain
│
├── domains/                         ← 8 DOMÍNIOS ESPECIALIZADOS (231 arquivos)
│   ├── registry.py                  ← DomainRegistry + @register_domain decorator
│   ├── orchestrator.py              ← DomainOrchestrator (audit + checkpointing)
│   ├── workflow.py                  ← DomainWorkflow: LangGraph intent→execute→format
│   ├── base.py                      ← DomainContext, DomainResponse, DomainPrompt
│   │
│   ├── jobs/                        ← CRUD de vagas
│   │   ├── domain.py
│   │   ├── api_client.py
│   │   ├── actions/                 ← search, details, analytics, bulk, create, update
│   │   ├── fairness.py              ← ← FAIRNESS EM VAGAS (verifica viés em JDs)
│   │   ├── memory.py                ← JobsConversationMemory
│   │   └── prompts.py
│   │
│   ├── applies/                     ← PIPELINE DE CANDIDATURAS
│   │   ├── domain.py
│   │   ├── api_client.py
│   │   ├── react_agent.py           ← ReAct agent LangGraph (MAX_ITERATIONS=12)
│   │   ├── actions/                 ← search, details, pipeline, scoring, bulk, comparison, analytics, sourcing, conversational
│   │   ├── memory.py                ← AppliesConversationMemory
│   │   ├── prompt_builder/          ← dynamic_builder, action_registry, domain_action
│   │   ├── formatters/              ← comparison, detail, table
│   │   ├── cache.py
│   │   └── cards.py
│   │
│   ├── sourced_profile_sourcing/    ← BUSCA E SOURCING (9 subagentes)
│   │   ├── agents/                  ← orchestrator, router, planner, search, detail, analytics, comparison, report, action
│   │   ├── actions/
│   │   ├── fairness.py              ← ← FAIRNESS EM SOURCING
│   │   ├── fact_checker.py          ← verifica contagens, médias, scores
│   │   └── memory.py
│   │
│   ├── scheduling/                  ← AGENDAMENTO DE ENTREVISTAS
│   │   ├── graph.py                 ← ← LangGraph multi-turno (SchedulingState TypedDict)
│   │   ├── domain.py
│   │   ├── api_client.py
│   │   ├── session.py               ← SchedulingSession (multi-turno)
│   │   ├── inference.py             ← InferenceEngine (parsing de horários)
│   │   ├── memory.py                ← SchedulingConversationMemory
│   │   └── formatters/              ← slots, confirmation
│   │
│   ├── evaluation/                  ← AVALIAÇÕES E ENTREVISTAS
│   │   ├── graph.py                 ← ← LangGraph: classify→evaluate→decide→craft
│   │   ├── state.py                 ← InterviewState TypedDict
│   │   ├── nodes.py                 ← classify_input, evaluate_response, decide_flow, craft_message
│   │   └── domain.py
│   │
│   ├── insights/                    ← MÉTRICAS E BRIEFINGS
│   │   ├── domain.py
│   │   ├── api_client.py
│   │   ├── actions/                 ← briefing, metrics, alerts, sector_benchmark
│   │   └── memory.py                ← InsightsConversationMemory
│   │
│   ├── messaging/                   ← COMUNICAÇÃO COM CANDIDATOS
│   │   ├── domain.py
│   │   ├── api_client.py
│   │   ├── actions/                 ← send_email, templates, check_history
│   │   └── memory.py                ← MessagingConversationMemory
│   │
│   └── autonomous/                  ← AGENTE REACT UNIVERSAL
│       ├── agent.py                 ← ← ReAct LangGraph (73+ tools, RetryPolicy)
│       ├── tools.py                 ← seleção dinâmica de tools por contexto
│       ├── api_client.py            ← UniversalAPIClient (lê 51 YAMLs)
│       ├── compression.py           ← compressão de contexto longo
│       ├── context_builder.py
│       ├── graph_nodes.py           ← nós do grafo autônomo
│       └── prompts.py
│
├── services/                        ← 51 SERVIÇOS TRANSVERSAIS
│   ├── memory/                      ← ← MEMÓRIA POR TENANT
│   │   ├── manager.py               ← MemoryManager (remember, recall, categorize)
│   │   ├── store.py                 ← TenantMemoryStore (PostgreSQL + pgvector 768d)
│   │   └── models.py                ← TenantMemory dataclass
│   ├── audit/                       ← ← AUDITORIA COMPLETA
│   │   ├── audit_callback.py        ← AuditCallbackHandler (LangChain callback)
│   │   ├── audit_models.py          ← AuditExecution, AuditEvent, AuditEventType
│   │   ├── audit_storage.py         ← JSONL storage em logs/audit/
│   │   └── audit_writer.py          ← PostgreSQL: tabela agent_executions
│   ├── circuit_breaker.py           ← ← CircuitBreaker (threshold, cooldown, reset)
│   ├── checkpointer.py              ← ← PostgresSaver + MemorySaver fallback
│   ├── embedding_service.py         ← Gemini embedding-001 (768 dims)
│   ├── semantic_cache.py            ← Cache semântico via Redis
│   ├── rag_service.py               ← RAG híbrido (semântico + textual)
│   ├── pii_filter.py                ← ← PII masking (CPF, email, phone) em logs
│   ├── security.py                  ← ← Injection detection + sanitização
│   ├── cost_ladder.py               ← CostLadder multi-tier routing
│   ├── model_router.py              ← ModelRouter (fast/default/heavy)
│   ├── llm_tracking_service.py      ← Tracking de tokens e custo por LLM
│   ├── llm_cache_service.py         ← Cache de respostas LLM
│   ├── proactive/                   ← ← ALERTAS PROATIVOS
│   │   ├── detector.py
│   │   ├── notifier.py
│   │   └── runner.py
│   ├── feedback/                    ← ← FEEDBACK TRACKER
│   │   └── tracker.py
│   ├── streaming_callback.py        ← Streaming de respostas
│   ├── react_observer.py            ← ReActObserver (rastreia tool calls)
│   ├── execution_tracker.py         ← ExecutionTracker (timing por step)
│   ├── thinking_message.py          ← ThinkingMessageService
│   ├── timed_node.py                ← _TimeoutError + node timeout
│   ├── sector_benchmark.py          ← Benchmarks por setor
│   ├── reference_resolver.py        ← Resolve referências ("ela", "aquela vaga")
│   ├── pending_action_store.py      ← Ações pendentes de confirmação (HITL)
│   ├── rabbitmq_service.py          ← RabbitMQ worker
│   ├── api_client.py                ← HTTP base client
│   └── rag_service.py               ← RAG com hybrid search
│
├── models/                          ← MODELOS DE ESTADO
│   ├── state.py                     ← QueryState TypedDict
│   ├── state/__init__.py
│   └── conversation_state.py        ← ConversationState
│
├── config/                          ← CONFIGURAÇÃO
│   ├── settings.py                  ← Settings singleton
│   └── memory_config.py
│
├── utils/                           ← UTILITÁRIOS
│   ├── llm_factory.py               ← create_tracked_llm() (factory principal)
│   └── message_sanitizer.py
│
└── docs/ (documentação interna)
    ├── ARQUITETURA_MULTI_AGENTE_DETALHADA.md
    ├── ANALISE_ADOCAO_PATTERNS_LIA.md
    ├── ARCHITECTURAL_AUDIT.md
    └── FUNCIONALIDADES.md
```

### 🔍 Análise de Mercado — Seção 3

**Pros LIA:**
- `shared/compliance/` como pasta de primeiro nível sinaliza que fairness não é um add-on
- `shared/providers/` com factory de LLMs garante ausência de vendor lock-in
- Separação explícita orchestrator / domains / shared segue DDD

**Contras LIA:**
- Dois lugares para serviços: `app/services/` (plana, 250+) e `domains/*/services/` — confusão sobre onde colocar código novo
- `app/services/ats_clients/` existe em dois lugares — duplicação de responsabilidade

**Pros v5:**
- `src/services/` consolidada (51 arquivos) vs 250+ espalhados na LIA
- Cada domínio é totalmente auto-contido: `domain.py`, `api_client.py`, `actions/`, `memory.py`, `prompts.py`
- `src/hub/` como camada explícita de sessão é um bounded context claro

**Contras v5:**
- `fairness.py` em dois domínios separados (jobs/, sourcing/) — deveria estar em `src/shared/`
- Sem pasta `shared/compliance/` — quando um 3º domínio precisar de fairness, vai duplicar código

**Recomendação para v5:**
1. Criar `src/shared/` com: `fairness/`, `pii/`, `audit/` (mover os arquivos existentes)
2. Mover `src/domains/jobs/fairness.py` e `src/domains/sourced_profile_sourcing/fairness.py` → `src/shared/fairness/`
3. Criar `src/shared/fairness/__init__.py` com `FairnessChecker` unificado

---

## 4. Orquestração e Roteamento

### Plataforma LIA — CascadedRouter (6 Tiers)

```
Usuário → main_orchestrator.py
             ↓
    [Tier 0] memory_resolver.py      → resolve "ele", "aquela vaga" (Zero custo)
             ↓ cache miss
    [Tier 1] LRU in-process          → hash MD5, O(1), sem Redis (Zero custo)
             ↓ cache miss
    [Tier 2] Redis hash cache         → distribuído, entre workers (Baixo custo)
             ↓ cache miss
    [Tier 3] semantic_cache.py        → pgvector cosine ≥ 0.92 (Baixo custo)
             ↓ cache miss
    [Tier 4] fast_router.py           → regex + keyword patterns (Baixo custo)
             ↓ sem match
    [Tier 5] llm_cascade.py           → Claude Haiku→Sonnet→Opus→Gemini→GPT-4o
             ↓
         domain_agent.py              → ReactAgent com tools especializadas
             ↓
    [Fallback] clarification_needed   → pergunta ao usuário
```

**Arquivos LIA:**
- `app/orchestrator/cascaded_router.py`
- `app/orchestrator/fast_router.py`
- `app/orchestrator/semantic_cache.py`
- `app/orchestrator/llm_cascade.py`
- `app/orchestrator/memory_resolver.py`

---

### recruiter_agent_v5 — Hub Architecture (3 Camadas)

```
Usuário (WebSocket/REST)
         ↓
    HubOrchestrator              ← src/hub/orchestrator.py
    (Redis Session Store)        ← ConversationSession por session_id
         ↓
    HubPlanner                   ← src/hub/planner.py
         ├── Fast-path: regex patterns → domínio direto (sem LLM)
         ├── CostLadder          ← src/services/cost_ladder.py
         │   ├── Tier: keywords → domain_id + confidence
         │   ├── Tier: multi-intent detection
         │   └── Tier: LLM fallback (Gemini)
         └── Supervisor LangGraph ← src/hub/supervisor_graph.py
                  ↓
    HubExecutor
         ↓
    DomainOrchestrator           ← src/domains/orchestrator.py
    (AuditCallback + Checkpointer)
         ↓
    DomainWorkflow (LangGraph)   ← src/domains/workflow.py
    StateGraph: intent → execute → format
         ↓
    Domain                       ← src/domains/{domain}/domain.py
    (process_intent → execute_action)
         ↓
    Rails API (Backend)
```

**Arquivos v5:**
- `src/hub/orchestrator.py` — HubOrchestrator (sessão, planejamento, execução)
- `src/hub/planner.py` — HubPlanner (fast-path + CostLadder + LLM)
- `src/hub/supervisor_graph.py` — LangGraph supervisor com DOMAIN_DESCRIPTIONS
- `src/hub/session.py` — ConversationSession (Redis + domain memories)
- `src/services/cost_ladder.py` — CostLadder com DOMAIN_KEYWORDS + ModelRouter
- `src/services/model_router.py` — ModelRouter (fast/default/heavy Gemini tiers)
- `src/services/reference_resolver.py` — resolve referências conversacionais
- `src/domains/orchestrator.py` — DomainOrchestrator
- `src/domains/workflow.py` — DomainWorkflow (LangGraph)

### Comparativo de Roteamento

| Aspecto | LIA | v5 |
|---|---|---|
| **Tipo** | Hierárquico 6-tier | Hub 3-camadas + CostLadder |
| **Cache semântico** | pgvector (cosine ≥ 0.92) | Redis semantic_cache.py |
| **Resolução de contexto** | memory_resolver.py | reference_resolver.py |
| **Roteamento por custo** | Haiku→Sonnet→Opus→Gemini→GPT | ModelRouter: fast/default/heavy Gemini |
| **Fallback** | clarification_needed | autonomous domain (ReAct universal) |
| **Multi-domínio** | 13 domínios mapeados | 8 domínios + autonomous fallback |
| **Framework** | LangGraph + custom | LangGraph (supervisor_graph) |
| **HITL** | hitl_service.request_approval() | pending_action_store.py |

### 🔍 Análise de Mercado — Seção 4

**Pros LIA:**
- 6 tiers com otimização de custo escalonada (Haiku→Opus) é o padrão "least capable model that meets requirements" — prática recomendada pela Anthropic
- Tier 0 (memory_resolver) para pronomes é sofisticação rara — a maioria manda contexto completo ao LLM

**Contras LIA:**
- 6 tiers aumentam latência acumulada e complexidade de debugging
- ✅ Threshold de cosine 0.92 agora configurável via `ROUTER_VECTOR_SIMILARITY_THRESHOLD` (Z5-03)

**Pros v5:**
- CostLadder com fallback para autonomous ReAct é uma estratégia elegante — se nenhum domínio tem certeza, o autonomous resolve
- ModelRouter (fast/default/heavy) é mais simples que 6 tiers com resultado similar para single-LLM

**Contras v5:**
- Zero otimização de custo entre providers (single-provider Gemini)
- Sem Tier 0 de resolução de referência — "ela" e "aquela vaga" vão para o LLM sem pré-processamento

**Recomendação para v5 — ALTA PRIORIDADE:**
1. Adicionar resolução de referências no HubPlanner (similar ao `memory_resolver.py` da LIA):
   ```python
   # src/hub/planner.py — adicionar antes do CostLadder
   from src.services.reference_resolver import ReferenceResolver
   resolved_query = ReferenceResolver.resolve(query, session.domain_memories)
   ```
2. Adicionar near-miss logging no CostLadder (confidence 0.5–0.7) para analisar onde o roteamento está errando
3. Configurar threshold do semantic_cache como envvar

---

## 5. Agentes por Domínio — Infográfico Completo

### Infográfico: LIA (23 agentes) vs v5 (domínios + agentes)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          PLATAFORMA LIA — 13 DOMÍNIOS / 23 AGENTES                      │
├──────────────────┬──────────────────────────────────────────────┬───────────┬───────────┤
│ DOMÍNIO          │ AGENTE PRINCIPAL                             │ TIPO      │ TOOLS     │
├──────────────────┼──────────────────────────────────────────────┼───────────┼───────────┤
│ Analytics        │ AnalyticsReactAgent                          │ ReAct     │ 8         │
│ ATS Integration  │ ATSIntegrationReactAgent                     │ ReAct     │ 7         │
│ Automation       │ AutomationReactAgent                         │ ReAct     │ 8         │
│ Communication    │ CommunicationReactAgent                      │ ReAct     │ 7         │
│ CV Screening     │ PipelineReactAgent                           │ ReAct     │ 16        │
│ CV Screening     │ WSIInterviewGraph                            │ StateGraph│ 3 nós     │
│ Hiring Policy    │ PolicyReactAgent (→shim Z5-02)               │ ReAct     │ 14        │
│ Interview Sched. │ InterviewGraph                               │ StateGraph│ 3 nós     │
│ Job Management   │ WizardReactAgent                             │ ReAct     │ 12        │
│ Job Management   │ JobWizardGraph                               │ StateGraph│ 4 nós     │
│ Pipeline (Z1)    │ PipelineTransitionAgent (supervisor)         │ ReAct     │ 22        │
│                  │  ├─ PipelineContextAgent                     │ Subagente │ 7         │
│                  │  ├─ PipelineDecisionAgent                    │ Subagente │ 8         │
│                  │  └─ PipelineActionAgent                      │ Subagente │ 7         │
│ Recruiter Asst.  │ KanbanReActAgent (supervisor Z1)             │ ReAct     │ 23        │
│                  │  ├─ KanbanSearchAgent                        │ Subagente │ 7         │
│                  │  ├─ KanbanInsightAgent                       │ Subagente │ 7         │
│                  │  └─ KanbanActionAgent                        │ Subagente │ 8         │
│ Recruiter Asst.  │ TalentReactAgent                             │ ReAct     │ 14        │
│ Recruiter Asst.  │ JobsMgmtReactAgent                           │ ReAct     │ 15        │
│ Sourcing         │ SourcingReactAgent                           │ ReAct     │ 17        │
│ Policy           │ PolicyAgent (canônico)                       │ StateGraph│ —         │
│ Talent Intel.    │ TalentIntelligenceAgent (Y-series)           │ ReAct     │ —         │
│ Sourcing Engage. │ SourcingEngagementGraph                      │ StateGraph│ 3 nós     │
├──────────────────┴──────────────────────────────────────────────┴───────────┴───────────┤
│ TOTAL: 12 ReAct + 4 StateGraph + 1 PolicySetup + 6 SubAgentes = 23 | 163 tools          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      recruiter_agent_v5 — 8 DOMÍNIOS + HUB LAYER                        │
├──────────────────┬──────────────────────────────────────────────┬───────────┬───────────┤
│ DOMÍNIO          │ AGENTE / CAMADA                              │ TIPO      │ TOOLS     │
├──────────────────┼──────────────────────────────────────────────┼───────────┼───────────┤
│ HUB (transversal)│ HubOrchestrator                              │ Orquestra │ —         │
│ HUB (transversal)│ HubPlanner (CostLadder + ModelRouter)        │ Router    │ —         │
│ HUB (transversal)│ SupervisorGraph (LangGraph)                  │ StateGraph│ —         │
│ Pipeline Global  │ IntentAnalyzerAgent                          │ Pipeline  │ RAG       │
│ Pipeline Global  │ APIPlannerAgent                              │ Pipeline  │ 51 YAMLs  │
│ Pipeline Global  │ APIExecutorAgent                             │ Pipeline  │ HTTP      │
│ Pipeline Global  │ PlanValidatorAgent                           │ Pipeline  │ —         │
│ Pipeline Global  │ DataProcessorAgent                           │ Pipeline  │ —         │
│ Pipeline Global  │ AnswerFormatterAgent                         │ Pipeline  │ —         │
│ Jobs             │ Domain + Actions (search, details, analytics)│ Domain    │ 6 actions │
│                  │  + fairness.py (viés em JDs)                 │           │           │
│ Applies          │ Domain + ReactAgent (MAX_ITER=12)            │ ReAct     │ 12 tools  │
│                  │  + Actions (scoring, pipeline, bulk, comp.)  │           │           │
│ Sourcing         │ SourcingOrchestrator (supervisor)            │ Orquestra │ —         │
│                  │  ├─ RouterAgent                              │ Subagente │ —         │
│                  │  ├─ PlannerAgent                             │ Subagente │ —         │
│                  │  ├─ SearchAgent                              │ Subagente │ 6 actions │
│                  │  ├─ DetailAgent                              │ Subagente │ —         │
│                  │  ├─ AnalyticsAgent                           │ Subagente │ —         │
│                  │  ├─ ComparisonAgent                          │ Subagente │ —         │
│                  │  ├─ ReportAgent                              │ Subagente │ —         │
│                  │  └─ ActionAgent                              │ Subagente │ —         │
│                  │  + fairness.py + fact_checker.py             │           │           │
│ Scheduling       │ SchedulingGraph (LangGraph multi-turno)      │ StateGraph│ API calls │
│                  │  SchedulingState TypedDict                   │           │           │
│                  │  InferenceEngine (parsing horários)          │           │           │
│ Evaluation       │ InterviewGraph (LangGraph)                   │ StateGraph│ 4 nós     │
│                  │  classify_input→evaluate→decide→craft        │           │           │
│ Insights         │ Domain + Actions (briefing, metrics, alerts) │ Domain    │ 4 actions │
│ Messaging        │ Domain + Actions (send_email, templates)     │ Domain    │ 4 actions │
│ Autonomous       │ ReActAgent (LangGraph, 73+ tools)            │ ReAct     │ 73+       │
│                  │  + compression + context_builder             │ Fallback  │           │
├──────────────────┴──────────────────────────────────────────────┴───────────┴───────────┤
│ TOTAL: 8 domínios | 4 grafos LangGraph | 2 ReAct (applies + autonomous) | 9 subagentes  │
│ ~30 agentes/camadas quando contados por responsabilidade                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Comparativo de Agentes por Domínio

| Domínio LIA | Domínio v5 | Grau de equivalência |
|---|---|---|
| Analytics | Insights | ✅ Parcial (insights/briefing/métricas) |
| ATS Integration | Autonomous (API universal) | ✅ Parcial (v5 via 51 YAMLs) |
| Automation | Autonomous | ⚠️ Parcial (v5 sem regras de automação) |
| Communication | Messaging | ✅ Similar (email + templates) |
| CV Screening | Applies (scoring) | ✅ Parcial (v5 tem scoring_overview) |
| Hiring Policy | Jobs (fairness.py) | ⚠️ Parcial (v5 sem compliance engine) |
| Interview Scheduling | Scheduling | ✅ Similar (ambos multi-turno com LangGraph) |
| Job Management | Jobs | ✅ Similar (CRUD + analytics) |
| Pipeline Transition | Applies (pipeline actions) | ✅ Similar |
| Recruiter Assistant (Kanban) | Applies + Insights | ✅ Parcial |
| Recruiter Assistant (Talent) | Sourcing | ✅ Similar |
| Sourcing | Sourcing (9 subagentes) | ✅ Equivalente (v5 mais robusto neste domínio) |
| Policy (Z5-02) | — | ❌ Não existe no v5 |
| Talent Intelligence | — | ❌ Não existe no v5 |

### 🔍 Análise de Mercado — Seção 5

**Sobre a pergunta "Só cobre sourcing":**
O documento anterior estava **errado**. O v5 cobre: jobs (CRUD + analytics), applies (pipeline completo + scoring), sourcing (9 subagentes), scheduling (multi-turno LangGraph), evaluation (LangGraph interview), insights (briefings + métricas), messaging (email + templates) e autonomous (73+ tools).

O v5 **não** cobre: policy/compliance engine, automation rules engine, talent intelligence avançado.

**Sobre "agentes próprios para clientes" (Eightfold/Phenom model):**

| O que o mercado faz | LIA hoje | v5 hoje | O que precisaria |
|---|---|---|---|
| Copilot Agents por persona | ✅ RecruiterBehaviorService (Z7-01) | ❌ Não tem | v5: adicionar perfil de usuário na sessão |
| Agent Studio (cliente cria agentes) | ❌ Não tem | ❌ Não tem | Ambos: UI + runtime de custom agents |
| Agentes por processo (R&S, performance) | ✅ 13 domínios | ✅ 8 domínios | Expandir domínios |
| Memória de persona do usuário | ✅ LongTermMemory | ✅ TenantMemoryStore | ✅ Ambos têm |

**Para oferecer "agentes próprios para clientes" (tipo Phenom X+ Studio):**
1. **LIA:** Criar endpoint de configuração de agente por tenant (`/api/v1/agents/configure`) que permita: customizar system prompt, adicionar/remover tools, configurar threshold de confiança — isso é possível com o `prompt_loader.py` existente (já tem override por tenant)
2. **v5:** Adicionar `tenant_config.py` no hub que carregue overrides de domínio por tenant: `{ "jobs": { "tools_enabled": ["search", "details"], "custom_prompt": "..." } }`

**Pros LIA:**
- 23 agentes cobrindo 13 domínios é cobertura funcional completa para ATS enterprise
- Subagentes Z1 mostram padrão de decomposição correto (supervisor + workers)
- RecruiterBehaviorService (Z7-01) é o primeiro passo para personalização por persona

**Contras LIA:**
- Sem "Agent Studio" — clientes não podem criar ou configurar agentes sem código

**Pros v5:**
- Os 9 subagentes de sourcing são altamente coesos (single responsibility)
- O autonomous ReAct com 73+ tools é o mais flexível — resolve qualquer query não mapeada
- A separação `planner → orchestrator → workers` é o padrão supervisor+workers do LangGraph

**Contras v5:**
- Sem policy/compliance engine — sem como aplicar regras de negócio por empresa
- Autonomous pode ser "over-used" — se o CostLadder errar o domínio, o autonomous resolve tudo mas com menor precisão

**Recomendação para v5:**
1. Criar `src/hub/tenant_config.py` com configurações por tenant lidas do Rails
2. Adicionar `policy/` domain para regras de negócio (ex: "não enviar email sem aprovação do gerente")
3. Criar meta-agente de "agent selection confidence" que mostra ao recrutador quando o sistema não tem certeza do domínio

---

## 6. Subagentes e Grafos LangGraph

### Plataforma LIA — Grafos LangGraph (5 StateGraphs)

| Grafo | Arquivo | Nós | Função |
|---|---|---|---|
| **WSI Interview Graph** | `cv_screening/agents/wsi_interview_graph.py` | generate_question → evaluate → score | Entrevista estruturada WSI |
| **Interview Graph** | `interview_scheduling/agents/interview_graph.py` | propose → confirm → notify | Agendamento inteligente |
| **Job Wizard Graph** | `job_management/agents/job_wizard_graph.py` | collect_info → enrich → validate → publish | Wizard de criação de vagas |
| **Sourcing Engagement** | `shared/agents/sourcing_engagement_nodes.py` | discover → contact → follow_up | Engajamento proativo |
| **Base State Machine** | `shared/agents/base_state_machine.py` | genérico | Base reutilizável |

### Sprint Z1 — 6 SubAgentes (19/03/2026) ✅

#### KanbanReActAgent → 3 Subagentes

| SubAgente | Arquivo | Função | Tools |
|---|---|---|---|
| **KanbanSearchAgent** | `recruiter_assistant/agents/subagents/kanban_search_agent.py` | Busca e filtro no Kanban | 7 |
| **KanbanInsightAgent** | `recruiter_assistant/agents/subagents/kanban_insight_agent.py` | Métricas e insights do pipeline | 7 |
| **KanbanActionAgent** | `recruiter_assistant/agents/subagents/kanban_action_agent.py` | Movimentação de candidatos | 8 |

#### PipelineTransitionAgent → 3 Subagentes

| SubAgente | Arquivo | Função | Tools |
|---|---|---|---|
| **PipelineContextAgent** | `pipeline/agents/subagents/pipeline_context_agent.py` | Leitura da etapa atual | 7 |
| **PipelineDecisionAgent** | `pipeline/agents/subagents/pipeline_decision_agent.py` | Avaliação e decisão | 8 |
| **PipelineActionAgent** | `pipeline/agents/subagents/pipeline_action_agent.py` | Execução + notificações | 7 |

---

### recruiter_agent_v5 — 4 Grafos LangGraph + 9 SubAgentes

#### Grafos LangGraph Confirmados

```
1. src/workflow/graph.py — WorkflowOrchestrator (pipeline de 6 agentes)
   ┌──────────────────────────────────────────────────────┐
   │ intent_analyzer → api_planner → api_executor         │
   │                                    ↓                 │
   │                   plan_validator ← →                 │
   │                       ↓                              │
   │ data_processor → answer_formatter → END              │
   └──────────────────────────────────────────────────────┘
   Nós: 6 | Edges condicionais: _should_continue, _should_continue_or_confirm,
             _should_replan_or_continue

2. src/hub/supervisor_graph.py — SupervisorGraph
   ┌──────────────────────────────────────────────────────┐
   │ Entrada → route_to_domain → domain_node → END        │
   │                ↓                                     │
   │          DOMAIN_DESCRIPTIONS dict (8 domínios)       │
   │          AuditCallbackHandler integrado               │
   └──────────────────────────────────────────────────────┘
   Usa: get_checkpointer() → PostgresSaver ou MemorySaver

3. src/domains/scheduling/graph.py — SchedulingGraph (multi-turno)
   ┌──────────────────────────────────────────────────────┐
   │ SchedulingState TypedDict                            │
   │ Nós: parse_input → check_slots → confirm → execute  │
   │ Edges condicionais: needs_more_input, CONFIRMATION   │
   └──────────────────────────────────────────────────────┘
   Suporta: multi-turno (pergunta faltante → espera usuário)
   Memória: SchedulingConversationMemory

4. src/domains/evaluation/graph.py — InterviewGraph (LangGraph)
   ┌──────────────────────────────────────────────────────┐
   │ InterviewState TypedDict                             │
   │ classify_input → [evaluate | decide_flow]            │
   │      evaluate → decide_flow → craft_message → END   │
   └──────────────────────────────────────────────────────┘
   Checkpointer: MemorySaver (by default)

5. src/domains/applies/react_agent.py — ReactAgent (LangGraph)
   ┌──────────────────────────────────────────────────────┐
   │ ReactState: messages (annotated list), iteration_count│
   │ MAX_ITERATIONS = 12                                  │
   │ Tools: search_candidates, search_jobs, ask_user,     │
   │        get_job_selective_processes, create_apply,    │
   │        api_request (genérica)                        │
   └──────────────────────────────────────────────────────┘

6. src/domains/autonomous/agent.py — AutonomousReAct (LangGraph)
   ┌──────────────────────────────────────────────────────┐
   │ 73+ tools selecionadas dinamicamente por contexto   │
   │ RetryPolicy integrada                                │
   │ Compression de contexto longo (compression.py)      │
   │ ExecutionTracker + ReActObserver                     │
   └──────────────────────────────────────────────────────┘
```

#### 9 SubAgentes de Sourcing

```
[router.py] → rota para o subagente correto
    ↓
[planner.py] → estratégia de busca
    ↓
[orchestrator.py] → coordena execução
    ├── [search.py]     → busca por skill/score/location/similar (embeddings)
    ├── [detail.py]     → aprofunda perfil
    ├── [analytics.py]  → métricas de sourcing
    └── [comparison.py] → compara candidatos
            ↓
        [report.py] → relatório estruturado
            ↓
        [action.py] → executa ações (invite, tag, pipeline)
```

**Diferença chave de checkpointing:**

| Aspecto | LIA | v5 |
|---|---|---|
| **Checkpointer** | `shared/agents/checkpointer.py` + PostgresSaver | `src/services/checkpointer.py` (PostgresSaver + MemorySaver fallback) |
| **Thread config** | thread_id por sessão | `build_thread_config(session_id, domain_id)` |
| **Estabilidade** | Produção | PostgresSaver instável (ARCHITECTURAL_AUDIT nota) — MemorySaver como default |

### 🔍 Análise de Mercado — Seção 6

**Resposta à pergunta "o v5 tem grafos ou LangGraph?":**
**Sim.** O v5 tem 6 grafos LangGraph confirmados no código:
1. `workflow/graph.py` — pipeline de 6 agentes com edges condicionais
2. `hub/supervisor_graph.py` — supervisor de domínios com checkpointing
3. `scheduling/graph.py` — multi-turno com `SchedulingState TypedDict`
4. `evaluation/graph.py` — entrevista com `InterviewState TypedDict`
5. `applies/react_agent.py` — ReAct com `ReactState` e `MAX_ITERATIONS=12`
6. `autonomous/agent.py` — ReAct universal com 73+ tools e `RetryPolicy`

O documento anterior estava **completamente errado** ao dizer que o v5 não usava LangGraph.

**Pros LIA:**
- LangGraph com grafos por domínio é estado da arte — Google, Amazon, Microsoft convergem para grafos com checkpointing
- Base State Machine compartilhado garante comportamento consistente entre grafos
- HITL integrado em SourcingReActAgent e CommunicationReActAgent (AUD-4) ✅

**Contras LIA:**
- 5 grafos para 13 domínios — maioria dos agentes usa ReAct simples quando poderiam se beneficiar de grafos

**Pros v5:**
- Scheduling como grafo multi-turno é a abordagem correta — mantém estado entre turnos de conversa sem reprocessar
- InterviewGraph com checkpointing (MemorySaver) permite retomar entrevistas interrompidas
- Autonomous com 73+ tools é o mais flexível do mercado para esse escopo

**Contras v5:**
- PostgresSaver instável (documentado no ARCHITECTURAL_AUDIT) — fallback para MemorySaver perde estado entre reinicios
- Sem HITL explícito em ações destrutivas (ex: criar candidatura sem confirmação no workflow geral — o applies/react_agent.py tem `ask_user` mas não é mandatório no hub)

**Recomendação para v5:**
1. Estabilizar PostgresSaver: criar migration SQL automática no startup + pooling de conexão dedicado
2. Adicionar HITL explícito no supervisor_graph para ações com `requires_confirmation=True`:
   ```python
   # src/hub/supervisor_graph.py — adicionar nó de confirmação
   workflow.add_conditional_edges(
       "domain_node",
       lambda state: "confirm" if state.get("requires_confirmation") else END,
       {"confirm": "confirmation_node", END: END}
   )
   ```
3. Criar grafo para o domínio de autonomous também — atualmente é ReAct puro sem checkpointing de sub-tarefas

---

## 7. Tool Registries (Ferramentas por Agente)

### Plataforma LIA — Registry Explícito por Domínio

| Domínio | Arquivo registry | Nº Tools | Exemplos |
|---|---|---|---|
| **Pipeline Transition** | `pipeline/agents/pipeline_tool_registry.py` | 22 | move_candidate, add_note, request_docs, schedule_interview |
| **Kanban (Recruiter)** | `recruiter_assistant/agents/kanban_tool_registry.py` | 23 | search_candidates, bulk_move, filter_stage, get_metrics |
| **Sourcing** | `sourcing/agents/sourcing_tool_registry.py` | 17 | search_external, enrich_profile, invite_to_apply |
| **CV Screening** | `cv_screening/agents/pipeline_tool_registry.py` | 16 | score_cv, extract_skills, check_requirements |
| **Hiring Policy** | `hiring_policy/agents/policy_tool_registry.py` | 14 | check_compliance, validate_jd, apply_affirmative |
| **Talent (Recruiter)** | `recruiter_assistant/agents/talent_tool_registry.py` | 14 | compare_candidates, get_profile, add_to_list |
| **Jobs Mgmt** | `recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | 15 | create_job, clone_job, update_status, get_analytics |
| **Job Wizard** | `job_management/agents/wizard_tool_registry.py` | 12 | generate_jd, enrich_requirements, suggest_salary |
| **Analytics** | `analytics/agents/analytics_tool_registry.py` | 8 | get_funnel, time_to_hire, diversity_metrics |
| **Automation** | `automation/agents/automation_tool_registry.py` | 8 | create_rule, trigger_action, schedule_task |
| **ATS Integration** | `ats_integration/agents/ats_integration_tool_registry.py` | 7 | sync_candidates, push_feedback, fetch_applications |
| **Communication** | `communication/agents/communication_tool_registry.py` | 7 | send_email, send_whatsapp, schedule_message |
| **TOTAL** | | **163 tools** | |

---

### recruiter_agent_v5 — Actions como Tool Registry Implícito

O v5 não usa `tool_registry.py` explícito. As tools são organizadas em `actions/` por domínio e como tools do autonomous.

#### Actions por Domínio (equivalente ao tool registry)

| Domínio | Pasta | Actions disponíveis |
|---|---|---|
| **Jobs** | `src/domains/jobs/actions/` | search, details, analytics, bulk, create, update |
| **Applies** | `src/domains/applies/actions/` | search, details, pipeline, scoring, bulk, comparison, analytics, sourcing, conversational |
| **Applies ReAct** | `src/domains/applies/react_agent.py` | search_candidates, search_jobs, ask_user, get_job_selective_processes, create_apply, api_request |
| **Sourcing** | `src/domains/sourced_profile_sourcing/agents/search.py` | search, filter_skill, filter_score, top_candidates, filter_location, find_similar (embeddings) |
| **Scheduling** | `src/domains/scheduling/graph.py` | check_available_slots, create_interview, confirm_scheduling |
| **Evaluation** | `src/domains/evaluation/nodes.py` | classify_input, evaluate_response, decide_flow, craft_message |
| **Insights** | `src/domains/insights/actions/` | briefing, metrics, alerts, sector_benchmark |
| **Messaging** | `src/domains/messaging/actions/` | send_email, check_history, list_templates |
| **Autonomous** | `src/domains/autonomous/tools.py` | 73+ tools selecionadas dinamicamente por contexto |

#### Autonomous — 51 APIs via YAML (documentados em `documentation/`)

```
applies_create.yml, applies_search.yml, applies_update.yml, applies_delete.yml
candidates_create.yml, candidates_search.yml, candidates_show.yml, candidates_update.yml, candidates_delete.yml
candidates_bulk_import_preview.yml
evaluations_create.yml, evaluations_search.yml, evaluations_update.yml, evaluations_delete.yml
evaluation_candidates_create.yml
experiences_create.yml, experiences_search.yml, experiences_show.yml, experiences_update.yml, experiences_delete.yml
jobs_create.yml, jobs_search.yml, jobs_show.yml, jobs_update.yml, jobs_delete.yml
jobs_journey.yml, jobs_status_search.yml, jobs_template_fields_search.yml
job_field_templates_create.yml, job_field_templates_search.yml, job_field_templates_update.yml, job_field_templates_delete.yml
job_journeys_create.yml, job_journeys_search.yml, job_journeys_update.yml, job_journeys_delete.yml
list_relationships_create.yml, list_relationships_create_collection.yml
lists_search.yml ... (51 total)
```

### 🔍 Análise de Mercado — Seção 7

**Pros LIA:**
- Registry explícito (`tool_registry.py`) é melhor prática — facilita auditoria, testes unitários e documentação automática
- 163 tools documentadas permitem geração automática de manifesto de capacidades

**Contras LIA:**
- Sem `tool_manifest.json` gerado automaticamente — exige leitura de código para saber o que o agente faz
- ✅ RESOLVIDO Z1: subagentes com 7–8 tools cada vs. 22–23 antes

**Pros v5:**
- `documentation/*.yml` são essencialmente um tool registry legível por humanos e máquinas — 51 APIs documentadas em YAML é uma abordagem excelente
- `tools.py` no autonomous com seleção dinâmica por contexto é mais eficiente que carregar todas as tools sempre

**Contras v5:**
- Sem registry explícito = sem visibilidade do que cada domain agent pode fazer sem ler o código
- Tools dinâmicas (51 YAMLs lidos em runtime) são difíceis de testar unitariamente

**Recomendação para v5 — Criar Tool Registry Explícito:**
```python
# CRIAR: src/domains/jobs/tool_registry.py
from dataclasses import dataclass
from typing import List

@dataclass
class ToolSpec:
    name: str
    description: str
    params: dict
    requires_confirmation: bool = False

JOBS_TOOLS: List[ToolSpec] = [
    ToolSpec("search_jobs", "Busca vagas por critérios", {"query": "str", "status": "str"}, False),
    ToolSpec("get_job_details", "Detalhes de uma vaga", {"job_id": "int"}, False),
    ToolSpec("create_job", "Cria nova vaga", {"title": "str", "description": "str"}, True),
    # ... demais actions
]

# PARA CADA DOMÍNIO: criar tool_registry.py similar
# Isso permite: auditoria, testes, documentação automática, fairness check por tool
```

---

## 8. Serviços de IA/ML

### Comparativo de Serviços de IA/ML

| Serviço | LIA | v5 |
|---|---|---|
| **Embeddings** | `cv_matching_service.py` (skills matching) | `embedding_service.py` (Gemini embedding-001, 768d) |
| **Cache semântico** | `semantic_cache.py` (pgvector cosine) | `semantic_cache.py` (Redis) |
| **RAG** | `rag_service.py` (documentos da vaga) | `rag_service.py` (busca híbrida: semântica + textual, psycopg2+pgvector) |
| **Scoring de candidatos** | `cv_screening_service.py` + `scoring_service.py` | `applies/actions/scoring.py` (scoring_overview, best_fit_analysis) |
| **Model routing** | `llm_cascade.py` (multi-provider) | `model_router.py` (fast/default/heavy Gemini) |
| **Tracking de tokens** | `ai_consumption.py` (por tenant) | `llm_tracking_service.py` (por chamada) |
| **LLM cache** | Redis + LRU in-process | `llm_cache_service.py` (Redis) |
| **Benchmarks de setor** | `sector_benchmark_service.py` | `sector_benchmark.py` |
| **Streaming** | `streaming_callback.py` | `streaming_callback.py` |
| **Drift detection** | `model_drift_service.py` (job diário) | Não |
| **A/B testing** | `ab_testing_service.py` | Não |
| **Scoring ML** | `ml_feedback_service.py` + finetuning | Não |
| **Qualidade RAGAS** | `ragas_evaluation_service.py` | Não |
| **Explicabilidade** | `agent_explainability.py` | Não |
| **Proactive alerts** | `proactive_worker.py` | `proactive/detector.py` + notifier + runner |
| **Fact checker** | `shared/compliance/fact_checker.py` | `sourcing/fact_checker.py` |

**Arquivos LIA:**
- `app/services/cv_screening_service.py`
- `app/services/scoring_service.py`
- `app/services/model_drift_service.py`
- `app/shared/ab_testing.py`
- `app/services/ragas_evaluation_service.py`
- `app/services/agent_quality_evaluator.py`

**Arquivos v5:**
- `src/services/embedding_service.py` — Gemini gemini-embedding-001, 768 dims
- `src/services/semantic_cache.py` — Redis
- `src/services/rag_service.py` — híbrido (semântico + keyword)
- `src/services/model_router.py` — ModelRouter(fast, default, heavy)
- `src/services/llm_tracking_service.py`
- `src/services/llm_cache_service.py`
- `src/services/sector_benchmark.py`
- `src/services/proactive/detector.py`

### 🔍 Análise de Mercado — Seção 8

**Pros LIA:**
- Drift detection diário + RAGAS + explicabilidade são os serviços mais avançados — a maioria das startups de HR Tech não tem nada disso
- A/B testing de prompts com controle de fairness (Sprint F1-02) é muito avançado

**Contras LIA:**
- Sem scoring de candidatos baseado em embeddings — o `cv_screening_service.py` usa regras, não vetores

**Pros v5:**
- Embedding service com pgvector integrado ao memory store e ao RAG é uma arquitetura coesa
- RAG híbrido (semântico + textual) é a abordagem que melhores resultados dá — idêntico ao que Retrieval Augmented Generation researchers recomendam
- Proactive detector + notifier + runner é uma arquitetura de 3 camadas bem separada

**Contras v5:**
- Sem drift detection — o sistema não sabe quando a qualidade das respostas está piorando
- Sem RAGAS ou avaliação de qualidade — "cego" para qualidade de respostas
- Sem scoring de candidatos baseado em ML — usa score da API Rails, não calcula internamente
- Sem A/B testing

**Recomendação para v5 — Passo a passo para adicionar drift detection (ver Seção 20):**
1. Criar `src/services/quality_tracker.py` que salva métricas de qualidade por sessão
2. Criar job Celery `src/tasks/quality_drift_job.py` que roda diariamente
3. Integrar com `audit_writer.py` existente para acessar histórico de execuções

---

## 9. Memória e Estado

### Plataforma LIA — Working Memory + Long Term Memory

```
Memória LIA
├── WorkingMemory (in-session)          ← shared/agents/working_memory.py
│   └── estado da conversa atual
├── LongTermMemory (cross-session)      ← shared/agents/long_term_memory.py
│   └── preferências e histórico do recrutador
├── LangGraph Checkpointer              ← shared/agents/checkpointer.py
│   └── estado dos grafos (PostgresSaver)
└── PostgreSQL                          ← modelos SQLAlchemy
    ├── tenant_memories (por empresa)
    └── agent_execution_logs
```

**Arquivos LIA:**
- `app/shared/agents/working_memory.py`
- `app/shared/agents/long_term_memory.py`
- `app/shared/agents/checkpointer.py`
- `app/shared/agents/memory_integration.py`

---

### recruiter_agent_v5 — Sistema de Memória Completo

> **Correção (19/03/2026):** O v5 tem sistema de memória substancial com PostgreSQL + pgvector. A afirmação "sem persistência" e "recrutador que volta no dia seguinte precisa repetir tudo" estava **completamente errada**.

```
Memória v5
├── ConversationSession (in-session)      ← src/hub/session.py
│   ├── session_id → Redis
│   └── domain_memories dict (por domínio)
│       ├── AppliesConversationMemory     ← src/domains/applies/memory.py
│       ├── JobsConversationMemory        ← src/domains/jobs/memory.py
│       ├── InsightsConversationMemory    ← src/domains/insights/memory.py
│       ├── MessagingConversationMemory   ← src/domains/messaging/memory.py
│       ├── SchedulingConversationMemory  ← src/domains/scheduling/memory.py
│       └── SourcingConversationMemory    ← src/domains/sourced_profile_sourcing/memory.py
│
├── TenantMemoryStore (cross-session)     ← src/services/memory/store.py
│   ├── PostgreSQL: tabela tenant_memories
│   ├── pgvector: embedding column (768 dims, Gemini)
│   ├── TTL: 30 dias por padrão
│   ├── Max: 500 memórias por tenant
│   └── Dedup: similaridade > 0.92 não duplica
│
├── MemoryManager                         ← src/services/memory/manager.py
│   ├── remember(tenant_id, content, category)  → salva com embedding
│   ├── recall(tenant_id, query, limit=5)        → busca semântica
│   └── categorias: hiring_preference, workflow_pattern, entity_insight, search_pattern
│
└── LangGraph Checkpointer               ← src/services/checkpointer.py
    ├── PostgresSaver (CHECKPOINTER_BACKEND=postgres)
    └── MemorySaver (fallback/default)
```

**Categorias de memória automáticas (auto-detectadas):**
| Categoria | Palavras-chave | Exemplo salvo |
|---|---|---|
| `hiring_preference` | preferencia, prefiro, gosto de | "prefiro candidatos com inglês fluente" |
| `workflow_pattern` | sempre, toda vez, fluxo | "sempre peço aprovação do gestor antes de avançar" |
| `entity_insight` | vaga, candidato, departamento | "vaga 7144 tem 3 etapas" |
| `search_pattern` | buscar, procurar, filtrar | "filtro padrão: score > 80, Python" |

### Comparativo de Memória

| Aspecto | LIA | v5 |
|---|---|---|
| **Memória in-session** | WorkingMemory | ConversationSession (Redis) + domain_memories por domínio |
| **Memória cross-session** | LongTermMemory (PostgreSQL) | TenantMemoryStore (PostgreSQL + pgvector 768d) |
| **TTL** | Não documentado | 30 dias (configurável em `DEFAULT_TTL_DAYS`) |
| **Busca semântica** | Sim (pgvector) | Sim (pgvector + Gemini embedding-001) |
| **Checkpointing** | PostgresSaver | PostgresSaver + MemorySaver fallback |
| **Categorização** | Por domínio | Auto-categorizadas (4 categorias) |
| **Dedup** | Não documentado | Threshold 0.92 — não duplica memórias similares |
| **Limite por tenant** | Não documentado | MAX_MEMORIES_PER_TENANT = 500 |

### 🔍 Análise de Mercado — Seção 9

**Pros LIA:**
- LongTermMemory com histório de múltiplas sessões é mais rico semanticamente
- Integração mais explícita com o orchestrator (memory_resolver.py resolve referências em Tier 0)

**Contras LIA:**
- Sem TTL documentado nas memórias — risco de acumulação indefinida de dados PII
- Sem dedup automático — mesma informação pode ser armazenada múltiplas vezes

**Pros v5:**
- TenantMemoryStore com TTL, dedup por similaridade e limite de 500 entradas é mais seguro que a LIA
- pgvector + Gemini embedding-001 é a implementação mais clean para busca semântica de memória
- Categorização automática por keywords é elegante sem precisar de LLM adicional

**Contras v5:**
- PostgresSaver instável (ARCHITECTURAL_AUDIT diz: "checkpointing nota 3/10") — perde estado entre reinicios
- Sem recall cross-domain — cada domain memory vive em silo
- Sem summary de memórias antigas — quando chega em 500 entradas, as mais antigas são apagadas sem resumo

**Recomendação para v5:**
1. Estabilizar PostgresSaver (prioridade ALTA — veja Seção 20, item V-09)
2. Criar `MemorySummarizer` que ao atingir 80% do limite (400/500) resume os mais antigos:
   ```python
   # src/services/memory/summarizer.py
   class MemorySummarizer:
       def summarize_oldest(self, tenant_id: int, count: int = 50) -> str:
           oldest = self._store.get_oldest(tenant_id, count)
           summary = self._llm.invoke(f"Resuma em 1 parágrafo: {oldest}")
           self._store.replace_batch(oldest, summary)
   ```
3. Adicionar recall cross-domain: quando a sessão muda de domínio, carregar memórias relevantes do tenant store

---

## 10. Prompts e Persona

### Comparativo de Gestão de Prompts

| Aspecto | LIA | v5 |
|---|---|---|
| **Gestão de prompts** | YAML externo + registry + override por tenant | `prompts.py` por domínio (Python) + `v5_persona.yaml` |
| **Formato** | YAML (`.yaml`) + Python (`.py`) — misto | Python (`.py`) — constantes de classe |
| **Anti-sycophancy** | Bloco estruturado em todos os prompts | Não implementado |
| **Few-shot** | 3 arquivos dedicados (orchestrator, pipeline, sourcing) | Não dedicado |
| **Override por empresa** | Sim (`prompt_loader.py` com `tenant_id`) | Não |
| **Chain-of-thought** | Estruturado (`cot.py`) | Implícito nos prompts |
| **Versionamento** | ✅ Z3-02: `version` + `updated_at` em 9 YAMLs | Git (commit hash como versão implícita) |
| **Prompt Builder dinâmico** | Não (prompts estáticos) | `applies/prompt_builder/` — construção dinâmica por contexto |

**Arquivos LIA:**
- `app/prompts/shared/lia_persona.yaml`
- `app/shared/prompts/prompt_registry.py`
- `app/shared/prompts/loader.py`
- `libs/contexts/*.yaml` (9 YAMLs com version + updated_at)

**Arquivos v5:**
- `src/domains/{domain}/prompts.py` — prompt de sistema por domínio
- `src/domains/applies/prompt_builder/` — AppliesDynamicPromptBuilder, PromptConfig, AppliesActionRegistry
  - `dynamic_builder.py` — build_system_prompt() + build_intent_prompt()
  - `action_registry.py` — registro de actions com exemplos
  - `domain_action.py` — DomainAction dataclass
- `v5_persona.yaml` — persona do assistente v5
- `.github/instructions/langchain-prompts.instructions.md` — guia de prompts para Copilot

**Destaque v5 — AppliesDynamicPromptBuilder:**
```python
# src/domains/applies/prompt_builder/dynamic_builder.py
# Constrói prompt dinâmico baseado em:
# - contexto do job (tem job_id ou não)
# - actions disponíveis (max 8 no prompt)
# - exemplos por action (max 2 por action)
# - modo compacto ou completo
class AppliesDynamicPromptBuilder:
    def build_system_prompt(self, job_id, has_job_context) -> str
    def build_intent_prompt(self, query, all_actions) -> str
```

### 🔍 Análise de Mercado — Seção 10

**Pros LIA:**
- YAML externo + loader + override por tenant é exatamente o que Langfuse oferece como enterprise feature
- Anti-sycophancy como bloco reutilizável é sofisticação que poucas empresas documentam
- Few-shot por domínio melhora significativamente a qualidade
- ✅ Versionamento implementado (Z3-02)

**Contras LIA:**
- Prompts em Python (.py) misturados com YAML (.yaml) — inconsistência
- Sem sistema de avaliação automática (métricas por versão pendentes)

**Pros v5:**
- `AppliesDynamicPromptBuilder` é o componente de prompt mais sofisticado do v5 — construção contextual baseada em availables actions e contexto do job
- Prompts em `prompts.py` por domínio são fáceis de encontrar — sabe exatamente onde está o prompt de cada agente

**Contras v5:**
- Hardcoded em Python = impossível customizar por cliente sem alterar código
- Sem anti-sycophancy — LLMs podem concordar com o usuário mesmo quando a resposta está errada
- Sem versionamento explícito (depende de Git commit hash)
- Sem few-shot estruturado nos prompts

**Recomendação para v5:**
1. Adicionar bloco anti-sycophancy em todos os prompts de sistema:
   ```python
   # Adicionar em src/domains/*/prompts.py — no sistema de todos os domínios
   ANTI_SYCOPHANCY_BLOCK = """
   IMPORTANTE: Seja direto e preciso. Não concorde com o usuário quando os dados mostram
   o contrário. Se um candidato tem score 45 e o usuário diz "ele é excelente",
   informe o score real e deixe o usuário decidir. Prefira dados a opiniões.
   """
   ```
2. Criar `src/shared/prompts/` com:
   - `base_system_prompt.py` — bloco compartilhado (anti-sycophancy + HITL rules)
   - `prompt_versioner.py` — versão baseada em hash do conteúdo
3. Externalizar prompts para YAML para facilitar customização por cliente

---

## 11. Fairness e Compliance de IA

### Plataforma LIA — FairnessGuard 3 Camadas (Obrigatório)

```
Camada 1: Pre-Decision Guard  → fairness_guard.py → block_if_biased()
Camada 2: In-Process Monitor  → audit_callback.py → log_decision()
Camada 3: Post-Decision Audit → admin_bias_audit.py → four_fifths_rule()
                                  └── test_four_fifths_rule.py
```

**Arquivos LIA:**
- `app/shared/compliance/fairness_guard.py` — 3 camadas obrigatórias
- `app/shared/compliance/fact_checker.py`
- `app/shared/compliance/audit_callback.py`
- `app/api/v1/admin_bias_audit.py` — dashboard + regra 4/5
- `docs/compliance/FRIA_WSI.md` — FRIA documentado

---

### recruiter_agent_v5 — Fairness em 2 Domínios

> **Correção (19/03/2026):** O v5 tem fairness em **2 domínios** (jobs + sourcing), não apenas sourcing. E tem `fact_checker.py` com 3 métodos de verificação.

**Arquivos v5:**

| Arquivo | Domínio | O que faz |
|---|---|---|
| `src/domains/jobs/fairness.py` | Jobs | Verifica viés em job descriptions (termos como "boa aparência", "jovem", "loiro") |
| `src/domains/sourced_profile_sourcing/fairness.py` | Sourcing | Verifica viés em filtros de busca de candidatos |
| `src/domains/sourced_profile_sourcing/fact_checker.py` | Sourcing | `verify_count_claim()`, `verify_average_claim()`, `verify_score_claim()` |
| `tests/test_fairness.py` | — | Testes de fairness |
| `tests/test_fact_checker.py` | — | Testes de fact checking |

**Detalhe: jobs/fairness.py** — verifica termos de viés em JDs antes de criar vagas no Rails. Se detectar "boa aparência", "bairros nobres", "universidade de primeira linha", bloqueia ou alerta o recrutador.

**Detalhe: fact_checker.py** — 3 verificações numéricas:
- `verify_count_claim(claimed_count, actual_data)` — se LLM disse "20 candidatos" mas são 18, corrige
- `verify_average_claim(claimed_avg, data, field)` — verifica médias com tolerância configurável
- `verify_score_claim(claimed_score, actual_score)` — verifica scores de candidatos

### Comparativo de Fairness

| Aspecto | LIA | v5 |
|---|---|---|
| **FairnessGuard estruturado** | Sim — 3 camadas obrigatórias | Não — fairness por domínio, não obrigatória |
| **Regra 4/5 (EEOC)** | Implementada + testada | Não |
| **Anti-alucinação (fact_checker)** | Em todos os domínios | Só em sourcing |
| **Dashboard de auditoria** | Sim (admin_bias_audit.py) | Não |
| **Explicabilidade** | API por decisão | Não |
| **FRIA documentado** | Sim (FRIA_WSI.md) | Não |
| **Fairness em job descriptions** | Sim (FairnessGuard) | Sim (jobs/fairness.py) |
| **Fairness em sourcing** | Sim (FairnessGuard) | Sim (sourcing/fairness.py) |
| **Testes de fairness** | `test_four_fifths_rule.py` | `test_fairness.py`, `test_fact_checker.py` |

### 🔍 Análise de Mercado — Seção 11

**Pros LIA — PONTO FORTE MÁXIMO:**
- NYC Local Law 144 (vigente 2023) exige auditoria de disparate impact — a LIA já implementa `four_fifths_rule()` — HireVue foi multado exatamente por não ter isso
- Fairness como camada 1 (pre-decision) é raro no mercado — a maioria faz fairness post-hoc
- FRIA documentado é o que a EU AI Act exige para sistemas de IA de alto risco

**Contras LIA:**
- Sem red teaming automatizado — nenhum processo de testar a FairnessGuard com inputs adversariais
- Sem relatório de fairness exportável para auditores externos (NYC LL144 requer isso)

**Pros v5:**
- Fairness em JDs (jobs/fairness.py) e fairness em filtros de sourcing mostra consciência do problema
- FactChecker com 3 verificações numéricas é uma boa proteção contra alucinação

**Contras v5:**
- Fairness não obrigatória — em produção no Brasil/EUA/Europa, risco legal sério
- Sem regra 4/5 (EEOC) — não pode fazer auditoria de disparate impact
- Sem dashboard de auditoria — dados de fairness não são visíveis para gestão

**Recomendação para v5 — Passo a passo para implementar FairnessGuard básico:**

**Passo 1:** Criar `src/shared/fairness/guard.py`:
```python
# CRIAR: src/shared/fairness/guard.py
import re
from typing import List, Tuple

BIAS_TERMS = [
    (r"\bboa aparência\b", "aparência física não é critério legal de seleção"),
    (r"\bjovem\b", "referência a idade pode ser discriminatória"),
    (r"\brecém-formado\b", "pode excluir candidatos mais experientes"),
    (r"\buniversidade de primeira linha\b", "critério de prestígio pode ser discriminatório"),
    (r"\bbairros nobres\b", "localização pode excluir por renda"),
]

def check_job_description_bias(jd: str) -> Tuple[bool, List[str]]:
    """Retorna (has_bias, [motivos])"""
    flags = []
    for pattern, reason in BIAS_TERMS:
        if re.search(pattern, jd, re.IGNORECASE):
            flags.append(reason)
    return len(flags) > 0, flags
```

**Passo 2:** Integrar no `src/domains/jobs/fairness.py` (já existe, ampliar):
```python
# MODIFICAR: src/domains/jobs/fairness.py
from src.shared.fairness.guard import check_job_description_bias

class JobsFairnessChecker:
    def validate_job_description(self, jd: str) -> dict:
        has_bias, reasons = check_job_description_bias(jd)
        return {
            "approved": not has_bias,
            "bias_detected": has_bias,
            "reasons": reasons,
            "recommendation": "Revise os termos destacados antes de publicar" if has_bias else "JD aprovada"
        }
```

**Passo 3:** Criar `src/services/audit/fairness_audit.py` (logging de decisões para dashboard futuro):
```python
# CRIAR: src/services/audit/fairness_audit.py
import json, logging
from datetime import datetime

logger = logging.getLogger("fairness_audit")

class FairnessAuditLogger:
    def log_decision(self, domain: str, action: str, input_data: dict, bias_detected: bool, reasons: list):
        logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "domain": domain,
            "action": action,
            "bias_detected": bias_detected,
            "reasons": reasons,
        }))
```

**Passo 4:** Adicionar teste de fairness obrigatório no CI:
```python
# CRIAR: tests/test_fairness_guard.py
from src.shared.fairness.guard import check_job_description_bias

def test_detects_appearance_bias():
    jd = "Procuramos candidato de boa aparência para trabalhar com clientes"
    has_bias, reasons = check_job_description_bias(jd)
    assert has_bias == True
    assert len(reasons) > 0

def test_approves_neutral_jd():
    jd = "Procuramos desenvolvedor Python com 3 anos de experiência"
    has_bias, reasons = check_job_description_bias(jd)
    assert has_bias == False
```

---

## 12. PII e Proteção de Dados

### Plataforma LIA — LGPD Compliance Completo

| Componente | LIA | v5 |
|---|---|---|
| **PII Masking (LLM prompt)** | `pii_masking.py` + Presidio NER Layer 4 | `pii_filter.py` (CPF, email, phone em logs) |
| **Injection Protection** | Não documentado explicitamente | `security.py` — 20+ padrões de injection |
| **Consentimento** | `consent_checker_service.py` + `granular_consent_service.py` | Não (Rails gerencia) |
| **DSR (direito ao esquecimento)** | `dsr_export_service.py` | Não |
| **LGPD Cleanup** | `lgpd_cleanup_service.py` | Não |
| **Admin LGPD** | `admin_lgpd.py` | Não |
| **Audit Trail** | `audit_callback.py` | `audit_callback.py` + `audit_writer.py` |
| **PII em logs** | Presidio + regex | PIIMaskingFilter em logging root |
| **Sanitização de input** | — | `sanitize_input()` + `MAX_SAFE_LENGTH=4000` |

**Arquivos LIA:**
- `app/shared/pii_masking.py`
- `app/services/consent_checker_service.py`
- `app/services/dsr_export_service.py`
- `app/services/lgpd_cleanup_service.py`
- `app/api/v1/admin_lgpd.py`

**Arquivos v5:**
```python
# src/services/pii_filter.py — PII em logs
_PII_PATTERNS = [
    (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    (re.compile(r'\b[\w.+-]+@[\w.-]+\.\w{2,}\b'), '[EMAIL]'),
    (re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}\b'), '[PHONE]'),
]
# PIIMaskingFilter aplicado no logging.root — TODOS os logs são mascarados

# src/services/security.py — Injection detection
INJECTION_PATTERNS = [
    r"ignore\s+(previous\s+|all\s+)*instructions?",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"jailbreak", r"dan\s*mode", r"developer\s*mode",
    r"esque[çc]a\s+tudo", r"agora\s+voc[êe]\s+[ée]",
    # ... 20+ padrões PT/EN
]
# detect_injection() retorna (bool, pattern_matched)
# safe_process_input() = sanitize + detect_injection + truncate (4000 chars)
```

### 🔍 Análise de Mercado — Seção 12

**Pros LIA:**
- LGPD compliance completo (consentimento granular, DSR, cleanup) é exigência legal no Brasil
- Presidio Layer 4 para NER em texto livre (currículos, descrições) é o estado da arte
- ✅ Presidio integrado (Sprint Z6-03): controlado por `LLM_PROMPT_PRESIDIO_ENABLED`

**Contras LIA:**
- Sem TTL automático nos dados de conversa — PII pode ficar indefinidamente no banco
- Sem criptografia de campo para CPF/email no PostgreSQL

**Pros v5:**
- `security.py` com 20+ padrões de injection detection PT/EN é mais completo que a maioria das plataformas
- `PIIMaskingFilter` no logging root garante que NENHUM log vaza PII — proteção mais profunda que regex só em prompts
- `MAX_SAFE_LENGTH=4000` previne prompt injection por overflow

**Contras v5:**
- Sem consentimento granular — violação potencial da LGPD Art. 7 para qualquer dado processado
- Sem DSR — candidatos não têm como solicitar exportação ou deleção dos dados
- Sem LGPD cleanup automático — dados ficam no banco indefinidamente

**Recomendação para v5 — PII e LGPD mínimo viável:**
1. Mover `pii_filter.py` para prompts (não só logs): adicionar mascaramento antes de enviar ao Gemini
2. Adicionar TTL nas `tenant_memories`: já existe `expires_at` no schema — implementar rotina de limpeza:
   ```python
   # CRIAR: src/tasks/lgpd_cleanup_task.py
   @celery_app.task
   def cleanup_expired_memories():
       with db.connect() as conn:
           conn.execute("DELETE FROM tenant_memories WHERE expires_at < NOW()")
   # Registrar no beat_schedule: diário às 3h
   ```
3. Delegar LGPD para Rails (rota mais prática): criar endpoint webhook `POST /v5/lgpd/delete-user` que o Rails chama quando candidato solicita deleção, e o v5 apaga as `tenant_memories` do tenant

---

## 13. Resiliência e Fallback de LLM

### Comparativo de Resiliência

| Componente | LIA | v5 |
|---|---|---|
| **Circuit Breaker** | 15+ circuits com SLOs (threshold=5, window=60s) | `circuit_breaker.py` — threshold configurável, cooldown, reset_all |
| **Timeout por nó** | `timed_tool_node.py` | `timed_node.py` — _TimeoutError |
| **Retry policy** | Celery + LangChain | LangGraph `RetryPolicy` no autonomous |
| **LLM Cascade** | Claude Haiku→Sonnet→Opus→Gemini→GPT-4o | Não (single-provider Gemini) |
| **Dead Letter Queue** | ✅ DLQService (Sprint F2-04) | Não |
| **Degraded mode** | ✅ Sprint F1-03 — respostas pré-programadas | Não |
| **Cache de fallback** | Sim (resposta cacheada) | `llm_cache_service.py` (Redis) |
| **Métricas de circuit** | Sim (`stats_manager.py` + admin endpoint) | Não |
| **Testes de circuit breaker** | Sim | `tests/test_circuit_breaker.py` + `test_circuit_breaker_integration.py` |

**Circuits LIA (15+):**
`CLAUDE`, `GEMINI`, `OPENAI`, `GUPY`, `PANDAPE`, `STACKONE`, `SENDGRID`, `RESEND`, `WORKOS`, `PEARCH`, `DEEPGRAM`, `WHATSAPP`, `TEAMS`, `REDIS`, `DB`

**Circuit Breaker v5 (global):**
```python
# src/services/circuit_breaker.py
class CircuitBreaker:
    DEFAULT_FAILURE_THRESHOLD = 5  # configurable
    # record_failure(), record_success(), is_open()
    # reset_all() para testes
    # get_state(key, threshold, cooldown)
```

### 🔍 Análise de Mercado — Seção 13

**Pros LIA:**
- 15+ circuits com SLOs formais é systems design de referência (Netflix Hystrix pattern)
- Cascade multi-provider é uma das poucas implementações documentadas em HR AI
- ✅ Degraded mode e DLQ implementados

**Contras LIA:**
- Sem chaos engineering — não há testes que deliberadamente falham providers

**Pros v5:**
- Circuit breaker com testes (`test_circuit_breaker.py`, `test_circuit_breaker_integration.py`) é melhor que ter circuit breaker sem testes
- LangGraph `RetryPolicy` no autonomous é retry nativo — sem código adicional

**Contras v5:**
- Se Gemini fica indisponível, o v5 para completamente — zero fallback de provider
- Sem DLQ — tasks que falham desaparecem silenciosamente
- Sem métricas de circuit — impossível saber quantas vezes o circuit abriu em produção

**Recomendação para v5:**
1. Adicionar fallback de provider no `llm_factory.py`:
   ```python
   # src/utils/llm_factory.py — adicionar fallback
   def create_tracked_llm(tier: str = "default"):
       try:
           return ChatGoogleGenerativeAI(model=MODEL_MAP[tier])
       except Exception:
           logger.warning("Gemini unavailable, fallback to OpenAI")
           return ChatOpenAI(model="gpt-4o-mini")  # fallback básico
   ```
2. Adicionar circuit breaker por provider no `llm_factory.py`
3. Criar Dead Letter Queue para RabbitMQ messages que falharam (ver Seção 20, item V-11)

---

## 14. Aprendizado e Adaptação

### Plataforma LIA — Ciclo Completo de Aprendizado

```
Feedback → ml_feedback_service.py → learning_loop_service.py
               → ab_testing_service.py (testa variações)
               → template_learning_service.py (atualiza templates)
               → routing_learning_service.py (ajusta roteamento)
               → finetuning_export.py (exporta dataset)
               → model_drift_service.py (detecta regressões)
```

**Arquivos LIA:**
- `app/shared/learning/learning_loop_service.py`
- `app/shared/learning/learning_snapshot_service.py` (✅ Z2-01)
- `app/shared/learning/ab_testing_service.py`
- `app/services/model_drift_service.py`
- `app/services/ml_feedback_service.py`
- `app/jobs/drift_job.py`

---

### recruiter_agent_v5 — Feedback Tracker (sem loop automático)

**Arquivos v5:**
- `src/services/feedback/tracker.py` — FeedbackTracker (salva feedback do recrutador)
- `src/services/proactive/detector.py` — ProactiveDetector (detecta padrões de uso)
- `src/services/proactive/notifier.py` — notificações proativas
- `src/services/proactive/runner.py` — executa detecções em background

**O que o v5 captura:**
- Feedback explícito do recrutador (thumbs up/down) via `FeedbackTracker`
- Padrões de uso detectados proativamente (ProactiveDetector)
- **Não tem:** loop automático de atualização de prompts/comportamento baseado no feedback

**Por que o v5 não implementou learning loop (conforme docs/ANALISE_ADOCAO_PATTERNS_LIA.md):**
> "O v5 não tem visibilidade sobre o que o recrutador faz DEPOIS de receber a resposta. O feedback está no Rails. Sem pipeline de callback Rails → v5, não tem como capturar."

### 🔍 Análise de Mercado — Seção 14

**Pros LIA:**
- Learning loop completo é o que diferencia produto que melhora sozinho de um que exige intervenção manual
- ✅ LearningSnapshotService com rollback (Z2-01) — se aprendizado introduzir regressão, pode reverter

**Contras LIA:**
- A/B testing com usuários reais pode criar experiências inconsistentes
- Risco de feedback loop viciado (✅ mitigado via FairnessGuard no loop — Sprint F1-02)

**Pros v5:**
- Sem aprendizado = sem risco de feedback loop viciado
- `proactive/` detector é uma boa base para detecção de padrões

**Contras v5:**
- O sistema é o mesmo no dia 1 e no dia 365 — não melhora com uso
- FeedbackTracker captura dados mas ninguém usa esses dados automaticamente

**Recomendação para v5 — Passo a passo para learning loop mínimo:**

```
Passo 1: Criar webhook Rails → v5 para feedback de uso
```
```python
# CRIAR: src/api/webhooks.py — endpoint para receber feedback do Rails
@router.post("/webhooks/recruiter-feedback")
async def receive_feedback(payload: dict):
    feedback_tracker.save(
        session_id=payload["session_id"],
        action_taken=payload["action_taken"],  # ex: candidato aprovado depois da sugestão
        positive=payload["outcome"] == "approved",
    )
```

```
Passo 2: Criar FeedbackAnalyzer que roda semanalmente
```
```python
# CRIAR: src/tasks/feedback_analysis_task.py
@celery_app.task
def analyze_weekly_feedback():
    insights = FeedbackAnalyzer().analyze_last_7_days()
    # Ex: "search_pattern 'Python senior' sempre seguido de filtro score > 85"
    # Salvar como tenant_memories de categoria 'workflow_pattern'
    MemoryManager().remember(
        tenant_id=GLOBAL_TENANT,
        content=insights.summary,
        category="workflow_pattern",
        source_action="weekly_feedback_analysis",
    )
```

```
Passo 3: Usar TenantMemoryStore para personalização baseada em histórico
```

---

## 15. Observabilidade de IA

### Comparativo de Observabilidade

| Componente | LIA | v5 |
|---|---|---|
| **Tracing de execução** | LangSmith + execution_log_store.py + **OTEL (Z6-02)** | `audit_callback.py` (node_start/end + timing) + `react_observer.py` |
| **Persistência de audit** | PostgreSQL + LangSmith | `audit_writer.py` (PostgreSQL: agent_executions) + JSONL (logs/audit/) |
| **Tracking de tokens** | `ai_consumption.py` por tenant | `llm_tracking_service.py` por chamada |
| **Métricas Prometheus** | 16 métricas (Y2/C4) | Não |
| **Qualidade de resposta** | RAGAS + `agent_quality_evaluator.py` | Não |
| **Explicabilidade** | `agent_explainability.py` | Não |
| **Drift detection** | `model_drift_service.py` + job diário | Não |
| **Health alerts** | `agent_health_alert_service.py` | Não |
| **ReAct observer** | Não explicitamente mencionado | `react_observer.py` — rastreia tool calls do ReAct |
| **Execution tracker** | `execution_log_store.py` | `execution_tracker.py` — timing por step |
| **Thinking messages** | Não | `thinking_message.py` — feedback ao usuário durante processamento |

**Arquivos v5 de observabilidade:**
```python
# src/services/audit/audit_callback.py — AuditCallbackHandler (LangChain callback)
class AuditCallbackHandler(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, *, run_id, ...):
        # registra NODE_START com timestamp
    def on_chain_end(self, outputs, *, run_id, ...):
        # registra NODE_END com duration_ms
    def on_chain_error(self, error, ...):
        # registra NODE_ERROR

# src/services/audit/audit_writer.py — PostgreSQL
CREATE TABLE agent_executions (
    execution_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(255),
    domain_id VARCHAR(100),
    user_query TEXT,  # com PII masking ([EMAIL], etc.)
    ...
)

# src/services/react_observer.py — ReActObserver
# rastreia tool calls: qual tool foi chamada, args, resultado, timing

# src/services/execution_tracker.py — ExecutionTracker
# timing por step, start/finish, to_dict()
```

### 🔍 Análise de Mercado — Seção 15

**Pros LIA:**
- OTEL + LangSmith + RAGAS é a combinação de referência para LLM observability em 2025
- `ai_consumption.py` por tenant permite cobrar por uso real — diferencial de negócio
- ✅ OTEL implementado (Sprint Z6-02)

**Contras LIA:**
- RAGAS mede qualidade de RAG mas não mede qualidade de raciocínio do agente

**Pros v5:**
- `audit_callback.py` integrado como LangChain callback é elegante — funciona automaticamente em qualquer grafo
- `audit_writer.py` com PostgreSQL garante persistência de todas as execuções
- `react_observer.py` para ReAct loop é específico e útil — sabe exatamente qual tool o agente tentou

**Contras v5:**
- Sem métricas Prometheus — impossível configurar alertas automáticos de latência/erro
- Sem RAGAS — sem avaliação de qualidade das respostas
- Sem drift detection — não sabe quando a qualidade está piorando

**Recomendação para v5:**
1. Adicionar endpoint Prometheus:
   ```python
   # CRIAR: src/api/metrics.py
   from prometheus_client import Counter, Histogram, generate_latest
   
   request_count = Counter("v5_requests_total", "Total requests", ["domain", "status"])
   request_latency = Histogram("v5_request_latency_seconds", "Latency", ["domain"])
   
   @router.get("/metrics")
   async def metrics():
       return Response(generate_latest(), media_type="text/plain")
   ```
2. Adicionar LangSmith para tracing: `LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY=...`
3. Criar endpoint de saúde com métricas: `GET /health` retornando `circuit_breaker_status`, `memory_count`, `last_audit_at`

---

## 16. Integrações com LLMs

### Comparativo de LLMs

| Provider | LIA | v5 |
|---|---|---|
| **Claude (Anthropic)** | Haiku, Sonnet, Opus — principal | Não |
| **Gemini (Google)** | Pro, Flash — voz + fallback | **gemini-2.5-flash — ÚNICO** |
| **OpenAI** | GPT-4o, GPT-4o-mini — fallback | Não (mencionado em docs antigos mas não no código atual) |
| **Embeddings** | Não explicitamente | **Gemini gemini-embedding-001** (768 dims) |
| **Cascade automático** | Haiku→Sonnet→Opus→Gemini→GPT | Não (ModelRouter: fast/default/heavy DENTRO do Gemini) |
| **Factory pattern** | `llm_factory.py` | `src/utils/llm_factory.py` (`create_tracked_llm()`) |
| **Tracking integrado** | `ai_consumption.py` | `llm_tracking_service.py` dentro do `create_tracked_llm()` |
| **Model selection** | Por tier global | ModelRouter por query complexity |

**Detalhe v5 — ModelRouter:**
```python
# src/services/model_router.py
class ModelRouter:
    def choose(self, query: str, operation: str = "", tool_count: int = 0) -> ModelChoice:
        if operation in {"compress_result", "synthesize_response"}:
            return ModelChoice(self._model_fast, "fast", ...)  # gemini-2.0-flash
        if _HEAVY_PATTERNS.match(query):
            return ModelChoice(self._model_heavy, "heavy", ...)  # gemini-2.5-pro
        if _FAST_PATTERNS.match(query):
            return ModelChoice(self._model_fast, "fast", ...)
        return ModelChoice(self._model_default, "default", ...)  # gemini-2.5-flash
```

### 🔍 Análise de Mercado — Seção 16

**Pros LIA:**
- Multi-provider com cascade é resiliência máxima — praticamente nenhuma plataforma de HR Tech documenta isso
- Factory pattern garante que adicionar novo provider é mudança isolada

**Contras LIA:**
- Sem suporte a modelos locais (Ollama) — para clientes com data residency
- Sem rate limiting por provider no factory

**Pros v5:**
- Single provider Gemini = zero complexidade de routing entre providers
- ModelRouter com fast/default/heavy por query é uma otimização de custo elegante dentro do mesmo provider
- `create_tracked_llm()` integra tracking automaticamente — toda chamada ao LLM é rastreada

**Contras v5:**
- Vendor lock-in total em Gemini — qualquer mudança de preço/API da Google impacta 100% do sistema
- Sem cascade entre providers — se Gemini cair, o v5 para

**Recomendação para v5:**
1. Adicionar OpenAI como fallback no `llm_factory.py` (mínimo viável):
   ```python
   # src/utils/llm_factory.py — modificar create_tracked_llm()
   def create_tracked_llm(tier: str = "default", fallback: bool = True):
       if CircuitBreaker.is_open("gemini"):
           logger.warning("Gemini circuit open, using OpenAI fallback")
           return ChatOpenAI(model="gpt-4o-mini")
       return ChatGoogleGenerativeAI(model=MODEL_MAP[tier])
   ```
2. Registrar circuit breaker no `circuit_breaker.py` para `gemini`

---

## 17. Testes de IA

### Comparativo de Testes

> **Correção (19/03/2026):** O v5 tem **96 arquivos de teste** (não "~3 arquivos"). Tem testes de fairness, memory, circuit breaker, audit, integração e conversação.

| Tipo de Teste | LIA | v5 |
|---|---|---|
| **Arquivos de teste** | 313 arquivos (4.600+ casos) | 96 arquivos |
| **Testes de fairness** | `test_four_fifths_rule.py` + outros | `test_fairness.py`, `test_fact_checker.py` |
| **Testes de memória** | Sim | `test_memory_preservation.py` |
| **Testes de circuit breaker** | Sim | `test_circuit_breaker.py`, `test_circuit_breaker_integration.py` |
| **Testes de auditoria** | Sim | `test_audit.py` |
| **Testes de agente** | Por domínio | `test_agents.py`, `test_autonomous_domain.py`, `test_autonomous_conversation.py` |
| **Testes de integração** | Não documentado como pipeline | `tests/integration/` (easy/medium/hard/very_hard/difficult) |
| **Scripts de conversação** | Não | `tests/conversation_scripts/` (autonomous, sourcing) |
| **Testes de PII** | Não | `test_pii_filter.py` |
| **Testes de segurança** | Não | `test_security.py` |
| **Testes de workflow** | Não | `test_workflow.py` |
| **Testes de cost ladder** | Não | `test_cost_ladder.py`, `test_conversation_flow/test_cost_ladder_tiers.py` |
| **Dataset golden** | `golden_dataset.py` | `tests/evals/run_evals.py` (avaliações) |
| **Pipeline CI/CD** | Não documentado | Não documentado |
| **DeepEval/RAGAS** | RAGAS (LIA) | Não |

**Arquivos de teste v5 (96 total):**
```
tests/
├── conftest.py
├── test_agents.py                   ← agentes pipeline
├── test_workflow.py                 ← WorkflowOrchestrator
├── test_fairness.py                 ← fairness (sourcing + jobs)
├── test_fact_checker.py             ← FactChecker
├── test_memory_preservation.py      ← ConversationSession memory
├── test_circuit_breaker.py          ← CircuitBreaker unitário
├── test_circuit_breaker_integration.py
├── test_audit.py                    ← AuditCallbackHandler
├── test_pii_filter.py               ← PIIMaskingFilter + mask_pii()
├── test_security.py                 ← injection detection
├── test_cost_ladder.py              ← CostLadder routing
├── test_autonomous_domain.py        ← autonomous agent
├── test_autonomous_conversation.py  ← conversas multi-turno
├── test_autonomous_fallback.py
├── test_evaluation.py               ← evaluation domain
├── test_insights.py                 ← insights domain
├── test_messaging_domain.py         ← messaging domain
├── test_scheduling_bypass.py        ← scheduling domain
├── test_sourcing_conversation.py    ← sourcing domain
├── test_hallucination_prevention.py
├── test_semantic_cache.py
├── test_checkpointer.py
├── test_model_router.py
├── test_api_planner.py, test_api_planner_unit.py, test_api_planner_contracts.py
├── test_api_executor.py
├── test_intent_analyzer_unit.py
├── integration/
│   ├── test_easy_cases.py
│   ├── test_medium_cases.py
│   ├── test_hard_cases.py
│   ├── test_very_hard_cases.py
│   └── test_difficult_cases.py
├── test_conversation_flow/
│   ├── test_cost_ladder_tiers.py
│   ├── test_cross_domain.py
│   ├── test_part1_insights_briefing.py
│   ├── test_part3_applies_triagem.py
│   ├── test_part4_sourcing.py
│   ├── test_part5_scheduling.py
│   ├── test_part6_messaging.py
│   └── test_part7_insights_eval_closing.py
└── evals/run_evals.py
```

### 🔍 Análise de Mercado — Seção 17

**Pros LIA:**
- Golden dataset para avaliação é prática que Google, Anthropic usam internamente
- `test_four_fifths_rule.py` é o tipo de teste que auditores externos pedem

**Contras LIA:**
- Coverage gate 30% (pytest.ini) — plataformas enterprise ficam em 60–80%
- Sem pipeline CI/CD para testes de LLM — testes lentos e caros sem estratégia de quando rodar

**Pros v5:**
- `tests/integration/` com 5 níveis de dificuldade (easy→very_hard→difficult) é estrutura de teste de qualidade profissional
- `test_conversation_flow/` testando cada parte de uma conversa longa é o tipo de teste de agente mais correto
- Testes de segurança e PII são diferencial — a maioria das plataformas não testa isso

**Contras v5:**
- 96 arquivos mas sem suite de CI/CD documentada — possivelmente os testes não rodam automaticamente
- Sem golden dataset formal — `evals/run_evals.py` existe mas sem dataset de referência
- Sem DeepEval ou métricas de qualidade LLM

**Recomendação para v5:**
1. Criar `.github/workflows/tests.yml`:
   ```yaml
   # CRIAR: .github/workflows/tests.yml
   name: Test Suite
   on: [push, pull_request]
   jobs:
     unit-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Run unit tests (sem LLM)
           run: pytest tests/ -v --ignore=tests/integration --ignore=tests/evals -x
     integration-tests:
       runs-on: ubuntu-latest
       if: github.event_name == 'pull_request'
       steps:
         - name: Run integration (com LLM mock)
           run: pytest tests/integration/test_easy_cases.py -v
   ```
2. Criar `tests/golden_dataset.py` com 50 perguntas canônicas + respostas esperadas
3. Adicionar DeepEval para métricas de qualidade:
   ```python
   # tests/test_response_quality.py
   from deepeval import evaluate
   from deepeval.metrics import HallucinationMetric, FaithfulnessMetric
   ```

---

## 18. Jobs e Processamento Assíncrono

### Plataforma LIA — Jobs Celery (Beat Schedule)

| Job | Frequência | Função | Arquivo |
|---|---|---|---|
| `drift_job` | Diário 3h | Detecta regressão de qualidade | `app/jobs/drift_job.py` |
| `proactive_alerts` | A cada hora | Alertas para recrutadores | `app/jobs/proactive_alerts_job.py` |
| `lgpd_cleanup` | Semanal Dom 2h | Remove dados expirados | `app/jobs/lgpd_cleanup_job.py` |
| `ab_testing_eval` | Diário 4h | Avalia variantes A/B | `app/jobs/ab_testing_job.py` |
| `finetuning_export` | Semanal | Exporta dataset de treino | `app/jobs/finetuning_export_job.py` |
| `learning_loop` | Diário | Aplica feedback ao sistema | `app/jobs/learning_loop_job.py` |
| `memory_consolidation` | Diário | Consolida memórias de longo prazo | `app/jobs/memory_job.py` |

---

### recruiter_agent_v5 — Celery + RabbitMQ

**Arquivos v5:**
- `src/celery_app.py` — configuração Celery
- `celery_worker.py` — entry point worker
- `deploy/systemd/celery-sourcing@.service` — worker de sourcing (multi-instance)
- `deploy/systemd/celery-evaluation@.service` — worker de evaluation
- `src/services/rabbitmq_service.py` — consumer RabbitMQ

**Workers documentados:**
```bash
# deploy/WORKERS_O_QUE_FAZEM.md (via docs/)
celery-sourcing@{1..N}   — N instâncias para processamento paralelo de sourcing
celery-evaluation@{1..N} — N instâncias para processamento de avaliações
```

**Diferença arquitetural:**

| Aspecto | LIA | v5 |
|---|---|---|
| **Broker** | Redis (Celery) | RabbitMQ + Celery |
| **Jobs scheduled** | 7+ jobs com beat schedule | Workers de domínio (sourcing, evaluation) |
| **DLQ** | ✅ DLQService (Redis LIST) | Não |
| **Monitoring** | Admin endpoint | `analyze_rabbitmq.py`, `inspect_celery.py`, `detailed_consumers.py` |

### 🔍 Análise de Mercado — Seção 18

**Pros LIA:**
- 7+ jobs scheduled cobrem todas as necessidades de manutenção automática
- DLQ com Redis garante que nenhuma task falha silenciosamente ✅

**Contras LIA:**
- Redis como broker pode ser gargalo sob alta carga — RabbitMQ é mais robusto para produção

**Pros v5:**
- RabbitMQ é o broker de produção padrão — mais robusto, ACK persistente, exchange routing
- Multi-instance workers com systemd é arquitetura de produção correta
- Scripts de diagnóstico (analyze_rabbitmq.py, inspect_celery.py) mostram maturidade operacional

**Contras v5:**
- Sem DLQ — tasks que falham 3x desaparecem
- Sem beat schedule — sem manutenção automática (cleanup, drift, etc.)

**Recomendação para v5:**
1. Adicionar DLQ no RabbitMQ:
   ```python
   # src/services/rabbitmq_service.py — adicionar dead letter exchange
   # No setup do RabbitMQ:
   channel.exchange_declare("dlx", "direct")
   channel.queue_declare("dead_letter_queue", durable=True)
   channel.queue_bind("dead_letter_queue", "dlx", "dead")
   ```
2. Criar `src/tasks/scheduled_tasks.py` com beat schedule básico:
   ```python
   # celery_app.py — adicionar beat_schedule
   app.conf.beat_schedule = {
       'lgpd-cleanup-daily': {
           'task': 'src.tasks.lgpd_cleanup_task.cleanup_expired_memories',
           'schedule': crontab(hour=3, minute=0),
       },
       'proactive-alerts-hourly': {
           'task': 'src.tasks.proactive_runner.run_proactive_detection',
           'schedule': crontab(minute=0),
       },
   }
   ```

---

## 19. Inventário de Arquivos de IA

### Plataforma LIA — Arquivos de IA por Categoria

| Categoria | Quantidade | Exemplos |
|---|---|---|
| **Agentes ReAct** | 12 | `*_react_agent.py` por domínio |
| **Grafos LangGraph** | 5 | `wsi_interview_graph.py`, `interview_graph.py`, `job_wizard_graph.py` |
| **SubAgentes Z1** | 6 | `kanban_*_agent.py`, `pipeline_*_agent.py` |
| **Tool Registries** | 12 | `*_tool_registry.py` por domínio |
| **System Prompts** | 12 | `*_system_prompt.py` por domínio |
| **Stage Contexts** | 12 | `*_stage_context.py` por domínio |
| **Fairness** | 4 | `fairness_guard.py`, `fact_checker.py`, `audit_callback.py`, `admin_bias_audit.py` |
| **Memória** | 3 | `working_memory.py`, `long_term_memory.py`, `memory_integration.py` |
| **Providers LLM** | 4 | `llm_claude.py`, `llm_gemini.py`, `llm_openai.py`, `llm_factory.py` |
| **Orchestrator** | 14 | `cascaded_router.py`, `llm_cascade.py`, `semantic_cache.py`... |
| **Resilência** | 2 | `circuit_breaker.py`, `dlq_service.py` |
| **Learning** | 5 | `learning_loop_service.py`, `ab_testing_service.py`... |
| **PII** | 2 | `pii_masking.py`, `consent_checker_service.py` |
| **LGPD** | 4 | `dsr_export_service.py`, `lgpd_cleanup_service.py`... |
| **Observabilidade** | 5 | `observability.py`, `execution_log_store.py`, `ai_consumption.py`... |
| **Testes de IA** | 313 | `test_four_fifths_rule.py`, `golden_dataset.py`... |

---

### recruiter_agent_v5 — Inventário Completo de Arquivos de IA

#### Hub e Orquestração

| Arquivo | Função |
|---|---|
| `src/hub/orchestrator.py` | HubOrchestrator — sessão, planejamento, execução |
| `src/hub/planner.py` | HubPlanner — fast-path + CostLadder + LLM |
| `src/hub/supervisor_graph.py` | LangGraph supervisor (roteia entre domínios) |
| `src/hub/supervisor_state.py` | SupervisorState TypedDict |
| `src/hub/session.py` | ConversationSession (Redis + domain_memories) |
| `src/hub/domain_agent_node.py` | Nó de execução de domínio no grafo |

#### Grafos LangGraph

| Arquivo | Grafo | Nós |
|---|---|---|
| `src/workflow/graph.py` | WorkflowOrchestrator | 6 (intent→plan→execute→validate→process→format) |
| `src/hub/supervisor_graph.py` | SupervisorGraph | route→domain→END |
| `src/domains/scheduling/graph.py` | SchedulingGraph | parse→check_slots→confirm→execute |
| `src/domains/evaluation/graph.py` | InterviewGraph | classify→evaluate→decide→craft |
| `src/domains/applies/react_agent.py` | ReactAgent (applies) | ReAct loop (MAX=12) |
| `src/domains/autonomous/agent.py` | AutonomousReAct | ReAct loop (RetryPolicy) |

#### Agentes de Domínio

| Arquivo | Domínio | Tipo |
|---|---|---|
| `src/agents/intent_analyzer.py` | Global | Pipeline + RAG |
| `src/agents/api_planner.py` | Global | Pipeline + 51 YAMLs |
| `src/agents/api_executor.py` | Global | Pipeline HTTP |
| `src/agents/plan_validator.py` | Global | Pipeline |
| `src/agents/data_processor.py` | Global | Pipeline |
| `src/agents/answer_formatter.py` | Global | Pipeline |
| `src/domains/applies/react_agent.py` | Applies | ReAct LangGraph |
| `src/domains/autonomous/agent.py` | Autonomous | ReAct LangGraph (73+ tools) |
| `src/domains/sourced_profile_sourcing/agents/orchestrator.py` | Sourcing | Supervisor |
| `src/domains/sourced_profile_sourcing/agents/router.py` | Sourcing | Router |
| `src/domains/sourced_profile_sourcing/agents/planner.py` | Sourcing | Planner |
| `src/domains/sourced_profile_sourcing/agents/search.py` | Sourcing | Search (embeddings) |
| `src/domains/sourced_profile_sourcing/agents/detail.py` | Sourcing | Detail |
| `src/domains/sourced_profile_sourcing/agents/analytics.py` | Sourcing | Analytics |
| `src/domains/sourced_profile_sourcing/agents/comparison.py` | Sourcing | Comparison |
| `src/domains/sourced_profile_sourcing/agents/report.py` | Sourcing | Report |
| `src/domains/sourced_profile_sourcing/agents/action.py` | Sourcing | Action |

#### Serviços de IA/ML

| Arquivo | Função |
|---|---|
| `src/services/embedding_service.py` | Gemini embedding-001 (768d) |
| `src/services/semantic_cache.py` | Cache semântico Redis |
| `src/services/rag_service.py` | RAG híbrido (semântico + textual) |
| `src/services/model_router.py` | ModelRouter (fast/default/heavy) |
| `src/services/cost_ladder.py` | CostLadder (routing multi-tier) |
| `src/services/llm_tracking_service.py` | Tracking de tokens por chamada |
| `src/services/llm_cache_service.py` | Cache de respostas LLM |
| `src/services/sector_benchmark.py` | Benchmarks por setor |
| `src/utils/llm_factory.py` | create_tracked_llm() — factory principal |

#### Memória e Estado

| Arquivo | Função |
|---|---|
| `src/services/memory/manager.py` | MemoryManager (remember, recall, categorize) |
| `src/services/memory/store.py` | TenantMemoryStore (PostgreSQL + pgvector) |
| `src/services/memory/models.py` | TenantMemory dataclass |
| `src/services/memory_service.py` | Serviço de memória de alto nível |
| `src/services/checkpointer.py` | PostgresSaver + MemorySaver |
| `src/config/memory_config.py` | Configuração de memória |
| `src/domains/applies/memory.py` | AppliesConversationMemory |
| `src/domains/jobs/memory.py` | JobsConversationMemory |
| `src/domains/insights/memory.py` | InsightsConversationMemory |
| `src/domains/messaging/memory.py` | MessagingConversationMemory |
| `src/domains/scheduling/memory.py` | SchedulingConversationMemory |
| `src/domains/sourced_profile_sourcing/memory.py` | SourcingConversationMemory |

#### Fairness, Compliance e Segurança

| Arquivo | Função |
|---|---|
| `src/domains/jobs/fairness.py` | Fairness em job descriptions |
| `src/domains/sourced_profile_sourcing/fairness.py` | Fairness em filtros de sourcing |
| `src/domains/sourced_profile_sourcing/fact_checker.py` | FactChecker (count, avg, score) |
| `src/services/pii_filter.py` | PIIMaskingFilter em logs (CPF, email, phone) |
| `src/services/security.py` | InjectionDetector + Sanitizer |

#### Auditoria e Observabilidade

| Arquivo | Função |
|---|---|
| `src/services/audit/audit_callback.py` | AuditCallbackHandler (LangChain) |
| `src/services/audit/audit_models.py` | AuditExecution, AuditEvent, AuditEventType |
| `src/services/audit/audit_storage.py` | JSONL storage (logs/audit/audit_YYYY-MM-DD.jsonl) |
| `src/services/audit/audit_writer.py` | PostgreSQL (agent_executions table) |
| `src/services/execution_tracker.py` | Timing por step |
| `src/services/react_observer.py` | ReActObserver (rastreia tool calls) |
| `src/services/thinking_message.py` | ThinkingMessageService (feedback ao usuário) |
| `src/services/streaming_callback.py` | Streaming de respostas |

#### Resiliência

| Arquivo | Função |
|---|---|
| `src/services/circuit_breaker.py` | CircuitBreaker (threshold, cooldown, reset_all) |
| `src/services/timed_node.py` | _TimeoutError + timeout por nó |
| `src/services/pending_action_store.py` | HITL (ações pendentes de confirmação) |

#### Proativo e Feedback

| Arquivo | Função |
|---|---|
| `src/services/proactive/detector.py` | Detecção de padrões proativos |
| `src/services/proactive/notifier.py` | Notificação proativa |
| `src/services/proactive/runner.py` | Execução em background |
| `src/services/feedback/tracker.py` | FeedbackTracker |

#### Testes de IA (96 arquivos)

| Arquivo | Cobre |
|---|---|
| `tests/test_fairness.py` | fairness.py |
| `tests/test_fact_checker.py` | fact_checker.py |
| `tests/test_pii_filter.py` | pii_filter.py |
| `tests/test_security.py` | security.py |
| `tests/test_memory_preservation.py` | ConversationSession memory |
| `tests/test_circuit_breaker.py` | CircuitBreaker |
| `tests/test_circuit_breaker_integration.py` | CircuitBreaker integration |
| `tests/test_audit.py` | AuditCallbackHandler |
| `tests/test_workflow.py` | WorkflowOrchestrator |
| `tests/test_hallucination_prevention.py` | anti-hallucination |
| `tests/test_autonomous_conversation.py` | ReAct autonomous |
| `tests/integration/test_easy_cases.py` | E2E fáceis |
| `tests/integration/test_very_hard_cases.py` | E2E difíceis |
| `tests/test_conversation_flow/test_cost_ladder_tiers.py` | CostLadder |
| `tests/test_conversation_flow/test_cross_domain.py` | cross-domain routing |
| `tests/evals/run_evals.py` | Avaliações LLM |

---

## 20. Plano de Otimização v5 — Passo a Passo

> Cada item indica: **Prioridade | Arquivo a modificar/criar | O que fazer | Código de referência**

### Fase V-1 — Crítico (Sprint 1–2)

---

#### V-01 · Estabilizar PostgresSaver (Checkpointing)

**Por que:** PostgresSaver instável é o maior risco de perda de estado — entrevistas de 30min reiniciam do zero.
**Nota do ARCHITECTURAL_AUDIT:** "checkpointing nota 3/10 — PostgresSaver quebrado, sem recovery"

**MODIFICAR: `src/services/checkpointer.py`**
```python
# Adicionar pool de conexão dedicado e retry
import psycopg2.pool
from tenacity import retry, stop_after_attempt, wait_exponential

_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        settings = get_settings()
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1, maxconn=5,
            host=settings.postgres.host,
            port=settings.postgres.port,
            user=settings.postgres.user,
            password=settings.postgres.password,
            database=settings.postgres.database,
        )
    return _pool

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def _create_postgres_saver() -> PostgresSaver:
    conn = _get_pool().getconn()
    saver = PostgresSaver(conn)
    saver.setup()
    return saver
```

**CRIAR: `src/tasks/checkpointer_health_task.py`**
```python
@celery_app.task
def verify_checkpointer_health():
    """Roda a cada 5 min para detectar falha do PostgresSaver antecipadamente."""
    try:
        saver = get_checkpointer()
        # simula put/get básico
        logger.info("[Checkpointer] Health OK")
    except Exception as e:
        logger.error(f"[Checkpointer] Health FAIL: {e}")
        # reset e força MemorySaver
        global _saver
        _saver = MemorySaver()
```

---

#### V-02 · Multi-tenancy Básico no Hub

**Por que:** Dois clientes diferentes usando o mesmo agente têm memórias e configurações misturadas.

**CRIAR: `src/hub/tenant_context.py`**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TenantContext:
    tenant_id: int
    company_name: str
    features_enabled: list  # ["scheduling", "evaluation", "messaging"]
    custom_domain_prompts: dict  # {"jobs": "Somos uma startup de tech..."}
    max_memories: int = 500
    memory_ttl_days: int = 30

def get_tenant_context(auth_token: str) -> TenantContext:
    """Busca config do tenant via Rails API."""
    from src.services.auth_service import AuthService
    user = AuthService.validate_token(auth_token)
    return TenantContext(
        tenant_id=user["company_id"],
        company_name=user["company_name"],
        features_enabled=user.get("ai_features", ["jobs", "applies", "sourcing"]),
        custom_domain_prompts=user.get("custom_prompts", {}),
    )
```

**MODIFICAR: `src/hub/orchestrator.py`**
```python
# Adicionar tenant_context em todas as execuções
from src.hub.tenant_context import get_tenant_context

class HubOrchestrator:
    async def process(self, query: str, auth_token: str, session_id: str) -> dict:
        tenant = get_tenant_context(auth_token)
        
        # Verificar features habilitadas
        domain = self.planner.plan(query, tenant.features_enabled)
        
        # Passar tenant_id para memória
        self.memory_manager.set_tenant(tenant.tenant_id)
```

---

#### V-03 · Criar shared/fairness/ Unificado

**Por que:** `fairness.py` em 2 domínios = duplicação. Quando jobs e sourcing crescerem para messaging e autonomous, vai triplicar.

**CRIAR: `src/shared/fairness/__init__.py`**
**CRIAR: `src/shared/fairness/guard.py`** (ver código em Seção 11)

**MOVER:** `src/domains/jobs/fairness.py` → lógica para `src/shared/fairness/job_description_checker.py`
**MOVER:** `src/domains/sourced_profile_sourcing/fairness.py` → `src/shared/fairness/candidate_filter_checker.py`

**CRIAR: `src/shared/fairness/fact_checker.py`** (unificado de sourcing para todos os domínios):
```python
# Mover src/domains/sourced_profile_sourcing/fact_checker.py → src/shared/fairness/fact_checker.py
# Renomear para uso genérico (não só sourcing)
class UniversalFactChecker:
    def verify_count_claim(self, claimed, actual_list, context="itens") -> FactCheckResult: ...
    def verify_average_claim(self, claimed_avg, data, field, tolerance=None) -> FactCheckResult: ...
    def verify_score_claim(self, claimed_score, actual_score, tolerance=5.0) -> FactCheckResult: ...
```

---

#### V-04 · PII Masking em Prompts (não só em logs)

**Por que:** `pii_filter.py` mascara logs mas o texto do usuário vai para o Gemini sem mascaramento.

**MODIFICAR: `src/utils/llm_factory.py`**
```python
# Adicionar wrapper que mascara PII antes de enviar ao LLM
from src.services.pii_filter import mask_pii

class TrackedLLM:
    def __init__(self, base_llm):
        self._llm = base_llm
    
    def invoke(self, messages: list) -> str:
        # Mascarar PII em todas as mensagens
        masked_messages = []
        for msg in messages:
            if hasattr(msg, 'content'):
                msg.content = mask_pii(msg.content)
            masked_messages.append(msg)
        return self._llm.invoke(masked_messages)
```

---

#### V-05 · Resolver Referências no HubPlanner

**Por que:** Sem `reference_resolver.py` integrado ao Hub, "ela" e "aquela vaga" vão para o Gemini sem contexto.

**CRIAR: `src/hub/context_resolver.py`**
```python
from src.services.reference_resolver import ReferenceResolver
from src.hub.session import ConversationSession

class ContextResolver:
    def resolve(self, query: str, session: ConversationSession) -> str:
        """
        Resolve referências pronominais usando memória de domínio da sessão.
        "ela" → candidata Maria da última ação
        "aquela vaga" → vaga 7144 da última ação
        """
        last_job_id = None
        last_candidate_id = None
        
        # Checar domain memories por referências recentes
        for domain, memory in session.domain_memories.items():
            if hasattr(memory, 'last_job_id') and memory.last_job_id:
                last_job_id = memory.last_job_id
            if hasattr(memory, 'last_candidate_id') and memory.last_candidate_id:
                last_candidate_id = memory.last_candidate_id
        
        # Substituir referências
        if last_job_id and any(ref in query.lower() for ref in ["aquela vaga", "essa vaga", "a vaga"]):
            query = query + f" (vaga {last_job_id})"
        if last_candidate_id and any(ref in query.lower() for ref in ["ela", "ele", "esse candidato"]):
            query = query + f" (candidato {last_candidate_id})"
        
        return query
```

**MODIFICAR: `src/hub/planner.py`** — adicionar `ContextResolver.resolve()` antes do CostLadder.

---

### Fase V-2 — Alta Prioridade (Sprint 3–4)

---

#### V-06 · Tool Registry Explícito por Domínio

**Para cada domínio, CRIAR: `src/domains/{domain}/tool_registry.py`**

Exemplo para jobs:
```python
# CRIAR: src/domains/jobs/tool_registry.py
from dataclasses import dataclass
from typing import List, Callable

@dataclass
class JobsTool:
    name: str
    description: str
    handler: Callable
    requires_confirmation: bool = False
    fairness_check: bool = False

JOBS_TOOLS: List[JobsTool] = [
    JobsTool("search_jobs", "Busca vagas por critérios", search_jobs_handler, False, False),
    JobsTool("get_job_details", "Detalhes de uma vaga", get_job_details_handler, False, False),
    JobsTool("create_job", "Cria nova vaga (JD gerada)", create_job_handler, True, True),
    JobsTool("update_job", "Atualiza vaga existente", update_job_handler, True, True),
    JobsTool("close_job", "Encerra vaga", close_job_handler, True, False),
]
```

---

#### V-07 · Bloco Anti-sycophancy em Todos os Prompts

**CRIAR: `src/shared/prompts/base_blocks.py`**
```python
ANTI_SYCOPHANCY = """
REGRA CRÍTICA — Integridade dos dados:
Você é um agente de dados, não um validador de opiniões. Se o usuário fizer uma afirmação
incorreta sobre os dados (ex: "esse candidato é excelente" quando o score é 42/100),
apresente os dados reais de forma clara e respeitosa, sem concordar com a afirmação incorreta.
Exemplo: "Entendo sua percepção. Os dados mostram score 42/100, com pontos fortes em X mas
fragilidades em Y. A decisão final é sua."
"""

HITL_RULES = """
AÇÕES DESTRUTIVAS — Confirmação obrigatória:
Para qualquer ação que não pode ser desfeita (criar candidatura, enviar email, mover etapa,
encerrar vaga), apresente um resumo claro do que será feito e aguarde confirmação explícita
do usuário antes de executar. Use ask_user() para isso.
"""
```

**MODIFICAR: todos os `src/domains/*/prompts.py`** — importar e incluir os blocos:
```python
# Adicionar no sistema de cada domínio
from src.shared.prompts.base_blocks import ANTI_SYCOPHANCY, HITL_RULES
SYSTEM_PROMPT = f"{DOMAIN_SPECIFIC_PROMPT}\n\n{ANTI_SYCOPHANCY}\n\n{HITL_RULES}"
```

---

#### V-08 · Dead Letter Queue para RabbitMQ

**MODIFICAR: `src/services/rabbitmq_service.py`**
```python
# Configurar DLX (Dead Letter Exchange) na declaração da fila
def setup_queues(channel):
    # Dead letter exchange
    channel.exchange_declare("lia.dlx", "direct", durable=True)
    channel.queue_declare("lia.dead_letters", durable=True, arguments={
        "x-message-ttl": 7 * 24 * 3600 * 1000  # 7 dias
    })
    channel.queue_bind("lia.dead_letters", "lia.dlx", "dead")
    
    # Fila principal com DLX configurado
    channel.queue_declare("lia.sourcing", durable=True, arguments={
        "x-dead-letter-exchange": "lia.dlx",
        "x-dead-letter-routing-key": "dead",
        "x-max-retries": 3,
    })
```

**CRIAR: `src/api/admin_dlq.py`** — endpoint para visualizar mensagens mortas.

---

#### V-09 · Prometheus Metrics

**CRIAR: `src/services/metrics_service.py`**
```python
from prometheus_client import Counter, Histogram, Gauge

# Contadores por domínio e status
request_count = Counter(
    "v5_requests_total",
    "Total de requests processados",
    ["domain", "status"]  # status: success, error, fallback
)

# Latência por domínio
request_latency = Histogram(
    "v5_request_latency_seconds",
    "Latência de processamento em segundos",
    ["domain"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Tokens por LLM
llm_tokens_total = Counter(
    "v5_llm_tokens_total",
    "Tokens consumidos por LLM",
    ["model", "tier"]  # tier: fast, default, heavy
)

# Circuit breaker status
circuit_status = Gauge(
    "v5_circuit_breaker_open",
    "Status do circuit breaker (1=aberto, 0=fechado)",
    ["service"]  # service: gemini, rabbitmq, postgres
)
```

**MODIFICAR: `src/api.py`** — adicionar endpoint `/metrics`:
```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

---

#### V-10 · Feedback Loop Básico (Learning Mínimo)

Ver Seção 14 — Aprendizado. Implementação em 3 passos:

**CRIAR: `src/api/webhooks.py`** (webhook Rails→v5 para feedback)
**CRIAR: `src/tasks/feedback_analysis_task.py`** (análise semanal)
**MODIFICAR: `src/hub/orchestrator.py`** (usar TenantMemoryStore com memórias de padrão)

---

### Fase V-3 — Médio Prazo (Sprint 5–8)

---

#### V-11 · Relatório de Fairness Exportável

**CRIAR: `src/services/fairness_reporter.py`**
```python
class FairnessReporter:
    def generate_period_report(self, tenant_id: int, period: str) -> dict:
        """
        period: "2026-Q1", "2026-03", "2026-W12"
        Retorna: {
            "period": str,
            "total_decisions_audited": int,
            "bias_flags_raised": int,
            "domains_checked": ["jobs", "sourcing"],
            "bias_terms_detected": [{"term": str, "count": int}],
            "recommendations": [str]
        }
        """
        # Lê audit_storage.py (JSONL) + filtra por tenant e período
        # Agrega métricas de fairness
        ...
```

**CRIAR: `src/api/admin_fairness.py`**
```python
@router.get("/admin/fairness/report")
async def get_fairness_report(period: str = "current-month"):
    reporter = FairnessReporter()
    report = reporter.generate_period_report(get_tenant_id(), period)
    return report

@router.get("/admin/fairness/export")
async def export_fairness_report(period: str, format: str = "json"):
    # format: json, csv
    ...
```

---

#### V-12 · Golden Dataset e Testes de Qualidade

**CRIAR: `tests/golden_dataset.py`**
```python
GOLDEN_DATASET = [
    {
        "query": "quantos candidatos temos na vaga 7144?",
        "expected_domain": "applies",
        "expected_action": "count",
        "expected_contains": ["candidatos", "7144"],
    },
    {
        "query": "lista as vagas abertas de tecnologia",
        "expected_domain": "jobs",
        "expected_action": "search",
        "expected_contains": ["tecnologia"],
    },
    # ... 50+ casos canônicos
]

def test_golden_dataset(hub_orchestrator, mock_rails_api):
    for case in GOLDEN_DATASET:
        result = hub_orchestrator.process(case["query"], mock_token)
        assert result["domain"] == case["expected_domain"]
        for term in case["expected_contains"]:
            assert term.lower() in result["response"].lower()
```

---

#### V-13 · Pipeline CI/CD para Testes

**CRIAR: `.github/workflows/tests.yml`**
```yaml
name: v5 Test Suite
on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  unit-tests:
    name: Unit Tests (sem LLM)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
          --ignore=tests/integration
          --ignore=tests/evals
          -x --tb=short
          -m "not slow"
  
  integration-tests:
    name: Integration Tests (com mock LLM)
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - run: pytest tests/integration/test_easy_cases.py
              tests/test_conversation_flow/ -v --tb=short
    env:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

---

## 21. Plano de Otimização LIA — Pendências

### Alta Prioridade (Sprint próximo)

| Item | Problema | Arquivo | Ação |
|---|---|---|---|
| **L-01** | Sem TTL em dados de conversa | `app/shared/agents/working_memory.py` | Adicionar TTL de 90 dias com cleanup automático |
| **L-02** | Relatório de fairness não exportável | `app/api/v1/admin_bias_audit.py` | Adicionar `GET /export?format=pdf` |
| **L-03** | Sem red teaming da FairnessGuard | `app/tests/` | Criar dataset adversarial + CI test |
| **L-04** | Cobertura de testes < 40% | `pytest.ini` | Aumentar `--cov-fail-under=50` |
| **L-05** | Sem prompts 100% YAML | `app/domains/*/agents/*_system_prompt.py` | Migrar .py → .yaml gradualmente |

### Médio Prazo

| Item | Problema | Ação |
|---|---|---|
| **L-06** | Sem Agent Studio para clientes | Criar `/api/v1/agents/configure` com tenant override |
| **L-07** | Sem criptografia de campo (CPF) | Adicionar `pgcrypto` para colunas PII no banco |
| **L-08** | LiteLLM vs llm_factory.py | Avaliar migração do cascade para LiteLLM |
| **L-09** | RAGAS só para RAG | Expandir RAGAS para avaliar qualidade de agente (tool selection, plan correctness) |
| **L-10** | Broker Redis → RabbitMQ | Migrar Celery broker para RabbitMQ (mais robusto em produção) |

---

## 22. Mapa de Domínios: Cobertura Cruzada LIA vs v5

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COBERTURA DE DOMÍNIOS                                   │
├──────────────────────────┬────────────────────────────┬─────────────────────┤
│ FUNCIONALIDADE           │ LIA                        │ v5                  │
├──────────────────────────┼────────────────────────────┼─────────────────────┤
│ CRUD de Vagas            │ ✅ Job Management           │ ✅ Jobs domain       │
│ Pipeline de Candidatos   │ ✅ CV Screening + Pipeline  │ ✅ Applies domain    │
│ Scoring de CVs           │ ✅ cv_screening_service     │ ✅ scoring.py action │
│ Sourcing de Talentos     │ ✅ Sourcing (1 agente)      │ ✅ 9 subagentes      │
│ Agendamento Entrevistas  │ ✅ InterviewGraph           │ ✅ SchedulingGraph   │
│ Avaliações / WSI         │ ✅ WSIInterviewGraph        │ ✅ InterviewGraph    │
│ Métricas / Insights      │ ✅ Analytics domain         │ ✅ Insights domain   │
│ Comunicação (Email)      │ ✅ Communication domain     │ ✅ Messaging domain  │
│ Automação de Regras      │ ✅ Automation domain        │ ⚠️ Via autonomous   │
│ Integração ATS           │ ✅ ATS Integration domain   │ ⚠️ Via 51 YAMLs     │
│ Policy / Compliance      │ ✅ Policy domain (Z5-02)    │ ❌ Não existe        │
│ Talent Intelligence      │ ✅ Y-series                 │ ❌ Não existe        │
│ LGPD Compliance          │ ✅ lgpd_cleanup + DSR       │ ❌ Sem compliance    │
│ Fairness 3 camadas       │ ✅ FairnessGuard mandatory  │ ⚠️ Opt-in 2 domínios│
│ Multi-tenancy no agente  │ ✅ budget + guardrails      │ ❌ Rails gerencia    │
│ Learning Loop            │ ✅ Ciclo completo           │ ⚠️ Só feedback tracker│
│ A/B Testing              │ ✅ ab_testing_service       │ ❌ Não               │
│ Drift Detection          │ ✅ model_drift_service      │ ❌ Não               │
│ LLM Multi-provider       │ ✅ Claude+Gemini+GPT cascade│ ❌ Gemini único      │
│ OTEL / Prometheus        │ ✅ OTEL (Z6-02)             │ ❌ Sem metrics       │
│ Memória por tenant       │ ✅ LongTermMemory           │ ✅ TenantMemoryStore │
│ Checkpointing LangGraph  │ ✅ PostgresSaver (estável)  │ ⚠️ instável (nota 3/10)|
│ Proactive Alerts         │ ✅ proactive_worker.py      │ ✅ proactive/         │
│ PII Masking              │ ✅ Presidio + regex         │ ✅ pii_filter.py     │
│ Injection Protection     │ Implícita                  │ ✅ security.py (20+) │
│ Circuit Breaker          │ ✅ 15+ circuits             │ ✅ 1 circuit global  │
│ Testes de IA             │ ✅ 313 arquivos             │ ✅ 96 arquivos       │
│ RAGAS / Qualidade LLM    │ ✅ ragas_evaluation_service │ ❌ Não               │
│ RAG Híbrido              │ ✅ rag_service.py           │ ✅ rag_service.py    │
│ Embeddings               │ Não explicitamente          │ ✅ Gemini 768d       │
│ RabbitMQ                 │ ❌ Usa Redis como broker    │ ✅ RabbitMQ nativo   │
│ Autonomous ReAct (73t.)  │ ⚠️ Via domains individuais │ ✅ autonomous/agent  │
└──────────────────────────┴────────────────────────────┴─────────────────────┘

Legenda: ✅ Implementado | ⚠️ Parcial | ❌ Não existe
```

### Gap Analysis Resumido

**A LIA está à frente do v5 em:**
- Multi-tenancy no agente
- LGPD compliance completo
- FairnessGuard 3 camadas obrigatório
- Learning loop completo
- LLM multi-provider com cascade
- OTEL + Prometheus + RAGAS
- Cobertura de domínios (13 vs 8)
- Volume de testes (313 vs 96)
- Relatórios e explicabilidade

**O v5 está à frente da LIA em:**
- RabbitMQ como broker (mais robusto que Redis para mensageria)
- Autonomous ReAct com 73+ tools e seleção dinâmica
- 9 subagentes de sourcing (mais granular que o SourcingReactAgent da LIA)
- injection protection explícita e testada (security.py com 20+ padrões)
- TenantMemoryStore com TTL + dedup + limite explícitos
- Scoring actions no domínio applies (best_fit_analysis, scoring_overview)
- Proactive detector com 3 camadas separadas

---

*Documento gerado em 19/03/2026 com base em leitura direta de todos os arquivos dos repositórios `WeDOTalent/recruiter_agent_v5` (820 arquivos) e `lia-agent-system/` (1.259 arquivos Python) via GitHub API.*

*Repositório v5 analisado: branch `main` | commit atualizado em 19/03/2026*
*Repositório LIA: branch `main` | Sprint mais recente: Z7-01 (19/03/2026)*
