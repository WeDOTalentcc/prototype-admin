# LLM Usage Tracking

Sistema de rastreamento de uso e custos de chamadas LLM (Large Language Models) no ATS Mercado.

---

## Visão Geral

O sistema registra **toda chamada LLM** feita pela aplicação — chat, embeddings, parsing, etc — em uma tabela `llm_usages` no schema `public`. Cada registro contém: modelo usado, operação, tokens consumidos, custo calculado em USD, latência e metadados de contexto.

---

## Arquitetura

```
┌─────────────────────────┐
│   Service / Job         │
│  (ex: ResumeParser)     │
│                         │
│  GeminiClient.chat(     │
│    tracking: {           │
│      operation: "..."   │
│    }                    │
│  )                      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│     GeminiClient        │
│                         │
│  1. Faz request Gemini  │
│  2. Extrai usage tokens │
│  3. Calcula custo via   │
│     CostCalculator      │
│  4. Salva LlmUsage      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Llm::CostCalculator    │
│                         │
│  Tabela de preços por   │
│  modelo (USD / tokens)  │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│  LlmUsage (Model)       │
│                         │
│  Scopes, agregações,    │
│  stats por model/op     │
└─────────────────────────┘
```

---

## Componentes

### 1. Model — `LlmUsage`

**Tabela:** `llm_usages` (schema public)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | integer | Usuário que disparou a chamada |
| `account_id` | integer | Conta (tenant) associada |
| `model` | string | Nome do modelo (ex: `gemini-2.5-flash`) |
| `operation` | string | Identificador da operação (ex: `search.query_analysis`) |
| `input_tokens` | integer | Tokens de entrada |
| `output_tokens` | integer | Tokens de saída |
| `total_tokens` | integer | Total de tokens |
| `cost_usd` | decimal(12,8) | Custo calculado em USD |
| `latency_ms` | decimal(10,2) | Latência da chamada em ms |
| `success` | boolean | Se a chamada foi bem-sucedida |
| `error_message` | text | Mensagem de erro (quando `success: false`) |
| `context` | jsonb | Metadados livres (service, feature, etc) |

**Índices:** `model`, `operation`, `success`, `[account_id, created_at]`, `[user_id, created_at]`, `created_at`, `context` (GIN)

**Scopes disponíveis:**

```ruby
LlmUsage.successful          # where(success: true)
LlmUsage.failed              # where(success: false)
LlmUsage.by_model("gemini-2.5-flash")
LlmUsage.by_operation("search.query_analysis")
LlmUsage.by_account(account_id)
LlmUsage.by_user(user_id)
LlmUsage.recent              # order(created_at: :desc)
LlmUsage.today               # criados hoje
LlmUsage.this_month          # criados neste mês
```

**Métodos de classe para agregação:**

```ruby
LlmUsage.total_cost_by_account(account_id, start_date:, end_date:)
LlmUsage.usage_stats_by_model(account_id, start_date:, end_date:)
LlmUsage.daily_costs(account_id, days: 30)
```

---

### 2. Tracking automático — `GeminiClient`

Toda chamada via `GeminiClient#chat` ou `GeminiClient#embeddings` pode ser rastreada passando o parâmetro `tracking:`:

```ruby
GeminiClient.new.chat(
  model: "gemini-2.5-flash",
  messages: [{ role: "user", content: "..." }],
  tracking: { operation: "candidates.resume_parsing" }
)
```

O `GeminiClient` automaticamente:
1. Mede a latência (tempo antes/depois da chamada)
2. Extrai `promptTokenCount`, `candidatesTokenCount`, `totalTokenCount` da resposta
3. Calcula o custo via `Llm::CostCalculator`
4. Cria o registro `LlmUsage` dentro do `Apartment::Tenant.switch("public")`

Para embeddings:
```ruby
GeminiClient.new.embeddings(
  text: "texto para embedding",
  model: "gemini-embedding-001",
  tracking: { operation: "embeddings.encode" }
)
```

> Se `tracking: nil`, nenhum registro é criado.

---

### 3. Tracking manual — `Llm::UsageTracker`

Para cenários onde se precisa de controle mais fino, usar o `UsageTracker` com bloco:

```ruby
tracker = Llm::UsageTracker.new(
  model: "gemini-2.5-flash",
  operation: "custom.operation",
  user: current_user,
  account: current_account,
  context: { service: "MyService", feature: "feature_x" }
)

tracker.track do
  # chamada LLM aqui — o response é retornado
  some_llm_call()
end
```

O tracker captura exceções, registra falhas com `success: false` e re-raises a exceção.

---

### 4. Cálculo de custos — `Llm::CostCalculator`

Tabela de preços embutida:

| Modelo | Input (USD/1M tokens) | Output (USD/1M tokens) |
|---|---|---|
| `gemini-2.0-flash` | $0.075 | $0.30 |
| `gemini-2.5-flash` | $0.075 | $0.30 |
| `gemini-1.5-pro` | $1.25 | $5.00 |
| `gemini-embedding-001` | $0.01/1K tokens | — |
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `text-embedding-3-small` | $0.02 | — |

```ruby
Llm::CostCalculator.calculate(
  model: "gemini-2.5-flash",
  input_tokens: 1000,
  output_tokens: 500
)
# => 0.00022500 (USD)
```

---

## APIs de Métricas

### API do Usuário (`V1::Users::LlmUsagesController`)

Base URL: `/v1/users/llm_usages`

| Endpoint | Método | Descrição |
|---|---|---|
| `/llm_usages` | GET | Lista registros paginados com filtros |
| `/llm_usages/:id` | GET | Detalhe de um registro |
| `/llm_usages` | POST | Cria registro manualmente |
| `/llm_usages/stats` | GET | Estatísticas por período (today, this_week, this_month, last_30_days) |
| `/llm_usages/by_model` | GET | Agregação por modelo |
| `/llm_usages/by_operation` | GET | Agregação por operação |
| `/llm_usages/by_service` | GET | Agregação por service (campo `context.service`) |
| `/llm_usages/daily_trend` | GET | Tendência diária (custo, requests, tokens, falhas) |
| `/llm_usages/failures` | GET | Últimas 100 falhas |
| `/llm_usages/recent` | GET | Registros mais recentes com detalhes |
| `/llm_usages/top_consumers` | GET | Top 20 usuários por custo |

**Filtros disponíveis no `index`:**

| Param | Descrição |
|---|---|
| `model` | Filtrar por modelo |
| `operation` | Filtrar por operação |
| `success` | `true` ou `false` |
| `user_id` | Filtrar por usuário |
| `start_date` | Data inicial |
| `end_date` | Data final |
| `page` / `per_page` | Paginação |

**Param `from`** (nos endpoints de agregação): data inicial no formato ISO 8601. Default: 30 dias atrás.

#### Exemplo de resposta — `GET /llm_usages/stats`

```json
{
  "success": true,
  "data": {
    "today": {
      "total_cost": 0.012345,
      "total_requests": 42,
      "successful_requests": 40,
      "failed_requests": 2,
      "total_tokens": 125000,
      "total_input_tokens": 100000,
      "total_output_tokens": 25000,
      "avg_latency_ms": 230.5
    },
    "this_week": { ... },
    "this_month": { ... },
    "last_30_days": { ... }
  }
}
```

#### Exemplo de resposta — `GET /llm_usages/by_model`

```json
{
  "success": true,
  "data": [
    {
      "model": "gemini-2.5-flash",
      "request_count": 1500,
      "total_input_tokens": 5000000,
      "total_output_tokens": 1200000,
      "total_tokens": 6200000,
      "total_cost": 0.735000,
      "avg_latency_ms": 245.30
    }
  ]
}
```

#### Exemplo de resposta — `GET /llm_usages/daily_trend?days=7`

```json
{
  "success": true,
  "data": [
    {
      "date": "2026-02-21",
      "request_count": 320,
      "total_cost": 0.045200,
      "total_tokens": 890000,
      "failed_count": 3
    }
  ]
}
```

#### Exemplo de resposta — `GET /llm_usages/top_consumers`

```json
{
  "success": true,
  "data": [
    {
      "user_id": 42,
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "request_count": 250,
      "total_cost": 0.125000,
      "total_tokens": 1500000
    }
  ]
}
```

---

### API Admin (`V1::Admin::LlmCostsController`)

Base URL: `/v1/admin/llm_costs`

| Endpoint | Método | Descrição |
|---|---|---|
| `/llm_costs/overview` | GET | Visão geral de custos (admin only) |

**Params:** `days` (default: 30)

Retorna custos agregados **cross-tenant**:

```json
{
  "success": true,
  "data": {
    "period_days": 30,
    "total_cost": 12.345678,
    "costs_by_model": {
      "gemini-2.5-flash": 8.123456,
      "gemini-embedding-001": 4.222222
    },
    "costs_by_operation": {
      "search.query_analysis": 3.100000,
      "candidates.resume_parsing": 2.500000
    },
    "costs_by_account": {
      "Acme Corp": 5.000000,
      "Beta Inc": 7.345678
    },
    "costs_by_user": {
      "John Doe": 2.000000,
      "Jane Smith": 1.500000
    },
    "daily_costs": {
      "2026-02-27": 0.450000,
      "2026-02-26": 0.380000
    },
    "total_tokens": 45000000,
    "record_count": 12500
  }
}
```

---

### API Legacy (`Api::V1::LlmUsagesController`)

Base URL: `/api/v1/llm_usages`

Endpoints: `index`, `show`, `create`, `stats` — mesma lógica, porém com serialização inline (sem JSONAPI serializer).

---

## Operações Rastreadas

Cada serviço que chama LLM registra uma `operation` descritiva:

| Operation | Service/Job |
|---|---|
| `search.query_analysis` | `Candidates::Search::QueryAnalyzer` |
| `search.query_rewriting` | `Candidates::Search::QueryRewriter` |
| `search.hyde_query_expansion` | `Candidates::Search::HydeQueryExpander` |
| `search.profile_extraction` | `Candidates::Search::ProfileExtractor` |
| `search.job_description_extraction` | `Candidates::Search::JobDescriptionProcessor` |
| `search.resume_profile_extraction` | `Candidates::Search::HybridSearchService` |
| `candidates.resume_parsing` | `Candidates::ResumeParserService` |
| `candidates.query_parsing` | `Candidates::QueryParserService` |
| `candidates.suggestion_autocomplete` | `Candidates::SuggestionService` |
| `local_search.query_optimization` | `Candidates::LocalSearchJob` |
| `similar_candidates.profile_synthesis` | `Candidates::SimilarCandidates::ProfileSynthesizer` |
| `similar_candidates.feedback_analysis` | `Candidates::SimilarCandidates::FeedbackAnalyzerService` |
| `embeddings.encode` | `Embeddings::Encoder` |
| `sourcing.query_requirements_extraction` | `SourcedProfiles::QueryRequirementsExtractor` |
| `sourcing.profile_analysis` | `SourcedProfiles::ProfileAnalyzer` |
| `evaluations.ai_feedback` | `Evaluations::AiFeedbackService` |
| `calendar.schedule_suggestion` | `CalendarEvents::ScheduleSuggestionService` |
| `jobs.suggestion` | `JobSuggestionService` |
| `pearch.query_parsing` | `Pearch::QueryParserService` |
| `business.big_five_generation` | `BusinessBigFiveService` |
| `search_archetypes.create_from_description` | `SearchArchetypes::CreateFromDescriptionService` |

---

## Queries úteis no Rails Console

```ruby
# Custo total de uma account nos últimos 30 dias
LlmUsage.total_cost_by_account(account.id, start_date: 30.days.ago)

# Stats por modelo
LlmUsage.usage_stats_by_model(account.id)

# Custo diário dos últimos 7 dias
LlmUsage.daily_costs(account.id, days: 7)

# Top 5 operações mais caras do mês
LlmUsage.this_month
  .successful
  .group(:operation)
  .sum(:cost_usd)
  .sort_by { |_, v| -v }
  .first(5)

# Requests falhados hoje
LlmUsage.today.failed.order(created_at: :desc)

# Latência média por modelo
LlmUsage.successful.group(:model).average(:latency_ms)

# Consumo por service (campo context)
LlmUsage.where("context->>'service' IS NOT NULL")
  .group("context->>'service'")
  .sum(:cost_usd)
```

---

## Como adicionar tracking a um novo serviço

Basta passar `tracking:` ao chamar `GeminiClient`:

```ruby
GeminiClient.new.chat(
  model: ENV.fetch("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
  messages: messages,
  temperature: 0.1,
  tracking: {
    operation: "meu_modulo.minha_operacao",
    service: "MeuModulo::MeuService",
    feature: "descricao_da_feature"
  }
)
```

O campo `operation` é obrigatório. Campos extras no hash vão para a coluna `context` (jsonb).
