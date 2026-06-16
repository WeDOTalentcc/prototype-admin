# Busca Híbrida — Documentação Completa End-to-End

> Documentação detalhada de todo o sistema de busca híbrida (local + global), cobrindo cada arquivo, classe, método e responsabilidade de ponta a ponta.

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Diagrama de Fluxo Completo](#2-diagrama-de-fluxo-completo)
3. [Rotas (Routes)](#3-rotas)
4. [Controller — SourcingsController](#4-controller)
5. [Models](#5-models)
   - 5.1 Sourcing
   - 5.2 SourcedProfile
   - 5.3 SourcedProfileSourcing
   - 5.4 SourcingFilter
6. [Enfileiramento — JobEnqueuerService](#6-enfileiramento)
7. [Busca Local — LocalSearchJob](#7-busca-local)
   - 7.1 Candidates::LocalSearchJob
   - 7.2 SearchArchetypes::LocalSearchJob
8. [HybridSearchService — Core da Busca](#8-hybrid-search-service)
   - 8.1 Detecção de Tipo de Query
   - 8.2 Busca Simples
   - 8.3 Busca Complexa
   - 8.4 Busca por Currículo
   - 8.5 Busca por Job Description
9. [Estratégias de Busca](#9-estratégias)
   - 9.1 ElasticsearchStrategy
   - 9.2 EmbeddingStrategy
10. [Fusão e Ranking](#10-fusão-e-ranking)
    - 10.1 WeightedRankFusion (RRF)
    - 10.2 Reranker
    - 10.3 AdaptivePool
11. [Serviços de Suporte à Busca](#11-serviços-de-suporte)
    - 11.1 SimpleQueryDetector
    - 11.2 QueryAnalyzer
    - 11.3 HydeQueryExpander
    - 11.4 HydeDocumentGenerator
    - 11.5 ProfileExtractor
    - 11.6 MultiQueryGenerator
    - 11.7 JobDescriptionProcessor
12. [Infraestrutura](#12-infraestrutura)
    - 12.1 Configuration
    - 12.2 BaseFilters / FilterMerger
    - 12.3 EmbeddingCache / QueryEmbeddingCache
    - 12.4 EmbeddingService
    - 12.5 SearchTelemetry / SearchExplainer
13. [Busca Global — Pearch](#13-busca-global)
    - 13.1 Pearch::TalentSearchJob
    - 13.2 Pearch::SearchService
    - 13.3 Pearch::CreditsService
    - 13.4 Pearch::SearchProfilesBuilder
    - 13.5 ProcessSourcingJob
14. [Busca de Candidatos Similares](#14-candidatos-similares)
15. [AI Analysis & Enrichment](#15-ai-analysis)
16. [WebSocket — SourcingChannel](#16-websocket)
17. [Suggestion Service (Copilot)](#17-suggestion-service)
18. [Conversão SourcedProfile → Candidate](#18-conversão)
19. [Tabela de Referência: Todos os Arquivos](#19-referência)

---

## 1. Visão Geral da Arquitetura

O sistema de busca combina duas fontes de dados:

| Fonte | Descrição | Banco | Custo |
|-------|-----------|-------|-------|
| **Local** | Candidatos já cadastrados na base do ATS | Elasticsearch (full-text) + pgvector (semântico) | Gratuito |
| **Global** | Candidatos da base externa Pearch (~500M perfis) | API REST externa | Créditos Pearch |

Quando ambas as fontes são usadas (`sources: ["local", "global"]`), o provider do Sourcing é `"hybrid"`.

### Stack Tecnológica

- **Elasticsearch** (via Searchkick): busca full-text com campos ponderados
- **pgvector**: busca semântica por similaridade de embeddings (768 dims, cosine distance)
- **Gemini API**: geração de embeddings (`gemini-embedding-001`) + análise de queries + HyDE
- **Pearch API v2**: busca global de candidatos
- **Redis**: cache de análises de query (1h TTL)
- **PostgreSQL**: cache de embeddings (24h TTL via `EmbeddingCache` model)
- **ActionCable**: WebSocket para progresso em tempo real
- **Sidekiq**: processamento assíncrono de jobs

---

## 2. Diagrama de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────────────­────┐
│                        REQUISIÇÃO DO USUÁRIO                                            │
│         POST /v1/users/sourcings { query, sources: ["local","global"], filters }        │
└────────────────────────────────────────┬────────────────────────────────────────────────-┘
                                         │
                                         ▼
              ┌──────────────────────────────────────────────────────────┐
              │          V1::Users::SourcingsController#create          │
              │                                                        │
              │  1. parse_sources → ["local"], ["global"] ou ambos     │
              │  2. create Sourcing (provider: local/global/hybrid)     │
              │  3. attach_files_to_sourcing (se enviou arquivos)       │
              │  4. PARA CADA source:                                   │
              │     └─ Sourcings::JobEnqueuerService.new(...).call      │
              └──────────────────┬─────────────────┬────────────────────┘
                                 │                 │
                    source="local"                 source="global"
                                 │                 │
                                 ▼                 ▼
┌────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  Candidates::LocalSearchJob        │  │  Pearch::TalentSearchJob             │
│  (Sidekiq, queue: default)         │  │  (Sidekiq, queue: default)           │
│                                    │  │                                      │
│  1. Switch tenant                  │  │  1. Switch tenant                    │
│  2. Aplicar 11 transformações      │  │  2. Pearch::SearchService.search()   │
│     de filtros                     │  │     - Validar créditos               │
│  3. HybridSearchService.search()   │  │     - HTTP POST api.pearch.ai/v2    │
│     ┌───────────────────────┐      │  │     - Consumir créditos              │
│     │ SimpleQueryDetector   │      │  │  3. ProcessSourcingJob               │
│     │   ├─ :simple          │      │  │     - Criar SourcedProfiles          │
│     │   ├─ :complex         │      │  │     - Deduplicar via                 │
│     │   ├─ :resume          │      │  │       ProfileMatchingService         │
│     │   └─ :job_description │      │  │     - Criar SourcedProfileSourcings  │
│     └───────────────────────┘      │  │                                      │
│                                    │  │                                      │
│  ┌──────────┐  ┌───────────────┐   │  └──────────────────────────────────────┘
│  │ Elastic  │  │ Embedding     │   │
│  │ search   │  │ (pgvector)    │   │
│  │ Strategy │  │ Strategy      │   │
│  └────┬─────┘  └──────┬────────┘   │
│       │               │            │
│       ▼               ▼            │
│  ┌─────────────────────────────┐   │
│  │ WeightedRankFusion (RRF)    │   │
│  │ K=60, weights dinâmicos     │   │
│  └──────────────┬──────────────┘   │
│                 ▼                  │
│  ┌─────────────────────────────┐   │
│  │ Reranker                    │   │
│  │ content quality + contact   │   │
│  │ + recency + skill match     │   │
│  └──────────────┬──────────────┘   │
│                 ▼                  │
│  Criar SourcedProfile +            │
│  SourcedProfileSourcing            │
│       │                            │
│       ▼                            │
│  after_commit →                    │
│  AiAnalysisJob (scoring)           │
└────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ SourcingChannel  │
        │ (WebSocket)      │
        │ Broadcast a cada │
        │ etapa/profile    │
        └─────────────────┘
```

---

## 3. Rotas

**Arquivo:** `config/routes.rb`

```
POST   /v1/users/sourcings                              → SourcingsController#create
GET    /v1/users/sourcings                              → SourcingsController#index
GET    /v1/users/sourcings/:id                          → SourcingsController#show
PATCH  /v1/users/sourcings/:id                          → SourcingsController#update
GET    /v1/users/sourcings/:id/stats                    → SourcingsController#stats
GET    /v1/users/sourcings/:id/context_for_ai           → SourcingsController#context_for_ai
POST   /v1/users/sourcings/:id/recalculate_stats        → SourcingsController#recalculate_stats
POST   /v1/users/sourcings/:id/refine                   → SourcingsController#refine
GET    /v1/users/sourcings/history                      → SourcingsController#history
GET    /v1/users/sourcings/credits                      → SourcingsController#credits
GET    /v1/users/sourcings/transactions                 → SourcingsController#transactions
POST   /v1/users/sourcings/search_profiles              → SourcingsController#search_profiles
POST   /v1/users/sourcings/find_similar_candidates      → SourcingsController#find_similar_candidates
```

---

## 4. Controller

**Arquivo:** `app/controllers/v1/users/sourcings_controller.rb`  
**Classe:** `V1::Users::SourcingsController < ApplicationController`

### Ações Públicas

| Ação | Parâmetros | Descrição |
|------|-----------|-----------|
| `index` | filtros padrão | Lista sourcings via Searchkick |
| `create` | `query`, `sources`, `files`, filtros | Cria `Sourcing`, enfileira jobs por source |
| `show` | `:id` | Retorna detalhes do sourcing |
| `update` | `:id`, `saved`, `notes`, `status`, `is_deleted` | Atualiza sourcing |
| `stats` | `:id` | Stats + distribuição de score + ROI |
| `context_for_ai` | `:id` | Dados para contexto AI |
| `recalculate_stats` | `:id` | Enfileira `Sourcings::CalculateStatsJob` |
| `refine` | `:id`, `liked_candidate_ids`, etc. | DEPRECATED — refinamento por feedback |
| `history` | `page`, `per_page` | Histórico agrupado por data |
| `credits` | `start_date`, `end_date` | Estatísticas de créditos |
| `transactions` | `limit`, `start_date`, `end_date` | Histórico de transações |
| `search_profiles` | — | Perfis de busca Pearch + saldo |
| `find_similar_candidates` | `candidate_ids`, `job_id`, `limit`, etc. | Busca candidatos similares |

### Métodos Privados Chave

| Método | Responsabilidade |
|--------|-----------------|
| `parse_sources` | Normaliza param `sources` para `["local"]`, `["global"]` ou ambos |
| `create_sourcing(sources)` | Cria Sourcing com `determine_provider` (hybrid se >1 source) |
| `enqueue_searches(sourcing, sources)` | Chama `Sourcings::JobEnqueuerService` para cada source |
| `handle_linkedin_sourcing(sources)` | Caminho especial para parsing de perfis LinkedIn |
| `attach_files_to_sourcing(sourcing)` | Extrai texto de arquivos via Yomu, opcionalmente gera query via `SuggestionService` |
| `build_pearch_options(pearch_params)` | Parseia opções do Pearch |

---

## 5. Models

### 5.1 Sourcing

**Arquivo:** `app/models/sourcing.rb`

| Associação | Tipo |
|-----------|------|
| `user` | `belongs_to` |
| `account` | `belongs_to` |
| `search_archetype` | `belongs_to` (optional) |
| `sourced_profiles` | `has_many` |
| `sourced_profile_sourcings` | `has_many` |
| `candidate_feedbacks` | `has_many` |
| `files` | `has_many_attached` |

**Validações:** `provider` ∈ `[pearch, linkedin, local, global, hybrid]`, `status` ∈ `[done, processing, failed]`

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `local?` | Boolean | true se provider=local ou hybrid com source local |
| `global?` | Boolean | true se provider=global/pearch ou hybrid com global |
| `hybrid?` | Boolean | true se provider=hybrid |
| `sources` | Array | Array de sources do campo parameters |
| `top_profiles(limit)` | ActiveRecord | Top profiles por score via SPS |
| `new_profiles` | ActiveRecord | Profiles ativos com status "new" |
| `stats` | Hash | Contagens por status, avg_score, info de contato |
| `score_distribution` | Hash | Contagem agrupada por score |
| `cost_per_profile` | Float | credits_used / profiles ativos |
| `roi_metrics` | Hash | Percentuais de utilidade + custo |

### 5.2 SourcedProfile

**Arquivo:** `app/models/sourced_profile.rb`

| Associação | Tipo |
|-----------|------|
| `sourcing` | `belongs_to` (optional) |
| `account` | `belongs_to` |
| `candidate` | `belongs_to` (optional) |
| `sourced_profile_sourcings` | `has_many` |
| `sourcings` | `has_many :through` |
| `sector_relationships` | `has_many` |
| `skill_relationships` | `has_many` |

**Validações:** `provider` ∈ `[pearch, linkedin, local]`, `status` ∈ `[new, viewed, interested, contacted, rejected, hired]`

| Método | Descrição |
|--------|-----------|
| `full_name` | Nome completo |
| `imported?` | true se `candidate_id` presente |
| `mark_as_viewed!` | Atualiza status para "viewed" |
| `experiences` / `educations` / `certifications` | Dados estruturados do profile_data |
| `current_experience` / `current_company_name` / `current_role` | Extração da experiência atual |
| `similar_profiles(limit)` | Busca profiles similares por embedding |
| `search_data` | Hash para indexação Searchkick |
| `find_existing_by_identity(...)` | Class method — deduplicação por external_id, CPF, email, linkedin |

### 5.3 SourcedProfileSourcing (Tabela Join)

**Arquivo:** `app/models/sourced_profile_sourcing.rb`

Liga `SourcedProfile` ↔ `Sourcing` com dados específicos por sourcing:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `score` | Float | Score da AI analysis |
| `analysis` | JSON | Resultado da análise AI |
| `ai_metadata` | JSON | Metadados da execução AI |
| `search_source` | String | "local", "global", "local_sourced" |
| `search_score` | Float | Score do motor de busca |
| `similarity_score` | Float | Score de similaridade vetorial |

**Callbacks:**
- `after_commit :enqueue_ai_analysis, on: :create` → Enfileira `SourcedProfiles::AiAnalysisJob`
- `after_commit :enqueue_stats_recalculation` → Recalcula stats do sourcing

| Método | Descrição |
|--------|-----------|
| `self.include_base` | SQL select com joins de dados do profile |
| `search_data` | Hash para indexação Searchkick |
| `get_candidate_feedback_type` | Tipo de feedback do candidato |

### 5.4 SourcingFilter

**Arquivo:** `app/models/sourcing_filter.rb`

Presets de filtros salvos pelo usuário.

| Método | Descrição |
|--------|-----------|
| `increment_usage!` | Incrementa contador de uso |
| `to_search_params` | Converte para parâmetros de busca |

---

## 6. Enfileiramento

**Arquivo:** `app/services/sourcings/job_enqueuer_service.rb`  
**Classe:** `Sourcings::JobEnqueuerService`

Roteador que despacha para o job correto baseado no `source`.

| Método | Visibilidade | Descrição |
|--------|-------------|-----------|
| `initialize(user:, sourcing:, query:, params:)` | public | Armazena contexto |
| `call` | public | Roteia para `enqueue_local_search` ou `enqueue_global_search` |
| `enqueue_local_search` | private | `Candidates::LocalSearchJob.perform_async(account_id, user_id, sourcing_id, query, where_json, filter_json, order_json, max_pages, return_sourced)` |
| `enqueue_global_search` | private | Transforma filtros internos → custom_filters Pearch, chama `Pearch::TalentSearchJob.perform_async(...)` |

### Mapeamento de Filtros para Pearch (Global)

| Filtro Interno | Filtro Pearch |
|---------------|--------------|
| `years_of_experience` (range) | `custom_filters.years_experience` (min/max) |
| `current/previous_job_titles` | `custom_filters.titles` |
| `job_levels` | `custom_filters.keywords` (com mapeamento bilíngue PT/EN) |
| `function_area_list` | `custom_filters.keywords` |
| `top_universities` | `custom_filters.studied_at_top_universities: true` |
| `startup_experience` | `custom_filters.has_startup_experience: true` |
| `decision_maker` | Adiciona CEO/CTO/Director aos titles |
| `open_to_opportunities` | Adiciona "open to work" aos keywords |
| `min/max_current_experience_years` | Convertido para meses |

---

## 7. Busca Local

### 7.1 Candidates::LocalSearchJob

**Arquivo:** `app/jobs/candidates/local_search_job.rb`  
**Classe:** `Candidates::LocalSearchJob` (Sidekiq, queue: `default`, retry: 2)

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `perform` | `account_id, user_id, sourcing_id, search_text, where_json, filter_json, order_json, max_pages, return_sourced` | Entry point — switch tenant, chama `execute_search` |
| `execute_search` | `sourcing_id, search_text, where_json, filter_json` | Parseia filtros, aplica 11 transformações, roteia para `execute_candidates_search` ou `execute_sourced_profile_sourcings_search` |
| `execute_candidates_search` | `sourcing, search_text, user_filters, limit` | **Cria `HybridSearchService`**, chama `.search(...)`, processa resultados em `SourcedProfile`/`SourcedProfileSourcing` |
| `execute_sourced_profile_sourcings_search` | `sourcing, search_text, user_filters, limit` | Busca `SourcedProfileSourcing` existentes via `SourcedProfileSourcings::SearchService` |
| `process_candidates` | `candidates, sourcing, account, user, search_meta_by_id` | Cria/linka `SourcedProfile` para cada candidato, broadcast via WebSocket |
| `create_or_update_sourced_profile` | `sourcing, candidate, account, user, search_meta` | Encontra existente ou cria novo `SourcedProfile` + `SourcedProfileSourcing` |

#### 11 Transformações de Filtros

| # | Método | Filtro |
|---|--------|--------|
| 1 | `apply_has_email_filter` | Filtra por presença de email |
| 2 | `apply_has_phone_filter` | Filtra por presença de telefone |
| 3 | `apply_has_email_or_phone_filter` | Email OU telefone |
| 4 | `apply_years_of_experience_filter` | Range de anos de experiência |
| 5 | `apply_current_role_time_filter` | Tempo na posição atual |
| 6 | `apply_average_time_in_companies_filter` | Média de tempo em empresas |
| 7 | `apply_hide_scope_filter` | Esconder candidatos já vistos |
| 8 | `apply_current_job_titles_filter` | Cargo atual |
| 9 | `apply_previous_job_titles_filter` | Cargos anteriores |
| 10 | `apply_job_levels_filter` | Nível/senioridade |
| 11 | `apply_function_area_list_filter` | Área funcional |

#### Sistema de Fallback

Se a busca principal retorna poucos resultados, tenta 3 estratégias progressivas + opcionalmente consulta LLM para sugestão alternativa via `ask_llm_for_alternative`.

### 7.2 SearchArchetypes::LocalSearchJob

**Arquivo:** `app/jobs/search_archetypes/local_search_job.rb`  
**Classe:** `SearchArchetypes::LocalSearchJob` (Sidekiq, queue: `default`, retry: 2)

Variante que usa **Search Archetypes** (templates pré-configurados de busca).

| Método | Descrição |
|--------|-----------|
| `perform(account_id, user_id, sourcing_id, archetype_id, profile, additional_options)` | Entry point para buscas baseadas em archetype |
| `execute_search` | Converte archetype → search params via `SearchArchetypes::ToLocalSearchService` |
| `execute_hybrid_search` | Cria `HybridSearchService`, constrói filtros, busca, processa |
| `execute_legacy_search` | Fallback para `Candidates::LocalSearchJob` |

---

## 8. HybridSearchService — Core da Busca

**Arquivo:** `app/services/candidates/search/hybrid_search_service.rb`  
**Classe:** `Candidates::Search::HybridSearchService`  
**Linhas:** ~873

Este é o **coração de toda a busca local**. Orquestra Elasticsearch + pgvector com múltiplos caminhos de busca.

### Struct de Resultado

```ruby
Result = Struct.new(:candidates, :metadata, :explanation, :search_meta_by_id)
```

### Dependências (inicializadas no constructor)

| Dependência | Classe | Uso |
|------------|--------|-----|
| `@es_strategy` | `ElasticsearchStrategy` | Busca full-text |
| `@emb_strategy` | `EmbeddingStrategy` | Busca semântica |
| `@embedding_cache` | `EmbeddingCache` | Cache de embeddings |
| `@query_analyzer` | `QueryAnalyzer` | Análise da query via LLM |
| `@hyde_expander` | `HydeQueryExpander` | Expansão HyDE |
| `@profile_extractor` | `ProfileExtractor` | Extração de perfil de currículos |
| `@multi_query_generator` | `MultiQueryGenerator` | Geração de múltiplas queries |
| `@hyde_generator` | `HydeDocumentGenerator` | Geração de CVs hipotéticos |
| `@jd_processor` | `JobDescriptionProcessor` | Processamento de JDs |

### Método Público

```ruby
search(query_text, user_filters: {}, limit: 50, debug: false) → Result
```

### 8.1 Detecção de Tipo de Query

Via `SimpleQueryDetector.detect(query)`:

| Tipo | Condição | Método Chamado |
|------|---------|---------------|
| `:simple` | 1-3 palavras, sem conectores complexos | `execute_simple_search` |
| `:resume` | >500 chars, >50 palavras, padrões de CV | `execute_resume_search` |
| `:job_description` | 3+ indicadores de JD (requisitos, responsabilidades, etc.) | `execute_jd_search` |
| `:complex` | Default (múltiplos requisitos, conectores lógicos) | `execute_complex_search` |

### 8.2 Busca Simples (`execute_simple_search`)

**Caminho mais rápido** — pula o QueryAnalyzer (~1.3s de economia).

```
Query Text
    │
    ├─── ElasticsearchStrategy.search(query, pool_size * 2)
    │         └─ Searchkick: campos ponderados, minimum_should_match dinâmico
    │
    ├─── EmbeddingCache.fetch(query) → vetor 768-dim
    │         └─ EmbeddingStrategy.search(embedding, pool_size)
    │              └─ apply_embedding_relevance_filter (threshold: 0.70)
    │
    └─── WeightedRankFusion.combine(es: 0.70, emb: 0.30)
              │
              ▼
         Reranker.apply(fused, limit)
              │
              ▼
         load_in_order(ids) → Candidate records
              │
              ▼
         build_search_meta_by_id → Result
```

**Retry:** Se `fused.size < limit` → retry com pool ×2 (capped em `max_pool_size`).

### 8.3 Busca Complexa (`execute_complex_search`)

**Caminho mais completo** — usa QueryAnalyzer (LLM) + HyDE.

```
Query Text
    │
    ├─── QueryAnalyzer.analyze(query)
    │         └─ Cache (SHA256, 1h TTL) → ou Gemini LLM (3s timeout)
    │         └─ Retorna: elasticsearch_query, embedding_query, confidence, entities
    │
    ├─── HydeQueryExpander.expand(query)
    │         └─ Gemini LLM → "mini CV hipotético do candidato ideal"
    │
    ├─── EmbeddingCache.fetch(hyde_text OU embedding_query)
    │         └─ Vetor 768-dim
    │
    ├─── ElasticsearchStrategy.search(analysis.elasticsearch_query)
    │
    ├─── EmbeddingStrategy.search(embedding)
    │
    ├─── AdaptivePool.adjust(es, emb, current_pool)
    │         └─ overlap < 0.2 → aumenta pool 1.5x, retry
    │         └─ overlap > 0.5 → diminui pool 0.8x
    │
    ├─── apply_embedding_keyword_gate(emb, analysis)
    │         └─ Remove embeddings que não contêm nenhum termo de busca no curriculum/role
    │
    ├─── fusion_weights_for(es_count, emb_count, overlap)
    │         └─ Dinâmico: se ES tem poucos (≤2) e emb tem muitos (≥5) → {es: 0.80, emb: 0.20}
    │
    ├─── WeightedRankFusion.combine(weights dinâmicos)
    │
    ├─── Reranker.apply(fused, limit)
    │
    └─── Se overlap baixo → es_first_ordered_ids (IDs do ES primeiro, depois embedding-only)
```

### 8.4 Busca por Currículo (`execute_resume_search`)

**Para queries longas (>500 chars)** — texto de currículo colado.

```
Resume Text
    │
    ├─── ProfileExtractor.extract(resume_text, source_type: :resume)
    │         └─ LLM → {seniority, years_experience, primary_role, core_technologies,
    │                    transferable_skills, industry}
    │         └─ Fallback: extração estruturada → keyword-based
    │
    ├─── MultiQueryGenerator.generate(profile, context: :resume)
    │         └─ 5 queries com pesos: role(0.3), tech(0.25), industry(0.2),
    │            experience(0.15), hybrid(0.1)
    │
    ├─── ElasticsearchStrategy.search(keywords do profile)
    │
    ├─── Para CADA query gerada:
    │         └─ HydeDocumentGenerator.generate(profile) → CV hipotético
    │         └─ EmbeddingCache.fetch(hyde_cv)
    │         └─ EmbeddingStrategy.search(embedding)
    │         └─ deduplicate_and_boost (IDs repetidos ganham boost)
    │
    ├─── Confidence-adjusted fusion weights:
    │         └─ confidence ≥ 0.75 → {es: 0.35, emb: 0.65}
    │         └─ confidence ≥ 0.50 → {es: 0.50, emb: 0.50}
    │         └─ confidence < 0.50 → {es: 0.70, emb: 0.30}
    │
    └─── WeightedRankFusion → Reranker → Result
```

### 8.5 Busca por Job Description (`execute_jd_search`)

**Para descrições de vagas** — combina skill matching com busca semântica.

```
JD Text
    │
    ├─── JobDescriptionProcessor.process(jd_text)
    │         └─ LLM (ou regex fallback) → {required_skills, nice_to_have_skills,
    │            seniority_range, role_titles, industry_keywords, experience_range,
    │            search_queries, boost_config}
    │
    ├─── build_jd_elasticsearch_query(processed_jd)
    │         └─ required_skills + first role_title + first 3 nice_to_have
    │
    ├─── execute_jd_embedding_search(processed_jd)
    │         └─ HydeDocumentGenerator.generate(profile, context: :job_description)
    │         └─ EmbeddingStrategy.search(jd_embedding)
    │
    ├─── WeightedRankFusion.combine(es: 0.60, emb: 0.40)
    │
    └─── Reranker.apply(fused, limit, custom_boost_config: processed_jd.boost_config)
              └─ Boost extra por match de skills requeridas no curriculum_text
```

### Métodos Auxiliares Chave

| Método | Descrição |
|--------|-----------|
| `effective_pool_size(limit)` | `(limit * 4).clamp(min_pool, max_pool)` |
| `handle_fallback(...)` | Embedding-only → ES-only → empty |
| `fusion_weights_for(es_count, emb_count, overlap)` | Pesos dinâmicos baseados em contagem e sobreposição |
| `es_first_ordered_ids(es, emb, limit)` | IDs do ES primeiro quando overlap é baixo |
| `load_in_order(ids)` | Carrega candidates preservando ordem |
| `build_search_meta_by_id(reranked, ids)` | `{id => {source: "both"/"elasticsearch"/"embedding", score: Float}}` |

---

## 9. Estratégias de Busca

### 9.1 ElasticsearchStrategy

**Arquivo:** `app/services/candidates/search/elasticsearch_strategy.rb`  
**Classe:** `Candidates::Search::ElasticsearchStrategy`

Busca full-text via **Searchkick** (Elasticsearch).

```ruby
search(query, user_filters: {}, pool_size: 100) → [{id:, rank:, score:, source: :elasticsearch}]
```

#### Campos Ponderados (search fields)

| Campo | Peso | Descrição |
|-------|------|-----------|
| `experiences_a` | ^7 | Experiências (mais relevante) |
| `curriculum_text` | ^5 | Texto do currículo |
| `role_name` | ^3 | Cargo atual |
| `recent_roles` | ^3 | Cargos recentes |
| `name` | ^2 | Nome do candidato |
| `current_company` | ^2 | Empresa atual |
| `self_introduction` | ^1 | Auto-apresentação |

#### Threshold Dinâmico (`minimum_should_match`)

| Tamanho da Query | Threshold |
|-----------------|-----------|
| 1-2 palavras | 100% |
| 3-4 palavras | 60% |
| 5-8 palavras | 40% |
| 9-20 palavras | 25% |
| 20+ palavras | 15% |

#### 14 Transformações de Filtros

`apply_years_of_experience_range`, `apply_current_role_time_range`, `apply_average_time_in_companies_range`, `apply_current_job_titles_filter`, `apply_previous_experiences_filter`, `apply_experiences_filter`, `apply_sectors_filter`, `apply_companies_filter`, `apply_company_sectors_filter`, `apply_universities_filter`, `extract_study_areas_filter`, `apply_academic_degree_filter`, `apply_skills_filter`, `apply_skill_categories_filter`, `apply_languages_filter`

### 9.2 EmbeddingStrategy

**Arquivo:** `app/services/candidates/search/embedding_strategy.rb`  
**Classe:** `Candidates::Search::EmbeddingStrategy`

Busca semântica via **pgvector** (similaridade de coseno).

```ruby
search(query_embedding, user_filters: {}, pool_size: 100) → [{id:, rank:, distance:, source: :embedding}]
```

#### Fluxo

1. Aplica **pré-filtros** restritivos (previous_experiences, sectors_a)
2. Query pgvector: `Embedding.for_candidates.nearest_neighbors(:embedding, query_embedding, distance: "cosine")`
3. Filtra por `max_distance` (configurável)
4. Aplica **filtros SQL whitelisted**: role_name, experiences, sectors, current_role_time, average_time_in_companies

#### Filtros Whitelisted para pgvector

Apenas filtros que podem ser aplicados via SQL na query pgvector:

`role_name`, `experiences_a`, `sectors_a`, `current_role_time_min`, `current_role_time_max`, `average_time_in_companies_min`, `average_time_in_companies_max`

---

## 10. Fusão e Ranking

### 10.1 WeightedRankFusion (RRF)

**Arquivo:** `app/services/candidates/search/weighted_rank_fusion.rb`  
**Classe:** `Candidates::Search::WeightedRankFusion`

Implementa **Reciprocal Rank Fusion** com pesos por fonte.

#### Fórmula

```
rrf_score = 1.0 / (K + rank)
weighted_score = weight × rrf_score
final_score = Σ weighted_scores (de todas as fontes)
```

- **K = 60** (constante RRF, configurável via `Configuration.rrf_k_constant`)
- **Pesos default:** `{ elasticsearch: 0.65, embedding: 0.35 }`

#### Struct de Saída — `RankedCandidate`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID do candidato |
| `contributions` | Hash | `{source → {rank, rrf_score, weighted_score, raw_score}}` |
| `final_score` | Float | Score final (soma dos weighted_scores) |
| `appeared_in_both?` | Boolean | Apareceu em ambas as fontes |
| `sources` | Array | Lista de fontes |

### 10.2 Reranker

**Arquivo:** `app/services/candidates/search/reranker.rb`  
**Classe:** `Candidates::Search::Reranker`

Reranking baseado em qualidade aplicado **após** a fusão RRF.

```ruby
Reranker.apply(ranked_candidates, limit:, custom_boost_config: nil) → [RerankedCandidate]
```

#### Fluxo

1. Pega top `limit × 2` candidatos
2. Carrega dados via `pluck` (sem carregar AR completo): email, phone, curriculum_text, updated_at
3. Calcula boost por candidato
4. `final_score = rrf_score × (1 + boost)`

#### Tiers de Qualidade de Conteúdo

| Chars no curriculum_text | Quality Score |
|--------------------------|--------------|
| > 2000 | 1.0 |
| > 1000 | 0.8 |
| > 500 | 0.6 |
| > 200 | 0.4 |
| ≤ 200 | 0.2 |

#### Sinais de Boost

| Sinal | Condição | Boost |
|-------|---------|-------|
| `rich_content` | quality ≥ 0.8 | +15% |
| `good_content` | quality ≥ 0.6 | +10% |
| `basic_content` | quality ≥ 0.4 | +5% |
| `has_contact` | email ou phone presentes | +5% |
| `is_recent` | updated_at < 90 dias | +3% |
| `empty_profile` (penalidade) | quality < 0.2 E sem contato | -20% |

#### Custom Boost (JD matching)

Conta quantas `required_skills` do JD aparecem no `curriculum_text`:

```
boost = config_weight × (matched_skills / total_skills)
```

### 10.3 AdaptivePool

**Arquivo:** `app/services/candidates/search/adaptive_pool.rb`  
**Classe:** `Candidates::Search::AdaptivePool`

Ajusta dinamicamente o tamanho do pool baseado na sobreposição entre ES e embeddings.

```ruby
AdaptivePool.adjust(es_results, emb_results, current_pool:) → PoolAdjustment
```

| Overlap (Jaccard) | Ação | Novo Pool |
|-------------------|------|-----------|
| < 0.2 | Aumenta e sinaliza retry | pool × 1.5 |
| > 0.5 | Diminui (resultados redundantes) | pool × 0.8 |
| 0.2 - 0.5 | Mantém | pool atual |

---

## 11. Serviços de Suporte à Busca

### 11.1 SimpleQueryDetector

**Arquivo:** `app/services/candidates/search/simple_query_detector.rb`

Detecta o tipo da query para escolher o caminho de busca.

| Classe Method | Retorno | Lógica |
|--------------|---------|--------|
| `detect(query)` | `:simple` / `:complex` / `:resume` / `:job_description` | Checa indicadores JD → CV → complex → default simple |
| `simple?(query)` | Boolean | |
| `complex?(query)` | Boolean | Múltiplos requisitos, conectores lógicos |
| `resume?(query)` | Boolean | >500 chars, >50 words, 2+ padrões de CV, nomes próprios, datas |
| `job_description?(query)` | Boolean | 3+ indicadores (requisitos, responsabilidades, benefícios) |

### 11.2 QueryAnalyzer

**Arquivo:** `app/services/candidates/search/query_analyzer.rb`

Analisa a query via LLM para otimizar a busca.

```ruby
analyze(query_text) → QueryAnalysis
```

| Campo do QueryAnalysis | Tipo | Descrição |
|----------------------|------|-----------|
| `original_query` | String | Query original |
| `entities` | Hash | `{role:, skills:, location:, seniority:, company:}` |
| `expanded_terms` | Array | Termos expandidos |
| `keyword_query` | String | Query otimizada para ES |
| `embedding_query` | String | Query otimizada para embedding |
| `confidence` | Float | 0.0 - 1.0 |

- **Cache:** SHA256 da query, TTL 1h
- **LLM:** Gemini, timeout 3s
- **Fallback:** `QueryAnalysis.passthrough(query)` — retorna query original com confidence 1.0

### 11.3 HydeQueryExpander

**Arquivo:** `app/services/candidates/search/hyde_query_expander.rb`

**HyDE = Hypothetical Document Embeddings**

```ruby
expand(query_text) → String (mini CV hipotético)
```

Gera um "mini currículo hipotético" do candidato ideal via Gemini LLM. Cache 1h. Usado para criar uma query de embedding mais rica na busca complexa.

### 11.4 HydeDocumentGenerator

**Arquivo:** `app/services/candidates/search/hyde_document_generator.rb`

```ruby
generate(profile, context: :resume, verbosity: :standard) → String
```

Gera documento hipotético (CV) a partir de um hash de perfil usando templates. 4 templates: `RESUME_HYDE_TEMPLATE`, `RESUME_CONCISE_TEMPLATE`, `JD_HYDE_TEMPLATE`, `JD_CONCISE_TEMPLATE`.

### 11.5 ProfileExtractor

**Arquivo:** `app/services/candidates/search/profile_extractor.rb`

```ruby
extract(text, source_type: :resume) → ExtractionResult
```

| Campo do ExtractionResult | Tipo |
|--------------------------|------|
| `profile` | Hash `{seniority, years_experience, primary_role, core_technologies, transferable_skills, industry}` |
| `confidence` | Float |
| `extraction_method` | Symbol `:llm` / `:structured` / `:keyword` |
| `missing_fields` | Array |

Cascade: LLM → extração estruturada → keyword-based.

### 11.6 MultiQueryGenerator

**Arquivo:** `app/services/candidates/search/multi_query_generator.rb`

```ruby
generate(profile, context: :resume) → Result{queries:, weights:, strategy_used:}
```

Gera até 5 queries a partir de um perfil extraído:

| Query | Foco | Peso |
|-------|------|------|
| 1 | Role-focused | 0.30 |
| 2 | Tech-focused | 0.25 |
| 3 | Industry-focused | 0.20 |
| 4 | Experience-focused | 0.15 |
| 5 | Hybrid | 0.10 |

### 11.7 JobDescriptionProcessor

**Arquivo:** `app/services/candidates/search/job_description_processor.rb`

```ruby
process(jd_text) → ProcessedJD
```

| Campo do ProcessedJD | Tipo | Descrição |
|---------------------|------|-----------|
| `required_skills` | Array | Skills obrigatórias |
| `nice_to_have_skills` | Array | Skills desejáveis |
| `seniority_range` | Hash | Range de senioridade |
| `role_titles` | Array | Títulos do cargo |
| `industry_keywords` | Array | Palavras-chave da indústria |
| `experience_range` | Hash | Range de experiência |
| `search_queries` | Array | Queries de busca geradas |
| `boost_config` | Hash | Configuração de boost para o Reranker |

Detecção de tipo de documento (`:job_description` / `:resume` / `:unknown`) → extração via LLM → fallback para regex.

---

## 12. Infraestrutura

### 12.1 Configuration

**Arquivo:** `app/services/candidates/search/configuration.rb`

Centraliza todas as constantes e configurações da busca.

| Método | Valor | Descrição |
|--------|-------|-----------|
| `initial_pool_size` | 100 | Pool inicial de busca |
| `min_pool_size` | 50 | Pool mínimo |
| `max_pool_size` | 300 | Pool máximo |
| `final_limit` | 50 | Limite default de resultados |
| `max_pool_retries` | 2 | Max retries do AdaptivePool |
| `rrf_k_constant` | 60 | Parâmetro K do RRF |
| `default_weights` | `{es: 0.65, emb: 0.35}` | Pesos padrão |
| `es_pool_multiplier` | 1.25 | Pedir 25% a mais ao ES |
| `emb_pool_multiplier` | 0.8 | Pedir 20% menos ao embedding |
| `embedding_cache_ttl` | 24h | TTL do cache de embeddings |
| `embedding_model_name` | `ENV[EMBEDDING_MODEL]` / `gemini-embedding-001` | Modelo de embedding |
| `embedding_max_distance` | `ENV[EMBEDDING_MAX_DISTANCE]` | Distância max cosine |
| `embedding_keyword_gate?` | `ENV[EMBEDDING_KEYWORD_GATE]` / true | Habilitar keyword gate |
| `embedding_relevance_threshold` | `ENV` / 0.70 | Threshold mínimo de relevância |
| `require_curriculum_text?` | `ENV` / true | Exigir curriculum_text |
| `pgvector_allowed_filters` | Array de symbols | Whitelist de filtros para pgvector |
| `locked_filters` | `[:account_id, :is_deleted]` | Filtros não sobrescrevíveis |

### 12.2 BaseFilters / FilterMerger

**Arquivo:** `app/services/candidates/search/base_filters.rb`  
**Arquivo:** `app/services/candidates/search/filter_merger.rb`

| Classe | Método | Descrição |
|--------|--------|-----------|
| `BaseFilters` | `to_hash` | `{account_id:, is_deleted: false, has_curriculum: true}` |
| `BaseFilters` | `base_scope(relation)` | `relation.where(account_id:, is_deleted: false)` |
| `FilterMerger` | `merge(base, user, warn_on_override:)` | Rejeita locked filters do user, merge com base |
| `FilterMerger` | `whitelist_for_pgvector(user_filters)` | Retorna apenas filtros permitidos para pgvector |

### 12.3 EmbeddingCache / QueryEmbeddingCache

#### EmbeddingCache (Database-backed)

**Arquivo:** `app/services/candidates/search/embedding_cache.rb`

- **Storage:** Model `::EmbeddingCache` (ActiveRecord)
- **Key:** `"search_emb:{model_version}:{account_id}:{sha256[0..15]}"`
- Cache hit: toca `last_accessed_at`
- Cache miss: gera via `EmbeddingService`, cria record
- Race condition: `RecordNotUnique` → `find_by!`

#### QueryEmbeddingCache (Rails.cache-backed)

**Arquivo:** `app/services/candidates/search/query_embedding_cache.rb`

- **Storage:** `Rails.cache` (Redis)
- **Key:** `"search_embedding:{tenant}:{sha256[0..15]}"`
- Mais leve que `EmbeddingCache`

### 12.4 EmbeddingService

**Arquivo:** `app/services/candidates/search/embedding_service.rb`

```ruby
generate(text) → Array[Float] (768 dims) ou nil
```

Wrapper do `GeminiClient.embeddings(text:, model:, dimensions: 768)`.

### 12.5 SearchTelemetry / SearchExplainer

**Arquivo:** `app/services/candidates/search/search_telemetry.rb`  
**Arquivo:** `app/services/candidates/search/search_explainer.rb`

Tracking de timing, eventos e construção de explicações detalhadas da busca.

| Classe | Métodos Chave |
|--------|--------------|
| `SearchTelemetry` | `time(name)`, `event(name, data)`, `elapsed_ms`, `log_summary(...)`, `build_simple_explanation(...)` |
| `SearchExplainer` | `log_step(name, data)`, `time(name)`, `build_explanation(...)` |

---

## 13. Busca Global — Pearch

### 13.1 Pearch::TalentSearchJob

**Arquivo:** `app/jobs/pearch/talent_search_job.rb`  
**Classe:** `Pearch::TalentSearchJob` (Sidekiq, queue: `default`, retry: 2)

| Método | Descrição |
|--------|-----------|
| `perform(account_id, user_id, sourcing_id, query, params_json)` | Entry point |
| `execute_search` | Chama `TalentSearchExecutorService` |
| `update_sourcing_with_result` | Atualiza sourcing com resultados |
| `enqueue_profile_processing` | Enfileira `ProcessSourcingJob` |
| `broadcast_sourcing_started/completed` | WebSocket events |

### 13.2 Pearch::SearchService

**Arquivo:** `app/services/pearch/search_service.rb`

**API:** `https://api.pearch.ai/v2/search` (timeout: 180s)

```ruby
search(query:, **options) → Hash
```

#### Fluxo

1. **Validar créditos** via `CreditsService`
2. **Build params** (query, type, limit, custom_filters, etc.)
3. **HTTP POST** para Pearch API
4. **Parse response**
5. **Log search** + **consumir créditos**
6. Se não `skip_sourcing_creation`: atualiza Sourcing + enfileira `ProcessSourcingJob`

#### Estimativa de Custo

```
custo = limit × type_cost
  + insights? → +1/profile
  + profile_scoring? → +1/profile
  + high_freshness? → +2/profile
  + reveal_emails? → +2/profile
  + reveal_phones? → +14/profile
```

| Type | Custo/perfil |
|------|-------------|
| `fast` | 1 |
| `balanced` (default) | 3 |
| `pro` | 5 |

#### Tratamento de Erros

| HTTP Status | Ação |
|------------|------|
| 400 | `ArgumentError` |
| 401 | Invalid key |
| 429 | Rate limit |

### 13.3 Pearch::CreditsService

**Arquivo:** `app/services/pearch/credits_service.rb`

Gerencia saldo de créditos Pearch na `Account`.

| Método | Descrição |
|--------|-----------|
| `add_credits!(amount, reason:, ...)` | Adiciona créditos |
| `consume_credits!(amount, reason:, ...)` | Consome créditos |
| `has_sufficient_credits?(amount)` | Verifica saldo |
| `current_balance` | Saldo atual |
| `total_consumed` | Total consumido |
| `transaction_history(limit:, ...)` | Histórico de transações |
| `statistics(...)` | Estatísticas de uso |

- Operações transacionais (`ActiveRecord::Base.transaction`)
- Audit trail via `PearchCreditTransaction`
- Broadcast via ActionCable: `"search_credits_account_#{account.id}"`
- Custom error: `InsufficientCreditsError`

### 13.4 Pearch::SearchProfilesBuilder

**Arquivo:** `app/services/pearch/search_profiles_builder.rb`

```ruby
SearchProfilesBuilder.build(params) → Hash (opções para Pearch API)
```

Constrói opções da API a partir de parâmetros do controller. Mapeia:
- `has_email` / `has_phone` / `show_emails` / `show_phones`
- `custom_filters`: current_job_titles, companies, universities, study_areas, skills, languages

#### Perfis de Busca (Pearch::SearchProfiles)

| Perfil | Crédito/resultado | Tempo | Tipo |
|--------|------------------|-------|------|
| `fast` | 1 | 5s | fast |
| `balanced` | 3 | 15s | balanced |
| `premium` | 7 | 45s | pro |

### 13.5 ProcessSourcingJob

**Arquivo:** `app/jobs/process_sourcing_job.rb`  
**Classe:** `ProcessSourcingJob` (Sidekiq, retry: 3)

Processa resultados da Pearch API e cria `SourcedProfile` records.

| Método | Descrição |
|--------|-----------|
| `perform(account_id, user_id, query, result_json, params_json, sourcing_id)` | Entry point |
| `create_sourced_profiles(sourcing, results, account)` | Itera resultados |
| `create_sourced_profile(sourcing, result, account)` | Cria/atualiza um profile |
| `merge_profile_data(profile, ...)` | Merge dados se profile já existe |
| `create_new_profile(account, ...)` | Cria profile novo |
| `create_or_update_sourced_profile_sourcing(profile, sourcing, result)` | Cria join record |

#### Deduplicação

Usa `SourcedProfiles::ProfileMatchingService` para encontrar profiles existentes por:
- `external_id`
- `email`
- `phone`
- `CPF`
- `LinkedIn URL`

Se duplicata: faz merge de dados (pode upgrade de provider `"local"` → `"hybrid"`).

#### Extração de Dados

| Método | O que extrai |
|--------|-------------|
| `extract_contact(profile_data, field)` | Email/phone primário |
| `extract_all_emails(profile_data)` | Todos os emails |
| `extract_all_phones(profile_data)` | Todos os telefones |
| `extract_current_company(profile_data)` | Empresa atual |
| `extract_current_title(profile_data)` | Cargo atual |
| `build_curriculum_text(profile_data, result)` | Texto do currículo |
| `find_current_experience(profile_data)` | Experiência mais recente |

---

## 14. Busca de Candidatos Similares

Sistema separado para encontrar candidatos similares a um ou mais candidatos base.

### 14.1 SimilarCandidatesSearchService

**Arquivo:** `app/services/candidates/similar_candidates_search_service.rb`

```ruby
call(candidate_ids:, job_id:, limit:, threshold:, exclude_ids:, sources:, pearch_options:, skip_cache:)
```

**Fluxo:** `validate_params!` → `load_base_candidates` → `find_cached_sourcing` → `search_local` (embedding) e/ou `search_global` (Pearch) → `create_sourcing` → `process_results` → `build_response`

### 14.2 SimilarCandidates::HybridSearchService

**Arquivo:** `app/services/candidates/similar_candidates/hybrid_search_service.rb`

```ruby
search(embedding:, intent_result:, exclude_ids:, limit:, threshold:) → results
```

Vector search via pgvector → se text search aplicável, fuse com `RankFusionService`.

### 14.3 SimilarCandidates::RankFusionService

**Arquivo:** `app/services/candidates/similar_candidates/rank_fusion_service.rb`

```ruby
fuse(vector_results:, text_results:, limit:) → fused results
```

RRF com K=60, `vector_weight=0.6`, `text_weight=0.4`. Interleava garantindo 30% mínimo de resultados de texto.

### 14.4 SimilarCandidates::GlobalSearchStrategy

**Arquivo:** `app/services/candidates/similar_candidates/global_search_strategy.rb`

Sintetiza perfil dos candidatos base → constrói params Pearch → valida créditos → chama `Pearch::SearchService` → normaliza resultados.

### 14.5 SimilarCandidates::EmbeddingRefinementService

**Arquivo:** `app/services/candidates/similar_candidates/embedding_refinement_service.rb`

```ruby
refine(liked_ids:, disliked_ids:) → refined embedding
```

Refinamento estilo **Rocchio**: ajusta centróide em direção aos "liked" (α=0.3) e afasta dos "disliked" (β=0.2), normaliza resultado.

---

## 15. AI Analysis & Enrichment

### 15.1 SourcedProfiles::AiAnalysisJob

**Arquivo:** `app/jobs/sourced_profiles/ai_analysis_job.rb`  
**Queue:** `:ai_analysis`

Enfileirado automaticamente via **`SourcedProfileSourcing` after_commit** ao criar.

| Método | Descrição |
|--------|-----------|
| `perform(account_id, sourced_profile_id, sourcing_id)` | Entry point |
| `enrich_profile_with_ai_data(sps)` | Enriquece com dados AI |
| `handle_success(sps, profile, result)` | Atualiza score + analysis + ai_metadata |
| `broadcast_profile_analyzed(...)` | WebSocket: `profile_analyzed` |
| `update_sourcing_progress(sourcing)` | Calcula % e broadcast `sourcing_progress` |

**Usa:**
- `SourcedProfiles::ProfileAnalyzer` — analisa profile contra query do sourcing
- `SourcedProfiles::AiEnrichmentService` — popula skills/expertise

**Pula:** Se não tem `curriculum_text` ou em ambiente de teste.

### 15.2 SourcedProfiles::CandidateEnrichmentService

**Arquivo:** `app/services/sourced_profiles/candidate_enrichment_service.rb`

Enriquece `SourcedProfile` com dados de um `Candidate` local.

| Área | O que enriquece |
|------|----------------|
| Contato | Nome, telefone |
| Posição | Cargo atual, empresa, senioridade inferida |
| Experiência | `experiences_data` estruturado |
| Educação | `educations_data` estruturado |
| Skills | `skills_data` da associação |
| Idiomas | `languages_data` |
| Currículo | `curriculum_text` (gera se ausente/curto <500 chars) |

**Inferência de senioridade:** 0-2yr=junior, 3-5=mid, 6-9=senior, 10+=lead

---

## 16. WebSocket — SourcingChannel

**Arquivo:** `app/channels/sourcing_channel.rb`

```ruby
stream_from "#{current_user.id}_sourcing_#{params[:sourcing_id]}"
```

### Eventos Broadcast

| Evento | Origem | Quando |
|--------|--------|--------|
| `sourcing_started` | TalentSearchJob / LocalSearchJob | Início da busca |
| `sourcing_completed` | TalentSearchJob / LocalSearchJob | Busca finalizada |
| `sourcing_failed` | TalentSearchJob / LocalSearchJob | Erro na busca |
| `sourcing_profiles_found` | LocalSearchJob / ProcessSourcingJob | Perfis iniciais encontrados |
| `profiles_processing_started` | LocalSearchJob / ProcessSourcingJob | Início do processamento |
| `profiles_processing_completed` | LocalSearchJob / ProcessSourcingJob | Processamento finalizado |
| `profiles_created` | ProcessSourcingJob | Perfis criados (global) |
| `global_profiles_created` | ProcessSourcingJob | Perfis globais criados |
| `profile_analyzed` | AiAnalysisJob | Profile analisado pela AI (com dados serializados) |
| `sourcing_progress` | AiAnalysisJob | % de progresso da análise |
| `profile_skipped` | AiAnalysisJob | Profile pulado |
| `sourcing_fully_completed` | AiAnalysisJob | Sourcing 100% completo |

---

## 17. Suggestion Service (Copilot)

**Arquivo:** `app/services/candidates/suggestion_service.rb`  
**Classe:** `Candidates::SuggestionService`  
**LLM:** Gemini (`gemini-2.0-flash`)

"Copilot" de busca que auxilia na construção de queries.

| Método | Input | Output |
|--------|-------|--------|
| `call(text)` | Texto parcial | `{suggestion: String, attributes: Hash}` |
| `generate_query_from_files(extracted_text)` | Texto de CV/JD | Query otimizada |
| `generate_query_from_boolean_search(boolean_query)` | Query booleana | Atributos estruturados |
| `suggest_role_names(role_names_text)` | Nomes de cargos | 5-10 cargos relacionados |
| `generate_query_from_filters(filters)` | Hash de filtros | Query em linguagem natural |
| `generate_concise_query_from_job(job)` | Record Job | Query concisa (≤15 palavras) |

**Attributes extraídos:** `role_name`, `experience_time`, `location`, `sector`, `skills`, `quality_score` (0-100)

---

## 18. Conversão SourcedProfile → Candidate

**Arquivo:** `app/services/sourced_profiles/convert_to_candidate_service.rb`  
**Classe:** `SourcedProfiles::ConvertToCandidateService`

Quando um SourcedProfile é movido para uma vaga (apply), precisa ser convertido em Candidate.

```ruby
ConvertToCandidateService.call(sourced_profile_ids) → {success:, converted:, skipped:, failed:, errors:}
```

### Fluxo

1. Para cada `sourced_profile_id`:
   - Se account tem `ats_provider` e profile não tem email → **descobre email via Pearch** (`Pearch::ContactEnrichmentService`)
   - Busca candidate existente por email/CPF/LinkedIn
   - Se não encontrou → cria novo `Candidate`
   - Cria skills, educations, experiences, languages
   - Atualiza `sourced_profile.candidate_id`
2. Sync pending applies para ATS (`AtsSync::ProcessApplyWithEnrichmentJob`)

### Jobs que Disparam Conversão

| Job/Controller | Contexto |
|---------------|----------|
| `AppliesController#create` | Ao criar apply de um SPS |
| `CreateCollectionJob` | Ao criar collection de applies |
| `CreateCollectionFromListJob` | Ao criar applies de uma lista |
| `AddAppliesFromListJob` | Ao adicionar applies de lista |
| `ListRelationshipJob` | Ao manipular relacionamentos de lista |

---

## 19. Tabela de Referência: Todos os Arquivos

### Controllers

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/controllers/v1/users/sourcings_controller.rb` | API de sourcings (CRUD + busca) |
| `app/controllers/concerns/ats_syncable.rb` | Concern de sync ATS |

### Models

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/models/sourcing.rb` | Registro de uma busca |
| `app/models/sourced_profile.rb` | Perfil encontrado |
| `app/models/sourced_profile_sourcing.rb` | Join: perfil ↔ busca (com score/analysis) |
| `app/models/sourcing_filter.rb` | Preset de filtros salvos |

### Jobs — Busca Local

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/jobs/candidates/local_search_job.rb` | Orquestra busca local (filtros + HybridSearchService) |
| `app/jobs/search_archetypes/local_search_job.rb` | Busca via archetype (template pré-configurado) |

### Jobs — Busca Global

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/jobs/pearch/talent_search_job.rb` | Orquestra busca global (Pearch API) |
| `app/jobs/process_sourcing_job.rb` | Cria SourcedProfiles dos resultados Pearch |

### Jobs — AI

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/jobs/sourced_profiles/ai_analysis_job.rb` | Análise e scoring AI de perfis |

### Services — Core da Busca

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/candidates/search/hybrid_search_service.rb` | **CORE** — orquestra ES + embeddings |
| `app/services/candidates/search/elasticsearch_strategy.rb` | Busca full-text (Searchkick) |
| `app/services/candidates/search/embedding_strategy.rb` | Busca semântica (pgvector) |
| `app/services/candidates/search/weighted_rank_fusion.rb` | Reciprocal Rank Fusion |
| `app/services/candidates/search/reranker.rb` | Reranking por qualidade |
| `app/services/candidates/search/adaptive_pool.rb` | Pool sizing dinâmico |

### Services — Análise de Query

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/candidates/search/simple_query_detector.rb` | Classifica tipo da query |
| `app/services/candidates/search/query_analyzer.rb` | Análise LLM da query (complex) |
| `app/services/candidates/search/hyde_query_expander.rb` | HyDE — CV hipotético (complex) |
| `app/services/candidates/search/hyde_document_generator.rb` | Gerador de documentos HyDE (resume/JD) |
| `app/services/candidates/search/profile_extractor.rb` | Extração de perfil de CVs (resume) |
| `app/services/candidates/search/multi_query_generator.rb` | Multi-query para CVs (resume) |
| `app/services/candidates/search/job_description_processor.rb` | Processamento de JDs |

### Services — Infraestrutura

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/candidates/search/configuration.rb` | Constantes e configurações |
| `app/services/candidates/search/base_filters.rb` | Filtros base (account_id, is_deleted) |
| `app/services/candidates/search/filter_merger.rb` | Merge de filtros base + user |
| `app/services/candidates/search/embedding_cache.rb` | Cache de embeddings (DB) |
| `app/services/candidates/search/query_embedding_cache.rb` | Cache de embeddings (Redis) |
| `app/services/candidates/search/embedding_service.rb` | Geração de embeddings (Gemini) |
| `app/services/candidates/search/search_telemetry.rb` | Telemetria de busca |
| `app/services/candidates/search/search_explainer.rb` | Explicação detalhada |

### Services — Pearch (Global)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/pearch/search_service.rb` | Cliente API Pearch |
| `app/services/pearch/credits_service.rb` | Gerenciamento de créditos |
| `app/services/pearch/search_profiles.rb` | Definições de perfis de busca |
| `app/services/pearch/search_profiles_builder.rb` | Builder de opções da API |
| `app/services/pearch/contact_enrichment_service.rb` | Enriquecimento de contatos |

### Services — Enfileiramento / Execução

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/sourcings/job_enqueuer_service.rb` | Roteador assíncrono (local/global) |
| `app/services/sourcings/search_executor_service.rb` | Executor síncrono (local/global) |

### Services — Candidatos Similares

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/candidates/similar_candidates_search_service.rb` | Orquestrador de busca similar |
| `app/services/candidates/similar_candidates/hybrid_search_service.rb` | Busca híbrida de similares |
| `app/services/candidates/similar_candidates/rank_fusion_service.rb` | RRF para similares |
| `app/services/candidates/similar_candidates/global_search_strategy.rb` | Busca global de similares |
| `app/services/candidates/similar_candidates/embedding_refinement_service.rb` | Refinamento Rocchio |

### Services — AI & Enrichment

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/services/sourced_profiles/candidate_enrichment_service.rb` | Enriquecimento de profile com dados de candidate |
| `app/services/sourced_profiles/convert_to_candidate_service.rb` | Conversão SourcedProfile → Candidate |
| `app/services/sourced_profiles/profile_matching_service.rb` | Deduplicação de profiles |
| `app/services/candidates/suggestion_service.rb` | Copilot de busca (LLM) |

### Channels

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/channels/sourcing_channel.rb` | WebSocket para progresso em tempo real |
