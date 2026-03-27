# Platform Map — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Gerado a partir do código real dos 6 repositórios do ecossistema.
> **FONTE DA VERDADE TÉCNICA** — qualquer informação conflitante em outros documentos deve ser resolvida aqui.

---

## Visão Geral

Plataforma SaaS multi-tenant de recrutamento com IA. O recrutador opera via linguagem natural (chat/voz) ou pela interface web. A LIA (IA da WeDOTalent) conduz triagens, agenda entrevistas, busca candidatos e fornece análises — tudo integrado ao ATS.

**Stack principal:** Ruby on Rails (API) + Nuxt 3/Vue 3 (frontend produção) + Python/FastAPI (serviços IA) + LangGraph (orquestração de agentes) + PostgreSQL multi-tenant (Apartment gem).

---

## 1. Mapa de Repositórios

| Repo | Stack | Papel | Localização |
|------|-------|-------|-------------|
| `ats_api` | Ruby on Rails 7.1 | API ATS de produção — vagas, candidatos, pipeline, mensagens | GitHub WeDOTalent |
| `ats_front` | Nuxt 3 + Vue 3 + Vuetify | Frontend ATS de produção | GitHub WeDOTalent |
| `wedo-nuxt` | Vue 3 + Nuxt 3 + Vuetify | Design System LIA v4.1 — biblioteca de componentes | GitHub WeDOTalent |
| `recruiter_agent_v5` | Python + LangGraph + Celery | [AI] Agente recrutador V5 — interface linguagem natural | GitHub WeDOTalent |
| `lia-agent-system` | Python + FastAPI + LangGraph | [AI] Serviços LIA — triagem WSI, sourcing, voz, análises | Replit |
| `plataforma-lia` | Next.js 14 + React + Tailwind | Protótipo PM — onde features nascem antes de ir para produção | Replit |
| `ats_mcp` | TypeScript + Node.js | MCP Server — bridge entre AI coding (Claude/Cursor) e o ecossistema | GitHub WeDOTalent |
| `data_collector` | Python | Coleta de dados externos | GitHub WeDOTalent |

---

## 2. Fluxo entre Sistemas

```
RECRUTADOR (browser / Microsoft Teams / WhatsApp)
           |
           ├── Interface Web ──────────────────────────────► ats_front (Nuxt 3)
           │                                                       │
           │                                                       ▼
           │                                               ats_api (Rails API)
           │                                                       │
           │                                    ┌──────────────────┴────────────────────┐
           │                                    │                                       │
           │                                    ▼                                       ▼
           │                          lia-agent-system (FastAPI)           PostgreSQL (multi-tenant)
           │                          [AI] LIA persona + WSI                      Apartment gem
           │                          + Sourcing + Voz
           │
           └── Chat / Linguagem Natural ──────► recruiter_agent_v5 (Python)
                                               [AI] Hub → Planner → Domain
                                               └── ats_api (Rails REST)

DEV WORKFLOW:
PM prototipa ──► plataforma-lia (Replit)
                 │
                 ▼
          Card Jira com spec
                 │
                 ▼ (ats_mcp lê prototipo + mapeia para código real)
          Dev implementa em ats_api + ats_front
```

---

## 3. Rotas da Interface do Recrutador

> Baseado no `ats_front` (produção, branch `develop`) — file-based routing Nuxt 3.

### 3.1 Páginas Públicas (sem auth)

| Rota | Arquivo | Descrição |
|------|---------|-----------|
| `/` | `pages/index.vue` | Login |
| `/vagas/[slug]/[account_slug]` | `pages/vagas/[slug]/[account_slug].vue` | Career page pública |
| `/evaluations/[id]/[uid]` | `pages/evaluations/[id]/[uid].vue` | [AI] Avaliação do candidato |
| `/interviews/[account_uid]/[token]` | `pages/interviews/[account_uid]/[token].vue` | [AI] Entrevista ao vivo |
| `/scheduling/[account_uid]/[token]` | `pages/scheduling/[account_uid]/[token].vue` | Auto-agendamento |
| `/terms` | `pages/terms.vue` | Termos de uso |
| `/cookies` | `pages/cookies/index.vue` | Política de cookies |
| `/reset-password/[token]` | `pages/reset-password/[token].vue` | Reset de senha |
| `/auth/callback` | `pages/auth/callback.vue` | Auth callback |
| `/workos-callback` | `pages/workos-callback.vue` | WorkOS SSO callback |
| `/setups/[uid]` | `pages/setups/[uid]/index.vue` | Configuração inicial |
| `/setups/[uid]/forms` | `pages/setups/[uid]/forms.vue` | Formulários de setup |

### 3.2 Navegação Principal — Recrutador (`/user/`)

| Rota | Arquivo | Descrição | Layout |
|------|---------|-----------|--------|
| `/user/dashboard` | `pages/user/dashboard/index.vue` | Dashboard principal | user |
| `/user/candidates` | `pages/user/candidates/index.vue` | Lista de candidatos | user |
| `/user/candidates/[id]` | `pages/user/candidates/[id].vue` | Perfil do candidato | user |
| `/user/candidates/sourcings/[id]` | `pages/user/candidates/sourcings/[id].vue` | Perfis sourced | user |
| `/user/jobs` | `pages/user/jobs/index.vue` | Lista de vagas | user |
| `/user/jobs/[id]` | `pages/user/jobs/[id]/index.vue` | Detalhe + Kanban | user |
| `/user/jobs/[id]/applies/[apply_id]` | `pages/user/jobs/[id]/applies/[apply_id].vue` | Detalhe candidatura | user |
| `/user/lia` | `pages/user/lia/index.vue` | [AI] Lista de chats LIA | user |
| `/user/lia/[uid]` | `pages/user/lia/[uid].vue` | [AI] Chat LIA específico | user |
| `/user/evaluations` | `pages/user/evaluations/index.vue` | Avaliações | user |
| `/user/sourcing/[id]/chat` | `pages/user/sourcing/[id]/chat.vue` | [AI] Chat de sourcing | user |
| `/user/settings` | `pages/user/settings/index.vue` | Configurações | user |
| `/user/microsoft` | `pages/user/microsoft.vue` | Auth Microsoft | user |

### 3.3 Admin (`/user/admin/`)

| Rota | Arquivo | Descrição |
|------|---------|-----------|
| `/user/admin/dashboard` | `pages/user/admin/dashboard.vue` | [RESTRICTED] Dashboard admin |
| `/user/admin/accounts` | `pages/user/admin/accounts/index.vue` | [RESTRICTED] Contas/tenants |
| `/user/admin/users` | `pages/user/admin/users/index.vue` | [RESTRICTED] Usuários |
| `/user/admin/roles` | `pages/user/admin/roles/index.vue` | [RESTRICTED] Permissões |
| `/user/admin/ai_costs` | `pages/user/admin/ai_costs/index.vue` | [RESTRICTED] [AI] Custos de IA |
| `/user/admin/business` | `pages/user/admin/business/index.vue` | [RESTRICTED] Negócios |
| `/user/admin/job_status` | `pages/user/admin/job_status/index.vue` | [RESTRICTED] Status de vagas |
| `/user/admin/sectors` | `pages/user/admin/sectors/index.vue` | [RESTRICTED] Setores |
| `/user/admin/whatsapp_configurations` | `pages/user/admin/whatsapp_configurations/index.vue` | [RESTRICTED] WhatsApp |

### 3.4 Protótipo plataforma-lia (Replit)

| Rota | Descrição | Status |
|------|-----------|--------|
| `/jobs` | Lista de vagas | Protótipo |
| `/jobs/[id]` | Detalhe da vaga + Kanban | Protótipo |
| `/funil-de-talentos` | Funil de candidatos | Protótipo |
| `/triagem/[token]` | [AI] Triagem pública do candidato | Protótipo |
| `/chat` | [AI] Interface de chat com LIA | Protótipo |
| `/vagas/[slug]` | Portal público de vagas | Protótipo |
| `/portal/data-request/[token]` | [RESTRICTED] LGPD — solicitação de dados | Compliance |

---

## 4. APIs do `ats_api` (Rails 7.1)

> Lido diretamente de `config/routes.rb`.

**Base URL:** `https://api.wedotalent.com/v1` (produção) | `http://localhost:8080/v1` (local)

**Auth:** JWT custom (gem `jwt`, sem Devise — implementado diretamente em `ApplicationController`). Token assinado com `Rails.application.secret_key_base`. Expiração: 24h. Header: `Authorization: Bearer <token>`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/v1/sessions` | Login — retorna JWT |
| GET | `/v1/me` | Usuário autenticado |
| POST | `/v1/logout` | Logout |
| GET | `/v1/users/applies` | Lista candidaturas |
| GET | `/v1/users/applies/:id` | Detalhe candidatura |
| POST | `/v1/users/applies` | Criar candidatura |
| PUT | `/v1/users/applies/:id` | Atualizar candidatura |
| DELETE | `/v1/users/applies/:id` | Remover candidatura |
| GET | `/v1/users/jobs` | Lista vagas |
| GET | `/v1/users/jobs/:id` | Detalhe vaga |
| POST | `/v1/users/jobs` | Criar vaga |
| PUT | `/v1/users/jobs/:id` | Atualizar vaga |
| DELETE | `/v1/users/jobs/:id` | Remover vaga |
| GET | `/v1/users/selective_processes` | Lista processos seletivos |
| GET | `/v1/users/selective_processes/:id` | Detalhe processo |
| POST | `/v1/users/selective_processes` | Criar processo |
| PUT | `/v1/users/selective_processes/:id` | Atualizar processo |
| DELETE | `/v1/users/selective_processes/:id` | Remover processo |
| GET | `/v1/users/candidates` | Lista candidatos |
| GET | `/v1/users/candidates/:id` | Perfil candidato |
| POST | `/v1/users/candidates` | Criar candidato |
| PUT | `/v1/users/candidates/:id` | Atualizar candidato |
| DELETE | `/v1/users/candidates/:id` | Remover candidato |
| GET | `/v1/users/messages` | Lista mensagens |
| POST | `/v1/users/messages` | Enviar mensagem |
| GET | `/v1/users/search` | Busca global de usuários |
| WebSocket | `/cable` | ActionCable — real-time |

---

## 5. Modelos de Dados (`ats_api`)

> Lido de `app/models/`.

| Model | Descrição | Campos críticos |
|-------|-----------|-----------------|
| `Account` | Tenant da plataforma | Multi-tenant root |
| `User` | Usuário (recrutador, admin) | email, role |
| `Job` | Vaga de emprego | title, status, salary_range, location |
| `Candidate` | Perfil do candidato | name, email, skills, score, city |
| `Apply` | Candidatura (Job ↔ Candidate) | status, score, pipeline_stage |
| `ApplyStatus` | Estados do pipeline | name, order, type |
| `SelectiveProcess` | Processo seletivo | stages, jobs, timeline |
| `Message` | Mensagem recrutador ↔ candidato | content, channel, direction |
| `Role` | Papel de usuário | name, permissions |
| `Permission` | Permissão atômica | resource, action |
| `RolePermission` | Relação Role ↔ Permission | — |
| `UserRole` | Relação User ↔ Role | — |
| `UserPermission` | Override direto por usuário | — |

**Multi-tenancy:** Apartment gem (schema-based). Cada Account tem schema PostgreSQL isolado.

---

## 6. Agentes de IA

### 6.1 `recruiter_agent_v5` — Agente Recrutador V5

[AI] Interface principal do recrutador via linguagem natural (Teams, WhatsApp, CLI, API).

**LLM:** Google Gemini (via `create_tracked_llm()`)
**Orquestração:** LangGraph + Celery + RabbitMQ
**Monitoramento:** LangSmith

**Arquitetura de execução:**
```
Query (recrutador)
    ↓
HubOrchestrator          (src/hub/orchestrator.py)
    ↓
HubPlanner               (src/hub/planner.py)
 ├── Fast-path (regex)   → resposta imediata < 100ms
 ├── CostLadder          → roteamento por complexidade
 └── LLM planning        → planejamento complexo
    ↓
DomainOrchestrator       (src/domains/orchestrator.py)
    ↓
DomainWorkflow (LangGraph) → intent → execute → format
    ↓
Domain.process_intent + Domain.execute_action
    ↓
ats_api (Rails REST)
```

**6 Domínios ativos (v5):**

| Domain ID | Pasta | Responsabilidade | Actions principais |
|-----------|-------|------------------|--------------------|
| `applies` | `src/domains/applies/` | Pipeline de candidaturas (per `job_id`) | search, pipeline, scoring, ranking, bulk, compare |
| `jobs` | `src/domains/jobs/` | CRUD e analytics de vagas | search, create, update, pipeline, analytics, auto_source |
| `insights` | `src/domains/insights/` | Analytics cross-domain | daily_briefing, metrics, bottleneck, reports, trends |
| `messaging` | `src/domains/messaging/` | Comunicação com candidatos (preview obrigatório) | send_feedback, send_invite, send_followup, bulk_send |
| `autonomous` | `src/domains/autonomous/` | Agente universal ReAct (~73 tools) | Qualquer ação via tools + playbooks YAML |
| `evaluation` | `src/domains/evaluation/` | Avaliação de candidatos (LangGraph próprio) | classify_input, evaluate_response, craft_message |

**Serviços cross-cutting:**

| Serviço | Localização | Função |
|---------|-------------|--------|
| Semantic Cache | `src/services/cache/` | Cache de respostas por embedding |
| Circuit Breaker | `src/services/` | Proteção contra falhas em cascata |
| Audit Service | `src/services/` | Log de decisões do agente |
| LLM Factory | `src/utils/llm_factory.py` | `create_tracked_llm()` — instanciação rastreada |
| PII Filter | `src/services/pii_filter.py` | Filtragem de dados pessoais |
| Checkpointer | `src/services/checkpointer.py` | Persistência de estado LangGraph |

---

### 6.2 `lia-agent-system` — Serviços LIA

[AI] Backend de IA da LIA persona. Processa triagens, avaliações, sourcing, voz e análises.

**LLM:** Google Gemini (produção); código contém providers Claude/OpenAI não ativados
**Framework:** FastAPI + LangGraph
**Canais suportados:** WhatsApp (360dialog), Microsoft Teams

**12 Domínios:**

| Domínio | Localização | Responsabilidade |
|---------|-------------|------------------|
| `cv_screening` | `app/domains/cv_screening/` | [AI] Triagem de CVs, WSI scoring, Bloom/Dreyfus |
| `sourcing` | `app/domains/sourcing/` | [AI] Busca, enriquecimento e engajamento de candidatos |
| `job_management` | `app/domains/job_management/` | [AI] Wizard de criação de vagas |
| `interview_scheduling` | `app/domains/interview_scheduling/` | [AI] Agendamento de entrevistas |
| `recruiter_assistant` | `app/domains/recruiter_assistant/` | [AI] Assistente do recrutador |
| `hiring_policy` | `app/domains/hiring_policy/` | Políticas de contratação e compliance |
| `analytics` | `app/domains/analytics/` | Analytics e métricas |
| `pipeline` | `app/domains/pipeline/` | Gestão do pipeline de candidatos |
| `communication` | `app/domains/communication/` | Templates e comunicações |
| `ats_integration` | `app/domains/ats_integration/` | Integração com ATS externo |
| `automation` | `app/domains/automation/` | Automações e regras |
| `policy` | `app/domains/policy/` | Políticas e compliance |

**Principais endpoints FastAPI** (`app/api/v1/`):

| Grupo | Endpoints | Descrição |
|-------|-----------|-----------|
| Auth | `auth.py`, `workos.py` | Autenticação e SSO |
| CV & Triagem | `cv_parser.py`, `wsi.py`, `wsi_async.py`, `triagem.py` | [AI] Parsing e scoring de CVs |
| Vaga | `briefing.py`, `wizard_smart_orchestrator.py` | [AI] Criação inteligente de vagas |
| Pipeline | `pipeline.py`, `bulk_actions.py`, `applications.py` | Gestão do funil |
| Sourcing | `sourcing_pipeline.py`, `candidate_search.py` | [AI] Busca de candidatos |
| Comunicação | `email.py`, `whatsapp.py`, `communications.py` | Mensagens multicanal |
| Analytics | `dashboard_data.py`, `predictive_analytics.py`, `workforce.py` | Métricas e previsões |
| Compliance | `admin_lgpd.py`, `audit_logs.py`, `bias_audit.py` | LGPD, SOC-2, auditoria |
| Admin | `admin.py`, `admin_settings.py`, `clients.py` | Gestão de clientes |
| Voz | `voice.py`, `transcription.py` | [AI] Entrevistas por voz |
| Agentes | `agent_chat_ws.py`, `agent_monitoring.py`, `agent_quality.py` | [AI] Monitoramento e qualidade |

---

## 7. Frontend — `ats_front`

> Lido de `ats_front` (branch `develop`, 901 arquivos). Números reais do codebase.

**Stack:** Nuxt 3 + Vue 3 + Vuetify 3 + TypeScript + Pinia (Options API) + Axios + ActionCable

| Métrica | Valor |
|---------|-------|
| Total de arquivos | 901 |
| Páginas | 34 (file-based routing Nuxt) |
| Feature modules | 28 (em `features/`, 358 arquivos) |
| Composables | 57 (em `composables/`) |
| Stores (Pinia) | 18 (em `stores/`, Options API) |
| Components totais | 145 (ui: 130, llm: 8, shared: 3, sourcing: 3, applies: 1) |
| Base components | 13 (`Base*` — wrappers Vuetify) |
| Table cell renderers | 30+ (`td*` — registro global) |
| Chat IA components | 10 (streaming, code blocks, markdown) |
| Plugins | 11 (em `plugins/`) |
| Layouts | 5 (user, admin, blank, evaluations, setup) |
| Types | 7 arquivos `.ts` |

**Maiores feature modules:**

| Feature | Arquivos | Descrição |
|---------|----------|-----------|
| `features/messages/` | 88 | Templates de comunicação |
| `features/candidates/` | 48 | Gestão + filtros + emails + cards |
| `features/lia/` | 46 | [AI] Chat LIA, sourcing, archetypes, search |
| `features/admin/` | 44 | AI costs dashboard, sectors, roles, WhatsApp |
| `features/jobs/` | 38 | Form multistep, cards, workflow, screening |
| `features/applies/` | 23 | Kanban, dialogs, screening results |

**Inventário completo de rotas (34 páginas):**

| Rota | Arquivo | Layout | Descrição |
|------|---------|--------|-----------|
| `/` | `pages/index.vue` | blank | Login |
| `/auth/callback` | `pages/auth/callback.vue` | blank | OAuth callback |
| `/workos-callback` | `pages/workos-callback.vue` | blank | WorkOS SSO callback |
| `/reset-password/[token]` | `pages/reset-password/[token].vue` | blank | Reset de senha |
| `/terms` | `pages/terms.vue` | blank | Termos de uso |
| `/cookies` | `pages/cookies/index.vue` | blank | Política de cookies |
| `/user/dashboard` | `pages/user/dashboard/index.vue` | user | Dashboard principal |
| `/user/candidates` | `pages/user/candidates/index.vue` | user | Lista de candidatos |
| `/user/candidates/[id]` | `pages/user/candidates/[id].vue` | user | Perfil do candidato |
| `/user/candidates/sourcings/[id]` | `pages/user/candidates/sourcings/[id].vue` | user | Resultados de sourcing |
| `/user/jobs` | `pages/user/jobs/index.vue` | user | Lista de vagas |
| `/user/jobs/[id]` | `pages/user/jobs/[id]/index.vue` | user | Detalhe da vaga + Kanban |
| `/user/jobs/[id]/applies/[apply_id]` | `pages/user/jobs/[id]/applies/[apply_id].vue` | user | Candidatura individual |
| `/user/lia` | `pages/user/lia/index.vue` | user | [AI] Hub LIA |
| `/user/lia/[uid]` | `pages/user/lia/[uid].vue` | user | [AI] Chat LIA |
| `/user/sourcing/[id]/chat` | `pages/user/sourcing/[id]/chat.vue` | user | [AI] Chat de sourcing |
| `/user/evaluations` | `pages/user/evaluations/index.vue` | user | Avaliações |
| `/user/settings` | `pages/user/settings/index.vue` | user | Configurações |
| `/user/microsoft` | `pages/user/microsoft.vue` | user | Auth Microsoft |
| `/user/admin/dashboard` | `pages/user/admin/dashboard.vue` | admin | Dashboard admin |
| `/user/admin/accounts` | `pages/user/admin/accounts/index.vue` | admin | Contas + LLM quota |
| `/user/admin/ai_costs` | `pages/user/admin/ai_costs/index.vue` | admin | [AI] Dashboard de custos IA |
| `/user/admin/business` | `pages/user/admin/business/index.vue` | admin | Dados da empresa |
| `/user/admin/job_status` | `pages/user/admin/job_status/index.vue` | admin | Status de vagas |
| `/user/admin/roles` | `pages/user/admin/roles/index.vue` | admin | Cargos e permissões |
| `/user/admin/sectors` | `pages/user/admin/sectors/index.vue` | admin | Setores |
| `/user/admin/users` | `pages/user/admin/users/index.vue` | admin | Gestão de usuários |
| `/user/admin/whatsapp_configurations` | `pages/user/admin/whatsapp_configurations/index.vue` | admin | Config WhatsApp |
| `/evaluations/[id]/[uid]` | `pages/evaluations/[id]/[uid].vue` | evaluations | [AI] Avaliação pública |
| `/interviews/[account_uid]/[token]` | `pages/interviews/[account_uid]/[token].vue` | blank | [AI] Entrevista ao vivo |
| `/scheduling/[account_uid]/[token]` | `pages/scheduling/[account_uid]/[token].vue` | blank | Auto-agendamento |
| `/setups/[uid]` | `pages/setups/[uid]/index.vue` | setup | Setup inicial |
| `/setups/[uid]/forms` | `pages/setups/[uid]/forms.vue` | setup | Formulários de setup |
| `/vagas/[slug]/[account_slug]` | `pages/vagas/[slug]/[account_slug].vue` | blank | Career page pública |

**Comunicação com backend:**
- HTTP REST dual: `$api` (`$fetch` wrapper, `plugins/api.ts`) + `$axios` (legacy, `plugins/axios.ts`)
- WebSocket via ActionCable (`@rails/actioncable` → `composables/useCable.ts`)
- Streaming de chat IA via `composables/useMessageStreaming.ts`
- Auth: JWT via `useCookie('auth_token')` — interceptor automático em ambos clients

**Tema Vuetify (`config/vuetify.config.ts`):**
- `lightTheme` / `darkTheme` com cores WeDo (cyan, green, orange, purple, magenta)
- Primary = `#111827` (Gray 900 — botões pretos)
- `componentDefaults`: VBtn rounded=12px, VTextField/VSelect density=compact
- Componentes Vuetify importados manualmente (sem auto-import)

**Ferramentas adicionais:**
- Histoire (Storybook-like) para component stories
- Vue Flow (diagramas de workflow)
- Vue Toastification (notificações)
- Splitpanes (layout redimensionável)
- Auto Animate (transições automáticas)

---

## 8. Design System — `wedo-nuxt` (biblioteca de componentes)

Biblioteca de componentes oficiais da plataforma.

**Stack:** Vue 3 + Nuxt 3 + Vuetify 3 + Tailwind CSS
**Design System:** LIA v4.1 (baseado em ElevenLabs UI — monocromático 90% grays + acentos WeDO 10%)
**Storybook equivalente:** Histoire

**Componentes core:**

| Componente | Arquivo | Função |
|------------|---------|--------|
| `LiaField` | `app/components/LiaField.vue` | Campo de formulário com slot + botão IA |
| `LiaTabBar` | `app/components/LiaTabBar.vue` | Navegação por abas |
| `LiaPageHeader` | `app/components/LiaPageHeader.vue` | Header de página |
| `LiaSectionHeader` | `app/components/LiaSectionHeader.vue` | Header de seção |
| `LiaFileUpload` | `app/components/LiaFileUpload.vue` | Upload de arquivos |
| `LiaBigFiveChart` | `app/components/LiaBigFiveChart.vue` | [AI] Gráfico Big Five |
| `LiaCtaBanner` | `app/components/LiaCtaBanner.vue` | Banner de CTA |
| `LiaDepartmentCard` | `app/components/LiaDepartmentCard.vue` | Card de departamento |

**Tokens de design:**
- Primary: `#111827` (gray-900)
- WeDO Cyan: `#60BED1`
- Background: `#FFFFFF`
- Surface: `#F9FAFB`
- Sombra padrão: `shadow-sm` (shadow-xl/2xl proibido)

---

## 8. MCP Server — `ats_mcp`

Bridge que permite AI coding assistants (Claude Code, Cursor) trabalhar automaticamente no ecossistema.

**Recursos disponíveis:**
- `ats://architecture` — Arquitetura completa do ATS
- `ats://tech-stack` — Stack técnica de cada projeto
- `ats://testing-guide` — Guia de testes e credenciais locais

**Tools disponíveis:**
- `get_jira_ticket` — Busca ticket Jira com specs
- `search_jira` — Pesquisa por JQL
- `find_related_files` — Mapeamento protótipo Replit → código ATS
- `read_replit` — Leitura do protótipo via SSH
- `map_replit_to_project` — Mapeamento de componentes
- `get_conventions` — Convenções do projeto
- `check_ats_health` — Health check dos serviços locais
- `rails_exec` — Execução de Ruby no Rails console
- `analyze_project` — Análise de estrutura do projeto

**Prompts pré-configurados:**
- `plan-from-ticket` — Gera plano de implementação a partir de ticket Jira
- `plan-from-description` — Gera plano a partir de descrição livre

---

## 9. Integrações Externas

| Serviço | Finalidade | Repos afetados | Tipo |
|---------|-----------|----------------|------|
| **WhatsApp (360dialog)** | Comunicação com candidatos | `lia-agent-system` | Webhook + API REST |
| **Microsoft Teams** | Interface do recrutador | `recruiter_agent_v5`, `lia-agent-system` | Bot Framework |
| **Google Gemini** | [AI] LLM — único provider em produção (ambos repos) | `recruiter_agent_v5`, `lia-agent-system` | API REST |
| **LangSmith** | [AI] Monitoramento de traces | `recruiter_agent_v5` | SDK Python |
| **Elasticsearch** | Busca full-text de candidatos/vagas | `ats_api` | Searchkick gem |
| **Redis** | Cache + filas Sidekiq + sessões | `ats_api`, `recruiter_agent_v5` | TCP |
| **RabbitMQ** | Fila de mensagens para workers Celery | `recruiter_agent_v5` | AMQP |
| **PostgreSQL** | Banco principal (multi-tenant) | `ats_api`, `recruiter_agent_v5` | Apartment gem |
| **WorkOS** | SSO e autenticação enterprise | `lia-agent-system` | SDK |
| **Apify** | Web scraping para sourcing | `lia-agent-system` | MCP + API |
| **Jira** | Gestão de tickets e specs | `ats_mcp`, scripts | API REST + OAuth |
| **ActionCable** | WebSockets real-time | `ats_api`, `ats_front` | Rails built-in |

---

## 10. Infraestrutura

| Componente | Tecnologia | Uso |
|-----------|-----------|-----|
| Banco de dados | PostgreSQL + Apartment gem | Multi-tenancy por schema |
| Cache | Redis | Sessions, Sidekiq, Celery, semantic cache |
| Background jobs (Ruby) | Sidekiq | Processamento assíncrono Rails |
| Background jobs (Python) | Celery + RabbitMQ | Agentes IA, evaluations |
| Search | Elasticsearch + Searchkick | Full-text candidates/jobs |
| Deploy | Google Cloud Platform (GCP) | VM + Cloud Run |
| Containers | Docker + docker-compose | Ambiente local |
| Process manager | systemd | Celery workers produção |

---

## 11. Elementos Especiais

### Marcações usadas neste documento

| Tag | Significado |
|-----|-------------|
| `[AI]` | Componente ou rota com lógica de IA |
| `[RESTRICTED]` | Acesso restrito por role ou compliance |
| `[ORPHAN]` | Componente ou rota sem uso identificado em produção |

### Componentes legados / protótipos

| Item | Localização | Status |
|------|-------------|--------|
| `plataforma-lia` (completo) | Replit | [ORPHAN] Protótipo — migrar features aprovadas para `ats_front` |
| `/mockup-shadcn-vue-page.tsx` | `plataforma-lia` | [ORPHAN] Experimento de migração Vue |
| Páginas arquivadas | `plataforma-lia/src/components/pages/archived/` | [ORPHAN] Features descontinuadas |

---

## 12. Dev Workflow — Spec Driven Development

```
1. Ideia → PM prototipa em plataforma-lia (Replit)
          ↓
2. Spec  → Card Jira criado com template SDD
          │  (inclui: comportamento esperado, critérios, arquivos afetados)
          ↓
3. Dev   → ats_mcp lê o card + protótipo automaticamente
          │  Claude Code / Cursor com contexto completo
          ↓
4. Code  → Implementação em ats_api + ats_front
          ↓
5. Test  → RSpec (ats_api) + Vitest (ats_front)
          ↓
6. PR    → Referencia o card Jira + atualiza docs impactados
```

**Documentos SDD (status):**

| Documento | Localização | Status |
|-----------|-------------|--------|
| `PLATFORM_MAP.md` | `docs/PLATFORM_MAP.md` | Atualizado |
| `AI_ARCHITECTURE.md` | `docs/specs/ai/AI_ARCHITECTURE.md` | Criado |
| `AGENT_SPECS.md` | `docs/specs/ai/AGENT_SPECS.md` | Criado |
| `LLM_DECISIONS.md` | `docs/specs/ai/LLM_DECISIONS.md` | Criado |
| `PROMPT_STANDARDS.md` | `docs/specs/ai/PROMPT_STANDARDS.md` | Criado |
| `AI_FAILURE_MODES.md` | `docs/specs/ai/AI_FAILURE_MODES.md` | Criado |
| `LIA_AUTOMATION.md` | `docs/specs/ai/LIA_AUTOMATION.md` | Criado (unificação de 4 docs) |
| `DATA_MODELS.md` | `docs/specs/backend/DATA_MODELS.md` | Criado |
| `API_CONTRACTS.md` | `docs/specs/backend/API_CONTRACTS.md` | Criado |
| `FRONTEND_STANDARDS.md` | `docs/specs/frontend/FRONTEND_STANDARDS.md` | Criado |
| `DESIGN_SYSTEM.md` | `docs/specs/frontend/DESIGN_SYSTEM.md` | Criado |
| `UX_PATTERNS.md` | `docs/specs/frontend/UX_PATTERNS.md` | Criado |
| `DIAGNOSTICO_REACT_VUE.md` | `docs/specs/frontend/DIAGNOSTICO_REACT_VUE.md` | Criado — 114 itens comparativos com coluna de decisão |
| `INVENTARIO_COMPONENTES.md` | `docs/specs/frontend/INVENTARIO_COMPONENTES.md` | Criado — 465 componentes + análise de otimização + plano de 6 fases |
| `QA_PROTOCOL.md` | `docs/specs/qa/QA_PROTOCOL.md` | Criado |
| `AI_QA_PROTOCOL.md` | `docs/specs/qa/AI_QA_PROTOCOL.md` | Criado |
| `GOLDEN_DATASET.md` | `docs/specs/qa/GOLDEN_DATASET.md` | Criado |
| `CONTRIBUTING.md` | `docs/specs/process/CONTRIBUTING.md` | Criado |
| `ONBOARDING.md` | `docs/specs/process/ONBOARDING.md` | Criado |
| `SPEC_TEMPLATE.md` | `docs/specs/process/SPEC_TEMPLATE.md` | Criado |
