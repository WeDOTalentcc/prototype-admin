# Theme: I11 — RAG / Semantic Search / Embeddings — Infrastructure Layer

## O que é este tema

O subsistema RAG do LIA cobre **retrieval-augmented generation** em dois sentidos complementares:

1. **Busca de candidatos híbrida** (`RAGPipelineService`): combina pgvector (cosine similarity) + tsvector PostgreSQL (BM25-like) com blending via `alpha`, FairnessGuard integrado em duas fases (pre-query + post-ranking), WRF reranking e LLM classification opcional.

2. **Augmentação de contexto conversacional** (`RAGService`): injeta histórico de conversa + mensagens similares + knowledge base no prompt antes do LLM.

Infraestrutura de suporte:
- `EmbeddingService`: geração de embeddings com cache LRU in-memory + EmbeddingProviderFactory (OpenAI/Gemini)
- `ChunkingStrategyFactory`: 4 estratégias de chunking (sliding_window, section_aware, semantic, recursive)
- `SemanticSearchService`: expansão semântica de queries de busca avançada (skills, cargos, indústrias)
- `VectorSemanticCache`: cache de roteamento pgvector (reduz 40-60% de chamadas LLM)
- `SemanticCache`: cache hash MD5 Redis para roteamento (camada hash antes do vector cache)
- `CacheStrategy`: single source of truth para todos os TTLs e invalidation rules do sistema
- `RAGASEvaluationService`: avaliação contínua de qualidade (faithfulness, relevancy, precision, recall)

Este tema não inclui as tabelas de banco ou migrações (ver I9), nem os agentes que consomem RAGService (ver I1/I3).

---

## Arquivos conectados (11 total)

### Camada Código (11 arquivos Python)

| Arquivo | Path Canônico | Responsabilidade |
|---------|---------------|------------------|
| `rag_service.py` | `app/domains/ai/services/rag_service.py` | RAG conversacional: histórico + similar + knowledge base |
| `rag_pipeline_service.py` | `app/domains/ai/services/rag_pipeline_service.py` | Busca híbrida de candidatos: BM25 + pgvector + FairnessGuard |
| `ragas_evaluation_service.py` | `app/domains/ai/services/ragas_evaluation_service.py` | Avaliação de qualidade RAGAS: 4 métricas, threshold 0.70 |
| `embedding_service.py` | `app/shared/intelligence/embedding_service.py` | Geração de embeddings: LRU cache + EmbeddingProviderFactory |
| `semantic_search_service.py` | `app/shared/intelligence/semantic_search_service.py` | Expansão semântica de queries: 7 domínios, Redis TTL 10min |
| `chunking/` | `app/shared/intelligence/chunking/` | 4 estratégias de chunking (base, factory, sliding_window, section_aware, semantic, recursive) |
| `smart_extractor.py` | `app/shared/intelligence/smart_extractor.py` | Extração de parâmetros estruturados de queries em linguagem natural |
| `vector_semantic_cache.py` | `app/orchestrator/vector_semantic_cache.py` | Cache semântico pgvector para roteamento (threshold 0.85) |
| `semantic_cache.py` | `app/orchestrator/semantic_cache.py` | Cache hash MD5 Redis para roteamento (TTL 3600s) |
| `rag_search.py` | `app/api/v1/rag_search.py` | Endpoint `GET /api/v1/candidates/rag-search` |
| `cache_strategy.py` | `app/shared/cache_strategy.py` | SSoT de toda configuração de cache (TTLs + invalidation rules) |

### Integration points

- **I9 Data Layer**: `pgvector` extensão em PostgreSQL; tabelas `routing_cache_vectors` (migration 028) + `candidates.embedding` column; `tsvector` index em candidates
- **I4 LLM Providers**: `EmbeddingProviderFactory` usa mesma fábrica de providers; `get_provider_for_tenant()` em SemanticSearchService
- **C1 Fairness**: `FairnessGuard` chamado 2× em `RAGPipelineService` (pre-query + post-ranking); `bias_audit_service.audit_ranking_results()` para FAR-5
- **I5 Observability**: `@trace_span` em todos os métodos de EmbeddingService; spans por fase do pipeline RAG
- **I3 Orchestration**: `SemanticCache` (hash) + `VectorSemanticCache` (pgvector) são Tier 1 do CascadedRouter

---

## Lógica IN → OUT

### RAGPipelineService — pipeline completo

```
Input: query (str) + company_id + alpha + job_info + sector
    │
    ▼
[1] FairnessGuard PRE-QUERY (FAR-2)
    │   - FairnessGuard().check(query)
    │   - Se bloqueado → RAGSearchResult(source="blocked", fairness_ok=False)
    ▼
[2] _detect_query_type(query) → auto-alpha
    │   - tech/cargo keywords → alpha=0.3 (BM25 dominante)
    │   - behavioral keywords → alpha=0.7 (semântico dominante)
    │   - padrão → alpha=0.5
    ▼
[3] BM25 Search (if alpha < 1.0)
    │   - SQL: plainto_tsquery('portuguese') + ts_rank
    │   - Filtra por company_id (multi-tenant)
    │   - Retorna: id, name, summary, skills, title, bm25_score
    ▼
[4] Semantic Search (if alpha > 0.0)
    │   - generate_embedding(query):
    │       1. EmbeddingCacheService Redis hit
    │       2. EmbeddingProviderFactory.embed_with_fallback()
    │       3. Fallback EmbeddingService Gemini
    │       4. None → degrada para BM25 only
    │   - SQL: 1-(embedding<=>:vec::vector) >= 0.75
    │   - Filtra por company_id (multi-tenant)
    │   - Retorna: id, name, summary, skills, title, semantic_score
    ▼
[5] Hybrid Blending
    │   - _normalize() scores de cada fonte
    │   - hybrid_score = alpha × semantic + (1-alpha) × bm25
    │   - source: "bm25" | "semantic" | "hybrid"
    ▼
[6] WRF Reranking (optional, graceful)
    │   - WRFDynamicKService.rank_candidates()
    │   - Skipped se import falhar (fail gracefully)
    ▼
[7] LLM Classification (optional — requires job_title)
    │   - LLMJobClassificationService.filter_candidates()
    │   - Only if len(merged) > 3 AND job_title provided
    │   - Skipped se import falhar (fail gracefully)
    ▼
[8] FairnessGuard POST-RANKING
    │   - _check_fairness(merged, top_n=10)
    │   - Regra: nenhum gênero > 70% no top-10
    │   - FairnessGuard().check_with_sector() para análise sectorial (se sector param)
    ▼
[9] FAR-5 Bias Audit (Real-time)
    │   - bias_audit_service.audit_ranking_results(dimension="gender", top_n=10)
    │   - Loga WARNING se fairness_ok=False
    ▼
Output: RAGSearchResult{results, query, total, source, fairness_ok, search_time_ms, metadata}
```

### RAGService — RAG conversacional

```
Input: query + session_id + company_id + system_prompt
    │
    ▼
[1] store_message(role="user") → memory_service
    ▼
[2] augment_with_context():
    │   - conversation_history: get_conversation_context(limit=10)
    │   - similar_messages: search_similar_messages(min_similarity=0.7)
    │     → filtra mensagens da sessão atual (cross-session only)
    │   - knowledge_docs: search_knowledge_base(min_similarity=0.6)
    ▼
[3] _format_context():
    │   Section 1: "## Relevant Knowledge:" (knowledge_docs[:N])
    │   Section 2: "## Related Past Conversations:" (similar_messages[:3], truncated 500 chars)
    │   Section 3: "## Current Conversation:" (history[-5:])
    ▼
[4] augmented_prompt = system_prompt + context + query
    ▼
[5] llm_service.generate(prompt, provider)
    ▼
[6] store_message(role="assistant") → memory_service
    ▼
Output: {response, context_used{history_count, similar_count, docs_count}, session_id}
```

---

## EmbeddingService — Detalhes

**Arquivo:** `app/shared/intelligence/embedding_service.py`

```python
EMBEDDING_DIMENSION = 768        # Gemini default; OpenAI text-embedding-3-small = 1536
_EMBEDDING_CACHE_SIZE = 512      # env: EMBEDDING_CACHE_SIZE (default 512)

class EmbeddingService:
    def __init__(self):
        self._cache: OrderedDict[str, list[float]] = OrderedDict()  # LRU in-memory
        self._cache_max = _EMBEDDING_CACHE_SIZE
```

### Cache key strategy

```python
@staticmethod
def _cache_key(text: str, provider: str | None) -> str:
    h = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:24]
    return f"{provider or 'default'}:{h}"
```

### LRU eviction

```python
def _cache_put(self, key: str, vector: list[float]) -> None:
    self._cache[key] = vector
    self._cache.move_to_end(key)
    while len(self._cache) > self._cache_max:
        self._cache.popitem(last=False)  # remove oldest
```

### Provider delegation

```python
# Todos os métodos delegam para EmbeddingProviderFactory
vector, provider_name, model = await EmbeddingProviderFactory.embed_with_fallback(
    text=text,
    preferred_provider=provider,  # None = default (EMBEDDING_DEFAULT_PROVIDER env var)
)
```

### Métodos públicos

| Método | Retorno | Uso |
|--------|---------|-----|
| `generate_embedding(text, provider)` | `list[float]` | Candidato único |
| `generate_embedding_with_metadata(text)` | `(vector, provider_name, model)` | Grava em job_embeddings table |
| `generate_batch_embeddings(texts)` | `list[list[float]]` | Indexação em lote |
| `generate_batch_embeddings_with_metadata(texts)` | `(vectors, provider, model)` | Batch com auditoria |
| `chunk_text(text, chunk_size, overlap, document_type, strategy_override)` | `list[str]` | Prepara texto para embedding |

### Empty text handling

```python
if not text or not text.strip():
    default_prov = EmbeddingProviderFactory.get_default()
    return [0.0] * default_prov.dimensions  # zero vector, não quebra
```

---

## Chunking Strategies

**Diretório:** `app/shared/intelligence/chunking/`

### Strategy resolution (ChunkingStrategyFactory)

```python
# Ordem de prioridade:
# 1. override (parâmetro explícito)
# 2. CHUNKING_STRATEGY env var (feature flag global)
# 3. document_type default (todos → "recursive")

_DEFAULT_DOC_TYPE_STRATEGY: dict[str, str] = {
    DocumentType.CV:               "recursive",
    DocumentType.JOB_DESCRIPTION:  "recursive",
    DocumentType.POLICY:           "recursive",
    DocumentType.GENERIC:          "recursive",
}
```

### 4 estratégias

| Estratégia | Classe | Melhor para |
|------------|--------|-------------|
| `sliding_window` | `SlidingWindowChunker` | Textos homogêneos, overlap fixo |
| `section_aware` | `SectionAwareChunker` | CVs e JDs com headers/seções |
| `semantic` | `SemanticChunker` | Agrupamento por similaridade semântica |
| `recursive` | `RecursiveTextSplitter` | Default — mais robusto para textos mistos |

### Configuração por tipo (settings)

```
CHUNKING_CV_CHUNK_SIZE / CHUNKING_CV_OVERLAP
CHUNKING_JD_CHUNK_SIZE / CHUNKING_JD_OVERLAP
CHUNKING_POLICY_CHUNK_SIZE / CHUNKING_POLICY_OVERLAP
CHUNKING_GENERIC_CHUNK_SIZE / CHUNKING_GENERIC_OVERLAP
```

Default (hardcoded fallback): `chunk_size=1000, overlap=100`

### Base classes

```python
class DocumentType(str, enum.Enum):
    CV = "cv"
    JOB_DESCRIPTION = "job_description"
    POLICY = "policy"
    GENERIC = "generic"

@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict = field(default_factory=dict)

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, **kwargs) -> list[Chunk]: ...
    
    @property
    @abstractmethod
    def strategy_name(self) -> str: ...
```

---

## VectorSemanticCache — Cache pgvector para roteamento

**Arquivo:** `app/orchestrator/vector_semantic_cache.py`

### Threshold e embeddings

```python
# Threshold default: settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD (fallback 0.85)
# Provider primário: OpenAI text-embedding-3-small (1536 dims)
# Fallback: Gemini text-embedding-004 (768 dims)

class VectorSemanticCache:
    def __init__(self, similarity_threshold=None, embedding_model=_EMBED_MODEL_OPENAI):
        if similarity_threshold is None:
            similarity_threshold = settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD
        self.threshold = similarity_threshold
```

### Fluxo de busca

```python
# get(message) → dict | None
# 1. EmbeddingCacheService.get_embedding(text, model)  ← Redis cache de embedding
# 2. Se cache miss → EmbeddingProviderFactory.embed_with_fallback() → cache
# 3. pgvector query: 1-(embedding <=> vec) >= threshold
# 4. Near-miss log se melhor sim >= (threshold - 0.05)
# 5. UPDATE hit_count+1 + last_hit_at = NOW() on hit
# 6. Retorna {domain_id, confidence, source, cache_source="vector_cache"}
```

### SQL de busca

```sql
-- Busca por cosine similarity >= threshold
SELECT id, domain_id, confidence, source, hit_count
FROM routing_cache_vectors
WHERE 1 - (message_embedding <=> :embedding::vector) >= :threshold
ORDER BY message_embedding <=> :embedding::vector
LIMIT 1;

-- Insert com ON CONFLICT DO NOTHING (idempotente)
INSERT INTO routing_cache_vectors
    (message_text, message_embedding, domain_id, confidence, source)
VALUES (:message_text, :embedding::vector, :domain_id, :confidence, :source)
ON CONFLICT DO NOTHING;
```

### Near-miss logging (Z5-03)

```python
# Loga quando melhor match < threshold mas > (threshold - near_margin)
# Env: ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN (default 0.05)
# Mensagem: "melhor_sim=X threshold=Y domain=Z — considere reduzir ROUTER_VECTOR_SIMILARITY_THRESHOLD"
```

**Fail-safe:** qualquer exceção → retorna `None` sem propagar.

---

## SemanticCache — Cache hash MD5 para roteamento

**Arquivo:** `app/orchestrator/semantic_cache.py`

```python
# Camada anterior ao VectorSemanticCache (hash exato vs fuzzy vector)
# TTL: settings.ROUTER_CACHE_TTL (default 3600s)

def _cache_key(message: str) -> str:
    normalized = message.lower().strip()
    return f"route_cache:{hashlib.md5(normalized.encode()).hexdigest()}"

class SemanticCache:
    async def get(self, message: str) -> dict | None: ...
    async def set(self, message: str, result: dict) -> None: ...
    async def invalidate(self, message: str) -> None: ...
    async def flush_all(self, pattern: str = "route_cache:*") -> int: ...
```

**Diferença de VectorSemanticCache:**
- Hash: "criar vaga dev" e "cria vaga pra dev" → **MISS** (strings diferentes)
- Vector: "criar vaga dev" e "cria vaga pra dev" → **HIT** (cosine_sim ≈ 0.97)

Posição no cascade: Tier 1 hash → Tier 2 vector → Tier 3+ LLM.

---

## SemanticSearchService — Expansão de queries

**Arquivo:** `app/shared/intelligence/semantic_search_service.py`

### 7 domínios de busca

```python
class SemanticDomain(StrEnum):
    SKILLS = "skills"
    JOB_TITLES = "job_titles"
    ROLES = "roles"
    INDUSTRIES = "industries"
    EXPERTISE = "expertise"
    FIELDS_OF_STUDY = "fields_of_study"
    COMPANIES = "companies"
```

### Resultado

```python
class SemanticSuggestion(BaseModel):
    term: str
    confidence: float         # 0.0 a 1.0
    is_synonym: bool = False
    is_related: bool = False
    is_broader: bool = False
    is_narrower: bool = False

class SemanticExpansionResult(BaseModel):
    original_query: str
    domain: SemanticDomain
    suggestions: list[SemanticSuggestion]  # max 10, ordered by confidence
    cached: bool = False
    processing_time_ms: int = 0
```

### Fluxo: LLM first, taxonomy fallback

```python
async def expand_query(domain, query, existing=[], use_cache=True):
    # 1. Validação (len >= 2)
    # 2. Redis cache hit → retorna imediato
    # 3. LLM via get_provider_for_tenant() com DOMAIN_PROMPTS[domain]
    #    → JSON array com term/confidence/is_synonym/...
    # 4. Se LLM falhar → _get_taxonomy_suggestions() (SKILLS/INDUSTRIES/JOB_TITLES taxonomy)
    # 5. Filtrar existing terms (case-insensitive)
    # 6. Sort by confidence DESC, max 10
    # 7. Cache no Redis se suggestions não vazio
```

### Cache key

```python
def _get_cache_key(self, domain, query, existing):
    content = f"{domain.value}:{query.lower().strip()}:{sorted(existing)}"
    return f"semantic:{hashlib.md5(content.encode()).hexdigest()}"
# TTL: 600s (10 min)
```

### Taxonomias estáticas (fallback)

- `SKILLS_TAXONOMY`: Frontend, Backend, Database, Cloud, Data, AI/ML
- `INDUSTRY_TAXONOMY`: Technology, Fintech, E-commerce, Healthcare, Education, HR Tech
- `JOB_TITLES_TAXONOMY`: 14 categorias (gerente, desenvolvedor, engineer, analista, designer, product, data, marketing, vendas, diretor, coordenador, senior, lead, head)

### Métodos de conveniência

```python
expand_skills(query, existing)
expand_job_titles(query, existing)
expand_roles(query, existing)
expand_industries(query, existing)
expand_expertise(query, existing)
expand_fields_of_study(query, existing)
expand_company_competitors(query, existing)
```

---

## CacheStrategy — SSoT de configuração de cache

**Arquivo:** `app/shared/cache_strategy.py`

### CacheDomain StrEnum

```python
class CacheDomain(StrEnum):
    CANDIDATE_SEARCH    # ttl=300s, invalidate_on=[candidate_update, candidate_create]
    CANDIDATE_PROFILE   # ttl=600s
    JOB_VACANCY         # ttl=300s, invalidate_on=[job_update, job_create, job_close]
    JOB_DESCRIPTION     # ttl=1800s (30 min)
    WSI_SCORE           # ttl=3600s (1h)
    PIPELINE_STAGES     # ttl=1800s
    COMPANY_CONFIG      # ttl=3600s
    SKILL_CATALOG       # ttl=86400s (24h)
    LLM_RESPONSE        # ttl=900s (15 min)
    TEMPLATE            # ttl=86400s
    ANALYTICS           # ttl=...
    ROUTING             # ttl=...
```

### Uso

```python
from app.shared.cache_strategy import CacheStrategy, CacheDomain

ttl = CacheStrategy.get_ttl(CacheDomain.CANDIDATE_SEARCH)       # 300
key = CacheStrategy.build_key(CacheDomain.CANDIDATE_SEARCH, query="python")
CacheStrategy.invalidate(CacheDomain.JOB_VACANCY, job_id="123")
```

**Regra:** Nenhum outro módulo define TTLs ou invalidation rules — sempre via `CacheStrategy`.

---

## RAGASEvaluationService — Qualidade contínua

**Arquivo:** `app/domains/ai/services/ragas_evaluation_service.py`

### 4 métricas RAGAS

| Métrica | Definição |
|---------|-----------|
| `faithfulness` | Resposta factualmente alinhada com o contexto fornecido |
| `answer_relevancy` | Resposta relevante para a pergunta |
| `context_precision` | Contexto fornecido é preciso para a pergunta |
| `context_recall` | Contexto recuperado cobre as informações necessárias |

### Threshold e armazenamento

```python
RAGAS_QUALITY_THRESHOLD = 0.70   # WARNING no log se overall_score < 0.70

@property
def passed_threshold(self) -> bool:
    if self.overall_score is None:
        return True  # fail-safe: não penalizar por ausência de score
    return self.overall_score >= RAGAS_QUALITY_THRESHOLD
```

- **Tabela:** `agent_ragas_evaluations`
- **Retenção:** 90 dias
- **Celery task:** `ragas.evaluate_batch` — diariamente às 03h UTC

**Fail-safe:** falha na avaliação RAGAS **não afeta** o funcionamento dos agentes.

---

## Endpoint RAG Search

**Arquivo:** `app/api/v1/rag_search.py`

```
GET /api/v1/candidates/rag-search
```

### Query parameters

| Param | Type | Default | Descrição |
|-------|------|---------|-----------|
| `q` | str | required | Query em linguagem natural |
| `company_id` | str | required | Tenant ID (multi-tenant scope) |
| `limit` | int | 20 | 1-100 resultados |
| `alpha` | float | 0.5 | 0=BM25, 1=semântico, 0.5=híbrido |
| `job_title` | str | "" | Para LLM classification |
| `job_area` | str | "" | Para LLM classification |
| `job_requirements` | str | "" | Para LLM classification |
| `sector` | str | "" | Para FairnessGuard L3 sector-aware |

### Response: RAGSearchResponse

```json
{
  "results": [...],
  "query": "desenvolvedor Python AWS",
  "total": 15,
  "source": "hybrid",
  "fairness_ok": true,
  "search_time_ms": 245.3,
  "metadata": {
    "alpha": 0.3,
    "bm25_count": 12,
    "semantic_count": 8,
    "embedding_available": true,
    "semantic_threshold": 0.75,
    "ranking_audit": {...},
    "llm_classification_applied": false
  }
}
```

---

## Pipeline Pre-WRF — Filtros de Qualidade Antes do Ranking Final

O pipeline Pre-WRF roda **antes do Weighted Rank Fusion** final para eliminar candidatos tecnicamente abaixo do threshold de qualificação, evitando que o WRF dilua o ranking com candidatos fracos. O pipeline é paramétrico por `qualification_level` ("alta"/"media"/"baixa").

### Serviços (4 arquivos)

| Serviço | Arquivo | Responsabilidade |
|---------|---------|-----------------|
| `PreWRFFilterService` (WDT-015) | `app/domains/cv_screening/services/pre_wrf_filter_service.py` | Orquestra os 3 serviços abaixo em sequência |
| `EsScoreDropAnalyzer` (WDT-011) | `app/shared/services/es_score_drop_analyzer.py` | Detecta quedas de score ES (Elasticsearch) |
| `PgvGapAnalyzer` (WDT-012) | `app/shared/services/pgv_gap_analyzer.py` | Detecta gaps de distância semântica pgvector |
| `WRFDynamicKService` (WDT-014) | `app/shared/services/wrf_dynamic_k_service.py` | WRF com K dinâmico adaptativo |

### Fluxo de execução

```python
# PreWRFFilterService.orchestrate(es_candidates, pgv_candidates, qualification_level):
1. EsScoreDropAnalyzer.analyze(es_candidates, level)
       → corta candidatos onde score_drop > DROP_THRESHOLD[level] ou gap estatístico
2. PgvGapAnalyzer.analyze(pgv_candidates, level)
       → corta candidatos onde gap de distância > mean_gap + GAP_MULTIPLIER[level] * std_gap
3. UNION de IDs sobreviventes dos passos 1 e 2
       → merged candidate_map (ES + pgv_distance/pgv_rank)
4. WRFDynamicKService.rank_candidates(survivors, level)
       → WRF score final + K adaptativo + pesos por level

# Output: {"candidates": wrf_ranked, "pipeline_log": {...}, "es_analysis": ..., "pgv_analysis": ...}
```

### Thresholds por `qualification_level`

**`EsScoreDropAnalyzer` — DROP_THRESHOLDS:**
```python
DROP_THRESHOLDS = {"alta": 0.40, "media": 0.55, "baixa": 0.70}
# Corta candidatos com queda > threshold% do score máximo
# Ou onde gap inter-score > mean + 2σ (estatístico — prevalece se anterior)
```

**`PgvGapAnalyzer` — GAP_MULTIPLIERS:**
```python
GAP_MULTIPLIERS = {"alta": 1.5, "media": 2.0, "baixa": 2.5}
# Corta candidatos onde gap_from_prev > mean_gap + multiplier * std_gap
```

**`WRFDynamicKService` — DEFAULT_K_VALUES e SCORE_WEIGHTS:**
```python
DEFAULT_K_VALUES = {"alta": 25, "media": 45, "baixa": 70}
# K configurável via env vars: WRF_K_ALTA, WRF_K_MEDIA, WRF_K_BAIXA
# K adaptativo (WRF_ADAPTIVE_K=true): 
#   if top_quartile_avg >= 0.75 → K *= 0.7 (precision mode)
#   if score_spread <= 0.35     → K *= 1.4 (recall mode)
#   if score_spread < 0.05      → K -= 10
# K bounded: [10, 100]

SCORE_WEIGHTS = {
    "alta":  {"es": 0.6, "pgv": 0.4},  # ES-heavy para alta qualificação
    "media": {"es": 0.5, "pgv": 0.5},  # balanceado
    "baixa": {"es": 0.4, "pgv": 0.6},  # PGV-heavy para baixa qualificação
}

# Fórmula WRF: weight_es * (1/(K + es_rank)) + weight_pgv * (1/(K + pgv_rank))
```

### `pipeline_log` (estrutura de saída)

```python
{
    "qualification_level": "media",
    "input": {"es_count": 120, "pgv_count": 118},
    "es_filter": {"output": 67, "cutoff_index": 67, "threshold": 0.55, "top_score": 0.92},
    "pgv_filter": {"output": 71, "gap_index": 71, "multiplier": 2.0},
    "fusion": {"survived": 89, "k_used": 42, "weights": {"es": 0.5, "pgv": 0.5}},
    "output": {"final_count": 89},
    "elapsed_seconds": 0.043
}
```

---

## Instruções para Claude Code / Cursor

### "Implementa RAG pipeline de busca de candidatos no v5"

```
1. Crie app/domains/ai/services/rag_pipeline_service.py
   - Implemente RAGPipelineService com _bm25_search() + _semantic_search()
   - BM25: plainto_tsquery('portuguese') + ts_rank
   - Semantic: pgvector operador <=> (cosine distance)
   - SEMPRE filtre por company_id (multi-tenant)
   - DEFAULT semantic_threshold = 0.75

2. Integre FairnessGuard em 2 momentos:
   - PRE-QUERY: FairnessGuard().check(query) — bloqueia discriminação na entrada
   - POST-RANKING: _check_fairness(results) — max 70% mesmo gênero no top-10

3. Crie app/api/v1/rag_search.py com GET /candidates/rag-search
   - RAGSearchResponse deve ter campo fairness_ok (auditável)

4. Para EmbeddingService:
   - LRU in-memory cache (OrderedDict, max 512 entries)
   - Cache key: sha256[:24] + provider prefix
   - Empty text → zero vector (não quebra)
   - Delegate para EmbeddingProviderFactory (ver I4)

5. Para SemanticCache + VectorSemanticCache:
   - SemanticCache: MD5 hash → Redis TTL 3600s
   - VectorSemanticCache: pgvector cosine sim >= 0.85
   - Ambos DEVEM falhar graciosamente (try/except → None)
```

### "Adiciona busca semântica expandida no v5"

```
1. Crie app/shared/intelligence/semantic_search_service.py
2. Implemente os 7 SemanticDomain values
3. Fluxo: Redis cache hit → LLM expansion → taxonomy fallback
4. Cache key: semantic:{md5(domain:query:sorted(existing))}
5. TTL: 600s (10 min)
6. Target: P95 < 300ms
```

### "Adiciona nova estratégia de chunking"

```
1. Crie app/shared/intelligence/chunking/<nome>.py
   herdando de ChunkingStrategy
2. Implemente chunk(text) → list[Chunk]
3. Defina strategy_name (str property)
4. Registre em ChunkingStrategyFactory._STRATEGY_MAP
5. Adicione ao _DEFAULT_DOC_TYPE_STRATEGY se for default para algum tipo
6. Feature flag: CHUNKING_STRATEGY=<nome> para rollout gradual
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## RAG / Embeddings
- FairnessGuard MUST be called PRE-QUERY and POST-RANKING in any candidate search
- Hybrid search: alpha controls BM25 vs pgvector blend (0=BM25, 1=semantic)
- Semantic threshold for candidate search: 0.75 (configurable)
- VectorSemanticCache threshold: settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD (default 0.85)
- Chunking default: RecursiveTextSplitter for all document types
- Override via CHUNKING_STRATEGY env var (feature flag)
- ALL cache TTLs defined in app/shared/cache_strategy.py — never hardcode TTLs
```

### Setup em Cursor rules (snippet pronto)

```
# RAG rules
- Every candidate search endpoint MUST return fairness_ok boolean
- FairnessGuard check BEFORE and AFTER candidate ranking — never skip
- Never call EmbeddingProviderFactory directly from routes; use EmbeddingService
- CacheStrategy is SSoT for TTLs — never define TTL constants outside cache_strategy.py
- pgvector queries MUST include company_id = :company_id filter (multi-tenant isolation)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|---------------|
| `alpha` parameter values | Ajustar heurísticas em `_detect_query_type()` |
| `_EMBEDDING_CACHE_SIZE` | Ajustar via env var `EMBEDDING_CACHE_SIZE` |
| `RAGAS_QUALITY_THRESHOLD` (0.70) | Pode subir para 0.80+ em produção mais madura |
| TTLs no `CacheStrategy` | Ajustar por volume de dados do v5 |
| `ROUTER_VECTOR_SIMILARITY_THRESHOLD` (0.85) | Ajustar via settings |
| Taxonomies estáticas (SKILLS/INDUSTRY/JOB_TITLES) | Expandir com domínio do v5 |
| `SemanticSearchService.cache_ttl` (600s) | Ajustar por frescor dos dados |

### NÃO pode adaptar (base legal ou arquitetural)

| Item | Motivo |
|------|--------|
| FairnessGuard PRE-QUERY | LGPD + EU AI Act — queries com atributos protegidos DEVEM ser bloqueadas |
| FairnessGuard POST-RANKING + fairness_ok no response | EU AI Act Art. 13 — transparência de decisão automatizada; `fairness_ok=false` deve ser auditável |
| `_FAIRNESS_MAX_SINGLE_GENDER_RATIO = 0.70` | 4/5 rule / disparate impact — base legal; > 80% é discriminação estatística |
| `company_id` em TODA query SQL | Multi-tenancy — RLS enforcement (ver I9) |
| Fail-graceful em VectorSemanticCache e SemanticCache | Router não pode falhar por indisponibilidade de cache — afeta SLA |
| RAGAS avaliação é Celery async (não síncrona) | Agent response latency — avaliação de qualidade NUNCA pode bloquear resposta |

---

## Checklist de completude (P0/P1/P2)

### RAGPipelineService

- [ ] (P0) FairnessGuard chamado ANTES da query (bloqueia discriminação na entrada)
- [ ] (P0) FairnessGuard chamado DEPOIS do ranking (`fairness_ok` no response)
- [ ] (P0) Todas as queries SQL filtram por `company_id` (multi-tenant)
- [ ] (P0) RAGSearchResponse inclui `fairness_ok: bool` (auditável)
- [ ] (P1) `_detect_query_type()` ajusta alpha automaticamente
- [ ] (P1) Degradação graciosa para BM25 quando embedding indisponível
- [ ] (P1) `search_time_ms` no response (SLA monitoring)
- [ ] (P2) WRF reranking configurado (fail-graceful se ausente)
- [ ] (P2) LLM classification aplicada quando job_title fornecido

### EmbeddingService

- [ ] (P0) Zero vector para texto vazio (não quebra pipeline)
- [ ] (P1) LRU cache com max 512 entries (env: EMBEDDING_CACHE_SIZE)
- [ ] (P1) `generate_embedding_with_metadata()` para registros que precisam de provedor/modelo
- [ ] (P2) `@trace_span` em todos os métodos (observability)

### Cache (Semantic + Vector)

- [ ] (P0) Ambos os caches falham graciosamente (try/except → None)
- [ ] (P1) `SemanticCache` TTL configurável via `ROUTER_CACHE_TTL`
- [ ] (P1) `VectorSemanticCache` threshold configurável via `ROUTER_VECTOR_SIMILARITY_THRESHOLD`
- [ ] (P1) Near-miss logging para ajuste de threshold (Z5-03)
- [ ] (P2) `hit_count` + `last_hit_at` atualizados no cache hit

### Chunking

- [ ] (P1) Estratégia selecionável por CHUNKING_STRATEGY env var (feature flag)
- [ ] (P1) `RecursiveTextSplitter` como default para todos os document types
- [ ] (P2) Chunk size/overlap configurável por tipo via settings
- [ ] (P2) `strategy.strategy_name` property em todas as implementações

### RAGASEvaluationService

- [ ] (P1) `RAGAS_QUALITY_THRESHOLD = 0.70` com fail-safe (None score = pass)
- [ ] (P1) Falha de avaliação NÃO afeta resposta do agente
- [ ] (P2) Celery task `ragas.evaluate_batch` configurado (03h UTC)

---

## Gotchas e erros comuns

### G1: Embedding dimension mismatch entre providers

**Problema:** OpenAI text-embedding-3-small = 1536 dims; Gemini text-embedding-004 = 768 dims. Se um candidato foi indexado com OpenAI e uma query usa Gemini, o pgvector operador `<=>` lança erro de dimensão incompatível.

**Solução:** `VectorSemanticCache` rastreia `self.embedding_model` e normaliza via `EmbeddingProviderFactory.embed_with_fallback()`. O campo `message_embedding` na tabela deve ter dimensão fixa (1536 para OpenAI, 768 para Gemini) — escolher **antes de criar a tabela** e manter consistente.

---

### G2: FairnessGuard não pode usar campo `gender` para tomada de decisão

**Problema:** `_check_fairness()` verifica `r.get("gender")` para calcular diversidade — parece contradiction com LGPD que proíbe uso de gênero em decisões IA.

**Esclarecimento:** O campo `gender` usado aqui é **contagem agregada para auditoria**, não para filtrar ou rejeitar candidatos. A função verifica se **nenhum gênero domina** (> 70%) — é uma medida de diversidade, não um critério de seleção. Se < 3 candidatos têm gender preenchido, a função retorna `True` (fail-safe).

---

### G3: alpha=0.5 é auto-ajustado

**Problema:** Dev passa `alpha=0.5` esperando blend 50/50, mas recebe resultado estranho.

**Causa:** `_detect_query_type()` sobrescreve alpha quando `alpha == 0.5` (o valor default). Queries com tech keywords → alpha=0.3; behavioral → alpha=0.7.

**Solução:** Para forçar 50/50 sem auto-ajuste, passe um valor diferente mas próximo, ex: `alpha=0.50001`, ou adapte a lógica para ter um `auto_alpha: bool` flag separado.

---

### G4: pgvector query sem índice ivfflat

**Problema:** `routing_cache_vectors` cresce para milhares de entradas; query `ORDER BY embedding <=>` sem índice vira full scan O(n).

**Solução:** Migration 028 cria índice `ivfflat` na coluna `message_embedding`. Para a tabela `candidates.embedding`, verificar se migration correspondente cria índice. Em v5, sempre criar índice `USING ivfflat (embedding vector_cosine_ops)` antes de popular a tabela.

---

### G5: SemanticCache e VectorSemanticCache na mesma sessão Redis

**Problema:** Ambos usam Redis mas com key prefixes diferentes (`route_cache:*` vs `routing_cache_vectors` no PG). `SemanticCache.flush_all()` só limpa chaves `route_cache:*`, não afeta o pgvector.

**Solução já implementada:** São camadas independentes. Limpar SemanticCache (hash) não limpa VectorSemanticCache (pgvector DB). Para limpar o vector cache, é necessário `DELETE FROM routing_cache_vectors` ou TTL explícito na tabela.

---

### G6: RAGAS evaluation bloqueia resposta se não for async

**Problema:** Se `ragas_evaluation_service.evaluate()` for chamado com `await` inline no handler, adiciona latência ao response final.

**Solução:** Sempre disparar via Celery task (`ragas.evaluate_batch`), nunca inline. O serviço tem fail-safe explícito: "falha na avaliação RAGAS não afeta o funcionamento dos agentes."

---

## Testes obrigatórios

| Teste | Path | Cenário coberto |
|-------|------|-----------------|
| BM25 search multi-tenant | `tests/integration/test_rag_pipeline.py` | Query com company_id A não retorna candidatos de company_id B |
| Semantic search multi-tenant | `tests/integration/test_rag_pipeline.py` | pgvector com company_id filter |
| FairnessGuard pre-query block | `tests/unit/test_rag_pipeline.py` | Query com atributo protegido → source="blocked", fairness_ok=False |
| FairnessGuard post-ranking gender diversity | `tests/unit/test_rag_pipeline.py` | 9/10 top candidatos mesmo gênero → fairness_ok=False |
| alpha auto-detection | `tests/unit/test_rag_pipeline.py` | "Python developer" → alpha=0.3; "liderança" → alpha=0.7 |
| Embedding cache LRU eviction | `tests/unit/test_embedding_service.py` | Inserir 513 entries → oldest evicted |
| Empty text → zero vector | `tests/unit/test_embedding_service.py` | `generate_embedding("")` → `[0.0]*768` |
| VectorSemanticCache graceful fail | `tests/unit/test_vector_cache.py` | DB indisponível → retorna None sem exceção |
| SemanticCache TTL | `tests/integration/test_semantic_cache.py` | get() após TTL → None |
| Chunking strategy resolution | `tests/unit/test_chunking_factory.py` | CHUNKING_STRATEGY=sliding_window override |
| SemanticSearchService taxonomy fallback | `tests/unit/test_semantic_search.py` | LLM falha → taxonomy retorna suggestions |
| RAGSearchResponse fairness_ok field | `tests/integration/test_rag_search_endpoint.py` | Response sempre tem fairness_ok: bool |
| RAGAS fail-safe | `tests/unit/test_ragas_evaluation.py` | RAGAS falha → passed_threshold=True, agente não afetado |

---

## Referências

- **C1 — Fairness & Anti-Discrimination** — `FairnessGuard` integrado em 2 fases do RAGPipelineService; `_FAIRNESS_MAX_SINGLE_GENDER_RATIO` = 4/5 rule
- **I4 — LLM Providers (BYOK)** — `EmbeddingProviderFactory` (OpenAI/Gemini); `get_provider_for_tenant()` em SemanticSearchService
- **I9 — Data Layer & Migrations** — Migration 028: `routing_cache_vectors` com ivfflat index; `candidates.embedding` pgvector column
- **I5 — Observability** — `@trace_span` em EmbeddingService; spans por fase no RAGPipeline
- **I3 — Orchestration** — SemanticCache + VectorSemanticCache como Tier 1 do CascadedRouter
- **I6 — API Layer** — `GET /api/v1/candidates/rag-search` documentado em `app/api/v1/rag_search.py`
- **EU AI Act Art. 13** — transparência; `fairness_ok` no response viabiliza auditoria
- **ADR-014** — Hybrid search architecture decision (ver docs/architecture/)
