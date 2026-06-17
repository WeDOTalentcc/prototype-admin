# Background Agent — Documentação Técnica Completa (Backend)

## Visão Geral

O Background Agent é um sistema de sourcing autônomo que busca candidatos de forma recorrente para uma vaga. Ele opera como um "recrutador automático" que:

1. Recebe critérios de busca vinculados a um `Job`
2. Executa buscas via um worker Python (LangGraph)
3. Avalia e pontua candidatos com IA
4. Entrega resultados para revisão do recrutador
5. Aprende com o feedback (aprovações/rejeições) para refinar buscas futuras

### Arquitetura de Alto Nível

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vue/Nuxt)                          │
│  Cria agent → Revisa candidatos → Aprova/Rejeita → Vê progresso     │
└─────────┬──────────────┬──────────────────────────┬──────────────────┘
          │ REST API      │ WebSocket (ActionCable)   │ REST API
          ▼              ▲                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                           RAILS API                                  │
│                                                                      │
│  BackgroundAgentsController ◄──── Authenticable (JWT + tenant)       │
│  AgentCyclesController                                               │
│  AgentFeedbacksController                                            │
│                                                                      │
│  Services:                                                           │
│    PublishToAgentService ──── cria Cycle + Sourcing + publica msg     │
│    BuildSearchContextService ── monta payload de contexto            │
│    ProcessFeedbackService ──── processa aprovações/rejeições         │
│    DeliverCandidatesService ── persiste candidatos entregues         │
│    ExtractPreferencesJob ──── extrai padrões de feedback             │
│                                                                      │
│  Channels:                                                           │
│    BackgroundAgentChannel ──── broadcast de progresso em tempo real   │
└─────────┬──────────────────────────────────────────┬─────────────────┘
          │ RabbitMQ                                  │ HTTP (report_progress)
          ▼                                           │
┌──────────────────────────────────────────────────────────────────────┐
│                        PYTHON WORKER                                 │
│                                                                      │
│  Consome fila RabbitMQ: background_agents.search                     │
│  Executa grafo LangGraph:                                            │
│    load_context → plan → generate_queries → search → evaluate        │
│      → score → deliver                                               │
│  Reporta progresso via POST /report_progress a cada step             │
│  Entrega candidatos via POST /deliver_cycle                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Modelos de Dados

### 1. `BackgroundAgent`

Entidade principal. Representa um agente de busca vinculado a uma vaga.

**Tabela:** `background_agents` (tenant-scoped)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | bigint | PK |
| `job_id` | FK | Vaga vinculada |
| `user_id` | FK | Recrutador dono |
| `account_id` | FK | Conta (tenant) |
| `name` | string | Nome do agente (default: título da vaga) |
| `criteria_text` | text | Critérios de busca em texto livre |
| `criteria_structured` | jsonb | Critérios estruturados (skills, seniority, etc.) |
| `calibration_state` | string | `pending` → `learning` → `calibrated` |
| `mode` | string | `review` (manual) ou `auto_add` (automático) |
| `status` | string | `active`, `paused`, `stopped` |
| `daily_limit` | integer | Máximo de candidatos/dia (default: 25) |
| `total_delivered` | integer | Total acumulado de candidatos entregues |
| `total_approved` | integer | Total aprovados pelo recrutador |
| `total_rejected` | integer | Total rejeitados pelo recrutador |
| `consecutive_approvals` | integer | Aprovações consecutivas (para sugerir auto_add) |
| `sources` | string[] | Providers de busca: `["local"]`, `["local", "pearch"]`, `["local", "linkedin"]` |
| `min_score_threshold` | float | Score mínimo para entregar candidato (default: 70.0) |
| `extracted_preferences` | jsonb | Preferências extraídas do feedback (skills, títulos, etc.) |
| `search_iteration_config` | jsonb | Config de iterações de busca (max iterations, min quality, providers) |
| `search_history` | jsonb | Histórico das últimas 100 iterações de busca |
| `diversity_queries` | jsonb | Queries de diversidade geradas pela IA |
| `auto_pause_days` | integer | Dias sem interação antes de pausar automaticamente (default: 4) |
| `last_interaction_at` | datetime | Última interação do recrutador (feedback) |
| `last_run_at` | datetime | Última execução do agente |
| `last_run_metadata` | jsonb | Metadados da última execução |
| `is_deleted` | boolean | Soft delete |

**Scopes:**
- `active` — status=active + is_deleted=false
- `runnable` — active + (last_run_at IS NULL OR < hoje)
- `calibrated` — calibration_state=calibrated

**Lifecycle de calibração:**
```
pending ──(1° feedback)──→ learning ──(5+ feedbacks)──→ calibrated
```
Ao atingir `calibrated`, o `ExtractPreferencesJob` analisa padrões de aprovação/rejeição.

### 2. `AgentCycle`

Cada execução do agente gera um ciclo. Um agente pode ter múltiplos ciclos ao longo do tempo.

**Tabela:** `agent_cycles` (tenant-scoped)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | bigint | PK |
| `background_agent_id` | FK | Agente pai |
| `sourcing_id` | FK | Sourcing associado (contém os candidatos encontrados) |
| `cycle_number` | integer | Número sequencial do ciclo (unique por agente) |
| `status` | string | `running` → `delivered` → `reviewed` / `expired` / `cancelled` |
| `candidates_delivered` | integer | Quantidade de candidatos entregues |
| `candidates_total_found` | integer | Total encontrados na busca (antes do filtro) |
| `execution_metadata` | jsonb | Métricas da execução (duração, iterações, providers, etc.) |
| `delivered_at` | datetime | Quando foi entregue |
| `reviewed_at` | datetime | Quando o recrutador revisou todos |
| `expires_at` | datetime | Expira 48h após entrega |

**Lifecycle:**
```
running ──(deliver_cycle)──→ delivered ──(todos feedbacks)──→ reviewed
                                 └──(48h sem revisão)──→ expired
                                 └──(agente deletado)──→ cancelled
```

### 3. `AgentFeedback`

Feedback do recrutador sobre cada candidato entregue.

**Tabela:** `agent_feedbacks` (tenant-scoped)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | bigint | PK |
| `background_agent_id` | FK | Agente |
| `agent_cycle_id` | FK | Ciclo em que foi entregue |
| `sourced_profile_sourcing_id` | FK | Candidato avaliado (unique por agente) |
| `action` | string | `approved` ou `rejected` |
| `reason` | text | Motivo (opcional, mais comum em rejeições) |

### 4. `BackgroundAgentStep`

Registro persistido de cada etapa de execução, para histórico e real-time via WebSocket.

**Tabela:** `background_agent_steps` (tenant-scoped)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | bigint | PK |
| `background_agent_id` | FK | Agente |
| `agent_cycle_id` | FK | Ciclo (opcional) |
| `step` | string | `plan`, `load_context`, `generate_queries`, `search`, `evaluate`, `score`, `deliver` |
| `status` | string | `running`, `done`, `error` |
| `message` | string | Descrição legível do que está acontecendo |
| `details` | jsonb | Dados ricos (queries, candidatos, gaps, diagnósticos, scores) |
| `iteration_number` | integer | Número da iteração (para steps que repetem) |

---

## Fluxo Completo: Ponta a Ponta

### Fase 1: Criação do Agente

```
Frontend: POST /v1/users/background_agents
  body: { background_agent: { job_id: 42, criteria_text: "Senior Ruby developer...", mode: "review" } }
```

**Controller `#create`:**
1. Valida params, define `name` (titulo da vaga se vazio), `mode` (default "review")
2. Cria `BackgroundAgent` com `status: "active"`, `calibration_state: "pending"`
3. Enfileira `BackgroundAgents::SetupJob.perform_async(agent.id, account_id)`
4. Retorna o agent serializado (201 Created)

**SetupJob:**
1. Faz `Apartment::Tenant.switch!(account.tenant)`
2. Chama `PublishToAgentService.new(background_agent: agent).call`

### Fase 2: Publicação no RabbitMQ

**`PublishToAgentService#call`:**

1. **Validações:**
   - Agent precisa estar `active`
   - `remaining_today` precisa ser > 0 (verifica quota diária)

2. **Cria Sourcing:**
   ```ruby
   Sourcing.create!(
     user_id: agent.user_id,
     provider: "background_agent",
     query: agent.criteria_text || job.title,
     status: "processing"
   )
   ```

3. **Cria AgentCycle:**
   ```ruby
   agent.agent_cycles.create!(
     sourcing: sourcing,
     cycle_number: agent.next_cycle_number,  # sequencial
     status: "running"
   )
   ```

4. **Monta contexto** via `BuildSearchContextService`:
   - Dados do agent (critérios, preferências, config)
   - Dados do job (título, skills, localidade)
   - Histórico de feedback (últimos 50, padrões de aprovação/rejeição)
   - IDs de perfis já apresentados (para não repetir)
   - IDs de candidatos já na vaga (para não duplicar)
   - Histórico de buscas (últimas 10 iterações)
   - Configuração de busca

5. **Gera JWT one-time-token** para o worker Python autenticar no Rails

6. **Publica no RabbitMQ:**
   ```
   Exchange: "background_agents" (direct, durable)
   Routing Key: "background_agents.search"
   Payload: {
     operation: "execute_intelligent_search",
     background_agent_id, cycle_id, sourcing_id,
     account_id, user_id,
     auth: { one_time_token, exchange_url, api_base_url },
     context: { agent, job, feedback_history, search_config, ... }
   }
   ```

### Fase 3: Processamento no Python

O worker Python consome a fila `background_agents.search` e executa um grafo LangGraph:

```
load_context → plan → generate_queries → search → evaluate
                                            ↑          ↓
                                            ├── reformulate (se NEEDS_IMPROVEMENT)
                                            └── paginate (se PAGINATE_MORE)
                                                       ↓
                                          score → deliver
```

**A cada step, o Python faz:**
```
POST /v1/users/background_agents/{id}/report_progress
  Authorization: Bearer {one_time_token}
  body: { step, status, message, cycle_id, iteration_number, details }
```

### Fase 4: Persistência de Progresso (Rails)

**Controller `#report_progress`** (requer service token):

1. Cria `BackgroundAgentStep` no banco (persistência)
2. Faz broadcast via `BackgroundAgentChannel`:
   ```ruby
   BackgroundAgentChannel.broadcast_to(
     "#{agent.user_id}_agent_#{agent.id}",
     { type: "progress", step, status, message, details, ... }
   )
   ```
3. Frontend recebe em tempo real via WebSocket

**Steps e seus `details` típicos:**

| Step | Details |
|------|---------|
| `plan` | `{ plan_text: "...", strategies: [...], estimated_iterations: 2 }` |
| `load_context` | `{ job_title: "...", has_preferences: true, feedback_count: 12 }` |
| `generate_queries` | `{ queries_count: 5, queries: [...] }` |
| `search` | `{ provider: "local", candidates_found: 23, strategies_used: [...] }` |
| `evaluate` | `{ quality_score: 0.72, gaps: [...], diagnosis: "...", decision: "GOOD_ENOUGH" }` |
| `score` | `{ candidates_scored: 20, average_score: 78.5, above_threshold: 15 }` |
| `deliver` | `{ candidates_delivered: 10, total_found: 45, duration_ms: 32500 }` |

### Fase 5: Entrega de Candidatos

Quando o Python termina, chama:

```
POST /v1/users/background_agents/{id}/deliver_cycle
  body: {
    cycle_id: 22,
    candidates_count: 10,
    total_found: 45,
    metadata: { duration_seconds: 32, iterations_count: 2, providers_used: ["local"] },
    candidates: [
      { candidate_id: 123, score: 85.2, category: "A", justification: "...", strengths: [...] },
      ...
    ]
  }
```

**Controller `#deliver_cycle`:**

1. Atualiza `AgentCycle` → status `delivered`, `candidates_delivered`, `delivered_at`, `expires_at = 48h`
2. Chama `DeliverCandidatesService`:
   - Para cada candidato: encontra/cria `SourcedProfile` + `SourcedProfileSourcing`
   - Salva `ai_metadata` com score, justificativa, strengths, concerns
3. Atualiza `BackgroundAgent`: `total_delivered`, `last_run_at`, `last_run_metadata`
4. Broadcast via WebSocket: `{ type: "cycle_delivered", cycle_id, cycle_number }`

### Fase 6: Revisão pelo Recrutador (Feedback)

O recrutador vê os candidatos entregues no frontend e aprova/rejeita cada um:

```
POST /v1/users/background_agents/{id}/feedbacks
  body: { feedback: { sourced_profile_sourcing_id: 456, action: "approved" } }

POST /v1/users/background_agents/{id}/feedbacks/bulk
  body: { feedbacks: [{ sourced_profile_sourcing_id: 456, action: "approved" }, ...] }
```

**`ProcessFeedbackService#call`:**

1. **Cria `AgentFeedback`** para cada item (unique por agent + profile)
2. **Atualiza contadores**: `total_approved`, `total_rejected`
3. **Atualiza calibração**:
   - < 5 feedbacks → `learning`
   - ≥ 5 feedbacks → `calibrated` + trigger `ExtractPreferencesJob`
4. **Conta aprovações consecutivas** (para sugerir `auto_add`)
5. **Atualiza `last_interaction_at`** (reseta o auto-pause timer)
6. Se todos os candidatos do ciclo foram avaliados → marca ciclo como `reviewed`

### Fase 7: Extração de Preferências

**`ExtractPreferencesJob`** (Sidekiq, async):

1. Carrega últimos 10 feedbacks aprovados e 10 rejeitados
2. Analisa padrões:
   - Skills mais comuns nos aprovados
   - Títulos/empresas/locais preferidos
   - Range de experiência
   - Motivos de rejeição mais frequentes
3. Salva em `agent.extracted_preferences`
4. Na próxima execução, o Python usa essas preferências para refinar buscas

### Fase 8: Execução Recorrente (Cron)

**`BackgroundAgents::CronJob`** — roda 2x/dia (9h e 15h UTC, seg-sex):

1. Sem argumentos: enfileira um job por `Account`
2. Com `account_id`: processa aquela conta
3. Para cada `BackgroundAgent.runnable`:
   - Verifica auto-pause (sem interação por N dias → pausa)
   - Se ainda ativo: chama `PublishToAgentService` → novo ciclo

**Scope `runnable`:**
```ruby
active.where("last_run_at IS NULL OR last_run_at < ?", Time.current.beginning_of_day)
```
Garante no máximo 1 execução/dia (mesmo com 2 crons).

---

## Busca em Providers Externos

Além do provider `local` (Elasticsearch/candidates internos), o agent pode buscar em:

### Pearch (Talent Search)

```
POST /v1/users/background_agents/{id}/pearch_search
  body: { query: "Senior Ruby developer", limit: 10, ... }
```
- Requer créditos Pearch na conta (`account.pearch_credits`)
- Usa `Pearch::TalentSearchExecutorService`
- Retorna perfis externos

### LinkedIn (via Apify)

```
POST /v1/users/background_agents/{id}/linkedin_search
  body: { query: "Ruby developer", locations: ["Brazil"], limit: 25, ... }
```
- Cria um `Sourcing` com `provider: "linkedin"`
- Usa `Apify::LinkedinSearchExecutorService`
- Retorna perfis do LinkedIn via scraping

---

## WebSocket (ActionCable)

### Canal: `BackgroundAgentChannel`

**Subscription:**
```javascript
{ channel: "BackgroundAgentChannel", agent_id: 1 }
```

**Stream:** `background_agent:{user_id}_agent_{agent_id}`

**Segurança:** Só aceita se `agent.user_id == current_user.id`

**Tipos de mensagem broadcast:**

| type | Quando | Dados |
|------|--------|-------|
| `progress` | Cada step da execução | `step, status, message, details, iteration_number, timestamp` |
| `cycle_delivered` | Candidatos entregues | `cycle_id, cycle_number, profiles_created` |
| `cycle_reviewed` | Todos feedbacks dados | `cycle_id, cycle_number` |

---

## APIs REST Completas

### Endpoints do Recrutador (JWT de usuário)

| Método | Path | Ação |
|--------|------|------|
| GET | `/background_agents` | Listar agentes do recrutador |
| POST | `/background_agents` | Criar novo agente |
| GET | `/background_agents/:id` | Detalhe do agente |
| PATCH | `/background_agents/:id` | Atualizar agente |
| DELETE | `/background_agents/:id` | Soft delete (para ciclos, desativa) |
| POST | `/background_agents/:id/pause` | Pausar agente |
| POST | `/background_agents/:id/resume` | Reativar agente |
| POST | `/background_agents/:id/stop` | Parar agente definitivamente |
| GET | `/background_agents/:id/steps` | Histórico de steps (filtro: `cycle_id`, `step`) |
| POST | `/background_agents/:id/reset_cycles` | Resetar todos ciclos/feedbacks (recomeçar) |
| GET | `/background_agents/:id/cycles` | Listar ciclos do agente |
| GET | `/background_agents/:id/cycles/:id` | Detalhe de um ciclo |
| POST | `/background_agents/:id/feedbacks` | Dar feedback (aprovação/rejeição) |
| POST | `/background_agents/:id/feedbacks/bulk` | Feedback em lote (max 100) |

### Endpoints de Serviço (JWT service/one_time_token — usado pelo Python)

| Método | Path | Ação |
|--------|------|------|
| GET | `/background_agents/runnable` | Listar agentes prontos para executar |
| GET | `/background_agents/:id/search_context` | Contexto completo para busca |
| POST | `/background_agents/:id/deliver_cycle` | Entregar resultados de um ciclo |
| PATCH | `/background_agents/:id/update_preferences` | Atualizar preferências extraídas |
| PATCH | `/background_agents/:id/update_status` | Atualizar status do agente |
| POST | `/background_agents/:id/log_search_iteration` | Logar iteração de busca |
| POST | `/background_agents/:id/report_progress` | Reportar progresso (persiste + broadcast WS) |
| POST | `/background_agents/:id/pearch_search` | Buscar no Pearch |
| POST | `/background_agents/:id/linkedin_search` | Buscar no LinkedIn |

---

## Execução Manual

### Via Rails console

```ruby
BackgroundAgents::SetupJob.new.perform(AGENT_ID, ACCOUNT_ID)
```

### Via rake task

```bash
docker compose exec web bin/rails "background_agents:run[AGENT_ID]"
docker compose exec web bin/rails "background_agents:run[AGENT_ID,ACCOUNT_ID]"
```

---

## Diagrama de Relacionamentos

```
BackgroundAgent (1)
  ├── belongs_to Job
  ├── belongs_to User
  ├── belongs_to Account
  │
  ├── has_many AgentCycles (1:N)
  │     ├── belongs_to Sourcing
  │     ├── has_many AgentFeedbacks (1:N)
  │     │     └── belongs_to SourcedProfileSourcing
  │     └── status: running → delivered → reviewed/expired
  │
  ├── has_many AgentFeedbacks (1:N, direto)
  │
  └── has_many BackgroundAgentSteps (1:N)
        └── step + status + details (progresso em tempo real)
```

---

## Sidekiq/Cron

**Queue:** `background_agents` (concurrency: 3)

| Job | Trigger | Retry |
|-----|---------|-------|
| `SetupJob` | Criação de agent via API | 3 |
| `CronJob` | Cron 9h + 15h UTC (seg-sex) | 1 |
| `ExtractPreferencesJob` | Ao atingir 5+ feedbacks | 2 |

---

## Multi-tenancy

- Todas as tabelas (`background_agents`, `agent_cycles`, `agent_feedbacks`, `background_agent_steps`) são **tenant-scoped**
- Controllers: tenant switch automático via `Authenticable` (JWT)
- Sidekiq jobs: **sempre** fazem `Apartment::Tenant.switch!(account.tenant)` manual
- Python worker: usa one_time_token JWT que carrega `account_id` → Rails faz o switch na autenticação
