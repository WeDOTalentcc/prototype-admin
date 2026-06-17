# Arquitetura - ATS Mercado

## 🏛️ Visão Geral

Sistema de ATS (Applicant Tracking System) com busca híbrida inteligente.

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADAS DA APLICAÇÃO                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📱 API Layer (Controllers)                                 │
│  ├─ v1/users/talent_searches_controller.rb                  │
│  └─ REST endpoints para busca                               │
│                                                              │
│  🎯 Service Layer (Business Logic)                          │
│  ├─ sourcings/job_enqueuer_service.rb                       │
│  ├─ candidates/search/hybrid_search_service.rb              │
│  ├─ candidates/search/elasticsearch_strategy.rb             │
│  └─ candidates/search/embedding_strategy.rb                 │
│                                                              │
│  ⚙️ Job Layer (Background Processing)                       │
│  ├─ candidates/local_search_job.rb                          │
│  └─ Sidekiq workers                                         │
│                                                              │
│  💾 Data Layer (Models)                                     │
│  ├─ Candidate                                               │
│  ├─ Sourcing                                                │
│  ├─ SourcedProfile                                          │
│  └─ Embedding                                               │
│                                                              │
│  🔍 Search Engines                                          │
│  ├─ Elasticsearch (full-text)                               │
│  └─ pgvector (semantic)                                     │
│                                                              │
│  🧠 External Services                                       │
│  ├─ Gemini API (embeddings + LLM)                           │
│  └─ ActionCable (WebSocket)                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Busca Híbrida

### 1. Request Flow

```
User Request
    │
    ├─► Controller (TalentSearchesController)
    │       │
    │       ├─► Cria Sourcing
    │       └─► Chama JobEnqueuerService
    │
    └─► Enfileira Job
            │
            └─► Candidates::LocalSearchJob (Sidekiq)
```

### 2. Job Execution

```
LocalSearchJob.perform
    │
    ├─► Switch Tenant (multi-tenancy)
    │
    ├─► Instancia HybridSearchService
    │
    ├─► Execute Search
    │       │
    │       ├─► SimpleQueryDetector (routing)
    │       │       │
    │       │       ├─► :simple   → execute_simple_search
    │       │       ├─► :resume   → execute_resume_search
    │       │       └─► :complex  → execute_complex_search
    │       │
    │       └─► Retorna Result
    │
    └─► Process Candidates
            │
            ├─► Cria SourcedProfiles
            ├─► Trigger AI analysis
            └─► Broadcast WebSocket
```

### 3. Hybrid Search Execution

```
HybridSearchService.search
    │
    ├─► PARALELO:
    │   ├─► ElasticsearchStrategy
    │   │   └─► Searchkick → Elasticsearch
    │   │
    │   └─► EmbeddingStrategy
    │       ├─► EmbeddingCache (check)
    │       │   └─► Miss? → Gemini API
    │       │
    │       └─► pgvector nearest_neighbors
    │
    ├─► WeightedRankFusion (combina)
    │
    ├─► Reranker (boost de qualidade)
    │
    └─► Load candidates (preserva ordem)
```

## 🗄️ Modelo de Dados

### Core Models

```ruby
Account (multi-tenant)
  ├─ has_many :users
  ├─ has_many :candidates
  ├─ has_many :sourcings
  └─ attribute :tenant (Apartment)

User
  ├─ belongs_to :account
  └─ has_many :sourcings

Candidate
  ├─ belongs_to :account
  ├─ has_one :embedding
  ├─ attribute :curriculum_text (text)
  └─ searchkick index (Elasticsearch)

Embedding
  ├─ belongs_to :reference (polymorphic)
  ├─ attribute :embedding (vector, 768-dim)
  └─ pgvector index (HNSW)

Sourcing
  ├─ belongs_to :user
  ├─ belongs_to :account
  ├─ has_many :sourced_profiles
  ├─ attribute :status (processing/done/error)
  └─ attribute :search_metadata (jsonb)

SourcedProfile
  ├─ belongs_to :sourcing
  ├─ belongs_to :candidate
  ├─ attribute :search_metadata (jsonb)
  └─ after_commit :trigger_ai_analysis

EmbeddingCache
  ├─ attribute :key (string, indexed)
  ├─ attribute :embedding (vector, 768-dim)
  ├─ attribute :model_version (string)
  └─ attribute :last_accessed_at (datetime)
```

### Database Schema Highlights

```sql
-- Candidates table (simplificado)
CREATE TABLE candidates (
  id BIGINT PRIMARY KEY,
  account_id BIGINT NOT NULL,
  name VARCHAR,
  email VARCHAR,
  curriculum_text TEXT,
  is_deleted BOOLEAN DEFAULT FALSE,

  INDEX idx_account_id (account_id),
  INDEX idx_email (email),
  FULLTEXT INDEX idx_curriculum (curriculum_text)
);

-- Embeddings table
CREATE TABLE embeddings (
  id BIGINT PRIMARY KEY,
  reference_type VARCHAR,
  reference_id BIGINT,
  embedding VECTOR(768),  -- pgvector

  INDEX idx_reference (reference_type, reference_id)
);

-- HNSW index para busca vetorial rápida
CREATE INDEX idx_embeddings_vector
  ON embeddings
  USING hnsw (embedding vector_cosine_ops);

-- Embedding cache
CREATE TABLE embedding_caches (
  id BIGINT PRIMARY KEY,
  key VARCHAR UNIQUE,
  embedding VECTOR(768),
  model_version VARCHAR,
  account_id BIGINT,
  last_accessed_at TIMESTAMP,

  INDEX idx_key (key),
  INDEX idx_model_version (model_version)
);
```

## 🔌 Integrações Externas

### Gemini API

```ruby
GeminiClient
  ├─ #chat(messages, model, temperature)
  │   └─ Usado por: QueryAnalyzer, HyDE, Fallback
  │
  └─ #embeddings(text, model, dimensions)
      └─ Usado por: EmbeddingService

Modelos:
  - gemini-2.0-flash: Rápido, análise (QueryAnalyzer)
  - gemini-2.5-flash: Balanceado, geração (HyDE)
  - gemini-embedding-001: Embeddings 768-dim
```

### Elasticsearch

```ruby
Candidate.search(query, options)
  ├─ Via Searchkick gem
  ├─ Índice: candidates_#{Rails.env}
  └─ Configuração:
      - Fields: curriculum_text^5, role_name^3, name^2
      - Analyzer: standard + stopwords PT
      - minimum_should_match: adaptativo
```

### pgvector

```ruby
Embedding.nearest_neighbors(:embedding, query_vector, distance: "cosine")
  ├─ Extension: pgvector
  ├─ Index: HNSW (Hierarchical Navigable Small World)
  └─ Distância: cosine (1 - similaridade)
```

### ActionCable (WebSocket)

```ruby
ActionCable.server.broadcast("sourcing_#{id}", event)
  ├─ Canais: sourcing_{sourcing_id}
  └─ Events:
      - sourcing_started
      - sourcing_profiles_found
      - sourcing_completed
      - sourcing_error
```

## 🔐 Multi-tenancy (Apartment)

### Tenant Switching

```ruby
# Automático em controllers
class ApplicationController
  before_action :switch_tenant

  def switch_tenant
    Apartment::Tenant.switch(current_user.account.tenant)
  end
end

# Manual em jobs/services
Apartment::Tenant.switch(@account.tenant) do
  # código que acessa dados isolados
end
```

### Schema

```
public (schema padrão)
  ├─ accounts
  ├─ users
  └─ shared_data

account_123 (schema do tenant)
  ├─ candidates
  ├─ sourcings
  ├─ sourced_profiles
  └─ embeddings

account_456 (outro tenant)
  ├─ candidates
  ├─ sourcings
  └─ ...
```

## 🔄 Cache Strategy

### Layer 1: Redis (Rails.cache)

```ruby
# QueryAnalyzer results
Rails.cache.fetch("query_analysis:#{sha256}", expires_in: 1.hour) do
  @query_analyzer.analyze(query)
end

# TTL: 1 hora
# Key: SHA256 da query normalizada
# Store: Hash completo da análise
```

### Layer 2: Database (EmbeddingCache)

```ruby
# Embedding vectors
EmbeddingCache.find_by(key: "search_emb:v1:#{account_id}:#{sha256}")
  .tap(&:touch_access)  # Atualiza last_accessed_at

# TTL: 24 horas (touch-based)
# Key: SHA256 + model_version + account_id
# Store: Vector 768-dim + metadata
# Cleanup: Job que remove entries > 7 dias
```

### Layer 3: Elasticsearch Query Cache

```
# Gerenciado internamente pelo ES
# Cache de queries idênticas
# TTL: configurável no ES
```

## 📊 Observabilidade

### Logging

```ruby
SearchTelemetry
  ├─ request_id (UUID)
  ├─ events[] (array de eventos)
  ├─ timings{} (hash de durações)
  └─ #log_summary (log final)

Rails.logger
  ├─ Structured logging com emojis
  ├─ Contexto: [ClassName] Mensagem
  └─ Níveis: DEBUG, INFO, WARN, ERROR
```

### Métricas (futuro)

```ruby
# StatsD/Prometheus
StatsD.increment('search.hybrid.executed')
StatsD.measure('search.hybrid.duration') { ... }
StatsD.gauge('search.results.count', count)
```

### Error Tracking (futuro)

```ruby
# Sentry/Rollbar
Sentry.capture_exception(error, extra: { sourcing_id: id })
```

## 🔧 Background Jobs (Sidekiq)

### Queues

```ruby
default: Busca local, processamento geral
pearch: Busca global em APIs externas
mailers: Envio de emails
```

### Retry Strategy

```ruby
sidekiq_options queue: :default, retry: 2

# Retry delays:
# 1st retry: ~25 seconds
# 2nd retry: ~2 minutes
# Dead queue após 2 retries
```

### Monitoring

```
Sidekiq Web UI: /sidekiq
  ├─ Queues
  ├─ Busy workers
  ├─ Retries
  └─ Dead jobs
```

## 🚀 Deployment

### Stack

```
Application: Ruby on Rails 7
Database: PostgreSQL 14+ (com pgvector)
Search: Elasticsearch 8
Cache: Redis 7
Jobs: Sidekiq
Web Server: Puma
```

### Environment Variables (principais)

```bash
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Elasticsearch
ELASTICSEARCH_URL=http://...

# Gemini API
GEMINI_API_KEY=...
GEMINI_CHAT_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=gemini-embedding-001

# Search Config
EMBEDDING_RELEVANCE_THRESHOLD=0.70
REQUIRE_CURRICULUM_TEXT=true
```

## 📈 Scaling Considerations

### Database

- **Read replicas**: Para queries pesadas
- **Partitioning**: Por account_id (sharding)
- **Connection pooling**: PgBouncer

### Search

- **ES cluster**: Multiple nodes para HA
- **pgvector**: HNSW index otimizado

### Cache

- **Redis cluster**: Para alta disponibilidade
- **Cache warming**: Pre-load embeddings comuns

### Jobs

- **Sidekiq concurrency**: Ajustar workers
- **Queue prioritization**: Critical > default
- **Rate limiting**: Para APIs externas

## 🔒 Security

### Multi-tenancy Isolation

- Apartment gem: schema-based isolation
- Row-level: account_id em todas as queries
- Verificação dupla: tenant switch + account_id

### API Security

- JWT authentication
- Rate limiting (Rack::Attack)
- CORS configurado

### Secrets Management

- ENV vars (nunca hardcode)
- Encrypted credentials (Rails)
- Rotação de API keys

## 🎯 Performance Targets

### Latência

- Simple search: < 500ms (p95)
- Complex search: < 2s (p95)
- Resume search: < 3s (p95)

### Throughput

- Buscas simultâneas: 100/min
- Background jobs: 1000/min

### Cache Hit Rate

- QueryAnalyzer: > 70%
- EmbeddingCache: > 80%

### Availability

- Uptime: 99.9%
- Error rate: < 0.1%
