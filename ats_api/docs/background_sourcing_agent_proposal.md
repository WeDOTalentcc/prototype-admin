# Background Sourcing Agent — Proposta Técnica Rails

## Visão Geral

Agente autônomo de sourcing que roda em background (diariamente), busca candidatos para uma vaga, pontua via IA, e entrega batches para o recrutador revisar. O recrutador dá feedback (approve/reject com motivo), e o agente refina os critérios nos ciclos seguintes.

Inspirado no PeopleGPT/Juicebox, mas construído **em cima da infraestrutura que já temos** — sem duplicar modelos, serviços ou pipelines existentes.

---

## Princípio Arquitetural: Reusar, Não Duplicar

O sistema atual já possui uma pipeline completa de sourcing:

| Componente existente | O que faz | Como o agent reusa |
|---|---|---|
| `Sourcing` | Sessão de busca com query, provider, status, parameters | Cada ciclo do agent cria um `Sourcing` normal |
| `SourcedProfile` | Perfil encontrado (nome, experiência, skills, etc.) | Candidatos do agent são `SourcedProfile` normais |
| `SourcedProfileSourcing` | Join profile↔sourcing com score + analysis IA | Score e análise vivem aqui, como sempre |
| `HybridSearchService` | Busca local (ES + pgvector) | Agent usa para busca local |
| `Pearch::SearchService` | Busca global (800M+ perfis) | Agent usa para busca global |
| `ProfileAnalyzer` | Pontuação 0-99 com rubrica (Gemini) | Agent usa para scoring |
| `AiAnalysisJob` | Job async de análise IA | Agent redireciona para o mesmo job |
| `AutoAddCandidateService` | Adiciona candidato à vaga automaticamente | Agent usa no modo `full_auto` |
| `SourcingChannel` | WebSocket para updates em tempo real | Agent notifica por aqui |
| `CandidateFeedback` | Like/dislike em perfis | Agent estende com feedback estruturado |
| `RecruitAgentService` | HTTP client para Python API | Agent estende com novos endpoints |
| `QueryRequirementsExtractor` | Extrai requisitos estruturados da query | Agent usa para critérios iniciais |

**O que é genuinamente novo:**
- Conceito de um agente com lifecycle (active → paused → stopped)
- Mecanismo de calibração (3 approvals consecutivos)
- Ciclos diários programados via cron
- Diversificação de queries entre ciclos
- Feedback estruturado que alimenta refinamento de busca
- Auto-pause por inatividade do recrutador

---

## Modelos de Dados

### 1. BackgroundAgent (novo)

Representa o agente configurado pelo recrutador para uma vaga.

```
background_agents
├── job_id (FK → jobs, NOT NULL)
├── user_id (FK → users, NOT NULL)
├── account_id (FK → accounts, NOT NULL)
├── name (string, NOT NULL) — ex: "Sourcing Backend Sr - SP"
├── criteria_text (text) — descrição em linguagem natural do candidato ideal
├── criteria_structured (jsonb, default: {}) — gerado pela LLM a partir do criteria_text
│   Estrutura: {
│     skills: ["ruby", "rails", "postgresql"],
│     seniority: "senior",
│     location: { city: "São Paulo", state: "SP", remote: true },
│     experience_years: { min: 5, max: null },
│     companies: ["nubank", "ifood", "stone"],
│     deal_breakers: ["sem experiência com APIs REST"],
│     nice_to_haves: ["experiência com Elasticsearch"]
│   }
├── calibration_state (string, NOT NULL, default: "pending")
│   Valores: pending → calibrating → calibrated
├── consecutive_approvals (integer, default: 0) — target: 3 para calibrar
├── extracted_preferences (jsonb, default: {}) — padrões extraídos dos feedbacks pela LLM
│   Estrutura: {
│     preferred_company_types: ["fintech", "scale-up"],
│     skill_weights: { "ruby": 0.9, "python": 0.6 },
│     deal_breakers: ["menos de 3 anos experiência"],
│     nice_to_haves: ["open source contributions"]
│   }
├── mode (string, NOT NULL, default: "review")
│   Valores: full_auto | review | shortlist
├── status (string, NOT NULL, default: "active")
│   Valores: active | paused | out_of_leads | stopped | failed
├── daily_limit (integer, default: 25) — máximo de candidatos por ciclo
├── total_delivered (integer, default: 0)
├── total_approved (integer, default: 0)
├── total_rejected (integer, default: 0)
├── auto_pause_days (integer, default: 4)
├── sources (string, array: true, default: ["local"]) — ["local"], ["global"], ["local", "global"]
├── min_score_threshold (float, default: 70.0) — score mínimo para incluir no batch
├── last_interaction_at (datetime) — último feedback do recrutador
├── last_run_at (datetime) — última execução do cron
├── last_run_metadata (jsonb, default: {}) — stats da última execução
├── diversity_queries (jsonb, default: []) — queries diversificadas da última run
├── paused_at (datetime)
├── stopped_at (datetime)
├── is_deleted (boolean, default: false, NOT NULL)
├── timestamps
└── Indexes: [status], [calibration_state], [status, calibration_state], [job_id], [user_id]
```

**Decisão: sem `presented_profile_ids` array.** A deduplicação é feita via query:
```ruby
# Perfis já apresentados = todos os SourcedProfile vinculados a Sourcings deste agent
already_presented_ids = SourcedProfile
  .joins(:sourced_profile_sourcings)
  .where(sourced_profile_sourcings: { sourcing_id: agent.agent_cycles.select(:sourcing_id) })
  .pluck(:id)
```
Isso escala melhor que um array integer[] que cresce indefinidamente.

**Decisão: sem `approved_profiles`/`rejected_profiles` JSONB.** Esses dados já vivem em `AgentFeedback`. Counters (`total_approved`, `total_rejected`) são suficientes no model.

### 2. AgentCycle (novo)

Cada execução diária do agent produz um cycle. O cycle é um wrapper fino sobre um `Sourcing` existente.

```
agent_cycles
├── background_agent_id (FK → background_agents, NOT NULL)
├── sourcing_id (FK → sourcings, NOT NULL) — O Sourcing real criado neste ciclo
├── cycle_number (integer, NOT NULL) — 1, 2, 3... sequencial
├── status (string, NOT NULL, default: "running")
│   Valores: running | delivered | reviewed | expired | failed
├── candidates_delivered (integer, default: 0) — quantos perfis passaram no threshold
├── candidates_total_found (integer, default: 0) — total encontrado antes do filtro
├── execution_metadata (jsonb, default: {})
│   Estrutura: {
│     started_at: "2026-03-22T06:00:00Z",
│     finished_at: "2026-03-22T06:12:00Z",
│     duration_ms: 720000,
│     queries_executed: ["ruby senior SP", "rails backend fintech", ...],
│     search_sources: ["local", "global"],
│     llm_tokens_used: 45000,
│     llm_cost_usd: 0.0045
│   }
├── delivered_at (datetime)
├── reviewed_at (datetime)
├── expires_at (datetime) — batch expira se não revisado em 7 dias
├── timestamps
└── Indexes: [background_agent_id, status], [sourcing_id], [background_agent_id, cycle_number]
```

**Por que `AgentCycle` em vez de `AgentBatch`?**
- O nome "cycle" reflete melhor a natureza iterativa (cada um refina o anterior)
- Cada cycle **aponta para um `Sourcing`** real — não duplica candidatos em JSONB
- Os candidatos do cycle são acessados via `cycle.sourcing.sourced_profile_sourcings`
- O score, analysis, e todos os dados IA já existem no `SourcedProfileSourcing`

**Acesso aos candidatos de um cycle:**
```ruby
cycle.sourcing.sourced_profile_sourcings
  .includes(:sourced_profile)
  .where(is_deleted: false)
  .where("score >= ?", agent.min_score_threshold)
  .order(score: :desc)
  .limit(agent.daily_limit)
```

### 3. AgentFeedback (novo)

Feedback estruturado do recrutador sobre cada candidato apresentado pelo agent.

```
agent_feedbacks
├── background_agent_id (FK → background_agents, NOT NULL)
├── agent_cycle_id (FK → agent_cycles, NOT NULL)
├── sourced_profile_sourcing_id (FK → sourced_profile_sourcings, NOT NULL)
├── action (string, NOT NULL)
│   Valores: approved | rejected | skipped | shortlisted
├── reason (text) — obrigatório se rejected, motivo textual do recrutador
├── timestamps
└── Indexes:
    [background_agent_id, sourced_profile_sourcing_id] UNIQUE — um feedback por perfil por agent
    [agent_cycle_id]
    [action]
```

**Decisão: sem `profile_snapshot` JSONB.** O snapshot é desnecessário porque:
- O `SourcedProfileSourcing` já tem score + analysis
- O `SourcedProfile` já tem todos os dados do perfil
- Se precisar do "estado no momento do feedback", o `SourcedProfileSourcing.analysis` (que é imutável por ciclo) serve como snapshot

**Decisão: `sourced_profile_sourcing_id` em vez de `profile_id` integer.** Isso dá acesso direto ao perfil COM o score/analysis daquele ciclo específico, via FK real.

---

## Diagrama de Relacionamentos

```
BackgroundAgent
  ├── belongs_to :job (EXISTENTE)
  ├── belongs_to :user (EXISTENTE)
  ├── belongs_to :account (EXISTENTE)
  ├── has_many :agent_cycles
  │     ├── belongs_to :sourcing (EXISTENTE) ←── O coração da sinergia
  │     │     └── has_many :sourced_profile_sourcings (EXISTENTE)
  │     │           ├── belongs_to :sourced_profile (EXISTENTE)
  │     │           ├── score, analysis, ai_metadata (EXISTENTES)
  │     │           └── has_many :candidate_feedbacks (EXISTENTE)
  │     └── has_many :agent_feedbacks
  │           └── belongs_to :sourced_profile_sourcing (EXISTENTE)
  └── has_many :agent_feedbacks (through: :agent_cycles)
```

---

## Lifecycle do Agent

```
                    ┌─────────────────────────────────────────────┐
                    │           CRIAÇÃO DO AGENT                  │
                    │  POST /v1/users/background_agents           │
                    │  → criteria_text + job_id + mode            │
                    │  → status: active                           │
                    │  → calibration_state: pending               │
                    │  → Enfileira: SetupJob (parsear criteria)   │
                    └────────────────────┬────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │         SETUP (async, Python)               │
                    │  SetupJob → Python /parse-criteria          │
                    │  → Gera criteria_structured via LLM         │
                    │  → calibration_state: calibrating           │
                    │  → Roda primeiro ciclo de busca             │
                    │  → Entrega batch para calibração            │
                    └────────────────────┬────────────────────────┘
                                         │
                                         ▼
              ┌──────────────────────────────────────────────────────────┐
              │               CALIBRAÇÃO (loop)                         │
              │                                                         │
              │  Recrutador revisa candidatos do batch:                  │
              │  ┌─────────────────────────────────────────────┐        │
              │  │ APPROVE → consecutive_approvals += 1        │        │
              │  │   Se >= 3 → calibration_state: calibrated ──┼──→ SAÍDA
              │  │ REJECT (com motivo) → consecutive_approvals = 0      │
              │  │   → Enfileira: ExtractPreferencesJob         │        │
              │  │   → Recalibra critérios                      │        │
              │  └─────────────────────────────────────────────┘        │
              │                                                         │
              │  Se não calibrado, monta novo batch com critérios       │
              │  refinados e volta ao loop                              │
              └──────────────────────────────────────────────────────────┘
                                         │
                                         │ calibrated!
                                         ▼
              ┌──────────────────────────────────────────────────────────┐
              │          EXECUÇÃO AUTÔNOMA (cron diário)                 │
              │                                                         │
              │  BackgroundAgentCronJob roda a cada 12h:                 │
              │  ┌─────────────────────────────────────────────┐        │
              │  │ 1. Auto-pause agents sem interação > N dias │        │
              │  │ 2. Expirar cycles antigos não revisados     │        │
              │  │ 3. Para cada agent .runnable:                │        │
              │  │    a. Gerar queries diversificadas           │        │
              │  │    b. Criar Sourcing + AgentCycle            │        │
              │  │    c. Executar busca (local/global)          │        │
              │  │    d. AI analysis via ProfileAnalyzer        │        │
              │  │    e. Filtrar por min_score_threshold        │        │
              │  │    f. Entregar batch (status: delivered)     │        │
              │  │    g. Notificar recrutador (WebSocket)       │        │
              │  │    h. Se full_auto: auto-add à vaga          │        │
              │  └─────────────────────────────────────────────┘        │
              │                                                         │
              │  Recrutador revisa → feedback → ExtractPreferences       │
              │  → Critérios refinados para próximo ciclo               │
              └──────────────────────────────────────────────────────────┘
                                         │
                                         ▼
              ┌──────────────────────────────────────────────────────────┐
              │            CONDIÇÕES DE PARADA                          │
              │                                                         │
              │  • Recrutador para agent manualmente → stopped           │
              │  • Sem interação por N dias → paused (auto)             │
              │  • 3 ciclos consecutivos com < 3 candidatos → out_of_leads
              │  • Erro crítico → failed                                │
              └──────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Controller: V1::Users::BackgroundAgentsController

| Method | Path | Ação |
|---|---|---|
| GET | `/v1/users/background_agents` | Lista agents do user logado (filtro por status, job_id) |
| POST | `/v1/users/background_agents` | Cria agent (job_id, name, criteria_text, mode, sources, daily_limit) |
| GET | `/v1/users/background_agents/:id` | Detalhes do agent com stats |
| PATCH | `/v1/users/background_agents/:id` | Atualiza config (name, criteria_text, mode, daily_limit, sources) |
| DELETE | `/v1/users/background_agents/:id` | Soft-delete |
| POST | `/v1/users/background_agents/:id/pause` | Pausa o agent |
| POST | `/v1/users/background_agents/:id/resume` | Retoma execução |
| POST | `/v1/users/background_agents/:id/stop` | Para definitivamente |

**Serializer:** `BackgroundAgentSerializer` (JSONAPI::Serializer)

Atributos: name, criteria_text, mode, status, calibration_state, consecutive_approvals, daily_limit, sources, min_score_threshold, total_delivered, total_approved, total_rejected, last_run_at, last_interaction_at, created_at.

Atributos computados: job_title, pending_cycles_count, is_calibrated.

Atributo condicional (full): criteria_structured, extracted_preferences, last_run_metadata, diversity_queries.

Relações: belongs_to :job, belongs_to :user.

### Controller: V1::Users::AgentCyclesController

| Method | Path | Ação |
|---|---|---|
| GET | `/v1/users/background_agents/:background_agent_id/cycles` | Lista cycles (filtro por status) |
| GET | `/v1/users/background_agents/:background_agent_id/cycles/:id` | Detalhes do cycle com candidatos |

**Serializer:** `AgentCycleSerializer` (JSONAPI::Serializer)

Atributos: cycle_number, status, candidates_delivered, candidates_total_found, delivered_at, reviewed_at, created_at.

Atributo condicional (full): execution_metadata.

Relação: belongs_to :sourcing (para acessar os candidatos via relação existente).

**Candidatos do cycle:** Retornados via `SourcedProfileSourcingSerializer` existente — já tem score, analysis, dados do perfil. Sem serializer novo.

### Controller: V1::Users::AgentFeedbacksController

| Method | Path | Ação |
|---|---|---|
| POST | `/v1/users/background_agents/:background_agent_id/cycles/:agent_cycle_id/feedbacks` | Feedback individual |
| POST | `/v1/users/background_agents/:background_agent_id/cycles/:agent_cycle_id/feedbacks/bulk` | Feedback em lote |

**Request body (individual):**
```json
{
  "sourced_profile_sourcing_id": 123,
  "action": "rejected",
  "reason": "Pouca experiência com microsserviços"
}
```

**Request body (bulk):**
```json
{
  "feedbacks": [
    { "sourced_profile_sourcing_id": 123, "action": "approved" },
    { "sourced_profile_sourcing_id": 124, "action": "rejected", "reason": "Sem experiência em fintech" },
    { "sourced_profile_sourcing_id": 125, "action": "skipped" }
  ]
}
```

### Endpoints Internos (Python → Rails)

Estes endpoints ficam no namespace `V1::Services` já existente, autenticados via OTT/JWT service token.

| Method | Path | Ação |
|---|---|---|
| GET | `/v1/services/background_agents/runnable` | Lista agents prontos para execução (calibrated + active + last_run > 20h) |
| POST | `/v1/services/background_agents/:id/deliver_cycle` | Python entrega batch de um ciclo executado |
| PATCH | `/v1/services/background_agents/:id/update_preferences` | Python atualiza preferências extraídas |
| PATCH | `/v1/services/background_agents/:id/update_status` | Python reporta status (out_of_leads, failed) |

**Payload de `deliver_cycle`:**
```json
{
  "sourcing_id": 456,
  "candidates_delivered": 22,
  "candidates_total_found": 150,
  "execution_metadata": {
    "started_at": "2026-03-22T06:00:00Z",
    "finished_at": "2026-03-22T06:12:00Z",
    "duration_ms": 720000,
    "queries_executed": ["ruby senior SP", "rails backend fintech"],
    "llm_tokens_used": 45000,
    "llm_cost_usd": 0.0045
  }
}
```

O Rails então cria o `AgentCycle`, atualiza contadores, e notifica via WebSocket.

---

## Services

### BackgroundAgents::SetupService (novo)

Chamado ao criar o agent. Gera `criteria_structured` a partir de `criteria_text` + dados da vaga.

```
Input:  agent (BackgroundAgent)
Fluxo:
  1. Usa QueryRequirementsExtractor (EXISTENTE) para extrair requisitos da criteria_text
  2. Enriquece com dados do Job (skills, seniority, location)
  3. Salva criteria_structured no agent
  4. Muda calibration_state para "calibrating"
  5. Dispara primeiro ciclo de busca para calibração
Return: { success: true }
```

### BackgroundAgents::ExecuteCycleService (novo)

Orquestra a execução de um ciclo de busca para um agent.

```
Input:  agent (BackgroundAgent), queries (array de queries diversificadas)
Fluxo:
  1. Cria um Sourcing (EXISTENTE) com parameters indicando que é de background_agent
  2. Cria um AgentCycle apontando para o Sourcing
  3. Usa Sourcings::JobEnqueuerService (EXISTENTE) para enfileirar buscas
     → As buscas rodam normalmente via LoadMoreCandidatesJob / Pearch::TalentSearchJob
     → AI analysis roda via AiAnalysisJob (EXISTENTE)
  4. Marca cycle como "running"
  5. Quando sourcing completa (via callback ou polling):
     → Filtra perfis com score >= min_score_threshold
     → Deduplica contra ciclos anteriores
     → Atualiza cycle com stats
     → Se mode == "full_auto": usa AutoAddCandidateService (EXISTENTE)
     → Marca cycle como "delivered"
     → Notifica recrutador via SourcingChannel (EXISTENTE)
Return: { success: true, cycle_id: ... }
```

**Ponto chave:** Este service NÃO reimplementa busca ou scoring. Ele orquestra os componentes existentes.

### BackgroundAgents::ProcessFeedbackService (novo)

Processa feedback do recrutador e atualiza estado do agent.

```
Input:  agent, cycle, feedbacks (array)
Fluxo:
  1. Cria AgentFeedback para cada item
  2. Para approvals:
     → Incrementa consecutive_approvals
     → Se >= 3 no estado "calibrating" → calibration_state = "calibrated"
  3. Para rejections com motivo:
     → Reseta consecutive_approvals (se em calibrating)
     → Enfileira ExtractPreferencesJob
  4. Atualiza counters no agent (total_approved, total_rejected)
  5. Atualiza last_interaction_at
  6. Se todos perfis do cycle receberam feedback → cycle.status = "reviewed"
Return: { success: true, calibrated: agent.calibrated? }
```

### BackgroundAgents::ExtractPreferencesService (novo)

Extrai padrões dos feedbacks via LLM para refinar busca.

```
Input:  agent
Fluxo:
  1. Coleta últimos 10 feedbacks approved (com score/analysis do SourcedProfileSourcing)
  2. Coleta últimos 10 feedbacks rejected (com reason + score/analysis)
  3. Monta prompt para Gemini:
     "Dado os perfis aprovados [X] e rejeitados [Y] com motivos [Z],
      extraia padrões de preferência do recrutador"
  4. Salva extracted_preferences no agent
  5. Opcionalmente refina criteria_structured
Return: { success: true, preferences: {...} }
```

Pode rodar no Rails (Gemini direto) ou delegar para Python. Decisão de implementação.

### BackgroundAgents::DiversifyQueriesService (novo)

Gera variantes de query para evitar exaustão.

```
Input:  agent
Fluxo:
  1. Pega criteria_text + criteria_structured + extracted_preferences
  2. Pega queries já usadas em ciclos anteriores (via agent_cycles → sourcing → query)
  3. Gera 5-10 variantes via LLM:
     - Títulos sinônimos (Backend Developer → Software Engineer → Engenheiro de Software)
     - Skills adjacentes (Ruby → Elixir, Python)
     - Empresas similares (Nubank → Stone, PagSeguro, Creditas)
     - Localizações expandidas (SP → Campinas, Curitiba, Remoto)
     - Seniority adjacente (Senior → Lead, Staff)
  4. Salva diversity_queries no agent
Return: [query1, query2, query3, ...]
```

---

## Sidekiq Jobs

### BackgroundAgents::SetupJob (novo)

```
Queue: default | Retry: 3
Trigger: Criação de BackgroundAgent
Ação: Chama SetupService → parseia criteria → muda state → dispara primeiro ciclo
Tenant: switch! via account_id do agent
```

### BackgroundAgents::CronJob (novo)

```
Queue: background_agents (NOVA FILA) | Retry: 1
Trigger: Cron — "0 6 * * *" (6h BRT) + "0 18 * * *" (18h BRT, opcional)
Ação:
  Para cada Account ativo:
    Apartment::Tenant.switch do
      1. Auto-pause agents sem interação > N dias
      2. Expirar cycles não revisados > 7 dias
      3. Detectar agents out_of_leads (3 ciclos com < 3 candidatos)
      4. Para cada agent .runnable (active + calibrated + last_run > 20h):
         → Gerar queries diversificadas (DiversifyQueriesService)
         → Executar ciclo (ExecuteCycleService) OU notificar Python
    end
Tenant: Itera Account.active com switch
```

**Decisão: Rails orquestra ou Python orquestra?**

Opção A — **Rails orquestra busca, Python só faz LLM:**
- Rails cria Sourcing, enfileira buscas, roda AI analysis
- Python só é chamado para diversificação de queries e extração de preferências
- Vantagem: reusa 100% da pipeline existente, menos latência
- Desvantagem: lógica de agente distribuída entre Rails e Python

Opção B — **Python orquestra tudo, Rails é API:**
- Rails serve endpoints para Python consultar/atualizar
- Python chama `GET /runnable`, faz buscas via API, cria batches via `POST /deliver_cycle`
- Vantagem: lógica de agente centralizada em Python
- Desvantagem: duplica chamadas HTTP, latência maior, Python precisa conhecer detalhes da busca

**Recomendação: Opção A para busca local, Opção B para lógica de agente complexa.**

O CronJob no Rails faz a parte mecânica (auto-pause, expiração, criação de Sourcing). Para diversificação de queries e extração de preferências, delega para Python via `RecruitAgentService` estendido. Melhor dos dois mundos.

### BackgroundAgents::ExtractPreferencesJob (novo)

```
Queue: default | Retry: 2
Trigger: Após feedbacks de rejection com motivo
Ação: Chama ExtractPreferencesService → LLM extrai padrões → salva no agent
Tenant: switch! via account_id
```

### BackgroundAgents::CycleCompletionJob (novo)

```
Queue: default | Retry: 2
Trigger: Quando o Sourcing de um ciclo termina (todos perfis analisados)
Ação:
  1. Filtra perfis com score >= threshold
  2. Deduplica contra ciclos anteriores
  3. Atualiza AgentCycle (candidates_delivered, status: delivered)
  4. Atualiza BackgroundAgent (total_delivered, last_run_at)
  5. Se mode == "full_auto": chama AutoAddCandidateService para cada perfil qualificado
  6. Notifica recrutador via WebSocket
Tenant: switch! via account_id
```

**Como saber quando o Sourcing terminou?**
O `AiAnalysisJob` existente já broadcast `sourcing_fully_completed`. O CycleCompletionJob pode ser enfileirado como callback quando a última análise roda, seguindo o mesmo padrão do `auto_source_batch_completed`.

---

## WebSocket (ActionCable)

### Opção: Estender SourcingChannel

Como cada `AgentCycle` cria um `Sourcing`, os eventos de progresso (`profile_analyzed`, `sourcing_fully_completed`) já funcionam automaticamente via `SourcingChannel`.

Para eventos específicos do agent (novo batch disponível, calibração completa), usar broadcast direto:

```ruby
SourcingChannel.broadcast_to(
  "#{agent.user_id}_sourcing_#{cycle.sourcing_id}",
  { type: "agent_cycle_delivered", agent_id: agent.id, cycle_id: cycle.id, count: cycle.candidates_delivered }
)
```

### Opção: BackgroundAgentChannel (novo, leve)

```ruby
class BackgroundAgentChannel < ApplicationCable::Channel
  def subscribed
    stream_for current_user
  end
end
```

Usado para notificações globais do agent (não vinculadas a um sourcing específico):
- `agent_cycle_ready` — novo batch para revisão
- `agent_calibrated` — calibração concluída
- `agent_paused` — auto-pause por inatividade
- `agent_out_of_leads` — sem mais candidatos

---

## Configuração Sidekiq

Adicionar fila ao [config/sidekiq.yml](config/sidekiq.yml):

```yaml
:queues:
  - [critical, 6]
  - [email_delivery, 4]
  - [sourcing_search, 6]
  - [default, 3]
  - [ai_analysis, 7]
  - [background_agents, 2]    # ← NOVA FILA
  - [embeddings, 2]
  - [linkedin_enrichment, 2]
  - mailers
  - active_storage
  - low
  - ats_sync
```

Adicionar cron ao [config/schedule.yml](config/schedule.yml):

```yaml
background_agent_morning:
  cron: "0 9 * * *"
  class: "BackgroundAgents::CronJob"
  queue: background_agents

background_agent_evening:
  cron: "0 21 * * *"
  class: "BackgroundAgents::CronJob"
  queue: background_agents
```

---

## Routes

```ruby
# config/routes.rb — dentro do namespace V1::Users existente
namespace :v1 do
  namespace :users do
    resources :background_agents do
      member do
        post :pause
        post :resume
        post :stop
      end
      resources :cycles, controller: "agent_cycles", only: %i[index show] do
        resources :feedbacks, controller: "agent_feedbacks", only: %i[create] do
          collection do
            post :bulk
          end
        end
      end
    end
  end

  # Endpoints internos (Python → Rails)
  namespace :services do
    resources :background_agents, only: [] do
      collection do
        get :runnable
      end
      member do
        post :deliver_cycle
        patch :update_preferences
        patch :update_status
      end
    end
  end
end
```

---

## Comunicação com Python (RecruitAgentService)

Estender o `RecruitAgentService` existente com novos métodos:

```ruby
# Novos endpoints no Python:
# POST /background-agents/parse-criteria    → Gera criteria_structured
# POST /background-agents/diversify-queries → Gera variantes de query
# POST /background-agents/extract-preferences → Extrai preferências de feedbacks
```

Usa o mesmo padrão de autenticação (`INTERNAL_API_SECRET`) e timeout já configurados.

---

## Deduplicação Entre Ciclos

A deduplicação é crítica para não apresentar o mesmo candidato repetidamente.

**Estratégia por camadas:**

1. **Deduplicação por SourcedProfile.external_id:** O `SourcedProfile.find_existing_by_identity` (existente) já faz dedup no momento da criação, por email, LinkedIn, CPF.

2. **Deduplicação por ciclos anteriores:** Na hora de filtrar o batch, excluir perfis que já apareceram:
```ruby
presented_sourcing_ids = agent.agent_cycles.pluck(:sourcing_id)

new_candidates = cycle.sourcing.sourced_profile_sourcings
  .where(is_deleted: false)
  .where("score >= ?", agent.min_score_threshold)
  .where.not(
    sourced_profile_id: SourcedProfileSourcing
      .where(sourcing_id: presented_sourcing_ids)
      .select(:sourced_profile_id)
  )
  .order(score: :desc)
  .limit(agent.daily_limit)
```

3. **Deduplicação contra candidatos já na vaga:** Excluir SourcedProfiles que já tenham Apply na vaga:
```ruby
already_applied_ids = Apply
  .where(job_id: agent.job_id, is_deleted: false)
  .pluck(:candidate_id)

# Excluir sourced_profiles cujo candidate_id está em already_applied_ids
.where.not(sourced_profile_id: SourcedProfile.where(candidate_id: already_applied_ids).select(:id))
```

---

## Relação com CandidateFeedback Existente

O `CandidateFeedback` existente (like/dislike simples) serve para feedback rápido no UI de sourcing manual.

O `AgentFeedback` novo é mais rico:
- Tem `reason` textual obrigatório em rejection
- Tem relação direta com `BackgroundAgent` e `AgentCycle`
- Alimenta o loop de calibração e extração de preferências

Não conflitam. São complementares. O recrutador pode dar like/dislike rápido E também dar feedback estruturado no contexto do agent.

---

## Modelo de Dados: Resumo das Migrations

### Migration 1: CreateBackgroundAgents

Tabela `background_agents` com todos os campos listados acima. Tenant-scoped (em `db/migrate/`).

### Migration 2: CreateAgentCycles

Tabela `agent_cycles` com FK para `background_agents` e `sourcings`. Tenant-scoped.

### Migration 3: CreateAgentFeedbacks

Tabela `agent_feedbacks` com FKs para `background_agents`, `agent_cycles`, `sourced_profile_sourcings`. Tenant-scoped.

---

## Checklist de Implementação

### Fase 1 — Fundação (Models + Migrations)
- [ ] Migration: CreateBackgroundAgents
- [ ] Migration: CreateAgentCycles
- [ ] Migration: CreateAgentFeedbacks
- [ ] Model: BackgroundAgent (validações, scopes, métodos de estado)
- [ ] Model: AgentCycle (validações, scopes, delegações)
- [ ] Model: AgentFeedback (validações, callback para atualizar agent)
- [ ] Adicionar `has_many :background_agents` no Job e User
- [ ] Factory: background_agent, agent_cycle, agent_feedback
- [ ] Specs: models

### Fase 2 — Serializers + Controllers CRUD
- [ ] BackgroundAgentSerializer
- [ ] AgentCycleSerializer
- [ ] AgentFeedbackSerializer (simples, poucas attrs)
- [ ] V1::Users::BackgroundAgentsController (CRUD + pause/resume/stop)
- [ ] V1::Users::AgentCyclesController (index, show)
- [ ] V1::Users::AgentFeedbacksController (create, bulk)
- [ ] Routes
- [ ] Specs: requests

### Fase 3 — Services + Jobs
- [ ] BackgroundAgents::SetupService
- [ ] BackgroundAgents::ProcessFeedbackService
- [ ] BackgroundAgents::ExecuteCycleService
- [ ] BackgroundAgents::DiversifyQueriesService
- [ ] BackgroundAgents::ExtractPreferencesService
- [ ] BackgroundAgents::SetupJob
- [ ] BackgroundAgents::CronJob
- [ ] BackgroundAgents::ExtractPreferencesJob
- [ ] BackgroundAgents::CycleCompletionJob
- [ ] Estender RecruitAgentService com endpoints de agent
- [ ] Config: sidekiq.yml (nova fila), schedule.yml (crons)
- [ ] Specs: services, jobs

### Fase 4 — WebSocket + Integração
- [ ] BackgroundAgentChannel
- [ ] Integrar CycleCompletionJob com SourcingChannel existente
- [ ] Endpoints internos (V1::Services::BackgroundAgentsController)
- [ ] Specs: channels, integration

### Fase 5 — Python API
- [ ] POST /background-agents/parse-criteria
- [ ] POST /background-agents/diversify-queries
- [ ] POST /background-agents/extract-preferences
- [ ] Trigger endpoint (se opção B para orquestração)

---

## Decisões em Aberto

1. **Quem orquestra a busca de cada ciclo?**
   - Rails (reusa pipeline inteira) vs. Python (centraliza lógica de agente)
   - Recomendação: Rails orquestra busca, Python faz LLM (diversificação + preferências)

2. **Extração de preferências: Rails + Gemini direto ou Python?**
   - Se for prompt simples → Rails com GeminiClient
   - Se precisar de reasoning complexo / LangGraph → Python
   - Recomendação: começar no Rails, migrar para Python se necessário

3. **Limite de agents por account/user?**
   - Sugestão: configurável, default 5 agents ativos por user

4. **Billing/seats model?**
   - Cada agent consome "seat"? Gratuito no MVP?
   - Decisão de produto, não técnica

5. **Frequência de execução configurável?**
   - Fixo 1x/dia? 2x/dia? Configurável por agent?
   - Sugestão MVP: fixo 1x/dia (cron 9h BRT)
