# LIA Platform — Guia de Deploy e Fluxo de Desenvolvimento

> **Documento de referência para o time de engenharia.**
> Cobre a jornada completa: do ambiente de desenvolvimento no Replit até a produção no GCP Cloud Run, passando pelo ambiente de staging.

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
24. [AUDITORIA PROFUNDA — Production Readiness (9 Dimensões)](#24-auditoria-profunda--production-readiness-9-dimensões)
    - 24.1 [LLM Factory / Vendor Lock-in](#241-llm-factory--vendor-lock-in)
    - 24.2 [Arquitetura de IA — Domínios e Padrões](#242-arquitetura-de-ia--domínios-e-padrões)
    - 24.3 [Fairness / Bias / Governança IA](#243-fairness--bias--governança-ia)
    - 24.4 [Multi-tenancy / Segurança](#244-multi-tenancy--segurança)
    - 24.5 [Production Readiness — Erros e Estado Atual](#245-production-readiness--erros-e-estado-atual)
    - 24.6 [Arquitetura / Overengineering](#246-arquitetura--overengineering)
    - 24.7 [Design / Frontend — Consistências](#247-design--frontend--consistências)
    - 24.8 [Infraestrutura / Deploy](#248-infraestrutura--deploy)
    - 24.9 [Repos Legados (GitHub)](#249-repos-legados-github--wedotalent-org)
    - 24.10 [Roadmap de Correções Prioritizado](#2410-roadmap-de-correções-prioritizado)

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
- Observabilidade: status a levantar com o time — logs centralizados, traces e alertas podem ou não estar configurados

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
| **Backend API** | Rails: 16 controllers, **12 tabelas reais** | FastAPI: **229 endpoints**, **110 models**, 59 migrações aplicadas |
| **Frontend** | Vue/Nuxt/Vuetify: 28 features, 58 composables, 18 stores Pinia | Next.js/React/Tailwind: **36+ páginas**, Design System completo |
| **Agentes IA** | recruiter-agent-v5: 8 domains, 7 agents, Celery + RabbitMQ | LangGraph: **53 domains**, **147 services**, WSI, voice, bias audit |
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
| **Domínios de negócio** | ~5 funcionais | **53 domínios** estruturados |
| **Migrações aplicadas** | 18 de 49 | 59 migrações aplicadas, banco completo |

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

2. **O FastAPI já faz tudo que o Rails faz — e mais.** O Rails provê CRUD para ~5 entidades. O FastAPI tem 229 endpoints, 53 domínios, 147 services, toda a camada de IA, compliance e um frontend completo.

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

Criar `.github/workflows/deploy.yml` em `ats-front-copia`:

```yaml
name: Deploy LIA Frontend

on:
  push:
    branches: [develop, main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build and Push Docker Image
        run: |
          gcloud builds submit \
            --tag gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }}

      - name: Deploy to Cloud Run (Staging)
        if: github.ref == 'refs/heads/develop'
        run: |
          gcloud run deploy lia-frontend-staging \
            --image gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }} \
            --region us-central1

      - name: Deploy to Cloud Run (Production)
        if: github.ref == 'refs/heads/main'
        run: |
          gcloud run deploy lia-frontend \
            --image gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }} \
            --region us-central1
```

#### 2.4 GitHub Actions — CI/CD Agent

Mesma estrutura, para o repositório `lia-agent-system`, apontando para o serviço Cloud Run `lia-agent-staging` / `lia-agent`.

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
| `LANGCHAIN_API_KEY` | (opcional) | Secret Manager (se ativo) | Secret Manager (se ativo) | LangSmith tracing |
| `SENTRY_DSN` | (opcional) | obrigatório | obrigatório | |

---

## 9. Checklist Pré-Go-Live

### Código (Replit / time dev)

- [x] Dockerfile do `plataforma-lia` criado (`plataforma-lia/Dockerfile` — multi-stage, Node 22 Alpine, standalone)
- [x] `next.config.js` com `output: 'standalone'`, `BACKEND_URL` parametrizado nos rewrites
- [x] `.env.example` completo e documentado (todas as vars com descrição por seção)
- [ ] `lia-agent-system` aponta para `DATABASE_URL` via variável de ambiente
- [ ] GitHub Actions configurado nos dois repositórios
- [ ] Testes E2E passando no staging
- [ ] Sentry configurado e recebendo eventos de teste
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
| **Twilio Voice** | `app/api/v1/twilio_voice.py` | Ligações reais (inbound/outbound), gravação | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| **Twilio WhatsApp** | `app/domains/communication/services/whatsapp_twilio_service.py` | WhatsApp via Twilio (alternativa ao Meta API) | mesmas credenciais Twilio |

> **Ação GCP:** Habilitar as APIs `speech.googleapis.com` e `texttospeech.googleapis.com` no projeto GCP. A autenticação usa o Service Account do Cloud Run — sem API key adicional.

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

| Ferramenta | Camada | Arquivo | Config |
|---|---|---|---|
| **Sentry** | Frontend + Backend | `sentry.client.config.ts`, `sentry-sdk[fastapi]` | `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN` |
| **Cloud Logging** | Backend | automático no Cloud Run | sem config adicional |
| **LangSmith** | Agentes LLM | `app/config/langsmith.py` | `LANGSMITH_API_KEY` (opcional) |
| **APM Cloud Monitoring** | GCP | via dashboards GCP | alertas configurados manualmente |

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
| 🟡 Importante | Twilio Voice + WhatsApp | Config pendente no Replit | Adicionar `TWILIO_*` ao Secret Manager |
| 🟡 Importante | Microsoft Teams Bot | Funciona (dev mode) | Registrar webhook URL de produção no Azure Bot Service |
| 🟡 Importante | Resend (email) | Código pronto | `RESEND_API_KEY` no Secret Manager |
| 🟡 Importante | RabbitMQ | Código pronto | Provisionar CloudAMQP ou VM e2-small |
| 🟡 Importante | Sentry | Código pronto | Criar projeto Sentry, adicionar DSN |
| 🟢 Desejável | HubSpot | Código pronto, config pendente | `HUBSPOT_ACCESS_TOKEN` quando necessário |
| 🟢 Desejável | PEARCH | Código pronto, config pendente | `PEARCH_API_KEY` (contato com PEARCH) |
| 🟢 Desejável | LangSmith | Código pronto | `LANGSMITH_API_KEY` quando quiser observabilidade de agentes |
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
| **Observabilidade** | Sentry integrado no frontend |
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

#### P1 — ⚠️ PARCIALMENTE RESOLVIDO (07/04/2026): proxy routes padronizados, 11 arquivos frontend pendentes

```
CORREÇÃO APLICADA:
  Os arquivos em /api/backend-proxy/* agora usam BACKEND_URL (server-side).

  .env.local atualizado: BACKEND_URL=http://127.0.0.1:8001 (sem NEXT_PUBLIC_)

PENDENTE — 11 arquivos no frontend ainda usam NEXT_PUBLIC_BACKEND_URL ou
NEXT_PUBLIC_API_URL diretamente (fora dos proxy routes):

  1. plataforma-lia/src/components/search/smart-search-input.tsx
  2. plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanJobEditing.ts
  3. plataforma-lia/src/hooks/use-pipeline-inheritance.ts
  4. plataforma-lia/src/hooks/use-return-events.ts
  5. plataforma-lia/src/hooks/use-proactive-alerts.ts
  6. plataforma-lia/src/hooks/use-candidate-data-requests.ts
  7. plataforma-lia/src/lib/api/candidate-search.ts
  8. plataforma-lia/src/lib/api/global-search-settings.ts
  9. plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx
  10. plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx
  11. plataforma-lia/src/components/search/hooks/smartSearchConstants.ts

AÇÃO (task separada de código — fora do escopo desta documentação):
  Substituir NEXT_PUBLIC_BACKEND_URL/NEXT_PUBLIC_API_URL nestes arquivos por
  chamadas via /api/backend-proxy/* ou por BACKEND_URL (server-side only).
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

#### P4 — ⚠️ PARCIALMENTE RESOLVIDO (07/04/2026): `NEXT_PUBLIC_BACKEND_URL` nos proxy routes

```
CORREÇÃO APLICADA:
  Os arquivos em /api/backend-proxy/* agora usam BACKEND_URL (sem NEXT_PUBLIC_).

PENDENTE:
  11 arquivos fora dos proxy routes ainda expõem NEXT_PUBLIC_BACKEND_URL
  ou NEXT_PUBLIC_API_URL ao browser. Listados em P1 acima.
  Resolução como task separada de código.
```

#### P5 — IMPORTANTE: Variáveis exclusivas do Replit no código

```
O código referencia variáveis que só existem no Replit:
  - REPLIT_DEV_DOMAIN  → usado para construir URLs (domínio do preview)
  - REPL_IDENTITY      → usado para identificação do ambiente
  - WEB_REPL_RENEWAL   → flag interna do Replit

Em produção (Cloud Run), essas variáveis serão undefined.

RISCO: Pode causar erros silenciosos ou URLs quebradas.

AÇÃO AGORA: Não quebra nada (estamos no Replit).
AÇÃO ANTES DO DEPLOY: Adicionar fallbacks em cada referência:
  process.env.REPLIT_DEV_DOMAIN || process.env.APP_DOMAIN || 'wedotalent.cc'
  São poucas referências — trabalho pontual.
```

#### P6 — IMPORTANTE: WebSockets sem parametrização para produção

```
2 componentes criam WebSockets diretamente:
  1. AsyncJobProgress.tsx — progresso de tarefas assíncronas
  2. VoIPCallButton.tsx  — chamadas VoIP em tempo real

Ambos constroem a URL do WebSocket a partir do domínio atual
(window.location). Isso funciona quando frontend e backend estão
no mesmo servidor, mas em produção com serviços separados pode quebrar.

AÇÃO AGORA: Funciona como está no Replit.
AÇÃO ANTES DO DEPLOY:
  - Cloud Run suporta WebSockets (precisa habilitar)
  - Parametrizar URLs WS com env var: NEXT_PUBLIC_WS_URL
  - Ajustar 2 arquivos
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

| Área | Severidade | Problema | Ação | Quando |
|---|---|---|---|---|
| **P1: NEXT_PUBLIC leak no frontend** | 🟡 Importante | 11 arquivos fora dos proxy routes ainda usam `NEXT_PUBLIC_BACKEND_URL` ou `NEXT_PUBLIC_API_URL` diretamente | Substituir por chamadas via proxy routes ou env var server-side (task separada de código) | Antes do deploy |
| **P2: Build falha** | 🔴 Crítico | `ai-credits/page.tsx` usa `dynamic(ssr:false)` em Server Component | Adicionar `"use client"`, remover `metadata` export | **Agora** |
| **P3: DATABASE_URL** | 🔴 Crítico | Backend aponta para `localhost:5432/lia_db` — banco não existe no Replit | Corrigir para `helium/heliumdb` (banco real) | **Agora** |
| **P4: NEXT_PUBLIC leak** | 🟡 Importante | URL do backend exposta no browser via `NEXT_PUBLIC_*` nos 11 arquivos listados em P1 | Resolver junto com P1 (task separada de código) | Antes do deploy |
| **P5: Replit vars** | 🟡 Importante | `REPLIT_DEV_DOMAIN`, `REPL_IDENTITY` → undefined no Cloud Run | Adicionar fallbacks com `APP_DOMAIN` | Antes do deploy |
| **P6: WebSockets** | 🟡 Importante | URLs WS hardcoded em 2 componentes | Parametrizar com `NEXT_PUBLIC_WS_URL` | Antes do deploy |
| **Mockups pendentes** | 🟡 Importante | 6 grupos de componentes no mockup sandbox | Revisar, aprovar ou descartar, integrar | Antes do deploy |
| **WorkOS prod** | 🟡 Importante | Credenciais apontam para dev | Criar ambiente prod + redirect URIs `wedotalent.cc` | Deploy |
| **Error Boundaries** | 🟢 Desejável | Parcialmente implementado | Verificar cobertura em pages críticas | Antes do deploy |
| **Headers de segurança** | 🟢 Desejável | CSP, X-Frame-Options não configurados | Adicionar em `next.config.js` | Antes do deploy |
| **Bundle size** | 🟢 Desejável | Não auditado | Rodar `next build` e checar | Antes do deploy |
| **Testes E2E silenciosos** | 🟢 Desejável | `.catch(() => {})` mascara falhas | Remover catch silenciosos | Antes do deploy |
| **Testes E2E WorkOS real** | 🟢 Desejável | Auth fixture usa cookie bypass | Rodar com credenciais reais em CI | Deploy |

### Checklist de production readiness — Frontend

**Correções críticas (bloqueiam deploy):**
- [ ] P1: Todos os 442 proxy routes padronizados para `BACKEND_URL` + porta `8001`
- [ ] P2: `next build` passa sem erros (`ai-credits/page.tsx` corrigido)
- [ ] P3: `DATABASE_URL` do backend corrigido para banco real

**Preparação para deploy:**
- [ ] P4+P1: Nenhuma variável `NEXT_PUBLIC_*` expõe URLs internas do backend
- [ ] P5: Variáveis Replit (`REPLIT_DEV_DOMAIN`, etc.) com fallbacks para Cloud Run
- [ ] P6: WebSocket URLs parametrizadas com `NEXT_PUBLIC_WS_URL`
- [ ] Mockups pendentes revisados — aprovados integrados, descartados removidos
- [ ] Headers de segurança adicionados no `next.config.js`
- [ ] Error boundary verificado em pages críticas (funil, chat, vagas)
- [ ] Testes E2E `.catch(() => {})` silenciosos removidos

**Configuração de produção (infra + produto):**
- [ ] `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` de produção configurados
- [ ] Redirect URIs do WorkOS registrados para `wedotalent.cc`
- [ ] Sentry DSN de produção configurado (`NEXT_PUBLIC_SENTRY_DSN`)
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

### Arquitetura de agentes

```
Requisição do usuário
        │
        ▼
┌───────────────────┐
│  FastAPI Router   │  ← 70+ endpoints organizados por domínio
│  (Port 8001)      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Intent Classifier │  ← Claude classifica a intenção da mensagem
│  (fast_router.py) │     antes de invocar o agente correto
└────────┬──────────┘
         │
    ┌────┴────────────────────────────┐
    │           DOMÍNIOS (40+)        │
    │                                 │
    │  ┌─────────────┐ ┌──────────┐  │
    │  │ CV Screening│ │ Sourcing │  │
    │  │  (LangGraph)│ │ (Graph)  │  │
    │  └─────────────┘ └──────────┘  │
    │  ┌─────────────┐ ┌──────────┐  │
    │  │Job Management│ │Analytics │  │
    │  └─────────────┘ └──────────┘  │
    │  ┌─────────────────────────┐   │
    │  │ Communication (Teams/WA)│   │
    │  └─────────────────────────┘   │
    └─────────────────────────────────┘
         │
         ▼
┌───────────────────┐
│  PostgreSQL       │  ← 69 ferramentas registradas
│  + pgvector       │     (candidate_tools, job_tools, analytics...)
│  Redis + RabbitMQ │
└───────────────────┘
```

### O que está sólido

| Área | Situação |
|---|---|
| **LangGraph** | Grafos de agentes implementados por domínio (cv_screening, sourcing, interview_scheduling) |
| **Tool Registry** | 69 ferramentas registradas e organizadas por domínio |
| **Policy Engine** | Controle de acesso e regras de negócio centralizadas |
| **Circuit Breakers** | Resiliência implementada para chamadas LLM e serviços externos |
| **PII Masking** | LGPD: mascaramento de dados pessoais no logger ativo |
| **HITL** | Human-in-the-loop implementado (aprovações antes de ações críticas) |
| **Alembic** | Migrations versionadas para o banco |
| **Dockerfile** | `Dockerfile` e `Dockerfile.prod` já existem |
| **Sentry** | `sentry-sdk[fastapi]` integrado |
| **WSI** | Voice Screening Interface implementado (triagem por voz) |

### O que precisa de atenção antes do deploy

| Área | Problema | Ação |
|---|---|---|
| **Shims de compatibilidade** | Shims usam `import *` que não exporta funções privadas (`_prefixo`) | ✅ Corrigido para os que encontramos — rodar `python3 -c "from app.main import app"` para validar todos. Padrão sistêmico: cada novo shim deve ser verificado |
| **Bug `wsi_repository.py`** | ✅ CORRIGIDO (07/04/2026) — Linhas 594 e 603 tinham SQL sem aspas e dicts com sintaxe JavaScript (`{call_sid: val}` em vez de `{"call_sid": val}`). Impedia o startup total do backend. | Corrigido e validado — backend rodando normalmente |
| **GOOGLE_APPLICATION_CREDENTIALS** | Speech/TTS precisam de service account | Configurar Workload Identity no Cloud Run |
| **RabbitMQ** | Sem serviço gerenciado no GCP | Provisionar (ver Seção 11.5) |
| 🔴 **P3: DATABASE_URL errado** | Backend `.env` aponta para `localhost:5432/lia_db` mas banco real do Replit está em `helium/heliumdb` com ~60 tabelas já migradas. Endpoints que fazem queries vão falhar com "connection refused" | **Agora:** Corrigir DATABASE_URL para `postgresql+asyncpg://postgres:password@helium/heliumdb`. **Deploy:** Cloud SQL com banco próprio (`lia_db`) + acesso ao Rails via REST (`RAILS_API_URL`) |
| **Redis prod** | Sem autenticação configurada no código | Adicionar `REDIS_URL` com senha para Memorystore |
| **Celery workers** | Não configurado para Cloud Run | Adicionar segundo serviço Cloud Run para workers Celery |
| **LANGSMITH** | Opcional mas recomendado para debug em prod | Adicionar `LANGSMITH_API_KEY` |
| **Secrets hardcoded** | Verificar se há chaves hardcoded em algum arquivo | Auditar com `grep -r "sk-ant\|AIza\|ghp_" app/` |

### Checklist de production readiness — IA

- [ ] `python3 -c "from app.main import app"` passa sem erros
- [ ] `alembic upgrade head` roda clean no banco de produção
- [ ] Todas as variáveis LLM (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) no Secret Manager
- [ ] Service Account com permissão para Speech API e TTS configurado
- [ ] RabbitMQ provisionado e `CELERY_BROKER_URL` configurado
- [ ] `REDIS_URL` apontando para Cloud Memorystore (com senha)
- [ ] Celery worker rodando como serviço separado no Cloud Run
- [ ] Circuit breakers validados para cada LLM (Claude, Gemini, OpenAI)
- [ ] Sentry DSN backend configurado (`SENTRY_DSN`)
- [ ] Teams webhook URL atualizada para URL de produção do Cloud Run

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
              → 59 migrações aplicadas, banco completo

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
- [ ] 🟡 **P1:** 11 arquivos frontend substituídos (NEXT_PUBLIC_BACKEND_URL/NEXT_PUBLIC_API_URL → chamadas via proxy routes — task separada)
- [ ] 🔴 **P2:** `next build` sem erros (`ai-credits/page.tsx` corrigido)
- [ ] 🟡 **P4:** Nenhuma `NEXT_PUBLIC_*` expondo URLs internas (resolver com P1)
- [ ] 🟡 **P5:** Variáveis Replit (`REPLIT_DEV_DOMAIN`) com fallbacks para Cloud Run
- [ ] 🟡 **P6:** WebSocket URLs parametrizadas com env var
- [ ] WorkOS prod configurado (API key + redirect URIs para `wedotalent.cc`)
- [ ] Headers de segurança em `next.config.js`
- [ ] Sentry DSN frontend
- [ ] Teams Tab URL atualizada para prod
- [ ] Testes E2E completos com WorkOS real em CI
- [ ] Mockups pendentes revisados e finalizados

**AI Agent (ver Seção 12.1 P3 e Seção 13 para detalhes):**
- [x] Bug `wsi_repository.py` corrigido (SQL sem aspas + dicts JS-style → Python correto)
- [x] `.env.example` atualizado (`API_PORT` corrigido, `RAILS_API_URL` adicionado)
- [ ] 🔴 **P3:** `DATABASE_URL` corrigido para banco real do Replit (`helium/heliumdb`)
- [ ] `python3 -c "from app.main import app"` sem erros (validar todos os shims `import *`)
- [ ] Migrations Alembic clean
- [ ] Todos os secrets movidos para Secret Manager
- [ ] Celery worker configurado como serviço separado
- [ ] Service Account para Google Speech/TTS
- [ ] Teams webhook URL atualizada para URL prod Cloud Run

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
- [ ] Twilio: credenciais prod no Secret Manager
- [ ] Microsoft Teams: webhook URL de prod registrado no Azure
- [ ] Resend: `RESEND_API_KEY` no Secret Manager
- [ ] Sentry: projetos criados (frontend + backend), DSNs configurados
- [ ] WhatsApp Meta: (se pronto) credenciais de prod

### Validação funcional (time completo)

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
| **PostgreSQL** | 🟢 **Obrigatório** | Banco de dados principal. Alembic roda 59 migrações. Cloud SQL no GCP. |
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

## 24. AUDITORIA PROFUNDA — PRODUCTION READINESS (9 Dimensões)

> **Data:** Abril 2026
> **Escopo:** Análise técnica do codebase Replit (plataforma-lia + lia-agent-system) + 7 repos GitHub (WeDOTalent org)
> **Objetivo:** Mapear riscos, gaps e recomendações antes do go-live

### Sumário Executivo

| # | Dimensão | Severidade | Findings | Status |
|---|----------|-----------|----------|--------|
| 24.1 | LLM Factory / Vendor Lock-in | ALTO | Factory existe mas bypass direto em ~34 arquivos | Parcial |
| 24.2 | Arquitetura de IA | CRITICO | 62 domínios, ~15 ativos, padrão inconsistente | Parcial |
| 24.3 | Fairness / Governança IA | ALTO | FairnessGuard 3 camadas implementado, gaps em enforcement | Bom |
| 24.4 | Multi-tenancy / Segurança | CRITICO | RLS + JWT + WorkOS implementados, gaps em dev fallbacks | Bom |
| 24.5 | Production Readiness | ALTO | Health checks robustos, endpoints com bugs conhecidos | Parcial |
| 24.6 | Arquitetura / Overengineering | MEDIO | Duplicação massiva em 3 camadas de serviços | Ruim |
| 24.7 | Design / Frontend | MEDIO | DS v4.2.1 adotado em ~70% das páginas | Bom |
| 24.8 | Infraestrutura / Deploy | MEDIO | Docker + Terraform existem, env vars documentadas | Bom |
| 24.9 | Repos Legados (GitHub) | BAIXO | 7 repos, 3 com valor, 4 obsoletos | N/A |

---

### 24.1 LLM Factory / Vendor Lock-in

#### Estado Atual

A plataforma possui uma abstração bem projetada em `app/shared/providers/`:

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Interface LLM | `llm_provider.py` (`LLMProviderABC`) | Implementado |
| Provider Gemini | `llm_gemini.py` (`GeminiLLMProvider`) | Implementado |
| Provider OpenAI | `llm_openai.py` (`OpenAILLMProvider`) | Implementado |
| Provider Claude | `llm_claude.py` (`ClaudeLLMProvider`) | Implementado |
| Factory LLM | `llm_factory.py` (`ProviderContainer`) | Implementado |
| Interface Embedding | `embedding_provider.py` (`EmbeddingProviderABC`) | Implementado |
| Embedding Gemini | `embedding_gemini.py` | Implementado |
| Embedding OpenAI | `embedding_openai.py` | Implementado |
| Factory Embedding | `embedding_factory.py` | Implementado |
| Tenant Context | `tenant_llm_context.py` | Implementado |
| Cost Cascade | `llm_cascade.py` (`LLMCascadeRouter`) | Implementado |

**Cascade de Custo (llm_cascade.py):**
1. Tier 1: `preferred_model` (se fornecido)
2. Tier 2: Gemini Flash (rápido/barato) — threshold 0.80 confidence
3. Tier 3: Claude Sonnet (médio) — threshold 0.70 confidence
4. Tier 4: Claude Opus (poderoso/caro) — fallback final

**Tenant Provider Registry:** `TenantProviderRegistry` mapeia `tenant_id` → `ProviderContainer`, permitindo API keys e modelos por tenant.

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | Bypass direto do Gemini | ALTO | ~34 arquivos referenciam `gemini` diretamente; alguns importam `google.generativeai` ou chamam `provider="gemini"` hardcoded, bypassando a factory |
| 2 | Voice hardcoded | ALTO | `gemini_voice_service.py` e `gemini_live_audio_service.py` usam `google.genai` direto, sem abstração via factory |
| 3 | Semantic search hardcoded | ALTO | `semantic_search_service.py` importa `google.generativeai` diretamente |
| 4 | Serviços de domínio bypassam factory | ALTO | `wsi_question_adjuster.py`, `job_qualification_service.py`, `llm_job_classification_service.py` chamam Gemini direto |
| 5 | Feature parity entre providers | MEDIO | `generate_with_tools` tem implementações divergentes entre Gemini/Claude/OpenAI (tipos e formatos de retorno diferentes) |
| 6 | UI de configuração de tenant | MEDIO | `tenant_llm_context.py` espera tabela `tenant_llm_configs` no DB, mas não há interface para gerenciar |

#### Recomendação

1. **[P2/G]** Migrar os ~34 arquivos com bypass direto para usar `LLMService` ou `llm_factory` — eliminar `import google.generativeai` diretos
2. **[P1/M]** Criar `VoiceProviderABC` e abstrair voice services (seguindo o padrão do embedding)
3. **[P2/M]** Normalizar output de `generate_with_tools` entre providers
4. **[P3/P]** Criar tela de configuração de LLM por tenant no admin

---

### 24.2 Arquitetura de IA — Domínios e Padrões

#### Estado Atual

**62 domínios** em `app/domains/`, categorizados em:

| Categoria | Domínios | Exemplos |
|-----------|---------|---------|
| AI-Enhanced (com agents/tools/prompts) | ~15 | `cv_screening`, `job_management`, `recruiter_assistant`, `sourcing`, `analytics`, `communication` |
| Infraestrutura/Base | ~10 | `admin`, `auth`, `billing`, `health_check`, `observability`, `saas_metrics` |
| CRUD/Repositório | ~25 | `company`, `interview`, `candidate`, `opinions`, `credits` |
| Empty/Stub | ~10 | `recruitment_campaign`, `talent_pool`, `journey_mapping`, `digital_twin` e outros |

**Padrões de IA:**

| Padrão | Onde | Exemplo |
|--------|-----|---------|
| LangGraph/StateGraph | Workflows complexos | `wsi_interview_graph.py`, `job_wizard_graph.py`, `interview_graph.py` |
| ReAct Agents | Domínios com tools | `analytics_react_agent.py`, `sourcing_react_agent.py` |
| Direct LLM Calls | Domínios simples | `Orchestrator._handle_directly`, `sourcing/prompts.py` |

**Orchestrator:** Multi-tier routing (Tier 5 CascadedRouter → Tier 6 Autonomous → PlanDetector/Executor → Fallback direto).

**Tool Registry:** ~35-45 tools registrados em categorias: `job_wizard`, `candidate`, `communication`, `job`, `export`, `query`, `pipeline`, `cv_match`.

**Prompt Quality (por domínio amostrado):**

| Domínio | Técnicas Usadas | Qualidade |
|---------|----------------|----------|
| `cv_screening` | YAML estruturado, Persona, Behavioral Rules, intent_examples | Alta |
| `job_wizard` | Few-shot, Chain-of-Thought, Structured Output (JSON Schema) | Alta |
| `sourcing` | Template strings com preenchimento | Média |
| Domínios stub | Strings literais ou ausentes | Baixa |

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | ~10 domínios vazios/stub | ALTO | `recruitment_campaign`, `talent_pool`, `journey_mapping`, `digital_twin` etc. — existem na estrutura mas sem lógica real |
| 2 | Domínios stub com estrutura completa | MEDIO | Domínios stub mantêm diretórios (repos/services/schemas/) com `__init__.py` vazio — ruído na navegação |
| 3 | Padrão inconsistente entre domínios | MEDIO | Alguns seguem DDD completo (repo/service/schema/route), outros são ad-hoc |
| 4 | Transição incompleta para LangGraph | MEDIO | Apenas 3 domínios usam StateGraph; maioria ainda é ReAct ou direto |
| 5 | Prompts sem técnicas em domínios ativos | MEDIO | Serviços como `sourcing/prompts.py` usam strings sem few-shot ou CoT |

#### Recomendação

1. **[P1/P]** Deletar ou mover para `_deprecated/` os ~10 domínios stub (reduzir ruído)
2. **[P3/P]** Verificar quais domínios stub têm referências ativas no Orchestrator e limpar
3. **[P3/G]** Padronizar prompts: migrar strings soltas para PromptTemplate YAML com few-shot/CoT
4. **[P4/GG]** Migrar domínios críticos restantes para LangGraph (avaliação case-a-case)

---

### 24.3 Fairness / Bias / Governança IA

#### Estado Atual

A plataforma implementa uma arquitetura de governança IA de **3 pilares** (LGPD, SOX, EU AI Act) com os seguintes componentes:

**FairnessGuard (3 Camadas) — `app/shared/compliance/fairness_guard.py`:**

| Camada | Implementação | Status |
|--------|--------------|--------|
| Layer 1: Explicit Bias | Regex engine detectando 16+ categorias (gênero, raça, idade, religião, orientação sexual, deficiência, etc.) | Implementado |
| Layer 2: Implicit Bias | Detecção de termos proxy (ex: "universidades de primeira linha" = viés socioeconômico) | Implementado |
| Layer 3: Semantic Bias | `check_fairness_async` usando LLM para detectar viés sutil que regex não captura | Implementado |

**Mensagens Educativas:** Quando violação é detectada, retorna explicação legal específica (ex: Art. 5, CLT).

**Middleware:** `fairness_guard_middleware.py` aplica decorators em endpoints de alto impacto (geração de JD, motivos de rejeição).

**WSI (Weighted Screening Index):**
- Geração de questões usando CBI, Dreyfus (Skill Levels), Bloom's Taxonomy
- `AuditService` lista `PROTECTED_CRITERIA` (idade, gênero, etnia, foto) forçosamente ignorados no scoring
- Cálculo: `Σ(peso_i × score_i)` via `score_calculator.py`

**Audit Service (`audit_service.py`):**
- Loga toda decisão IA com reasoning completo, critérios usados e ignorados
- Método `get_candidate_decisions` para "Right to Explanation"
- Rastreamento de `human_review_required` e `human_override`
- Retenção: 2-5 anos (730-1825 dias)

**LGPD/GDPR:**
- Domínios dedicados: `lgpd`, `consent`, `data_subject`
- Data Subject Requests implementados no frontend
- Migration `060` com criptografia para campos PII (email, CPF) e TTL indexes

**Culture Analyzer:** Mapeia competências culturais para Big Five (OCEAN) em vez de "culture fit" vago.

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | Enforcement seletivo | ALTO | FairnessGuard middleware aplica-se apenas em endpoints de JD e rejeição; outros endpoints de decisão (triagem, ranking) podem não estar cobertos |
| 2 | Layer 3 depende de LLM | MEDIO | Checagem semântica de bias é async e depende de disponibilidade do LLM — pode falhar silenciosamente |
| 3 | Audit storage | MEDIO | Logs de auditoria armazenados no mesmo banco — escala pode ser problema com volume alto |
| 4 | 13 Crenças WeDO | BAIXO | Documentadas no Guide v3.3 mas não codificadas como regras no código — são referência filosófica, não enforcement |

#### Recomendação

1. **[P1/M]** Expandir FairnessGuard middleware para cobrir endpoints de triagem/ranking/sourcing
2. **[P2/P]** Adicionar fallback para Layer 3 quando LLM estiver indisponível (ex: flag warnings em vez de fail-open)
3. **[P3/M]** Mover audit logs para storage separado (S3/BigQuery) para escala
4. **[P4/P]** Codificar Crenças WeDO como checklist de validação no pipeline de IA

---

### 24.4 Multi-tenancy / Segurança

#### Estado Atual

**Isolamento de Tenant:**

| Mecanismo | Implementação | Status |
|-----------|--------------|--------|
| PostgreSQL RLS | `set_config('app.company_id', :cid, true)` via `set_tenant_context` | Implementado |
| JWT com company_id | Claims: `sub`, `role`, `company_id` no payload | Implementado |
| Middleware de Auth | `AuthEnforcementMiddleware` valida JWT e injeta `company_id` em `request.state` + `ContextVar` | Implementado |
| TenantGuard | `get_verified_company_id` valida X-Company-ID vs JWT claim | Implementado |
| WorkOS SSO | Domain checking, user syncing, org → company_id mapping | Implementado |
| WorkOS SCIM | Directory Sync completo (user CRUD, group membership, auto-provisioning) | Implementado |

**Auth JWT:**
- Algoritmo: HS256
- Access token: 30 min TTL
- Refresh token: 7 dias TTL
- Cookies: `lia_access_token`, `workos_session`

**Rate Limiting:**
- Redis-backed sliding window (`app/middleware/rate_limiter.py`)
- 600 req/min por usuário, 3000 req/min por company
- Fallback: in-memory dict se Redis indisponível

**CORS:**
- `CORSMiddleware` com `settings.CORS_ORIGINS`
- Defaults dev: `localhost:5000`, `localhost:3000`
- `allow_credentials=True`, todos os métodos/headers

**Frontend Auth (`middleware.ts`):**
- Gatekeeper: verifica cookies `lia_access_token` ou `workos_session`
- Auto-inject: `Authorization: Bearer <token>` em requests proxy
- Public paths excluídos corretamente

**Endpoints sem filtro de company_id (esperado):**
- Auth: `login`, `register`, `forgot-password`, `reset-password`, `verify-email`
- Health: `/health`, `/api/v1/health`, `/api/v1/health/langgraph`
- Public: Páginas de vagas públicas
- Webhooks: WhatsApp, Twilio, Mailgun (usam signature verification)

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | Dev fallbacks com credenciais | MEDIO | `DEV_AUTO_LOGIN` existe no middleware.ts (provavelmente desabilitado via `NODE_ENV` guard em produção); `INTERNAL_API_SECRET` com default vazio — verificar se guards são efetivos |
| 2 | Scripts com mock credentials | ALTO | Scripts em `/scripts` com credenciais hardcoded para Jira/Notion (mesmo que de teste) |
| 3 | CORS wildcards em dev | MEDIO | `allow_methods=["*"]`, `allow_headers=["*"]` — precisa ser restrito em produção |
| 4 | SSL strip no asyncpg | MEDIO | `database.py` strip `sslmode=` do DATABASE_URL — precisa configuração manual de SSL context para produção |
| 5 | Rate limiter fallback | BAIXO | Se Redis cai, fallback é in-memory — sem proteção real em múltiplas instâncias |

#### Recomendação

1. **[P1/P]** Garantir que `DEV_AUTO_LOGIN` e demo fallbacks são desabilitados quando `APP_ENV=production`
2. **[P1/P]** Limpar credenciais de scripts utilitários; usar env vars
3. **[P2/P]** Configurar CORS restritivo para produção (ex: apenas `https://wedotalent.cc`)
4. **[P2/M]** Implementar SSL context explícito para asyncpg em produção
5. **[P3/P]** Documentar que rate limiter requer Redis para funcionar em multi-instance

---

### 24.5 Production Readiness — Erros e Estado Atual

#### Estado Atual

**Health Checks (`system_health.py`):**

| Categoria | Checks | Status |
|-----------|--------|--------|
| Critical | PostgreSQL connectivity, Redis ping | Implementado |
| Infra | Celery workers (queue length), Broker, Rate Limiter | Implementado |
| AI/Services | LLM providers (Anthropic, Gemini, OpenAI), Voice (Deepgram, OpenMic), Circuit Breakers (14 circuits) | Implementado |
| Integrations | WhatsApp, Microsoft/Google Calendar, LinkedIn, Indeed, Slack | Implementado |
| Probes | `/health/ready` (DB + Redis), `/health/live` (process check) | Implementado |

**Error Handling:**
- Padronizado via `@handle_agent_errors` decorator com `AgentErrorCode` (LLM_ERROR, DATABASE_ERROR, etc.)
- `StructuredLoggingMiddleware` + PII masking global (`PIIMaskingFilter`)
- Sentry integration (`init_sentry`)
- LangSmith para LLM tracing
- Pydantic validation errors retornam 422 com código `VALIDATION_ERROR`

**Database Migrations:**
- 59-60 migrations Alembic
- Últimas: `060_encrypt_pii_fields_and_ttl_indexes.py` (PII encryption + TTL)

**WebSocket:**
- `WSManager` singleton com session storage e user mapping
- Frontend com lógica de reconnection (testada em `use-agent-streaming-reconnect.test.ts`)
- Async bridge: Celery → RabbitMQ response queue → WS push

**Celery Tasks:**

| Task | Queue | Função |
|------|-------|--------|
| `agents.sourcing.search` | sourcing_high | Busca async de candidatos (30-120s) |
| `agents.triagem.run` | evaluation_normal | Triagem em batch de CVs |
| `lgpd.run_cleanup_daily` | onboarding_low | Deleção de dados expirados (90-365 dias) |
| `drift.run_batch` | evaluation_normal | Detecção de drift em modelos |
| `audit.apply_lifecycle_policy` | onboarding_low | Rotação mensal de logs S3 |

**Redis:**

| Uso | TTL | Obrigatório? |
|-----|-----|-------------|
| Celery broker/backend | N/A | Sim |
| Semantic cache (LLM) | 86400s (24h) | Sim (reduz custos LLM) |
| Router cache | 3600s (1h) | Sim |
| Rate limiter | Sliding window | Sim (multi-instance) |
| Session data (HITL, WSI) | Variável | Sim |

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | `is_synced_to_calendar` None vs bool | ALTO | Campo pode ser `None` mas Pydantic espera `bool` — causa 500 em endpoints de entrevistas |
| 2 | Talent pools com bugs | ALTO | Funcionalidade existe mas endpoints podem falhar (reportado em sessões anteriores) |
| 3 | Rails fallback silencioso | MEDIO | Endpoints com padrão "Rails-first, Local-fallback" — se Rails está down, fallback pode mascarar problemas de dados |
| 4 | Redis = degradação significativa sem ele | MEDIO | Redis necessário para Celery, cache semântico, rate limiting, sessões. Sem Redis: tarefas background falham, custos LLM aumentam, rate limiting perde eficácia multi-instance. `BROKER_BACKEND` suporta alternativas (RabbitMQ, PubSub) |
| 5 | 60 migrations sem squash | BAIXO | 60 migrations Alembic — deploy inicial em banco novo leva tempo; squash reduziria |

#### Recomendação

1. **[P1/P]** Corrigir `is_synced_to_calendar`: `Optional[bool] = False` no modelo Pydantic
2. **[P1/M]** Auditar e corrigir talent pools endpoints
3. **[P2/P]** Garantir que `APP_ENV=production` desabilita Rails fallback (ou que Rails está operacional)
4. **[P2/P]** Documentar Redis como dependência obrigatória no runbook
5. **[P3/M]** Squash migrations para deploy clean

---

### 24.6 Arquitetura / Overengineering

#### Estado Atual

**Tamanho do codebase:**
- `lia-agent-system`: ~4.717 arquivos
- `plataforma-lia`: ~130.834 arquivos (incluindo node_modules)

**Duplicação em 3 camadas:**

```
app/services/           ← Shims (import * from shared/services/)
app/shared/services/    ← Implementação real
app/domains/*/services/ ← Implementação por domínio (parcial)
```

Exemplo: `voice_service.py` existe nas 3 camadas — `app/services/`, `app/shared/services/`, e `app/domains/voice/services/`.

**Rails Integration Layer:**

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Rails Adapter | `rails_adapter.py` | Em uso ativo, marcado para remoção |
| Rails JWT | `rails_jwt.py` | Autenticação cross-system |
| WeDOTalent Rails | `wedotalent_rails.py` | Bridge para entidades Rails |

Dezenas de arquivos contêm comentários: `"# Will be deleted after ats-api-rails handoff is complete"` e `"# Do NOT migrate to a domain"`.

**ATS Factory:** `ats_factory.py` — factory para clientes ATS externos (Gupy, Pandape, Merge). Funcional mas com abstração excessiva para o número atual de providers.

**Circuit Breaker:** Implementado e **ativo** em produção — usado em LLM providers, ATS clients, e sourcing services. Testado com chaos tests.

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | 3 camadas de serviços duplicados | ALTO | `app/services/` contém ~97 shims puros (import * from shared/) + ~61 arquivos com lógica. Migração faseada necessária — não deletar tudo de uma vez |
| 2 | 62 domínios com estrutura redundante | MEDIO | Cada domínio tem `__init__.py` vazio em repositories/, services/, schemas/, models/ — centenas de arquivos vazios |
| 3 | Rails layer em transição | MEDIO | ~30+ arquivos com "will be deleted" mas sem timeline definida |
| 4 | Over-segmentação de domínios | MEDIO | Domínios como `consent`, `credits`, `opinions` poderiam ser sub-módulos de domínios maiores |
| 5 | Centenas de `# noqa: F401` | BAIXO | `__init__.py` com imports não utilizados suprimidos — polui namespaces |

#### Recomendação

1. **[P2/G]** Migrar `app/services/` faseadamente — primeiro os 97 shims puros, depois os 61 com lógica (mover para domínios corretos)
2. **[P2/M]** Limpar `__init__.py` vazios — manter apenas os necessários para package discovery
3. **[P2/G]** Definir timeline para remoção da Rails layer — ou manter como "legacy adapter" com documentação clara
4. **[P3/M]** Consolidar micro-domínios em domínios maiores (ex: `consent` + `data_subject` → `compliance`)

---

### 24.7 Design / Frontend — Consistências

#### Estado Atual

**Design System LIA v4.2.1 — Tokens definidos em `src/lib/design-tokens.ts` + `src/styles/design-tokens.css`:**

| Token | Valor | Uso |
|-------|-------|-----|
| `lia-text-primary` | Gray 900 (#111827) | Títulos, labels |
| `lia-text-secondary` | Gray 600 (#4B5563) | Texto secundário |
| `lia-text-muted` | Gray 500 (#6B7280) | Texto terciário |
| `lia-border-subtle` | #E5E7EB | Bordas, separadores |
| `lia-bg-primary` | White | Fundo principal |
| WeDo Cyan | Brand | Elementos de IA/LIA |
| WeDo Green | Brand | Sucesso |
| WeDo Orange | Brand | Avisos |
| WeDo Purple | Brand | Insights |

**Tipografia:**
- Open Sans (85%) — UI principal
- Inter (10%) — dados, métricas, tabelas
- JetBrains Mono (5%) — código, IDs técnicos

**Escopo:**
- 32 páginas em `src/app/`
- 136 componentes compartilhados em `src/components/`
- 169 componentes page-specific

**Adoção:**
- Páginas modernas (AgentStudio, Chat, Funil) — ~100% tokens
- Páginas legadas (Login, Register) — hardcoded values
- Responsividade: Mobile-first com `sm:`, `md:`, `lg:` consistentes

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | Login/Register com cores hardcoded | MEDIO | `bg-white`, `border-gray-200`, `text-gray-950`, `text-gray-400` — não usam tokens |
| 2 | Source Serif 4 residual | BAIXO | Referência em login page branding, marcada como "removida" no DS v4.1 mas ainda presente |
| 3 | Layout files legados | BAIXO | Alguns layouts mais antigos ainda com classes Tailwind diretas em vez de tokens |
| 4 | Componentes page-specific demais | BAIXO | 169 page-specific vs 136 shared — ratio poderia ser melhor com mais abstração |

#### Recomendação

1. **[P2/P]** Migrar Login/Register para usar tokens DS v4.2.1
2. **[P3/P]** Remover referências residuais de Source Serif 4
3. **[P3/M]** Auditar componentes page-specific e promover reusáveis para `src/components/`

---

### 24.8 Infraestrutura / Deploy

#### Estado Atual

**Variáveis de Ambiente (centralizadas em `libs/config/lia_config/config.py` via `pydantic-settings`):**

| Categoria | Variáveis | Obrigatório? |
|-----------|----------|-------------|
| Database | `DATABASE_URL`, `DATABASE_POOL_SIZE` (20), `DATABASE_MAX_OVERFLOW` (10) | Sim |
| Cache/Messaging | `REDIS_URL`, `RABBITMQ_URL`, `BROKER_BACKEND` | Sim |
| AI/LLM | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS` | Sim (min 1) |
| LLM Models | `LLM_PRIMARY_MODEL` (claude-sonnet), `LLM_FAST_MODEL`, `LLM_POWERFUL_MODEL` | Defaults ok |
| Auth | `SECRET_KEY`, `RAILS_JWT_SECRET_KEY`, `WORKOS_CLIENT_ID` | Sim |
| Voice | `TWILIO_ACCOUNT_SID`, `DEEPGRAM_API_KEY` | Opcional |
| Integrations | `STRIPE_SECRET_KEY`, `MAILGUN_API_KEY`, `MERGE_API_KEY` | Opcional |
| Observability | `SENTRY_DSN`, `LANGCHAIN_API_KEY` | Recomendado |
| App | `APP_ENV`, `DEBUG`, `CORS_ORIGINS` | Sim |

**PostgreSQL:**
- Driver: asyncpg
- Pool: 20 connections, 10 overflow, pre_ping, recycle 3600s
- RLS: `app.company_id` session variable
- SSL: Precisa configuração manual (strip de `sslmode=` no código)

**Docker:**

| Arquivo | Função |
|---------|--------|
| `lia-agent-system/Dockerfile` | API |
| `lia-agent-system/Dockerfile.prod` | Produção |
| `lia-agent-system/Dockerfile.worker` | Celery workers |
| `lia-agent-system/docker-compose.yml` | Dev |
| `lia-agent-system/docker-compose.prod.yml` | Produção |
| `plataforma-lia/Dockerfile` | Frontend |
| `plataforma-lia/netlify.toml` | Deploy Netlify (alternativo) |

**Terraform:** `lia-agent-system/terraform/gcp/` — Cloud Run na região `us-central1`.

**Dependências Python:** `fastapi==0.115.5`, `sqlalchemy==2.0.36`, `langchain==0.3.9`, `celery==5.4.0` — versions pinned, sem conflitos detectados.

**Dependências npm:** `next^15.3.2`, `react^19.0.0`, `tailwindcss^3.4.17` — versões recentes. `dompurify^3.3.3` para XSS protection.

#### Problemas Encontrados

| # | Problema | Severidade | Detalhes |
|---|---------|-----------|---------|
| 1 | SSL asyncpg manual | ALTO | Código strip `sslmode=` — produção GCP requer SSL explícito |
| 2 | CORS dev-only defaults | MEDIO | `localhost:5000,3000` hardcoded como defaults — precisa override em produção |
| 3 | Redis obrigatório sem docs | MEDIO | 5 funções dependem de Redis mas runbook não documenta como obrigatório |
| 4 | langsmith dependency warnings | BAIXO | Conflito reportado em post-merge logs (não bloqueia mas gera warnings) |
| 5 | npm audit 1 high severity | BAIXO | Vulnerabilidade reportada nas dependências npm |

#### Recomendação

1. **[P1/M]** Implementar SSL context para asyncpg em produção (GCP Cloud SQL requer)
2. **[P1/P]** Configurar `CORS_ORIGINS` para produção no Terraform/Cloud Run env vars
3. **[P2/P]** Documentar Redis como dependência obrigatória no DEPLOY_GUIDE
4. **[P3/P]** Resolver conflito langsmith
5. **[P3/P]** Executar e resolver `npm audit` findings

---

### 24.9 Repos Legados (GitHub — WeDOTalent org)

#### Inventário

| Repo | Stack | Tamanho | Última Atualização | Status |
|------|-------|---------|-------------------|--------|
| `ats_api` | Ruby on Rails 7.1 + PostgreSQL + Redis + Sidekiq + Elasticsearch | 4.412KB / 171 files | 2026-04-08 | Ativo (bridge) |
| `recruiter_agent_v5` | Python + LangGraph + Celery + RabbitMQ | 3.693KB / 834 files | 2026-04-08 | Referência |
| `ats_front` | Desconhecido (só `.gitignore`) | 4.695KB / 1 file | 2026-02-19 | Morto |
| `wedo-nuxt` | Nuxt 3 + Vue 3 + Vuetify (via `vuetify-nuxt-module`) + Histoire | 178KB / 77 files | 2026-02-19 | Protótipo |
| `ats_mcp` | TypeScript MCP Server | 51KB / 30 files | 2026-03-07 | Funcional |
| `data_collector` | Python + Alembic + Docker + Workers | 582KB / 317 files | 2026-02-18 | Funcional |
| `wedotalent-admin` | TypeScript | 687KB | 2026-04-03 | Desconhecido |
| `reembolsointeligente` | Vazio | 0KB | 2026-02-11 | Morto |

#### Análise de Valor

**ats_api (Rails) — VALOR: MEDIO**
- Stack completa: Rails 7.1 + Apartment (multi-tenant schema-based) + Searchkick/Elasticsearch + Sneakers (RabbitMQ)
- Contém modelos de dados legados que a plataforma LIA ainda consulta via bridge
- **Veredicto:** Manter como bridge até migração completa de dados para FastAPI. Não investir em novas features.

**recruiter_agent_v5 — VALOR: ALTO (como referência)**
- 834 arquivos, 60+ scripts utilitários, 7 agents, 8 domínios
- Documentação extensiva: `PRODUCT_CAPABILITIES.md` cataloga 60+ tipos de queries que o agente suporta
- Celery com 4 queues prioritárias + RabbitMQ + Supervisor
- **Veredicto:** Base de conhecimento para catálogo de capabilities da LIA. Código já parcialmente migrado. Manter como referência read-only.

**ats_front — VALOR: NULO**
- Apenas `.gitignore` (1 arquivo). Conteúdo deletado ou nunca comitado.
- **Veredicto:** Deletar ou arquivar.

**wedo-nuxt — VALOR: BAIXO**
- Nuxt 3 + Vue 3 + Vuetify com Histoire (component playground)
- 77 arquivos, muito inicial
- **Veredicto:** Referência para futura migração Vue. Sem urgência.

**ats_mcp — VALOR: MEDIO**
- TypeScript MCP Server (Model Context Protocol) para integração com LLMs
- Funcional, bem estruturado (30 files)
- **Veredicto:** Pode ser útil para integrações de IA com ferramentas externas. Avaliar integração.

**data_collector — VALOR: MEDIO**
- Python workers para coleta de dados de plataformas de emprego
- Docker + Alembic + Workers + API
- Documentação operacional (`QUAL_SCRIPT_USAR.md`, `PLANO_CARGA_COMPLETA.md`)
- **Veredicto:** Operacional para alimentação de dados. Manter se sourcing externo for prioridade.

---

### 24.10 Roadmap de Correções Prioritizado

#### Fase 1 — Críticos (antes do go-live) — Esforço: 2-3 sprints

| # | Item | Dimensão | Esforço |
|---|------|---------|--------|
| 1 | Corrigir `is_synced_to_calendar` Optional[bool] | 24.5 | P |
| 2 | Verificar que `DEV_AUTO_LOGIN` guard funciona em produção | 24.4 | P |
| 3 | Limpar credenciais hardcoded em scripts | 24.4 | P |
| 4 | Configurar CORS para produção | 24.4 / 24.8 | P |
| 5 | Implementar SSL context para asyncpg | 24.8 | M |
| 6 | Documentar Redis como dependência obrigatória | 24.5 / 24.8 | P |

#### Fase 2 — Altos (primeiros 30 dias pós-launch) — Esforço: 3-4 sprints

| # | Item | Dimensão | Esforço |
|---|------|---------|--------|
| 7 | Migrar ~34 arquivos com Gemini bypass para usar factory | 24.1 | G |
| 8 | Expandir FairnessGuard para endpoints de triagem/ranking | 24.3 | M |
| 9 | Corrigir talent pools endpoints | 24.5 | M |
| 10 | Migrar `app/services/` faseadamente (97 shims + 61 com lógica) | 24.6 | G |
| 11 | Migrar Login/Register para DS tokens | 24.7 | P |
| 12 | Criar VoiceProviderABC para abstração de voice | 24.1 | M |

#### Fase 3 — Médios (60-90 dias pós-launch) — Esforço: 4-6 sprints

| # | Item | Dimensão | Esforço |
|---|------|---------|--------|
| 13 | Deletar/deprecar ~10 domínios stub | 24.2 | P |
| 14 | Normalizar feature parity entre LLM providers | 24.1 | M |
| 15 | Definir timeline para remoção da Rails layer | 24.6 | G |
| 16 | Squash Alembic migrations | 24.5 | M |
| 17 | Mover audit logs para storage separado | 24.3 | M |
| 18 | Padronizar prompts com YAML templates | 24.2 | G |

#### Fase 4 — Baixos (backlog) — Esforço: ongoing

| # | Item | Dimensão | Esforço |
|---|------|---------|--------|
| 19 | Criar UI de configuração LLM por tenant | 24.1 | M |
| 20 | Consolidar micro-domínios | 24.6 | M |
| 21 | Arquivar repos mortos (ats_front, reembolsointeligente) | 24.9 | P |
| 22 | Resolver npm audit findings | 24.8 | P |
| 23 | Migrar domínios críticos para LangGraph | 24.2 | GG |

---

*Última atualização: Abril 2026 (pós-auditoria completa do ecossistema wedocc2026 + auditoria profunda production readiness)*
*Domínio: wedotalent.cc · Região GCP: us-central1 · Stack: Next.js 15 + FastAPI + Rails 7 (opcional)*
*Integrações mapeadas: Claude, Gemini, OpenAI, WorkOS, Twilio Voice, Google STT/TTS, Teams, WhatsApp, Resend, HubSpot, PEARCH, Redis, RabbitMQ, Celery, Sentry, LangSmith*
*Decisão arquitetural: FastAPI é a fonte de verdade. Rails é opt-in para dados legados. Ver Seção 2F.*
