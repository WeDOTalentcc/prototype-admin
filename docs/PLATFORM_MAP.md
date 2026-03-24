# Platform Map — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
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

> Baseado em `PRODUCT_CAPABILITIES.md` do `recruiter_agent_v5` e `plataforma-lia/src/app/`.

### 3.1 Navegação Principal (recrutador)

| Rota | Descrição | Role |
|------|-----------|------|
| `/user/dashboard` | Dashboard principal | recruiter |
| `/user/jobs` | Lista de vagas | recruiter |
| `/user/jobs?tab=active` | Vagas ativas | recruiter |
| `/user/jobs?tab=paused` | Vagas pausadas | recruiter |
| `/user/jobs?tab=archived` | Vagas arquivadas | recruiter |
| `/user/jobs?tab=urgent` | Vagas urgentes | recruiter |
| `/user/candidates` | Lista de candidatos | recruiter |
| `/user/candidates?tab=candidatos` | Todos os candidatos | recruiter |
| `/user/candidates?tab=favoritos` | Candidatos favoritos | recruiter |
| `/user/evaluations` | Avaliações e testes | recruiter |
| `/user/control-panel` | Painel de controle | recruiter |
| `/user/lia` | Interface direta com a LIA | recruiter |
| `/user/admin/dashboard` | Dashboard administrativo | [RESTRICTED] admin |

### 3.2 Fluxos Funcionais (plataforma-lia — protótipo)

| Rota | Descrição | Status |
|------|-----------|--------|
| `/jobs` | Lista de vagas | Protótipo |
| `/jobs/[id]` | Detalhe da vaga + Kanban | Protótipo |
| `/funil-de-talentos` | Funil de candidatos | Protótipo |
| `/funil-de-talentos/candidato/[id]` | Perfil no funil | Protótipo |
| `/triagem/[token]` | Triagem pública do candidato | [AI] Protótipo |
| `/chat` | Interface de chat com LIA | [AI] Protótipo |
| `/tasks` | Tarefas | Protótipo |
| `/vagas/[slug]` | Portal público de vagas | Protótipo |
| `/portal/data-request/[token]` | [RESTRICTED] LGPD — solicitação de dados | Compliance |
| `/configuracoes` | Configurações da conta | recruiter |
| `/configuracoes/integracoes` | Integrações externas | admin |
| `/configuracoes/ai-credits` | [AI] Créditos de IA | admin |

### 3.3 Admin (super-admin WeDOTalent)

| Rota | Descrição |
|------|-----------|
| `/admin` | Dashboard super-admin |
| `/admin/clientes/[clientId]/*` | Gestão por cliente (setup, users, metrics, billing...) |
| `/admin/compliance/*` | LGPD, SOC-2, ISO-27001, auditoria |
| `/admin/configuracoes/*` | Configurações globais, comunicações, políticas |
| `/admin/jornada-recrutamento` | Jornada de recrutamento |
| `/admin/templates` | Templates globais |
| `/admin/sso` | [RESTRICTED] SSO configuration |

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

**5 Domínios:**

| Domain ID | Pasta | Responsabilidade | Actions principais |
|-----------|-------|------------------|--------------------|
| `jobs` | `src/domains/jobs/` | CRUD e analytics de vagas | list, detail, analytics, pipeline, readiness |
| `applies` | `src/domains/applies/` | Pipeline de candidaturas | search, scoring, bulk, comparison, pipeline |
| `sourced_profile_sourcing` | `src/domains/sourced_profile_sourcing/` | Busca e comparação de candidatos | search, compare, rank, enrich |
| `scheduling` | `src/domains/scheduling/` | Agendamento multi-turno | schedule, reschedule, cancel, availability |
| `evaluation` | `src/domains/evaluation/` | Avaliações e testes | evaluate, score, report |

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

**LLM:** Anthropic Claude (via integração modelFarm)
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

## 7. Design System — `wedo-nuxt`

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
| **Google Gemini** | [AI] LLM para agente V5 | `recruiter_agent_v5` | API REST |
| **Anthropic Claude** | [AI] LLM para LIA | `lia-agent-system` | API REST (modelFarm proxy) |
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

**Documentos SDD (a criar — veja tasks relacionadas):**
- `docs/PLATFORM_MAP.md` ← este documento
- `docs/ARCHITECTURE.md`
- `docs/CODING_STANDARDS.md`
- `docs/specs/standards/FRONTEND_STANDARDS.md`
- `docs/specs/standards/BACKEND_STANDARDS.md`
- `docs/specs/standards/AI_ARCHITECTURE.md`
- `docs/specs/standards/AGENT_SPECS.md`
- `docs/specs/standards/PROMPT_STANDARDS.md`
- `docs/specs/qa/GOLDEN_DATASET.md`
- `docs/specs/templates/SPEC_TEMPLATE.md`
- `docs/specs/templates/AGENT_SPEC_TEMPLATE.md`
- `docs/specs/templates/JIRA_CARD_TEMPLATE.md`

---

> **Próximos documentos SDD:** Ver `docs/ARCHITECTURE.md` para decisões técnicas, `docs/specs/standards/AI_ARCHITECTURE.md` para orquestração de agentes.
