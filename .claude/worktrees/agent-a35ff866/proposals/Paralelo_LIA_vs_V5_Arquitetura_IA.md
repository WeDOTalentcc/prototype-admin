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

**Guias de Implementação (ao final do documento)**

- [🛠️ Guia Técnico: Como Construir Agent Studio na WeDOTalent](#️-guia-técnico-como-construir-agent-studio-na-wedotalent)
  - [Parte 1 — LIA: Passo a Passo para Agent Studio](#parte-1--lia-passo-a-passo-para-agent-studio)
  - [Parte 2 — v5: Passo a Passo para Agent Studio](#parte-2--v5-passo-a-passo-para-agent-studio)
  - [Comparativo LIA vs v5 para Agent Studio](#comparativo-lia-vs-v5-para-agent-studio)
- [🤖 Parte 3 — Como Cada Tipo de Agente do Mercado Funciona e Como Construir na WeDOTalent](#-parte-3--como-cada-tipo-de-agente-do-mercado-funciona-e-como-construir-na-wedotalent)
  - [Agente Tipo 1 — Digital Twins (Eightfold Project Andromeda)](#agente-tipo-1--digital-twins-eightfold-project-andromeda)
  - [Agente Tipo 2 — Multi-Agent de Sourcing por Vaga (Juicebox Agents 2.0)](#agente-tipo-2--multi-agent-de-sourcing-por-vaga-juicebox-agents-20)
  - [Agente Tipo 3 — Agentes por Setor/Template (Phenom X+ Studio)](#agente-tipo-3--agentes-por-setortemplate-phenom-x-studio)
  - [Agente Tipo 4 — Guided Autonomy (hireEZ EZ Agent)](#agente-tipo-4--guided-autonomy-hireez-ez-agent)
  - [Agente Tipo 5 — Agente de Voz para Triagem (Phenom Interview Agent / Olivia)](#agente-tipo-5--agente-de-voz-para-triagem-phenom-interview-agent--olivia)
  - [Resumo: Esforço × Custo Operacional por Tipo](#resumo-todos-os-tipos-de-agente--esforço--custo-operacional)

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

---

## 🛠️ Guia Técnico: Como Construir Agent Studio na WeDOTalent

> Baseado na leitura real do código-fonte de `lia-agent-system/` e do repositório `recruiter_agent_v5` (GitHub WeDOTalent).
> Cada passo referencia arquivos reais que existem hoje. Nada aqui é hipotético.

---

### PARTE 1 — LIA: Passo a Passo para Agent Studio

#### O que já existe e serve de base

| Arquivo existente | O que já faz | O que falta para Agent Studio |
|---|---|---|
| `app/shared/prompts/prompt_registry.py` | `PromptRegistry` com versionamento semântico — `register_prompt()`, `get_prompt()`, `compare_versions()` | Não tem override **por tenant** — registry é global em memória |
| `app/orchestrator/tenant_budget.py` | `TenantBudget` — Redis rastreia tokens/mês por `company_id`, alerta a 80%, bloqueia a 100% | Só controla tokens, não configura comportamento do agente |
| `app/services/tenant_context_service.py` | `TenantContextService.get_context()` — lê `company_name`, `sector`, `autonomy_level`, `open_vacancies` do DB e injeta como snippet no prompt do orquestrador | Campos lidos são fixos — cliente não pode customizar o que é injetado |
| `app/orchestrator/cascaded_router.py` | Flui `company_id` por todos os 6 tiers de roteamento; chama `TenantContextService` no Tier 5 | Roteamento não varia por tenant — mesmos agentes para todos |
| `app/tools/tool_registry_loader.py` | Carrega `tool_registry_metadata.yaml` com `allowed_agents` por tool | Filtro é por tipo de agente, não por tenant |
| `app/api/v1/admin_agents.py` | `POST /api/v1/admin/agents/reload` — hot-reload do YAML de agentes | Sem endpoint de configuração por tenant |
| `app/api/v1/admin_prompts.py` | Endpoints admin para consultar prompts do `PromptRegistry` | Sem escrita/override por tenant |

**Conclusão sobre a LIA:** a espinha dorsal existe. `tenant_context_service.py` já prova que o sistema sabe ler configuração por tenant e injetá-la no prompt. Falta: (1) tabela para guardar configurações de agente por tenant, (2) serviço que carregue essa config, (3) hook no fluxo do prompt para aplicar o override, (4) filtro de tools por tenant, (5) endpoint para o cliente salvar sua config.

---

#### Passo LIA-1: Tabela de configuração de agente por tenant

Criar migration no Rails ATS (ou via Alembic na LIA, dependendo de onde vive o schema compartilhado):

```sql
-- Migration: create_tenant_agent_configs
CREATE TABLE tenant_agent_configs (
    id              BIGSERIAL PRIMARY KEY,
    company_id      BIGINT       NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    agent_name      VARCHAR(64)  NOT NULL,   -- ex: "sourcing", "cv_screening", "scheduling"
    is_enabled      BOOLEAN      NOT NULL DEFAULT true,
    custom_prompt_suffix TEXT,               -- texto que é APPENDED ao system prompt base
    tools_disabled  TEXT[]       DEFAULT '{}',  -- ex: {"linkedin_search", "export_csv"}
    confidence_threshold NUMERIC(3,2) DEFAULT 0.75, -- 0.0 a 1.0
    tone            VARCHAR(32)  DEFAULT 'profissional', -- "profissional"|"informal"|"tecnico"
    sector_context  TEXT,                    -- ex: "Empresa de logística com foco em motoristas CLT"
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      BIGINT       REFERENCES users(id),
    UNIQUE (company_id, agent_name)          -- uma config por agente por empresa
);

CREATE INDEX idx_tenant_agent_configs_company ON tenant_agent_configs(company_id);
```

**Por que `custom_prompt_suffix` e não substituição total?** Porque o prompt base (registrado no `PromptRegistry`) contém regras éticas, LGPD e FairnessGuard obrigatórios — o cliente personaliza a camada de contexto/tom, não as regras de compliance.

---

#### Passo LIA-2: `TenantAgentConfigService` — carrega config do DB

Criar `lia-agent-system/app/services/tenant_agent_config_service.py`:

```python
"""
TenantAgentConfigService — carrega configuração de agentes por empresa.
Usa Redis como cache com TTL de 5 minutos para evitar query ao DB a cada mensagem.
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)
_CACHE_TTL = 300  # 5 minutos


@dataclass
class AgentConfig:
    agent_name: str
    is_enabled: bool = True
    custom_prompt_suffix: Optional[str] = None
    tools_disabled: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.75
    tone: str = "profissional"
    sector_context: Optional[str] = None


class TenantAgentConfigService:

    async def get_config(
        self, company_id: str, agent_name: str, db: AsyncSession
    ) -> AgentConfig:
        """Retorna configuração do agente para o tenant. Fail-safe: retorna defaults."""

        # 1. Tenta cache Redis
        cached = await self._get_from_cache(company_id, agent_name)
        if cached:
            return cached

        # 2. Busca no DB
        try:
            from app.models.tenant_agent_config import TenantAgentConfig
            result = await db.execute(
                select(TenantAgentConfig).where(
                    TenantAgentConfig.company_id == company_id,
                    TenantAgentConfig.agent_name == agent_name,
                )
            )
            row = result.scalar_one_or_none()

            config = AgentConfig(
                agent_name=agent_name,
                is_enabled=row.is_enabled if row else True,
                custom_prompt_suffix=row.custom_prompt_suffix if row else None,
                tools_disabled=row.tools_disabled if row else [],
                confidence_threshold=float(row.confidence_threshold) if row else 0.75,
                tone=row.tone if row else "profissional",
                sector_context=row.sector_context if row else None,
            )
            await self._set_cache(company_id, agent_name, config)
            return config
        except Exception as exc:
            logger.warning("[TenantAgentConfig] fallback defaults: %s", exc)
            return AgentConfig(agent_name=agent_name)

    async def _get_from_cache(self, company_id: str, agent_name: str) -> Optional[AgentConfig]:
        try:
            import redis.asyncio as aioredis
            from app.core.config import settings
            r = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            async with r:
                raw = await r.get(f"agent_cfg:{company_id}:{agent_name}")
                if raw:
                    d = json.loads(raw)
                    return AgentConfig(**d)
        except Exception:
            pass
        return None

    async def _set_cache(self, company_id: str, agent_name: str, cfg: AgentConfig):
        try:
            import redis.asyncio as aioredis
            from app.core.config import settings
            r = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            async with r:
                import dataclasses
                await r.setex(
                    f"agent_cfg:{company_id}:{agent_name}",
                    _CACHE_TTL,
                    json.dumps(dataclasses.asdict(cfg)),
                )
        except Exception:
            pass


tenant_agent_config_service = TenantAgentConfigService()
```

---

#### Passo LIA-3: Integrar override no `PromptRegistry`

Adicionar método `get_tenant_prompt()` em `app/shared/prompts/prompt_registry.py`:

```python
def get_tenant_prompt(
    self,
    name: str,
    tenant_suffix: Optional[str] = None,
    tone: str = "profissional",
    sector_context: Optional[str] = None,
) -> Optional[str]:
    """
    Retorna prompt base + customizações do tenant.
    
    O prompt base nunca é substituído — apenas complementado.
    Ordem de composição:
      1. Prompt base (versão latest do registry)
      2. Bloco de contexto do setor (sector_context)
      3. Sufixo customizado do tenant (custom_prompt_suffix)
      4. Instrução de tom (tone)
    """
    base = self.get_prompt(name, "latest")
    if base is None:
        return None

    parts = [base]

    if sector_context:
        parts.append(
            f"\n\n## Contexto da Empresa\n{sector_context}"
        )

    TONE_INSTRUCTIONS = {
        "profissional": "Mantenha tom formal e profissional em todas as respostas.",
        "informal":     "Use linguagem mais próxima e informal, mas sempre respeitosa.",
        "tecnico":      "Priorize precisão técnica; use termos específicos da área sem simplificar.",
    }
    if tone and tone in TONE_INSTRUCTIONS:
        parts.append(f"\n\n## Tom de Comunicação\n{TONE_INSTRUCTIONS[tone]}")

    if tenant_suffix:
        parts.append(f"\n\n## Instruções Adicionais do Cliente\n{tenant_suffix}")

    return "\n".join(parts)
```

**Ponto de integração:** em cada agente especializado da LIA, onde hoje se faz:
```python
prompt = prompt_registry.get_prompt("sourcing")
```
Passa a ser:
```python
cfg = await tenant_agent_config_service.get_config(company_id, "sourcing", db)
prompt = prompt_registry.get_tenant_prompt(
    "sourcing",
    tenant_suffix=cfg.custom_prompt_suffix,
    tone=cfg.tone,
    sector_context=cfg.sector_context,
)
```

---

#### Passo LIA-4: Filtro de tools por tenant

Adicionar `filter_tools_for_tenant()` em `app/tools/tool_registry_loader.py`:

```python
def filter_tools_for_tenant(
    tools: list,
    disabled_tool_names: list[str],
    company_id: str,
) -> list:
    """
    Remove tools desabilitadas pelo tenant da lista de tools ativas.
    
    Args:
        tools:               lista de LangChain Tool objects já instanciados
        disabled_tool_names: nomes de tools que o tenant desabilitou
                             (vem de AgentConfig.tools_disabled)
        company_id:          usado apenas para log

    Returns:
        Lista filtrada de tools
    """
    if not disabled_tool_names:
        return tools

    disabled_set = set(disabled_tool_names)
    filtered = [t for t in tools if t.name not in disabled_set]

    removed = [t.name for t in tools if t.name in disabled_set]
    if removed:
        logger.info(
            "[ToolFilter] company=%s removeu tools=%s do agente", company_id, removed
        )
    return filtered
```

**Ponto de integração:** em `app/domains/sourcing/agents/sourcing_tool_registry.py` (e equivalentes por domínio), antes de montar o agente LangChain:

```python
tools = build_sourcing_tools(context)  # lista atual
cfg = await tenant_agent_config_service.get_config(company_id, "sourcing", db)
tools = filter_tools_for_tenant(tools, cfg.tools_disabled, company_id)
agent = create_react_agent(llm, tools, prompt)
```

---

#### Passo LIA-5: Endpoint de configuração — `POST /api/v1/admin/agents/configure`

Criar `app/api/v1/admin_agent_config.py`:

```python
"""
Admin — Configuração de agentes por tenant (Agent Studio API).

Endpoints:
  GET  /api/v1/admin/agents/config          → lista configs do tenant
  GET  /api/v1/admin/agents/config/{name}   → config de um agente específico
  PUT  /api/v1/admin/agents/config/{name}   → salva/atualiza config
  DELETE /api/v1/admin/agents/config/{name} → restaura defaults
"""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from app.auth.dependencies import require_admin
from app.core.database import get_db

router = APIRouter(prefix="/admin/agents/config", tags=["Agent Studio"])


class AgentConfigRequest(BaseModel):
    is_enabled: bool = True
    custom_prompt_suffix: Optional[str] = Field(
        None, max_length=2000,
        description="Texto adicionado ao final do system prompt. "
                    "Não pode sobrescrever regras éticas ou LGPD."
    )
    tools_disabled: List[str] = Field(
        default_factory=list,
        description="Nomes de tools a desabilitar. Ex: ['linkedin_search', 'export_csv']"
    )
    confidence_threshold: float = Field(0.75, ge=0.0, le=1.0)
    tone: str = Field("profissional", pattern="^(profissional|informal|tecnico)$")
    sector_context: Optional[str] = Field(None, max_length=500)


@router.get("")
async def list_agent_configs(
    x_company_id: str = Header(..., alias="X-Company-ID"),
    _user=Depends(require_admin),
    db=Depends(get_db),
):
    """Lista todas as configurações de agentes do tenant."""
    from app.models.tenant_agent_config import TenantAgentConfig
    from sqlalchemy import select
    result = await db.execute(
        select(TenantAgentConfig).where(TenantAgentConfig.company_id == x_company_id)
    )
    rows = result.scalars().all()
    return {"configs": [r.to_dict() for r in rows], "company_id": x_company_id}


@router.put("/{agent_name}")
async def upsert_agent_config(
    agent_name: str,
    body: AgentConfigRequest,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    _user=Depends(require_admin),
    db=Depends(get_db),
):
    """Cria ou atualiza configuração de um agente para o tenant."""
    from app.models.tenant_agent_config import TenantAgentConfig
    from sqlalchemy import select

    VALID_AGENTS = {
        "sourcing", "cv_screening", "interviewer", "scheduling",
        "wsi_evaluator", "analyst_feedback", "ats_integrator",
        "recruiter_assistant", "proactive_insights", "job_planner",
    }
    if agent_name not in VALID_AGENTS:
        from fastapi import HTTPException
        raise HTTPException(400, f"Agente '{agent_name}' inválido. Válidos: {VALID_AGENTS}")

    result = await db.execute(
        select(TenantAgentConfig).where(
            TenantAgentConfig.company_id == x_company_id,
            TenantAgentConfig.agent_name == agent_name,
        )
    )
    row = result.scalar_one_or_none()

    if row:
        row.is_enabled = body.is_enabled
        row.custom_prompt_suffix = body.custom_prompt_suffix
        row.tools_disabled = body.tools_disabled
        row.confidence_threshold = body.confidence_threshold
        row.tone = body.tone
        row.sector_context = body.sector_context
    else:
        row = TenantAgentConfig(
            company_id=x_company_id,
            agent_name=agent_name,
            **body.model_dump(),
        )
        db.add(row)

    await db.commit()

    # Invalidar cache Redis do tenant
    from app.services.tenant_agent_config_service import tenant_agent_config_service
    await tenant_agent_config_service._invalidate_cache(x_company_id, agent_name)

    return {"status": "ok", "agent": agent_name, "company_id": x_company_id}
```

---

#### Passo LIA-6: Hook no orquestrador — injetar config no início do chain

Em `app/orchestrator/main_orchestrator.py`, onde hoje ocorre:
```python
_tenant_ctx = await self._tenant_context_service.get_context(
    company_id=str(ctx.company_id), db=db
)
ctx.tenant_context_snippet = _tenant_ctx.to_prompt_snippet()
```

Adicionar logo abaixo:
```python
# Carregar config de agente do tenant para o domínio roteado
_agent_cfg = await tenant_agent_config_service.get_config(
    company_id=str(ctx.company_id),
    agent_name=route_result.domain_id,  # ex: "sourcing", "scheduling"
    db=db,
)
ctx.agent_config = _agent_cfg   # propagar no contexto para os agentes usarem

# Bloquear agente desabilitado pelo tenant
if not _agent_cfg.is_enabled:
    return self._build_disabled_agent_response(route_result.domain_id)
```

---

#### Resumo LIA — O que ficou faltando vs. o que foi mapeado

| Componente | Arquivo | Status |
|---|---|---|
| Tabela `tenant_agent_configs` | Migration SQL (Passo 1) | ❌ Criar |
| `TenantAgentConfigService` | `app/services/tenant_agent_config_service.py` | ❌ Criar |
| `PromptRegistry.get_tenant_prompt()` | `app/shared/prompts/prompt_registry.py` | ❌ Adicionar método |
| `filter_tools_for_tenant()` | `app/tools/tool_registry_loader.py` | ❌ Adicionar função |
| Endpoint `/admin/agents/config` | `app/api/v1/admin_agent_config.py` | ❌ Criar |
| Hook no orquestrador | `app/orchestrator/main_orchestrator.py` | ❌ Modificar |
| UI de configuração (frontend) | `plataforma-lia/` | ❌ Criar (fora do escopo deste guia) |

**Esforço estimado:** 2 sprints de backend (2 semanas) + 2 sprints de frontend para UI no-code.

---

### PARTE 2 — v5: Passo a Passo para Agent Studio

#### O que já existe e serve de base

| Arquivo existente | O que já faz | O que falta para Agent Studio |
|---|---|---|
| `src/domains/base.py` | `DomainPrompt` (ABC) com `get_system_prompt(context: DomainContext)` — cada domínio implementa seu próprio prompt | Não há mecanismo de override externo; o prompt é hard-coded na classe do domínio |
| `src/domains/registry.py` | `DomainRegistry` — `register()`, `get_instance()`, `list_domains()` | Registry é global e estático — sem filtro por tenant |
| `src/hub/catalog.py` | `DomainCatalog` — monta catálogo de domínios + rotas de navegação para o HubPlanner | Catálogo é único para todos os tenants — sem versão por empresa |
| `src/hub/planner.py` | `HubPlanner` — usa `DomainCatalog.get_catalog()` para decidir para qual domínio rotear | Sem awareness de tenant — não sabe quais domínios o tenant tem acesso |
| `src/hub/executor.py` | `HubExecutor.execute()` — chama `DomainOrchestrator.process_query(domain_id, query, context_data)` | `context_data` já tem `workspace_id` — é o ponto de entrada do tenant_id |
| `src/domains/base.py` | `DomainContext.workspace_id: Optional[int]` — campo já existe no dataclass | Não é usado para carregar config do tenant — apenas passado para a API |
| `src/api.py` | `ChatRequest.context_data: Dict[str, Any]` — payload livre; `workspace_id` é enviado pelo Rails via `context_data` | Sem middleware de validação de tenant; sem injeção de config |

**Conclusão sobre o v5:** `workspace_id` já chega no `DomainContext` — o tenant ID existe no sistema. O problema é que nada usa esse `workspace_id` para personalizar o comportamento dos domínios. O ponto cirúrgico de intervenção é o `DomainOrchestrator._build_context()` que constrói o `DomainContext` — é ali que a config do tenant precisa ser injetada.

---

#### Passo v5-1: `src/hub/tenant_config.py` — loader de config por tenant

Criar `src/hub/tenant_config.py`:

```python
"""
TenantConfig — carrega configuração de agentes por workspace_id.

O v5 não tem DB próprio. A config vive no Rails ATS (ats_api).
Este loader chama a API interna do Rails e cacheia em Redis.

Estrutura da config:
{
  "workspace_id": 42,
  "domains_enabled": ["jobs", "applies", "sourcing", "scheduling"],
  "domain_overrides": {
    "sourcing": {
      "custom_prompt_suffix": "Foco em candidatos CLT para logística.",
      "tools_disabled":       ["enrich_linkedin"],
      "confidence_threshold": 0.80,
      "tone":                 "informal"
    },
    "jobs": {
      "custom_prompt_suffix": null,
      "tools_disabled":       [],
      "confidence_threshold": 0.75,
      "tone":                 "profissional"
    }
  }
}
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import urllib.request

logger = logging.getLogger(__name__)

_ALL_DOMAINS = [
    "jobs", "applies", "sourcing", "sourced_profile_sourcing",
    "scheduling", "evaluation", "insights", "messaging", "autonomous",
]
_CACHE_TTL = 300  # 5 minutos


@dataclass
class DomainOverride:
    custom_prompt_suffix: Optional[str] = None
    tools_disabled: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.75
    tone: str = "profissional"
    sector_context: Optional[str] = None


@dataclass
class TenantConfig:
    workspace_id: int
    domains_enabled: List[str] = field(default_factory=lambda: list(_ALL_DOMAINS))
    domain_overrides: Dict[str, DomainOverride] = field(default_factory=dict)

    def is_domain_enabled(self, domain_id: str) -> bool:
        return domain_id in self.domains_enabled

    def get_override(self, domain_id: str) -> DomainOverride:
        return self.domain_overrides.get(domain_id, DomainOverride())


class TenantConfigLoader:

    _RAILS_BASE = os.getenv("RAILS_INTERNAL_URL", "http://ats_api:3000")

    def load(self, workspace_id: int) -> TenantConfig:
        """Carrega config do tenant. Tenta Redis → Rails API → defaults."""
        cached = self._from_redis(workspace_id)
        if cached:
            return cached

        config = self._from_rails_api(workspace_id)
        self._to_redis(workspace_id, config)
        return config

    def _from_redis(self, workspace_id: int) -> Optional[TenantConfig]:
        try:
            import redis
            from src.config.settings import get_settings
            r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
            raw = r.get(f"tenant_cfg_v5:{workspace_id}")
            if raw:
                return self._parse(workspace_id, json.loads(raw))
        except Exception as e:
            logger.debug("[TenantConfig] Redis miss: %s", e)
        return None

    def _from_rails_api(self, workspace_id: int) -> TenantConfig:
        """Chama /internal/agent_studio/config/{workspace_id} no Rails."""
        try:
            url = f"{self._RAILS_BASE}/internal/agent_studio/config/{workspace_id}"
            token = os.getenv("INTERNAL_API_TOKEN", "")
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                return self._parse(workspace_id, data)
        except Exception as e:
            logger.warning("[TenantConfig] Rails API falhou, usando defaults: %s", e)
            return TenantConfig(workspace_id=workspace_id)

    def _parse(self, workspace_id: int, data: dict) -> TenantConfig:
        overrides = {}
        for domain_id, ov in data.get("domain_overrides", {}).items():
            overrides[domain_id] = DomainOverride(
                custom_prompt_suffix=ov.get("custom_prompt_suffix"),
                tools_disabled=ov.get("tools_disabled", []),
                confidence_threshold=float(ov.get("confidence_threshold", 0.75)),
                tone=ov.get("tone", "profissional"),
                sector_context=ov.get("sector_context"),
            )
        return TenantConfig(
            workspace_id=workspace_id,
            domains_enabled=data.get("domains_enabled", list(_ALL_DOMAINS)),
            domain_overrides=overrides,
        )

    def _to_redis(self, workspace_id: int, config: TenantConfig):
        try:
            import redis
            import dataclasses
            from src.config.settings import get_settings
            r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
            payload = {
                "domains_enabled": config.domains_enabled,
                "domain_overrides": {
                    k: dataclasses.asdict(v)
                    for k, v in config.domain_overrides.items()
                },
            }
            r.setex(f"tenant_cfg_v5:{workspace_id}", _CACHE_TTL, json.dumps(payload))
        except Exception as e:
            logger.debug("[TenantConfig] Redis write falhou: %s", e)

    def invalidate(self, workspace_id: int):
        try:
            import redis
            from src.config.settings import get_settings
            r = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
            r.delete(f"tenant_cfg_v5:{workspace_id}")
        except Exception:
            pass


tenant_config_loader = TenantConfigLoader()
```

---

#### Passo v5-2: Filtrar domínios no `DomainCatalog` por tenant

Em `src/hub/catalog.py`, adicionar método `get_catalog_for_tenant()`:

```python
@classmethod
def get_catalog_for_tenant(cls, workspace_id: int) -> str:
    """
    Retorna catálogo de domínios filtrado para o tenant.
    Domínios não habilitados para o tenant são removidos do catálogo
    que o HubPlanner usa para rotear — o LLM do planner nunca os vê.
    """
    from src.hub.tenant_config import tenant_config_loader
    tenant_cfg = tenant_config_loader.load(workspace_id)

    sections = ["## Domínios Disponíveis (Backend AI Agents)"]
    domains = DomainRegistry.list_domains()

    for domain_id, domain_name in domains.items():
        # ← Filtro central: remove domínio se tenant não tem acesso
        if not tenant_cfg.is_domain_enabled(domain_id):
            continue

        instance = DomainRegistry.get_instance(domain_id)
        if not instance:
            continue
        actions = instance.get_allowed_actions()
        action_list = "\n".join(
            f"    - {a.id}: {a.description} (tipo: {a.action_type.value})"
            for a in actions
        )
        sections.append(
            f"- **{domain_id}** ({domain_name}): {instance.description}\n"
            f"  Ações:\n{action_list}"
        )

    # Rotas de navegação são iguais para todos (frontend não tem restrição por tenant agora)
    sections.append("\n## Rotas de Navegação (Frontend)")
    for route_id, route_info in cls.NAVIGATION_ROUTES.items():
        sections.append(f"- **{route_id}**: {route_info['description']}")

    return "\n".join(sections)
```

**Ponto de integração** — em `src/hub/planner.py`, onde hoje se usa `DomainCatalog.get_catalog()`:
```python
# Antes:
catalog = DomainCatalog.get_catalog()

# Depois:
workspace_id = context_data.get("workspace_id")
catalog = (
    DomainCatalog.get_catalog_for_tenant(workspace_id)
    if workspace_id else DomainCatalog.get_catalog()
)
```

---

#### Passo v5-3: Override de prompt por tenant no `DomainOrchestrator`

Em `src/domains/orchestrator.py`, dentro de `process_query()`, após `domain = DomainRegistry.get_instance(domain_id)`:

```python
def process_query(self, domain_id: str, user_query: str, context_data: Dict[str, Any]) -> DomainResponse:
    domain = DomainRegistry.get_instance(domain_id)
    if not domain:
        return DomainResponse(success=False, message=f"Domínio '{domain_id}' não encontrado", ...)

    # ← NOVO: carregar config do tenant
    workspace_id = context_data.get("workspace_id")
    tenant_cfg = None
    domain_override = None
    if workspace_id:
        from src.hub.tenant_config import tenant_config_loader
        tenant_cfg = tenant_config_loader.load(int(workspace_id))

        # Bloquear domínio desabilitado pelo tenant
        if not tenant_cfg.is_domain_enabled(domain_id):
            return DomainResponse(
                success=False,
                message=f"Este recurso não está habilitado para sua conta. "
                        f"Entre em contato com o suporte.",
                error="domain_disabled_for_tenant",
            )

        domain_override = tenant_cfg.get_override(domain_id)

    context = self._build_context(domain_id, context_data)

    # ← NOVO: injetar override na chamada de get_system_prompt
    # DomainWorkflow.run() vai chamar domain.get_system_prompt(context)
    # Wrappamos o domain com um proxy que aplica o override
    if domain_override:
        domain = _TenantOverrideDomain(domain, domain_override)

    # Resto do fluxo existente continua igual...
    result = self.workflow.run(domain, context, user_query)
    return result
```

O proxy `_TenantOverrideDomain` (criar no mesmo arquivo):

```python
class _TenantOverrideDomain:
    """
    Proxy leve que aplica override de tenant em cima de qualquer DomainPrompt.
    Não altera o comportamento do domínio — apenas compõe o system prompt.
    """
    def __init__(self, domain: "DomainPrompt", override: "DomainOverride"):
        self._domain = domain
        self._override = override

    def __getattr__(self, name):
        return getattr(self._domain, name)

    def get_system_prompt(self, context: "DomainContext") -> str:
        base_prompt = self._domain.get_system_prompt(context)
        parts = [base_prompt]

        if self._override.sector_context:
            parts.append(f"\n\n## Contexto da Empresa\n{self._override.sector_context}")

        TONE_MAP = {
            "profissional": "Mantenha tom formal e profissional.",
            "informal":     "Use linguagem próxima e acolhedora, mas respeitosa.",
            "tecnico":      "Priorize precisão técnica e terminologia específica da área.",
        }
        tone_instr = TONE_MAP.get(self._override.tone)
        if tone_instr:
            parts.append(f"\n\n## Tom\n{tone_instr}")

        if self._override.custom_prompt_suffix:
            parts.append(
                f"\n\n## Instruções do Cliente\n{self._override.custom_prompt_suffix}"
            )

        return "\n".join(parts)

    def get_tools(self, context: "DomainContext") -> list:
        """Filtra tools desabilitadas pelo tenant antes de passar para o grafo."""
        all_tools = self._domain.get_tools(context)
        if not self._override.tools_disabled:
            return all_tools
        disabled = set(self._override.tools_disabled)
        return [t for t in all_tools if t.name not in disabled]
```

---

#### Passo v5-4: Propagar `workspace_id` obrigatório no `api.py`

Em `src/api.py`, adicionar validação no endpoint `/chat`:

```python
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str | None = None
    hub_mode: bool = True
    context_data: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: int | None = None  # ← NOVO: pode vir aqui OU dentro de context_data

@app.post("/chat")
async def chat(req: ChatRequest):
    router = _get_router()
    loop = asyncio.get_event_loop()

    # ← NOVO: garantir que workspace_id esteja sempre em context_data
    context_data = {**req.context_data, "session_id": req.session_id}
    if req.workspace_id:
        context_data["workspace_id"] = req.workspace_id

    payload = {
        "question":    req.message,
        "domain":      req.domain,
        "context_data": context_data,
        "session_id":  req.session_id,
        "hub_mode":    req.hub_mode,
    }
    result = await loop.run_in_executor(None, router.route, payload)
    return JSONResponse(content={...})
```

O Rails ATS (`ats_api`) já envia `workspace_id` dentro de `context_data` — confirmado no código do `HubOrchestrator` que usa `context_data.get("workspace_id")` para a `SessionStore`. A mudança aqui apenas garante que também pode vir como campo de primeiro nível.

---

#### Passo v5-5: Endpoint de configuração no Rails (`ats_api`)

O v5 é um serviço Python sem DB próprio — as configurações de tenant vivem no **Rails** (`ats_api`). Criar no Rails:

```ruby
# config/routes.rb (adicionar no namespace :internal)
namespace :internal do
  resources :agent_studio, only: [] do
    collection do
      get  "config/:workspace_id", to: "agent_studio#show"
      put  "config/:workspace_id/domains/:domain_id", to: "agent_studio#update_domain"
      delete "config/:workspace_id/domains/:domain_id", to: "agent_studio#reset_domain"
    end
  end
end

# app/controllers/internal/agent_studio_controller.rb
module Internal
  class AgentStudioController < ApplicationController
    before_action :authenticate_internal_token!

    VALID_DOMAINS = %w[
      jobs applies sourcing sourced_profile_sourcing
      scheduling evaluation insights messaging autonomous
    ].freeze

    def show
      workspace = Workspace.find(params[:workspace_id])
      configs   = workspace.agent_studio_configs.index_by(&:domain_id)

      render json: {
        workspace_id:     workspace.id,
        domains_enabled:  workspace.agent_studio_domains_enabled || VALID_DOMAINS,
        domain_overrides: configs.transform_values(&:to_api_hash),
      }
    end

    def update_domain
      domain_id = params[:domain_id]
      return render_error("Domínio inválido") unless VALID_DOMAINS.include?(domain_id)

      workspace = Workspace.find(params[:workspace_id])
      config    = workspace.agent_studio_configs
                           .find_or_initialize_by(domain_id: domain_id)

      config.update!(
        custom_prompt_suffix:  params[:custom_prompt_suffix],
        tools_disabled:        params[:tools_disabled] || [],
        confidence_threshold:  params[:confidence_threshold] || 0.75,
        tone:                  params[:tone] || "profissional",
        sector_context:        params[:sector_context],
      )

      # Invalidar cache do Python v5
      TenantConfigInvalidatorJob.perform_later(workspace.id)

      render json: { status: "ok", domain_id: domain_id }
    end
  end
end
```

**Modelos Rails necessários:**
```ruby
# app/models/agent_studio_config.rb
class AgentStudioConfig < ApplicationRecord
  belongs_to :workspace
  validates :domain_id, inclusion: { in: Internal::AgentStudioController::VALID_DOMAINS }
  validates :confidence_threshold, numericality: { in: 0.0..1.0 }
  validates :tone, inclusion: { in: %w[profissional informal tecnico] }

  def to_api_hash
    {
      custom_prompt_suffix:  custom_prompt_suffix,
      tools_disabled:        tools_disabled || [],
      confidence_threshold:  confidence_threshold,
      tone:                  tone,
      sector_context:        sector_context,
    }
  end
end
```

---

#### Resumo v5 — O que ficou mapeado

| Componente | Arquivo | Status |
|---|---|---|
| `TenantConfigLoader` | `src/hub/tenant_config.py` | ❌ Criar (Passo v5-1) |
| Catálogo filtrado por tenant | `src/hub/catalog.py` | ❌ Adicionar método (Passo v5-2) |
| Override de prompt + tools | `src/domains/orchestrator.py` | ❌ Modificar (Passo v5-3) |
| `workspace_id` garantido no payload | `src/api.py` | ❌ Modificar (Passo v5-4) |
| Endpoint de config no Rails | `ats_api` Rails | ❌ Criar (Passo v5-5) |
| Model `AgentStudioConfig` | `ats_api` Rails | ❌ Criar migration + model |
| UI de configuração (frontend) | `ats_front` / `wedo-nuxt` | ❌ Fora do escopo deste guia |

**Esforço estimado:** 1.5 sprint Python + 1 sprint Rails (2.5 semanas total, pode ser paralelo).

---

### Comparativo LIA vs v5 para Agent Studio

| Dimensão | LIA | v5 |
|---|---|---|
| **Tenant ID no sistema** | `company_id` (já flui em todos os componentes via `ctx.company_id`) | `workspace_id` (já existe em `DomainContext`, vem via `context_data`) |
| **Base para override de prompt** | `PromptRegistry` com versionamento — só precisa adicionar `get_tenant_prompt()` | `get_system_prompt()` abstrato por domínio — precisa de proxy decorator |
| **Base para filtro de tools** | `tool_registry_metadata.yaml` com `allowed_agents` — adicionar dimensão `tenant` | Tools são instanciadas por domínio — precisa interceptar antes do grafo LangGraph |
| **Onde vive a config** | DB LIA (PostgreSQL local) — acesso direto via SQLAlchemy | DB Rails (`ats_api`) — acesso via HTTP interno |
| **Cache** | Redis já integrado (`TenantBudget` usa o mesmo padrão) | Redis disponível — padrão idêntico ao que TenantMemoryStore usa |
| **Complexidade de implementação** | ⭐⭐ Moderada — infraestrutura de tenant já madura | ⭐⭐⭐ Alta — v5 nunca foi multi-tenant; adicionar a noção de workspace em todos os pontos |
| **Risco de regressão** | Baixo — override é aditivo (suffix), não substitui prompt base | Médio — proxy `_TenantOverrideDomain` precisa implementar todos os métodos abstratos |
| **Tempo estimado (backend)** | ~2 semanas | ~2.5 semanas |
| **Dependência de outro time** | Não — tudo na LIA | Sim — precisa de endpoint Rails + migration no `ats_api` |

**Recomendação de ordem:** implementar na LIA primeiro (menor risco, infraestrutura mais madura), usar como piloto com 2-3 clientes, então portar o aprendizado para o v5.

---

## 🤖 Parte 3 — Como Cada Tipo de Agente do Mercado Funciona e Como Construir na WeDOTalent

> Baseado em leitura real dos arquivos de `lia-agent-system/` e `recruiter_agent_v5` (GitHub WeDOTalent).
> Para cada padrão: mecanismo técnico do mercado → UI do concorrente → precificação → implementação LIA com código → implementação v5 com código.

---

### Agente Tipo 1 — Digital Twins (Eightfold Project Andromeda)

#### Como o Eightfold implementa tecnicamente

Um **Digital Twin** no Eightfold é um agente que imita o raciocínio de um especialista humano interno (SME — Subject Matter Expert). O processo de criação tem 3 fases:

```
FASE 1 — CAPTURA DE CONHECIMENTO (1-2 semanas com o especialista)
├── Entrevistas gravadas com o SME (recrutador sênior, gestor de área)
│   └── Pergunta-padrão: "Por que você aprovou esse candidato?"
├── Histórico de decisões do especialista no ATS (últimos 12 meses)
│   ├── Aprovações: quais perfis viraram contratação
│   └── Rejeições: quais perfis foram descartados e por quê
├── Documentos produzidos pelo SME
│   ├── Scorecard de vagas anteriores
│   ├── Emails de feedback para candidatos
│   └── Notas de entrevista
└── Output: corpus de ~500-2000 exemplos rotulados

FASE 2 — INDEXAÇÃO DO CORPUS (automático, horas)
├── Cada exemplo vira um embedding de 768d (text-embedding-gecko)
├── Armazenado em pgvector com metadados:
│   ├── decision: "approved" | "rejected"
│   ├── reasoning: texto livre do SME
│   ├── candidate_profile: JSON resumido
│   └── job_context: título, área, nível
└── Resultado: base vetorial do twin = "cérebro" do especialista

FASE 3 — AGENTE TWIN (runtime)
├── Input: novo candidato + vaga
├── RAG: busca os K=5 exemplos mais similares no corpus do twin
├── Few-shot prompt:
│   "[SME Name] costuma aprovar perfis como: {exemplos_recuperados}
│    [SME Name] costuma rejeitar perfis como: {exemplos_rejeitados}
│    Avalie este candidato: {perfil_atual}"
└── Output: score + justificativa no estilo do SME
```

#### UI do Eightfold — Como aparece para o cliente

```
┌─────────────────────────────────────────────────────────────────┐
│  Eightfold AI — Project Andromeda                    [+ Novo Twin]│
├─────────────────────────────────────────────────────────────────┤
│  Seus Digital Twins                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐      │
│  │ 👤 Ana Costa            │  │ 👤 Pedro Oliveira        │      │
│  │ Gerente de Eng. Sênior  │  │ Especialista Comercial   │      │
│  │ ★★★★★ 94% precisão    │  │ ★★★★☆ 87% precisão    │      │
│  │ 312 decisões indexadas  │  │ 189 decisões indexadas   │      │
│  │ Vagas: Backend, Data    │  │ Vagas: Sales, CS         │      │
│  │ [Usar] [Ver raciocínio] │  │ [Usar] [Treinar mais]   │      │
│  └─────────────────────────┘  └─────────────────────────┘      │
│                                                                  │
│  Criar novo Twin:                                                │
│  1. Selecione o especialista ──────────────── [Ana Costa ▾]     │
│  2. Período de histórico ──────────────────── [12 meses ▾]     │
│  3. Áreas de vaga ─────────────── [Tecnologia] [+ Adicionar]   │
│  4. Importar documentos ──────────────────── [Arrastar aqui]   │
│  [Iniciar treinamento do Twin →]                                │
└─────────────────────────────────────────────────────────────────┘

Quando o recrutador usa o twin em uma vaga:
┌─────────────────────────────────────────────────────────────────┐
│  Candidato: Maria Souza  │  Twin: Ana Costa                     │
├─────────────────────────────────────────────────────────────────┤
│  Score Twin: 87/100  ▓▓▓▓▓▓▓▓▓░░                              │
│                                                                  │
│  💭 Raciocínio da Ana:                                          │
│  "Perfil muito similar ao João Silva (contratado em ago/24).    │
│   Os 6 anos em Python distribuído e a experiência com           │
│   sistemas de alta escala compensam a ausência de              │
│   graduação formal. Recomendo entrevista técnica."              │
│                                                                  │
│  📊 Exemplos que embasaram:                                     │
│  ✅ João Silva (contratado) — 94% similar                       │
│  ✅ Carla Lima (contratada) — 89% similar                       │
│  ❌ Rafael Torres (rejeitado) — 78% similar                     │
│                                                                  │
│  [Aceitar recomendação] [Ver exemplos] [Discordar + feedback]  │
└─────────────────────────────────────────────────────────────────┘
```

#### Precificação do Eightfold (Digital Twins)

| Modelo | Valor | Estrutura |
|---|---|---|
| **Plataforma base** | $150K–$500K/ano | Enterprise license, negociado |
| **Twin por especialista** | Incluído na licença | Até X twins conforme tier |
| **Overage de indexação** | ~$0.10–0.30/documento indexado | Acima da cota contratada |
| **Inferência (uso do twin)** | Incluída | Pooled compute |
| **Modelo de venda** | Direto enterprise, mínimo 1.000 funcionários | Sem self-serve |

#### Como construir na LIA — Digital Twins

**Arquivos que já existem e servem de base:**
- `app/services/gemini_voice_service.py` — transcrição de entrevistas gravadas com o SME
- `app/domains/sourcing/services/pgv_analyzer.py` — análise de candidatos via pgvector
- `app/domains/sourcing/services/es_analyzer.py` — busca híbrida (pgvector + ES)
- `app/shared/prompts/prompt_registry.py` — versionamento de prompts (o "prompt do twin")

**Passo LIA-Twin-1: Tabela de corpus do twin**

```sql
-- Migration: create_digital_twins
CREATE TABLE digital_twins (
    id              BIGSERIAL PRIMARY KEY,
    company_id      BIGINT      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    twin_name       VARCHAR(128) NOT NULL,  -- "Ana Costa - Eng. Sênior"
    sme_user_id     BIGINT      REFERENCES users(id),
    specialties     TEXT[]      DEFAULT '{}',  -- ["backend", "data", "cloud"]
    decision_count  INT         DEFAULT 0,
    accuracy_pct    NUMERIC(5,2),
    is_active       BOOLEAN     DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE twin_decisions (
    id              BIGSERIAL PRIMARY KEY,
    twin_id         BIGINT      NOT NULL REFERENCES digital_twins(id) ON DELETE CASCADE,
    decision        VARCHAR(16) NOT NULL CHECK (decision IN ('approved','rejected','maybe')),
    reasoning       TEXT        NOT NULL,  -- texto do SME explicando a decisão
    candidate_snapshot  JSONB,            -- snapshot do perfil no momento da decisão
    job_snapshot        JSONB,            -- snapshot da vaga
    embedding       vector(768),          -- embedding do reasoning+perfil combinados
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_twin_decisions_embedding
    ON twin_decisions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
CREATE INDEX idx_twin_decisions_twin ON twin_decisions(twin_id, decision);
```

**Passo LIA-Twin-2: `TwinKnowledgeIndexer` — captura de corpus**

Criar `lia-agent-system/app/services/twin_knowledge_indexer.py`:

```python
"""
TwinKnowledgeIndexer — constrói o corpus de conhecimento de um Digital Twin.

Fontes de dados:
  1. Transcrições de entrevistas (gemini_voice_service.py já faz isso)
  2. Histórico de decisões no ATS (aprovações/rejeições com reasoning)
  3. Documentos uploadados (scorecards, emails de feedback)
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.gemini_voice_service import GeminiVoiceService
from app.shared.providers.llm_factory import get_llm

logger = logging.getLogger(__name__)


class TwinKnowledgeIndexer:

    def __init__(self):
        self._voice_svc = None
        self._embedding_fn = None

    @property
    def voice_svc(self) -> GeminiVoiceService:
        if self._voice_svc is None:
            self._voice_svc = GeminiVoiceService()
        return self._voice_svc

    async def index_from_ats_history(
        self,
        twin_id: int,
        company_id: str,
        months_back: int = 12,
        db: AsyncSession = None,
    ) -> int:
        """
        Indexa histórico de decisões do ATS para o twin.
        Busca aprovações e rejeições com reasoning do recrutador.

        Returns: número de decisões indexadas
        """
        from app.models.job_application import JobApplication
        from app.models.digital_twin import TwinDecision

        # Buscar decisões com reasoning no ATS
        # (depende da estrutura do modelo Rails — adaptar conforme schema)
        result = await db.execute(
            select(JobApplication).where(
                JobApplication.company_id == company_id,
                JobApplication.reviewer_notes.isnot(None),
            ).limit(2000)
        )
        applications = result.scalars().all()

        indexed = 0
        for app in applications:
            decision = self._map_status_to_decision(app.status)
            if not decision:
                continue

            # Combinar perfil + reasoning para embedding
            text_for_embedding = (
                f"Decisão: {decision}\n"
                f"Cargo: {app.job_title}\n"
                f"Perfil: {json.dumps(app.candidate_snapshot or {})}\n"
                f"Raciocínio: {app.reviewer_notes}"
            )
            embedding = await self._embed(text_for_embedding)

            twin_decision = TwinDecision(
                twin_id=twin_id,
                decision=decision,
                reasoning=app.reviewer_notes or "",
                candidate_snapshot=app.candidate_snapshot,
                job_snapshot={"title": app.job_title},
                embedding=embedding,
            )
            db.add(twin_decision)
            indexed += 1

        await db.commit()
        logger.info("[TwinIndexer] twin=%d indexed %d decisions", twin_id, indexed)
        return indexed

    async def index_from_audio(
        self, twin_id: int, audio_bytes: bytes, db: AsyncSession
    ) -> str:
        """
        Transcreve entrevista gravada com o SME e indexa o raciocínio.
        Usa GeminiVoiceService (já integrado na LIA).
        """
        # 1. Transcrever áudio — serviço já existe na LIA
        transcription = await self.voice_svc.transcribe_audio(
            audio_bytes, "audio/mp4", "pt-BR"
        )

        # 2. Extrair decisões e reasonings do transcript via LLM
        llm = get_llm(tier="default")
        extract_prompt = f"""
        A seguir é a transcrição de uma entrevista onde um especialista de RH
        explica suas decisões sobre candidatos. Extraia cada decisão como JSON:
        
        Transcrição: {transcription.text}
        
        Retorne um array JSON:
        [
          {{
            "candidato_mencionado": "Nome ou descrição",
            "decisao": "approved|rejected|maybe",
            "raciocinio": "Texto explicativo do especialista"
          }}
        ]
        Responda APENAS com o JSON, sem texto adicional.
        """
        response = await llm.ainvoke(extract_prompt)
        decisions = json.loads(response.content)

        # 3. Indexar cada decisão extraída
        indexed = 0
        for d in decisions:
            text_for_embedding = f"Decisão: {d['decisao']}\nRaciocínio: {d['raciocinio']}"
            embedding = await self._embed(text_for_embedding)

            from app.models.digital_twin import TwinDecision
            db.add(TwinDecision(
                twin_id=twin_id,
                decision=d["decisao"],
                reasoning=d["raciocinio"],
                embedding=embedding,
            ))
            indexed += 1

        await db.commit()
        return f"Transcrição indexada: {indexed} decisões extraídas"

    async def _embed(self, text: str) -> List[float]:
        """Gera embedding de 768d. Reutiliza padrão do pgv_analyzer da LIA."""
        try:
            from app.domains.sourcing.services.pgv_analyzer import get_text_embedding
            return await get_text_embedding(text)
        except Exception as e:
            logger.warning("[TwinIndexer] embedding falhou: %s", e)
            return []

    @staticmethod
    def _map_status_to_decision(status: str) -> Optional[str]:
        APPROVED = {"hired", "offer_accepted", "passed_interview", "shortlisted"}
        REJECTED = {"rejected", "disqualified", "failed_screening", "declined"}
        if status in APPROVED:
            return "approved"
        if status in REJECTED:
            return "rejected"
        return None


twin_indexer = TwinKnowledgeIndexer()
```

**Passo LIA-Twin-3: `TwinInferenceService` — agente twin em runtime**

```python
"""
TwinInferenceService — avalia candidatos usando o raciocínio de um Digital Twin.

Fluxo:
  1. Recebe candidato + vaga
  2. Busca K=5 exemplos mais similares no corpus do twin (pgvector)
  3. Monta few-shot prompt com os exemplos
  4. LLM gera score + reasoning no estilo do especialista
"""
import json
import logging
from dataclasses import dataclass
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class TwinEvaluation:
    twin_id: int
    twin_name: str
    score: int                    # 0-100
    decision: str                 # "approved" | "rejected" | "maybe"
    reasoning: str                # texto no estilo do SME
    supporting_examples: List[dict]  # exemplos do corpus que embasaram


class TwinInferenceService:

    async def evaluate(
        self,
        twin_id: int,
        candidate_profile: dict,
        job_context: dict,
        k: int = 5,
        db: AsyncSession = None,
    ) -> TwinEvaluation:
        """
        Avalia candidato usando o twin. Retorna score + raciocínio do especialista.
        """
        # 1. Gerar embedding do candidato atual
        candidate_text = (
            f"Cargo: {job_context.get('title')}\n"
            f"Perfil: {json.dumps(candidate_profile)}"
        )
        from app.domains.sourcing.services.pgv_analyzer import get_text_embedding
        query_embedding = await get_text_embedding(candidate_text)

        # 2. Buscar exemplos similares no corpus do twin via pgvector
        examples = await self._retrieve_similar_examples(twin_id, query_embedding, k, db)

        # 3. Separar aprovados de rejeitados para o few-shot
        approved_ex = [e for e in examples if e["decision"] == "approved"][:3]
        rejected_ex = [e for e in examples if e["decision"] == "rejected"][:2]

        # 4. Buscar metadados do twin
        from app.models.digital_twin import DigitalTwin
        from sqlalchemy import select
        result = await db.execute(select(DigitalTwin).where(DigitalTwin.id == twin_id))
        twin = result.scalar_one()

        # 5. Montar few-shot prompt
        approved_block = "\n".join(
            f"  - Perfil aprovado: {e['candidate_snapshot']}\n"
            f"    Raciocínio: \"{e['reasoning']}\""
            for e in approved_ex
        ) or "  (sem exemplos aprovados ainda)"

        rejected_block = "\n".join(
            f"  - Perfil rejeitado: {e['candidate_snapshot']}\n"
            f"    Raciocínio: \"{e['reasoning']}\""
            for e in rejected_ex
        ) or "  (sem exemplos rejeitados ainda)"

        prompt = f"""
Você é {twin.twin_name}, especialista em recrutamento.
Com base no seu histórico de decisões:

PERFIS QUE VOCÊ COSTUMA APROVAR:
{approved_block}

PERFIS QUE VOCÊ COSTUMA REJEITAR:
{rejected_block}

Agora avalie este candidato para a vaga de {job_context.get('title')}:
{json.dumps(candidate_profile, ensure_ascii=False, indent=2)}

Responda com JSON:
{{
  "score": <0-100>,
  "decision": "approved|rejected|maybe",
  "reasoning": "<seu raciocínio em primeira pessoa, máx 3 frases>"
}}
"""
        from app.shared.providers.llm_factory import get_llm
        llm = get_llm(tier="default")
        response = await llm.ainvoke(prompt)
        result = json.loads(response.content)

        return TwinEvaluation(
            twin_id=twin_id,
            twin_name=twin.twin_name,
            score=result["score"],
            decision=result["decision"],
            reasoning=result["reasoning"],
            supporting_examples=examples,
        )

    async def _retrieve_similar_examples(
        self, twin_id: int, embedding: List[float], k: int, db: AsyncSession
    ) -> List[dict]:
        """Busca K exemplos mais similares no corpus do twin via pgvector."""
        result = await db.execute(
            f"""
            SELECT decision, reasoning, candidate_snapshot,
                   1 - (embedding <=> '{embedding}'::vector) AS similarity
            FROM twin_decisions
            WHERE twin_id = {twin_id}
              AND embedding IS NOT NULL
            ORDER BY embedding <=> '{embedding}'::vector
            LIMIT {k}
            """
        )
        rows = result.fetchall()
        return [
            {
                "decision": r[0],
                "reasoning": r[1],
                "candidate_snapshot": r[2] or {},
                "similarity": round(float(r[3]), 3),
            }
            for r in rows
        ]


twin_inference = TwinInferenceService()
```

**Passo LIA-Twin-4: Endpoint API**

```python
# app/api/v1/digital_twins.py
from fastapi import APIRouter, Depends, UploadFile, File, Header
from app.auth.dependencies import require_admin
from app.core.database import get_db
from app.services.twin_knowledge_indexer import twin_indexer
from app.services.twin_inference import twin_inference

router = APIRouter(prefix="/digital-twins", tags=["Digital Twins"])

@router.post("")
async def create_twin(body: CreateTwinRequest, x_company_id=Header(..., alias="X-Company-ID"),
                      _user=Depends(require_admin), db=Depends(get_db)):
    """Cria um Digital Twin para um especialista."""
    # Cria registro + dispara indexação do histórico ATS em background
    twin_id = await _create_twin_record(body, x_company_id, db)
    await twin_indexer.index_from_ats_history(twin_id, x_company_id, body.months_back, db)
    return {"twin_id": twin_id, "status": "indexing"}

@router.post("/{twin_id}/index-audio")
async def index_audio(twin_id: int, file: UploadFile = File(...),
                      db=Depends(get_db), _user=Depends(require_admin)):
    """Indexa entrevista gravada com o SME."""
    audio = await file.read()
    msg = await twin_indexer.index_from_audio(twin_id, audio, db)
    return {"status": "ok", "message": msg}

@router.post("/{twin_id}/evaluate")
async def evaluate_candidate(twin_id: int, body: EvaluateRequest,
                             db=Depends(get_db)):
    """Avalia candidato usando o Digital Twin."""
    evaluation = await twin_inference.evaluate(
        twin_id, body.candidate_profile, body.job_context, db=db
    )
    return {"evaluation": evaluation}
```

**Implementar no v5:** o v5 tem `TenantMemoryStore` com pgvector 768d e TTL — a tabela `tenant_memories` já é exatamente o que precisamos para o corpus do twin. Adicionar categoria `"twin_decision"` e campo `source_action = "twin:{twin_id}"`. O `RAGService` do v5 já implementa busca híbrida pgvector + keyword — reutilizar diretamente.

| Componente | LIA | v5 |
|---|---|---|
| Embedding | `pgv_analyzer.get_text_embedding()` | `EmbeddingService` + `RAGService` |
| Armazenamento vetorial | Criar `twin_decisions` table | Reutilizar `tenant_memories` (adicionar categoria "twin") |
| Transcrição | `GeminiVoiceService.transcribe_audio()` | Adicionar `audio_transcription_service.py` já existe no v5 |
| Inference | `TwinInferenceService` (criar) | Criar `src/services/twin_inference.py` |

**Esforço estimado:** 3 sprints (LIA) · 2.5 sprints (v5 — reutiliza mais)

---

### Agente Tipo 2 — Multi-Agent de Sourcing por Vaga (Juicebox Agents 2.0)

#### Como o Juicebox implementa tecnicamente

O modelo do Juicebox é "**N agentes em paralelo, um por vaga**". Cada agente é uma instância isolada com:

```
ESTRUTURA DE UM JUICEBOX AGENT (por vaga)
├── identity: {agent_id, job_id, job_title, criado_em}
├── search_strategy: critérios base extraídos da vaga (skills, senioridade, local)
├── outreach_config: templates de email, cadência (dia 1, dia 3, dia 7)
├── learning_state:
│   ├── positive_signals: [{candidato_id, o_que_gostei}] ← feedback "aprovar"
│   ├── negative_signals: [{candidato_id, por_que_rejeitar}] ← feedback "rejeitar"
│   └── calibration_version: int  ← incrementa a cada recalibração
└── performance:
    ├── profiles_viewed: int
    ├── emails_sent: int
    ├── replies_received: int
    └── conversion_rate: float

CICLO DE VIDA DO AGENTE
Day 0: Criação → extrai critérios da JD → configura estratégia inicial
Day 1-N:
  ├── Busca perfis (30+ fontes, 800M+ base)
  ├── Ranqueia por fit com estratégia atual
  ├── Envia emails personalizados (max 35/dia)
  └── Recebe feedback do recrutador
       ↓
       Recrutador rejeita candidato com motivo
       ↓ (real-time)
       Agente recalibra: ajusta pesos, exclui perfil-tipo
       ↓
       Próxima rodada usa estratégia calibrada
```

**O mecanismo de recalibração em tempo real** (o que diferencia do concorrente):
- Cada rejeição com motivo → LLM extrai "anti-critério" → adiciona ao vetor de exclusão
- Cada aprovação → LLM extrai "critério positivo" → reforça vetor de busca
- Critérios novos → nova busca em paralelo com a estratégia anterior → compara resultados

#### UI do Juicebox — Como aparece para o cliente

```
┌─────────────────────────────────────────────────────────────────┐
│  Juicebox Agents          [+ Novo Agente]  [Ver todos os agentes]│
├─────────────────────────────────────────────────────────────────┤
│  Agentes ativos (3/5 do plano)                                   │
│                                                                  │
│  ┌────────────────────────────────────┐                         │
│  │ 🤖 Agente: Senior Backend Engineer │  ● Ativo — Dia 12      │
│  │ Vaga #4521 · São Paulo / Remoto    │                         │
│  ├────────────────────────────────────┤                         │
│  │ Esta semana:                       │  Desde o início:        │
│  │ 📧 47 emails enviados              │  📋 312 perfis analis.  │
│  │ 💬 8 respostas (17%)               │  ✅ 23 aprovados        │
│  │ 🎯 3 entrevistas agendadas         │  ❌ 289 filtrados       │
│  ├────────────────────────────────────┤                         │
│  │ Estratégia atual (v3):             │                         │
│  │ ✅ Python + Go · 5+ anos           │                         │
│  │ ✅ Sistemas distribuídos           │                         │
│  │ ❌ Sem: bootcamp recente (<2 anos) │  ← adicionado no dia 8 │
│  │ ❌ Sem: apenas CRUD/e-commerce     │  ← adicionado no dia 10│
│  │ [Editar estratégia]                │                         │
│  └────────────────────────────────────┘                         │
│                                                                  │
│  Candidatos desta semana:                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Carlos M.  Fit: 94%  [✅ Aprovar] [❌ Rejeitar ▾] [📧]   │   │
│  │ Ana L.     Fit: 89%  [✅ Aprovar] [❌ Rejeitar ▾] [📧]   │   │
│  │ Paulo S.   Fit: 71%  [✅ Aprovar] [❌ Rejeitar ▾] [📧]   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Ao rejeitar → modal de motivo:                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Por que rejeitar Paulo S.?                        │           │
│  │ ○ Experiência insuficiente                        │           │
│  │ ○ Stack diferente do necessário                   │           │
│  │ ● Apenas CRUD/ecommerce, sem sistemas complexos   │           │
│  │ ○ Outro: [________________________]               │           │
│  │ [Confirmar rejeição + treinar agente]             │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

#### Precificação do Juicebox (Agents 2.0)

| Tier | Preço | Agentes | Perfis/mês | Emails/dia |
|---|---|---|---|---|
| **Starter** | ~$500/mês | 1 agente | 2.000 | 15/agente |
| **Growth** | ~$1.500/mês | 5 agentes | 10.000 | 35/agente |
| **Scale** | ~$4.000/mês | 20 agentes | 50.000 | 35/agente |
| **Enterprise** | Custom | Ilimitado | Custom | Custom |

**Modelo:** SaaS por número de agentes ativos (não por candidato).
Overage de emails: ~$0.02/email acima da cota.

#### Como construir na LIA — Multi-Agent Sourcing por Vaga

**Já existe na LIA:**
- `SourcingReActAgent` em `app/domains/sourcing/agents/sourcing_react_agent.py` — agente ReAct completo de sourcing
- `SourcingPlannerAgent`, `SourcingSearchAgent`, `SourcingEnrichAgent`, `SourcingEngagementAgent` — 4 subagentes especializados por etapa
- Stage context em `sourcing_stage_context.py` com: `search-criteria → talent-search → profile-analysis → shortlist-creation → outreach`

**O que falta:** cada agente acima é **único e síncrono** — não existe o modelo de "N instâncias por vaga, persistentes entre sessões, com feedback loop".

**Passo LIA-Sourcing-1: Modelo de dados para agente persistente por vaga**

```sql
CREATE TABLE sourcing_agents (
    id              BIGSERIAL PRIMARY KEY,
    company_id      BIGINT      NOT NULL REFERENCES companies(id),
    job_id          BIGINT      REFERENCES job_vacancies(id),
    agent_name      VARCHAR(128) NOT NULL,       -- "Agente Backend Sênior"
    status          VARCHAR(16)  DEFAULT 'active', -- active|paused|completed
    calibration_v   INT          DEFAULT 1,       -- versão da estratégia

    -- Estratégia atual (JSON atualizado a cada recalibração)
    search_strategy JSONB NOT NULL DEFAULT '{}', -- skills, seniority, location, exclusions
    outreach_config JSONB NOT NULL DEFAULT '{}', -- email templates, cadência

    -- Contadores de performance
    profiles_viewed INT DEFAULT 0,
    emails_sent     INT DEFAULT 0,
    emails_replied  INT DEFAULT 0,
    candidates_approved INT DEFAULT 0,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sourcing_agent_signals (
    id          BIGSERIAL PRIMARY KEY,
    agent_id    BIGINT      NOT NULL REFERENCES sourcing_agents(id) ON DELETE CASCADE,
    signal_type VARCHAR(16) NOT NULL CHECK (signal_type IN ('positive','negative')),
    candidate_id BIGINT,
    reason      TEXT        NOT NULL,  -- motivo dado pelo recrutador
    anti_criteria TEXT[],              -- critérios extraídos pelo LLM da rejeição
    pos_criteria TEXT[],              -- critérios extraídos da aprovação
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

**Passo LIA-Sourcing-2: `SourcingAgentOrchestrator` — cria e gerencia N agentes por empresa**

Criar `lia-agent-system/app/services/sourcing_agent_orchestrator.py`:

```python
"""
SourcingAgentOrchestrator — gerencia múltiplos agentes de sourcing persistentes.

Cada agente é uma instância isolada vinculada a uma vaga.
Reutiliza os subagentes existentes (SourcingSearchAgent, SourcingEnrichAgent, etc.)
mas adiciona: persistência entre sessões + feedback loop de recalibração.
"""
import json
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.providers.llm_factory import get_llm

logger = logging.getLogger(__name__)


class SourcingAgentOrchestrator:

    async def create_agent(
        self, company_id: str, job_id: int, db: AsyncSession
    ) -> dict:
        """
        Cria um novo agente de sourcing para uma vaga.
        Extrai a estratégia inicial automaticamente da JD.
        """
        # 1. Carregar vaga do ATS
        job = await self._load_job(job_id, db)

        # 2. Extrair estratégia inicial da JD via LLM
        strategy = await self._extract_strategy_from_jd(job["description"], job["title"])

        # 3. Persistir agente
        from app.models.sourcing_agent import SourcingAgent
        agent = SourcingAgent(
            company_id=company_id,
            job_id=job_id,
            agent_name=f"Agente {job['title']}",
            search_strategy=strategy,
            outreach_config=self._default_outreach_config(),
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        logger.info("[SourcingAgentOrchestrator] Criado agent_id=%d para job_id=%d", agent.id, job_id)
        return {"agent_id": agent.id, "strategy": strategy}

    async def process_feedback(
        self,
        agent_id: int,
        candidate_id: int,
        signal_type: str,    # "positive" | "negative"
        reason: str,
        db: AsyncSession,
    ) -> dict:
        """
        Processa feedback do recrutador e recalibra a estratégia do agente.
        Este é o coração do feedback loop em tempo real.
        """
        # 1. Carregar agente
        result = await db.execute(
            select(SourcingAgent).where(SourcingAgent.id == agent_id)  # type: ignore
        )
        agent = result.scalar_one()

        # 2. Extrair critérios do motivo via LLM
        llm = get_llm(tier="fast")  # Haiku — tarefa simples
        extract_prompt = f"""
        Um recrutador {('aprovou' if signal_type == 'positive' else 'rejeitou')} um candidato.
        Motivo: "{reason}"
        
        Extraia os critérios técnicos como lista de strings curtas (máx 5 itens).
        Responda APENAS com JSON: {{"criterios": ["critério 1", "critério 2"]}}
        """
        resp = await llm.ainvoke(extract_prompt)
        criterios = json.loads(resp.content).get("criterios", [])

        # 3. Persistir sinal
        from app.models.sourcing_agent import SourcingAgentSignal
        signal = SourcingAgentSignal(
            agent_id=agent_id,
            signal_type=signal_type,
            candidate_id=candidate_id,
            reason=reason,
            anti_criteria=criterios if signal_type == "negative" else [],
            pos_criteria=criterios if signal_type == "positive" else [],
        )
        db.add(signal)

        # 4. Recalibrar estratégia do agente
        new_strategy = await self._recalibrate_strategy(agent, signal_type, criterios)
        agent.search_strategy = new_strategy
        agent.calibration_v += 1

        await db.commit()
        logger.info(
            "[SourcingAgentOrchestrator] agent=%d recalibrado para v%d | signal=%s | criterios=%s",
            agent_id, agent.calibration_v, signal_type, criterios
        )
        return {"calibration_version": agent.calibration_v, "new_strategy": new_strategy}

    async def run_sourcing_cycle(
        self, agent_id: int, db: AsyncSession
    ) -> List[dict]:
        """
        Executa um ciclo de sourcing para o agente.
        Reutiliza SourcingSearchAgent + SourcingEnrichAgent existentes da LIA.
        """
        result = await db.execute(
            select(SourcingAgent).where(SourcingAgent.id == agent_id)  # type: ignore
        )
        agent = result.scalar_one()

        # Reutilizar SourcingSearchAgent existente com a estratégia do agente
        from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
        from app.shared.agents.agent_interface import AgentInput

        search_agent = SourcingSearchAgent()
        agent_input = AgentInput(
            message=self._strategy_to_query(agent.search_strategy),
            context={
                "company_id": agent.company_id,
                "job_id": agent.job_id,
                "sourcing_agent_id": agent_id,
            },
        )
        output = await search_agent.process(agent_input)

        # Atualizar contadores
        candidates = output.data.get("candidates", [])
        agent.profiles_viewed += len(candidates)
        await db.commit()

        return candidates

    async def _extract_strategy_from_jd(self, jd: str, title: str) -> dict:
        llm = get_llm(tier="fast")
        prompt = f"""
        Extraia os critérios de busca desta vaga para um agente de sourcing.
        Vaga: {title}
        Descrição: {jd[:2000]}
        
        Responda com JSON:
        {{
          "required_skills": ["skill1", "skill2"],
          "seniority": "junior|mid|senior|lead",
          "location": "cidade ou remote",
          "min_years_exp": 0,
          "exclusions": []
        }}
        """
        resp = await llm.ainvoke(prompt)
        return json.loads(resp.content)

    async def _recalibrate_strategy(
        self, agent, signal_type: str, criterios: List[str]
    ) -> dict:
        strategy = dict(agent.search_strategy)
        if signal_type == "negative":
            strategy.setdefault("exclusions", [])
            strategy["exclusions"] = list(set(strategy["exclusions"] + criterios))
        else:
            strategy.setdefault("positive_signals", [])
            strategy["positive_signals"] = list(set(
                strategy.get("positive_signals", []) + criterios
            ))
        return strategy

    @staticmethod
    def _strategy_to_query(strategy: dict) -> str:
        skills = ", ".join(strategy.get("required_skills", []))
        loc = strategy.get("location", "")
        excl = strategy.get("exclusions", [])
        excl_str = f" Excluir: {', '.join(excl)}." if excl else ""
        return f"Buscar candidatos com {skills} em {loc}.{excl_str}"

    @staticmethod
    def _default_outreach_config() -> dict:
        return {
            "template_initial": "Olá {nome}, vi seu perfil e gostaria de conversar sobre uma oportunidade em {empresa}...",
            "template_followup": "Olá {nome}, seguindo minha mensagem anterior...",
            "cadence_days": [1, 3, 7],
            "max_emails_per_day": 35,
        }

    async def _load_job(self, job_id: int, db: AsyncSession) -> dict:
        from app.models.job_vacancy import JobVacancy
        result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
        job = result.scalar_one()
        return {"title": job.title, "description": job.description}


sourcing_agent_orchestrator = SourcingAgentOrchestrator()
```

**Implementar no v5:** o v5 tem 9 subagentes de sourcing (`search`, `planner`, `orchestrator`, `router`, `action`, `analytics`, `comparison`, `detail`, `report`) e o `QUERY_PATTERNS` que mapeia intenções a pipelines. A estratégia de implementação no v5:

1. Adicionar `workspace_id` + `sourcing_agent_id` no `context_data` passado para o hub
2. O `HubPlanner` detecta domínio `sourced_profile_sourcing` + verifica se há agente persistente vinculado à vaga
3. O `SourcingAgentOrchestrator` (criar em `src/services/sourcing_agent_orchestrator.py`) usa os mesmos subagentes existentes mas carrega a estratégia do DB antes de cada ciclo

**Esforço estimado:** 2.5 sprints (LIA — reutiliza subagentes) · 2 sprints (v5 — estrutura mais simples)

---

### Agente Tipo 3 — Agentes por Setor/Template (Phenom X+ Studio)

#### Como o Phenom implementa tecnicamente

O Phenom X+ Studio usa o conceito de **Agent Templates** — configurações pré-montadas por setor industrial. Em vez de o cliente criar do zero, ele escolhe um template e personaliza apenas o que precisa:

```
ARQUITETURA DO PHENOM X+ STUDIO

agent_template_library: {                    ← biblioteca de templates
  "manufacturing": {
    name: "Agente para Manufatura",
    description: "Triagem acelerada para posições operacionais de chão de fábrica",
    system_prompt_base: "...",               ← prompt otimizado para o setor
    screening_questions: [                   ← perguntas padrão do setor
      "Você tem disponibilidade para turnos noturnos?",
      "Possui NR-35 (trabalho em altura)?",
      "Experiência com linha de montagem?"
    ],
    tools_enabled: ["voice_screening", "schedule", "bulk_outreach"],
    tools_disabled: ["linkedin_search"],     ← linkedin é irrelevante para operacional
    scoring_weights: {
      "certifications": 0.4,               ← NRs valem mais que graduação
      "experience_years": 0.3,
      "location_proximity": 0.3,           ← deslocamento é fator crítico
    },
    languages_supported: ["pt-BR", "es"],
    created_at: "2025-04-10"
  },
  "healthcare": { ... },
  "retail": { ... },
  "transportation": { ... },
  "technology": { ... }
}

FLUXO DE CRIAÇÃO DO AGENTE PELO CLIENTE (no-code):
1. Cliente escolhe template (ex: "Manufatura")
2. Phenom mostra campos pré-preenchidos
3. Cliente ajusta: nome do agente, perguntas extras, tom
4. Click "Ativar" → agente fica disponível no portal de candidatos
5. Candidatos interagem com o agente (chat ou voz)
6. Agente triagem automática → envia approved para ATS
```

#### UI do Phenom X+ Studio — Como aparece para o cliente

```
┌─────────────────────────────────────────────────────────────────┐
│  X+ Agent Studio                                [Meus Agentes ▾]│
├─────────────────────────────────────────────────────────────────┤
│  Criar Agente — Passo 1 de 3: Escolha o template               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 🏭           │  │ 🏥           │  │ 🛒           │          │
│  │ MANUFATURA   │  │ SAÚDE        │  │ VAREJO       │          │
│  │              │  │              │  │              │          │
│  │ Para vagas   │  │ Para vagas   │  │ Para vagas   │          │
│  │ operacionais │  │ de saúde e   │  │ de atendente │          │
│  │ e linha de   │  │ cuidadores   │  │ e estoque    │          │
│  │ montagem     │  │              │  │              │          │
│  │ [Selecionar] │  │ [Selecionar] │  │ [Selecionar] │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 🚛           │  │ 💻           │  │ ✨           │          │
│  │ TRANSPORTE   │  │ TECNOLOGIA   │  │ PERSONALIZADO│          │
│  │ [Selecionar] │  │ [Selecionar] │  │ [Criar do 0] │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ─────────────── Passo 2: Personalizar ──────────────────────  │
│  Nome do agente: [Agente Manufatura Unidade SP_____________]    │
│  Idioma: [Português ▾]  Tom: [○Formal ●Amigável ○Direto]       │
│                                                                  │
│  Perguntas de triagem:                               [+ Add]    │
│  ✅ Disponibilidade para turnos? ─────────────────── [✎] [🗑]  │
│  ✅ Possui NR-35?  ─────────────────────────────────── [✎] [🗑] │
│  + [Adicionar pergunta personalizada]                            │
│                                                                  │
│  ─────────────── Passo 3: Publicar ──────────────────────────  │
│  Canal: ●Chat no portal  ○Voz (telefone)  ○WhatsApp             │
│  [← Voltar]          [Pré-visualizar] [Ativar Agente →]         │
└─────────────────────────────────────────────────────────────────┘
```

#### Precificação do Phenom X+ Studio

| Tier | Preço | Agentes | Candidatos/mês | Canais |
|---|---|---|---|---|
| **X+ Core** | ~$80K/ano | 3 agentes | 5.000 | Chat |
| **X+ Professional** | ~$150K/ano | 10 agentes | 20.000 | Chat + Voz |
| **X+ Enterprise** | Custom | Ilimitado | Ilimitado | Todos |
| **Por agente extra** | ~$8K/ano | +1 agente | — | — |

**Add-ons:** Avatar de entrevista (+$25K/ano) · Detecção de fraude (+$15K/ano) · Analytics avançado (+$10K/ano).

#### Como construir na LIA — Agent Templates por Setor

**Já existe na LIA:**
- `TenantAgentConfigService` (criado na Parte 1) — armazena config por tenant+agente
- `PromptRegistry.get_tenant_prompt()` — composição de prompts
- Agente de voz: `deepgram_service.py` + `lia_voice.py` + `gemini_voice_service.py`

**Passo LIA-Template-1: Biblioteca de templates embutida no código**

Criar `lia-agent-system/app/shared/agent_templates/sector_templates.py`:

```python
"""
Biblioteca de templates de agente por setor industrial.
Equivalente ao que o Phenom X+ Studio chama de "Agent Templates".

Para adicionar um template novo:
  1. Adicionar entrada no dict SECTOR_TEMPLATES
  2. Deploy — nenhuma migration necessária (templates são read-only, config por tenant vai no DB)
"""
from typing import Dict, Any, List

SECTOR_TEMPLATES: Dict[str, Dict[str, Any]] = {

    "manufacturing": {
        "display_name": "Manufatura",
        "description": "Para vagas operacionais, linha de montagem e chão de fábrica",
        "icon": "🏭",
        "system_prompt_suffix": (
            "Foque em critérios práticos: disponibilidade de turno, proximidade geográfica, "
            "certificações NR e experiência com equipamentos específicos. "
            "Não penalize ausência de graduação formal em vagas operacionais. "
            "Pergunte sobre disponibilidade para horas extras antes de qualquer outra coisa."
        ),
        "default_screening_questions": [
            "Você tem disponibilidade para trabalhar em turnos (manhã/tarde/noite)?",
            "Qual é sua distância de deslocamento até a unidade?",
            "Possui alguma certificação NR (NR-10, NR-12, NR-35)? Se sim, quais?",
            "Tem experiência com linha de montagem ou processos industriais?",
        ],
        "scoring_weights": {
            "certifications": 0.40,
            "experience_years": 0.30,
            "location_proximity": 0.30,
        },
        "tools_enabled": [
            "voice_screening", "schedule_interview",
            "bulk_outreach", "send_screening_form"
        ],
        "tools_disabled": ["linkedin_search", "github_search"],
        "confidence_threshold": 0.70,
        "tone": "informal",
    },

    "healthcare": {
        "display_name": "Saúde",
        "description": "Para vagas de enfermagem, cuidadores, técnicos de saúde",
        "icon": "🏥",
        "system_prompt_suffix": (
            "Priorize habilitação profissional, experiência clínica e registro em conselho (COREN, CRM). "
            "Pergunte sobre especialidades e experiência com equipamentos médicos específicos. "
            "Seja empático e compreensivo — candidatos da saúde têm agenda complexa."
        ),
        "default_screening_questions": [
            "Qual é seu número de registro no conselho profissional (COREN/CRM)?",
            "Possui experiência em qual área clínica? (UTI, PS, ambulatório, home care)",
            "Tem disponibilidade para plantões de 12h ou 24h?",
            "Possui ACLS ou BLS atualizado?",
        ],
        "scoring_weights": {
            "professional_license": 0.50,
            "clinical_experience": 0.35,
            "certifications": 0.15,
        },
        "tools_enabled": ["schedule_interview", "send_screening_form", "verify_credentials"],
        "tools_disabled": ["linkedin_search"],
        "confidence_threshold": 0.80,
        "tone": "profissional",
    },

    "retail": {
        "display_name": "Varejo",
        "description": "Para atendentes, operadores de caixa e repositores",
        "icon": "🛒",
        "system_prompt_suffix": (
            "Foque em disponibilidade (fins de semana são obrigatórios no varejo), "
            "habilidades de atendimento ao cliente e experiência com PDV. "
            "Considere candidatos sem experiência se demonstrarem proatividade."
        ),
        "default_screening_questions": [
            "Você tem disponibilidade para trabalhar aos fins de semana e feriados?",
            "Tem experiência com atendimento ao cliente?",
            "Já trabalhou com sistema de caixa/PDV?",
            "Qual é sua disponibilidade de horário (parcial/integral)?",
        ],
        "scoring_weights": {
            "availability": 0.40,
            "customer_service_exp": 0.35,
            "pdv_experience": 0.25,
        },
        "tools_enabled": ["voice_screening", "schedule_interview", "bulk_outreach"],
        "tools_disabled": ["github_search", "linkedin_search"],
        "confidence_threshold": 0.65,
        "tone": "informal",
    },

    "technology": {
        "display_name": "Tecnologia",
        "description": "Para vagas de software, dados, infra e produto",
        "icon": "💻",
        "system_prompt_suffix": (
            "Avalie profundidade técnica, não apenas lista de tecnologias no currículo. "
            "Priorize contribuições open source, projetos reais e raciocínio sobre "
            "soluções técnicas. Para seniores, verifique experiência com sistemas em produção."
        ),
        "default_screening_questions": [
            "Descreva o sistema mais complexo que você já desenvolveu ou manteve.",
            "Quais tecnologias usa no dia a dia? Qual delas você domina mais profundamente?",
            "Tem contribuições open source ou projetos pessoais? Pode compartilhar?",
            "Como você lida com débito técnico no ambiente de trabalho?",
        ],
        "scoring_weights": {
            "technical_depth": 0.50,
            "experience_years": 0.30,
            "open_source": 0.20,
        },
        "tools_enabled": ["linkedin_search", "github_search", "schedule_interview"],
        "tools_disabled": ["bulk_outreach"],
        "confidence_threshold": 0.80,
        "tone": "tecnico",
    },

    "transportation": {
        "display_name": "Transporte e Logística",
        "description": "Para motoristas, operadores de logística e entregadores",
        "icon": "🚛",
        "system_prompt_suffix": (
            "CNH atualizada e histórico de infrações são os critérios mais críticos. "
            "Pergunte sobre categorias de habilitação, experiência com tipos de carga "
            "e disponibilidade para viagens. Verifique a validade do ASO."
        ),
        "default_screening_questions": [
            "Qual a categoria da sua CNH e quando vence?",
            "Tem histórico de infrações graves nos últimos 12 meses?",
            "Tem disponibilidade para viagens? (municipal/estadual/interestadual)",
            "Experiência com qual tipo de carga? (seca, refrigerada, perigosa)",
            "Seu ASO (Atestado de Saúde Ocupacional) está em dia?",
        ],
        "scoring_weights": {
            "license_validity": 0.40,
            "clean_record": 0.35,
            "cargo_experience": 0.25,
        },
        "tools_enabled": ["voice_screening", "schedule_interview", "verify_credentials"],
        "tools_disabled": ["linkedin_search", "github_search"],
        "confidence_threshold": 0.75,
        "tone": "informal",
    },
}


def get_template(sector: str) -> Dict[str, Any]:
    """Retorna template de setor. Raise ValueError se não encontrado."""
    if sector not in SECTOR_TEMPLATES:
        raise ValueError(f"Template '{sector}' não existe. Disponíveis: {list(SECTOR_TEMPLATES.keys())}")
    return SECTOR_TEMPLATES[sector]


def list_templates() -> List[Dict[str, str]]:
    """Lista templates disponíveis para exibir na UI."""
    return [
        {
            "id": k,
            "display_name": v["display_name"],
            "description": v["description"],
            "icon": v["icon"],
        }
        for k, v in SECTOR_TEMPLATES.items()
    ]
```

**Passo LIA-Template-2: Endpoint para instanciar um template como config de tenant**

```python
# Em app/api/v1/admin_agent_config.py — adicionar endpoint:

@router.post("/templates/{sector}/apply")
async def apply_sector_template(
    sector: str,
    agent_name: str,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    _user=Depends(require_admin),
    db=Depends(get_db),
):
    """
    Instancia um template de setor como configuração de agente do tenant.
    O cliente ainda pode sobrescrever qualquer campo depois.
    """
    from app.shared.agent_templates.sector_templates import get_template

    template = get_template(sector)

    # Upsert em tenant_agent_configs usando dados do template
    body = AgentConfigRequest(
        is_enabled=True,
        custom_prompt_suffix=template["system_prompt_suffix"],
        tools_disabled=template["tools_disabled"],
        confidence_threshold=template["confidence_threshold"],
        tone=template["tone"],
        sector_context=f"Setor: {template['display_name']}. {template['description']}",
    )

    # Reutilizar endpoint upsert existente
    return await upsert_agent_config(
        agent_name=agent_name,
        body=body,
        x_company_id=x_company_id,
        _user=_user,
        db=db,
    )


@router.get("/templates")
async def list_agent_templates():
    """Lista templates disponíveis para exibir na UI do Agent Studio."""
    from app.shared.agent_templates.sector_templates import list_templates
    return {"templates": list_templates()}
```

**Implementar no v5:** adicionar `src/hub/agent_templates.py` com o mesmo `SECTOR_TEMPLATES` dict. O endpoint de aplicação chama `TenantConfigLoader.invalidate()` + Rails `PUT /internal/agent_studio/config/{workspace_id}/domains/{domain_id}` com os dados do template.

**Esforço estimado:** 1 sprint (LIA — reutiliza Partes 1 e 2) · 1 sprint (v5)

---

### Agente Tipo 4 — Guided Autonomy (hireEZ EZ Agent)

#### Como o hireEZ implementa tecnicamente

O **EZ Agent** executa **múltiplas estratégias de busca em paralelo** e apresenta os resultados ranqueados. O diferencial: o agente não espera o recrutador definir tudo — ele propõe estratégias e executa em paralelo:

```
ARQUITETURA DO EZ AGENT (hireEZ)

INPUT do recrutador:
  - Título da vaga
  - Localização
  - 2-3 habilidades-chave (opcional)

FASE 1 — PLANEJAMENTO DE ESTRATÉGIAS (LLM, ~2s)
  O agente gera automaticamente 3-5 estratégias de busca:
  ┌─────────────────────────────────────────────┐
  │ Estratégia A: "Busca direta"                │
  │   → Skills exatas + localização             │
  │                                             │
  │ Estratégia B: "Adjacentes"                  │
  │   → Títulos similares + skills relacionadas │
  │                                             │
  │ Estratégia C: "Silver medalists"            │
  │   → Candidatos que passaram de entrevista   │
  │     em vagas similares recentemente         │
  │                                             │
  │ Estratégia D: "Reengajamento"               │
  │   → Candidatos inativos há 6+ meses com     │
  │     perfil compatível no banco interno      │
  └─────────────────────────────────────────────┘

FASE 2 — EXECUÇÃO PARALELA (30-90s)
  Estratégias A, B, C, D rodam simultaneamente
  em threads/workers separados → 45+ fontes de dados

FASE 3 — DEDUPLICAÇÃO + RANKING (LLM, ~5s)
  Merge de resultados → remove duplicatas (email/LinkedIn)
  → Score de fit calculado por estratégia
  → Ranking final: melhor candidato de cada estratégia
  → Apresenta top-N com "como foi encontrado"
```

#### UI do hireEZ EZ Agent — Como aparece para o cliente

```
┌─────────────────────────────────────────────────────────────────┐
│  EZ Agent — Nova busca                                           │
├─────────────────────────────────────────────────────────────────┤
│  Vaga: [Senior Data Engineer___________________________]         │
│  Local: [São Paulo, SP ou Remoto___________]                    │
│  Skills-chave (opcional): [Python] [Spark] [+ adicionar]        │
│  [🚀 Iniciar busca guiada]                                      │
│                                                                  │
│  ───── EZ Agent trabalhando ──────────────────────────────────  │
│  ✅ Estratégia A: Busca direta ─────────────── 89 candidatos    │
│  ✅ Estratégia B: Títulos adjacentes ──────────── 142 candidatos │
│  🔄 Estratégia C: Silver medalists ──────── (buscando...)       │
│  ✅ Estratégia D: Reengajamento banco interno ─── 23 candidatos │
│                                              Total: 300+ únicos  │
│                                                                  │
│  ───── Top candidatos (ranqueados) ───────────────────────────  │
│                                                                  │
│  #1  Ana Lima  ●●●●● 96 pts              via Estratégia A       │
│  8 anos · Senior Data Engineer · SP      Python, Spark, Airflow │
│  [Ver perfil] [Contatar] [Mover para pipeline]                  │
│                                                                  │
│  #2  Carlos M. ●●●●○ 88 pts              via Estratégia B       │
│  6 anos · Data Platform Lead · Remoto    PySpark, dbt, Kafka    │
│  [Ver perfil] [Contatar] [Mover para pipeline]                  │
│                                                                  │
│  #3  Beatriz S. ●●●●○ 85 pts             via Estratégia D       │
│  ♻️ Reengajamento — candidatou-se há 8 meses (vaga similar)     │
│  [Ver perfil] [Contatar] [Mover para pipeline]                  │
│                                                                  │
│  [Ver todos os 300 candidatos] [Refinar estratégias] [Exportar] │
└─────────────────────────────────────────────────────────────────┘
```

#### Precificação do hireEZ EZ Agent

| Tier | Preço | Buscas/mês | Estratégias paralelas | Fontes |
|---|---|---|---|---|
| **Professional** | ~$300/usuário/mês | 50 | 3 | 30+ |
| **Business** | ~$500/usuário/mês | 200 | 5 | 45+ |
| **Enterprise** | Custom | Ilimitado | Ilimitado | 45+ |

**Nota:** hireEZ cobra por **usuário-recrutador**, não por vaga ou candidato.

#### Como construir na LIA — Guided Autonomy

**Já existe na LIA:**
- `SourcingPlannerAgent` — define critérios de busca (etapa de planning)
- `SourcingSearchAgent` — executa busca (uma estratégia por vez, síncrona)
- `SourcingEnrichAgent` — enriquece perfis encontrados
- `app/domains/sourcing/services/vacancy_search.py` — busca por vagas similares

**O que falta:** execução paralela de múltiplas estratégias + merge + ranking.

**Passo LIA-Guided-1: `MultiStrategySearchService`**

Criar `lia-agent-system/app/services/multi_strategy_search.py`:

```python
"""
MultiStrategySearchService — executa múltiplas estratégias de busca em paralelo.
Implementa o padrão "guided autonomy" do hireEZ EZ Agent.

Estratégias implementadas:
  A. direct_search    — critérios exatos da vaga
  B. adjacent_titles  — títulos similares + skills relacionadas
  C. silver_medalists — candidatos que passaram por vagas similares
  D. reengagement     — candidatos inativos no banco com perfil compatível
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    strategy_id: str
    strategy_name: str
    candidates: List[Dict[str, Any]]
    count: int
    elapsed_ms: float


@dataclass
class MultiStrategyResult:
    total_unique: int
    candidates_ranked: List[Dict[str, Any]]  # deduplicados + ranqueados
    strategy_results: List[StrategyResult]
    elapsed_ms: float


class MultiStrategySearchService:

    async def search(
        self,
        job_title: str,
        required_skills: List[str],
        location: str,
        company_id: str,
        job_id: int = None,
        strategies: List[str] = None,
    ) -> MultiStrategyResult:
        """
        Executa múltiplas estratégias em paralelo e retorna candidatos ranqueados.
        """
        import time
        start = time.time()

        # Estratégias a executar (default: todas)
        enabled = strategies or ["direct", "adjacent", "silver", "reengagement"]

        # Executar todas em paralelo com asyncio.gather
        tasks = {}
        if "direct" in enabled:
            tasks["direct"] = self._strategy_direct(job_title, required_skills, location)
        if "adjacent" in enabled:
            tasks["adjacent"] = self._strategy_adjacent_titles(job_title, required_skills, location)
        if "silver" in enabled and job_id:
            tasks["silver"] = self._strategy_silver_medalists(job_id, required_skills)
        if "reengagement" in enabled:
            tasks["reengagement"] = self._strategy_reengagement(company_id, required_skills)

        results_raw = await asyncio.gather(*tasks.values(), return_exceptions=True)
        strategy_results = []
        for (sid, _), result in zip(tasks.items(), results_raw):
            if isinstance(result, Exception):
                logger.warning("[MultiStrategy] estratégia=%s falhou: %s", sid, result)
                continue
            strategy_results.append(result)

        # Deduplicar por email/LinkedIn URL
        all_candidates = []
        seen_ids: set = set()
        for sr in strategy_results:
            for c in sr.candidates:
                uid = c.get("email") or c.get("linkedin_url") or c.get("id")
                if uid and uid not in seen_ids:
                    seen_ids.add(uid)
                    c["found_via"] = sr.strategy_id
                    all_candidates.append(c)

        # Ranquear por fit score (descendente)
        ranked = sorted(all_candidates, key=lambda x: x.get("fit_score", 0), reverse=True)

        elapsed = (time.time() - start) * 1000
        return MultiStrategyResult(
            total_unique=len(ranked),
            candidates_ranked=ranked,
            strategy_results=strategy_results,
            elapsed_ms=elapsed,
        )

    async def _strategy_direct(
        self, job_title: str, skills: List[str], location: str
    ) -> StrategyResult:
        """Estratégia A: busca direta com critérios exatos."""
        import time; t = time.time()
        from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
        from app.shared.agents.agent_interface import AgentInput

        agent = SourcingSearchAgent()
        query = f"Buscar {job_title} com {', '.join(skills)} em {location}"
        output = await agent.process(AgentInput(message=query, context={}))
        candidates = output.data.get("candidates", [])

        return StrategyResult(
            strategy_id="direct",
            strategy_name="Busca Direta",
            candidates=candidates,
            count=len(candidates),
            elapsed_ms=(time.time() - t) * 1000,
        )

    async def _strategy_adjacent_titles(
        self, job_title: str, skills: List[str], location: str
    ) -> StrategyResult:
        """Estratégia B: títulos similares e skills relacionadas."""
        import time; t = time.time()
        from app.shared.providers.llm_factory import get_llm
        import json

        # Gerar títulos adjacentes via LLM
        llm = get_llm(tier="fast")
        resp = await llm.ainvoke(
            f"Liste 3 títulos de cargo similares a '{job_title}' no mercado brasileiro. "
            f"Responda APENAS com JSON: {{\"titles\": [\"título1\", \"título2\", \"título3\"]}}"
        )
        adj_titles = json.loads(resp.content).get("titles", [job_title])

        from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
        from app.shared.agents.agent_interface import AgentInput
        agent = SourcingSearchAgent()
        query = f"Buscar {' ou '.join(adj_titles)} com {', '.join(skills)} em {location}"
        output = await agent.process(AgentInput(message=query, context={}))
        candidates = output.data.get("candidates", [])

        return StrategyResult(
            strategy_id="adjacent",
            strategy_name="Títulos Adjacentes",
            candidates=candidates,
            count=len(candidates),
            elapsed_ms=(time.time() - t) * 1000,
        )

    async def _strategy_silver_medalists(
        self, job_id: int, skills: List[str]
    ) -> StrategyResult:
        """
        Estratégia C: candidatos que já foram entrevistados em vagas similares
        e chegaram à etapa final mas não foram contratados.
        Reutiliza vacancy_search.py da LIA para encontrar vagas similares.
        """
        import time; t = time.time()
        from app.domains.sourcing.services.vacancy_search import find_similar_vacancies

        similar_jobs = await find_similar_vacancies(job_id, limit=5)
        silver_candidates = []
        for similar_job in similar_jobs:
            # Buscar candidatos que chegaram à etapa de entrevista nessas vagas
            finalists = await self._get_job_finalists(similar_job["id"])
            silver_candidates.extend(finalists)

        return StrategyResult(
            strategy_id="silver",
            strategy_name="Silver Medalists",
            candidates=silver_candidates,
            count=len(silver_candidates),
            elapsed_ms=(time.time() - t) * 1000,
        )

    async def _strategy_reengagement(
        self, company_id: str, skills: List[str]
    ) -> StrategyResult:
        """
        Estratégia D: candidatos inativos há 6+ meses no banco interno
        com skills compatíveis. Evita sourcing externo caro.
        """
        import time; t = time.time()
        from app.domains.sourcing.services.pgv_analyzer import search_internal_candidates

        candidates = await search_internal_candidates(
            company_id=company_id,
            skills=skills,
            inactive_days_min=180,
        )
        return StrategyResult(
            strategy_id="reengagement",
            strategy_name="Reengajamento Banco Interno",
            candidates=candidates,
            count=len(candidates),
            elapsed_ms=(time.time() - t) * 1000,
        )

    @staticmethod
    async def _get_job_finalists(job_id: int) -> List[dict]:
        """Busca candidatos que chegaram à etapa de entrevista em uma vaga."""
        try:
            from app.core.database import get_db_sync
            from app.models.job_application import JobApplication
            # Buscar applies em etapas avançadas
            finalists = []  # implementar query real
            return finalists
        except Exception:
            return []


multi_strategy_search = MultiStrategySearchService()
```

**Implementar no v5:** usar `asyncio.gather()` com 4 chamadas paralelas ao `DomainOrchestrator.process_query()` (uma por estratégia, todas com domain `sourced_profile_sourcing`) + deduplicação pelo `candidate_resolver.py` existente no hub.

**Esforço estimado:** 2 sprints (LIA) · 1.5 sprints (v5 — `candidate_resolver.py` já existe)

---

### Agente Tipo 5 — Agente de Voz para Triagem (Phenom Interview Agent / Olivia)

#### Como o Phenom e a Olivia (Paradox) implementam tecnicamente

```
ARQUITETURA DO AGENTE DE VOZ DE TRIAGEM

Canal 1 — WebSocket (triagem via navegador/app):
  Candidato → microfone → WebSocket → STT (Deepgram) → texto
  → Agente LLM → resposta texto → TTS (OpenAI/ElevenLabs) → áudio
  → Candidato ouve

Canal 2 — Telefone outbound (OpenMic.ai / Twilio):
  Agente liga para candidato → gravação → STT → Agente LLM
  → TTS → fala para candidato → grava respostas

FLUXO DA ENTREVISTA DE VOZ (state machine):
  [INTRO] → [QUESTIONS] → [SCORING] → [CLOSING]

  INTRO: "Olá {nome}, sou a LIA, assistente da {empresa}.
          Vou fazer algumas perguntas rápidas sobre sua candidatura à vaga de {cargo}."

  QUESTIONS (N perguntas configuradas pelo recrutador):
    Para cada pergunta:
      1. Agente faz a pergunta em voz
      2. Candidato responde (máx 90s)
      3. Deepgram transcreve em tempo real
      4. Agente confirma entendimento ou pede esclarecimento
      5. Score parcial calculado

  SCORING:
    Resposta do candidato → embedding → compare com respostas ideais do SME
    → Score 0-100 por pergunta → Score final = média ponderada

  CLOSING: "Obrigada {nome}! Suas respostas foram registradas.
             O time de RH entrará em contato em até 3 dias úteis."
  → Envia resumo ao recrutador via webhook
```

#### UI do Phenom/Olivia — Como aparece para o cliente (recrutador) e candidato

**Tela do recrutador (configuração):**
```
┌─────────────────────────────────────────────────────────────────┐
│  Configurar Entrevista de Voz — Vaga: Operador de Logística     │
├─────────────────────────────────────────────────────────────────┤
│  Agente: ●LIA (texto+voz)  ○Somente voz  ○Somente texto        │
│  Canal: ●WhatsApp  ○Telefone automático  ○Link de acesso        │
│  Idioma: [Português BR ▾]                                        │
│  Duração máx: [10 min ▾]                                        │
│                                                                  │
│  Perguntas de triagem:                         [+ Nova pergunta] │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. "Você tem disponibilidade para turnos?"               │   │
│  │    Resposta ideal: "Sim, disponível"  Peso: 30%  [✎][🗑] │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 2. "Tem CNH válida categoria D ou E?"                    │   │
│  │    Resposta ideal: "Sim, categoria [D/E]" Peso: 40% [✎][🗑]│  │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 3. "Onde você mora atualmente?"                          │   │
│  │    Resposta ideal: <cidade próxima>  Peso: 30%  [✎][🗑]  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  [Pré-visualizar conversa] [Testar com meu número] [Ativar ▸]   │
└─────────────────────────────────────────────────────────────────┘
```

**O que o candidato vê (WhatsApp / link):**
```
┌─────────────────────────────────────────────────────────────────┐
│  LIA — Assistente de Recrutamento          [🔴 Gravando]        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🤖 "Olá João! Sou a LIA, assistente da LogisBr.               │
│       Vou te fazer 3 perguntas rápidas sobre a vaga             │
│       de Motorista. Levará cerca de 5 minutos.                  │
│       Pode começar quando quiser!"                               │
│                                                                  │
│  🎙️ [●●●●●●●●●●●●●●●●●●●●●●●●]  0:23                          │
│  "Sim, tenho disponibilidade para trabalhar de segunda a..."    │
│                                                                  │
│  ──────────────────────────────────────────────────────────     │
│  Pergunta 1/3  ████████░░░░░░░░░░░░  35%                       │
│                                                                  │
│  [⏸ Pausar]  [🔄 Repetir pergunta]  [💬 Mudar para texto]      │
└─────────────────────────────────────────────────────────────────┘
```

#### Precificação do Phenom Interview Agent / Olivia (Paradox)

| Produto | Preço | Modelo | Inclui |
|---|---|---|---|
| **Phenom Interview Agent** | +$25K/ano (add-on ao X+) | Licença anual | Triagem por voz + scoring |
| **Olivia (Paradox)** | $30K–$100K/ano | Enterprise, por volume | Voz + texto + agendamento |
| **OpenMic.ai** (white-label) | ~$0.15/minuto de ligação | Pay-per-use | STT + TTS + orquestração |
| **Deepgram Nova-2** | ~$0.0043/minuto | Pay-per-use | Somente STT |

**Para a WeDOTalent:** usar Deepgram (já integrado) para STT + OpenMic (já integrado) para chamadas outbound. Custo estimado por entrevista de 10 min: ~$0.20 de Deepgram + $1.50 de OpenMic = **~$1.70/entrevista** — repassar ao cliente com margem de 3x = ~$5/entrevista ou incluir em pacote.

#### Como construir na LIA — Agente de Voz para Triagem

**Já existe na LIA — base completa pronta:**
- `app/api/v1/lia_voice.py` — WebSocket + REST para voz (`VoiceTranscriptionResponse`, `VoiceChatResponse`)
- `app/services/gemini_voice_service.py` — STT via Gemini Flash (transcrição de arquivos de áudio)
- `app/api/v1/voice_screening_test.py` — `deepgram_service` + `openmic_service` já integrados
- `app/models/voice_screening.py` — modelo de dados de triagem por voz já existe

**O que já existe no modelo:**
```python
# app/models/voice_screening.py — já existe na LIA
class VoiceScreening:
    id, company_id, job_id, candidate_id
    agent_id        # ID do agente de voz configurado
    channel         # "whatsapp" | "web" | "phone"
    status          # "scheduled" | "in_progress" | "completed" | "failed"
    transcript      # JSON com a conversa completa
    score           # 0-100 score final
    scores_by_q     # JSONB {pergunta_id: score}
    duration_secs
    created_at, completed_at
```

**O que falta: conectar tudo em um fluxo de entrevista gerenciado por state machine.**

**Passo LIA-Voice-1: `VoiceInterviewStateMachine` — orquestrador da entrevista**

Criar `lia-agent-system/app/services/voice_interview_state_machine.py`:

```python
"""
VoiceInterviewStateMachine — controla o fluxo de uma entrevista de voz.

States:
  INTRO → QUESTION_{N} → SCORING → CLOSING → DONE

Cada state tem:
  - prompt do agente (o que a LIA fala)
  - handler de resposta do candidato
  - condição de transição para o próximo state

Reutiliza:
  - gemini_voice_service.py → STT (transcrição)
  - voice_service.py → TTS (síntese de fala para a LIA "falar")
  - PromptRegistry → prompts de entrevista configurados pelo tenant
"""
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

from app.services.gemini_voice_service import GeminiVoiceService
from app.shared.prompts.prompt_registry import prompt_registry

logger = logging.getLogger(__name__)


class InterviewState(Enum):
    INTRO = "intro"
    QUESTIONING = "questioning"
    SCORING = "scoring"
    CLOSING = "closing"
    DONE = "done"


@dataclass
class ScreeningQuestion:
    question_id: str
    text: str           # "Você tem disponibilidade para turnos noturnos?"
    ideal_answer: str   # resposta ideal para comparação de score
    weight: float       # peso no score final (soma = 1.0)
    max_duration_s: int = 90


@dataclass
class VoiceInterviewSession:
    session_id: str
    company_id: str
    job_id: int
    candidate_id: int
    candidate_name: str
    questions: List[ScreeningQuestion]
    state: InterviewState = InterviewState.INTRO
    current_q_idx: int = 0
    answers: Dict[str, str] = field(default_factory=dict)   # q_id → transcrição
    scores: Dict[str, float] = field(default_factory=dict)  # q_id → score 0-100
    final_score: Optional[float] = None


class VoiceInterviewStateMachine:

    def __init__(self):
        self._voice_svc = GeminiVoiceService()

    async def handle_audio_input(
        self,
        session: VoiceInterviewSession,
        audio_bytes: bytes,
        audio_format: str = "audio/webm",
    ) -> dict:
        """
        Processa input de áudio do candidato e avança o state machine.

        Returns:
            {
              "agent_text": "...",        # o que a LIA vai falar/escrever
              "agent_audio_b64": "...",   # TTS do texto (base64)
              "state": "questioning",
              "progress": 0.33,          # 0.0 a 1.0
              "is_done": False
            }
        """
        # 1. Transcrever áudio do candidato
        transcription = await self._voice_svc.transcribe_audio(
            audio_bytes, audio_format, "pt-BR"
        )
        candidate_answer = transcription.text
        logger.info(
            "[VoiceInterview] session=%s state=%s answer=%s",
            session.session_id, session.state.value, candidate_answer[:80]
        )

        # 2. Avançar state machine
        if session.state == InterviewState.INTRO:
            return await self._handle_intro(session)

        elif session.state == InterviewState.QUESTIONING:
            return await self._handle_answer(session, candidate_answer)

        elif session.state == InterviewState.SCORING:
            return await self._handle_scoring(session)

        elif session.state == InterviewState.CLOSING:
            return await self._handle_closing(session)

        return {"agent_text": "Obrigada! Entrevista encerrada.", "is_done": True}

    async def _handle_intro(self, session: VoiceInterviewSession) -> dict:
        """Gera mensagem de boas-vindas e faz primeira pergunta."""
        first_q = session.questions[0]
        text = (
            f"Olá {session.candidate_name}! Sou a LIA, assistente de recrutamento. "
            f"Vou fazer {len(session.questions)} perguntas rápidas. "
            f"Pode começar respondendo: {first_q.text}"
        )
        session.state = InterviewState.QUESTIONING
        session.current_q_idx = 0
        return self._build_response(session, text)

    async def _handle_answer(
        self, session: VoiceInterviewSession, answer: str
    ) -> dict:
        """Registra resposta atual e avança para próxima pergunta ou scoring."""
        current_q = session.questions[session.current_q_idx]

        # Registrar resposta
        session.answers[current_q.question_id] = answer

        # Score parcial via LLM
        score = await self._score_answer(answer, current_q)
        session.scores[current_q.question_id] = score

        # Avançar
        session.current_q_idx += 1
        if session.current_q_idx < len(session.questions):
            next_q = session.questions[session.current_q_idx]
            text = f"Entendido! Próxima pergunta: {next_q.text}"
        else:
            session.state = InterviewState.SCORING
            text = "Perfeito! Aguarde um momento enquanto processo suas respostas."

        return self._build_response(session, text)

    async def _handle_scoring(self, session: VoiceInterviewSession) -> dict:
        """Calcula score final e prepara mensagem de encerramento."""
        total = sum(
            session.scores.get(q.question_id, 0) * q.weight
            for q in session.questions
        )
        session.final_score = round(total, 1)
        session.state = InterviewState.CLOSING
        return await self._handle_closing(session)

    async def _handle_closing(self, session: VoiceInterviewSession) -> dict:
        """Mensagem de encerramento e disparo de webhook ao recrutador."""
        text = (
            f"Obrigada {session.candidate_name}! "
            f"Suas respostas foram registradas com sucesso. "
            f"O time de RH da empresa entrará em contato em breve. Até logo!"
        )
        session.state = InterviewState.DONE

        # Salvar resultado no banco + notificar recrutador
        await self._save_and_notify(session)

        return {**self._build_response(session, text), "is_done": True}

    async def _score_answer(self, answer: str, question: ScreeningQuestion) -> float:
        """Scoring via LLM: compara resposta com a resposta ideal."""
        from app.shared.providers.llm_factory import get_llm
        llm = get_llm(tier="fast")
        prompt = f"""
        Pergunta: "{question.text}"
        Resposta ideal: "{question.ideal_answer}"
        Resposta do candidato: "{answer}"
        
        Dê um score de 0 a 100 para a adequação da resposta.
        Responda APENAS com o número inteiro.
        """
        resp = await llm.ainvoke(prompt)
        try:
            return float(resp.content.strip())
        except Exception:
            return 50.0

    def _build_response(self, session: VoiceInterviewSession, text: str) -> dict:
        progress = session.current_q_idx / max(len(session.questions), 1)
        return {
            "agent_text": text,
            "state": session.state.value,
            "progress": round(progress, 2),
            "current_question": session.current_q_idx,
            "total_questions": len(session.questions),
            "is_done": session.state == InterviewState.DONE,
        }

    async def _save_and_notify(self, session: VoiceInterviewSession):
        """Salva resultado da entrevista e notifica recrutador."""
        try:
            from app.services.notification_service import notification_service
            await notification_service.send(
                company_id=session.company_id,
                event_type="voice_screening_completed",
                title=f"Triagem por voz concluída — {session.candidate_name}",
                body=f"Score: {session.final_score}/100 · {len(session.questions)} perguntas respondidas",
                severity="info",
                channels=["bell", "email"],
                metadata={
                    "candidate_id": session.candidate_id,
                    "job_id": session.job_id,
                    "score": session.final_score,
                    "answers": session.answers,
                    "scores_by_question": session.scores,
                },
            )
        except Exception as e:
            logger.warning("[VoiceInterview] notify falhou: %s", e)


voice_interview_state_machine = VoiceInterviewStateMachine()
```

**Passo LIA-Voice-2: Endpoint WebSocket para triagem em tempo real**

```python
# Em app/api/v1/lia_voice.py — adicionar endpoint WebSocket:

@voice_router.websocket("/voice/interview/{session_id}")
async def voice_interview_ws(
    websocket: WebSocket,
    session_id: str,
    db=Depends(get_db),
):
    """
    WebSocket de entrevista de voz em tempo real.
    
    Protocolo:
      → Cliente envia: {"type": "audio", "data": "<base64>", "format": "audio/webm"}
      ← Servidor responde: {"type": "agent", "text": "...", "state": "...", "progress": 0.33}
    
    Para triagem por telefone, usar POST /voice/interview/{session_id}/phone-call
    que dispara chamada outbound via openmic_service (já integrado na LIA).
    """
    await websocket.accept()

    # Carregar sessão de entrevista do Redis
    session = await _load_voice_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="session_not_found")
        return

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "audio":
                audio_bytes = base64.b64decode(data["data"])
                audio_format = data.get("format", "audio/webm")

                response = await voice_interview_state_machine.handle_audio_input(
                    session, audio_bytes, audio_format
                )

                # TTS: converter resposta da LIA em áudio
                audio_response = await voice_service.synthesize_speech(
                    response["agent_text"], language="pt-BR"
                )
                response["agent_audio_b64"] = base64.b64encode(
                    audio_response
                ).decode() if audio_response else None

                await websocket.send_json(response)

                if response.get("is_done"):
                    await websocket.close()
                    break

    except WebSocketDisconnect:
        logger.info("[VoiceInterview] ws desconectado: session=%s", session_id)

    except Exception as e:
        logger.error("[VoiceInterview] erro: %s", e)
        await websocket.close(code=1011)
```

**Implementar no v5:** adicionar rota WebSocket em `src/api.py` + criar `src/services/voice_interview_state_machine.py` (mesmo código acima, ajustando imports). O v5 já tem `tts_service.py` e `audio_transcription_service.py` — toda a infraestrutura de voz já está lá.

| Componente | LIA | v5 |
|---|---|---|
| STT | `GeminiVoiceService.transcribe_audio()` ✅ | `audio_transcription_service.py` ✅ |
| TTS | `voice_service.synthesize_speech()` ✅ | `tts_service.py` ✅ |
| Chamada telefônica | `openmic_service` ✅ | Criar integração OpenMic |
| State machine | `VoiceInterviewStateMachine` ❌ Criar | ❌ Criar |
| WebSocket endpoint | `lia_voice.py` — adicionar rota ✅ | `src/api.py` — adicionar rota |
| Scoring de respostas | `_score_answer()` via LLM ❌ Criar | ❌ Criar |

**Esforço estimado:** 2 sprints (LIA — infraestrutura 80% pronta) · 2.5 sprints (v5)

---

### Resumo: Todos os Tipos de Agente × Esforço × Custo Operacional

| Tipo de Agente | Referência | LIA (sprints) | v5 (sprints) | Custo operacional est. |
|---|---|---|---|---|
| **Digital Twins** | Eightfold Andromeda | 3 | 2.5 | ~$0.05/avaliação (LLM few-shot) |
| **Multi-agent sourcing** | Juicebox Agents 2.0 | 2.5 | 2 | ~$0.02/ciclo (busca + feedback LLM) |
| **Templates por setor** | Phenom X+ Studio | 1 | 1 | Zero extra (config only) |
| **Guided autonomy** | hireEZ EZ Agent | 2 | 1.5 | ~$0.10/busca paralela (4 estratégias) |
| **Voz para triagem** | Phenom Interview · Olivia | 2 | 2.5 | ~$1.70/entrevista (Deepgram + OpenMic) |
| **Agent Studio (infra base)** | Partes 1 + 2 deste guia | 2+2.5 | 1.5+2.5 | — |

**Sequência recomendada de implementação:**
```
Sprint 1-2:  Templates por setor (menor risco, mais impacto de produto)
Sprint 3-4:  Agent Studio infra (Partes 1+2 — habilita tudo)
Sprint 5-6:  Multi-agent sourcing (retorno imediato — aceleração de sourcing)
Sprint 7-8:  Guided autonomy (diferencial competitivo)
Sprint 9-11: Digital Twins (requer histórico de dados do cliente)
Sprint 12-13: Voz para triagem (infra 80% pronta, finalizar state machine)
```

---

### 🔬 Pesquisa de Mercado: Quem oferece "Agent Studio" em Recrutamento?

> Pesquisa realizada em 19/03/2026 com base em anúncios oficiais, press releases e sites das plataformas.

**Definição de "Agent Studio":** funcionalidade que permite ao cliente (empresa contratante) criar, configurar ou personalizar seus próprios agentes de IA sem escrever código — via interface no-code/low-code dentro da plataforma.

---

#### Tier 1 — Agent Studio Nativo (cliente cria agentes sem código)

| Plataforma | Produto | Lançamento | Modelo | Link |
|---|---|---|---|---|
| **Phenom** | **X+ Agent Studio** | Abril 2025 | No-code, zero-config, agentes por setor (manufatura, saúde, hospitality, transporte, varejo). Cliente escolhe tipo de agente, setor, e personaliza perguntas de triagem. Sem código. | phenom.com/x-plus-ai-agents |
| **Workday** | **Flowise Agent Builder** | H1 FY2026 (preview 2025) | Low-code. Workday adquiriu a Flowise em agosto 2025 e integrou como builder de agentes dentro do Workday Extend Professional. Permite criar agentes por processo sem codificar. | workday.com |
| **SAP SuccessFactors** | **Joule Studio** | Beta Q4 2025 | Low-code/no-code. Extensão do Joule (copilot SAP) para criar agentes Joule customizados via SAP Build. Global GA planejado para 2026. | sap.com |

---

#### Tier 2 — Agentes Configuráveis (cliente parametriza, não cria do zero)

| Plataforma | Produto | Lançamento | Modelo | Obs. |
|---|---|---|---|---|
| **Juicebox (PeopleGPT)** | **Juicebox Agents 2.0** | Janeiro 2026 | Cliente cria múltiplos agentes de sourcing — um por vaga, setor ou mercado. Cada agente aprende com feedback em tempo real. Dashboard centralizado de desempenho. $116M captados (Sequoia). **Foco exclusivo: sourcing.** | YC S22 · juicebox.ai/agent |
| **Eightfold AI** | **Project Andromeda (Digital Twins)** | 2025 | "Digital Twins" captura conhecimento institucional de SMEs (especialistas internos) e o transforma em agentes. O cliente configura quem é o "especialista" que o twin vai imitar. Não é studio visual, é um processo de treinamento do twin. | eightfold.ai |
| **iCIMS** | **iCIMS Agents** | Junho 2025 (AI Sourcing Agent: Outubro 2025) | Agentes pré-construídos que o cliente ativa — sem editor de agente. Filosófico de "agente que age dentro de parâmetros definidos pelo recrutador". Roadmap: cobrir todo o ciclo de aquisição. | icims.com |
| **hireEZ** | **EZ Agent** | Março 2025 | "Guided autonomy" — semi-autônomo. Recrutador define parâmetros (perfil, localização, estratégias); EZ Agent executa múltiplas estratégias em paralelo e apresenta os melhores candidatos. 800M+ profiles, 45+ fontes. | hireez.com |
| **Paradox (Olivia)** | **AI Video Studio** | 2025 | Foco em vídeo: cliente cria vídeos de job preview com IA. **Não** é agente de recrutamento configurável pelo cliente — é uma ferramenta de produção de conteúdo. (Nota: Paradox foi **adquirida pela Workday em 2025**.) | paradox.ai |

---

#### Tier 3 — Plataformas SEM Agent Studio (usam integrações de terceiros)

| Plataforma | Situação | Como clientes constroem agentes |
|---|---|---|
| **Greenhouse** | Sem agent studio nativo | Via integrações: Relevance AI, Beam.ai, Tray.ai (700+ apps), Arahi AI |
| **Ashby** | Sem agent studio | AI Notetaker, AI summaries — ferramentas de assistência, não agentes configuráveis |
| **Lever** | Sem agent studio | Integrações com plataformas terceiras |
| **SmartRecruiters** | Winston AI integrado ao Joule SAP (2026) após aquisição pela SAP em Set 2025 | Convergindo para Joule Studio do SAP |
| **Beamery** | "Ray" (copilot AI) | Agente advisor — não configurável pelo cliente |
| **SeekOut** | Talent intelligence avançado | Sem studio — interface de busca sofisticada |
| **Gem** | CRM + sourcing avançado | Sem studio — automação de sequências, não agentes |
| **Fetcher** | Hybrid AI + humano | Sem studio — curadoria humana em cima de IA |

---

#### Análise Detalhada: Juicebox (a plataforma que o usuário perguntou)

**Juicebox** (também chamada de **PeopleGPT**) é a plataforma de sourcing AI nativa mais avançada do mercado em 2026 em termos de multi-agent scaling:

```
Juicebox Agents 2.0 (lançado Janeiro 2026)
├── Multi-agent: crie N agentes, um por vaga/função/mercado
├── Real-time learning: rejeitar um candidato com feedback
│     → agente recalibra critérios imediatamente
├── Dashboard centralizado: performance de todos os agentes
├── 800M+ profiles · 30+ fontes de dados
├── 35 emails personalizados/dia por agente
└── 200+ perfis qualificados/semana por agente

Clientes: Ramp, Cognition, Quora, Perplexity
Funding: $116M (Sequoia Series B, Set 2025) · Valuation: ~$850M
Fundado: 2022 (Y Combinator S22)
```

**Diferença crítica do Juicebox vs. Phenom X+ Studio:**
- Juicebox = agentes de **sourcing** (busca + outreach) — não cobre triagem estruturada, agendamento, avaliações, onboarding
- Phenom X+ Studio = agentes para **todo o ciclo** (sourcing, triagem por voz, fraude, agendamento, entrevista por avatar, retenção)

**Por que o Juicebox é relevante para a WeDOTalent:**
- É o competidor direto do módulo de sourcing da LIA — mas foca 100% em sourcing
- A LIA cobre mais domínios (agendamento, avaliação, analytics, automação, comunicação)
- Se um cliente WeDOTalent precisar de sourcing puro em escala, o Juicebox é a alternativa especializada

---

#### Resumo: Posicionamento Competitivo para Agent Studio

```
SOFISTICAÇÃO DE AGENT STUDIO NO MERCADO (Março 2026)

Mais sofisticado
        ▲
        │
Phenom  ●  X+ Agent Studio — no-code, por setor, zero-config (LÍDER)
        │
Workday ●  Flowise Agent Builder — low-code, H1 FY2026
        │
SAP     ●  Joule Studio — low-code, beta Q4 2025
        │
Juicebox●  Multi-agent dashboard — sourcing only, jan 2026
        │
Eightfold● Digital Twins — treinamento por especialista
        │
iCIMS  ●   Agentes pré-built ativáveis, sem editor
        │
hireEZ ●   EZ Agent configurável por parâmetros
        │
LIA    ●   Tenant override de prompts (técnico, não UI)  ← POSIÇÃO ATUAL
        │
v5     ●   Sem personalização por cliente
        │
GH/Ashby● Sem studio nativo — integração terceiros
        ▼
Menos sofisticado
```

**O que a LIA precisaria para entrar no Tier 1 (Agent Studio):**

```
Fase 1 (MVP — 2 sprints):
├── UI: painel "Configurar Agente" no admin do cliente
│   └── Campos: nome do agente, tom de voz, domínios ativos, persona
├── Backend: /api/v1/agents/configure (usa prompt_loader.py existente)
└── Persistência: tenant_agent_config table

Fase 2 (Produto — 4 sprints):
├── Criador visual de fluxo (ex: quando candidato passa para triagem → agente envia email)
├── Galeria de templates pré-construídos por setor
│   └── Exemplos: "Triagem para vagas de tecnologia", "Sourcing para varejo"
├── Métricas por agente configurado (taxa de resposta, conversão)
└── A/B testing de configurações de agente

Fase 3 (Diferencial — roadmap):
├── Agente de voz (Deepgram já integrado na LIA)
├── Avatar de entrevista (como Phenom Interview Agent)
└── Agente de retenção (monitorar sinais de saída proativamente)
```

**Por que a LIA tem vantagem técnica sobre Phenom/Workday para implementar isso:**
- `prompt_loader.py` já carrega prompts com override por `tenant_id` — 80% do backend já existe
- `RecruiterBehaviorService` (Z7-01) já captura perfil do recrutador — pode ser usado para personalizar o agente
- FairnessGuard embutido — qualquer agente criado pelo cliente passa automaticamente pela fairness check (Phenom não tem isso explícito)
- LGPD compliance nativo — agentes configurados pelo cliente herdam toda a proteção de dados

---

**Pros LIA:**
- 23 agentes cobrindo 13 domínios é cobertura funcional completa para ATS enterprise
- Subagentes Z1 mostram padrão de decomposição correto (supervisor + workers)
- RecruiterBehaviorService (Z7-01) é o primeiro passo para personalização por persona
- `prompt_loader.py` com override por tenant é a base técnica para um Agent Studio

**Contras LIA:**
- Sem "Agent Studio" com UI — clientes não podem criar ou configurar agentes sem código
- Para chegar ao nível Phenom X+ Studio: 2–3 quarters de produto dedicado

**Pros v5:**
- Os 9 subagentes de sourcing são altamente coesos (single responsibility)
- O autonomous ReAct com 73+ tools é o mais flexível — resolve qualquer query não mapeada
- A separação `planner → orchestrator → workers` é o padrão supervisor+workers do LangGraph

**Contras v5:**
- Sem policy/compliance engine — sem como aplicar regras de negócio por empresa
- Sem qualquer mecanismo de personalização por cliente
- Autonomous pode ser "over-used" — se o CostLadder errar o domínio, o autonomous resolve tudo mas com menor precisão

**Recomendação para v5:**
1. Criar `src/hub/tenant_config.py` com configurações por tenant lidas do Rails
2. Adicionar `policy/` domain para regras de negócio (ex: "não enviar email sem aprovação do gerente")
3. Criar meta-agente de "agent selection confidence" que mostra ao recrutador quando o sistema não tem certeza do domínio

---

