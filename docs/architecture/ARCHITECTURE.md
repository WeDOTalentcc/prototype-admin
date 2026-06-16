# WeDOTalent / Plataforma LIA — Architecture Reference

> **Source of truth técnica.** Documento canônico que descreve a arquitetura real da plataforma a partir de leitura direta do código.
>
> **Versão:** 1.0
> **Data:** 2026-04-15
> **Mantenedor:** Time de Engenharia WeDOTalent
> **Como atualizar:** ver seção [Como manter este documento](#como-manter-este-documento) no final.

---

## Sumário

1. [Sumário Executivo](#1-sumário-executivo)
2. [Visão Geral](#2-visão-geral)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Arquitetura em Camadas](#4-arquitetura-em-camadas)
5. [Backend Architecture (`lia-agent-system`)](#5-backend-architecture-lia-agent-system)
6. [Frontend Architecture (`plataforma-lia`)](#6-frontend-architecture-plataforma-lia)
7. [Chat & Conversation Layer](#7-chat--conversation-layer)
8. [Data Layer](#8-data-layer)
9. [Cross-cutting Infrastructure](#9-cross-cutting-infrastructure)
10. [Agent System (Deep Dive)](#10-agent-system-deep-dive)
11. [Agent Studio (Custom Agents)](#11-agent-studio-custom-agents)
12. [Compliance & Security](#12-compliance--security)
13. [Deploy & DevOps](#13-deploy--devops)
14. [Roadmap & Pendências Conhecidas](#14-roadmap--pendências-conhecidas)
15. [Apêndices](#15-apêndices)

---

## 1. Sumário Executivo

**Plataforma LIA** é uma SaaS B2B multi-tenant de recrutamento e seleção com IA, da empresa **WeDOTalent**.

**Mercado-alvo:** alto volume (varejo, logística, call centers), RPO white-label, empresas que precisam escalar triagem sem aumentar equipe.

**Compliance:** LGPD, BCB 498, SOX, ISO 27001, EU AI Act.

### Escala atual (2026-04-15)

| Dimensão | Quantidade | Observação |
|---|---|---|
| Backend (`lia-agent-system`) | ~460 KLOC | FastAPI + Python 3.11 |
| Frontend (`plataforma-lia`) | ~150 KLOC | Next.js 15 + React 19 |
| Endpoints REST backend | 310 | em `app/api/v1/` |
| Modelos SQLAlchemy | 115 ativos + 5 globais | shim em `app/models/`, real em `libs/models/` |
| Domínios DDD | 62 subdiretórios | em `app/domains/` |
| ReAct agents implementados | 14 | LangGraph-based, 7 principais + 7 derivados |
| Migrations Alembic | 78 + 1 draft (079) | sequencial, sem branches |
| Componentes React | 437 únicos (~1.300 arquivos) | em `src/components/` |
| Hooks customizados | 60+ (~172 arquivos) | em `src/hooks/` |
| Páginas Next.js | 31 autenticadas + ~15 públicas | em `src/app/[locale]/` |
| Rotas backend-proxy | 507 | em `src/app/api/backend-proxy/` |
| Stores Zustand | 15 | em `src/stores/` |
| Tabelas críticas com `company_id` | 95 | RLS via PostgreSQL |
| Integrações externas | 20+ | LLMs, ATS, comm channels, auth, billing |
| Compliance subsystems | 14 | FairnessGuard, BiasAudit, HITL, AuditService, etc. |
| i18n keys | ~7.5K em pt-BR + en | next-intl |

### Filosofia Central

> **O chat é a interface principal.** O recrutador opera quase tudo via linguagem natural com a LIA. Formulários e botões são suporte, não destino.

> **Multi-tenant first.** Cada `company_id` é isolado em todos os níveis (DB row-level, LLM provider config opcional, filas Celery, cache Redis).

> **Compliance por design.** FairnessGuard pré-processa toda query em domínio HR; AuditService registra toda decisão; PII masking aplicado globalmente em logs e prompts LLM.

> **Portabilidade Vue.** Frontend React/Next está sendo escrito de forma compatível com migração futura para Vue 3 + Nuxt 3 + Pinia (hooks separados, props tipadas, callbacks `on*`, sem React-only patterns).

---

## 2. Visão Geral

### 2.1 Repositórios do ecossistema

A plataforma vive em múltiplos repositórios. Os 2 que importam para o trabalho diário são:

| Repo | Stack | Papel | Localização |
|---|---|---|---|
| **`wedotalent02202026`** | Python + FastAPI + Next.js | Monorepo principal: backend AI (`lia-agent-system/`) + frontend (`plataforma-lia/`) | GitHub WeDOTalentcc |
| **`ats-api-copia`** | Ruby on Rails 7.1 + PostgreSQL | API ATS de produção (CRUD vagas/candidatos/pipeline) | GitHub WeDOTalentcc |

> ⚠️ **NÃO USAR:** `recruiter_agent_v5`. Este repo é legacy e está PROIBIDO conforme decisão arquitetural — toda lógica de agente vive em `lia-agent-system/app/domains/`.

### 2.2 Divisão de responsabilidades (CRUD vs IA)

```
┌────────────────────────────────────────────────────────┐
│  ats-api-copia (Rails)                                 │
│  ────────────────────────────                          │
│  CRUD: vagas, candidatos, pipeline, mensagens          │
│  ATS production data                                   │
└────────────────────────────────────────────────────────┘
                       ▲
                       │ REST
                       │
┌────────────────────────────────────────────────────────┐
│  lia-agent-system (Python/FastAPI)                     │
│  ──────────────────────────────────                    │
│  IA: agentes ReAct, LLM orchestration                  │
│  WSI, sourcing, voice screening, fairness audit        │
│  310 endpoints REST, 14 agentes, 117 models            │
└────────────────────────────────────────────────────────┘
                       ▲
                       │ HTTP via /api/backend-proxy/
                       │
┌────────────────────────────────────────────────────────┐
│  plataforma-lia (Next.js)                              │
│  ───────────────────────────                           │
│  UI: 31 páginas, UnifiedChat global, dashboards        │
│  i18n pt-BR/en, dark mode, Design System v4.2.1        │
└────────────────────────────────────────────────────────┘
```

### 2.3 Fluxo de uma interação típica

Cenário: recrutador entra em `/pt/jobs/{id}`, abre o UnifiedChat lateral, digita "criar uma vaga de Python junior".

```
1. UnifiedChat (UI)
   └─ handleSend → sendChatMessage("criar uma vaga...")

2. useChatMessages.sendMessage
   └─ extrai pageContext: { job_vacancy_id, page_type: "jobs" }
   └─ adiciona user message ao state local
   └─ decide transport: WS → SSE → REST

3. WebSocket (preferencial)
   └─ POST /ws/chat/{session_id} com { type: "message", content, context, domain: "job_management" }

4. Backend chat_adapter.process_message()
   └─ build UniversalContext (user_id, company_id, message, page_context)
   └─ MainOrchestrator.process(ctx, db)

5. CascadedRouter (8 tiers)
   ├─ Tier 0 MemoryResolver (sem pronomes detectados)
   ├─ Tier 1-4 caches (miss na primeira vez)
   ├─ Tier 4 FastRouter: regex "criar.*vaga" → MATCH (job_management, conf=0.95)
   └─ skip Tier 5-8

6. JobsManagementAgent (LangGraphReActBase + EnhancedAgentMixin)
   ├─ Layer 1 (few-shot estático)
   ├─ Layer 2 (tenant calibration weights)
   ├─ Layer 3 (global insights snippet)
   ├─ ReAct loop: thinking → tool calls (create_job_wizard) → observation → response

7. WebSocket events streaming back
   ├─ thinking: "Entendi que quer criar vaga..."
   ├─ token: "Ótimo! Vou..."
   ├─ panel_update: { panel_type: "job_creation", action: "open" }
   └─ message_complete: { content: "...", conversation_id }

8. Frontend (UnifiedChat)
   ├─ Renderiza markdown da resposta
   ├─ Abre DynamicContextPanel com wizard
   ├─ Persiste message no chatMessages state
   └─ Backend salva message + conversation no PostgreSQL

9. Compliance + Audit (paralelo)
   ├─ AuditService.log_decision() registra a interação
   ├─ FairnessGuard pré-validou a query
   └─ pre/post compliance via c3b_layer.py
```

---

## 3. Stack Tecnológico

### 3.1 Backend (`lia-agent-system/`)

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.11 |
| Framework web | FastAPI | latest |
| ORM | SQLAlchemy 2.0 (async) | 2.x |
| Migrations | Alembic | 1.x |
| Driver DB | asyncpg | 0.x |
| LLM orchestration | LangGraph + LangChain | 0.x |
| LLM providers | Anthropic Claude (primário), Google Gemini, OpenAI | — |
| Background jobs | Celery 5.4 + RabbitMQ | — |
| Cache | Redis 7 | — |
| Vector DB | pgvector (extension PostgreSQL) | — |
| Auth | WorkOS (SSO + SCIM) | — |
| Observability | OpenTelemetry, Prometheus, LangSmith | — |
| Testing | pytest + pytest-asyncio | — |

### 3.2 Frontend (`plataforma-lia/`)

| Camada | Tecnologia | Versão |
|---|---|---|
| Framework | Next.js (App Router) | 15.5.15 |
| UI library | React | 19.0.0 |
| Linguagem | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.x → 4.1 (em migração) |
| Component library | shadcn/ui (Radix UI) | latest |
| Forms | react-hook-form + Zod | 7.x / 4.x |
| State management | Zustand | 5.0 |
| i18n | next-intl | 4.9.1 |
| Charts | Recharts + Chart.js | — |
| Toast | Sonner | 2.x |
| Drag & Drop | @dnd-kit | 6.x |
| Markdown | marked + DOMPurify | — |
| Date | date-fns | 4.x |
| Auth | jose (JWT) + WorkOS sessions | 6.x |
| Testing | Vitest + Testing Library + Playwright | — |
| Code quality | Biome | 1.9.4 |

### 3.3 Frontend futuro (preparação para migração)

| Camada | Tecnologia futura |
|---|---|
| Framework | Vue 3 + Vuetify 3 + Nuxt 3 |
| State | Pinia |
| Testing | Vitest (mantém) |

> Todo código novo no frontend deve seguir padrões compatíveis com Vue: hooks separados de componentes, props tipadas via interface, callbacks `onEvent`, sem React-only patterns (`cloneElement`, `forwardRef`, HOCs excessivos).

### 3.4 Infraestrutura

| Componente | Provedor |
|---|---|
| Backend hosting | Docker Compose (dev/staging) — produção via plataforma de orquestração |
| Frontend hosting | Netlify |
| Database | Neon (managed PostgreSQL) |
| Redis | managed (provider varia) |
| RabbitMQ | managed |
| File storage | local disk (dev) → S3-like (produção) |

---

## 4. Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────────────┐
│                    USER (Recrutador)                          │
│           Browser · Microsoft Teams · WhatsApp                │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND: plataforma-lia (Next.js 15)                       │
│  ─────────────────────────────                               │
│  • 31 páginas autenticadas + ~15 públicas                    │
│  • UnifiedChat global montado em [locale]/layout.tsx         │
│  • 437 componentes, 60+ hooks, 15 stores Zustand             │
│  • i18n pt-BR + en (next-intl)                               │
│  • Design System v4.2.1 (Open Sans + Inter, dark mode)       │
└──────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴────────────┐
                │                          │
                ▼                          ▼
┌────────────────────────┐    ┌────────────────────────────────┐
│ Frontend Proxy Layer   │    │ WebSocket Direto               │
│ ─────────────────────  │    │ ─────────────────              │
│ /api/backend-proxy/X   │    │ /ws/chat/{session_id}          │
│ → ${BACKEND}/api/v1/X  │    │ Auth via JWT query string      │
│ Auth header forwarding │    │ Streaming bidirecional         │
│ 507 rotas              │    │ Real-time events               │
└────────────────────────┘    └────────────────────────────────┘
                │                          │
                └──────────────┬───────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  BACKEND: lia-agent-system (FastAPI)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Layer (310 endpoints REST + WS + SSE)            │   │
│  │ app/api/v1/                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Orchestrator Layer                                   │   │
│  │ ChatAdapter → MainOrchestrator                       │   │
│  │ CascadedRouter (8 tiers: memory, cache, LLM, etc.)   │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Agent Layer (LangGraph ReAct)                        │   │
│  │ 14 agentes em app/domains/<domain>/agents/           │   │
│  │ + Custom agents do Agent Studio                      │   │
│  │ Base classes: LangGraphReActBase + EnhancedAgentMixin│   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tools Layer                                          │   │
│  │ Per-domain: get_<domain>_tools()                     │   │
│  │ Global: app/tools/ + tool_permissions.yaml           │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Shared Services Layer                                │   │
│  │ FairnessGuard, AuditService, HITLService,            │   │
│  │ CircuitBreaker, RAGPipeline, EventStore, etc.        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Persistence Layer                                    │   │
│  │ Models (SQLAlchemy 2.0 async) — 115 tabelas          │   │
│  │ Repositories — 250+ classes                          │   │
│  │ PostgreSQL (Neon) + pgvector                         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Background Jobs (Celery 5.4)                                │
│  app/jobs/tasks/ — 10 modules                                │
│  • compliance.py: LGPD cleanup, audit lifecycle              │
│  • communication.py: email, WhatsApp, Teams                  │
│  • company_documents.py: PDF/DOCX → FairnessGuard → extract  │
│  • feedback.py, ml.py, voice.py, memory.py, agents.py        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  External Integrations (20+)                                 │
│  ─────────────────────────                                   │
│  LLMs:   Anthropic Claude · Google Gemini · OpenAI           │
│  AI/ML:  Pearch AI · Deepgram · OpenMic.ai · Apify · LangSmith│
│  Comm:   MS Teams · MS Graph · WhatsApp (Meta+Twilio)        │
│  Email:  SendGrid · Resend · Mailgun                         │
│  ATS:    Gupy · Pandapé · Merge.dev                          │
│  Auth:   WorkOS (SSO+SCIM)                                   │
│  CRM:    HubSpot                                             │
│  Bill:   Stripe                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Backend Architecture (`lia-agent-system`)

### 5.1 Estrutura de diretórios

```
lia-agent-system/
├── app/                              ← FastAPI application
│   ├── main.py                       ← FastAPI app, lifespan, middleware stack
│   ├── api/
│   │   ├── routes.py                 ← Central router registry (310 endpoints)
│   │   ├── orchestrator_routes.py
│   │   └── v1/                       ← 310 endpoint files
│   │       ├── chat.py               ← REST chat principal (~1100 linhas)
│   │       ├── agent_chat_ws.py      ← WebSocket chat (~900 linhas)
│   │       ├── agent_chat_sse.py     ← Server-Sent Events fallback
│   │       ├── conversations.py
│   │       ├── candidates/, jobs/, sourcing/, pipeline/, etc.
│   │       └── (300+ outros)
│   ├── auth/                         ← User model, dependencies
│   ├── core/                         ← Config, DB, logging, startup
│   ├── domains/                      ← DDD: 62 subdirs
│   │   ├── ai/                       ← LLM service, RAG pipeline
│   │   ├── agent_studio/             ← Custom agents (CustomAgentRuntime)
│   │   ├── candidates/, chat/, communication/, company/
│   │   ├── company_settings/         ← S02: profile, culture, benefits, workforce
│   │   ├── compliance/, cv_screening/, hiring_policy/
│   │   ├── job_management/
│   │   ├── kanban_search, kanban_insight, kanban_action/
│   │   ├── pipeline_context, pipeline_decision, pipeline_action/
│   │   ├── recruiter_assistant/      ← fallback agent
│   │   ├── sourcing, sourcing_planner, sourcing_search, sourcing_enrich, sourcing_engagement/
│   │   ├── talent_pool/, digital_twin/, recruitment_campaign/
│   │   └── (40+ outros)
│   ├── orchestrator/                 ← Agent routing + execution
│   │   ├── chat_adapter.py
│   │   ├── cascaded_router.py        ← 8 tiers
│   │   ├── domain_mappings.py        ← agent_type → domain_id
│   │   └── config/domain_routing.yaml
│   ├── shared/                       ← Cross-cutting infrastructure
│   │   ├── compliance/               ← FairnessGuard, c3b_layer, audit_service
│   │   ├── fairness/                 ← fairness_guard.py (3 layers)
│   │   ├── resilience/               ← circuit_breaker, dlq_service
│   │   ├── tracing.py                ← OpenTelemetry
│   │   ├── pii_masking.py
│   │   ├── encryption/               ← Fernet field encryption
│   │   ├── tenant_llm_context.py     ← multi-tenant context var
│   │   └── tool_handler.py
│   ├── tools/                        ← Tool registry global + tool_permissions.yaml
│   ├── prompts/domains/              ← <domain>.yaml prompts
│   ├── schemas/                      ← Pydantic models (55 arquivos)
│   ├── models/                       ← Shims → libs/models/lia_models/
│   ├── jobs/tasks/                   ← Celery tasks (10 modules)
│   └── middleware/auth_enforcement.py
├── libs/                             ← Shared libraries (importable)
│   ├── agents-core/lia_agents_core/  ← LangGraphReActBase, EnhancedAgentMixin, AgentInterface
│   ├── config/lia_config/            ← Pydantic settings, database, celery_app
│   ├── audit/lia_audit/              ← audit_storage.py
│   └── models/lia_models/            ← Modelos SQLAlchemy reais (120 arquivos)
├── alembic/versions/                 ← 78 migrations + 1 draft (079)
├── tests/
└── pyproject.toml + requirements.txt
```

### 5.2 Padrões arquiteturais

- **DDD (Domain-Driven Design):** cada domínio em `app/domains/<domain>/` com estrutura padrão `agents/`, `tools/`, `services/`, `repositories/`, `actions/`, `config/`.
- **Layered:** API → Orchestrator → Agent → Tools → Shared Services → Persistence.
- **Hexagonal (parcial):** repositories abstraem persistência; LLM provider factory abstrai providers externos.
- **Multi-tenant via context var:** `tenant_llm_context.get_current_llm_tenant()` retorna `company_id` setado por middleware.
- **Async-first:** SQLAlchemy 2.0 async, FastAPI async, Celery para work em background.

### 5.3 Inventário de domínios (62 subdiretórios)

Os principais com agente ReAct:

| Domínio | Agente principal | Status |
|---|---|---|
| `agent_studio` | CustomAgentRuntime (dinâmico) | Real |
| `ai` | LLMService + RAGPipeline | Real |
| `analytics` | AnalyticsAgent | Real |
| `candidates` | (CRUD + tools, sem agent dedicado) | Real |
| `communication` | CommunicationAgent | Real |
| `company_settings` | CompanySettingsReActAgent | Real (P36 + 12 tools) |
| `cv_screening` | CVScreeningAgent + WSI | Real |
| `digital_twin` | DigitalTwinAgent | Real |
| `hiring_policy` | PolicyReActAgent | Real |
| `job_management` | JobsManagementAgent (Wizard) | Real |
| `kanban_*` (3 sub-domínios) | KanbanReActAgent | Real |
| `pipeline_*` (3 sub-domínios) | PipelineReActAgent | Real |
| `recruiter_assistant` | RecruiterAssistantAgent (fallback) | Real |
| `recruitment_campaign` | CampaignAgent | Real |
| `sourcing` + 4 sub-domínios | SourcingAgent (split em 4 etapas) | Real |
| `talent_pool` | TalentPoolAgent | Real |
| `voice_screening` (em talent_pool) | VoiceScreeningAgent | Real |

### 5.4 API Layer (310 endpoints)

`app/api/routes.py` registra todos. Categorias principais:

| Categoria | Quantidade aprox |
|---|---|
| Chat & Conversation | ~30 endpoints (6 routers) |
| Candidates | ~50 endpoints |
| Jobs | ~40 endpoints |
| Sourcing | ~30 endpoints |
| Pipeline / Kanban | ~25 endpoints |
| Screening | ~20 endpoints |
| Communication | ~25 endpoints |
| Compliance | ~20 endpoints |
| Company | ~30 endpoints |
| Agent Studio | ~30 endpoints |
| Admin | ~20 endpoints |
| Auth | ~15 endpoints |
| Outros | ~20 endpoints |

---

## 6. Frontend Architecture (`plataforma-lia`)

### 6.1 Estrutura de diretórios

```
plataforma-lia/
├── src/
│   ├── app/
│   │   ├── [locale]/                     ← i18n routing (pt-BR, en)
│   │   │   ├── layout.tsx                ← Providers globais (LiaFloatProvider, etc.)
│   │   │   ├── page.tsx                  ← Dashboard inicial
│   │   │   └── (31 páginas autenticadas)
│   │   ├── api/
│   │   │   ├── auth/                     ← WorkOS, session, magic-link
│   │   │   ├── backend-proxy/            ← 507 rotas proxy → backend FastAPI
│   │   │   └── portal/                   ← LGPD data-request públicos
│   │   └── layout.tsx                    ← Root layout
│   ├── components/                       ← 1.300+ arquivos, 437 componentes únicos
│   │   ├── ui/                           ← 71 primitivos shadcn
│   │   ├── unified-chat/                 ← 28 componentes do chat principal
│   │   ├── settings/                     ← 81 componentes (hubs)
│   │   ├── pages-agent-studio/           ← 10 componentes (custom agent builder)
│   │   ├── pages-jobs, pages-candidates, pages-talent-pools/
│   │   ├── lia-float/, lia-screening/
│   │   ├── modals/, search/, tables/
│   │   ├── workflow-rail/, kanban/, charts/
│   │   ├── chat/ (LEGACY), expanded-chat/ (LEGACY)
│   ├── hooks/                            ← 60+ hooks (~172 arquivos)
│   │   ├── chat/                         ← useChatMessages, useChatSocket, etc.
│   │   ├── ai/                           ← use-agent-streaming
│   │   ├── candidates/, recruitment/, agents/, settings/, search/, jobs/
│   │   └── shared/, ui/, company/, prompt/
│   ├── contexts/                         ← 3 providers globais
│   │   ├── auth-context.tsx
│   │   ├── lia-float-context.tsx         ← UnifiedChat state global
│   │   └── teams-sso-context.tsx
│   ├── stores/                           ← 15 stores Zustand
│   ├── services/lia-api/                 ← 14 arquivos (API client)
│   ├── lib/                              ← Utilities (permissions, design-tokens, etc.)
│   ├── types/                            ← TypeScript shared types
│   ├── i18n/, messages/                  ← next-intl config + pt-BR.json + en.json
│   ├── utils/permissions.ts              ← RBAC
│   └── middleware.ts                     ← Edge: auth, locale, CORS
├── public/, messages/
└── package.json + tsconfig.json + tailwind.config.ts
```

### 6.2 Layout global

`src/app/[locale]/layout.tsx`:

```tsx
<NextIntlClientProvider>
  <JWTAuthProvider>             // sessão
    <ThemeProvider>             // dark mode
      <LiaFloatProvider>        // estado global do chat
        <ErrorBoundary>
          <UnifiedChatConditional />     // chat lateral montado UMA vez
          <WorkflowRailWrapper />
          <WeeklyDigestChatProvider />
          <SonnerToaster />
          {children}
        </ErrorBoundary>
      </LiaFloatProvider>
    </ThemeProvider>
  </JWTAuthProvider>
</NextIntlClientProvider>
```

### 6.3 RBAC (5 níveis)

`src/utils/permissions.ts`:

| Role | Capacidades principais |
|---|---|
| Admin | Tudo: usuários, billing, audit logs, settings |
| Manager | Team próprio, pipeline, hiring, reports |
| Senior Recruiter | Candidatos, jobs, entrevistas, calibration |
| Recruiter | Candidatos, screening, pipeline |
| Intern | Read-only candidatos, triagem |

`canAccessPage(role, page)` valida no middleware. `usePermissions()` no client.

### 6.4 Design System v4.2.1

- 90% monocromático (grays) + 10% accent WeDo
- Botões primários: `bg-gray-900`. Cyan (`#60BED1`) **apenas para LIA**
- Tipografia: Open Sans 85% + Inter 10% + JetBrains Mono 5%
- Border radius: `rounded-md` (8px) universal
- Fonte base: 11px (text-xs redefinido)
- **Dark mode obrigatório** em todos os componentes
- Tokens em `tailwind.config.ts` + `src/lib/design-tokens.ts` + `src/styles/design-tokens.css`. **NUNCA hex hardcoded**

### 6.5 Padrões de portabilidade Vue

| Aspecto | Compatibilidade |
|---|---|
| Componentes com `function Component({ props, onEvent })` | ✓ 95% |
| Props via interface | ✓ Compatível |
| Callbacks `on*` | ✓ Mappable pra `@event` |
| `useContext()` (~85 instâncias) | ⚠️ Migrar pra Pinia stores |
| `forwardRef` (~85 ocorrências) | ⚠️ Refatorar |
| Zustand → Pinia | ✓ 1:1 direct mapping |

---

### 6.6 Roteamento context-aware (T-1165)

`useNavigationIntent` (`plataforma-lia/src/hooks/shared/use-navigation-intent.ts`) é o único caller que decide se `lia:navigation-hint` deve ser disparado, via helper puro `resolveNavigationIntentMode(raw, pathname)`:

- (a) já em `/chat` + alvo em `CHAT_FIRST_TARGET_PAGES` (atualmente só `"Vagas"`) → `page=null` (supressão, fluxo segue no chat);
- (b) outra rota → `mode="ask"`.

`UnifiedChat.tsx` forwarda `result.mode` no `detail` do CustomEvent; `DashboardApp` ramifica em `detail.mode === "ask"`, posta uma mensagem da LIA no chat propondo a transição, e classifica a resposta livre PT-BR do recrutador via `classifyNavConfirmation` (positivos "sim/vamos/pode/bora/claro/ok/manda/fechou/...", negativos "não/agora não/depois/deixa pra lá/cancela/...", com negativos tendo precedência sobre tokens positivos como "pode" em "pode esperar"). Só `yes` dispara `router.push`; `no` posta ack ("Combinado — seguimos por aqui."); ambíguo deixa a proposta pendente até a próxima mensagem.

`useWizardFlow` emite o mesmo hint `{page:"Vagas", mode:"ask", hint:"wizard:<stage>"}` quando `currentStage` transita para uma `SPLIT_STAGE` (review/publish/calibration/handoff/done/scheduling); transições dentro do mesmo stage não re-emitem (guard via `useRef`). Callers legacy (`useProactiveActionRouter`, `TourController`, `DonePanel`, `BibliotecaLiaRouteClient`, `NavigationHintCard`) que não setam `mode` continuam no caminho `navigate` direto.

**Sentinelas:** `src/hooks/__tests__/use-navigation-intent.context.test.ts` (5 cenários do helper puro) + `src/components/__tests__/classify-nav-confirmation.test.ts` (positivos/negativos/ambíguos exaustivo) + E2E `e2e/tests/wizard/20-roteamento-split-view-coerente.spec.ts` (3 cenários: A=intent em /chat não empurra; B=ask + "pode ir" → push; B'=ask + "agora não" → ack).

---

## 7. Chat & Conversation Layer

### 7.1 Visão geral

Toda interação com a LIA passa pelo **UnifiedChat**: um único componente React montado globalmente em `src/app/[locale]/layout.tsx:151` via `<UnifiedChatConditional />`.

**3 modos visuais** (state em `localStorage.lia-chat-mode`):
- **sidebar** (default) — lateral direito, resizable 300-600px
- **floating** — janela flutuante 360x520px no canto inferior
- **fullscreen** — tela inteira (modo `/chat`)

### 7.2 Estado global — `lia-float-context.tsx`

**`ChatContextType` enum:**
```typescript
type ChatContextType =
  | "general" | "job_chat" | "talent_chat" | "kanban_chat" | "candidates_chat"
  | "agent_studio"      // adicionado em PR2 (2026-04-15)
  | "settings_config"   // adicionado em PR2/S02
```

`useLiaFloat()` provê UI state (isOpen, dynamicPanel, etc.)
`useLiaChatContext()` provê chat state (messages, switchChatContext, sendMessage, HITL, clarification, streaming)

### 7.3 Transport Layer

**Hierarquia:** WebSocket primário → SSE fallback → REST fallback

| Hook | Responsabilidade |
|---|---|
| `useLiaChatConnection` | Facade |
| `useChatSocket` | WebSocket auth + event handling |
| `useChatMessages` | REST + SSE fallback, conversation lifecycle |
| `useChatTransport` | Abstração (`ws | sse | disconnected`) |
| `useAgentStreaming` | Stream parsing |

### 7.4 Backend Chat Endpoints

**REST (`app/api/v1/chat.py`):**
- `POST /chat` — principal
- `POST /chat/with-attachments` — multipart com arquivo (10MB max)
- `POST /chat/stream` — SSE
- `GET /chat/conversations`, `GET /chat/{id}/messages`
- `POST /chat/context` — notificar mudança de contexto (S02)

**WebSocket (`agent_chat_ws.py`):** `GET /ws/chat/{session_id}?token=<jwt>`

Eventos: thinking, token, message_complete, panel_update, background_task_update, hitl_pending, fairness_warning, clarification, error.

### 7.5 Cascaded Router (8 tiers)

| Tier | Nome | Função |
|---|---|---|
| 0 | MemoryResolver | Resolve pronomes/referências |
| 1 | LRU in-process | Hash MD5 local O(1) |
| 2 | Redis hash cache | Distribuído exact match |
| 3 | VectorSemanticCache | pgvector cosine ≥ 0.85 |
| 4 | FastRouter | Regex em `domain_routing.yaml` |
| 5 | LLM Cascade | Haiku → Sonnet → Opus |
| 6 | AutonomousReActAgent | Cross-domain fallback |
| 7 | Custom Studio Agents | CustomAgentRuntime |
| 8 | Fallback Clarification | `needs_clarification=true` + opções |

### 7.6 Mensagens especiais

| Tipo | Trigger | UI Component |
|---|---|---|
| HITL approval | `hitl_pending` event | `HITLConfirmCard` inline |
| Clarification chips | `clarification` event (Tier 8) | Chips clicáveis em `UnifiedMessageList` |
| Dynamic Panel | `panel_update` event | `DynamicContextPanel` split view |
| Background Task | `background_task_update` | Toast com progress bar |
| Plan Progress | `plan_progress` | `PlanProgressCard` |
| Thinking | `thinking` event | `TypingIndicator` |
| Streaming Tokens | `token` events | Concatenado em `streamingContent` |
| Fairness Warning | `fairness_warning` | Banner dismissable |

### 7.7 Mudanças recentes (Sessão 2026-04-15)

3 PRs commitados:

- **PR1 `9ec36564`** — Hotfix crash do `ConversationalCreator`
- **PR2 `610cac74`** — `agent_studio` + `settings_config` propagados na stack; `needs_clarification` renderizado
- **PR3 `aa903f56`** — Validação de LLM key no startup, badge "Chave do sistema", docstring fallback chain

---

## 8. Data Layer

### 8.1 Estrutura

- 115 modelos SQLAlchemy 2.0 async + 5 globais
- Shim: `app/models/X.py` → `from lia_models.X import *`
- Engine: PostgreSQL 16 + asyncpg
- Multi-tenant: RLS via `SET ROLE lia_app` + `set_config('app.company_id', ...)`
- Vector: pgvector, dim=768 (Google Gemini embeddings)
- Migrations: Alembic, 78 + 1 draft (079)

### 8.2 Modelos por categoria (115 total)

| Categoria | Quantidade | Exemplos |
|---|---|---|
| Tenant / Empresa | 9 | CompanyProfile, Department, Benefit, CompanyCulture |
| Conversation / Chat | 5 | Conversation, Message, ConversationSummary |
| Jobs / Vagas | 6 | JobVacancy, JobDraft, JobTemplate |
| Candidates | 7 | Candidate, CandidateAttachment, etc. |
| Pipeline | 3 | PipelineTemplate, PipelineStage |
| Sourcing / Talent Pool | 3 | TalentPool, SourcingAgent |
| Custom Agents (Agent Studio) | 11 | CustomAgent, AgentVersion, AgentDeployment |
| Compliance / Audit | 8 | AuditLog, BiasAuditSnapshot, FairnessAudit |
| LLM / AI | 5 | TenantLLMConfig, AIConsumption, ModelDriftAlert |
| Vector / Embeddings | 6 | DigitalTwin, KnowledgeBase |
| Communication | 8 | EmailTemplate, AlertConfig |
| Auth / Users | 5 | ClientUser, ClientAccount |
| Event Store | 2 | DomainEvent (append-only) |
| Screening / CV | 6 | Screening, VoiceScreening |
| Automation / Tasks | 7 | Automation, Task |
| Insights / Analytics | 7 | IntelligenceLayer, SuccessProfile |
| Learning & Feedback | 6 | Feedback, RoutingFeedback |
| Arquivos & Metadata | 4 | CompanyDocuments |
| Preferences & Config | 7 | GlobalPolicy, GlobalSearchSettings |
| Outros | 13 | Billing, DigitalTwin, ATSIntegration |

### 8.3 Multi-tenancy

- **95 modelos** têm `company_id` (indexed)
- **5 globais** sem `company_id`: ClientUser, ClientAccount, User (WorkOS), AdminSettings, HealthCheck
- RLS automático: queries filtram por `app.company_id` configurado via contextvar

### 8.4 Migrations Alembic — marcos

| Rev | Descrição |
|---|---|
| 001 | add_intelligence_and_personalization (schema inicial) |
| 015 | add_fairness_audit_log (BiasAuditSnapshot + FairnessAudit) |
| 025 | add_screening_workflow |
| 058 | tenant_llm_configs (encrypted Fernet) |
| 070 | agent_deployments |
| 078 | few_shot_candidates |
| **079** | **company_workforce_and_documents (S02 — draft, 2026-04-15)** |

### 8.5 Cache & Memory

- **Redis:** cascaded router cache, conversation cache, embedding cache (TTL 24h), DLQ storage
- **WorkingMemoryService** (per-conversation): Redis + PostgreSQL
- **EmbeddingCache** (pgvector): warmed at startup

### 8.6 Event Sourcing

`DomainEvent` table (append-only):

- `aggregate_type`, `aggregate_id`, `event_type`, `event_data` (JSONB), `company_id`, `sequence_number`
- Eventos: CandidateCreated, CandidateMoved, JobCreated, JobPublished, ScreeningCompleted, InterviewScheduled, ApprovalGranted

### 8.7 PII / Encryption

- **Field-level Fernet** em email/phone/CPF via `EncryptedFieldMixin`
- `email_hash` SHA-256 indexed (search sem revelar plaintext)
- **PII masking** global em logs via `install_global_pii_masking()` + em prompts LLM via `strip_pii_for_llm_prompt()`
- Env: `FIELD_ENCRYPTION_KEY`

---

## 9. Cross-cutting Infrastructure

### 9.1 Auth & Authorization

**WorkOS SSO + SCIM:**
- `app/api/v1/workos.py` — main + scim_router + auth_router + webhook_router
- Provisioning automático via SCIM events
- Env: `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_WEBHOOK_SECRET`

**Internal:**
- `app/auth/dependencies.py` — `get_current_user`, `get_current_user_or_demo`, `require_admin`
- `app/middleware/auth_enforcement.py` — JWT validation + PUBLIC_PREFIXES allowlist

### 9.2 Compliance Stack — 14 sistemas (todos REAIS)

| Sistema | Arquivo | Endpoint |
|---|---|---|
| LGPD / DSR | `app/api/v1/lgpd_compliance.py` | `/api/v1/lgpd-compliance/data-requests` |
| Granular Consent | `consent_gate.py` | `/api/v1/consent/granular/{id}` |
| **FairnessGuard 3 layers** | `fairness_guard.py` | Layer 3 opt-in via `FAIRNESS_LAYER3_ENABLED` |
| BiasAudit (Four-Fifths) | `bias_audit_service.py` | `/api/v1/bias-audit/job/{id}/results` |
| BiasAuditSnapshot | `bias_audit_snapshot.py` | `/api/v1/bias-audit/job/{id}/history` |
| Model Drift Detection | `model_drift_detection.py` | Celery `compliance.check_drift_batch` |
| HITL | `hitl_service.py` | `/api/v1/hitl/{thread_id}/approve` |
| **AuditService** | `audit_service.py` | `log_decision()` (todos os 14 agentes) |
| Circuit Breakers | `circuit_breaker.py` | per-provider |
| PolicyEngine | `policy_agent.py` | `/api/v1/policy-engine/evaluate` |
| RAG Híbrido | `rag_pipeline_service.py` | `/api/v1/candidates/rag-search` |
| Event Store | `audit_storage.py` | persistência DB |
| **PII Masking** | `pii_masking.py` | global |
| SOC 2 / ISO 27001 | `compliance_controls_repository.py` | Trust Center |

### 9.3 LLM Compliance Layer (Etapa 1)

**`app/shared/compliance/c3b_layer.py`:**
- `pre_compliance()` — PII stripping + FairnessGuard L3 (domain-aware)
- `post_compliance()` — AuditService.log_decision + FactChecker (placeholder)
- Flag `LIA_DISABLE_C3B=1` desativa (só dev)

### 9.4 Observability

**Tracing:** OpenTelemetry preferencial + LightweightTracer fallback. LangSmith via `LANGCHAIN_API_KEY`.

**Metrics:** Prometheus em `/api/v1/metrics`. Token tracking per company/user.

**Logging:** JSON em prod, human-readable em dev. PII masking global.

### 9.5 Resilience

**Circuit Breakers:** CLOSED → OPEN (5 failures) → HALF_OPEN (30s) → CLOSED
- Providers: ANTHROPIC, OPENAI, GEMINI, WORKOS, PEARCH, STRIPE

**DLQ:** Redis LIST per fila, TTL 7 dias, cap 1000. PII masking antes de persistir.

**Fallback LLM:** Anthropic → Gemini → OpenAI (com circuit breaker per-provider).

### 9.6 Background Tasks (Celery 5.4)

`app/jobs/tasks/`:
- `agents.py`, `agents_legacy.py`, `communication.py`, `compliance.py`
- `company_documents.py` (S02)
- `feedback.py`, `followup.py`, `memory.py`, `ml.py`, `voice.py`

**Beat schedule:** LGPD cleanup (daily), audit lifecycle (monthly), drift (daily), summarization (hourly), retraining (weekly).

### 9.7 Integrações Externas (20+)

| Categoria | Integração | Env Var |
|---|---|---|
| **LLM** | Anthropic Claude Sonnet 4.5 | `AI_INTEGRATIONS_ANTHROPIC_API_KEY` ou `ANTHROPIC_API_KEY` |
| | Google Gemini | `AI_INTEGRATIONS_GEMINI_API_KEY` |
| | OpenAI GPT | `AI_INTEGRATIONS_OPENAI_API_KEY` ou `OPENAI_API_KEY` |
| **AI/ML** | Pearch AI | `PEARCH_API_KEY` |
| | Deepgram (STT) | `DEEPGRAM_API_KEY` |
| | OpenMic.ai | `OPENMIC_WEBHOOK_SECRET` |
| | Apify | `APIFY_API_KEY` |
| | LangSmith | `LANGCHAIN_API_KEY` |
| **Comm** | MS Teams Bot | `MICROSOFT_APP_ID/PASSWORD/TENANT_ID` |
| | MS Graph (Outlook) | `AZURE_CLIENT_ID/SECRET/TENANT_ID` |
| | WhatsApp Meta | `WHATSAPP_VERIFY_TOKEN`, etc. |
| | WhatsApp Twilio | `TWILIO_ACCOUNT_SID`, etc. |
| **Email** | SendGrid | `SENDGRID_API_KEY` |
| | Resend | `RESEND_API_KEY` |
| | Mailgun | `MAILGUN_API_KEY` |
| **ATS** | Gupy / Pandapé / Merge.dev | API keys respectivas (ver §9.8) |
| **ATS (interno)** | Rails ATS — `ats-api-copia` | `RAILS_API_TOKEN` (sync FastAPI ↔ Rails) |
| **Auth/SaaS** | WorkOS | `WORKOS_API_KEY/CLIENT_ID/WEBHOOK_SECRET` |
| | HubSpot (CRM) | `HUBSPOT_API_KEY` |
| | Stripe (billing) | `STRIPE_SECRET_KEY/WEBHOOK_SECRET` |

---

### 9.8 ATS Integration Boundary

A camada de integração ATS é a fronteira entre `lia-agent-system` (FastAPI) e
sistemas externos de ATS — tanto o ATS Rails interno (`ats-api-copia`) quanto
provedores externos (Gupy, Pandapé, Merge.dev). Toda comunicação cross-system
passa por este contorno; nenhum agente, controller ou job acessa um ATS
diretamente.

**Camadas:**

```
External ATS (Gupy/Pandapé/Merge)        Rails ATS (ats-api-copia)
        ▲                                          ▲
        │ HTTPS                                    │ HTTPS (Bearer token)
        ▼                                          ▼
┌──────────────────────────────┐    ┌─────────────────────────────────┐
│ ats_clients/ (provider SDKs) │    │ /api/v1/rails-sync/* (FastAPI)  │
│  base.py, gupy.py,           │    │  GET candidates/{id}/enrichment │
│  pandape.py, merge.py        │    │  GET jobs/{id}/intelligence     │
│  wedotalent_rails.py         │    │  GET compliance/status          │
│                              │    │  POST bulk-sync/candidates      │
│ ATSProviderFactory cache     │    │                                 │
└──────────────────────────────┘    └─────────────────────────────────┘
        ▲                                          ▲
        │                                          │
┌────────────────────────────────────────────────────────────────────┐
│ libs/schemas/ats/         ← Pydantic wire contracts (response_model)│
│ rails_sync.py             ← envelopes + provenance (source/synced_at)│
└────────────────────────────────────────────────────────────────────┘
        ▲                                          ▲
        │                                          │
┌────────────────────────────────────────────────────────────────────┐
│ app/domains/ats_integration/ (DDD domain)                          │
│  • agents/   — ATSIntegrationReActAgent (4-file pattern)           │
│  • services/ — ATSSyncService, gupy/pandape/merge services         │
│  • repositories/                                                   │
│      ats_repository.py        — domain models (5 ATS tables)       │
│      rails_sync_repository.py — read-only facade for rails-sync    │
│  • tools/    — ats_tools (tool registry for the agent)             │
└────────────────────────────────────────────────────────────────────┘
```

**Contracts:**

- **Wire contracts:** `libs/schemas/ats/` holds the Pydantic envelopes for every
  rails-sync endpoint. Every response carries `source: "fastapi"` and an
  ISO-8601 `synced_at` so the Rails consumer can audit provenance. Schemas live
  in `libs/` (not `app/schemas/`) because they are part of the cross-service
  public surface.
- **Provider clients:** `app/domains/ats_integration/services/ats_clients/`
  defines the abstract `ATSClient` (Template Method) plus concrete clients per
  provider. New providers register in `ATSProviderFactory.PROVIDER_CLASSES` and
  read credentials from `ATS_<PROVIDER>_*` env vars.
- **Persistence:** the 5 canonical ATS tables (`ats_connections`,
  `ats_sync_jobs`, `ats_candidates`, `ats_webhook_logs`, `ats_job_mappings`)
  live in `lia_models.ats_integration` and are accessed only via
  `ATSRepository`. Cross-domain reads needed by `rails-sync` (Candidate,
  JobVacancy, EmailTemplate) flow through `RailsSyncRepository`.
- **Architectural enforcement:** rails-sync compliance with ADR-001 (no SQL in
  controllers) and ADR-005 (every endpoint declares `response_model`) is locked
  in `tests/contract/test_rails_sync_contracts.py`. The inverse direction
  (FastAPI → Rails ATS via `WeDOTalentATSClient`) is locked in
  `tests/contract/test_wedotalent_rails_client_contract.py`, which uses
  `respx` to stub the Rails endpoints and assert auth header, JSONAPI
  envelope unwrapping, 4xx non-retry, 5xx retry-with-backoff, and bounded
  retries.

**Notas sobre o ATS Rails (`ats-api-copia`):**

- Stack: Rails 7.1 + PostgreSQL com Apartment gem (multi-tenancy por schema —
  `Account` e `User` excluídos do isolamento, todas as outras tabelas vivem no
  schema do tenant).
- Auth: JWT custom assinado com `Rails.application.secret_key_base` (24 h de
  expiração). WorkOS / futuras sessões ATS-issued podem entrar no mesmo slot
  `Authorization: Bearer …` consumido por FastAPI (ver ADR-013).
- Real-time: ActionCable (`/cable`) para mensagens recrutador ↔ candidato. O
  FastAPI **não** consome esse canal — apenas a superfície REST acima.
- Inconsistências conhecidas (snapshot 2026-03-24, ainda não endereçadas):
  Pundit no Gemfile mas `app/policies/` vazio; CORS de produção apenas com
  `localhost:3000` no repo.

---

## 10. Agent System (Deep Dive)

### 10.1 Hierarquia de classes

```
BaseAgent (abstract, libs/agents-core)
  ↓
LangGraphReActBase (langgraph_react_base.py)
  - PostgresSaver para persistência
  - LangChain ChatModel injection (_get_model)
  - ReAct loop via LangGraph create_react_agent
  ↓
EnhancedAgentMixin (enhanced_agent_mixin.py)
  - 3 layers de inteligência (P36):
    Layer 1: Few-shot estático (de YAML)
    Layer 2: Tenant calibration weights
    Layer 3: Global insights snippet
  - Quality floor (12.6)
  - Auto-evolving pipeline (12.7)
  ↓
DomainSpecificReActAgent (e.g. CompanySettingsReActAgent)
  - _get_tools() retornando ToolDefinition[]
  - DOMAIN_INSTRUCTIONS (concat de prompt parts)
  - Confidence scoring específico do domínio
  - process() → AgentOutput { message, actions, confidence, metadata }
```

### 10.2 Padrão de 4 arquivos por agente

```
app/domains/<domain>/agents/
├── <domain>_react_agent.py     ← Classe principal (LangGraphReActBase + EnhancedAgentMixin)
├── <domain>_tool_registry.py   ← get_<domain>_tools() → ToolDefinition[]
├── <domain>_system_prompt.py   ← Carrega de YAML
└── <domain>_stage_context.py   ← (opcional) Estágios de workflow
```

### 10.3 Tool System

**Tool Registry:**
- Per-domain: `get_<domain>_tools()`
- Global: `app/tools/` (cross-domain: `search_candidates`, `list_jobs`)

**ToolDefinition:**
```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema
    function: Callable[..., Awaitable[dict]]
```

**Decorators:**
- `@tool_handler("<domain>")` — error handling, audit, fairness check
- `@register_agent("<domain>")` — registry
- `@register_domain` — auto-discovery no startup

**Permissions:** `app/tools/tool_permissions.yaml` — escopos `talent_funnel`, `job_table`, `in_job`, `global`, `universal`, `restricted_tools`.

### 10.4 `domain_mappings.py`

Mapeia agent_type → domain_id:

```python
AGENT_TYPE_TO_DOMAIN = {
    "job_planner": "job_management",
    "sourcing": "sourcing",
    "cv_screening": "cv_screening",
    "kanban_search": "kanban_search",
    # ... (~38 entries, incluindo company_settings e agent_studio adicionados em S02/PR2)
    "company": "company_settings",
    "company_settings": "company_settings",
    "minha_empresa": "company_settings",
    "settings_config": "company_settings",
    "agent_studio": "agent_studio",
}
DEFAULT_DOMAIN = "recruiter_assistant"
```

---

## 11. Agent Studio (Custom Agents)

`app/domains/agent_studio/` — sistema completo para usuários criarem agentes customizados via UI.

### 11.1 Estrutura

```
app/domains/agent_studio/
├── domain.py
├── custom_agent_runtime.py         ← Runtime dinâmico
├── actions.py
└── config/capabilities.yaml
```

### 11.2 Endpoints (`app/api/v1/custom_agents.py`)

- `POST /custom-agents` (create), `GET` (list), `PATCH`, `DELETE`
- `POST /custom-agents/generate-from-description` (PR1: Pydantic `GeneratedAgentConfig`)
- `POST /custom-agents/{id}/test`, `/execute`, `/publish`, `/clone`
- `GET /custom-agents/{id}/versions`, `POST .../revert/{version}`
- `GET /custom-agents/studio/consumption`, `/quota`, `/compliance-summary`, `/metrics/summary`

### 11.3 Lifecycle

```
draft → active → paused → archived
   ↑               ↓
   └── revert ─────┘
```

### 11.4 Marketplace

`MarketplaceListing` table — empresas publicam agentes (review approval) e instalam. Pricing: free ou credits per execution.

### 11.5 Calibration

- **DigitalTwins** — agente que aprende com decisões do recrutador
- **MultiStrategy** — busca em paralelo com 4 estratégias (direct, adjacent profiles, finalists, re-engagement)

---

## 12. Compliance & Security

Detalhado em [§9.2](#92-compliance-stack--14-sistemas-todos-reais) e [§9.3](#93-llm-compliance-layer-etapa-1).

### 12.1 Highlights

- **14 subsistemas reais** (não stubs)
- **PII masking global** (logs + LLM prompts + DLQ)
- **FairnessGuard 3 layers** com hard block opt-in
- **AuditService** em todos os 14 agentes
- **Field-level encryption** com Fernet em PII
- **WorkOS SSO + SCIM** enterprise-grade

### 12.2 Gaps conhecidos

- **Security Studio (Etapa 2)** — placeholder, sem pattern detection dinâmica
- **FactChecker** (post_compliance) — stub
- **HubSpot integration** — básica
- **Demo mode** — bypass de auth (risco em prod)

---

## 13. Deploy & DevOps

### 13.1 Backend

**Docker Compose:**

| Serviço | Imagem | Porta |
|---|---|---|
| postgres | pgvector/pgvector:pg16 | 5432 |
| redis | redis:7-alpine | 6379 |
| rabbitmq | rabbitmq:3-management | 5672 / 15672 |
| api | FastAPI | 8000 |
| api-vagas / api-funil | FastAPI variants | 8001 / 8002 |
| celery, celery-beat | worker / scheduler | async |

### 13.2 Frontend

- **Hosting:** Netlify
- **Build:** `npx next build`
- Env vars: `BACKEND_URL`, `WORKOS_*`, `NEXT_PUBLIC_*`

### 13.3 Database

- **Neon** (managed PostgreSQL), async pool 20+5
- Migrations: `alembic upgrade head`

### 13.4 Staging

- URL: `https://staging2.wedotalent.cc`
- Env: `RAILS_API_URL`, `RAILS_BACKEND_URL`

---

## 14. Roadmap & Pendências Conhecidas

### 14.1 Concluído recentemente (Sessão 2026-04-15)

| Item | Commit | Descrição |
|---|---|---|
| PR1 | `9ec36564` | Hotfix ConversationalCreator — defensividade frontend + `_coalesce` + Pydantic |
| PR2 | `610cac74` | Chat agent_studio — propagar contexto + render clarification chips |
| PR3 | `aa903f56` | LLM gaps visibility — validação startup + badge UX + docstring |

### 14.2 S02 (Settings Conversacional) — pendente

Arquivos pendentes de commit:
- `settings_progress.py` (sem hardcodes)
- `company_tool_registry.py` (12 tools com TIER 1-4)
- `company_settings.yaml` (onboarding modes)
- `domain_routing.yaml` (settings_config patterns)
- `domain_mappings.py` (entries)
- Migration `079` (workforce_entries + company_documents)
- `company_documents.py` endpoint + Celery task
- `capabilities.yaml`, `settings_tiers.yaml`

Ver `docs/settings-conversacional/S02_RELATORIO.md`.

### 14.3 Próximas sprints

- **S03:** Frontend "Minha Empresa" com 7 cards + UnifiedChat. 8-12 dias.
- **HiringPoliciesHub refactor:** migrar chat próprio → UnifiedChat
- **Modo bottom-dock chat:** registrado em `memory/feedback_chat_inferior.md`
- **Security Studio (Etapa 2):** pattern detection pra tools custom

### 14.4 Migrations pendentes

- Aplicar `079_company_workforce_and_documents.py` em staging + prod
- Restart Celery worker para pegar `process_company_document_task`

---

## 15. Apêndices

### 15.1 Glossário

| Termo | Definição |
|---|---|
| LIA | Learning Intelligence Assistant |
| WSI | Work Sample Interview |
| HITL | Human-in-the-Loop |
| DSR | Data Subject Request (LGPD) |
| PII | Personally Identifiable Information |
| ReAct | Reasoning + Acting |
| DDD | Domain-Driven Design |
| RBAC | Role-Based Access Control |
| SSO | Single Sign-On |
| SCIM | System for Cross-domain Identity Management |
| DLQ | Dead Letter Queue |
| RLS | Row-Level Security (PostgreSQL) |
| Tier 8 | Última camada do CascadedRouter (clarification fallback) |

### 15.2 Documentos canônicos relacionados

| Documento | Path |
|---|---|
| Guia WeDOTalent v3.4 | `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` |
| Design System v4.2.1 | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| Compliance Architecture | `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` |
| Sprint History | `docs/archived/sprint-history.md` |
| Runbook Operacional | `docs/RUNBOOK_DEGRADATION.md`, `docs/RUNBOOK_INCIDENT_PLAYBOOKS.md` |

### 15.3 ADRs

`docs/adr/`: ADR-001 (multi-agent), ADR-002 (observability), 001-python-not-ruby, 002-graph-vs-react.

### 15.4 Skills

`.agents/skills/`: `/feature-impact`, `/feature-audit`, `/vue-migration-prep`, `/design-standardize`, `/testing-patterns`, `/wedo-governance`, `/screening-compliance`, `/dei-fairness`, `/lgpd-data-protection`.

### 15.5 Env vars críticas

```bash
# App
APP_ENV=production|staging|development

# Database
NEON_DATABASE_URL=postgresql+asyncpg://...

# LLM Providers (pelo menos UM)
AI_INTEGRATIONS_ANTHROPIC_API_KEY=sk-ant-...
AI_INTEGRATIONS_GEMINI_API_KEY=...
AI_INTEGRATIONS_OPENAI_API_KEY=sk-...
LLM_DEFAULT_PROVIDER=gemini

# Encryption
FIELD_ENCRYPTION_KEY=<Fernet 32-byte base64>

# Auth
WORKOS_API_KEY, WORKOS_CLIENT_ID, WORKOS_WEBHOOK_SECRET

# Comm
MICROSOFT_APP_ID/PASSWORD/TENANT_ID
AZURE_CLIENT_ID/SECRET/TENANT_ID
WHATSAPP_VERIFY_TOKEN, TWILIO_ACCOUNT_SID, SENDGRID_API_KEY

# AI/ML
PEARCH_API_KEY, DEEPGRAM_API_KEY, APIFY_API_KEY, LANGCHAIN_API_KEY

# ATS
GUPY_API_KEY, PANDAPE_API_KEY, MERGE_API_KEY

# Observability
OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT

# Feature flags
LIA_DISABLE_C3B=false
FAIRNESS_LAYER3_ENABLED=true
DEMO_MODE=false

# Storage
LIA_UPLOAD_DIR=/tmp/lia_uploads
LIA_COMPANY_DOCS_DIR=/tmp/lia_uploads/company_documents
```

### 15.6 Comandos úteis

```bash
# Backend
cd lia-agent-system
uvicorn app.main:app --reload --port 8000
alembic upgrade head
celery -A app.core.celery_app worker --loglevel=info
pytest tests/

# Frontend
cd plataforma-lia
npm run dev
npx next build
npx tsc --noEmit
npm run test

# Git workflow
git status --short
git log --oneline -10
```

---

## Como manter este documento

Este documento é **source of truth técnica**. Ele só é útil se for mantido atualizado.

### Quem atualiza
- Toda mudança arquitetural (novo domínio, novo agente, nova integração, mudança em padrão) deve atualizar a seção correspondente.
- Time de Engenharia é responsável pelas seções 5-13.
- Time de Compliance é co-responsável pelas seções 12 e 9.2.

### Quando atualizar
- **No mesmo PR** que introduz a mudança arquitetural. Não deixar pra "depois".
- A cada release maior (mensal): revisão completa do sumário executivo (§1).

### Como validar
- A cada 3 meses: rerun de 5 Agents Explore (como no protocolo de criação) cruzando com código atual.
- Marcar `(verified YYYY-MM-DD)` em seções recém-validadas.

### O que NÃO entra aqui
- Decisões em discussão (use ADRs em `docs/adr/`)
- Especificações de produto/UX (use `docs/specs/`)
- Diagnósticos pontuais (use `docs/audit/` ou `docs/analises/`)
- Histórico de sprints (use `docs/archived/sprint-history.md`)

### Princípio de honestidade
Se algo está stub ou não funciona como esperado, **diga**. Documento decorativo que mente é pior que documento ausente.

---

**Versão atual:** 1.0
**Próxima revisão prevista:** 2026-07-15 (3 meses)
