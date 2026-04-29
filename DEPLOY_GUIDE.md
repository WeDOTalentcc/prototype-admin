# LIA Platform — Guia de Deploy e Fluxo de Desenvolvimento

> **Documento de referência para o time de engenharia.**
> Cobre a jornada completa: do ambiente de desenvolvimento no Replit até a produção no GCP Cloud Run, passando pelo ambiente de staging.
>
> **Última atualização:** 15 de abril de 2026
> **Changelog recente:**
> - **NOVA SEÇÃO 25** — Status de Integração Completa (snapshot abril/15) com checklist consolidado por time. Começar a leitura por aí para o estado atual.
> - **MIGRATION_PLAN: 72/90 (80%) concluído.** Sessão 4 fechou Sprints 1, 7, 8 via 10 commits cross-repo. Ref: `docs/audit/fase7-execucao/RELATORIO_SESSAO_4_2026-04-15.md`
> - **2 blockers críticos identificados (15/abr):**
>   1. Admin Panel não cria tenant no Rails — cliente criado fica inacessível na ATS (ver 25.3)
>   2. Follow-ups Sprint 7 (F-1 + F-2) não concluídos — `GET /v1/candidates?fork_uuid=<uuid>` ausente (ver 25.4)
> - **LLM Factory 95% pronto** — 3 providers (Claude/Gemini/OpenAI) + circuit breaker + multi-tenant. 3 micro-tasks para fechamento (ver 25.5).
> - **GCP operacional** — Cloud Run, RabbitMQ, Sentry, CORS, OTEL tracer. Pendente: secrets prod (MAILGUN, SENTRY_DSN, OTEL endpoint) + alertas Cloud Monitoring.
> - Bugs frontend 15/abr fixados: Kanban `t is not a function` (c5aad4ab) + Funil "Erro ao carregar candidatos" regressão do Task #195 (da000dd1).
> - Twilio Voice credenciais configuradas (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER=+551150289337)
> - WhatsApp Business pendente aprovação Meta (conta duplicada deletada, aguardando liberação)
> - P1/P4 resolvidos: zero `NEXT_PUBLIC_BACKEND_URL`/`NEXT_PUBLIC_API_URL` no codebase (Task #99)
> - P2/P3 resolvidos: build ok, DATABASE_URL apontando para banco real
> - P6 resolvido: WebSocket URLs parametrizadas com `NEXT_PUBLIC_WS_URL` (Task #74)
> - P5 reduzido: 4 arquivos de app (2 frontend + 2 backend) ainda usam vars Replit-only
> - Tasks #91/#92 canceladas; rotas migradas diretamente na Task #99
> - Migrations: 60 Alembic + 3 novas Rails (account_id, users.email index, fork_uuid); Endpoints: 362+; Models: 217+
> - Sidebar reordenada: Operacional → Recrutamento → Configuração

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Estado Atual (ANTES)](#2-estado-atual-antes)
2A. [Auditoria do Ecossistema Legado (wedocc2026)](#2a-auditoria-do-ecossistema-legado-wedocc2026)
2B. [Auditoria Real do Rails (ats-api-copia)](#2b-auditoria-real-do-rails-ats-api-copia)
2C. [Comparação Completa — Plataforma LIA vs Ecossistema WeDO](#2c-comparação-completa--plataforma-lia-vs-ecossistema-wedo-6-repos)
2D. [O que a Plataforma LIA já Cobre](#2d-o-que-a-plataforma-lia-já-cobre-correção-de-comparação)
2E. [Valor do ats-front-copia (Vue) para Migração Futura](#2e-valor-do-ats-front-copia-vue-para-migração-futura)
2F. [Decisão Arquitetural — Rails como Opt-in](#2f-decisão-arquitetural--rails-como-opt-in)
2G. [recruiter-agent-v5-copia — Análise e Comparação com LIA](#2g-recruiter-agent-v5-copia--análise-e-comparação-com-lia)
3. [Estado Alvo (DEPOIS)](#3-estado-alvo-depois)
4. [Fluxo de Desenvolvimento ao Cliente](#4-fluxo-de-desenvolvimento-ao-cliente)
5. [Ambientes](#5-ambientes)
6. [Passo a Passo de Deploy](#6-passo-a-passo-de-deploy)
7. [Fluxo de Trabalho do Time](#7-fluxo-de-trabalho-do-time)
8. [Variáveis de Ambiente](#8-variáveis-de-ambiente)
9. [Checklist Pré-Go-Live](#9-checklist-pré-go-live)
10. [Troubleshooting](#10-troubleshooting)
23. [Infraestrutura — Obrigatório vs Opcional para Deploy](#23-infraestrutura--obrigatório-vs-opcional-para-deploy)
24. [AUDITORIA PROFUNDA COMPARATIVA — Production Readiness](#24-auditoria-profunda-comparativa--production-readiness)
    - 24.1 [Inventário Comparativo](#241-inventário-comparativo)
    - 24.2 [Frontend — Comparativo](#242-frontend--comparativo)
    - 24.3 [Backend/API — Comparativo](#243-backendapi--comparativo)
    - 24.4 [Camada de IA — Comparativo](#244-camada-de-ia--comparativo)
    - 24.5 [Segurança & Compliance — Comparativo](#245-segurança--compliance--comparativo)
    - 24.6 [Infraestrutura & Deploy — Comparativo](#246-infraestrutura--deploy--comparativo)
    - 24.7 [Testes & Qualidade — Comparativo](#247-testes--qualidade--comparativo)
    - 24.8 [Observabilidade — Comparativo](#248-observabilidade--comparativo)
    - 24.9 [Análise Detalhada — Repos wedocc2026](#249-análise-detalhada--repos-wedocc2026)
    - 24.10 [Riscos Sistêmicos — Por Produto](#2410-riscos-sistêmicos--por-produto)
    - 24.11 [Scorecard Comparativo](#2411-scorecard-comparativo)
    - 24.12 [Roadmap Consolidado](#2412-roadmap-consolidado)
25. **[Status de Integração Completa — Snapshot 15/abr/2026](#25-status-de-integração-completa--snapshot-15abril2026)** ← COMEÇAR AQUI
    - 25.1 [Sumário Executivo](#251-sumário-executivo)
    - 25.2 [Status por Área](#252-status-por-área) (Frontend / FastAPI / Rails / Admin / Data Collector / GCP)
    - 25.3 [Blocker #1 — GAP CRÍTICO: Admin Panel → Rails Tenant](#253-blocker-1--gap-crítico-admin-panel--rails-tenant)
    - 25.4 [Blocker #2 — Follow-ups Sprint 7 (F-1 + F-2)](#254-blocker-2--follow-ups-sprint-7-não-concluídos-f-1--f-2)
    - 25.5 [LLM Factory — Status 95%](#255-llm-factory--status-95-3-micro-tasks-para-fechar)
    - 25.6 [**CHECKLIST CONSOLIDADO — Por Time**](#256-checklist-consolidado--por-time)
    - 25.7 [Ordem Recomendada de Ataque](#257-ordem-recomendada-de-ataque)

---

## 1. Visão Geral da Arquitetura

A Plataforma LIA é composta por dois serviços core obrigatórios e um backend legado opcional:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLATAFORMA LIA                           │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐                   │
│   │  plataforma-lia  │    │ lia-agent-system │                  │
│   │  (Next.js 15)   │◄──►│ (FastAPI/Python) │                  │
│   │  React/Tailwind  │    │  Claude/Gemini   │                  │
│   │  Porta: 5000    │    │  Porta: 8001     │                  │
│   └────────┬────────┘    └────────┬─────────┘                  │
│            │                      │                             │
│            │              ┌───────┘                             │
│            │              │  (PostgreSQL — fonte de verdade)   │
│            │              │                                     │
│            │         ╔════╧════════════════╗                   │
│            └────────►║   ats-api-copia     ║  ← OPCIONAL       │
│          (opcional)  ║  (Rails 7 / REST)   ║     dados legados │
│                      ╚════════════════════╝                   │
└─────────────────────────────────────────────────────────────────┘
```

> **Nota pós-auditoria (abril 2026):** O diagrama acima reflete a realidade descoberta na auditoria profunda do ecossistema wedocc2026. O Rails é um componente **opcional** — a plataforma funciona 100% sem ele. Quando `RAILS_BACKEND_URL` está vazia (situação atual), todas as rotas caem automaticamente no FastAPI. Ver Seção 2F para a decisão arquitetural completa.

| Serviço | Repositório | Tecnologia | Responsabilidade |
|---|---|---|---|
| Frontend | `plataforma-lia` | Next.js 15 + React + Tailwind | Interface do usuário, pages, componentes |
| AI Agent | `lia-agent-system` | FastAPI + Python + LangGraph | Agentes IA, orquestração, integrações, **fonte de verdade** |
| Rails API | `ats-api-copia` | Rails 7 + PostgreSQL | **Opcional** — dados legados de clientes reais do ATS antigo |

---

## 2. Estado Atual (ANTES)

### Infraestrutura em Produção Hoje

```
┌──────────────────────────────────────────────────────────────────┐
│                     STACK LEGADA (ANTES)                         │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────┐    │
│  │    wedo-nuxt-copia   │    │   recruiter-agent-v5-copia   │   │
│  │  (Vue 3 / Nuxt)     │◄──►│  (Python / Gemini / Langchain│   │
│  │  Frontend Legado    │    │   Agente Legado)             │   │
│  └──────────┬──────────┘    └──────────────┬───────────────┘   │
│             │                               │                    │
│             └───────────────┬───────────────┘                   │
│                             ▼                                    │
│                ┌────────────────────────┐                       │
│                │     ats-api-copia      │                       │
│                │  (Rails 7 + PostgreSQL) │                       │
│                │  ← permanece inalterado │                       │
│                └────────────────────────┘                       │
│                                                                  │
│  Ambiente:   Servidor próprio / VPS + Staging já existe         │
│  Deploy:     A confirmar com o time (manual ou CI/CD parcial)  │
│  Domínio:    wedotalent.cc                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Limitações do stack legado:**
- Frontend Vue/Nuxt sem sistema de design padronizado
- Agente Python com LangGraph implementado, porém aquém das capacidades esperadas — cobertura de domínios e robustez limitadas em relação à nova LIA
- Deploy: status a confirmar com o time — possivelmente manual ou com CI/CD parcial
- Ambiente de staging já existe (criado pelo time) — nível de integração e automação a verificar
- Observabilidade: Sentry ativo (org `talensesgroup-wedotalent`, 4 issues rastreadas) + LangSmith ativo (projeto `lia-agent-system`, 301+ traces). Cloud Logging e APM automáticos no GCP pós-deploy

---

## 2A. Auditoria do Ecossistema Legado (wedocc2026)

> Auditoria realizada em abril 2026 com dados verificados diretamente nos repositórios da organização wedocc2026 no GitHub.

### Mapa dos 6 Repos do Ecossistema WeDO

> **Nota:** O `wedotalent-admin-copia` (TypeScript/Next.js — Painel Admin) foi identificado mas **não faz parte do ecossistema Rails/ATS**. O mapa abaixo cobre apenas os 6 repos relevantes.

| Repositório | Stack | Tamanho | Papel no Ecossistema |
|---|---|---|---|
| `ats-api-copia` | Ruby on Rails 7 + PostgreSQL | Backend principal | API REST para CRUD de dados do ATS (candidatos, vagas, aplicações) |
| `ats-front-copia` | Nuxt 3 + Vue 3 + Vuetify | Frontend principal | ATS Frontend com 28 features, 336+ arquivos, ActionCable (WebSocket Rails) |
| `recruiter-agent-v5-copia` | Python + Celery + RabbitMQ | Agentes IA | Agentes IA v5: 8 domains, 7 agents especializados, LangGraph workflow |
| `wedo-nuxt-copia` | Vue 3 + Nuxt | Frontend v5 | Novo frontend (early stage — ~178 KB, em desenvolvimento) |
| `ats-mcp-copia` | TypeScript | MCP server | Integração de tools via Model Context Protocol — ~51 KB |
| `data-collector-copia` | Python | Sincronização | Scripts de sync/migração de dados entre sistemas ATS |

### Relação entre os repos

```
ats-front-copia (Nuxt/Vue)
    │
    ├── ActionCable → ats-api-copia (Rails) ← fonte de dados legada
    │
    └── Via API REST → ats-api-copia

recruiter-agent-v5-copia (Python)
    │
    └── Acessa dados via ats-api-copia (Rails REST API)

data-collector-copia (Python)
    └── Scripts de sincronização com ats-api-copia
```

---

## 2B. Auditoria Real do Rails (ats-api-copia)

> Auditoria de dados verificados linha a linha no repositório `wedocc2026/ats-api-copia`. Esta seção corrige informações incorretas presentes em versões anteriores deste documento.

### Os 6 Claims Verificados

#### Claim 1: Controllers

| Controller | Existe? | Funcional? |
|---|---|---|
| `CandidatesController` | ✅ Sim | CRUD completo, 2073 bytes |
| `JobsController` | ✅ Sim | CRUD com owner check, 2586 bytes |
| `AppliesController` | ✅ Sim | CRUD com soft delete |
| `SelectiveProcessesController` | ✅ Sim | — |
| `MessagesController` | ✅ Sim | — |
| `UsersController` | ✅ Sim | — |
| `ClientAccountsController` | ✅ Sim | via resources |
| `ClientUsersController` | ✅ Sim | via resources |
| `CompanyProfilesController` | ✅ Sim | via resources |
| `DepartmentsController` | ✅ Sim | via resources |
| `EmailTemplatesController` | ✅ Sim | via resources |
| `InterviewsController` | ✅ Sim | 2197 bytes |
| `NotificationsController` | ✅ Sim | via resources |
| `TalentPoolsController` | ✅ Sim | com ações custom (add_candidates, move_to_job) |
| `RecruitmentCampaignsController` | ✅ Sim | com ações custom (advance_stage, complete_stage) |
| `SessionsController` | ✅ Sim | JWT auth funcional |
| `CandidateListsController` | ❌ NÃO EXISTE | Faltante — frontend tem rotas backendTarget: "rails" que darão 404 |
| `InterviewNotesController` | ❌ NÃO EXISTE | Faltante — idem acima |
| `FeedbackController` | ❌ NÃO EXISTE | Faltante — idem acima |

**Veredicto:** São **16 controllers** (não 14). Os 3 faltantes estão confirmados.

#### Claim 2: Models vs Tabelas Reais no Banco

| O que existe | Quantidade | Detalhe |
|---|---|---|
| Arquivos `.rb` em `app/models/` | 97 arquivos | Existem como código Ruby |
| Tabelas **reais no banco** (schema.rb) | **12 tabelas** | accounts, applies, candidates, jobs, messages, permissions, role_permissions, roles, selective_processes, user_permissions, user_roles, users |
| Models "órfãos" (sem tabela) | ~85 arquivos | Existem como código mas sem tabela correspondente no banco |

**Veredicto:** Os 85 models sem tabela vão crashar qualquer feature que os use. As migrações que criariam client_accounts, departments, email_templates, interviews, etc. nunca foram aplicadas ao banco.

#### Claim 3: Migrações

| Item | Valor Real |
|---|---|
| Total de migrações no repo | **49** (não 47) |
| Versão do schema.rb | `2025_07_14_142059` |
| Migrações **aplicadas** ao banco | ~18 (anteriores a 20250715) |
| Migrações **NÃO aplicadas** | **31** (de 20250715 em diante) |

**Veredicto:** 31 migrações foram adicionadas ao repo mas nunca executadas contra o banco.

#### Claim 4: Routes CRUD Funcionais

**Veredicto:** Rotas CRUD existem para candidates, jobs, applies, selective_processes, messages, users, client_accounts, client_users, company_profiles, departments, email_templates, interviews, notifications, talent_pools, recruitment_campaigns, sessions. **MAS:** como apenas 12 tabelas existem no banco, as routes para departments, email_templates, interviews, etc. vão retornar erro de banco — os models Ruby existem mas as tabelas não.

#### Claim 5: RBAC enforcement

**Veredicto: CONFIRMADO que está faltando.** O `ApplicationController` tem apenas:
- `authorize_request` — verifica JWT válido
- `only_admin` — check simples `@current_user.is_admin`
- `ensure_owner` no `JobsController` — verifica se o user é dono do job

As tabelas `roles`, `permissions`, `role_permissions`, `user_roles`, `user_permissions` existem no schema, mas **nenhum controller usa esses dados para autorização**. O RBAC está montado no banco mas completamente desconectado da aplicação. Não existe Pundit, CanCanCan, Rolify, ou qualquer sistema de RBAC granular.

#### Claim 6: Auth unificada (JWT)

**Veredicto: PARCIALMENTE FEITO.**
- ✅ Rails gera JWT com `Rails.application.secret_key_base` e payload `{user_id, exp}`
- ✅ FastAPI tem `rails_jwt.py` que decodifica JWT com `RAILS_JWT_SECRET_KEY`
- ❌ Falta: configurar o mesmo secret nos dois lados e testar end-to-end
- ❌ Falta: Refresh token — o JWT expira em 24h e não há mecanismo de renovação

### Tabela Resumo: O que o Documento Dizia vs Realidade

| O que o documento anterior dizia | Realidade verificada na auditoria |
|---|---|
| 14 controllers existem | 16 existem, 3 faltam — número estava errado |
| 93 models existem | 97 arquivos, mas **só 12 têm tabelas** no banco — muito enganoso |
| 47 migrações | 49 migrações, mas **31 não foram aplicadas** |
| Schema completo | Schema tem 12 tabelas, não 97 — banco incompleto |
| Rails "quase pronto" | Esqueleto existe, banco incompleto, RBAC decorativo, sem infra (Redis, Elasticsearch) |
| "~2 semanas de trabalho" para integrar | Subestimado — migrações faltantes + conflitos + debug pode levar 3-4 semanas |

### Problemas Críticos Identificados (Não Documentados Anteriormente)

1. **Gap massivo models/tabelas:** 97 models vs 12 tabelas — qualquer feature que use os 85 models sem tabela vai crashar
2. **Apartment (multi-tenancy):** configurado no Gemfile mas schema.rb mostra tabelas compartilhadas — sem evidência que schemas por tenant existam
3. **Searchkick sem Elasticsearch:** no Gemfile mas sem Elasticsearch configurado — `perform_search` vai falhar
4. **Sidekiq sem Redis:** no Gemfile mas sem Redis e workers configurados — background jobs não funcionam
5. **90+ rotas frontend com `backendTarget: "rails"`:** como `RAILS_BACKEND_URL` está vazia, tudo cai no FastAPI hoje — correto. Se alguém configurar essa variável sem o Rails estar pronto, quebra tudo de uma vez
6. **31 migrações não executadas:** schema.rb em `2025_07_14_142059` mas 31 migrações posteriores no repo — podem ter conflitos

---

## 2C. Comparação Completa — Plataforma LIA vs Ecossistema WeDO (6 repos)

> Comparação justa considerando **todos os 6 repos** do ecossistema WeDO, não apenas o Rails.

| Capacidade | WeDO (6 repos combinados) | Plataforma LIA (Replit — 2 repos) |
|---|---|---|
| **Backend API** | Rails: 16 controllers, **12 tabelas reais** | FastAPI: **362+ endpoints**, **217+ models**, 60 migrações aplicadas |
| **Frontend** | Vue/Nuxt/Vuetify: 28 features, 58 composables, 18 stores Pinia | Next.js/React/Tailwind: **36+ páginas**, Design System completo |
| **Agentes IA** | recruiter-agent-v5: 8 domains, 7 agents, Celery + RabbitMQ | LangGraph: **58 domains**, **147 services**, WSI, voice, bias audit |
| **Auth** | JWT básico (sem RBAC funcional) + WorkOS no Rails | JWT + WorkOS no FastAPI + TenantGuard |
| **WebSocket** | ActionCable (depende do Rails) | WebSocket nativo FastAPI — sem dependência extra |
| **Multi-tenancy** | Apartment gem (não testado, schemas não encontrados) | `company_id` + `tenant_guard` + `auth_enforcement` |
| **Busca** | Searchkick/Elasticsearch (precisa infra extra) | SQL + embeddings semânticos + busca híbrida |
| **Background jobs** | Sidekiq + Celery + RabbitMQ (3 sistemas) | Celery com 12+ tasks + async nativo Python |
| **Compliance** | Não encontrado | LGPD, Bias Audit, Governance completos |
| **Voice/Audio** | Composables de audio no Vue (frontend) | Voice screening completo (Gemini Live Audio) |
| **Observabilidade** | Básica | Circuit breakers, audit logs, tracing, Sentry |
| **Deploy infra obrigatória** | Docker + Redis + Elasticsearch + RabbitMQ + ActionCable | Apenas PostgreSQL — zero dependências extras obrigatórias |
| **Services (camada de negócio)** | 0 (lógica inline nos controllers) | **147 services** cobrindo toda a plataforma |
| **Domínios de negócio** | ~5 funcionais | **58 domínios** estruturados |
| **Migrações aplicadas** | 18 de 49 | 60 migrações aplicadas, banco completo |

---

## 2D. O que a Plataforma LIA já Cobre (Correção de Comparação)

> Esta seção documenta capacidades que existem na plataforma LIA e foram inicialmente subestimadas ou incorretamente comparadas como "ausentes".

### Google Calendar e Agendamento

A plataforma LIA tem agendamento completo — mais profundo que o `smart-calendar` do Vue (4 arquivos):

- **`zero_touch_scheduling_service.py`** (351 linhas) — scheduling zero-touch: candidato recebe link, escolhe horário, entrevista é criada automaticamente
- **`google_calendar_client.py`** — integração Google Calendar (shim apontando para `integrations_hub`)
- **Frontend:** rotas prontas em `/api/backend-proxy/calendar/google/auth-url`, `/calendar/health`, `/calendar/reschedule-interview`, `/scheduling/link`

### Kanban / Pipeline (Visualização de Workflow)

34 arquivos só no Kanban board (`plataforma-lia/src/components/kanban/`):
- `KanbanBoard.tsx`, `KanbanColumn.tsx`, `CandidateCard.tsx`
- Drag & drop, filtros, transições universais, context menu por coluna, badges de saturação
- Hooks: `use-drag-drop`, `use-kanban-filters`, `use-universal-transition`, `use-column-config`
- Testes automatizados inclusos

> O `Vue Flow` (editor visual de fluxos tipo draw.io) que o ecossistema WeDO tem é diferente do kanban — esse sim não existe na LIA.

### WebSocket Nativo

A LIA tem WebSocket nativo — sem dependência de Rails (ActionCable):
- **`ws_manager.py`** — gerenciador de conexões WebSocket
- **`agent_chat_ws.py`** — chat em tempo real
- **`jobs_ws.py`** — atualizações de vagas
- **`gemini_voice.py`** — voice streaming via WebSocket
- **Frontend:** `useChatSocket.ts`, `use-agent-streaming.ts`, `use-float-streaming.ts`

### Multi-tenancy

Enforcement completo via:
- **`tenant_guard.py`** — enforça isolamento por tenant (rejeita cross-tenant em produção)
- **`tenant_llm_context.py`** — contexto LLM por tenant
- **`auth_enforcement.py`** — middleware de autenticação por empresa
- `company_id` em todas as queries e models

### Background Jobs (Celery)

Celery configurado com 12+ tasks (`celery_tasks.py` — 1692 linhas):
- drift check em batch, triagem curricular em lote, sourcing via Pearch
- email em massa, briefing diário, follow-up automático
- WSI abandonados, feedback automático, avaliação RAGAS, weekly digest
- Broker pode ser Redis ou RabbitMQ (configurável no deploy)

### Busca Semântica + Híbrida

Mais avançada que Elasticsearch/Searchkick:
- **`semantic_search_service.py`** — busca por embeddings (entende significado, não só keywords)
- **`hybrid_search_service.py`** — combina busca semântica (pgvector) + FTS (tsvector) com score híbrido configurável
- **`domain_embedding_service.py`** — embeddings por domínio
- RAG pipeline para contexto dos agentes

---

## 2E. Valor do ats-front-copia (Vue) para Migração Futura

> O `ats-front-copia` é um frontend Vue/Nuxt/Vuetify substancial — mais maduro que o React em algumas features específicas. Esta seção documenta o que tem valor e o que a LIA já cobre.

### Inventário do ats-front-copia

| Feature Vue | Arquivos | Valor |
|---|---|---|
| `messages` | 101 arquivos | Alta — UI de mensagens mais desenvolvida, chat, áudio, streaming |
| `candidates` | 55 arquivos | Média — a LIA já tem equivalente mas com menos profundidade de UI |
| `jobs` | 43 arquivos | Média — a LIA já tem equivalente |
| `composables` | 58 composables | Alta — cobrindo audio, sourcing, calendar, interviews, voice, LLM quota |
| `stores (Pinia)` | 18 stores | Média — state management estruturado |
| `smart-calendar` | 4 arquivos | Baixa — a LIA tem equivalente mais profundo no backend |

### Features Vue que a LIA já cobre

| Feature Vue | Status na LIA |
|---|---|
| Kanban/Pipeline | ✅ 34 arquivos, drag & drop, filtros, transições |
| Google Calendar / agendamento | ✅ zero_touch_scheduling_service.py (351 linhas) |
| WebSocket real-time | ✅ nativo FastAPI, sem ActionCable |
| Multi-tenancy | ✅ tenant_guard + company_id |
| Background jobs | ✅ Celery 12+ tasks |
| Auth | ✅ JWT + WorkOS |
| Voice/Audio | ✅ Gemini Live Audio + voice screening completo |
| Busca | ✅ semântica + híbrida (mais avançada que Searchkick) |
| WorkOS | ✅ integrado no Next.js |

### Features Vue que teriam valor real para migrar para o React

| Feature Vue | Existe na LIA? | Valor de migrar |
|---|---|---|
| **Messaging UI** (101 arquivos) | Parcialmente | **Alta** — UI mais madura com chat, áudio, streaming de mensagens |
| **TipTap editor** | Não (editor mais simples) | Alta — editor rich text para templates de email |
| **Vue Flow** | Não | Média — editor visual de fluxos (type draw.io para processos) |
| `ActionCable` WebSocket | Substituído por WS nativo | Não precisa migrar |

> **Recomendação:** O que vale considerar é **migrar as features boas do Vue para o React** (especialmente a UI de messages e o TipTap), não manter o Rails como backend.

---

## 2F. Decisão Arquitetural — Rails como Opt-in

> Esta seção documenta a decisão estratégica resultante da auditoria de abril 2026.

### Decisão

**FastAPI é a fonte de verdade. Rails NÃO é necessário para o funcionamento da plataforma.**

### Fundamentos da Decisão

1. **O app funciona 100% sem Rails.** Quando `RAILS_BACKEND_URL` está vazia (situação atual), todas as 94 rotas com `backendTarget: "rails"` caem automaticamente no FastAPI via `proxy-handler.ts`. Nada quebra.

2. **O FastAPI já faz tudo que o Rails faz — e mais.** O Rails provê CRUD para ~5 entidades. O FastAPI tem 362+ endpoints, 58 domínios, 147 services, toda a camada de IA, compliance e um frontend completo.

3. **A camada de integração Rails já está pronta.** Se e quando Rails for ativado, o código já existe:
   - `wedotalent_rails.py` — 588 linhas, HTTP client completo com retry e backoff
   - `rails_adapter.py` — 939 linhas, field mapping completo Fork ↔ Rails
   - Circuit breaker com fallback automático para FastAPI
   - `rails_jwt.py` — JWT validator para tokens Rails
   - Health check endpoint para Rails
   - ~94 rotas frontend marcadas com `backendTarget: "rails"`

4. **O banco Rails tem gaps significativos.** 12 tabelas reais vs 97 models, 31 migrações não aplicadas, RBAC desconectado. Integrar "agora" exigiria 3-4 semanas de trabalho no Rails.

### As 3 Opções Avaliadas

| Opção | Descrição | Decisão |
|---|---|---|
| **A. Clonar Rails no Replit** | Instalar Ruby/Rails, apontar para banco Neon, rodar migrações | **Rejeitada** — adiciona infra (Ruby, Redis, Elasticsearch) que pode desestabilizar o que já funciona. Banco compartilhado é risco. |
| **B. Criar tabelas via SQL/Alembic** | Traduzir 31 migrações Rails para SQL puro ou Alembic | **Rejeitada** — cria tabelas sem aplicação para populá-las. Trabalho desperdiçado se Rails não estiver rodando. |
| **C. Replicar no FastAPI (status quo)** | FastAPI já tem equivalentes para tudo — continuar construindo aqui | **✅ Adotada** — FastAPI é a fonte de verdade. Rails entra como upgrade opt-in para dados legados, rota por rota, quando houver servidor dedicado. |

### Como ativar o Rails (quando chegar o momento)

```
Pré-requisitos para ativar Rails:
  1. Servidor dedicado para Rails (GCP, Replit separado, etc.)
  2. Dados reais de clientes no banco Rails que precisam ser acessados
  3. Infra completa: Redis (Sidekiq), Elasticsearch (Searchkick)
  4. 31 migrações faltantes rodadas e conflitos resolvidos
  5. 3 controllers faltantes criados (CandidateLists, InterviewNotes, Feedback)
  6. RBAC conectado (usar tabelas roles/permissions que já existem)

Ativação gradual (plug-and-play):
  1. Configurar RAILS_BACKEND_URL e RAILS_API_URL no ambiente
  2. Rodar health check: GET /health/rails
  3. Flipar uma rota de cada vez (domínio por domínio)
  4. Monitorar circuit breaker — fallback automático para FastAPI se Rails falhar
```

### Esforço estimado para ativar Rails (no servidor dedicado)

| Item | Esforço |
|---|---|
| Rodar 31 migrações faltantes e resolver conflitos | 1-2 dias |
| Criar 3 controllers faltantes | 1 dia |
| Conectar RBAC real | 2-3 dias |
| Configurar Searchkick (Elasticsearch) | 1 dia |
| Configurar Sidekiq (Redis) | 1 dia |
| Refresh token JWT | 4 horas |
| Testar end-to-end | 1-2 dias |
| **Total estimado** | **~2-3 semanas** |

> **Nota:** Esse esforço ocorre no servidor Rails (fora do Replit), não impacta o desenvolvimento contínuo da plataforma LIA.

### Route Migration Status (Tasks #91/#92 cancelled → Task #99 completed directly)

> **Nota (abril 2026):** As Tasks #91 e #92 foram planejadas para migrar rotas Rails→FastAPI de forma gradual, mas foram **canceladas** porque o trabalho foi feito diretamente na Task #99, que migrou todos os 104 arquivos de proxy routes + os 11 arquivos frontend restantes de uma vez.

All **104 frontend proxy route files** have been migrated from Rails-dependent patterns to FastAPI:

- **94 routes** using `createProxyHandlers` (auto-fallback via `proxy-handler.ts`)
- **10 manual-fetch routes** (recruitment-campaigns and talent-pools) rewritten to call FastAPI directly
- **11 arquivos frontend** que usavam `NEXT_PUBLIC_BACKEND_URL`/`NEXT_PUBLIC_API_URL` diretamente — todos migrados para proxy routes
- **Zero Rails references remain** in proxy routes — `backendTarget: "rails"` fully eliminated
- **Zero `NEXT_PUBLIC_BACKEND_URL`/`NEXT_PUBLIC_API_URL`** no codebase

When `RAILS_BACKEND_URL` is empty (default), all requests go to FastAPI. No manual route flipping needed.

### Rails Consumption API (Task #92 — rails_sync.py)

FastAPI now exposes reverse-direction endpoints for Rails to consume AI/enrichment data:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/rails-sync/candidates/{id}/enrichment` | GET | WSI scores, AI insights, screening |
| `/api/v1/rails-sync/jobs/{id}/intelligence` | GET | Sourcing data, market saturation |
| `/api/v1/rails-sync/compliance/status` | GET | LGPD, audit, platform stats |
| `/api/v1/rails-sync/bulk-sync/candidates` | POST | Batch enrichment (max 50) |

Auth: `Authorization: Bearer <RAILS_API_TOKEN>` (same token, bidirectional). Rate limit: 120 req/60s.

See `lia-agent-system/RAILS_API_INTEGRATION.md` for full endpoint docs, Ruby examples, and model gap analysis.

---

## 2G. recruiter-agent-v5-copia — Análise e Comparação com LIA

> O `recruiter-agent-v5-copia` é o agente Python legado do ecossistema WeDO. Esta seção documenta o que ele tem e como a LIA o supera.

### O que o recruiter-agent-v5 tem

| Componente | Detalhe |
|---|---|
| **Domains** | 8: applies, autonomous, evaluation, insights, jobs, messaging, scheduling, sourcing |
| **Agents** | 7 especializados: intent_analyzer, api_planner, api_executor, data_processor, answer_formatter, plan_validator |
| **Infraestrutura** | Celery + RabbitMQ para processamento assíncrono |
| **Orquestração** | LangGraph workflow e orchestrator |

### Comparação com a LIA

| Dimensão | recruiter-agent-v5 | Plataforma LIA |
|---|---|---|
| **Domains** | 8 | **53** |
| **Agents** | 7 | Múltiplos por domínio (LangGraph) |
| **Services** | 0 (lógica nos agents) | **147 services** |
| **WSI (triagem por voz)** | Não | ✅ Completo |
| **Bias Audit** | Não | ✅ FairnessGuard, Four-Fifths Rule |
| **LGPD/Compliance** | Não | ✅ Completo (PII masking, DSR, retenção) |
| **RAG / Embeddings** | Não | ✅ pgvector, busca semântica, hybrid search |
| **Voice screening** | Não | ✅ Gemini Live Audio |
| **Explicabilidade** | Não | ✅ Explainability nos decisions |
| **Multi-tenant enforcement** | Não | ✅ TenantGuard + company_id |
| **Observabilidade** | Básica | ✅ Circuit breakers, audit logs, Sentry |

> **Veredicto:** A LIA supera o recruiter-agent-v5 em todas as dimensões. O v5 pode ser descontinuado assim que a migração para a LIA estiver completa.

---

## 3. Estado Alvo (DEPOIS)

### Infraestrutura LIA no GCP

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        STACK LIA — GCP (DEPOIS)                          │
│                                                                          │
│   Domínio: wedotalent.cc          SSL: Google-managed Certificate        │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Cloud Load Balancer                           │   │
│   │              (SSL termination + path-based routing)              │   │
│   └──────────────┬───────────────────────────┬───────────────────────┘  │
│                  │ /                          │ /api/agent/*             │
│                  ▼                            ▼                          │
│   ┌──────────────────────────┐  ┌──────────────────────────────────┐   │
│   │   Cloud Run: lia-frontend │  │   Cloud Run: lia-agent           │   │
│   │   (Next.js 15 / Docker)   │  │   (FastAPI / Docker)             │   │
│   │   Min 1 instance          │  │   Min 1 instance                 │   │
│   │   Max 10 instances        │  │   Max 5 instances                │   │
│   │   2 vCPU / 2 GB RAM       │  │   4 vCPU / 4 GB RAM             │   │
│   └─────────────┬─────────────┘  └───────────────┬──────────────────┘  │
│                 │                                 │                      │
│                 └─────────────┬───────────────────┘                     │
│                               ▼                                          │
│              ┌────────────────────────────────┐                         │
│              │      Cloud SQL (PostgreSQL 16)   │                        │
│              │      Instância compartilhada     │                        │
│              │      Rails DB + LIA DB           │                        │
│              └────────────────────────────────┘                         │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐     │
│   │ Cloud Storage │  │ Cloud Redis  │  │    Secret Manager        │     │
│   │  (CVs/Docs)  │  │  (Cache/Job) │  │  (API Keys / Env Vars)   │     │
│   └──────────────┘  └──────────────┘  └──────────────────────────┘     │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐                                   │
│   │ Cloud Logging │  │   Sentry     │                                   │
│   │  (Observ.)   │  │   (Erros)    │                                   │
│   └──────────────┘  └──────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Ganhos com a nova arquitetura:**
- Auto-scaling: Cloud Run sobe instâncias automaticamente sob carga
- Zero downtime deploy: Cloud Run faz blue/green deployment nativo
- Banco compartilhado: Rails e FastAPI leem o mesmo PostgreSQL (Cloud SQL)
- CI/CD automático: push na `main` → staging; tag `v*.*.*` → produção
- Observabilidade: logs centralizados no Cloud Logging + erros no Sentry
- Segredos gerenciados: Secret Manager (sem `.env` em produção)

---

## 4. Fluxo de Desenvolvimento ao Cliente

### Visão completa — ciclo contínuo do produto

O produto opera em três ciclos simultâneos que se alimentam:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CICLO COMPLETO DO PRODUTO — DESENVOLVIMENTO → OPERAÇÃO          │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 1 — NOVAS FEATURES                            │   │
│  │                                                                        │   │
│  │  Spec / demanda                                                        │   │
│  │  (PM ou time) ──► Desenvolvimento ──► PR + Review ──► Staging         │   │
│  │                                                             │          │   │
│  │                                              QA aprova?    │          │   │
│  │                                                 Sim ────► Produção   │   │
│  │                                                 Não ────► Fix + retry│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 2 — BUGS E CORREÇÕES                          │   │
│  │                                                                        │   │
│  │  Bug encontrado ──► Triage ──► hotfix/* branch ──► Staging            │   │
│  │  (QA, time ou       (Jira)       ou fix/* branch       │              │   │
│  │   cliente)                                        QA valida?          │   │
│  │                                                        │              │   │
│  │                                              Sim ────► Produção       │   │
│  │                                              Não ────► Fix + retry   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 3 — FEEDBACK DO CLIENTE                       │   │
│  │                                                                        │   │
│  │  Cliente reporta bug ──────────────────────► Ciclo 2 (correção)      │   │
│  │  ou faz sugestão                                                       │   │
│  │       │                                                                │   │
│  │  PM/time faz triage                                                    │   │
│  │       │                                                                │   │
│  │       ├── Bug confirmado ─────────────────► Ciclo 2                  │   │
│  │       ├── Feature aprovada ───────────────► Ciclo 1 (nova feature)   │   │
│  │       └── Fora do escopo / backlog ───────► Documentado no Jira      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ciclo 1 — Novas features: do código à produção

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUXO: NOVA FEATURE → PRODUÇÃO                        │
│                                                                          │
│  1. DESENVOLVIMENTO  (responsabilidade do time de engenharia)            │
│  ───────────────────────────────────────────────────────────            │
│                                                                          │
│   Time de engenharia (ambiente central — todos os devs)                 │
│   ┌──────────────────────────────────────────────────────────┐         │
│   │  Replit  ──── ou ────  VS Code / Cursor / qualquer IDE   │         │
│   │  (mesmo repositório GitHub, mesmas branches, mesmo fluxo)│         │
│   │  plataforma-lia/ · lia-agent-system/ · Porta 5000 + 8001 │         │
│   └──────────────────────────┬───────────────────────────────┘         │
│                               │                                          │
│   + Você (PM/produto)         │  contribui com features e protótipos    │
│     no mesmo fluxo ───────────┘  sem ser responsável pelo processo      │
│                                                                          │
│              │ git push → branch feature/*                              │
│              ▼                                                           │
│                                                                          │
│  2. PULL REQUEST                                                         │
│  ───────────────                                                         │
│                                                                          │
│   feature/* ──────────────► develop                                     │
│                                PR review pelo time                       │
│                                Testes automáticos (GitHub Actions)      │
│                                                                          │
│  3. STAGING + QA                                                         │
│  ────────────────                                                        │
│                                                                          │
│   develop branch → deploy automático → STAGING GCP                      │
│   ┌───────────────────────────────────────────────────────┐             │
│   │  staging.wedotalent.cc                                │             │
│   │  QA manual pelo time (checklist por feature)          │             │
│   │  Demo para cliente quando aplicável                  │             │
│   └───────────────────────────────────────────────────────┘             │
│              │                                                           │
│        QA aprovou?                                                       │
│        ├── Sim → PR: develop → main                                     │
│        └── Não → fix na branch → re-teste no staging                   │
│              │                                                           │
│              ▼                                                           │
│                                                                          │
│  4. PRODUÇÃO                                                             │
│  ─────────────                                                           │
│                                                                          │
│   develop → main  (merge manual com aprovação)                           │
│   main branch → deploy automático → PRODUÇÃO GCP                        │
│   ┌───────────────────────────────────────────────────────┐             │
│   │  wedotalent.cc                                        │             │
│   │  Cloud Run (prod) ← banco de dados produção          │             │
│   │  Clientes finais acessam aqui                        │             │
│   └───────────────────────────────────────────────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estratégia de branches

```
main          ──────────────────────────────────►  PRODUÇÃO
                  ▲               ▲
develop       ────┴───────────────┤   STAGING
                  ▲               │
feature/*     ────┘               │   branches de feature (PR → develop)
                                  │
hotfix/*      ────────────────────┘   correções urgentes (PR → main direto)
                                      depois sincroniza: main → develop
```

| Branch | Ambiente | Deploy | Banco | Uso |
|---|---|---|---|---|
| `feature/*` | Replit / local | Manual (dev) | Postgres local | Novas features e melhorias |
| `fix/*` | Replit / local | Manual (dev) | Postgres local | Correções não urgentes (P3/P4) |
| `develop` | Staging GCP | Automático (push) | Cloud SQL staging | Integração contínua |
| `hotfix/*` | Local → Produção | PR → main | Cloud SQL prod | Bugs P1/P2 em produção |
| `main` | Produção GCP | Automático (push) | Cloud SQL produção | Código em produção |

---

## 5. Ambientes

### Comparação dos três ambientes

| | **Desenvolvimento** | **Staging** | **Produção** |
|---|---|---|---|
| **URL Frontend** | `localhost:5000` | `staging.wedotalent.cc` | `wedotalent.cc` |
| **URL Backend** | `localhost:8001` | `api-staging.wedotalent.cc` | `api.wedotalent.cc` |
| **Banco** | PostgreSQL local (Replit) | Cloud SQL - instância staging | Cloud SQL - instância prod |
| **AI Models** | Claude + Gemini (keys do Replit) | Mesmas keys (Secret Manager) | Mesmas keys (Secret Manager) |
| **Deploy** | Automático no Replit | GitHub Actions → Cloud Run | GitHub Actions → Cloud Run |
| **Logs** | Console Replit | Cloud Logging | Cloud Logging + Sentry |
| **Branch** | feature/* | develop | main |

### Conectar Replit ao Staging

Para testar features do Replit contra o banco de staging (sem subir código):

```bash
# No Replit, mudar temporariamente as variáveis de ambiente:
DATABASE_URL=<staging-cloud-sql-url>
BACKEND_URL=https://api-staging.wedotalent.cc

# Reiniciar os serviços localmente
```

> **Atenção:** Nunca apontar o Replit para o banco de **produção** durante desenvolvimento.

---

## 6. Passo a Passo de Deploy

> **O que fazer agora vs. o que fazer no momento do deploy:**
>
> | O que fazer **agora** (desenvolvimento em curso) | O que fazer **na hora do deploy** (esta seção) |
> |---|---|
> | Continuar desenvolvendo features no Replit | Criar o Dockerfile do Next.js (Fase 1.1 abaixo) |
> | Finalizar fluxos críticos e resolução de mockups | Configurar variáveis de produção no Secret Manager |
> | Integrar e testar com Rails API localmente | Push para GitHub + ativar GitHub Actions |
> | Validar fluxos no ambiente Replit | Provisionar GCP: Cloud Run, Cloud SQL, Redis |
> | Preparar specs e documentação | Configurar domínio `wedotalent.cc` e SSL |
> | Resolver pendências de UI listadas na Seção 12 | Rodar smoke tests no staging existente |
>
> As fases abaixo são o **manual de referência para o time de infra** no momento do go-live — não são ações urgentes para o desenvolvimento atual.

### Fase 1 — Preparação do código (Replit)

#### 1.1 Dockerfile do Next.js

Criar `plataforma-lia/Dockerfile`:

```dockerfile
FROM node:22-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json bun.lock* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]
```

Adicionar em `plataforma-lia/next.config.js`:
```js
output: 'standalone'  // necessário para Docker otimizado
```

#### 1.2 Arquivo de variáveis de referência

Criar `plataforma-lia/.env.production.example`:

```bash
# Backend URL — server-side only (rewrites + proxy routes)
BACKEND_URL=https://api.wedotalent.cc
NEXT_PUBLIC_APP_URL=https://wedotalent.cc
NEXT_PUBLIC_WS_URL=wss://api.wedotalent.cc

# Rails (para rotas com backendTarget: "rails" no proxy-handler.ts)
RAILS_BACKEND_URL=https://api.wedotalent.cc

# Auth (Microsoft/Azure AD)
MICROSOFT_APP_ID=246eb1e7-a437-4cb2-a231-0325b567be5f
MICROSOFT_APP_PASSWORD=<secret>
AZURE_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6

# Analytics (opcional)
NEXT_PUBLIC_SENTRY_DSN=<sentry-dsn>
```

Criar `lia-agent-system/.env.production.example`:

```bash
# Database (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://lia_user:<password>@<cloud-sql-ip>/lia_db

# AI Models
ANTHROPIC_API_KEY=<secret>
OPENAI_API_KEY=<secret>              # fallback opcional
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json  # ou Workload Identity
GOOGLE_CLOUD_PROJECT=wedotalent-prod

# Microsoft Teams Bot
MICROSOFT_APP_ID=246eb1e7-a437-4cb2-a231-0325b567be5f
MICROSOFT_APP_PASSWORD=<secret>
AZURE_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6
# Teams-specific (obrigatório para aquisição de token do Bot)
TEAMS_APP_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6
# URL pública da plataforma (usada pelo manifest do Teams e deep links)
WEDOTALENT_PLATFORM_URL=https://ai.wedotalent.cc

# Cache e filas
REDIS_URL=redis://<cloud-redis-ip>:6379/0
RABBITMQ_URL=amqp://<user>:<pass>@<host>:5672/

# Rails API (backend→backend: FastAPI chama Rails)
RAILS_API_URL=https://api.wedotalent.cc

# Segurança
SECRET_KEY=<mesma-do-frontend>
API_PORT=8001

# Observability
SENTRY_DSN=<sentry-dsn>
LANGCHAIN_API_KEY=<langsmith-secret>  # opcional
```

#### 1.3 Configuração do banco compartilhado

No `lia-agent-system/app/core/config.py`, garantir que o `DATABASE_URL` venha de variável de ambiente (já existe):

```python
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://lia_user:lia_password@localhost/lia_db")
```

Para staging/produção, apenas apontar a variável para o Cloud SQL do Rails.

---

### Fase 2 — GitHub (repositórios)

#### 2.1 Push do frontend para `ats-front-copia`

```bash
cd plataforma-lia/
git init
git remote add origin https://github.com/wedocc2026/ats-front-copia.git
git add .
git commit -m "feat: initial LIA platform frontend"
git push -u origin main
```

#### 2.2 Push do agent para repositório próprio

```bash
cd lia-agent-system/
git init
git remote add origin https://github.com/wedocc2026/lia-agent-system.git
git add .
git commit -m "feat: initial LIA agent system"
git push -u origin main
```

#### 2.3 GitHub Actions — CI/CD Frontend

Arquivo: `plataforma-lia/.github/workflows/deploy.yml` (já criado)

- Trigger: push em `develop` (staging) ou `main` (production)
- Jobs: Security Scan (npm audit) → Build Docker → Push Artifact Registry → Deploy Cloud Run
- Smoke test automático após deploy
- Build args para variáveis NEXT_PUBLIC_* via GitHub Secrets

#### 2.4 GitHub Actions — CI/CD Backend

Arquivo: `lia-agent-system/.github/workflows/deploy.yml` (já criado)

- Trigger: push em `develop` (staging) ou `main` (production)
- Jobs: Security Scan (bandit + pip-audit) → Build API + Worker → Push Artifact Registry → Deploy Cloud Run
- Deploya `lia-api` (Cloud Run Service, Gunicorn) + `lia-worker` (Cloud Run Service, Celery + health wrapper, --no-cpu-throttling --min-instances=1)
- Secrets sensíveis via GCP Secret Manager (não GitHub Secrets)
- Alembic upgrade head roda no startup do container

#### 2.5 GitHub Secrets — Documentação Completa

Ver `GITHUB_SECRETS_SETUP.md` na raiz do projeto para lista completa de secrets,
permissões da service account, e instruções de setup do Artifact Registry.

---

### Fase 3 — GCP (time de infra)

> O Terraform já existe em `lia-agent-system/terraform/gcp/`. Use-o como base.

#### 3.1 Cloud SQL

```bash
# Criar instância
gcloud sql instances create lia-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-standard-2 \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=100GB

# Criar banco para o LIA Agent
gcloud sql databases create lia_db --instance=lia-postgres

# Criar banco para Rails (se migrar do servidor atual)
gcloud sql databases create ats_production --instance=lia-postgres

# Rodar migrations
# Rails:
RAILS_ENV=production DATABASE_URL=<cloud-sql-url> rails db:migrate
# FastAPI (Alembic):
DATABASE_URL=<cloud-sql-url> alembic upgrade head
```

#### 3.2 Secret Manager

```bash
# Criar todos os segredos
echo -n "sk-ant-..." | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
echo -n "AIza..."    | gcloud secrets create GEMINI_API_KEY    --data-file=-
echo -n "..."        | gcloud secrets create MS_APP_PASSWORD   --data-file=-
# ... demais segredos
```

#### 3.3 Cloud Run — Frontend

```bash
gcloud run deploy lia-frontend \
  --image gcr.io/<project>/lia-frontend:latest \
  --region us-central1 \
  --platform managed \
  --min-instances 1 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --port 3000 \
  --set-secrets MICROSOFT_APP_ID=MICROSOFT_APP_ID:latest \
  --set-env-vars BACKEND_URL=https://api.wedotalent.cc
```

#### 3.4 Cloud Run — AI Agent

```bash
gcloud run deploy lia-agent \
  --image gcr.io/<project>/lia-agent:latest \
  --region us-central1 \
  --platform managed \
  --min-instances 1 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 4 \
  --port 8001 \
  --set-secrets ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --set-secrets DATABASE_URL=DATABASE_URL:latest
```

#### 3.5 Load Balancer + Domínio

```bash
# Criar IP estático
gcloud compute addresses create lia-lb-ip --global

# Criar Cloud Armor policy (segurança)
gcloud compute security-policies create lia-security-policy \
  --description="LIA Platform WAF"

# Configurar domínio via DNS:
# wedotalent.cc       A    <IP estático>
# *.wedotalent.cc     A    <IP estático>
```

#### 3.6 Cloud Storage (uploads)

```bash
gcloud storage buckets create gs://lia-uploads-prod \
  --location=us-central1 \
  --uniform-bucket-level-access

# Lifecycle: mover CVs com +1 ano para Nearline
gcloud storage buckets update gs://lia-uploads-prod \
  --lifecycle-file=lifecycle-config.json
```

---

### Fase 4 — Staging (ambiente de testes)

O staging segue a **mesma infraestrutura**, com instâncias menores e banco separado:

```bash
# Cloud SQL staging
gcloud sql databases create lia_db_staging --instance=lia-postgres

# Cloud Run staging — frontend
gcloud run deploy lia-frontend-staging \
  --image gcr.io/<project>/lia-frontend:develop-latest \
  --region us-central1 \
  --min-instances 0 \   # pode escalar para zero (economiza custo)
  --max-instances 3 \
  --set-env-vars BACKEND_URL=https://api-staging.wedotalent.cc

# Cloud Run staging — agent
gcloud run deploy lia-agent-staging \
  --image gcr.io/<project>/lia-agent:develop-latest \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 2
```

**DNS para staging:**

```
staging.wedotalent.cc       → Cloud Run: lia-frontend-staging
api-staging.wedotalent.cc   → Cloud Run: lia-agent-staging
```

### Fase 5 — Feature Flags para Rollout Gradual

> Permite migrar domínios do FastAPI para o Rails de forma incremental, com rollback instantâneo sem redeploy, apenas alterando variáveis de ambiente.
>
> **⚠️ Pós-auditoria (abril 2026):** As 94 rotas com `backendTarget: "rails"` **funcionam normalmente sem Rails** — com `RAILS_BACKEND_URL` vazia, o proxy-handler.ts usa fallback automático para FastAPI. A migração domínio por domínio só é necessária **se e quando Rails for ativado** como opt-in (ver Seção 2F). Não é necessário fazer nada agora para o deploy funcionar.

**Padrão de variável por domínio:**

```bash
# Formato: <DOMINIO>_BACKEND=rails|fastapi
# "fastapi" é o default implícito — só precisa setar quando migrando para Rails
# Se RAILS_BACKEND_URL estiver vazia (situação atual), mesmo com _BACKEND=rails,
# o proxy cai no FastAPI automaticamente — zero impacto.

CANDIDATES_BACKEND=rails      # opcional — apenas se Rails estiver ativo
JOBS_BACKEND=rails            # opcional — apenas se Rails estiver ativo
INTERVIEWS_BACKEND=fastapi    # FastAPI já serve — não requer migração
NOTIFICATIONS_BACKEND=fastapi # FastAPI já serve — não requer migração
EMAIL_TEMPLATES_BACKEND=fastapi # FastAPI já serve — não requer migração
```

**Como funciona no proxy-handler.ts:**

O `proxy-handler.ts` já suporta a opção `backendTarget: "rails"` por rota. A feature flag por domínio é um controle em nível de ambiente — o valor da variável determina qual `backendTarget` usar para cada grupo de rotas. **Requisito de adoção:** as rotas de cada domínio precisam ser adaptadas para ler a variável de ambiente e passar o valor ao `createProxyHandlers` — o padrão abaixo deve ser adotado em cada arquivo de rota do domínio:

```typescript
// Exemplo de uso com flag de ambiente (padrão recomendado para rollout)
const candidatesBackend = process.env.CANDIDATES_BACKEND === "rails" ? "rails" : "fastapi"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/candidates",
  methods: ["GET", "POST"],
  backendTarget: candidatesBackend,
})
```

**Estado atual (snapshot abril 2026):** 442 rotas no total, 94 já apontando para `backendTarget: "rails"` com o valor fixo. Essas 94 rotas **funcionam com FastAPI** enquanto `RAILS_BACKEND_URL` estiver vazia. Este número deve ser recontado antes de cada marco de migração.

**Rollback rápido via nova revisão Cloud Run:**

Se Rails apresentar problemas em produção, reverter para FastAPI é feito em segundos — Cloud Run cria uma nova revisão com a variável atualizada (sem mudança de código, sem novo build de imagem):

```bash
# Cloud Run aplica a nova variável criando nova revisão rapidamente:
gcloud run services update lia-frontend \
  --update-env-vars CANDIDATES_BACKEND=fastapi \
  --region us-central1
# A nova revisão entra em serviço em ~15-30 segundos (sem redeploy de imagem)
```

**Ordem sugerida de migração por domínio (apenas se/quando Rails for ativado):**

| Domínio | Variável | Prioridade | Status |
|---|---|---|---|
| Candidatos | `CANDIDATES_BACKEND` | Alta | Opcional — FastAPI já serve |
| Vagas | `JOBS_BACKEND` | Alta | Opcional — FastAPI já serve |
| Aplicações | `APPLIES_BACKEND` | Alta | Opcional — FastAPI já serve |
| Entrevistas | `INTERVIEWS_BACKEND` | Média | Opcional — FastAPI já serve |
| Notificações | `NOTIFICATIONS_BACKEND` | Média | Opcional — FastAPI já serve |
| Email templates | `EMAIL_TEMPLATES_BACKEND` | Baixa | Opcional — FastAPI já serve |

---

## 7. Fluxo de Trabalho do Time

### 7.1 Rotina de desenvolvimento — nova feature ou melhoria

```
Dev (Replit ou VS Code/Cursor)
│
├── 1. Puxa a branch develop atualizada
│       git checkout develop && git pull
│
├── 2. Cria branch de feature
│       git checkout -b feature/nome-da-feature
│
├── 3. Desenvolve e testa localmente
│       npm run dev (frontend, porta 5000)
│       uvicorn app.main:app (backend, porta 8001)
│
├── 4. Commit + Push
│       git add . && git commit -m "feat: descrição"
│       git push origin feature/nome-da-feature
│
├── 5. Abre Pull Request → develop
│       GitHub PR: feature/* → develop
│       GitHub Actions roda testes automáticos
│       Code review do time
│
├── 6. Merge → staging automático
│       Aprovado e mergeado → deploy automático no staging
│       staging.wedotalent.cc recebe as mudanças
│
├── 7. QA no staging
│       Time executa checklist de QA para a feature
│       ├── Passou → PR: develop → main (aprovação manual)
│       └── Reprovou → dev abre fix na mesma branch ou nova fix/*
│               └── Volta para o passo 4 → re-teste no staging
│
└── 8. Deploy produção
        Merge para main → deploy automático produção
        wedotalent.cc recebe as mudanças
        Monitorar Sentry + logs nas primeiras horas
```

### 7.2 Fluxo de bug em produção — hotfix

Quando um bug crítico é encontrado em produção, o fluxo é diferente do fluxo padrão — bypassa o `develop` para chegar rápido à produção:

```
Bug identificado em produção
│
├── 1. Criar card no Jira com prioridade (P1/P2/P3)
│       P1 = produto fora do ar ou dado corrompido
│       P2 = funcionalidade crítica quebrada
│       P3 = problema menor, sem bloqueio
│
├── 2. Criar branch diretamente de main
│       git checkout main && git pull
│       git checkout -b hotfix/nome-do-bug
│
├── 3. Corrigir localmente e testar
│       Reproduzir o bug antes de corrigir
│       Confirmar que o fix resolve sem efeitos colaterais
│
├── 4. PR: hotfix/* → main  (revisão rápida, 1 aprovador)
│       GitHub Actions roda testes automáticos
│       Code review focado no fix (não no contexto geral)
│
├── 5. Deploy automático em produção
│       Merge para main → Cloud Run produção atualizado
│       Verificar no Sentry que o erro parou de aparecer
│
└── 6. Sincronizar com develop
        git checkout develop && git merge main
        Garante que a correção não será perdida na próxima feature
```

**Classificação de prioridade de bug:**

| Prioridade | Definição | Tempo alvo de resposta |
|---|---|---|
| **P1 — Crítico** | Sistema fora do ar, dados de clientes em risco, autenticação quebrada | Fix em produção em até 4h |
| **P2 — Alto** | Funcionalidade principal quebrada (triagem, kanban, chat) mas produto funciona | Fix em produção em até 24h |
| **P3 — Médio** | Problema visual, funcionalidade secundária ou edge case raro | Fix na próxima sprint |
| **P4 — Baixo** | Melhoria cosmética, mensagem de erro imprecisa | Backlog |

### 7.3 Processo de QA — o que é testado e como

O QA não é um passo único — é um processo por tipo de mudança:

**Para novas features:**

```
Checklist de QA por feature (quem faz: QA ou dev responsável)
│
├── Fluxo principal funciona conforme spec?
├── Casos de erro tratados? (campo vazio, API offline, usuário sem permissão)
├── Funciona em diferentes tamanhos de tela? (responsividade)
├── Multi-tenant: funciona isolado entre empresas diferentes?
├── Performance: não há regressão perceptível de velocidade?
├── Testes E2E automatizados passando? (Playwright em e2e/)
└── Sem warnings críticos no console do browser / Sentry?
```

**Para hotfixes:**

```
Checklist de QA de hotfix (mais rápido — foco no bug)
│
├── O bug original foi corrigido?
├── O fix não quebrou nada ao redor? (smoke test das funcionalidades adjacentes)
└── O Sentry para de registrar o erro após o deploy?
```

**Quem faz o QA:**
- Hoje: o próprio time de desenvolvimento (dev ou PM valida no staging)
- Roadmap: QA dedicado para releases maiores

**Onde bugs e ajustes são registrados:**
- Jira (cards de bug com prioridade, reprodução e critério de aceite do fix)
- PRs do GitHub linkados ao card Jira correspondente

### 7.4 Ciclo de feedback do cliente — bugs, sugestões e novas features

Clientes em uso do produto são uma fonte contínua de melhorias. Este fluxo descreve como esse feedback é capturado, triado e transformado em trabalho real.

**Canais de entrada de feedback:**

| Canal | Tipo de feedback | Quem recebe |
|---|---|---|
| **Email / WhatsApp direto** | Bugs críticos, dúvidas urgentes | CS / PM |
| **Formulário ou canal dedicado** | Sugestões, melhorias, relatos de comportamento inesperado | PM |
| **Slack compartilhado** (quando ativo) | Dúvidas rápidas, feedback informal | CS / PM |
| **Reunião de acompanhamento** | Feedback estruturado, roadmap, prioridades | PM |
| **Sentry / logs internos** | Bugs técnicos identificados antes do cliente (proativo) | Time de engenharia |

**Fluxo de triage — o que acontece com cada feedback:**

```
Feedback entra (qualquer canal)
         │
         ▼
PM ou CS registra no Jira com contexto:
  - O que o cliente reportou (comportamento observado)
  - O que era esperado acontecer
  - Frequência / impacto (quantos clientes afetados?)
  - Evidências (prints, vídeo, logs)
         │
         ▼
Triage de classificação:
  │
  ├── É um BUG?
  │       │
  │       ├── P1/P2 (crítico/alto) ──► Hotfix imediato (Fluxo 7.2)
  │       └── P3/P4 (médio/baixo) ──► Entra no backlog da próxima sprint
  │
  ├── É uma MELHORIA ou NOVA FEATURE?
  │       │
  │       ├── Alinhada com o roadmap → PM escreve spec → Ciclo 1 (feature)
  │       └── Fora do escopo atual → Documentada no Jira (backlog)
  │
  └── É uma DÚVIDA DE USO?
          └── CS resolve com documentação / suporte direto
              Se for recorrente → virar melhoria de UX ou documentação
```

**O que faz uma feature de cliente entrar no sprint:**

Não basta um cliente pedir — o PM avalia:
1. Quantos clientes teriam benefício (impacto)
2. Alinhamento com a direção do produto
3. Esforço de implementação vs. valor entregue
4. Urgência (está bloqueando o cliente de usar o produto?)

**Fechamento do loop com o cliente:**

Quando um bug reportado pelo cliente é corrigido, ou uma feature sugerida é entregue, o cliente deve ser notificado. Isso constrói confiança e mostra que o feedback foi levado a sério. Quem fecha esse loop: CS ou PM, após o deploy em produção.

### Como o Replit se encaixa após o deploy

```
┌─────────────────────────────────────────────────────────────────┐
│               Replit — Ambiente central do time                  │
│                                                                  │
│  DESENVOLVIMENTO (responsabilidade do time de engenharia)        │
│  ├── Ambiente padrão compartilhado pelo time                    │
│  ├── Alternativa: VS Code / Cursor apontando para GitHub        │
│  ├── Todos usam as mesmas branches, PRs e CI/CD                 │
│  └── Time é dono do fluxo: feature → develop → staging → prod  │
│                                                                  │
│  PROTÓTIPO E PRODUTO (você, PM)                                 │
│  ├── Contribui com features e novas telas no Replit             │
│  ├── Valida fluxos de UX antes de passar para o time            │
│  └── Participa do mesmo fluxo de PR sem ser responsável por ele │
│                                                                  │
│  DEBUGGING (qualquer membro do time)                            │
│  ├── Reproduzir bugs de produção localmente                     │
│  ├── Testar hotfixes antes de subir para staging                │
│  └── Explorar logs e traces em tempo real                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Variáveis de Ambiente

### Referência completa por serviço

#### Frontend — `plataforma-lia`

> Referência completa: `plataforma-lia/.env.example`

| Variável | Dev (Replit) | Staging | Produção | Notas |
|---|---|---|---|---|
| `BACKEND_URL` | `http://127.0.0.1:8001` | URL interna Cloud Run | URL interna Cloud Run | Usada pelo `next.config.js` nos rewrites e proxy routes — NÃO exposta ao browser |
| `RAILS_BACKEND_URL` | **vazio** (recomendado) | URL interna Cloud Run do Rails | URL interna Cloud Run do Rails | **Opcional** — Deixar vazio = FastAPI serve tudo. Usada por `proxy-handler.ts` para rotas `backendTarget: "rails"`. Preencher apenas se Rails for ativado como opt-in. Diferente de `RAILS_API_URL` (usada pelo FastAPI) |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:5000` | `https://staging.wedotalent.cc` | `https://wedotalent.cc` | |
| `NEXT_PUBLIC_WS_URL` | `ws://127.0.0.1:8001` | `wss://api-staging.wedotalent.cc` | `wss://api.wedotalent.cc` | WebSocket para chat real-time |
| `WORKOS_API_KEY` | Replit Secret | Secret Manager | Secret Manager | **Obrigatório** — auth SSO |
| `WORKOS_CLIENT_ID` | Replit Secret | Secret Manager | Secret Manager | **Obrigatório** — auth SSO |
| `WORKOS_REDIRECT_URI` | `http://localhost:5000/api/auth/workos/callback` | `https://staging.wedotalent.cc/api/auth/workos/callback` | `https://wedotalent.cc/api/auth/workos/callback` | Deve ser registrado no dashboard WorkOS |
| `WORKOS_SESSION_SECRET` | string aleatória | Secret Manager | Secret Manager | Mín. 32 caracteres |
| `WORKOS_WEBHOOK_SECRET` | Replit Secret | Secret Manager | Secret Manager | |
| `SECRET_KEY` | string aleatória | Secret Manager | Secret Manager | **Compartilhada com backend** — JWT signing |
| `INTERNAL_API_SECRET` | string aleatória | Secret Manager | Secret Manager | Token intra-serviço Next.js↔FastAPI |
| `SERVICE_API_TOKEN` | string aleatória | Secret Manager | Secret Manager | |
| `MICROSOFT_APP_ID` | `246eb1e7-...` | `246eb1e7-...` | `246eb1e7-...` | |
| `MICROSOFT_APP_PASSWORD` | Replit Secrets | Secret Manager | Secret Manager | |
| `AZURE_TENANT_ID` | `bd25f438-...` | `bd25f438-...` | `bd25f438-...` | |
| `NEXT_PUBLIC_SENTRY_DSN` | (opcional) | obrigatório | obrigatório | |

⚠️ **Alertas de segurança identificados na auditoria:**

| Alerta | Detalhe | Status |
|---|---|---|
| `DEV_AUTO_LOGIN_EMAIL/PASSWORD` | Credenciais de auto-login existem no código. Em dev, o middleware **não verifica JWT** — qualquer cookie `lia_access_token` é aceito. | ✅ Já protegido por `NODE_ENV !== 'production'` no middleware e rota 404 em prod |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | Chave Anthropic referenciada no frontend Next.js | ⚠️ Verificar que é server-side only (Server Components/Actions) — nunca deve chegar ao browser |
| Variáveis Replit (`REPLIT_DEV_DOMAIN`, `REPL_IDENTITY`) | Usadas em código do app — serão `undefined` no Cloud Run | ⚠️ Auditar e adicionar fallbacks antes do deploy |
| Variáveis `NEXT_PUBLIC_*` | Todas são injetadas no JS do browser e visíveis ao usuário | ✅ Nenhum secret detectado em vars `NEXT_PUBLIC_*` |

#### Backend — `lia-agent-system`

> Referência completa: `lia-agent-system/.env.example`

| Variável | Dev (Replit) | Staging | Produção | Notas |
|---|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db` | Cloud SQL staging | Cloud SQL prod | Driver asyncpg obrigatório |
| `ANTHROPIC_API_KEY` | via Replit integração | Secret Manager | Secret Manager | LLM primário (Claude) |
| `OPENAI_API_KEY` | (opcional) | Secret Manager (se ativo) | Secret Manager (se ativo) | Fallback LLM |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/path/to/service-account.json` | Workload Identity (Cloud Run) | Workload Identity (Cloud Run) | Google Speech/TTS/Gemini |
| `GOOGLE_CLOUD_PROJECT` | `seu-projeto-gcp` | `wedotalent-staging` | `wedotalent-prod` | |
| `REDIS_URL` | `redis://localhost:6379/0` | Cloud Memorystore staging | Cloud Memorystore prod | Cache, token budget, HITL, Celery results |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | CloudAMQP ou VM | CloudAMQP ou VM | Message broker Celery |
| `RAILS_API_URL` | **vazio** (recomendado) | URL interna Cloud Run do Rails | URL interna Cloud Run do Rails | **Opcional** — Deixar vazio = FastAPI serve tudo. Usado pelo FastAPI para chamar Rails (backend→backend). O `RailsAdapter` só tenta Rails se esta variável estiver preenchida. Diferente de `RAILS_BACKEND_URL` (usado pelo frontend) |
| `SECRET_KEY` | string aleatória | Secret Manager | Secret Manager | **Mesma do frontend** — JWT signing |
| `API_HOST` | `0.0.0.0` | `0.0.0.0` | `0.0.0.0` | |
| `API_PORT` | `8001` | `8001` | `8001` | |
| `MICROSOFT_APP_ID` | `246eb1e7-...` | `246eb1e7-...` | `246eb1e7-...` | |
| `MICROSOFT_APP_PASSWORD` | Replit Secrets | Secret Manager | Secret Manager | |
| `AZURE_TENANT_ID` | `bd25f438-...` | `bd25f438-...` | `bd25f438-...` | |
| `TWILIO_ACCOUNT_SID` | Replit Secret ✅ | Secret Manager | Secret Manager | **Configurado** — Voice screening |
| `TWILIO_AUTH_TOKEN` | Replit Secret ✅ | Secret Manager | Secret Manager | **Configurado** — Voice screening |
| `TWILIO_PHONE_NUMBER` | `+551150289337` ✅ | mesmo | mesmo | Voice outbound calls |
| `TWILIO_WHATSAPP_NUMBER` | ⚠️ pendente Meta | `whatsapp:+551150289337` | `whatsapp:+551150289337` | WhatsApp — aguardando aprovação Meta Business |
| `LANGCHAIN_API_KEY` | (opcional) | Secret Manager (se ativo) | Secret Manager (se ativo) | LangSmith tracing |
| `SENTRY_DSN` | (opcional) | obrigatório | obrigatório | |

---

## 9. Checklist Pré-Go-Live

### Código (Replit / time dev)

- [x] Dockerfile do `plataforma-lia` criado (`plataforma-lia/Dockerfile` — multi-stage, Node 22 Alpine, standalone)
- [x] `next.config.js` com `output: 'standalone'`, `BACKEND_URL` parametrizado nos rewrites
- [x] `.env.example` completo e documentado (todas as vars com descrição por seção)
- [x] `lia-agent-system` aponta para `DATABASE_URL` via variável de ambiente (`helium/heliumdb`)
- [x] Twilio credenciais configuradas (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN em Secrets; TWILIO_PHONE_NUMBER=+551150289337 em env var)
- [ ] GitHub Actions configurado nos dois repositórios
- [ ] Testes E2E passando no staging
- [x] Sentry configurado e recebendo eventos — org `talensesgroup-wedotalent` ativo, 4 issues rastreadas
- [ ] Bot Teams funcionando com Tenant ID correto (`bd25f438-...`)

### Infraestrutura (time infra)

- [ ] Cloud SQL provisionado e com backup automático configurado
- [ ] Migrations Alembic rodadas (`alembic upgrade head`) — **obrigatório**
- [ ] ~~Migrations Rails rodadas (`rails db:migrate`)~~ — **condicional, apenas se Rails for ativado como opt-in** (ver Seção 2F)
- [ ] Secret Manager populado com todas as variáveis
- [ ] Cloud Run (frontend + agent) deployado em staging
- [ ] Cloud Run (frontend + agent) deployado em produção
- [ ] Load Balancer configurado com SSL
- [ ] DNS apontando: `wedotalent.cc` + `staging.wedotalent.cc` + APIs
- [ ] Cloud Storage criado para uploads de arquivos
- [ ] Cloud Armor (WAF) ativo
- [ ] Alertas de Cloud Monitoring configurados (CPU, latência, erros 5xx)

### Validação funcional (time completo)

- [ ] Login / Autenticação funcionando em produção
- [ ] Criação e listagem de vagas
- [ ] Upload e parsing de CVs
- [ ] Chat com LIA (agente Claude)
- [ ] Bot do Teams respondendo
- [ ] Funil de candidatos (kanban)
- [ ] Geração de relatórios
- [ ] Envio de notificações

### 9.1 Scanning de Segurança no CI (SAST/SCA)

> O `Cloud Armor (WAF)` cobre proteção em runtime (Seção 6). Esta subseção cobre a camada de análise estática e de dependências — deve rodar no CI antes de qualquer deploy para staging ou produção.

**Análise estática de código (SAST):**

| Ferramenta | Alvo | Comando | O que detecta |
|---|---|---|---|
| **Bandit** | Python (FastAPI) | `bandit -r lia-agent-system/app/ -ll` | Injeções SQL, uso inseguro de `eval`, segredos hardcoded, criptografia fraca |
| **Brakeman** | Ruby (Rails) | `brakeman ats-api-copia/ --no-pager` | SQL injection, XSS, CSRF, exposição de massa de parâmetros |

**Análise de dependências (SCA):**

| Ferramenta | Alvo | Comando |
|---|---|---|
| **pip-audit** | Python | `pip-audit -r lia-agent-system/requirements.txt` |
| **bundle-audit** | Ruby/Gems | `bundle-audit check --update` (dentro de `ats-api-copia/`) |
| **npm audit** | Node.js | `npm audit --audit-level=high` (dentro de `plataforma-lia/`) |

**Teste de penetração pré-go-live:**

```bash
# OWASP ZAP contra o ambiente de staging
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.wedotalent.cc \
  -r zap_report.html
```

**Integração no GitHub Actions:**

```yaml
# Adicionar ao workflow de CI (roda em todo PR para develop e main)
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Bandit (Python SAST)
      run: pip install bandit && bandit -r lia-agent-system/app/ -ll
    - name: npm audit (Node SCA)
      working-directory: plataforma-lia
      run: npm audit --audit-level=high
```

**Critério de bloqueio:** Zero findings com severity HIGH ou CRITICAL antes do go-live. Findings de severity LOW/MEDIUM devem ser documentados com plano de remediação.

---

## 10. Troubleshooting

### Backend não sobe (ImportError)

Causa comum: função privada (`_calculate_confidence`) não exportada por `import *`.

```bash
# Verificar qual módulo está falhando
cd lia-agent-system
python3 -c "from app.main import app"

# Solução: exportar explicitamente a função privada no shim
# Editar app/shared/services/<service>.py e adicionar:
from app.domains.<domain>.services.<service> import _nome_da_funcao  # noqa: F401
```

### Bot Teams retorna 401

Verificar propagação do App Registration no Azure:
```
App ID: 246eb1e7-a437-4cb2-a231-0325b567be5f
Tenant: bd25f438-71ab-4f63-a88f-abc8da37a1f6
```
A propagação pode levar até 24h após mudança de Tenant ID. Não requer alteração de código.

### Cloud Run com cold start alto

Definir `--min-instances 1` para evitar que a instância escale para zero:
```bash
gcloud run services update lia-frontend \
  --min-instances 1 \
  --region us-central1
```

### Banco de dados — conexão recusada no Cloud Run

Cloud Run precisa do Cloud SQL Auth Proxy. Verificar:
```bash
gcloud run services update lia-agent \
  --add-cloudsql-instances <project>:us-central1:lia-postgres \
  --region us-central1
```

---

## 11. Mapa Completo de Integrações

> Análise extraída diretamente do código-fonte (`requirements.txt`, `package.json`, serviços e rotas). Cada integração tem status, função e o que é necessário para o deploy.

### 11.1 Modelos de Linguagem (LLMs)

| Integração | Status no código | Função | Chave necessária | GCP |
|---|---|---|---|---|
| **Claude (Anthropic)** | ✅ Core — em produção | Triagem de CVs, agente principal, análise de candidatos, WSI | `ANTHROPIC_API_KEY` | Secret Manager |
| **Gemini (Google AI)** | ✅ Core — em produção | Voz conversacional, chat LIA, busca semântica, insights | `GEMINI_API_KEY` | Secret Manager |
| **OpenAI** | ⚠️ Opcional | Fine-tuning export, busca por JD, triagem backup | `OPENAI_API_KEY` | Secret Manager (se ativo) |
| **LangSmith** | ⚠️ Opcional | Tracing de LLM calls, observabilidade de agentes | `LANGSMITH_API_KEY` | Secret Manager (se ativo) |

**LangGraph** (framework dos agentes) roda localmente — não é uma integração externa, é parte do código.

---

### 11.2 Voz e Transcrição (Google + Twilio)

```
Fluxo de triagem por voz:
Candidato → Twilio Voice (ligação) → Google Cloud Speech-to-Text (STT)
        → LIA Agent (Gemini / Claude análise) → resposta em áudio (TTS)
        → grava resultado no banco → notifica recrutador
```

| Integração | Arquivo principal | Função | Configuração GCP |
|---|---|---|---|
| **Google Cloud Speech-to-Text** | `app/api/v1/gemini_voice.py` | Transcrição das triagens por voz em tempo real | Habilitar API no projeto GCP |
| **Google Cloud Text-to-Speech** | `app/api/v1/voice.py` | LIA fala com o candidato durante triagem | Habilitar API no projeto GCP |
| **Twilio Voice** | `app/api/v1/twilio_voice.py` | Ligações reais (inbound/outbound), gravação | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | ✅ Credenciais configuradas (Replit Secrets + env var) |
| **Twilio WhatsApp** | `app/domains/communication/services/whatsapp_twilio_service.py` | WhatsApp via Twilio (alternativa ao Meta API) | mesmas credenciais Twilio + `TWILIO_WHATSAPP_NUMBER` | ⚠️ WhatsApp pendente aprovação Meta Business Suite |

> **Status Twilio (abril 2026):**
> - ✅ `TWILIO_ACCOUNT_SID` — configurado como Replit Secret
> - ✅ `TWILIO_AUTH_TOKEN` — configurado como Replit Secret
> - ✅ `TWILIO_PHONE_NUMBER` — `+551150289337` configurado como env var
> - ⚠️ **WhatsApp Business:** Pendente aprovação do número no Meta Business Suite. Uma conta duplicada foi deletada; aguardando liberação da conta principal. Voice calls funcionam; WhatsApp aguardando.
>
> **Ação GCP:** Habilitar as APIs `speech.googleapis.com` e `texttospeech.googleapis.com` no projeto GCP. A autenticação usa o Service Account do Cloud Run — sem API key adicional. Mover `TWILIO_*` para Secret Manager.

---

### 11.3 Comunicação e Notificações

| Canal | Integração | Arquivo principal | Status | Configuração |
|---|---|---|---|---|
| **Email transacional** | Resend | `app/api/v1/email.py` | ✅ Ativo | `RESEND_API_KEY` |
| **WhatsApp (Meta)** | WhatsApp Business API | `app/domains/communication/services/whatsapp_meta_service.py` | ⚠️ Config pendente | `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` |
| **Microsoft Teams** | Bot Framework + Graph API | `app/domains/communication/services/teams_service.py` | ✅ Ativo (dev mode) | `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `AZURE_TENANT_ID` |
| **Teams SSO** | MSAL + Microsoft Graph | `app/domains/communication/services/teams_sso_service.py` | ✅ Ativo | mesmas credenciais MS |
| **Teams Recordings** | Microsoft Graph | `app/domains/communication/services/teams_recording_service.py` | ✅ Ativo | `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |

---

### 11.4 Agendamento e Calendário

| Integração | Arquivo | Função | Configuração |
|---|---|---|---|
| **Google Calendar** | `app/domains/interview_scheduling/services/calendar_service.py` | Criar/gerenciar entrevistas no Google Calendar | `GOOGLE_CALENDAR_CREDENTIALS` (service account JSON) |
| **Microsoft Calendar** | `app/domains/integrations_hub/services/microsoft_graph_service.py` | Agendamento via Outlook / Teams | mesmas credenciais Microsoft Graph |
| **APScheduler** | `app/jobs/scheduled_reports.py` | Jobs internos (relatórios agendados, alertas proativos) | sem config externa |
| **Celery** | `app/core/celery_app.py` | Tasks assíncronas longas (triagem em batch, exportações) | `CELERY_BROKER_URL` (RabbitMQ) |

---

### 11.5 Infraestrutura de Filas e Cache

```
Arquitetura de filas da LIA:
                                    ┌─────────────┐
FastAPI request ──► Celery task ──► │  RabbitMQ   │ ──► Celery worker processa
                                    └─────────────┘
                                          │
                              ┌───────────▼──────────┐
                              │         Redis         │
                              │  - Cache de sessões   │
                              │  - Token budgets      │
                              │  - HITL TTL store     │
                              │  - Celery result back │
                              └───────────────────────┘
```

| Serviço | Uso no código | Deploy no GCP |
|---|---|---|
| **Redis** | Cache, token budget, HITL store, Celery results | Cloud Memorystore (Redis) |
| **RabbitMQ (aio-pika)** | Message broker para Celery, jd_search, agent_chat_ws | Cloud Run sidecar ou VM dedicada |
| **Celery** | Workers assíncronos para triagem em batch, drift detection | Cloud Run (worker) separado |

> **Nota:** RabbitMQ é o único serviço que não tem managed service direto no GCP. Opções: (1) VM e2-small dedicada, (2) substituir por Cloud Pub/Sub (maior esforço de migração), (3) CloudAMQP (serviço gerenciado externo).

---

### 11.6 CRM e Sourcing Externo

| Integração | Arquivo | Função | Status | Config |
|---|---|---|---|---|
| **HubSpot** | `app/domains/company/services/hubspot_service.py` | Sync de empresas e contatos com CRM | ⚠️ Config pendente | `HUBSPOT_ACCESS_TOKEN` |
| **PEARCH** | `app/domains/sourcing/services/pearch_service.py` | Busca externa de candidatos (banco proprietário) | ⚠️ Config pendente | `PEARCH_API_KEY` |
| **GitHub** | `app/domains/sourcing/services/github_service.py` | Sourcing de devs via GitHub API | ✅ Ativo | `GITHUB_TOKEN` (injetado pelo Replit) |

---

### 11.7 Autenticação e Multi-tenant (WorkOS)

```
Fluxo de autenticação na LIA:

Usuário acessa wedotalent.cc
         │
         ▼
┌─────────────────────────┐
│   WorkOS SSO            │  ← Gerencia organizações (multi-tenant)
│   - Google SSO          │     Cada empresa = 1 organização WorkOS
│   - Microsoft SSO       │     session cookie: workos_session
│   - SAML Enterprise     │
└──────────┬──────────────┘
           │ workosProfile.organizationId
           ▼
┌─────────────────────────┐
│   Next.js Backend Proxy │  ← /api/backend-proxy/* lê workos_session
│   getWorkOSSession()    │     injeta organizationId em todas as requests
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   FastAPI / Rails API   │  ← filtra dados pelo organizationId (tenant)
└─────────────────────────┘
```

| Componente | Arquivo | Notas |
|---|---|---|
| **WorkOS SDK** | `plataforma-lia/src/lib/workos-session.ts` | Gerencia sessão multi-tenant |
| **Organização** | todos os `/api/backend-proxy/*.ts` | injeta `organizationId` nas chamadas |
| **SSO Providers** | WorkOS dashboard | Google, Microsoft, SAML configurados por empresa |

> **Para o deploy:** Configurar `WORKOS_API_KEY` e `WORKOS_CLIENT_ID` no Secret Manager. Registrar o domínio `wedotalent.cc` como redirect URI no WorkOS dashboard.

---

### 11.8 Observabilidade

| Ferramenta | Camada | Arquivo | Config | Status |
|---|---|---|---|---|
| **Sentry** | Frontend + Backend | `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`, `app/core/sentry.py` | `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN` | ✅ **ATIVO** — org `talensesgroup-wedotalent`, capturando eventos (4 issues rastreadas). PII scrubbing ativo (CPF, email, telefone). Frontend: client + server + edge configs. Backend: FastAPI + Starlette integrations com `send_default_pii=False` |
| **LangSmith** | Agentes LLM | `app/config/langsmith.py` | `LANGSMITH_API_KEY` | ✅ **ATIVO** — projeto `lia-agent-system`, 301+ traces capturados. Rastreia grafos LangGraph (orchestrator, wizard, screening, interview, job wizard). Error rate 67% em dev (LLM unavailable, serialização) — esperado em ambiente de desenvolvimento |
| **Cloud Logging** | Backend | automático no Cloud Run | sem config adicional | ⏳ Automático ao fazer deploy no GCP Cloud Run — stdout/stderr roteado automaticamente. Sem integração custom no código |
| **APM Cloud Monitoring** | GCP | via dashboards GCP | alertas configurados manualmente | ⏳ Configuração manual no GCP pós-deploy — sem código necessário na aplicação |

---

### 11.9 Plano de Ação para Integrações — O que falta plugar

| Prioridade | Integração | Status atual | Ação necessária |
|---|---|---|---|
| 🔴 Crítico | WorkOS | Código pronto, sem credenciais prod | Criar conta WorkOS Prod, configurar domínio, adicionar secrets |
| 🔴 Crítico | Claude (Anthropic) | Funciona no Replit | Mover chave para Secret Manager GCP |
| 🔴 Crítico | Gemini (Google AI) | Funciona no Replit | Habilitar Vertex AI no projeto GCP + Secret Manager |
| 🔴 Crítico | PostgreSQL (Cloud SQL) | Banco local no Replit | Provisionar Cloud SQL, rodar migrations |
| 🔴 Crítico | Redis (Memorystore) | redis local no Replit | Provisionar Cloud Memorystore |
| 🟡 Importante | Google Voice/STT | Código pronto | Habilitar APIs `speech.googleapis.com`, `texttospeech.googleapis.com` |
| ✅ Parcial | Twilio Voice | ✅ Credenciais configuradas (Replit Secrets + env var `+551150289337`) | Mover `TWILIO_*` para Secret Manager GCP |
| ⚠️ Pendente | Twilio WhatsApp | Credenciais Twilio ok; número WhatsApp pendente aprovação Meta Business Suite | Completar registro Meta → adicionar `TWILIO_WHATSAPP_NUMBER` |
| 🟡 Importante | Microsoft Teams Bot | Funciona (dev mode) | Registrar webhook URL de produção no Azure Bot Service |
| 🟡 Importante | Resend (email) | Código pronto | `RESEND_API_KEY` no Secret Manager |
| 🟡 Importante | RabbitMQ | Código pronto | Provisionar CloudAMQP ou VM e2-small |
| ✅ Ativo | Sentry | **Integrado e ativo** — org `talensesgroup-wedotalent` | DSNs já configurados, eventos sendo capturados |
| 🟢 Desejável | HubSpot | Código pronto, config pendente | `HUBSPOT_ACCESS_TOKEN` quando necessário |
| 🟢 Desejável | PEARCH | Código pronto, config pendente | `PEARCH_API_KEY` (contato com PEARCH) |
| ✅ Ativo | LangSmith | **Integrado e ativo** — projeto `lia-agent-system`, 301+ traces | API key configurada, rastreando todos os grafos LangGraph |
| 🟢 Desejável | OpenAI | Fallback implementado | `OPENAI_API_KEY` se quiser usar GPT como fallback |

---

## 12. Avaliação — Frontend (Next.js / React / Tailwind)

> Status atual do `plataforma-lia/` para production readiness.

### O que está sólido

| Área | Situação |
|---|---|
| **Arquitetura** | Next.js 15 App Router, Server Components, Server Actions — padrão moderno |
| **Design System** | Tailwind + shadcn/ui, componentes padronizados com variantes CVA |
| **Tipagem** | TypeScript strict mode ativo, tipos bem definidos |
| **Auth** | WorkOS SSO integrado, `workos_session` cookie, middleware de proteção de rotas |
| **Proxy de API** | `/api/backend-proxy/*` centraliza todas as chamadas ao backend (boa separação) |
| **Observabilidade** | Sentry ativo (org `talensesgroup-wedotalent`) + LangSmith ativo (301+ traces) |
| **Teams** | `@microsoft/teams-js` integrado, rotas de tab e auth criadas |
| **WebSockets** | Chat em tempo real via WS implementado |
| **Testes E2E** | Pasta `e2e/` com 20 arquivos Playwright — auth fixture via cookie bypass (dev mode) |

#### Resultados E2E (07/04/2026 — Replit, Chromium do sistema via Nix)

| Grupo | Passaram | Falharam | Notas |
|---|---|---|---|
| **Auth** (login.spec.ts) | 6/6 | 0 | Testa UI da página de login |
| **Kanban** (move-candidate.spec.ts) | 6/7 | 1 | Falha: `data-testid="kanban-column"` não existe na página |
| **Wizard steps 1-3** | 12/13 | 1 | Falha: texto esperado diferente do renderizado |
| **Wizard steps 4-7** | — | — | Timeout no Replit (45s/teste × muitos testes) |
| **Chat** (9 arquivos) | — | — | Pesados demais para Replit (precisam CI dedicado) |

**Pendência**: Rodar suíte completa com credenciais WorkOS reais em CI (GitHub Actions) para validação de produção.

### O que foi corrigido nesta auditoria (07/04/2026)

| Item | O que era | O que foi feito |
|---|---|---|
| `next.config.js` | `distDir: 'out'`, `trailingSlash: true`, rewrites com `127.0.0.1:8001` hardcoded | Removidos. Adicionado `output: 'standalone'`. Rewrites parametrizados via `BACKEND_URL` env var (fallback: `http://127.0.0.1:8001`) |
| `Dockerfile` | Não existia | Criado: multi-stage build, Node 22 Alpine, `output: standalone` |
| `.env.example` | Só 2 vars, porta errada (8000) | Reescrito com ~20 vars documentadas por seção (WorkOS, segurança, Sentry, dev flags) |
| `.env.example` backend | Faltava `RAILS_API_URL`, `API_PORT` errado | Adicionado `RAILS_API_URL`, corrigido `API_PORT` para 8001 |
| Testes E2E | Nunca rodados, auth incompatível | Chromium instalado via Nix, auth fixture adaptado para cookie bypass, resultados acima |
| `.dockerignore` | Não existia | Criado (exclui node_modules, .next, e2e, .env*) |

### 12.1 Diagnóstico Profundo (07/04/2026)

> Auditoria de código analisando: rotas, proxy backend, integrações IA, banco de dados, auth, WebSockets, e build de produção.

#### Mapa de páginas e rotas (✅ saudável)

| Rota | Página | Componente principal |
|---|---|---|
| `/` | Dashboard | `DashboardApp` + `OnboardingController` |
| `/login` | Login | `LoginClient` (WorkOS SSO) |
| `/login/welcome` | Onboarding | Apresentação animada do fluxo LIA |
| `/funil` | Pipeline Kanban | `DashboardApp` (visão default) |
| `/funil-de-talentos` | Talent Funnel | `FunilDeTalentosClient` (busca + gestão candidatos) |
| `/funil-de-talentos/candidato/[id]` | Perfil do candidato | `CandidatoDetailClient` |
| `/jobs` | Lista de vagas | `JobsPage` |
| `/jobs/[id]` | Detalhe da vaga | `JobDetailClient` |
| `/chat` | Chat com LIA | `ChatPage` (interface do agente IA) |
| `/tasks` | Tarefas | `DashboardApp` com `initialPage="Tarefas"` |
| `/configuracoes` | Configurações | `DashboardApp` com `initialPage="Configurações"` |
| `/configuracoes/ai-credits` | Créditos de IA | `AiCreditsPage` (gráficos recharts) |
| `/vagas/[slug]` | Página pública da vaga | Landing page para candidatos |
| `/shared/[token]` | Busca compartilhada | Link público para lista curada de candidatos |
| `/triagem/[token]` | Triagem IA | Interface de conversa candidato ↔ LIA |
| `/portal/data-request/[token]` | Portal de dados do candidato | Submissão segura de dados pessoais |
| `/privacidade` | Portal de privacidade | LGPD compliance, DSR |
| `/ajuda` | Centro de ajuda | Explicação da análise IA, Big Five, arquétipos |
| `/register` | Cadastro | `RegisterClient` |
| `/forgot-password`, `/reset-password` | Recuperação de senha | Fluxo completo |
| `/upgrade` | Upgrade de plano | Billing |
| `/design-system` | Referência visual | Tokens de cor, tipografia, sombras |
| `/teams-tab` | Microsoft Teams | Redirect para `/vagas` |

**Resultado:** Todas as rotas apontam para componentes válidos. Nenhum import quebrado encontrado.

#### P1 — ✅ RESOLVIDO (Task #99 — abril 2026): proxy routes 100% padronizados

```
CORREÇÃO APLICADA:
  Todos os 104 arquivos de proxy routes + os 11 arquivos frontend que usavam
  NEXT_PUBLIC_BACKEND_URL/NEXT_PUBLIC_API_URL foram migrados.

  Resultado: ZERO referências a NEXT_PUBLIC_BACKEND_URL ou NEXT_PUBLIC_API_URL
  no codebase. Todas as chamadas ao backend passam por proxy routes ou usam
  BACKEND_URL (server-side only).

  Arquivos migrados na Task #99:
  - smart-search-input.tsx, useKanbanJobEditing.ts, use-pipeline-inheritance.ts
  - use-return-events.ts, use-proactive-alerts.ts, use-candidate-data-requests.ts
  - candidate-search.ts, global-search-settings.ts, useCandidatePageCore.tsx
  - useCandidateFiles.tsx, smartSearchConstants.ts
```

#### P2 — ✅ RESOLVIDO (07/04/2026): `next build` — página de Créditos de IA

```
CORREÇÃO APLICADA:
  - Adicionado "use client" ao src/app/configuracoes/ai-credits/page.tsx
  - metadata permanece em layout.tsx (já existente)
  - Build compila sem este erro
```

#### P3 — ✅ RESOLVIDO (07/04/2026): Backend conectado ao banco real

```
CORREÇÃO APLICADA:
  - DATABASE_URL corrigido para postgresql+asyncpg://postgres:password@helium/heliumdb
  - API_PORT corrigido para 8001
  - Backend inicia e conecta ao banco real (~60 tabelas Alembic)

BUGS DE STARTUP ADICIONAIS CORRIGIDOS:
  - core_search.py: adicionado import de CreditService/get_credit_service
  - email_tracking.py: adicionado import de ABTestingService/get_ab_testing_service
  - notification_service.py: adicionado extend_existing=True nas tabelas
    Notification e ChatNotification (conflito SQLAlchemy de registros duplicados)

AÇÃO NO DEPLOY (GCP):
  Provisionar Cloud SQL PostgreSQL 16. O Python terá seu próprio banco
  (lia_db) e acessará dados do Rails via API REST (RAILS_API_URL).
```

#### P4 — ✅ RESOLVIDO (Task #99 — abril 2026): `NEXT_PUBLIC_BACKEND_URL` eliminado

```
CORREÇÃO APLICADA:
  Todos os arquivos (proxy routes + 11 arquivos frontend) migrados.
  ZERO referências a NEXT_PUBLIC_BACKEND_URL ou NEXT_PUBLIC_API_URL no codebase.
  Resolvido junto com P1 na Task #99.
```

#### P5 — ⚠️ PARCIALMENTE RESOLVIDO: Variáveis exclusivas do Replit no código

```
4 ARQUIVOS DE APP com vars Replit-only (bloqueiam deploy):

  Frontend (2):
  1. plataforma-lia/src/lib/workos.ts — REPLIT_DEV_DOMAIN (redirect URI do WorkOS)
  2. plataforma-lia/src/lib/api/jira-service.ts — REPL_IDENTITY / WEB_REPL_RENEWAL (auth Jira via Replit connector)

  Backend (2):
  3. lia-agent-system/app/api/v1/shared_searches.py — REPLIT_DEV_DOMAIN (base URL para links)
  4. lia-agent-system/app/shared/channels/adapters/email_adapter.py — REPLIT_DEV_DOMAIN (links em emails)

  Scripts dev-only (~20 arquivos em scripts/ e lia-agent-system/scripts/):
  - Usam REPL_IDENTITY / WEB_REPL_RENEWAL para auth Jira via Replit connector
  - NÃO são deployados — sem risco para produção

AÇÃO ANTES DO DEPLOY:
  Frontend: Adicionar fallbacks:
    process.env.REPLIT_DEV_DOMAIN || process.env.APP_DOMAIN || 'wedotalent.cc'
  Backend: Adicionar fallbacks:
    os.environ.get("REPLIT_DEV_DOMAIN", os.environ.get("APP_DOMAIN", "wedotalent.cc"))
  Jira: Migrar auth para JIRA_ACCESS_TOKEN + JIRA_SITE_URL (Cloud Run)
  Trabalho estimado: ~30 minutos.
```

#### P6 — ✅ RESOLVIDO (Task #74 — abril 2026): WebSockets parametrizados

```
CORREÇÃO APLICADA:
  NEXT_PUBLIC_WS_URL é usada em 3 componentes:
  1. AsyncJobProgress.tsx — progresso de tarefas assíncronas
  2. VoIPCallButton.tsx  — chamadas VoIP em tempo real
  3. use-agent-streaming.ts — streaming de agentes

  Valor dev (Replit): ws://127.0.0.1:8001
  Valor prod: wss://api.wedotalent.cc

AÇÃO NO DEPLOY:
  - Configurar NEXT_PUBLIC_WS_URL=wss://api.wedotalent.cc em produção
  - Habilitar WebSocket no Cloud Run (timeout 3600s)
```

#### Autenticação (✅ totalmente implementada — não é stub)

```
A autenticação foi auditada e está completamente wired:

  WorkOS SSO:
    /api/auth/workos/sso     → redireciona para WorkOS
    /api/auth/workos/callback → recebe token, cria sessão, sincroniza com backend

  JWT tradicional:
    /api/auth/auto-login     → login dev automático (demo@wedotalent.com)
    /api/v1/auth/login       → login real no backend
    /api/v1/auth/refresh     → refresh de token

  Middleware:
    middleware.ts verifica workos_session OU lia_access_token em TODA request
    Paths públicos corretamente excluídos (/login, /vagas/*, /triagem/*, etc.)

  Sessão:
    Cookies HTTP-only (lia_access_token, workos_session)
    Assinatura HMAC via session-crypto.ts
    Auto-login dev chama o backend real (não é fake)

  Backend:
    app/api/v1/auth.py — login, refresh, verificação JWT
    app/api/v1/workos.py — sync de usuário WorkOS
    Audit logs implementados para tentativas de login
```

#### Integrações IA (✅ server-side only — seguras)

```
Auditoria de chaves API:

  AI_INTEGRATIONS_ANTHROPIC_API_KEY:
    ✅ CONFIRMADO SERVER-SIDE ONLY
    Usado em: src/app/api/ai/extract-archetype-info/route.ts (API Route)
              src/app/api/ai/suggest-companies/route.ts (API Route)
              src/app/api/ai/suggest-expertise/route.ts (API Route)
    Todas são API Routes (server-side). Nenhuma usa NEXT_PUBLIC_.
    A chave NUNCA chega ao browser.

  Providers configurados:
    - Anthropic (Claude): core — triagem, análise, sugestões
    - Google (Gemini): core — chat, voz, busca semântica
    - OpenAI (GPT): fallback terciário

  Frontend apenas exibe status das integrações via IntegrationsHub.tsx
  (sem chaves, apenas nomes e status on/off).
```

### O que precisa de atenção antes do deploy

| Área | Severidade | Status | Ação | Quando |
|---|---|---|---|---|
| **P1: NEXT_PUBLIC leak no frontend** | ~~🟡 Importante~~ | ✅ RESOLVIDO (Task #99) | Zero referências a `NEXT_PUBLIC_BACKEND_URL`/`NEXT_PUBLIC_API_URL` | Feito |
| **P2: Build falha** | ~~🔴 Crítico~~ | ✅ RESOLVIDO | `"use client"` adicionado ao `ai-credits/page.tsx` | Feito |
| **P3: DATABASE_URL** | ~~🔴 Crítico~~ | ✅ RESOLVIDO | Backend conectado ao banco Replit (`helium/heliumdb`) | Feito |
| **P4: NEXT_PUBLIC leak** | ~~🟡 Importante~~ | ✅ RESOLVIDO (Task #99) | Resolvido junto com P1 | Feito |
| **P5: Replit vars** | 🟡 Importante | ⚠️ 4 arquivos de app restantes (2 frontend + 2 backend) | Adicionar fallbacks — ver lista detalhada abaixo | Antes do deploy |
| **P6: WebSockets** | ~~🟡 Importante~~ | ✅ RESOLVIDO (Task #74) | `NEXT_PUBLIC_WS_URL` parametrizado em 3 componentes | Feito |
| **WorkOS prod** | 🟡 Importante | Pendente | Criar ambiente prod + redirect URIs `wedotalent.cc` | Deploy |
| **Error Boundaries** | 🟢 Desejável | Parcialmente implementado | Verificar cobertura em pages críticas | Antes do deploy |
| **Headers de segurança** | 🟢 Desejável | Pendente | CSP, X-Frame-Options em `next.config.js` | Antes do deploy |
| **Bundle size** | 🟢 Desejável | Não auditado | Rodar `next build` e checar | Antes do deploy |
| **Testes E2E WorkOS real** | 🟢 Desejável | Pendente | Rodar com credenciais reais em CI | Deploy |

### Checklist de production readiness — Frontend

**Correções críticas (bloqueiam deploy):**
- [x] P1: Todos os 104+ proxy route files padronizados para `BACKEND_URL` + porta `8001` — zero `NEXT_PUBLIC_BACKEND_URL` (Task #99)
- [x] P2: `next build` passa sem erros (`ai-credits/page.tsx` corrigido — `"use client"` adicionado)
- [x] P3: `DATABASE_URL` do backend corrigido para banco real (`helium/heliumdb`)

**Preparação para deploy:**
- [x] P4+P1: Zero variáveis `NEXT_PUBLIC_*` expondo URLs internas do backend (Task #99)
- [ ] P5: 4 arquivos de app com vars Replit-only precisam de fallback para deploy:
  - `plataforma-lia/src/lib/workos.ts` — usa `REPLIT_DEV_DOMAIN` (redirect URI)
  - `plataforma-lia/src/lib/api/jira-service.ts` — usa `REPL_IDENTITY` / `WEB_REPL_RENEWAL` (auth Jira via Replit connector)
  - `lia-agent-system/app/api/v1/shared_searches.py` — usa `REPLIT_DEV_DOMAIN` (base URL links)
  - `lia-agent-system/app/shared/channels/adapters/email_adapter.py` — usa `REPLIT_DEV_DOMAIN` (email links)
  - Nota: ~20 scripts em `scripts/` e `lia-agent-system/scripts/` também usam `REPL_IDENTITY`/`WEB_REPL_RENEWAL` mas são dev-only (não deployados)
- [x] P6: WebSocket URLs parametrizadas com `NEXT_PUBLIC_WS_URL` (Task #74)
- [ ] Headers de segurança adicionados no `next.config.js`
- [ ] Error boundary verificado em pages críticas (funil, chat, vagas)

**Configuração de produção (infra + produto):**
- [ ] `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` de produção configurados
- [ ] Redirect URIs do WorkOS registrados para `wedotalent.cc`
- [x] Sentry DSN configurado — org `talensesgroup-wedotalent` ativo, capturando eventos
- [ ] Testes E2E completos com WorkOS real em CI
- [ ] Teams Tab URL atualizada para domínio de produção

**Já feito:**
- [x] `Dockerfile` com `output: standalone` criado (`plataforma-lia/Dockerfile`)
- [x] `next.config.js` corrigido (standalone, BACKEND_URL parametrizado, distDir/trailingSlash removidos)
- [x] `.env.example` completo com todas as variáveis documentadas
- [x] `.dockerignore` criado
- [x] Testes E2E rodando no Replit (Chromium via Nix + auth fixture adaptado)
- [x] Integrações IA confirmadas como server-side only (Anthropic, Gemini, OpenAI)
- [x] Autenticação WorkOS SSO + JWT totalmente implementada (não é stub)

---

## 13. Avaliação — Camada de IA (Python / FastAPI / LangGraph)

> Status atual do `lia-agent-system/` para production readiness.
> Última auditoria: Abril 2026.

### 13.1 Arquitetura de Agentes

```
Requisição do usuário
        │
        ▼
┌───────────────────────┐
│  FastAPI Router       │  ← 362+ endpoints (REST + WebSocket)
│  (Port 8001)          │     organizados em 58 domínios
└────────┬──────────────┘
         │
    ┌────┴─────────────────────────────────────────────┐
    │                                                   │
    ▼                                                   ▼
┌──────────────────────┐                ┌──────────────────────┐
│  Fast Router         │                │  Orchestrator        │
│  (navigation_intent) │                │  (Multi-Agent ReAct) │
│  keyword-based,      │                │  LLM-based intent    │
│  sem LLM (rápido)    │                │  classification      │
│  → mapeia p/ páginas │                │  → delega p/ agentes │
└──────────────────────┘                └────────┬─────────────┘
                                                 │
                        ┌────────────────────────┼──────────────────────┐
                        │                        │                      │
                        ▼                        ▼                      ▼
               ┌─────────────────┐    ┌──────────────────┐   ┌─────────────────┐
               │  7 Core Agents  │    │  LangGraph Flows │   │  Specialized    │
               │  (ReAct)        │    │  (StateGraph)    │   │  Agents         │
               │                 │    │                  │   │                 │
               │  • Wizard       │    │  • WSI Interview │   │  • Diversity    │
               │  • Pipeline     │    │  • Job Wizard    │   │  • GitHub       │
               │  • Sourcing     │    │  • Interview     │   │  • StackOverflow│
               │  • Talent       │    │    Scheduling    │   │  • Nurture      │
               │  • JobsMgmt     │    │                  │   │  • Action       │
               │  • Kanban       │    │                  │   │  • Decision     │
               │  • Policy       │    │                  │   │  • Context      │
               └────────┬────────┘    └────────┬─────────┘   └────────┬────────┘
                        │                      │                      │
                        └──────────────────────┼──────────────────────┘
                                               │
                                               ▼
                              ┌────────────────────────────────┐
                              │  Tool Registry (60+ tools)     │
                              │  Organizado por categoria:     │
                              │  Job Wizard (9), Candidates (9)│
                              │  Query/Analytics (8), Talent   │
                              │  Pool (5), Agent Studio (4),   │
                              │  Digital Twins (3), Campaigns  │
                              │  (3), Communication (2), etc.  │
                              └────────────────────────────────┘
                                               │
                                               ▼
                              ┌────────────────────────────────┐
                              │  PostgreSQL (217 models)       │
                              │  + pgvector (768-dim, HNSW)    │
                              │  Redis (cache + rate limit)    │
                              │  Celery (36 tasks, 4 queues)   │
                              └────────────────────────────────┘
```

### 13.2 Domínios (56)

| Categoria | Domínios |
|-----------|----------|
| **Core Recrutamento** | `candidates`, `cv_screening`, `sourcing`, `triagem`, `talent_pool`, `pipeline`, `recruitment`, `recruitment_campaign`, `recruitment_journey` |
| **Vagas** | `job_management`, `job_vacancies_analytics`, `hiring_policy` |
| **Entrevistas & Voz** | `interview_scheduling`, `voice` |
| **Comunicação** | `communication`, `email_templates`, `notifications` |
| **Analytics & IA** | `analytics`, `ai`, `agent_memory`, `agent_studio`, `digital_twin`, `opinions`, `goals` |
| **Compliance & Segurança** | `compliance`, `consent`, `data_subject`, `lgpd`, `policy`, `trust_center` |
| **Administração** | `admin`, `admin_settings`, `auth`, `billing`, `credits`, `company`, `company_culture`, `clients`, `client_users` |
| **Automação** | `automation`, `autonomous`, `bulk_actions`, `tasks`, `approvals` |
| **Integrações** | `ats_integration`, `integrations_hub`, `shared_searches`, `technical_tests` |
| **Observabilidade** | `observability`, `health_check`, `saas_metrics` |
| **Outros** | `chat`, `journey_mapping`, `recruiter_assistant`, `workforce` |

**LangGraph ativo em:** `cv_screening` (WSI Interview Graph), `job_management` (Job Wizard Graph), `interview_scheduling` (Interview Graph).

### 13.3 LLM Provider Layer

#### Factory Multi-Provider

```
┌─────────────────────────────────────────────────────────────┐
│  LLMProviderFactory + ProviderContainer                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Gemini  │  │  Claude  │  │  OpenAI  │                 │
│  │ (primary)│→ │(fallback)│→ │(fallback)│                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  Fallback automático: se primary falha (CircuitBreaker),   │
│  tenta o próximo na sequência configurada por tenant.       │
│                                                             │
│  TenantProviderRegistry: tenant_id → ProviderContainer     │
│  Fonte de config: tool_permissions.yaml                     │
│  Budget tracking: tenant_budget.py (Redis, mensal)          │
└─────────────────────────────────────────────────────────────┘
```

| Componente | Arquivo | Status |
|-----------|---------|--------|
| LLM Factory | `app/shared/providers/llm_factory.py` | Implementado — Gemini, Claude, OpenAI com fallback |
| Embedding Factory | `app/shared/providers/embedding_factory.py` | Implementado — Gemini (`text-embedding-004`) e OpenAI (`text-embedding-3-small`), 768-dim, fallback |
| Voice Provider ABC | `app/shared/providers/voice_provider.py` | ABC existe mas não universalmente enforced |
| Tenant Config | `app/tools/tool_permissions.yaml` + `tenant_llm_context.py` | Implementado — provider e fallback por tenant |
| Tenant Budget | `app/orchestrator/tenant_budget.py` | Implementado — tracking mensal de tokens em Redis |
| LLM Bootstrap | `app/shared/llm_bootstrap.py` | Safety net — monkey-patches imports diretos para injetar API key, PII strip e audit log |

#### Bypasses da Factory (arquivos que instanciam providers diretamente)

| Provider | Arquivos com bypass | Risco |
|----------|-------------------|-------|
| Gemini (`google.genai.Client`) | `gemini_voice_service.py`, `gemini_voice.py` (API), `llm.py` (AI domain) | Médio — bootstrap mitiga com monkey-patch |
| Claude (`anthropic.Anthropic`) | `experience_highlights.py`, `archetypes.py`, scripts Jira | Médio — bootstrap mitiga |
| OpenAI (`openai.OpenAI`) | Menos frequente em app code, patches via bootstrap | Baixo |

**Mitigação:** `llm_bootstrap.py` intercepta construtores diretos de `anthropic.Anthropic`, `openai.OpenAI` e `genai.Client` e injeta API key, PII stripping e audit logging automaticamente, mesmo sem usar a factory.

### 13.4 Comunicação & Voice

| Canal | Serviço | Arquivo | Status |
|-------|---------|---------|--------|
| **Voice (WSI)** | Twilio PSTN + VoIP | `twilio_voice_service.py` | Implementado — chamadas outbound e browser-based |
| **Voice STT** | Gemini Flash 2.5 | `gemini_voice_service.py` | Implementado — via Replit AI Integrations |
| **Voice TTS** | OpenAI TTS | Via voice orchestrator | Implementado — transcoded para μ-law (Twilio) |
| **Voice Fallback STT** | Deepgram `nova-2` | `deepgram_service.py` | Implementado — fallback se transcrição primária for curta/baixa confiança |
| **WhatsApp** | Twilio Content API | `whatsapp_twilio_service.py` | Implementado — texto, mídia, botões interativos nativos |
| **Teams** | Incoming Webhooks + Bot Framework | `teams_service.py` | Implementado — Adaptive Cards, alertas por severidade |
| **Email** | Resend + Mailgun (fallback) | `email_service.py` | Implementado — factory com FallbackProvider, circuit breaker |
| **WebSocket** | WSManager singleton | `ws_manager.py` | Implementado — audio stream, chat real-time, job monitoring |

**Pipeline de voz WSI completo:**

```
Twilio (μ-law audio)
    ↕ WebSocket /audio-stream
Gemini Flash 2.5 (STT)
    ↓
LIA LLM (processamento)
    ↓
OpenAI (TTS)
    ↓ transcode → μ-law
Twilio (audio para candidato)
    ↓
PII Masking → Transcript → wsi_deterministic_scorer
```

### 13.5 Resiliência & Segurança

| Componente | Implementação | Detalhes |
|-----------|--------------|---------|
| **Circuit Breakers** | 18 serviços monitorados | Anthropic, OpenAI, Gemini, Pearch, WorkOS, Merge, Google Calendar, Gupy, Pandapé, Mailgun, Resend, Twilio, Deepgram, iugu, vindi, etc. Config: 5 falhas → open, 30s recovery, 2 sucessos → close |
| **SLOs** | Definidos por serviço | Ex: Anthropic 99.9% availability, p95 8s. Degraded mode com respostas amigáveis |
| **FairnessGuard** | 16 categorias de discriminação | Gender, Race, Age, Religion, Disability, Socioeconomic, etc. Regex (Layer 1) + implicit bias (Layer 3). Bloqueia e retorna mensagem educativa (CLT Art. 5, Lei 10.741/03) |
| **PII Masking** | 4 camadas | Layer 1: regex (CPF, email, phone) nos logs. Layer 2: `strip_pii_for_llm_prompt` antes de enviar a LLMs. Layer 3: Sentry `before_send`. Layer 4: Microsoft Presidio NER para nomes/locais |
| **Rate Limiting** | Redis sliding window | Per-user: 600/min, 20K/hr. Per-company: 3K/min, 60K/hr. Fallback in-memory se Redis cai |
| **HITL** | LangGraph interrupts + Redis + DB | Flows protegidos: WizardGraph (criação de vaga), PipelineTransition (mudança de estágio), WSI Interview (scores). Redis para fast-path (24h TTL), DB para audit trail. Opt-in `auto_confirm` por domínio |
| **Policy Engine** | Regras por setor | `ALPHA1_SECTOR_RULES` com autonomy levels e HITL thresholds por indústria. Rules: ALLOW, DENY, REQUIRE_APPROVAL |
| **Auth Middleware** | JWT + Cross-Tenant Guard | Extrai `company_id` do JWT, compara com header `X-Company-ID`, rejeita mismatches com 403 |
| **Prompt Injection Guard** | `check_input_security` | Roda em todos POST/PUT agent-facing |
| **Sentry** | PII scrubbing + `send_default_pii=False` | `before_send` hook com `_scrub_pii` em exceptions e breadcrumbs |

### 13.6 Infraestrutura de Dados

| Componente | Quantidade | Detalhes |
|-----------|-----------|---------|
| **Alembic migrations** | 60 | Versionadas em `alembic/versions/` |
| **SQLAlchemy models** | 217 | 109 em `libs/models/` + 108 em `app/models/` |
| **pgvector** | 768-dim | Embeddings com índice HNSW para RAG search |
| **Redis** | 6 categorias de cache | Pipeline stats (60s), search (120s), job insights (180s), analytics (90s), semantic cache router (86400s) |
| **Celery tasks** | 36 implementações | 15 agendadas no beat_schedule (drift checks, LGPD cleanup, daily briefings) |
| **Celery queues** | 4 prioridades | `sourcing_high` (P8), `evaluation_normal` (P5), `vagas_normal` (P5), `onboarding_low` (P3) |
| **Broker** | Configurável | Default Redis, suporta RabbitMQ e PubSub via `BROKER_BACKEND` |

**Docker:**

| Arquivo | Propósito |
|---------|----------|
| `Dockerfile` | Dev — python:3.11-slim, deps + libs editáveis |
| `Dockerfile.prod` | Multi-stage (builder + runtime), non-root user (`appuser`), healthcheck, `alembic upgrade head` no startup + gunicorn |
| `Dockerfile.worker` | Celery workers dedicados |

**Health Checks:**

| Endpoint | Propósito |
|----------|----------|
| `/health` | Unificado — DB, Redis, Celery, LLM providers |
| `/health/ready` | Kubernetes readiness — falha se DB ou Redis estiver down |
| `/health/live` | Kubernetes liveness — 200 se processo vivo |
| `/api/v1/sourcing/health` | Health do domínio sourcing |
| `/api/v1/calendar/health` | Health do domínio calendar |

### 13.7 Variáveis de Ambiente Obrigatórias

| Categoria | Variáveis |
|-----------|----------|
| **Infra** | `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `BROKER_BACKEND` |
| **Segurança** | `SECRET_KEY` (obrigatório em prod), `ADMIN_API_KEY` |
| **LLM** | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`) |
| **Integrações** | `WORKOS_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `STRIPE_SECRET_KEY` |
| **Voice** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| **Observabilidade** | `SENTRY_DSN` (recomendado), `LANGSMITH_API_KEY` (recomendado) |

### 13.8 O que está sólido

| Área | Estado | Evidência |
|------|--------|----------|
| **Multi-Agent Orchestration** | Robusto | 7 core agents + specialized, Orchestrator com intent routing, LangGraph para flows complexos |
| **LLM Factory + Fallback** | Robusto | 3 providers com fallback automático, tenant config, budget tracking, bootstrap safety net |
| **Tool Registry** | Robusto | 60+ tools organizadas por 12 categorias com metadata YAML |
| **Circuit Breakers + SLOs** | Robusto | 18 serviços com thresholds calibrados, degraded mode, alertas Teams |
| **FairnessGuard + PII** | Robusto | 16 categorias de bias, 4 camadas de PII masking incluindo Presidio NER |
| **HITL** | Robusto | LangGraph interrupts em 3 flows críticos, Redis + DB dual-write, audit trail |
| **Policy Engine** | Robusto | Regras por setor, ALLOW/DENY/REQUIRE_APPROVAL |
| **WSI Voice Pipeline** | Robusto | Pipeline completo Twilio→Gemini STT→LLM→OpenAI TTS→Twilio, fallback Deepgram |
| **Auth + Cross-Tenant** | Robusto | JWT + company_id guard + prompt injection check |
| **Comunicação Multi-Canal** | Robusto | Voice, WhatsApp (botões nativos), Teams (Adaptive Cards), Email (Resend+Mailgun fallback) |
| **Infraestrutura** | Robusto | 217 models, 60 migrations, 36 Celery tasks, Redis caching semântico, Docker multi-stage prod |
| **Health Probes** | Robusto | Kubernetes-ready (ready/live), domain-specific health endpoints |

### 13.9 O que precisa de atenção antes do deploy

| # | Área | Problema | Severidade | Ação |
|---|------|---------|-----------|------|
| 1 | **DATABASE_URL** | ✅ RESOLVIDO — Backend conecta ao banco Replit (`helium/heliumdb`). Para deploy: Cloud SQL com `lia_db` | ✅ Resolvido | Deploy: configurar `DATABASE_URL` no Secret Manager apontando para Cloud SQL |
| 2 | **Shims de compatibilidade** | ✅ RESOLVIDO — Shims que usavam `import *` sem exportar funções `_prefixo` foram ajustados | ✅ Resolvido | Validar com `python3 -c "from app.main import app"` após cada novo shim |
| 3 | **Bug wsi_repository.py** | ✅ RESOLVIDO (07/04/2026) — SQL sem aspas e dicts com sintaxe JS | ✅ Resolvido | Backend rodando normalmente |
| 4 | **Voice provider abstraction** | `VoiceProvider` ABC existe mas `gemini_voice_service.py` e `voice_screening_orchestrator.py` importam `genai` diretamente | MEDIO | Migrar para usar ABC consistently (não bloqueia deploy) |
| 5 | **GOOGLE_APPLICATION_CREDENTIALS** | Speech/TTS precisam de service account em prod | ALTO | Configurar Workload Identity no Cloud Run |
| 6 | **Redis prod** | Sem autenticação configurada no código para prod | ALTO | Configurar `REDIS_URL` com senha para Cloud Memorystore |
| 7 | **Celery workers** | Configurados mas sem deploy separado para Cloud Run | ALTO | Provisionar segundo serviço Cloud Run usando `Dockerfile.worker` |
| 8 | **RabbitMQ** | Sem serviço gerenciado provisionado no GCP. Broker default é Redis — funciona mas RabbitMQ é preferível para durabilidade | MEDIO | Provisionar Cloud Pub/Sub ou RabbitMQ gerenciado (ver Seção 11.5), ou manter Redis como broker |
| 9 | **Factory bypasses** | ~5 arquivos app instanciam LLM providers diretamente (voz, experience highlights, archetypes) | BAIXO | `llm_bootstrap.py` mitiga com monkey-patch; migrar gradualmente para factory |
| 10 | **Tenant budget hard limits** | Tracking existe mas sem circuit breaker por gasto — tenant pode exceder orçamento | MEDIO | Implementar bloqueio automático quando budget mensal atingir threshold |

### 13.10 Checklist de Production Readiness — IA

**Infraestrutura:**

- [x] `python3 -c "from app.main import app"` passa sem erros
- [x] 60 Alembic migrations versionadas
- [x] `Dockerfile.prod` multi-stage com non-root user e healthcheck
- [ ] `alembic upgrade head` validado no banco de produção (Cloud SQL)
- [ ] `DATABASE_URL` no Secret Manager apontando para Cloud SQL
- [ ] `REDIS_URL` apontando para Cloud Memorystore (com senha)
- [ ] `SECRET_KEY` em Secret Manager (obrigatório em prod)
- [ ] Celery worker rodando como serviço separado (`Dockerfile.worker`)
- [ ] Broker configurado (Redis ou RabbitMQ/Pub/Sub)

**LLM & IA:**

- [x] LLM Factory com 3 providers (Gemini, Claude, OpenAI) e fallback automático
- [x] Embedding Factory com 2 providers (Gemini, OpenAI) e 768-dim consistente
- [x] LLM Bootstrap safety net ativo (monkey-patch de imports diretos)
- [x] Tenant provider config via `tool_permissions.yaml`
- [x] Tenant budget tracking em Redis
- [ ] `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY` no Secret Manager
- [ ] Budget hard limits implementados por tenant
- [ ] Validar fallback chain com circuit breaker aberto em staging

**Segurança & Compliance:**

- [x] FairnessGuard com 16 categorias de discriminação
- [x] PII Masking em 4 camadas (regex, LLM strip, Sentry scrub, Presidio NER)
- [x] HITL em 3 flows críticos (Wizard, Pipeline, WSI)
- [x] Auth JWT + Cross-Tenant Guard + Prompt Injection Check
- [x] Rate limiting per-user e per-company com Redis sliding window
- [x] Policy Engine com regras por setor
- [x] Sentry com PII scrubbing e `send_default_pii=False`
- [ ] `SENTRY_DSN` configurado para produção
- [ ] Workload Identity para Google APIs (Speech, Calendar)

**Comunicação:**

- [x] WSI Voice Pipeline completo (Twilio→Gemini→LLM→OpenAI TTS→Twilio)
- [x] WhatsApp com botões interativos nativos (Twilio Content API)
- [x] Teams com Adaptive Cards e alertas por severidade
- [x] Email com fallback Resend→Mailgun
- [x] WebSocket para audio stream, chat, job monitoring
- [x] `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` configurados (Replit Secrets) — mover para Secret Manager GCP no deploy
- [x] `TWILIO_PHONE_NUMBER` configurado (`+551150289337`)
- [ ] `TWILIO_WHATSAPP_NUMBER` — aguardando aprovação Meta Business Suite
- [ ] Teams webhook URL atualizada para URL de produção
- [ ] `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` no Secret Manager

**Observabilidade:**

- [x] Health probes Kubernetes-ready (ready/live/unified)
- [x] Circuit Breakers com SLOs para 18 serviços
- [x] LangSmith tracing ativo — projeto `lia-agent-system`, 301+ traces capturados
- [x] Prometheus metrics endpoint (`/metrics`)
- [x] `LANGSMITH_API_KEY` configurado e ativo
- [ ] Grafana conectado ao Prometheus scrape

---

## 14. Avaliação — Rails API e Banco de Dados

> `ats-api-copia` — componente **opcional** de dados legados. Auditado em profundidade em abril 2026.
>
> **Mudança fundamental pós-auditoria:** O Rails NÃO é o "core de dados" — o FastAPI/Alembic já é a fonte de verdade. O Rails é um backend opt-in para dados legados, ativado apenas quando necessário.

> **Nota sobre dados quantitativos:** Os números de controllers, rotas, tabelas e linhas de código abaixo foram verificados no audit de abril 2026. São dados pontuais — podem mudar se houver commits nos repos legados. Para dados voláteis como "contagem de rotas frontend com backendTarget:rails", revalidar antes de cada marco de deploy.

### O que o Rails API realmente provê (dados verificados na auditoria)

**Controllers — 16 controllers no código fonte, 3 ausentes (não implementados). Classificação por estado real:**

**Controllers implementados com tabelas reais no banco (11 funcionais):**

| Controller | Rotas principais | Status |
|---|---|---|
| `SessionsController` | `POST /v1/sessions` | ✅ Funcional — JWT auth |
| `UsersController` | `GET/PUT /v1/me`, `/v1/users/users` | ✅ Funcional |
| `CandidatesController` | `GET/POST/PUT/DELETE /v1/users/candidates` | ✅ Funcional — CRUD completo |
| `JobsController` | `GET/POST/PUT/DELETE /v1/users/jobs` | ✅ Funcional — com owner check |
| `AppliesController` | `GET/POST/PUT/DELETE /v1/users/applies` | ✅ Funcional — com soft delete |
| `SelectiveProcessesController` | `GET /v1/users/selective_processes` | ✅ Funcional |
| `MessagesController` | `GET/POST /v1/users/messages` | ✅ Funcional |
| `ClientAccountsController` | `GET/POST/PUT /v1/users/client_accounts` | ✅ Funcional (via resources) |
| `ClientUsersController` | `GET/POST/PUT /v1/users/client_users` | ✅ Funcional (via resources) |
| `CompanyProfilesController` | `GET/POST/PUT /v1/users/company_profiles` | ✅ Funcional (via resources) |
| `TalentPoolsController` | `GET/POST /v1/users/talent_pools` + custom actions | ✅ Controller existe; tabela criada só após rodar 31 migrações faltantes |
| `RecruitmentCampaignsController` | `GET/POST /v1/users/recruitment_campaigns` + custom actions | ✅ Controller existe; tabela criada só após rodar 31 migrações faltantes |

**Controllers com rotas definidas mas tabelas faltantes (requerem 31 migrações não aplicadas):**

| Controller | Rotas | Status |
|---|---|---|
| `DepartmentsController` | `GET/POST/PUT /v1/users/departments` | ⚠️ Controller existe, tabela NÃO existe no banco — erro de banco se chamado |
| `EmailTemplatesController` | `GET/POST/PUT /v1/users/email_templates` | ⚠️ Idem — erro de banco |
| `InterviewsController` | `GET/POST/PUT /v1/users/interviews` | ⚠️ Idem — erro de banco |
| `NotificationsController` | `GET/POST/PUT /v1/users/notifications` | ⚠️ Idem — erro de banco |

**Controllers completamente ausentes (3 — causarão 404 se Rails for ativado sem criá-los):**

| Controller faltante | Impacto |
|---|---|
| `CandidateListsController` | 3 rotas frontend com `backendTarget: "rails"` darão 404 |
| `InterviewNotesController` | Idem |
| `FeedbackController` | Idem |

> **Nota crítica:** As tabelas de departments, email_templates, interviews e notifications não existem no banco real do Rails (schema.rb versão 2025_07_14_142059). As 31 migrações que as criariam nunca foram aplicadas. Ativar esses controllers sem rodar as migrações resulta em erros de banco.

### Estratégia de integração LIA ↔ Rails (apenas se Rails for ativado)

```
OPÇÃO A (REST — mais simples, pós-auditoria recomendado):
  lia-agent-system ──REST──► ats-api-copia (Rails)
  Simples, mantém fronteira clara entre serviços.
  Latência adicional de ~5-20ms por request.
  Usar apenas para os 5 recursos com tabelas reais:
  candidates, jobs, applies, messages, selective_processes

OPÇÃO B (banco compartilhado — mais performático):
  lia-agent-system ──SQL──► PostgreSQL (mesma instância que o Rails)
  Zero latência de rede interna.
  Requer acesso read/write direto às tabelas Rails.
  Risco: quebrar integridade se escrita não seguir convenções Rails.

OPÇÃO C (status quo — sem Rails):
  lia-agent-system serve tudo via FastAPI
  RAILS_API_URL vazia = RailsAdapter usa local DB diretamente
  Zero latência de rede, zero dependências extras
  ✅ ADOTADA — ver Seção 2F
```

**Recomendação:** manter Opção C (status quo — FastAPI serve tudo) até que haja dados reais de clientes no banco Rails que precisem ser acessados. As Opções A e B são relevantes **apenas se/quando Rails for ativado** como opt-in.

### 14.1 Compatibilidade de Dados: Formato JSON e Serialização

> Esta subseção é crítica durante a migração Frontend ↔ Rails. O frontend foi originalmente escrito para consumir respostas do FastAPI (dicts planos). O Rails usa `JSONAPI::Serializer` que produz formato aninhado.

**Diferença de formato:**

```json
// FastAPI — flat dict (formato atual que o frontend espera)
{
  "id": 42,
  "name": "João Silva",
  "email": "joao@example.com",
  "status": "active"
}

// Rails com JSONAPI::Serializer — formato aninhado
{
  "data": {
    "id": "42",
    "type": "candidate",
    "attributes": {
      "name": "João Silva",
      "email": "joao@example.com",
      "status": "active"
    }
  }
}
```

**Decisão de arquitetura (escolher uma abordagem antes de migrar cada domínio):**

| Abordagem | Descrição | Quando usar |
|---|---|---|
| **Adapter no proxy** | O Next.js proxy transforma a resposta Rails para o formato flat antes de entregar ao frontend | Quando há muitos componentes consumindo o dado e seria difícil mudar todos |
| **Serializer customizado no Rails** | Configurar o Rails para retornar flat JSON em vez de JSONAPI padrão | Preferido — mais simples, evita lógica no proxy |
| **Adapter no frontend** | Componentes React entendem os dois formatos | Não recomendado — espalha lógica de parsing |

**Recomendação:** usar o serializer customizado no Rails (opção B). Configurar `JSONAPI::Serializer` com `include_root: false` ou usar serializers que retornem flat JSON por padrão — equivalente ao que FastAPI produz.

**Convenções de naming:**

| Aspecto | FastAPI | Rails | Ação |
|---|---|---|---|
| Nomes de campos | `snake_case` | `snake_case` | Compatível — sem mudança |
| IDs | integer (`42`) | string (`"42"`) | Converter no serializer Rails: `id.to_i` |
| Datas/timestamps | ISO 8601 UTC (`2026-04-08T10:00:00Z`) | ISO 8601 UTC | Compatível — sem mudança |
| Booleanos | `true`/`false` | `true`/`false` | Compatível |
| Arrays vazios | `[]` | `[]` | Compatível |
| Campos nulos | `null` | `null` | Compatível |

**Timezone:** ambos os serviços devem usar UTC. Verificar `config.time_zone = "UTC"` no `application.rb` do Rails e `PGTZ=UTC` na variável de ambiente do banco.

**Checklist de compatibilidade por domínio migrado:**

- [ ] Formato de resposta verificado (flat vs. JSONAPI aninhado) antes de conectar ao frontend
- [ ] IDs tipados como integer no contrato da API (Rails retorna string por padrão no JSONAPI)
- [ ] Timestamps em UTC nos dois lados
- [ ] Campos com nomes diferentes mapeados explicitamente no serializer

### Checklist de production readiness — Rails + Banco

- [ ] Cloud SQL provisionado (PostgreSQL 16 com pgvector habilitado)
- [ ] ~~Banco Rails migrado para Cloud SQL (`rails db:migrate`)~~ — **condicional, apenas se Rails for ativado como opt-in** (ver Seção 2F)
- [ ] Banco LIA criado (`lia_db`) — **FastAPI é a fonte de verdade**
- [ ] Migrations Alembic do FastAPI rodadas (`alembic upgrade head`) — **obrigatório**
- [ ] Backups automáticos habilitados no Cloud SQL (retenção 7 dias)
- [ ] Point-in-time recovery habilitado
- [ ] IP do Cloud Run autorizado a conectar no Cloud SQL
- [ ] Connection pooling configurado (pgBouncer ou Cloud SQL Proxy)
- [ ] `RAILS_API_URL` deixada **vazia** (FastAPI serve tudo) — preencher apenas se Rails for ativado
- [ ] ~~Formato JSON de resposta Rails validado~~ — não necessário enquanto Rails estiver inativo

---

## 14.3 Estratégia de Ownership de Migração (Database)

> Define qual serviço é o "dono" de cada tabela do PostgreSQL — quem faz CRUD, quem roda migrations, quem é a fonte de verdade. Atualizado pós-auditoria de abril 2026.

**Regra geral (revisada pós-auditoria):**

```
FastAPI/Alembic owns: TUDO — todas as tabelas ativas existem via Alembic.
              → Migrations via `alembic upgrade head`
              → FastAPI é a fonte de verdade para todos os domínios
              → 60 migrações aplicadas, banco completo

Rails owns (opt-in futuro): apenas tabelas com dados legados de clientes reais.
              → Migrations via `rails db:migrate` (ActiveRecord)
              → Apenas as 12 tabelas que REALMENTE existem no schema Rails:
                accounts, applies, candidates, jobs, messages, permissions,
                role_permissions, roles, selective_processes, user_permissions,
                user_roles, users
              → AS OUTRAS TABELAS (departments, email_templates, interviews, etc.)
                NÃO existem no banco Rails — as 31 migrações pendentes nunca rodaram

Coexistência (quando Rails ativado): FastAPI pode ler tabelas Rails via SQL ou REST.
```

**Mapeamento de domínios por owner (estado atual):**

| Domínio | Owner ATUAL | Tabelas principais | Migration tool |
|---|---|---|---|
| Candidatos | **FastAPI** | `candidates` (Alembic) | Alembic |
| Vagas | **FastAPI** | `jobs`, `selective_processes` (Alembic) | Alembic |
| Aplicações | **FastAPI** | `applies` (Alembic) | Alembic |
| Clientes / Empresas | **FastAPI** | `client_accounts`, `client_users`, `company_profiles` (Alembic) | Alembic |
| Usuários | **FastAPI** | `users` (Alembic) | Alembic |
| Entrevistas | **FastAPI** | `interviews` (Alembic) | Alembic |
| Mensagens | **FastAPI** | `messages` (Alembic) | Alembic |
| Email templates | **FastAPI** | `email_templates` (Alembic) | Alembic |
| Notificações | **FastAPI** | `notifications` (Alembic) | Alembic |
| Embeddings / Vetores | FastAPI | `candidate_embeddings`, `job_embeddings` | Alembic |
| Sessões de triagem | FastAPI | `screening_sessions`, `triagem_sessions` | Alembic |
| Estado de agentes | FastAPI | `agent_state`, `conversation_history` | Alembic |
| WSI / Perguntas | FastAPI | `wsi_sessions`, `wsi_questions` | Alembic |
| Audit logs IA | FastAPI | `ai_audit_logs`, `bias_reports` | Alembic |
| LGPD / Retenção | FastAPI | `lgpd_retention`, `dsr_requests` | Alembic |

**O que muda quando Rails for ativado (opt-in futuro):**

| Domínio | Owner após Rails ativado | Condição |
|---|---|---|
| Candidatos | Rails (dados legados) | Apenas as 12 tabelas com dados reais no banco Rails |
| Vagas | Rails (dados legados) | Idem |
| Mensagens | Rails (dados legados) | Idem |
| Demais domínios | FastAPI/Alembic | Continuam no FastAPI mesmo com Rails ativo |

**Regra para novas tabelas:**

> **Estado atual:** toda nova tabela → **FastAPI/Alembic**.
> **Após Rails ativado:** se a tabela armazena dados de negócio legados já existentes no banco Rails → Rails owns. Se é dado novo ou de IA → FastAPI/Alembic owns.

**Conflitos a evitar:**

- Nunca rodar `alembic` em tabelas que Rails criou (quando Rails ativado)
- Em banco compartilhado, prefixar tabelas IA com `lia_` para distinguir visualmente
- Se Rails for ativado: migrations Alembic primeiro, depois testar conectividade Rails → banco antes de rodar `rails db:migrate`

---

## 15. Arquitetura Multi-tenant e LLM Factory

> O conceito central do produto: cada empresa usa a LIA com seu próprio contexto, dados e — futuramente — seu próprio modelo de linguagem.

### 15.1 Como o multi-tenant funciona hoje

```
┌─────────────────────────────────────────────────────────────┐
│                ISOLAMENTO POR TENANT (HOJE)                  │
│                                                              │
│  Empresa A (Tenant A)          Empresa B (Tenant B)         │
│  organizationId: org_aaa       organizationId: org_bbb       │
│                                                              │
│  WorkOS SSO → workos_session   WorkOS SSO → workos_session   │
│       │                               │                      │
│       ▼                               ▼                      │
│  /api/backend-proxy            /api/backend-proxy            │
│  (injeta org_aaa em todas      (injeta org_bbb em todas      │
│   as chamadas ao backend)       as chamadas ao backend)      │
│       │                               │                      │
│       ▼                               ▼                      │
│  FastAPI filtra por            FastAPI filtra por            │
│  company_id = org_aaa          company_id = org_bbb          │
│       │                               │                      │
│  MESMO banco PostgreSQL ──────────────┘                      │
│  Dados isolados por company_id                              │
└─────────────────────────────────────────────────────────────┘
```

**Nível de isolamento atual:** Lógico — e isso significa o seguinte:

```
ISOLAMENTO LÓGICO (o que temos):
  Banco único. Todos os clientes compartilham o mesmo servidor PostgreSQL.
  Cada linha das tabelas tem um company_id que separa os dados.

  SELECT * FROM candidates WHERE company_id = 'empresa-a'
  → empresa-A nunca vê dados da empresa-B... desde que o filtro funcione.

  Risco: um bug de query que esqueça o filtro pode, em teoria, expor dados.
  Mitigação: testes de isolamento, revisão de código, middleware de auth.

ISOLAMENTO FÍSICO (não temos — para o futuro):
  Cada cliente teria seu próprio banco de dados separado.
  Impossível vazamento por bug de query.
  Custo: muito maior. Operação: muito mais complexa.
  Quando faz sentido: clientes enterprise, contratos com exigências
  regulatórias (bancos, saúde, governo).
```

**Conclusão:** para o mercado inicial (PME e midmarket), isolamento lógico é suficiente, correto e é o padrão adotado pela maioria dos SaaS B2B. Isolamento físico fica no roadmap para contratos enterprise futuros (Fase 3 abaixo).

---

### 15.2 LLM Factory — O conceito

O produto prevê que cada empresa-cliente possa plugar seu próprio modelo de linguagem:

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM FACTORY                                │
│                                                                 │
│  empresa-a → ANTHROPIC_API_KEY = sk-ant-xxx  → Claude          │
│  empresa-b → usa LIA SaaS (chave WeDO)       → Claude/Gemini   │
│  empresa-c → OPENAI_API_KEY = sk-openai-xxx  → GPT-4o          │
│  empresa-d → GEMINI_API_KEY = AIza-xxx       → Gemini Pro      │
│                                                                 │
│  Resolvido por:                                                 │
│  app/orchestrator/fast_router.py — seleciona o LLM             │
│  app/shared/resilience/circuit_breaker.py — fallback automático │
└─────────────────────────────────────────────────────────────────┘
```

**Status no código:** O `fast_router.py` e o `circuit_breaker.py` já implementam fallback entre modelos. A factory per-tenant (onde cada empresa usa sua própria chave) está no roadmap mas **não está completamente implementada** — hoje o sistema usa chaves globais (da WeDO).

**Para implementar LLM Factory completa:**
1. Adicionar tabela `company_llm_configs` (chave criptografada por company_id)
2. Modificar o `fast_router.py` para carregar a chave do tenant antes de invocar o LLM
3. Usar KMS do GCP para criptografar as chaves armazenadas no banco

**Pré-requisito crítico antes de liberar a factory: benchmarking de modelos**

Quando um cliente usa um LLM diferente do Claude (ex: GPT-4o, Gemini, Llama), o produto precisa garantir que a qualidade se mantém. Isso exige um processo de avaliação formal antes de liberar cada modelo:

| Dimensão | O que avaliar |
|---|---|
| **Assertividade** | O agente classifica intenções corretamente? Candidatos são rankeados com qualidade similar? |
| **Formato de output** | O modelo retorna JSON estruturado de forma confiável (sem alucinações de formato)? |
| **Compatibilidade de prompts** | Nossos prompts são Claude-específicos ou LLM-agnósticos? Precisam de adaptação? |
| **Latência** | O tempo de resposta é aceitável para o produto (metas: triagem <3s, chat <2s)? |
| **Custo por operação** | Triagem de 100 CVs custa quanto em cada modelo? Comparar com Claude como baseline. |
| **Janela de contexto** | O modelo suporta a quantidade de contexto que os agentes usam (8k–32k tokens)? |
| **Estabilidade** | O modelo produz respostas consistentes entre chamadas idênticas (baixa variância)? |

Esse processo se chama *model evaluation* (ou LLM benchmarking). Deve rodar contra um dataset curado de vagas e candidatos reais (anonimizados) antes de qualquer modelo ser liberado para produção. O time de AI é responsável por esse processo.

---

### 15.3 WorkOS — Multi-tenant em produção

```
Plano WorkOS necessário para produção:
  - Tier: Enterprise (suporta múltiplas organizações, SAML, SCIM)
  - Configurações por ambiente: Dev, Staging, Production (3 ambientes)
  - SSO providers por organização: Google, Microsoft, SAML genérico

Configurações obrigatórias no WorkOS dashboard:
  - Redirect URIs:
      https://wedotalent.cc/api/auth/workos/callback
      https://staging.wedotalent.cc/api/auth/workos/callback
      http://localhost:5000/api/auth/workos/callback (dev)
  - Allowed origins:
      https://wedotalent.cc
      https://staging.wedotalent.cc
```

---

### 15.4 Evolução da arquitetura — Roadmap de multi-tenancy

| Fase | Descrição | Complexidade |
|---|---|---|
| **Fase 1 (atual)** | Isolamento lógico por `company_id`, chaves LLM globais | ✅ Implementado |
| **Fase 2** | LLM Factory: cada empresa usa sua própria chave | Média (2-3 sprints) |
| **Fase 3** | Banco isolado por cliente (schema separado) | Alta (mídia enterprises) |
| **Fase 4** | Modelo fine-tuned por cliente (dados próprios) | Alta (roadmap longo) |

---

## 16. Checklist Final — Go-Live

> Lista consolidada de todos os itens deste documento. Use como board de acompanhamento antes do go-live.
>
> **Nota pós-auditoria (abril 2026):** Rails NÃO é pré-requisito para o go-live. FastAPI é a fonte de verdade. Deixar `RAILS_API_URL` e `RAILS_BACKEND_URL` **vazias** para o primeiro deploy — FastAPI serve tudo automaticamente. Ver Seção 2F e Seção 23.

### Código (Replit + time dev)

**Frontend (ver Seção 12.1 para detalhes de cada item):**
- [x] Dockerfile Next.js criado com `output: standalone` (`plataforma-lia/Dockerfile`)
- [x] `next.config.js` corrigido (standalone, BACKEND_URL, sem distDir/trailingSlash)
- [x] `.env.example` completo e documentado
- [x] `.dockerignore` criado
- [x] Testes E2E rodando no Replit (24/26 passando, auth via cookie bypass)
- [x] Integrações IA confirmadas como server-side only (sem leak de chaves)
- [x] Autenticação WorkOS SSO + JWT auditada — totalmente implementada
- [x] ✅ **P1:** 104+ proxy route files migrados + 11 arquivos frontend corrigidos (Task #99) — zero `NEXT_PUBLIC_BACKEND_URL`
- [x] ✅ **P2:** `next build` passa sem erros (`ai-credits/page.tsx` — `"use client"` adicionado)
- [x] ✅ **P4:** Zero `NEXT_PUBLIC_*` expondo URLs internas (resolvido com P1, Task #99)
- [ ] 🟡 **P5:** 4 arquivos de app com vars Replit-only precisam de fallback (2 frontend: `workos.ts`, `jira-service.ts` + 2 backend: `shared_searches.py`, `email_adapter.py`)
- [x] ✅ **P6:** WebSocket URLs parametrizadas com `NEXT_PUBLIC_WS_URL` (Task #74)
- [ ] WorkOS prod configurado (API key + redirect URIs para `wedotalent.cc`)
- [ ] Headers de segurança em `next.config.js`
- [ ] Sentry DSN frontend
- [ ] Teams Tab URL atualizada para prod
- [ ] Testes E2E completos com WorkOS real em CI

**AI Agent (ver Seção 12.1 P3 e Seção 13 para detalhes):**
- [x] Bug `wsi_repository.py` corrigido (SQL sem aspas + dicts JS-style → Python correto)
- [x] `.env.example` atualizado (`API_PORT` corrigido, `RAILS_API_URL` adicionado)
- [x] ✅ **P3:** `DATABASE_URL` corrigido para banco real (`helium/heliumdb`)
- [x] `python3 -c "from app.main import app"` sem erros
- [x] 60 Alembic migrations versionadas e sequência limpa
- [x] Twilio credenciais configuradas (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)
- [ ] Todos os secrets movidos para Secret Manager GCP
- [ ] Celery worker configurado como serviço separado
- [ ] Service Account / Workload Identity para Google Speech/TTS
- [ ] Teams webhook URL atualizada para URL prod Cloud Run
- [ ] TWILIO_WHATSAPP_NUMBER configurado após aprovação Meta

### Infraestrutura (time infra)

**GCP:**
- [ ] Projeto GCP criado com billing ativo
- [ ] APIs habilitadas: Cloud Run, Cloud SQL, Cloud Memorystore, Speech, TTS, Secret Manager, Container Registry
- [ ] Cloud SQL PostgreSQL 16 provisionado
- [ ] Cloud Memorystore (Redis) provisionado
- [ ] RabbitMQ provisionado (CloudAMQP ou VM)
- [ ] Secret Manager populado (todos os secrets)
- [ ] Cloud Run: `lia-frontend` deployado
- [ ] Cloud Run: `lia-agent` deployado
- [ ] Cloud Run: `celery-worker` deployado (serviço adicional)
- [ ] Load Balancer configurado com SSL
- [ ] DNS: `wedotalent.cc` + `staging.wedotalent.cc` + APIs

**Staging:**
- [ ] Cloud Run staging deployado (frontend + agent)
- [ ] Banco staging separado do banco de produção
- [ ] GitHub Actions: develop → staging automático
- [ ] GitHub Actions: main → prod automático

### Integrações (time produto + infra)

- [ ] WorkOS: ambiente de produção criado e configurado
- [ ] Anthropic: `ANTHROPIC_API_KEY` no Secret Manager prod
- [ ] Google AI: `GEMINI_API_KEY` no Secret Manager prod
- [ ] Google Speech/TTS: APIs habilitadas no projeto GCP
- [ ] Twilio Voice: mover credenciais (já configuradas no Replit) para Secret Manager GCP
- [ ] Twilio WhatsApp: completar registro Meta Business Suite → configurar `TWILIO_WHATSAPP_NUMBER`
- [ ] Microsoft Teams: webhook URL de prod registrado no Azure
- [ ] Resend: `RESEND_API_KEY` no Secret Manager
- [x] Sentry: ativo em dev (org `talensesgroup-wedotalent`, 4 issues rastreadas) — configurar DSN prod no Secret Manager
- [ ] WhatsApp Meta: (se pronto) credenciais de prod

### Validação funcional (time completo)

> **Plano detalhado:** ver `VALIDATION_PLAN.md` para checklist completo com 50+ smoke tests,
> critérios go/no-go, runbook de rollback, e testes de isolamento multi-tenant.

- [ ] Login Google SSO (via WorkOS)
- [ ] Login Microsoft SSO (via WorkOS)
- [ ] Criação de vaga
- [ ] Upload de CV + triagem por Claude
- [ ] Triagem por voz (Twilio + Google STT)
- [ ] Chat com LIA no funil
- [ ] Bot Teams respondendo em prod
- [ ] Mover candidato no kanban
- [ ] Geração de relatório
- [ ] Notificação por email (Resend)
- [ ] Notificação por WhatsApp (se ativo)
- [ ] LGPD: solicitação de exclusão de dados (endpoint admin)
- [ ] Multi-tenant: criar 2 empresas separadas, confirmar isolamento de dados

---

## 17. Fluxo de Desenvolvimento Assistido por IA (PM + Claude Code)

> Esta seção documenta o fluxo de trabalho onde o PM desenvolve features diretamente com auxílio de IA (Replit + Claude Code), e como esse código se integra ao processo do time de engenharia.

### O modelo de trabalho

O PM tem capacidade de criar features, corrigir bugs e evoluir o produto utilizando Replit como ambiente de desenvolvimento e Claude Code como assistente técnico. Para garantir qualidade e consistência, esse fluxo usa três pilares:

1. **Specs** — documentos de especificação técnica que descrevem o comportamento esperado antes de qualquer código ser escrito
2. **Skills** — instruções padronizadas que ensinam ao assistente de IA os padrões do projeto (Design System, arquitetura, convenções de código)
3. **Revisão do time** — todo código gerado que for para `develop` passa por code review de um dev antes do merge

### Fluxo de uma feature

```
PM identifica necessidade
         │
         ▼
Escreve spec (comportamento esperado, critérios de aceite)
         │
         ▼
Claude Code gera o código guiado pelos specs + skills
         │
         ▼
PM valida no Replit (funcionalidade, visual, fluxo)
         │
         ▼
PM abre PR → branch feature/* → develop
         │
         ▼
Dev do time faz code review
  - Verifica consistência com arquitetura
  - Identifica efeitos colaterais não visíveis no contexto local
  - Valida que padrões do projeto foram seguidos
         │
         ▼
Aprovado → merge → staging → produção
```

### Por que o code review ainda é necessário?

O código gerado por IA com bons specs é de qualidade consistente — mas o assistente não tem visibilidade do contexto completo do produto (outros módulos, banco de dados em produção, edge cases de uso real). O dev do time preenche essa lacuna:

- Detecta efeitos colaterais em outras partes do sistema
- Garante que a migration de banco está correta
- Valida performance em escala
- Mantém o time ciente de tudo que entra no produto

### Biblioteca de documentação técnica (TODO)

Existe um trabalho em andamento de consolidar uma **biblioteca de documentos técnicos padrão** — seguindo práticas de mercado — para uso não apenas do PM mas de todo o time, que trabalha cada vez mais com IA no desenvolvimento.

Esta biblioteca inclui (e não se limita a):

| Tipo de documento | Propósito |
|---|---|
| **Architecture Decision Records (ADR)** | Registra decisões arquiteturais com contexto e alternativas consideradas |
| **Technical Specs** | Descreve comportamento técnico esperado antes de implementar |
| **API Contracts** | Define contratos de interface entre serviços |
| **Runbooks** | Passo a passo para operações e incidentes em produção |
| **Onboarding técnico** | Guia de entrada para novos devs no projeto |
| **Skills de IA** | Instruções para o assistente seguir os padrões do projeto |
| **Playbooks de feature** | Checklist para implementar, testar e entregar uma feature |

> **Próximo passo:** o PM irá repassar a biblioteca completa destes documentos para ser adicionada como **Anexo** a este guia, servindo de referência consolidada para o time.

---

## 18. Status de Integrações — Microsoft Office 365 e Google Workspace

### Microsoft

| Integração | Status | Detalhes |
|---|---|---|
| **Microsoft Teams** | ✅ Pronto | Bot configurado (Azure Bot Service), Adaptive Cards, webhook de screening implementado. Pendente: propagação de credenciais no Azure (401 temporário) |
| **Microsoft SSO** | ✅ Pronto | Via WorkOS — login com conta Microsoft funcional |
| **Outlook (email)** | ✅ Parcial | Microsoft Graph API cobre leitura/envio de email via Outlook — a integração depende da autorização via Graph no tenant do cliente |
| **Calendário Outlook** | ✅ Parcial | Graph API suporta agendamento via Outlook Calendar — implementação similar ao Google Calendar já existente |
| **SharePoint / OneDrive** | ❌ Não integrado | Mencionados como conceito no código mas sem integração real de API |
| **Word / Excel** | ❌ Não integrado | Não há integração com documentos Office — não é parte do roadmap atual |

### Google

| Integração | Status | Detalhes |
|---|---|---|
| **Google SSO** | ✅ Pronto | Via WorkOS — login com conta Google funcional |
| **Google Calendar** | ✅ Pronto | `google-api-python-client` instalado, agendamento de entrevistas via Google Calendar implementado |
| **Google STT/TTS** | ✅ Pronto | Triagem de voz (WSI) usa Google Speech-to-Text e Text-to-Speech |
| **Gmail** | ❌ Não integrado | Email é enviado via Resend, não via Gmail API |
| **Google Drive / Docs / Sheets** | ❌ Não integrado | Sem integração com o Google Workspace de documentos |

### O que falta para Microsoft Office / Google Workspace completo?

A integração completa com documentos (Drive, Docs, SharePoint, OneDrive) não é parte do roadmap atual. Para clientes que precisam dessas integrações, o caminho é:
1. Definir caso de uso específico (ex: "exportar relatório para Google Sheets")
2. Criar card Jira com spec
3. O time implementa a integração pontual via API correspondente (Google Sheets API, OneDrive API)

---

## 19. Status de Integração — Slack

### O que existe hoje

O código referencia Slack em múltiplos pontos do sistema:

| Área | Arquivo | Função |
|---|---|---|
| **Hub de integrações** | `app/api/v1/integrations_hub.py` | Slack listado como canal de integração disponível |
| **Journey mapping** | `app/api/v1/journey_mapping.py` | Notificações de jornada via Slack |
| **Configuração de alertas** | `app/api/backend-proxy/alerts/config/route.ts` | Slack como destino de alertas configurável |
| **Presets de empresa** | `CompanyPresetsModal.tsx` | Interface para configurar integração Slack por empresa |

### Status

```
✅ Estrutura implementada: canais de alerta e notificação via Slack previstos na arquitetura
⚠️  Credenciais: requer Slack App configurada e OAuth token por tenant (não está em produção)
⚠️  Webhook de incoming: URL de webhook por workspace Slack precisa ser configurada por cliente
❌ Não validado em produção: integração não foi homologada end-to-end
```

### Para ativar o Slack em produção por cliente

1. Cliente cria um **Slack App** no workspace deles (ou usa o app WeDO se existir)
2. Gera o **Incoming Webhook URL** para o canal desejado
3. Configura na plataforma LIA via `CompanyPresetsModal` ou API de settings
4. Testa com notificação de candidato movido no pipeline

> Slack é uma integração leve (sem SDK pesado — apenas webhook POST) e pode ser ativada rapidamente para clientes que usam Slack como ferramenta principal.

---

## 20. Onboarding e Implementação no Cliente

> Roteiro de referência para implantação da LIA em um novo cliente. Cobre desde a configuração técnica até a homologação de canais.

### Visão geral do processo

```
FASE 1: Configuração da conta
  ↓ SSO + WorkOS
  ↓ Criação da organização (tenant)
  ↓ Usuários e permissões

FASE 2: Configuração dos canais
  ↓ Botão LIA (embed no site/ATS)
  ↓ WhatsApp Business (homologação Meta)
  ↓ Microsoft Teams (bot no tenant do cliente)
  ↓ Email (domínio verificado no Resend)
  ↓ Slack (opcional — webhook por workspace)

FASE 3: Integração com ATS do cliente (se houver)
  ↓ Webhook de eventos ou API REST
  ↓ Mapeamento de stages do funil

FASE 4: Configuração da LIA
  ↓ Persona e tom de voz
  ↓ Templates de mensagens
  ↓ Políticas de triagem (hiring policies)

FASE 5: Homologação e go-live
  ↓ Teste de ponta a ponta com vaga real
  ↓ Aprovação do cliente
  ↓ Ativação em produção
```

### Checklist de implantação — novo cliente

#### Fase 1: Conta e acesso

- [ ] Organização criada no WorkOS (`organizationId` gerado)
- [ ] SSO configurado (Google, Microsoft ou SAML do cliente)
- [ ] Usuários administradores criados e acessando a plataforma
- [ ] Permissões de papéis configuradas (admin, recrutador, gestor)

#### Fase 2: Canais de comunicação

**Botão LIA (embed)**
- [ ] Script do botão gerado para o site/ATS do cliente
- [ ] URL de destino configurada (landing page de candidatos)
- [ ] Teste: candidato clica no botão → inicia fluxo de triagem
- [ ] (Opcional) Integração com ATS via iframe ou redirect com parâmetros

**WhatsApp Business — Homologação Meta**
- [ ] Cliente possui conta no **Meta Business Suite** verificada
- [ ] **WhatsApp Business Account (WABA)** criado e aprovado pela Meta
- [ ] Número de telefone dedicado registrado no WABA
- [ ] **Número de telefone verificado** na API do WhatsApp Cloud
- [ ] `WHATSAPP_ACCESS_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID` configurados
- [ ] `WHATSAPP_VERIFY_TOKEN` configurado e webhook registrado no Meta dashboard
- [ ] URL do webhook apontando para `https://wedotalent.cc/api/v1/whatsapp/webhook`
- [ ] Teste de ponta a ponta: mensagem enviada → resposta da LIA recebida
- [ ] Templates de mensagem aprovados pela Meta (para mensagens ativas — fora da janela de 24h)

> **Atenção:** A homologação do WhatsApp com a Meta pode levar de 3 a 10 dias úteis dependendo da verificação do negócio. Iniciar este processo com antecedência.

**Microsoft Teams**
- [ ] Tenant Azure do cliente identificado (`AZURE_TENANT_ID`)
- [ ] Bot da LIA registrado no Azure Bot Service do cliente (ou WeDO com permissão)
- [ ] App do Teams instalado no workspace do cliente
- [ ] Canal de triagem configurado no Teams
- [ ] Teste: candidato recebe mensagem do bot → responde → LIA processa

**Email (Resend)**
- [ ] Domínio de email do cliente verificado no Resend (registros DNS: SPF, DKIM)
- [ ] Endereço de remetente configurado (ex: `lia@empresa-cliente.com.br`)
- [ ] Teste de envio: email de triagem enviado e recebido sem ir para spam

**Slack (opcional)**
- [ ] Slack App configurada no workspace do cliente
- [ ] Webhook URL do canal de notificações configurado na plataforma
- [ ] Teste: movimentação de candidato gera notificação no Slack

#### Fase 3: Integração com ATS do cliente (se aplicável)

- [ ] ATS do cliente identificado (Greenhouse, Lever, Workday, SAP, interno, etc.)
- [ ] Método de integração definido: webhook, API REST ou exportação manual
- [ ] Mapeamento de stages: estágios do ATS → estágios da LIA
- [ ] Teste de sincronização: candidato criado na LIA aparece no ATS
- [ ] Definir quem é o sistema de registro (source of truth): LIA ou ATS?

#### Fase 4: Configuração da LIA para o cliente

- [ ] Persona da LIA definida (nome, tom de voz, idioma)
- [ ] Templates de mensagem para cada canal aprovados pelo cliente
- [ ] **Hiring policies** configuradas (critérios de triagem automática)
- [ ] Vagas padrão criadas para testes
- [ ] Limite de triagens simultâneas configurado (controle de saturação)

#### Fase 5: Homologação e go-live

- [ ] Sessão de homologação com cliente — testar fluxo completo com vaga real
- [ ] Candidato de teste passa pelo funil completo (inscrição → triagem → retorno)
- [ ] Todos os canais ativos respondem corretamente
- [ ] Cliente aprova o comportamento da LIA (tom, qualidade das respostas)
- [ ] Monitoramento ativo nas primeiras 48h (Sentry, logs)
- [ ] Contato de suporte do cliente definido para escalonamento

---

## 21. Qualidade de IA — Gates Pós-Deploy

> Estes itens não bloqueiam o go-live, mas devem ser implementados nas semanas seguintes ao deploy estável em produção. São os controles que garantem que os agentes IA da LIA mantêm qualidade, equidade e performance ao longo do tempo.
>
> ⚠️ **IMPORTANTE:** Os scripts e datasets desta seção **não existem ainda no repositório**. Estão descritos como especificação — devem ser implementados como tasks separadas após o go-live inicial.

### 21.1 Golden Datasets e Eval Framework

> **STATUS: A IMPLEMENTAR** — Nenhum golden dataset existe no repositório. O diretório `lia-agent-system/evals/` ainda não foi criado.

**Objetivo:** garantir que mudanças no código dos agentes não degradam a qualidade das respostas de triagem.

**Golden dataset — composição mínima (a criar):**

```
50 inputs de screening com outputs esperados:
  - 20 perfis de candidato claramente qualificados (devem ter score alto)
  - 20 perfis claramente desqualificados (devem ter score baixo)
  - 10 perfis borderline (teste de calibração)

Cada input inclui:
  - Texto do CV (ou dados estruturados)
  - Descrição da vaga
  - Output esperado: { score: float, classificacao: str, justificativa: str }
```

**Métricas de qualidade (LLM-as-judge):**

| Métrica | Definição | Threshold mínimo |
|---|---|---|
| **Faithfulness** | O output é fiel às informações do CV (sem alucinações)? | > 0.85 |
| **Relevancy** | A justificativa é relevante para a vaga analisada? | > 0.80 |
| **Consistency** | Mesma entrada produz scores similares em chamadas repetidas? | variância < 10% |

**Quando rodar (após implementar):**

- Antes de qualquer deploy que toque código em `app/domains/cv_screening/`, `app/domains/wsi/` ou `app/orchestrator/`
- Após mudança de modelo LLM (Claude → Gemini ou vice-versa)
- Mensalmente como verificação de drift

**Localização a criar:** `lia-agent-system/evals/golden_datasets/screening/`

### 21.2 Auditoria de Viés (Bias Audit Automation)

> **STATUS: A IMPLEMENTAR** — O script `lia-agent-system/scripts/bias_audit.py` **não existe**. O `FairnessGuard` está implementado em `app/domains/bias_detection/`, mas o script de cron de auditoria automatizada ainda precisa ser criado.

**Objetivo:** garantir que o sistema de triagem não discrimina candidatos com base em características protegidas (gênero, etnia, idade, etc.).

**Métrica central — Adverse Impact Ratio (AIR):**

```
AIR = taxa de aprovação do grupo minoritário / taxa de aprovação do grupo majoritário

Regra dos Quatro Quintos (Four-Fifths Rule):
  AIR < 0.80 → ALERTA — possível viés adverso — investigar imediatamente
  AIR ≥ 0.80 → dentro do limite aceitável
```

**Configuração do cron (a implementar):**

```bash
# Rodar semanalmente (ex: domingo 02:00 UTC)
# Script a criar: lia-agent-system/scripts/bias_audit.py

0 2 * * 0 python lia-agent-system/scripts/bias_audit.py \
  --period=7d \
  --alert-threshold=0.80 \
  --output=gs://lia-uploads-prod/bias-reports/
```

**Ações por resultado:**

| AIR | Ação |
|---|---|
| ≥ 0.80 | Registrar no relatório mensal — nenhuma ação imediata |
| 0.70 – 0.79 | Notificar time de AI + revisar prompts de triagem |
| < 0.70 | Alertar imediatamente + pausar triagens automáticas até investigação |

**Relatório mensal:** consolidar AIR por vaga, por empresa-cliente e por grupo demográfico. Armazenar em Cloud Storage. Revisão obrigatória pelo time de AI e compliance.

**Referência:** `FairnessGuard` está implementado em `lia-agent-system/app/domains/bias_detection/`. O script de cron (`bias_audit.py`) deve ser criado como task separada.

### 21.3 Load Testing — Baseline de Performance (Locust)

> **STATUS: A IMPLEMENTAR** — O arquivo `lia-agent-system/load_tests/locustfile.py` **não existe**. O diretório `load_tests/` ainda não foi criado. O código abaixo é a especificação do que deve ser implementado.

**Objetivo:** validar que a infraestrutura GCP suporta a carga esperada antes do go-live e após mudanças de infra.

**SLAs de referência:**

| Operação | P95 | P99 |
|---|---|---|
| CRUD (listar candidatos, vagas) | < 200ms | < 500ms |
| Chat com LIA (streaming) | < 5s para primeira resposta | < 10s |
| Triagem de CV (screening) | < 5s | < 10s |
| Upload de CV + parse | < 3s | < 7s |

**Configuração do teste Locust (a criar em `lia-agent-system/load_tests/locustfile.py`):**

```python
# A IMPLEMENTAR — este arquivo não existe ainda
from locust import HttpUser, task, between

class LIAUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_candidates(self):
        self.client.get("/api/v1/users/candidates", headers={"Authorization": f"Bearer {TOKEN}"})

    @task(2)
    def list_jobs(self):
        self.client.get("/api/v1/users/jobs")

    @task(1)
    def send_chat_message(self):
        self.client.post("/api/agent/chat", json={"content": "Liste as vagas abertas"})
```

**Executar contra staging (após implementar):**

```bash
# 50 usuários simultâneos, ramp-up de 10/segundo, duração 5 minutos
locust -f load_tests/locustfile.py \
  --host=https://staging.wedotalent.cc \
  --users=50 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --html=load_test_report.html
```

**Gate de aprovação:** P95 dentro dos SLAs acima para pelo menos 95% das requisições. Se algum endpoint falhar, não avançar para produção sem investigação.

---

## 22. Plano de Limpeza de Código — Cenários Pós-Decisão Arquitetural

> Esta seção foi atualizada pós-auditoria de abril 2026. O contexto mudou: não é mais "migração para Rails" mas sim dois cenários de limpeza distintos.
>
> **Cenário A:** Rails é ativado como opt-in (dados legados são necessários)
> **Cenário B:** Rails nunca é ativado (plataforma segue 100% FastAPI)

### 22.1 Cenário A — Limpeza após ativação do Rails (opt-in)

> Executar **somente após** o Rails estar estável em produção para cada domínio, com monitoring ativo e baseline de regressão confirmado.

Quando Rails passar a servir um domínio com dados legados, o código FastAPI equivalente pode ser marcado como deprecated:

| Domínio | Arquivos / Módulos | Aprox. linhas | Pré-requisito para deprecar |
|---|---|---|---|
| Candidatos (legados) | `app/api/v1/candidates/` (splitado em 5 módulos) | ~1.739L | Rails serving candidates estável por 2+ semanas **com dados reais** |
| Clientes (legados) | `app/api/v1/clients/` (splitado em 7 módulos) | ~1.271L | Rails serving clients estável |
| Teams/Usuários (legados) | `app/api/v1/teams.py` | ~1.451L | Rails serving teams estável |

> **Nota:** Billing, WorkOS e recruitment stages são domínios onde o FastAPI tem implementações mais completas que o Rails — NÃO migrar esses domínios para o Rails.

**Após cada domínio transferido para Rails:**
- Não remover o código FastAPI imediatamente — manter como fallback por 2+ semanas
- Atualizar `backendTarget` nas rotas correspondentes para `"rails"` explicitamente
- Monitorar circuit breaker — fallback automático está ativo

### 22.2 Cenário B — Remoção de código de integração Rails (Rails nunca ativado)

> Se a decisão for nunca ativar o Rails, o código de integração pode ser removido progressivamente.

| Item | Localização | Volume | Condição |
|---|---|---|---|
| RailsAdapter | `app/domains/integrations_hub/services/rails_adapter.py` | 939L | Rails confirmado como nunca necessário |
| Client Rails | `app/services/ats_clients/wedotalent_rails.py` | 588L | Idem |
| JWT validator | `app/auth/rails_jwt.py` | — | Idem |
| Frontend flags | `backendTarget: "rails"` em 94 rotas | — | Remover flag, deixar só FastAPI |

### 22.3 Stubs e código morto (prioritário — independente do cenário)

| Item | Localização | Volume | Ação |
|---|---|---|---|
| Stub services | `app/services/` | ~120 arquivos de 2 linhas | Remover após confirmar que nenhum router os importa |
| Stub models | `app/models/` | Variável | Remover modelos que não têm tabela no banco |
| Frontend routes mortas | `plataforma-lia/src/app/api/` | ~186 rotas custom | Remover se `createProxyHandlers` cobrir o equivalente |

### 22.4 Serviços IA sensíveis — remoção com cautela especial

> Estes dois arquivos requerem um baseline de regressão IA **antes** de qualquer remoção, porque afetam diretamente a qualidade dos agentes de triagem.

| Arquivo | Linhas | Pré-requisito OBRIGATÓRIO |
|---|---|---|
| `triagem_session_service.py` | ~370L | Golden dataset (Seção 21.1) rodando em produção + baseline documentado + 50 inputs comparados pré/pós |
| `wsi_service.py` | ~320L | Idem acima + validação do WSI pipeline end-to-end em staging |

**Regra:** estes dois arquivos só podem ser removidos após produção estável com monitoring, com o eval framework ativo, e após o time de AI validar que as métricas de faithfulness e relevancy se mantêm ≥ threshold.

---

## 23. Infraestrutura — Obrigatório vs Opcional para Deploy

> Esta seção clarifica quais componentes de infraestrutura são necessários para o deploy da Plataforma LIA e quais são opcionais. Atualizado pós-auditoria de abril 2026.

### Tabela de Infraestrutura

| Componente | Status | Detalhes |
|---|---|---|
| **PostgreSQL** | 🟢 **Obrigatório** | Banco de dados principal. Alembic roda 60 migrações. Cloud SQL no GCP. |
| **pgvector** | 🟢 **Obrigatório** | Extensão PostgreSQL para embeddings semânticos. Habilitar no Cloud SQL. |
| **Redis** | 🟡 **Recomendado** | Cache, token budget, HITL, Celery results. Sem Redis: Celery usa backend alternativo, HITL pode ter problemas. Cloud Memorystore no GCP. |
| **Celery workers** | 🟡 **Recomendado** | Background jobs (12+ tasks). Sem Celery: operações assíncronas ficam pendentes. Segundo Cloud Run service. |
| **RabbitMQ** | 🟡 **Opcional** (pode usar Redis) | Message broker para Celery. Redis também serve como broker — RabbitMQ só necessário se escala exigir. CloudAMQP ou VM dedicada. |
| **Docker** | 🟢 **Transparente** | Dockerfiles já existem para frontend e backend. Cloud Run usa Docker nativamente. |
| **Elasticsearch** | ❌ **Desnecessário** | O ecossistema WeDO legado usa Searchkick + Elasticsearch. A LIA usa busca semântica + FTS (pgvector + tsvector) — **não precisa de Elasticsearch**. |
| **Rails (ats-api-copia)** | 🔵 **Opcional (opt-in)** | Ver Seção 2F. Só necessário se houver dados legados de clientes que precisem ser acessados. RAILS_API_URL e RAILS_BACKEND_URL vazias = FastAPI serve tudo. |
| **Ruby / Rails runtime** | 🔵 **Opcional (opt-in)** | Necessário apenas se Rails for ativado. Não instalar no ambiente Replit atual. |
| **Sidekiq** | 🔵 **Opcional (opt-in)** | Background jobs do Rails. Só necessário se Rails for ativado. |
| **ActionCable** | ❌ **Desnecessário** | WebSocket via Rails. A LIA usa WebSocket nativo FastAPI — ActionCable não é necessário. |
| **Terraform** | 🟡 **Recomendado** | IaC em `lia-agent-system/terraform/gcp/`. Não obrigatório, mas recomendado para reproducibilidade do infra. |
| **Cloud Armor (WAF)** | 🟡 **Recomendado** | Proteção DDoS e WAF. Não obrigatório para MVP, mas recomendado para produção. |

### Resumo: o que é realmente necessário para o primeiro deploy

```
OBRIGATÓRIO para o deploy funcionar:
  1. PostgreSQL (Cloud SQL) com pgvector
  2. Alembic migrations rodadas (alembic upgrade head)
  3. Cloud Run para frontend (Next.js — porta 5000)
  4. Cloud Run para backend (FastAPI — porta 8001)
  5. Secret Manager com variáveis obrigatórias (WorkOS, LLMs, etc.)

RECOMENDADO (adicionar antes de go-live):
  6. Redis (Cloud Memorystore) — para Celery e cache
  7. Celery worker (segundo Cloud Run service)

NÃO NECESSÁRIO:
  - Elasticsearch
  - Rails runtime
  - ActionCable
  - RabbitMQ (pode usar Redis como broker)
  - Sidekiq
```

### Comparação: custo de infra LIA vs Ecossistema WeDO Legado

| Item de infra | WeDO legado | Plataforma LIA |
|---|---|---|
| Banco de dados | PostgreSQL | PostgreSQL (mesmo) |
| Cache | Redis (Sidekiq) | Redis (Celery) |
| Busca | Elasticsearch (extra custo) | pgvector + FTS (zero custo extra) |
| WebSocket | ActionCable (dentro do Rails) | FastAPI nativo |
| Background jobs | Sidekiq + Celery + RabbitMQ (3 sistemas) | Celery (1 sistema) |
| Language runtimes | Ruby + Python + Node | Python + Node |
| **Complexidade operacional** | **Alta** | **Baixa** |

---

## Repositórios e Contatos

| Repositório | URL | Responsável |
|---|---|---|
| Frontend LIA | `github.com/wedocc2026/ats-front-copia` | Time Front |
| AI Agent LIA | `github.com/wedocc2026/lia-agent-system` | Time Back / AI |
| Rails API | `github.com/wedocc2026/ats-api-copia` | Time Back |
| Terraform GCP | `lia-agent-system/terraform/gcp/` | Time Infra |

---

---


## 24. AUDITORIA PROFUNDA COMPARATIVA — PRODUCTION READINESS

> **Data:** Abril 2026 (v3 — reescrita comparativa)
> **Escopo:** Análise técnica comparativa de dois produtos independentes:
> - **Produto Replit** = `plataforma-lia` (frontend) + `lia-agent-system` (backend) — produto principal ativo
> - **Produto wedocc2026** = `ats_api` + `ats_front` + `recruiter_agent_v5` + `wedotalent-admin` + `data_collector` + `ats_mcp` + `wedo-nuxt` — repos GitHub (WeDOTalent org)
>
> **Objetivo:** Mapear riscos, gaps e recomendações para cada produto separadamente, com análise comparativa por dimensão.
>
> **NOTA IMPORTANTE:** A versão anterior (v2) desta seção misturava dados dos dois produtos sem separação clara e continha erros factuais significativos (`ats_front` listado como "Morto", `wedotalent-admin` como "Desconhecido", contagem de bypasses inflada). Esta versão corrige tudo com dados auditados diretamente no código via GitHub API e análise do filesystem Replit.

---

### 24.1 Inventário Comparativo

#### Produto Replit (Ativo — Plataforma LIA)

| Componente | Stack | Arquivos | Métricas-Chave |
|-----------|-------|----------|---------------|
| **plataforma-lia** (frontend) | Next.js 15, React 19, Tailwind, Shadcn/Radix, Zustand, SWR | 2.090 em `src/` | 32 páginas, 1.201 componentes, 152 hooks, 35 services, 20 stores |
| **lia-agent-system** (backend) | Python 3.11+, FastAPI 0.115.5, SQLAlchemy 2.0.36, LangGraph 0.2.53, Celery 5.4.0 | 1.820 `.py` em `app/` + 169 em `libs/` | 362+ endpoints, 58 domínios, 217 models, 60 migrations, 388 test files |

**Total Replit:** ~4.079 arquivos de código (excl. node_modules, __pycache__)

#### Produto wedocc2026 (GitHub — WeDOTalent org)

| Repo | Stack | Arquivos | Branches | Último Push | Status |
|------|-------|----------|----------|------------|--------|
| **ats_api** | Ruby on Rails 7.1, PostgreSQL, Apartment, Elasticsearch, Sneakers (RabbitMQ) | 171 (main) | 44 | 2026-04-09 | Ativo (bridge para LIA) |
| **ats_front** | Nuxt 3, Vue 3, Vuetify, Pinia, TipTap, ActionCable | 904 (branch `develop`) | 39 | 2026-04-09 | **Ativo** (branch `main` vazio — todo código em `develop`) |
| **recruiter_agent_v5** | Python, LangGraph, Celery, RabbitMQ, 100% Gemini | 912 | 8 | 2026-04-08 | Referência / Parcialmente migrado para LIA |
| **wedotalent-admin** | Next.js, React, TypeScript, Shadcn/Radix, Tailwind | 438 | 1 | 2026-04-03 | Painel admin/compliance |
| **data_collector** | Python, FastAPI, Alembic, Docker | 146 (100 `.py`) | 2 | 2026-02-19 | Funcional (coleta de vagas) |
| **ats_mcp** | TypeScript, MCP SDK, Zod | ~30 | 1 | 2026-03-07 | Funcional (dev tooling) |
| **wedo-nuxt** | Nuxt 3, Vue 3, Vuetify, Histoire | 77 | 1 | 2026-02-19 | Protótipo de design |
| **reembolsointeligente** | — | 0 | 0 | 2026-02-11 | Morto (vazio) |

**Total wedocc2026:** ~2.678 arquivos de código (nos branches ativos)

**CORREÇÃO v3:** A versão anterior listava `ats_front` como "Morto — 1 arquivo". **Isso era incorreto.** O branch `main` tem apenas o `.gitignore`, mas o branch `develop` (39 branches ativos, último push 2026-04-09) contém um frontend Nuxt completo com 904 arquivos, 537 componentes Vue, 34 páginas e 18 stores. O `wedotalent-admin` também era listado como "Desconhecido" — é um painel admin Next.js com 63 páginas e 103 componentes focado em compliance (LGPD, SOC-2, SOX, ISO-27001). Contagem de "~34 bypasses Gemini" era inflada — são ~5 arquivos app com bypass direto (o resto são testes, scripts e bootstrap).

---

### 24.2 Frontend — Comparativo

| Dimensão | Replit: `plataforma-lia` | wedocc2026: `ats_front` (develop) + `wedotalent-admin` |
|----------|--------------------------|-------------------------------------------------------|
| **Framework** | Next.js 15 + React 19 | Nuxt 3 + Vue 3 + Vuetify (ats_front); Next.js + React (admin) |
| **Linguagem** | TypeScript (strict: true) | TypeScript (107 `.ts`) + Vue SFC (537 `.vue`) |
| **Design System** | DS LIA v4.2.1 — Shadcn/Radix + tokens CSS (`--lia-*`, `--wedo-*`) | Vuetify + `liaTheme` + `liaDefaults` customizados |
| **Tipografia** | Open Sans 85% + Inter 10% + JetBrains Mono 5% | Material Design Icons (`@mdi/font`) |
| **State Management** | Zustand (20 stores) + SWR + React Context | Pinia (18 stores) + composables (59) |
| **Páginas** | 32 (`page.tsx` no App Router) | 34 Vue pages + 63 admin pages = **97 total** |
| **Componentes** | 1.201 (incl. page-specific) | 147 (ats_front) + 103 (admin) = **250 total** |
| **Features/Modules** | Hooks (152) + services (35) | Features (357) + composables (59) |
| **Auth** | WorkOS SSO + Custom JWT (middleware.ts) | JWT + ActionCable WebSocket |
| **Rich Text** | — | TipTap (13 extensions) — editor WYSIWYG completo |
| **Charts** | Chart.js + Recharts | — |
| **Comunicação API** | Backend Proxy (`/api/backend-proxy` → FastAPI :8001) | Axios direto para Rails (:8080) + WebSocket (ActionCable) + Python AI (:8001) |
| **Testes** | Vitest + Playwright (~1.026 test files), Storybook + Chromatic | Playwright + axe-core (accessibility) + Histoire (component playground) |
| **Sentry** | Integrado (client/server/edge) | Não evidenciado |

**Observações:**
- `ats_front` tem mais páginas (34+63=97) que `plataforma-lia` (32), mas `plataforma-lia` tem 4.8x mais componentes (1.201 vs 250)
- `ats_front` conecta tanto ao Rails (porta 8080 via ActionCable) quanto ao Python AI (porta 8001) — arquitetura tri-camada
- `wedotalent-admin` tem 63 páginas focadas em compliance/governance (LGPD, SOC-2, SOX, ISO-27001, bias audit, trust center, SoD)
- `plataforma-lia` é mais maduro em observabilidade (Sentry, Storybook) e design system (tokens, variáveis CSS)

---

### 24.3 Backend/API — Comparativo

| Dimensão | Replit: `lia-agent-system` | wedocc2026: `ats_api` + `recruiter_agent_v5` |
|----------|--------------------------|----------------------------------------------|
| **Framework** | FastAPI 0.115.5 (Python 3.11+) | Rails 7.1 (Ruby) + FastAPI/Flask (Python) |
| **Endpoints** | 362+ (REST + WebSocket) | ~30 Rails routes + deploy docs mencionam endpoints |
| **Domínios** | 57 diretórios de domínio em DDD | 8 domínios no v5 (applies, autonomous, evaluation, insights, jobs, messaging, scheduling, sourcing) |
| **Models** | 217 SQLAlchemy (109 libs + 108 app) | 18 Rails models (Account, User, Job, Candidate, Apply, etc.) |
| **Migrations** | 60 Alembic | 20 Rails migrations |
| **Multi-tenant** | PostgreSQL RLS (`app.company_id`) + JWT + WorkOS SSO/SCIM | Apartment gem (schema-based) — elevator **comentado** |
| **Auth** | JWT HS256 (30min access, 7d refresh) + WorkOS SSO + Cross-Tenant Guard + Prompt Injection Guard | JWT HS256 (24h token) — `authorize_request` duplicado |
| **Search** | pgvector (768-dim HNSW/IVFFlat) | Elasticsearch via Searchkick |
| **Queue/Workers** | Celery 5.4 (36 tasks, 4 queues prioritárias, 15 scheduled) | Sneakers (RabbitMQ) no Rails + Celery no v5 |
| **Docker** | 3 Dockerfiles (dev, prod, worker) + 2 docker-compose | Dockerfile (Rails multi-stage) + docker-compose workers (v5) |
| **CI/CD** | GitHub Actions (ruff, bandit, pytest, DeepEval) | Brakeman + RuboCop (Rails); **Nenhum CI** no v5 |
| **Health Probes** | Kubernetes-ready (`/health/ready`, `/health/live`) + domain-specific | Não evidenciado |
| **Connection Pool** | asyncpg: pool 20, overflow 10, pre_ping, recycle 3600s | db_pool: 10 dev / 30 prod — sem pooling externo |
| **CORS** | Configurável via env vars (default localhost) | `http://localhost:3000` hardcoded |
| **Rate Limiting** | Redis sliding window (600/min user, 3K/min company) | Não evidenciado |
| **SSL** | Strip de `sslmode=` — precisa config manual | `sslmode: require` em production (OK) |

**Observações:**
- `lia-agent-system` é 10x maior que `ats_api` em models (217 vs 18) e endpoints (362+ vs ~30)
- Multi-tenant no Replit é mais robusto (RLS + JWT guard + WorkOS), mas o Apartment do Rails é mais maduro em isolamento de schema
- `recruiter_agent_v5` tem 912 arquivos de código Python mas **sem CI/CD** e **100% Gemini** (vendor lock-in crítico)
- A Rails bridge (`ats_api`) está ativa — o Replit backend conecta a ele via `rails_adapter.py`

---

### 24.4 Camada de IA — Comparativo

| Dimensão | Replit: `lia-agent-system` | wedocc2026: `recruiter_agent_v5` |
|----------|--------------------------|----------------------------------|
| **LLM Providers** | 3 providers (Gemini, Claude, OpenAI) com fallback automático + Cost Cascade | 100% Gemini — **sem abstração, sem fallback** |
| **LLM Factory** | `LLMProviderFactory` + `ProviderContainer` + tenant config | Direto via `google-generativeai` e `langchain-google-genai` |
| **Embedding** | Factory com 2 providers (Gemini + OpenAI), 768-dim | Gemini embeddings direto |
| **LLM Safety Net** | `llm_bootstrap.py` monkey-patches imports diretos | Não existe |
| **Agents** | 7 core ReAct + especializados (Diversity, GitHub, StackOverflow, Nurture) | 7 agents (intent, planner, validator, executor, processor, formatter, autonomous) |
| **LangGraph** | 3 flows ativos (WSI Interview, Job Wizard, Interview Scheduling) | Presente mas com stack mista (LangChain + Flask + Streamlit) |
| **Tool Registry** | 60+ tools em 12 categorias com metadata YAML | 21 tool files |
| **Orchestrator** | Multi-tier: Fast Router → Orchestrator (LLM-based intent) → Agent delegation | Pipeline linear: Intent → Plan → Validate → Execute → Process → Format |
| **Fairness** | FairnessGuard 3 camadas (regex, implicit, semantic LLM) + 16 categorias | Testes de fairness existem (70+ test files) mas sem guard middleware |
| **PII** | 4 camadas (regex logs, LLM strip, Sentry scrub, Presidio NER) | Não evidenciado como camada |
| **HITL** | 3 flows protegidos via LangGraph interrupts + Redis + DB | Não evidenciado |
| **Voice** | Pipeline: Twilio → Gemini STT → LLM → OpenAI TTS → Twilio + Deepgram fallback | `interview_ai/` com Dockerfile — escopo menor |
| **Tenant LLM Config** | Per-tenant provider/fallback + budget tracking em Redis | Não existe (single-tenant) |
| **Circuit Breakers** | 18 serviços com SLOs calibrados e degraded mode | Não evidenciado |
| **Policy Engine** | Regras por setor (ALPHA1_SECTOR_RULES) com ALLOW/DENY/REQUIRE_APPROVAL | Não evidenciado |

**Observações:**
- O Replit é significativamente mais maduro em governança IA (FairnessGuard, PII, HITL, Policy Engine)
- O v5 tem vendor lock-in **crítico** em Gemini — qualquer mudança de preço/API requer rewrite
- O v5 tem valor como referência de capabilities (60+ queries documentadas) e patterns de testes (fairness, hallucination)
- `llm_bootstrap.py` do Replit é um safety net único — não existe equivalente no v5

---

### 24.5 Segurança & Compliance — Comparativo

| Dimensão | Replit | wedocc2026 |
|----------|-------|-----------|
| **Auth** | JWT HS256 + WorkOS SSO/SCIM + Cross-Tenant Guard | JWT HS256 (Rails) — `authorize_request` duplicado |
| **Multi-tenant** | RLS + JWT company_id + TenantGuard + middleware | Apartment gem (schema-based) — elevator **comentado** |
| **CORS** | Configurável via env (default: localhost:5000,3000) | Hardcoded `localhost:3000` (ats_api); não configurado (v5) |
| **CSP** | Via Next.js headers | **Toda comentada** no Rails |
| **Rate Limiting** | Redis sliding window (600/min user, 3K/min company) | Não implementado |
| **PII Masking** | 4 camadas (regex, LLM strip, Sentry scrub, Presidio NER) | Não evidenciado |
| **Prompt Injection** | `check_input_security` em POST/PUT agent-facing | Não evidenciado |
| **Sentry PII** | `before_send` hook + `send_default_pii=False` | Não integrado |
| **LGPD/Compliance** | 3 domínios dedicados (lgpd, consent, data_subject), Migration 060 (PII encryption + TTL) | Não evidenciado no código (admin tem 63 páginas de compliance UI sem backend) |
| **Hardcoded Secrets** | Nenhum em app/ (scripts utilitários têm mocks) | `guest:guest` RabbitMQ default, `ALLOWED_BRANDS` hardcoded (data_collector) |
| **RCE Risk** | Nenhum | `rails-exec` tool no ats_mcp — **RCE potencial** |
| **CI Security Scan** | bandit (Python SAST) | Brakeman (Rails SAST) |

---

### 24.6 Infraestrutura & Deploy — Comparativo

| Dimensão | Replit | wedocc2026 |
|----------|-------|-----------|
| **Containers** | 3 Dockerfiles (API, prod multi-stage, worker) + 2 docker-compose | Dockerfile (Rails) + Dockerfile (v5 interview_ai) + docker-compose workers |
| **Prod Config** | Multi-stage, non-root (`appuser`), healthcheck, `alembic upgrade head` no startup | Rails: multi-stage, non-root, bootsnap — bem configurado |
| **Terraform/IaC** | `terraform/gcp/` — Cloud Run us-central1 | Deploy docs mencionam GCP Cloud Run + GKE Autopilot (v5) |
| **Health Probes** | Kubernetes-ready: `/health` + `/health/ready` + `/health/live` | Não evidenciado |
| **DB Pool** | asyncpg pool 20/10, pre_ping, recycle 3600s | Rails db_pool 10/30 sem pooling externo |
| **Redis** | Cache semântico (24h), router (1h), rate limit, sessions, Celery broker | Sidekiq (Rails) |
| **Env Vars** | Centralizadas via pydantic-settings, validação na startup | `os.getenv` + `python-dotenv` (v5), Rails credentials |
| **Backup** | Não documentado (Cloud SQL managed?) | Não documentado |
| **SSL** | Strip de `sslmode=` — precisa config manual | `sslmode: require` em prod (Rails OK) |
| **Deps Pinning** | Pinned (pyproject.toml + package.json) | Rails Gemfile.lock OK; **data_collector sem pinning** |

---

### 24.7 Testes & Qualidade — Comparativo

| Dimensão | Replit | wedocc2026 |
|----------|-------|-----------|
| **Backend Tests** | 388 files, pytest + pytest-asyncio, gate 45% | v5: 102 files (fairness, hallucination); Rails: 34 spec files; data_collector: **0 testes** |
| **Frontend Tests** | 1.026 test files, Vitest + Playwright | ats_front: Playwright + Histoire; admin: não evidenciado |
| **Coverage Gate** | Backend 45%, Frontend 35% | Não definido |
| **Domínios com testes** | 11 de 57 (~19%) | v5: cobertura extensiva; Rails: ~5 model specs |
| **AI/LLM Tests** | DeepEval, Ragas, golden datasets, LLM-as-judge | Fairness e hallucination patterns no v5 (valor como referência) |
| **Load Tests** | Locust: 6 cenários, 4 perfis, SLAs definidos — **não no CI** | Não evidenciado |
| **Security Tests** | Red teaming, PII, prompt injection suites | Brakeman (Rails SAST) |
| **E2E** | Playwright (separado do CI) | Playwright disponível no ats_front |
| **Storybook** | Ativo + Chromatic | Histoire (Vue component playground) |

---

### 24.8 Observabilidade — Comparativo

| Dimensão | Replit | wedocc2026 |
|----------|-------|-----------|
| **Error Tracking** | Sentry (backend + frontend, PII scrubbing) | Não integrado |
| **LLM Tracing** | LangSmith (input/output, tokens, latency, costs) | Não evidenciado |
| **Metrics** | Prometheus endpoint `/metrics` (circuit_breaker_state, fairness_blocks, agent_duration) | Não evidenciado |
| **Dashboards** | Definidos (Agent Latency, LLM Costs, Circuit Breakers, Drift) — Grafana **não deployed** | Não evidenciado |
| **Alertas** | Teams webhook (circuit breaker open) | Não evidenciado |
| **SLOs** | 18+ serviços com targets (ex: Anthropic 99.9%) | Não definidos |
| **Drift Detection** | Serviço de detecção de variações em comportamento/custos | Não evidenciado |
| **Agent Monitoring** | API dedicada com health scores (Gold/Silver/Bronze) | Não evidenciado |
| **OpenTelemetry** | Setup básico em `app/observability/` | Não evidenciado |

---

### 24.9 Análise Detalhada — Repos wedocc2026

#### ats_api (Rails 7.1) — Bridge Ativo

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| Multi-tenancy | Apartment gem (schema-based), `Account`/`User` excluídos (global). Elevator **comentado** | ALTO |
| Auth | JWT HS256 24h, `authorize_request` duplicado em 2 controllers | MEDIO |
| CORS | Hardcoded `http://localhost:3000` | ALTO |
| CSP | **Toda comentada** | ALTO |
| RabbitMQ | Sneakers `guest:guest` default | MEDIO |
| Models | 18 (Account, User, Job, Candidate, Apply, SelectiveProcess, etc.) | OK |
| Migrations | 20 | OK |
| Specs | 34 files (5 model, rest request specs) | MEDIO |
| CI | Brakeman + importmap audit + RuboCop — **sem testes no CI** | MEDIO |
| Docker | Multi-stage, non-root, bootsnap — bem configurado | OK |
| Branches | 44 branches (muitos develop-* ativos: felipe, giovanni, victhor) | INFO |

#### ats_front (Nuxt 3 + Vue 3 + Vuetify) — Frontend Ativo

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| Branch | **Todo código em `develop`** — `main` tem só `.gitignore` | ALTO (workflow) |
| Stack | Nuxt 3, Vue 3, Vuetify, Pinia, TipTap WYSIWYG, ActionCable, vuelidate | OK |
| Tamanho | 904 files: 537 Vue, 107 TS, 42 docs | OK |
| Páginas | 34 (auth, dashboard, candidates, jobs, evaluations, interviews, settings, admin) | OK |
| Componentes | 147 | OK |
| Composables | 59 | OK |
| Stores | 18 Pinia | OK |
| Features | 357 feature files | OK |
| Backend | Rails (:8080) + Python AI (:8001) via `runtimeConfig` | OK |
| Testing | Playwright + axe-core (accessibility) | BOM |

**CORREÇÃO v3:** Este frontend era listado como "Morto" na versão anterior. **Incorreto.** O branch `develop` é o branch de trabalho principal com 39 branches feature ativas (WT-1592, WT-1598, etc.) e último push em 2026-04-09.

#### recruiter_agent_v5 (Python/LangGraph) — Referência

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| Vendor Lock-in | 100% Gemini (`google-generativeai==0.8.3`, `langchain-google-genai==2.0.8`) | CRITICO |
| CI/CD | **Nenhum GitHub Actions** (tem `.github/instructions/` para Copilot) | ALTO |
| Tests | 102 files (fairness, hallucination prevention, security patterns) | BOM |
| Agents | 7 (intent, planner, validator, executor, processor, formatter, autonomous) | OK |
| Tools | 21 tool files | OK |
| Deps | Stack mista: LangChain + Celery + Streamlit + Flask | MEDIO |
| Files | 912 arquivos (CORREÇÃO: v2 dizia 834) | OK |

**Valor para LIA:** Catálogo de capabilities (60+ queries em `PRODUCT_CAPABILITIES.md`), patterns de testes de fairness/hallucination.

#### wedotalent-admin (Next.js) — Painel Admin/Compliance

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| Stack | Next.js + React + Shadcn/Radix + Tailwind (mesma stack do Replit) | OK |
| Tamanho | 438 files (177 TSX, 168 TS, 2 CSS) | OK |
| Páginas | **63 páginas**: clientes (18 sub-pages), compliance (30+ sub-pages), monitoring | OK |
| Componentes | 103 | OK |
| Compliance | LGPD, SOC-2, SOX, ISO-27001, bias audit, trust center, DPO, portal titular, SoD audit | OK |
| Reuso | Mesmo stack Shadcn/Radix/Tailwind do Replit — possibilidade de merge | INFO |

**CORREÇÃO v3:** Anteriormente listado como "Desconhecido". É um painel admin de compliance/governance com escopo extenso cobrindo áreas ainda não implementadas no Replit (SOC-2, SOX, ISO-27001, SoD audit, trust center).

#### data_collector (Python) — Pipeline de Dados

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| Testes | **0 testes funcionais** | CRITICO |
| Deps | `requirements.txt` **sem version pinning** | ALTO |
| Config | `ALLOWED_BRANDS` hardcoded | MEDIO |
| Workers | 3 (apply_sender, job_sender, selective_process_sender) → enviam para Rails | OK |

#### ats_mcp (TypeScript MCP Server) — Dev Tooling

| Aspecto | Finding | Severidade |
|---------|---------|-----------|
| RCE | `rails-exec` tool permite execução remota — **RCE potencial** | CRITICO |
| Tools | 8: Jira, Analyze Project, Find Files, Read Replit, Map Replit, ATS Health, Rails Exec | OK |
| Path traversal | `config.json` com paths sem validação | ALTO |

#### wedo-nuxt — Protótipo (77 files, Nuxt 3 + Vuetify, `liaTheme` customizado, nenhum risco)
#### reembolsointeligente — Morto (0 files, repo vazio)

---

### 24.10 Riscos Sistêmicos — Por Produto

#### Riscos do Produto Replit

| # | Risco | Severidade | Detalhes |
|---|-------|-----------|---------|
| R1 | **Rails bridge sem timeline** | ALTO | ~30+ arquivos marcados "will be deleted" sem data. Se Rails cai, fallback silencioso pode mascarar perda de dados |
| R2 | **Voice sem abstração** | ALTO | LLM e embedding têm factory, mas voice é Gemini-hardcoded. Mudança de preço/API = rewrite forçado |
| R3 | **LLM costs sem hard limit** | MEDIO | `tenant_budget` tracking existe mas sem circuit breaker por gasto |
| R4 | **Backup não documentado** | CRITICO | Nenhum script/referência a Cloud SQL automated backups |
| R5 | **Coverage baixo** | ALTO | 45%/35% muito abaixo do recomendado (>80%). 81% dos domínios sem testes diretos |
| R6 | **Prometheus/Grafana não deployed** | ALTO | Métricas definidas no código mas sem dashboard/alertas funcionais |
| R7 | **FairnessGuard enforcement seletivo** | ALTO | Cobre JD e rejeição, mas triagem/ranking/sourcing podem não estar protegidos |
| R8 | **Mapa funcional incompleto** | MEDIO | 32 páginas sem mapa de "página → status funcional". Bugs em talent pools e interviews |
| R9 | **N+1 queries** | ALTO | Nenhum uso de eager loading (joinedload/selectinload) em relationships |
| R10 | **SSL asyncpg manual** | ALTO | Strip de `sslmode=` — produção GCP requer SSL explícito |

#### Riscos do Produto wedocc2026

| # | Risco | Severidade | Detalhes |
|---|-------|-----------|---------|
| W1 | **ats_front em branch errado** | ALTO | Todo código em `develop`, `main` vazio. Deploy/CI pode mirar no branch errado |
| W2 | **v5 vendor lock-in Gemini** | CRITICO | 100% Gemini sem abstração. Inviável como base para produção multi-provider |
| W3 | **v5 sem CI/CD** | ALTO | 912 arquivos sem pipeline de qualidade |
| W4 | **data_collector sem testes** | CRITICO | Pipeline de dados com 0 testes + deps sem pinning |
| W5 | **ats_mcp RCE** | CRITICO | `rails-exec` tool = Remote Code Execution se exposto |
| W6 | **Rails CSP desabilitada** | ALTO | Content Security Policy toda comentada |
| W7 | **Rails tenant elevator comentado** | ALTO | Apartment configurado mas sem middleware de routing automático |
| W8 | **Rails CORS localhost-only** | ALTO | Sem configuração para produção |

#### Riscos Cruzados (ambos produtos)

| # | Risco | Detalhes |
|---|-------|---------|
| C1 | **Gap Guide vs código** | WeDO Guide v3.3 documenta 13 Crenças, 8 Inegociáveis. FairnessGuard implementa bias, mas Crenças são referência filosófica sem enforcement |
| C2 | **Dependência Rails como bridge** | Replit depende de `ats_api` (Rails) para dados legados, mas Rails tem gaps de segurança (CSP, CORS, tenant) |
| C3 | **Admin duplicado** | `wedotalent-admin` tem 63 páginas admin com a mesma stack Shadcn/Radix do Replit — potencial de reuso/merge |

---

### 24.11 Scorecard Comparativo

| Dimensão | Replit | wedocc2026 | Vencedor |
|----------|--------|-----------|----------|
| **Escala de código** | 4.079 files | 2.678 files | Replit (1.5x) |
| **Maturidade de IA** | Factory multi-provider, fallback, budget, bootstrap, 60+ tools | 100% Gemini, 21 tools, sem abstração | **Replit** |
| **Governança IA** | FairnessGuard 3 camadas, PII 4 camadas, HITL, Policy Engine | Testes de fairness (referência), sem middleware | **Replit** |
| **Segurança** | RLS + JWT + WorkOS + Rate Limiting + Prompt Injection Guard | Apartment (comentado), JWT duplicado, CSP off, RCE no MCP | **Replit** |
| **Observabilidade** | Sentry + LangSmith + Prometheus (parcial) + SLOs + Drift Detection | Não implementado | **Replit** |
| **Testes** | 1.414 test files, Locust, DeepEval, Ragas | 149 test files, data_collector com 0 | **Replit** |
| **CI/CD** | GitHub Actions (CI completo, CD manual) | Brakeman (Rails), 0 CI no v5 | **Replit** |
| **Frontend UX** | 32 páginas, DS v4.2.1, 1.201 componentes | 97 páginas (34+63), Vuetify, TipTap WYSIWYG, Histoire | Complementar |
| **Admin/Compliance** | Parcial (domínios lgpd, consent, data_subject) | 63 páginas admin (SOC-2, SOX, ISO-27001, LGPD completo) | **wedocc2026** |
| **Docker/Deploy** | Prod-ready (multi-stage, non-root, healthcheck, Terraform) | Prod-ready (Rails), parcial (v5) | Replit |

---

### 24.12 Roadmap Consolidado

#### Fase 1 — Críticos (antes do go-live) — Esforço: 3-4 sprints

| # | Item | Produto | Dimensão | Esforço |
|---|------|---------|---------|--------|
| 1 | Corrigir `is_synced_to_calendar` Optional[bool] | Replit | Backend | P |
| 2 | Verificar `DEV_AUTO_LOGIN` guard em produção | Replit | Segurança | P |
| 3 | Limpar credenciais hardcoded em scripts | Replit | Segurança | P |
| 4 | Configurar CORS para produção | Ambos | Segurança | P |
| 5 | Implementar SSL context para asyncpg | Replit | Infra | M |
| 6 | Documentar e verificar backup Cloud SQL | Replit | DR | P |
| 7 | Definir RTO/RPO targets | Replit | DR | P |
| 8 | Corrigir N+1 queries com eager loading | Replit | Performance | M |
| 9 | Implementar CD automatizado | Replit | CI/CD | G |
| 10 | Deployar Grafana + conectar Prometheus | Replit | Observabilidade | M |

#### Fase 2 — Altos (primeiros 30 dias) — Esforço: 4-5 sprints

| # | Item | Produto | Dimensão | Esforço |
|---|------|---------|---------|--------|
| 11 | Migrar ~5 arquivos com LLM bypass direto para factory | Replit | IA | M |
| 12 | Expandir FairnessGuard para triagem/ranking/sourcing | Replit | Governança | M |
| 13 | Corrigir talent pools endpoints | Replit | Backend | M |
| 14 | Criar VoiceProviderABC | Replit | IA | M |
| 15 | Subir coverage gate para 60%/50% | Replit | Testes | G |
| 16 | Integrar Locust smoke ao CI | Replit | Performance | P |
| 17 | Adicionar Playwright ao CI | Replit | Testes | M |
| 18 | Integrar PagerDuty/OpsGenie | Replit | Observabilidade | M |
| 19 | Implementar budget hard limits por tenant | Replit | IA | M |
| 20 | Merge `ats_front` develop → main | wedocc2026 | Workflow | P |

#### Fase 3 — Médios (60-90 dias) — Esforço: 5-7 sprints

| # | Item | Produto | Dimensão | Esforço |
|---|------|---------|---------|--------|
| 21 | Deprecar ~10 domínios stub | Replit | Arquitetura | P |
| 22 | Normalizar feature parity LLM providers | Replit | IA | M |
| 23 | Definir timeline remoção Rails layer | Ambos | Arquitetura | G |
| 24 | Squash Alembic migrations | Replit | Backend | M |
| 25 | Mover audit logs para storage separado | Replit | Governança | M |
| 26 | Padronizar prompts com YAML templates | Replit | IA | G |
| 27 | Migrar `app/services/` (shims → domínios) | Replit | Arquitetura | G |
| 28 | Criar testes para domínios sem cobertura | Replit | Testes | GG |
| 29 | Completar OpenTelemetry end-to-end | Replit | Observabilidade | G |
| 30 | Avaliar merge de `wedotalent-admin` páginas no Replit | Ambos | Frontend | G |

#### Fase 4 — Backlog — Esforço: ongoing

| # | Item | Produto | Dimensão | Esforço |
|---|------|---------|---------|--------|
| 31 | UI de configuração LLM por tenant | Replit | IA | M |
| 32 | Consolidar micro-domínios | Replit | Arquitetura | M |
| 33 | Habilitar CSP no Rails | wedocc2026 | Segurança | P |
| 34 | Pinar deps do data_collector + adicionar testes | wedocc2026 | Qualidade | M |
| 35 | Revisar segurança do `rails-exec` no ats_mcp | wedocc2026 | Segurança | P |
| 36 | Migrar domínios críticos para LangGraph | Replit | IA | GG |
| 37 | Resolver npm audit findings | Replit | Segurança | P |
| 38 | Planejar failover multi-região | Replit | DR | GG |
| 39 | Arquivar repos mortos (reembolsointeligente) | wedocc2026 | Limpeza | P |
| 40 | Adicionar CI ao recruiter_agent_v5 | wedocc2026 | CI/CD | M |

---

## 25. Status de Integração Completa — Snapshot 15/abril/2026

> **Contexto:** Esta seção consolida o estado real da integração entre todos os componentes do ecossistema (frontend, FastAPI, Rails, Admin Panel, Data Collector, GCP) baseado em auditoria direta do código nos 4 repos envolvidos, cruzada com o [`RELATORIO_SESSAO_4_2026-04-15.md`](docs/audit/fase7-execucao/RELATORIO_SESSAO_4_2026-04-15.md). Substitui e atualiza o estado descrito nas Seções 9 e 16 (que refletiam o estado de abril/07).
>
> **Score geral:** 72/90 items do `MIGRATION_PLAN` concluídos (80%). Infraestrutura GCP operacional. Dois blockers críticos identificados para fechamento total.

### 25.1 Sumário Executivo

| Métrica | Valor |
|---|---|
| Items concluídos (MIGRATION_PLAN) | **72/90 (80%)** |
| Items pendentes | 18 (9 DevOps/manual, 3 OTEL, 4 Wave 6 escala, 2 follow-ups Sprint 7) |
| Sprints 100% | 12/12 (Sessão 4 fechou Sprint 1, 7, 8) |
| Commits cross-repo (sessão 4) | 10 (7 wedotalent + 3 ats-api) |
| Blockers críticos para go-live | **2** (ver 25.3 e 25.4) |
| LLM Factory | 95% pronto (3 micro-tasks pendentes) |
| RabbitMQ / Sentry / OTEL / CORS / Cloud Run | ✅ Operacionais |

**Os dois blockers críticos:**
1. **Admin Panel não cria tenant no Rails** (Seção 25.3) — multi-tenancy fica inconsistente. Cliente criado no admin não consegue usar ATS.
2. **Follow-up F-1 do Sprint 7** (Seção 25.4) — endpoint `GET /v1/candidates?fork_uuid=<uuid>` ausente no Rails; `find_candidate_by_fork_uuid` ausente no Python client. Sprint 7.3 só funciona pela metade.

Nenhum dos dois é bloqueio de ambiente (não precisa de DevOps) — ambos são código novo a ser implementado.

---

### 25.2 Status por Área

#### 25.2.1 Frontend — `plataforma-lia` (Next.js 15)

| Item | Status | Evidência / Nota |
|---|---|---|
| WorkOS SSO implementado | ✅ | `src/lib/auth/workos.ts` |
| Multi-tenancy lógica (org injection) | ✅ | `src/lib/api/auth-headers.ts` |
| Backend proxy `/api/backend-proxy/*` | ✅ | `createProxyHandlers` + FastAPI/Rails target |
| Build em produção (`next build`) | ✅ | P2 resolvido |
| Docker + Cloud Run | ✅ | `plataforma-lia/Dockerfile` multi-stage standalone |
| Sentry DSN prod | ❌ | Falta configurar `NEXT_PUBLIC_SENTRY_DSN` no Secret Manager GCP |
| WorkOS prod redirect URIs | ❌ | Registrar `https://wedotalent.cc/api/auth/workos/callback` no dashboard WorkOS |
| Bugs recentes (15/04) | ✅ | `c5aad4ab` Kanban `t`; `da000dd1` Funil `ensureServerReady` regressão do #195 |

#### 25.2.2 Backend FastAPI — `lia-agent-system`

| Item | Status | Evidência |
|---|---|---|
| Sprint 1 — Tenant Isolation (Rails) | ✅ | Commit `1639beb` |
| Sprint 7 — CRUD Migration (deprecation layer) | ✅ | Commits `652b5028`, `f002e79c`, `07fa70f7` |
| Sprint 8 — E2E Tests (22 testes) | ✅ | Commits `6f15aaa9`, `03db3fa0`, `0252ef33`, `a7240840` — rodam com env vars setadas |
| LLM Factory (Claude + Gemini + OpenAI) | ✅ 95% | `app/shared/providers/llm_factory.py` — 3 providers + circuit breaker + multi-tenant |
| RabbitMQ producer (`aio_pika`) | ✅ | `app/shared/messaging/rabbitmq_producer.py:36-47` |
| Sentry SDK | ✅ | `sentry-sdk[fastapi]==2.19.2` em `requirements.txt` |
| OpenTelemetry tracer | ✅ custom | `app/shared/tracing.py:1-70` — LightweightTracer + OTLP exporter |
| CORS | ✅ | `app/main.py:434-435` via `CORSMiddleware`, env-driven |
| Logs estruturados (JSON) | ❌ | `structlog` ausente em `requirements.txt` |
| `find_candidate_by_fork_uuid` no Rails client | ❌ | **Follow-up F-2** — não implementado em `wedotalent_rails.py` |
| Prompt versioning em Git | ⚠️ | 12 YAML em `app/prompts/domains/` mas sem hash/version/rollback |

#### 25.2.3 Backend Rails — `ats-api-copia`

| Item | Status | Evidência |
|---|---|---|
| Migrations Sprint 1 (account_id, fork_uuid, users.email index) | ✅ código | `db/migrate/20260415120001-3_*.rb` commit `1639beb` + `3668eae` |
| `rails db:migrate` em staging/prod | ❌ **BLOCKER DevOps** | Item 1.3 do plano — não aplicado ainda |
| `schema.rb` atualizado | ❌ | Schema version `2025_07_14_142059` vs max migration `20260415120003` — rodar `bin/rails db:schema:dump` pós-migrate |
| JWT 24h (HS256, `secret_key_base`) | ✅ | `app/controllers/application_controller.rb:21-32` |
| Sneakers consumer + 6 event handlers | ✅ | `app/workers/lia_events_worker.rb` — LIA-E03 versioning, DLQ, ack/reject/requeue |
| CORS (`rack-cors`) | ✅ env-driven | Commit `cfdd2ee` (item 0.2) |
| Sentry | ✅ | `config/initializers/sentry.rb:1-23` |
| `POST /v1/accounts` (criar tenant) | ❌ **BLOCKER produto** | Endpoint não existe — ver 25.3 |
| `GET /v1/candidates?fork_uuid=<uuid>` | ❌ **Follow-up F-1** | Sprint 7.3 assumiu existência; nunca foi implementado |
| Backfill `candidates.account_id` | ⚠️ | Task `candidates:backfill_account_id` criada; roda após 1.3 |

#### 25.2.4 Admin Panel — `wedotalent-admin-copia` ⚠️ GAP CRÍTICO

| Item | Status | Evidência |
|---|---|---|
| Criação de `ClientAccount` (FastAPI) | ✅ | `clients_crud.py:173` |
| Provisionamento WorkOS Organization | ✅ | `clients_crud.py:179` |
| Clone templates de email do cliente | ✅ | `clients_crud.py:182` |
| Welcome email | ✅ | via Mailgun (quando `MAILGUN_API_KEY` setado) |
| Sync HubSpot (Company + Deal) | ✅ | `clients_crud.py:204` |
| **Criação de `accounts` no Rails** | ❌ **CRÍTICO** | **Não chama Rails em momento algum** — ver 25.3 |

#### 25.2.5 Data Collector — `data-collector-copia`

| Item | Status | Evidência |
|---|---|---|
| RabbitMQ consumer (`pika`) | ✅ | `queues/connection.py:17-20` |
| Integrações Gupy / Pandapé / Merge | ✅ | ETL popula `applies`/`selective_processes` |
| Multi-tenant awareness | ⚠️ DT-001 | Consome `DEFAULT_ACCOUNT_ID` — workaround single-tenant; não cria tenant |

#### 25.2.6 GCP Infrastructure

| Item | Status | Nota |
|---|---|---|
| Cloud Run deploy workflow (FastAPI + Frontend) | ✅ | `.github/workflows/deploy.yml` com `gcloud run deploy` |
| Secret Manager (via `--set-secrets` no Cloud Run) | ✅ | DATABASE_URL, REDIS_URL já mapeados |
| RabbitMQ (CloudAMQP ou VM) | ✅ operacional | Conexão via `RABBITMQ_URL` |
| Secrets **pendentes** em staging/prod | ❌ | `MAILGUN_API_KEY`, `SENTRY_DSN`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `CORS_ORIGINS`/`CORS_ALLOWED_ORIGINS` |
| Alertas Cloud Monitoring (CRITICAL + WARNING) | ❌ | Items 4.7 + 10.4 do plano — criar policies |
| Logs estruturados (Cloud Logging) | ⚠️ | Request ID propagado, mas sem JSON structured logging |

---

### 25.3 Blocker #1 — GAP CRÍTICO: Admin Panel → Rails Tenant

**Descoberto em:** 2026-04-15 (auditoria cruzada deste documento)

#### O problema

Quando um admin cria um novo cliente no `wedotalent-admin-copia`, o fluxo executa:

```
POST /clients → FastAPI (wedotalent02202026)
  ├─ 1. ClientAccount no Postgres FastAPI     ✅  clients_crud.py:173
  ├─ 2. Organization no WorkOS (SSO)           ✅  clients_crud.py:179
  ├─ 3. Clone templates de email               ✅  clients_crud.py:182
  ├─ 4. Welcome email via Mailgun              ✅  clients_crud.py:~190
  ├─ 5. Sync HubSpot (Company + Deal)          ✅  clients_crud.py:204
  └─ 6. Criar Account no Rails                 ❌  NÃO ACONTECE
```

**Consequência prática:** Cliente criado no admin **não consegue acessar vagas/candidatos/processos**. O `TenantScoped` concern do Rails (`app/controllers/concerns/tenant_scoped.rb:13`) filtra tudo por `@current_user.account_id` — se o `account` nunca foi criado no Rails, `current_user.account_id` aponta pra inexistente, queries retornam empty, UI mostra "sem dados".

**Rails não tem endpoint para criar account via API.** Hoje a criação é via `db/seeds.rb` (idempotent `find_or_create_by`) ou `rails console` — processo manual.

#### Opções de solução (escolher 1)

**Opção A — FastAPI chama Rails (recomendada):**
1. **Rails:** criar endpoint `POST /v1/admin/accounts` (protegido por `INTERNAL_API_SECRET` ou JWT com role admin). Aceita `{name, tenant_slug, client_account_id}` e cria `Account` + link com `ClientAccount` FastAPI. **Atenção arquitetural:** Rails usa **Apartment gem para multi-schema Postgres** (ver `accounts.tenant`/`staging_tenant` na tabela). O endpoint precisa provisionar o schema via `Apartment::Tenant.create(tenant_slug)` na mesma transação — criar só o registro `Account` não é suficiente.
2. **FastAPI:** adicionar em `clients_crud.py` após criar `ClientAccount`:
   ```python
   await rails_client.create_account(
       name=client.name,
       tenant_slug=slugify(client.name),
       client_account_id=str(client.id)
   )
   ```
3. Rollback: se Rails falhar, fazer compensating action (deletar ClientAccount + WorkOS Org + HubSpot Company).
4. Esforço: ~2 sprints (1 Rails + 1 Python + testes de isolamento cross-service).

**Opção B — Webhook event-driven:**
1. FastAPI emite evento `tenant.created` no RabbitMQ após criar ClientAccount.
2. `LiaEventsWorker` no Rails escuta o evento e cria o `Account` assíncrono.
3. Vantagem: desacoplado, recuperável via DLQ.
4. Desvantagem: eventual consistency — cliente pode tentar usar a plataforma antes do Account existir no Rails.
5. Esforço: ~1.5 sprints.

**Opção C — Unificar fonte de verdade:**
- Definir Rails como fonte única de `account` (já é fonte única de vagas, candidatos, processos) e remover duplicação em FastAPI.
- FastAPI vira cliente (lê de Rails via adapter) em vez de manter `ClientAccount` próprio.
- Alinhado com memória de projeto: *"CRUD moving to Rails, IA stays in Python"*.
- Esforço: ~3-4 sprints (mais arquitetural).

**Recomendação:** Começar com Opção A (tátic, rápida) e planejar Opção C para roadmap.

---

### 25.4 Blocker #2 — Follow-ups Sprint 7 não concluídos (F-1 + F-2)

Sprint 7.3 do `MIGRATION_PLAN` entregou migration + adapter wiring, mas os dois lados ficaram pela metade:

**F-1 — Rails:** criar endpoint `GET /v1/candidates?fork_uuid=<uuid>`
- **Arquivo:** `ats-api-copia/app/controllers/v1/users/candidates_controller.rb#index`
- **Escopo:** whitelist `fork_uuid` em permitted params + filtro `Candidate.where(fork_uuid: params[:fork_uuid])` quando presente
- **Esforço:** ~30min + teste

**F-2 — Python:** implementar `find_candidate_by_fork_uuid(fork_uuid)` em `WeDOTalentATSClient`
- **Arquivo:** `wedotalent02202026/lia-agent-system/app/domains/ats_integration/services/ats_clients/wedotalent_rails.py` (587 linhas, falta esse método)
- **Escopo:** `async def find_candidate_by_fork_uuid(self, fork_uuid: str)` → `GET /v1/users/candidates?fork_uuid=<uuid>` → desempacota primeira match
- **Usado por:** `rails_adapter.py:498` (já chama, falha graciosa hoje com `getattr(..., None)`)
- **Esforço:** ~30min + teste

Enquanto F-1 + F-2 não existirem, qualquer lookup de candidato via UUID retorna `None` — plataforma continua funcionando (fallback para IDs bigint), mas cross-system lookup fica sem coverage.

---

### 25.5 LLM Factory — Status 95% (3 micro-tasks para fechar)

**Arquitetura atual (confirmada em código):** `app/shared/providers/llm_factory.py` + `ProviderContainer` + `TenantProviderRegistry`.

| Dimensão | Status | Evidência |
|---|---|---|
| 3 providers (Claude `sonnet-4-6`, Gemini `2.5-flash`, OpenAI `gpt-4o`) | ✅ | `llm_claude.py:29`, `llm_gemini.py:23`, `llm_openai.py:15` |
| Fallback chain com circuit breaker | ✅ | Default `["gemini","claude","openai"]` em `llm_factory.py:19`, breaker em cada provider |
| Multi-tenant com API keys isoladas | ✅ | `TenantProviderRegistry` em `llm_factory.py:93-150` |
| Token budget por request + por dia | ✅ | `token_budget_service.py:20-94` — plans starter/pro/business/enterprise |
| PII stripping obrigatório | ✅ | `llm.py:333-359` + `strip_pii_for_llm_prompt()` |
| Audit logs estruturados `[LLM-AUDIT]` | ✅ | `llm.py:239-253` |
| Dashboard usage por tenant (endpoint) | ❌ | Não existe `GET /api/v1/admin/billing/usage-by-tenant` |
| Métricas Prometheus de latência/provider | ❌ | `_METRICS_AVAILABLE = False` |
| Retry automático no ClaudeLLMProvider | ⚠️ | Só Gemini tem `@retry` — Claude só tem circuit breaker |

**Para fechar LLM Factory como produto (esforço ~2h):**
1. Endpoint `/api/v1/admin/billing/usage-by-tenant` (~1h)
2. Adicionar `@retry(stop_after_attempt=2, wait_exponential)` em `ClaudeLLMProvider` (~30min)
3. Runbook curto documentando fallback chain em `docs/ops/llm-runbook.md` (~30min)

Itens opcionais (pós-fechamento): métricas Prometheus, prompt versioning em Git, error handling por tipo (401 vs 429 vs 5xx).

---

### 25.6 CHECKLIST CONSOLIDADO — Por Time

> Use como board de acompanhamento. Ordem dentro de cada time é por prioridade (top = mais urgente).

#### 🔧 DevOps / Infraestrutura GCP

- [ ] **CRÍTICO — Item 1.3:** Rodar `bundle exec rails db:migrate` em staging, depois `rake candidates:backfill_account_id DRY_RUN=true`, depois `rake candidates:backfill_account_id`, depois `rails runner 'p Candidate.where(account_id: nil).count'` — esperado 0
- [ ] **Secrets pendentes** em Secret Manager GCP (staging + prod):
  - [ ] `MAILGUN_API_KEY` (sandbox em staging + whitelist `e2e-test@wedotalent.cc`)
  - [ ] `SENTRY_DSN` (Python + Rails + Next.js — 3 variáveis)
  - [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` (Cloud Trace ou Jaeger)
  - [ ] `CORS_ORIGINS` (Python, lista JSON) + `CORS_ALLOWED_ORIGINS` (Rails, CSV)
  - [ ] `REDIS_ENCRYPTION_KEY` (gerar com Fernet)
  - [ ] `TWILIO_*` já setado em dev — migrar para Secret Manager GCP
- [ ] **Alertas Cloud Monitoring** (itens 4.7 + 10.4):
  - [ ] CRITICAL: error rate >5%, latência p95 >2s, circuit breaker open, worker DLQ >100
  - [ ] WARNING: error rate >1%, latência p95 >1s
- [ ] **Rodar E2E tests em staging** (Sprint 8) com env vars dos fixtures — 22 testes / 4 suites — ver seções 2.3 do `RELATORIO_SESSAO_4`
- [ ] **Revogar API Key Atlassian** (item 0.1) — admin.atlassian.com
- [ ] **Monitorar deprecation logs** por 2-4 semanas: `grep "\[rails-migration\] deprecated endpoint hit"`
- [ ] **Flipar `STRICT_RAILS_ONLY=true`** em prod após zero hits por 2 semanas consecutivas (sunset programado 2026-07-31)
- [ ] **Regenerar `schema.rb`** pós-migrate: `cd ats-api-copia && bin/rails db:schema:dump`

#### 🦊 Backend Rails (`ats-api-copia`)

- [ ] **CRÍTICO — F-1:** Adicionar filtro `fork_uuid` em `v1/users/candidates_controller.rb#index` + whitelist em permitted params
- [ ] **CRÍTICO — Endpoint tenant:** Criar `POST /v1/admin/accounts` (protegido por `INTERNAL_API_SECRET`) para Opção A do gap admin — ver 25.3
- [ ] Follow-up migration `change_column :candidates, :account_id, :bigint, null: false` (DT-009) — aplicar após backfill em staging confirmar zero NULL
- [ ] Considerar endpoint `POST /v1/sessions/refresh` para evitar re-login a cada 24h (gap de UX identificado)

#### 🐍 Backend FastAPI (`lia-agent-system`)

- [ ] **CRÍTICO — F-2:** Adicionar `async def find_candidate_by_fork_uuid(fork_uuid: str)` em `app/domains/ats_integration/services/ats_clients/wedotalent_rails.py` (depende de F-1)
- [ ] **CRÍTICO — Criar `rails_client.create_account()`** e chamar em `clients_crud.py` após `ClientAccount` create — ver 25.3 Opção A
- [ ] **LLM Factory fechamento (3 micro-tasks):**
  - [ ] Endpoint `/api/v1/admin/billing/usage-by-tenant` (~1h)
  - [ ] `@retry` decorator em `ClaudeLLMProvider` (~30min)
  - [ ] Runbook `docs/ops/llm-runbook.md` (~30min)
- [ ] **OTEL spans** (desbloqueados após Secret `OTEL_EXPORTER_OTLP_ENDPOINT`):
  - [ ] Item 4.1: agent spans `agent.{domain}.process` nos 14 ReAct agents
  - [ ] Item 4.2: LLM spans `llm.call` com tokens/cost
  - [ ] Item 4.3: handoff spans `router.handoff` no `CascadedRouter`
- [ ] Adicionar `structlog` em `requirements.txt` + middleware de JSON logging
- [ ] `libs/notification_service.py:905` — remover `raise Exception()` genérico (DT-003)

#### 🎨 Frontend (`plataforma-lia`)

- [ ] Configurar `NEXT_PUBLIC_SENTRY_DSN` prod no Secret Manager
- [ ] Registrar redirect URIs de prod no dashboard WorkOS (`https://wedotalent.cc/api/auth/workos/callback`)
- [ ] Atualizar Teams Tab URL para prod (após DNS apontar)
- [ ] Headers de segurança em `next.config.js` (CSP experimental por ora)
- [ ] P5 pendente: 4 arquivos com vars Replit-only (fallbacks): `workos.ts`, `jira-service.ts`, `shared_searches.py`, `email_adapter.py`

#### 🏢 Admin Panel (`wedotalent-admin-copia`)

- [ ] **CRÍTICO — Integração Rails:** Após Rails expor `POST /v1/admin/accounts`, atualizar flow do admin para validar que tenant foi criado com sucesso (retry + rollback). Ver 25.3.
- [ ] Expor indicador visual no admin sobre status de cada integração (FastAPI / WorkOS / HubSpot / Rails) — hoje é silencioso
- [ ] Documentar fluxo completo de criação de cliente em `docs/admin/new-client-flow.md`

#### 🧪 QA / Produto

- [ ] Rodar Sprint 8 E2E em staging (pré-requisito: DevOps completou checklist acima)
- [ ] Validar isolamento multi-tenant: criar 2 clientes completos (admin → ClientAccount + WorkOS + HubSpot + **Rails Account**), logar com cada, confirmar que não se veem
- [ ] Testar fluxo cross-system candidate: buscar por `fork_uuid` (depois de F-1 + F-2) retorna match correto
- [ ] Validar que deprecation layer Sprint 7 loga corretamente endpoints antigos sendo chamados

---

### 25.7 Ordem Recomendada de Ataque

**Semana 1 (DevOps):** Passos 1-4 do checklist de ativação (env vars + migrations + alertas). Desbloqueia tudo.

**Semana 2 (Rails team):** F-1 (endpoint `fork_uuid`) + endpoint `POST /v1/admin/accounts` (desbloqueia gap do admin panel).

**Semana 3 (Python team):** F-2 (`find_candidate_by_fork_uuid` no client) + integração admin→Rails em `clients_crud.py` + LLM Factory fechamento (3 micro-tasks).

**Semana 4 (Frontend + QA):** configurações prod + 22 E2E em staging + validação multi-tenant completa.

**Semana 5+:** OTEL spans (4.1-4.3), observabilidade, monitor deprecation até sunset 31/jul.

---

*Seção 25 adicionada em 2026-04-15 por auditoria cruzada dos 4 repos + RELATORIO_SESSAO_4.md*
*Fontes: `clients_crud.py:134-222`, `tenant_scoped.rb:12-21`, `wedotalent_rails.py`, `llm_factory.py`, `deploy.yml`, migrations `db/migrate/20260415120001-3_*.rb`, commits `1639beb`/`652b5028`/`f002e79c`/`07fa70f7`/`6f15aaa9`/`03db3fa0`/`0252ef33`/`a7240840`/`3668eae`/`9368bb0`/`c5aad4ab`/`da000dd1`*

---

*Última atualização: Abril 2026 (auditoria profunda v3 — análise comparativa Replit vs wedocc2026)*
*Fonte de dados: Código Replit (filesystem direto) + GitHub API (WeDOTalent org, 8 repos auditados)*
*Domínio: wedotalent.cc · Região GCP: us-central1*
*Produto Replit: Next.js 15 + FastAPI 0.115.5 + LangGraph 0.2.53 (4.079 files)*
*Produto wedocc2026: Rails 7.1 + Nuxt 3 + Python LangGraph (2.678 files em 8 repos)*
*Integrações: Claude, Gemini, OpenAI, WorkOS, Twilio, Deepgram, Teams, WhatsApp, Resend, Mailgun, Redis, Celery, Sentry, LangSmith, Prometheus*
*Decisão arquitetural: FastAPI (Replit) é a fonte de verdade. Rails é opt-in para dados legados. Ver Seção 2F.*
