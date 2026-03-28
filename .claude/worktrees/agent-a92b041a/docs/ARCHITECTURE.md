# Architecture — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> Baseado em leitura direta do código dos 6 repositórios do ecossistema.
> Tom: técnico e direto. Para mapa de repositórios e rotas, ver `PLATFORM_MAP.md`.

---

## 1. Stack de Frontend

### 1.1 Decisão: Nuxt 3 + Vue 3 + Vuetify 3 (produção)

**O que foi decidido:** O frontend de produção do ATS (`ats_front`) usa Nuxt 3 com Vue 3 e Vuetify 3 como UI library. A estrutura é orientada a features (`features/`, `composables/`, `stores/`).

**Stack completa:**
- Framework: Nuxt 3 (Vue 3)
- UI: Vuetify 3 via `vuetify-nuxt-module`
- State: Pinia (`stores/` — 16 stores)
- Data fetching: `@tanstack/vue-query`
- Forms: VeeValidate + Zod
- Icons: `@mdi/font` (Material Design Icons)
- Estilos globais: SCSS via `assets/scss/global.scss`

**Por que foi decidido:** Vuetify fornece componentes prontos com acessibilidade e densidade adequada para um SaaS B2B. Nuxt 3 oferece SSR nativo, roteamento baseado em arquivo e ecossistema modular compatível com o design system.

**Alternativas descartadas:** React + Next.js (ficou no protótipo PM — `plataforma-lia`). A duplicidade existe porque o protótipo foi construído por PMs antes da decisão de stack de produção.

---

### 1.2 Decisão: wedo-nuxt como biblioteca de componentes isolada

**O que foi decidido:** O Design System (`wedo-nuxt`) é um repositório separado do `ats_front`. Componentes com prefixo `Lia*` são publicados como biblioteca.

**Componentes principais:** `LiaField`, `LiaTabBar`, `LiaPageHeader`, `LiaSectionHeader`, `LiaFileUpload`, `LiaBigFiveChart`, `LiaCtaBanner`.

**Tokens canônicos:**
- Primary: `#111827` (gray-900) — monocromático 90%
- WeDO Cyan: `#60BED1` — acento 10%
- Sombra: `shadow-sm` (shadow-xl/2xl proibidos no design system)

**Storybook:** Histoire (`@histoire/plugin-nuxt`, `@histoire/plugin-vue`).

**Por que foi decidido:** Isola o design system do código de produto, permitindo evolução independente e versionamento. Evita que mudanças de UI quebrarem componentes compartilhados.

---

### 1.3 Decisão: plataforma-lia como protótipo PM (Next.js 14 + React)

**O que foi decidido:** Next.js 14 com App Router para protótipos de PM. Não vai a produção diretamente — funcionalidades aprovadas são reimplementadas no `ats_front`.

**Padrão de API:** As chamadas ao backend passam por um proxy interno (`/api/backend-proxy/*`) que o Next.js expõe como API Routes. Isso evita expor credenciais no cliente.

```typescript
// Exemplo real — plataforma-lia/src/lib/api/candidate-search.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""
fetch(`${API_BASE}/api/backend-proxy/search/candidates`, ...)
```

**Auth:** WorkOS (SSO) — `src/lib/workos.ts`, `src/lib/workos-session.ts`.

**Alternativas descartadas:** Não há — decisão de contexto. O protótipo é ferramenta de PM, não de engenharia.

---

## 2. Stack de Backend

### 2.1 Decisão: Ruby on Rails 7.1 como API ATS de produção

**O que foi decidido:** `ats_api` é o backend de produção em Rails 7.1. Expõe endpoints REST versionados (`/v1/`).

**Stack completa:**
- Framework: Ruby on Rails 7.1
- Banco: PostgreSQL com Apartment gem (multi-tenancy por schema)
- Background jobs: Sidekiq 7 + Redis
- Real-time: ActionCable (WebSockets) — `app/channels/message_channel.rb`
- Search: Elasticsearch + Searchkick
- Serialização: `jsonapi-serializer`
- CORS: `rack-cors`

**Por que foi decidido:** Rails oferece convenções maduras para CRUD de ATS (modelos, concerns, jobs). O ecossistema de gems cobre todos os requisitos sem código custom extensivo.

**Alternativas descartadas:** Node.js/Express (sem evidência de avaliação formal no código).

---

### 2.2 Decisão: JWT custom (sem Devise full) para autenticação

**O que foi decidido:** Autenticação via JWT implementada diretamente no `ApplicationController` usando a gem `jwt`. O token é assinado com `Rails.application.secret_key_base`. Expiração: 24 horas.

```ruby
# app/controllers/application_controller.rb — código real
def jwt_encode(payload, exp = 24.hours.from_now)
  payload[:exp] = exp.to_i
  JWT.encode(payload, Rails.application.secret_key_base)
end

def authorize_request
  header = request.headers['Authorization']
  token = header.split(' ').last if header
  decoded = jwt_decode(token)
  @current_user = User.find_by(id: decoded[:user_id])
  render json: { error: 'Not Authorized' }, status: :unauthorized unless @current_user
end
```

**Por que foi decidido:** Implementação direta é mais simples que Devise completo para uma API stateless. O token carrega apenas `user_id`.

**Alternativas descartadas:** Devise + Warden (mais adequado para apps com sessão de browser, não para API pura).

> ⚠️ **Inconsistência identificada:** `config/application.rb` define `config.api_only = false`, mas o projeto usa ActionController::Base e serve como API. Ver seção "Decisões Pendentes".

---

### 2.3 Decisão: PostgreSQL schema-based multi-tenancy (Apartment gem)

**O que foi decidido:** Cada Account (cliente) tem um schema PostgreSQL isolado. `Account` e `User` são modelos excluídos do isolamento (compartilhados). Todos os outros dados ficam no schema do tenant.

```ruby
# config/initializers/apartment.rb — código real
Apartment.configure do |config|
  config.excluded_models = %w[ Account User ]
  config.use_schemas = true
  config.tenant_names = lambda { Account.pluck :tenant }
end
```

O scoping por conta é reforçado via concern `AccountScopable` nos modelos:

```ruby
# app/models/concerns/account_scopable.rb
module AccountScopable
  included do
    before_validation :assign_account
  end
end
```

**Por que foi decidido:** Isolamento de dados por schema oferece segurança real entre clientes sem overhead de banco separado por cliente. Apartment é a solução Rails padrão para isso.

**Alternativas descartadas:** Row-level tenancy (menos isolamento), banco separado por cliente (custo operacional alto).

---

### 2.4 Decisão: FastAPI como backend de serviços IA (lia-agent-system)

**O que foi decidido:** Serviços de IA da LIA rodam em Python com FastAPI. Este serviço é separado do `ats_api` — não compartilha banco nem processo.

**Middlewares registrados (ordem de execução):**
1. `StructuredLoggingMiddleware` — log estruturado de requests
2. `RequestIdMiddleware` — X-Request-ID em cada request
3. `RateLimitMiddleware` — proteção por cliente
4. `CORSMiddleware` — configurado via `settings.CORS_ORIGINS`

**Monitoramento:** Sentry (DSN via `SENTRY_DSN`) + integração com FastAPI e Starlette.

**Auth:** WorkOS SSO — Bearer token verificado a cada request. Grupos SCIM sincronizados com roles da plataforma.

**Config:** Módulo `lia_config.config` (biblioteca interna) — `app/core/config.py` é apenas um shim de compatibilidade retroativa:
```python
# app/core/config.py
from lia_config.config import DatabaseSettings, CacheSettings, LLMSettings, Settings, settings
```

---

## 3. Estratégia de AI/LLM

### 3.1 Decisão: Dois sistemas de IA independentes com LLMs diferentes

**O que foi decidido:** A plataforma tem dois sistemas de IA que rodam em paralelo e independentes:

| Sistema | LLM | Framework | Domínio |
|---------|-----|-----------|---------|
| `recruiter_agent_v5` | Google Gemini (`gemini-2.5-flash`) | LangGraph + Celery | Interface linguagem natural do recrutador |
| `lia-agent-system` | Anthropic Claude (via modelFarm proxy) | LangGraph + FastAPI | Triagem WSI, sourcing, voz, análises |

**Por que foi decidido:** Os sistemas evoluíram de equipes diferentes. O `recruiter_agent_v5` foi construído com Gemini (melhor custo-benefício para roteamento de intenções). O `lia-agent-system` usa Claude para tarefas que exigem raciocínio mais elaborado (triagem comportamental, scoring com Bloom/Dreyfus).

**Alternativas descartadas:** LLM único (aumentaria acoplamento e vendor lock-in; a diversidade permite fallback).

---

### 3.2 Decisão: LangGraph para todos os fluxos de agentes

**O que foi decidido:** Ambos os sistemas usam LangGraph como orquestrador de estado. A regra explícita, encontrada no código do `lia-agent-system`:

```python
# wsi_interview_graph.py — comentário arquitetural real
"""
Por que Graph (não ReAct)?
- Fluxo sequencial determinístico: pergunta 1 → 2 → N → resultado
- Cada etapa deve ser rastreável individualmente (compliance BCB 498, SOX)
- Sem decisão autônoma — transições baseadas em regras explícitas
- Auditável: log completo de cada nó para FairnessGuard e Bias Audit

Conforme recomendação arquitetural: fluxos previsíveis = Graph,
fluxos com raciocínio autônomo = ReAct.
"""
```

**Regra aplicada:**
- Fluxo determinístico (triagem WSI, agendamento sequencial) → `StateGraph` com nós explícitos
- Raciocínio autônomo (planner, intenção ambígua) → ReAct / agente com tools

**Por que foi decidido:** Auditabilidade é requisito não negociável (BCB 498, SOX, LGPD). Grafos com nós nomeados geram traces completos por etapa, o que não é possível com chains monolíticas.

**Alternativas descartadas:** LangChain chains puras (sem grafo de estado), AutoGPT-style (não auditável).

---

### 3.3 Decisão: Arquitetura Hub → Planner → Domain no recruiter_agent_v5

**O que foi decidido:** O roteamento de queries do recrutador segue uma hierarquia de 3 camadas:

```
Query
  └── HubOrchestrator    (sessão, contexto)
        └── HubPlanner   (routing por complexidade)
              ├── Fast-path (regex) → < 100ms
              ├── CostLadder        → custo incremental
              └── LLM planning      → casos complexos
                    └── DomainOrchestrator → DomainWorkflow (LangGraph) → Domain → API
```

**Por que foi decidido:** O CostLadder evita chamar LLM para queries simples ("listar vagas ativas" → regex match direto). Apenas queries ambíguas chegam ao LLM, reduzindo latência e custo.

**LLM Factory:** `create_tracked_llm()` em `src/utils/llm_factory.py` — instância única rastreada por LangSmith. Nunca instanciar `ChatGoogleGenerativeAI` diretamente.

**LangSmith:** Habilitado via `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`. Projeto configurado em `LangSmithConfig.project`.

---

### 3.4 Decisão: Celery + RabbitMQ para execução assíncrona de agentes

**O que foi decidido:** Tasks de IA de longa duração (sourcing, evaluation) rodam em workers Celery com RabbitMQ como broker. Cada domínio tem sua própria fila com prioridade:

```python
# src/config/celery_config.py — código real
DOMAIN_QUEUES = {
    "sourced_profile_sourcing": QueueConfig(name="sourcing_high", priority=10),
    "jobs": QueueConfig(name="jobs_high", priority=9),
    "evaluation": QueueConfig(name="evaluation_normal", priority=5),
    "default": QueueConfig(name="default", priority=1),
}
```

**Por que foi decidido:** Agentes com múltiplas chamadas LLM podem levar 30-60 segundos. HTTP síncrono não é viável. Celery permite retries configuráveis (`task_default_retry_delay`, `task_acks_late=True`).

**Alternativas descartadas:** Sidekiq (Ruby-only, não compatível com código Python), Dramatiq (menos ecossistema).

---

### 3.5 Decisão: Guardrails em banco de dados (não hardcoded)

**O que foi decidido:** Regras de segurança para agentes IA são armazenadas em tabela `guardrails` (PostgreSQL), populadas via seed. Dois níveis: primários (todos os agentes) e secundários (por domínio).

**Por que foi decidido:** Guardrails em banco permitem ajuste sem redeploy. Permite auditoria de quais regras estavam vigentes em uma data (compliance SOX/BCB 498).

---

## 4. Padrões de Integração entre Serviços

### 4.1 Decisão: Todos os agentes consomem ats_api via REST (sem acesso direto ao banco)

**O que foi decidido:** `recruiter_agent_v5` e `lia-agent-system` nunca acessam o PostgreSQL do `ats_api` diretamente. Toda leitura/escrita passa pelos endpoints REST.

```
recruiter_agent_v5 → GET /v1/users/jobs → ats_api → PostgreSQL (schema do tenant)
lia-agent-system   → POST /v1/users/applies → ats_api → PostgreSQL (schema do tenant)
```

**Por que foi decidido:** Mantém o `ats_api` como única fonte de verdade. Mudanças de schema do banco não quebram os agentes diretamente — a interface REST absorve.

**Alternativas descartadas:** Acesso direto ao banco pelos agentes (violaria isolamento de tenant, dificultaria auditoria).

---

### 4.2 Decisão: plataforma-lia usa proxy Next.js para lia-agent-system

**O que foi decidido:** O protótipo não chama `lia-agent-system` diretamente do browser. As chamadas passam por API Routes do Next.js (`/api/backend-proxy/*`) que fazem o proxy.

**Por que foi decidido:** Evita expor a URL e credenciais do backend no cliente. Permite adicionar auth, logging e transformação de payload sem alterar o frontend.

**Inconsistência identificada:** CORS do `ats_api` só permite `http://localhost:3000` — credenciais de produção não encontradas no código.

---

### 4.3 Decisão: ats_mcp como bridge para dev workflow (não é infraestrutura de produção)

**O que foi decidido:** O MCP server (`ats_mcp`) serve exclusivamente para o workflow de desenvolvimento (Claude Code, Cursor). Ele lê código do Replit, tickets do Jira e mapeia para o código de produção.

**Não é chamado em produção** — não faz parte do fluxo de dados entre usuário final e plataforma.

---

### 4.4 Decisão: WebSockets em dois pontos separados

**O que foi decidido:** Real-time acontece em dois lugares independentes:

| Onde | Tecnologia | Uso |
|------|-----------|-----|
| `ats_api` | ActionCable (`/cable`) | Mensagens recrutador ↔ candidato em tempo real |
| `lia-agent-system` | FastAPI WebSockets (`agent_chat_ws.py`, `jobs_ws.py`) | Streaming de respostas IA |

**Por que foi decidido:** ActionCable é nativo ao Rails — zero custo adicional para mensagens. FastAPI WebSockets para streaming de LLM (SSE e WS) é mais flexível que ActionCable para payloads de IA.

**API de streaming do recruiter_agent_v5:** SSE (Server-Sent Events) via `EventSourceResponse` da lib `sse-starlette`. Timeout interno de 200s com keepalive.

---

## 5. Estrutura de Dados Principal

### 5.1 Multi-tenancy: dois bancos PostgreSQL, dois propósitos

| Banco | Porta | Owner | Uso |
|-------|-------|-------|-----|
| ATS PostgreSQL | 5432 (padrão) | `ats_api` (Rails) | Dados de produção — vagas, candidatos, pipeline |
| Agent PostgreSQL | 5433 | `recruiter_agent_v5` | Estado de agentes — checkpoints LangGraph, semantic cache, audit |

Os dois bancos são **totalmente separados**. O agente não lê dados de recrutamento diretamente do banco do ATS.

---

### 5.2 Modelo de dados do ATS (ats_api)

```
Account (tenant root — fora do schema isolado)
  └── User (fora do schema isolado)
       └── UserRole → Role → RolePermission → Permission
       └── UserPermission (overrides diretos)

[Schema do tenant]
  Job ────────────── SelectiveProcess
   └── Apply ──────── Candidate
        └── ApplyStatus (pipeline stages)
  Message (recrutador ↔ candidato, qualquer direção)
```

**Concerns de Model:**
- `AccountScopable`: auto-atribui `account_id` via `Current.user.account_id` no `before_validation`
- `Searchable`: integração Searchkick para indexação Elasticsearch

---

### 5.3 Estado de agentes (recruiter_agent_v5)

Gerenciado via LangGraph `Checkpointer` em PostgreSQL (porta 5433). Cada sessão mantém:
- `session_id` (UUID)
- Estado do grafo (nó atual, histórico de mensagens)
- Contexto do domínio ativo

Redis (porta 6380) armazena cache semântico de respostas LLM (evita chamadas duplicadas) e routing cache.

---

## 6. Decisões de Segurança e Autenticação

### 6.1 ats_api: JWT com secret_key_base (sem rotação automática)

**Implementação:** JWT assinado com `Rails.application.secret_key_base`. Decodificação com rescue de exceção (token inválido retorna nil). Expiração hardcoded em 24h.

**Risco identificado:** `secret_key_base` é o mesmo usado para cookies — uma rotação de chave invalidaria todos os tokens simultaneamente.

---

### 6.2 lia-agent-system: WorkOS SSO + Rate Limiting + Request ID

**Implementação:**
- Auth: Bearer token verificado pelo middleware WorkOS. SCIM sync de grupos → roles da aplicação.
- Rate limiting: `RateLimitMiddleware` (implementação customizada).
- Rastreabilidade: `RequestIdMiddleware` adiciona `X-Request-ID` em todas as respostas.
- Logging: `StructuredLoggingMiddleware` garante logs em JSON com contexto de request.
- Erros: Sentry captura exceções com `FastApiIntegration` + `StarletteIntegration`.

---

### 6.3 Compliance IA: Guardrails + Bias Audit + FairnessGuard

**Implementação:**
- Guardrails: tabela em banco, dois níveis (primário global + secundário por domínio).
- Bias Audit: endpoint `admin_bias_audit.py`, dashboard em `/admin/compliance/auditoria/bias`.
- WSI Scoring: auditável por nó LangGraph — cada pergunta tem `bloom_level` (1-6) e `dreyfus_level` (1-5) registrados.
- LGPD: `admin_lgpd.py`, `consent_management.py`, `data_subject_requests.py`, portal titular em `/portal/data-request/[token]`.

---

### 6.4 CORS: apenas localhost em desenvolvimento (produção não encontrada no código)

**Implementação encontrada no código:**
```ruby
# config/initializers/cors.rb — código real
allow do
  origins 'http://localhost:3000'
  resource '*', headers: :any, methods: %i[get post put patch delete options head]
end
```

> ⚠️ **Nenhuma configuração CORS de produção foi encontrada no repositório.** Pode estar em variável de ambiente ou arquivo não commitado.

---

## 7. Decisões Pendentes / Inconsistências Identificadas

| # | Item | Localização | Problema |
|---|------|-------------|---------|
| 1 | `api_only = false` | `ats_api/config/application.rb` | Config diz não-API mas o sistema é API pura. Pode afetar middleware stack e comportamento de cookies. |
| 2 | CORS produção ausente | `ats_api/config/initializers/cors.rb` | Apenas `localhost:3000` configurado. Origins de produção não encontradas no código. |
| 3 | Pundit não implementado | `ats_api` | Mencionado na arquitetura (ats_mcp docs), gem `pundit` no Gemfile, mas `app/policies/` vazio. Autorização de nível de recurso não existe. |
| 4 | Dois LLMs sem estratégia escrita | `recruiter_agent_v5` + `lia-agent-system` | Gemini vs Claude não tem decisão registrada. Não há critério documentado para qual usar em casos limítrofes. |
| 5 | `ats_front` vazio no GitHub | GitHub `WeDOTalent/ats_front` | Repositório tem apenas `.gitignore`. Código do frontend de produção não está no GitHub — localização real desconhecida. |
| 6 | Multi-tenancy em Python | `lia-agent-system` | O `ats_api` usa Apartment gem para isolamento de tenant. O `lia-agent-system` em Python não tem mecanismo equivalente documentado — não está claro como dados de IA são isolados por cliente. |
| 7 | FairnessGuard | `lia-agent-system` | Referenciado em comentários e docs como sistema de 3 camadas, mas implementação não encontrada como módulo separado. Pode estar distribuída em `bias_audit.py` e `guardrails.py`. |
| 8 | Plano de graduação protótipo→produção | `plataforma-lia` → `ats_front` | Não há processo formal no código para promover features do Next.js para o Nuxt 3. O `ats_mcp` tem `find_related_files` e `map_replit_to_project` mas sem workflow codificado. |
| 9 | Semantic cache sem invalidação documentada | `recruiter_agent_v5` | Cache semântico em Redis/PostgreSQL sem estratégia de invalidação encontrada no código. |
| 10 | CORS do lia-agent-system | `lia-agent-system/app/main.py` | Usa `settings.CORS_ORIGINS` (configurável), mas valor padrão não encontrado no código. |

---

> Para mapa de repositórios, rotas e domínios, ver `PLATFORM_MAP.md`.
> Próximo documento SDD: `docs/specs/standards/AI_ARCHITECTURE.md` — detalhamento de prompts, avaliação de agentes e padrões de LangGraph.
