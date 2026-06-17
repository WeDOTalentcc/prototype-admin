# Local Search - Arquitetura Técnica Detalhada

> **Documento Técnico**  
> **Público-alvo:** Desenvolvedores, Arquitetos de Software  
> **Última atualização:** 2026-02-01

## 📐 Diagramas de Arquitetura

### Diagrama 1: Arquitetura Completa do Sistema

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  GET /api/v1/candidates/search?query=<text>&limit=10                         │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    HybridSearchService (Orchestrator)                        │
│                                                                              │
│  initialize(account_id:, tenant:)                                            │
│    @es_strategy = ElasticsearchStrategy.new                                  │
│    @emb_strategy = EmbeddingStrategy.new                                     │
│    @embedding_cache = EmbeddingCache.new                                     │
│    @query_analyzer = QueryAnalyzer.new                                       │
│    @hyde_expander = HydeQueryExpander.new                                    │
│    @profile_extractor = ProfileExtractor.new          ◄── NOVO               │
│    @multi_query_generator = MultiQueryGenerator.new  ◄── NOVO                │
│    @hyde_generator = HydeDocumentGenerator.new       ◄── NOVO                │
│    @jd_processor = JobDescriptionProcessor.new       ◄── NOVO                │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SimpleQueryDetector                                  │
│                                                                              │
│  detect(query_text) → Symbol                                                 │
│    → :simple          (fast path, no LLM)                                    │
│    → :complex         (QueryAnalyzer + HyDE)                                 │
│    → :resume          (multi-query retrieval)  ◄── MELHORADO                 │
│    → :job_description (JD processing)          ◄── NOVO                      │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌───────────────┐  ┌────────────────┐  ┌──────────────┐
    │ :simple       │  │ :resume        │  │ :jd          │
    │ :complex      │  │                │  │              │
    │ (Original)    │  │ (Enhanced)     │  │ (New)        │
    └───────────────┘  └────────┬───────┘  └──────┬───────┘
                                │                  │
                                ▼                  ▼
                    ┌────────────────────────────────────────┐
                    │     SEARCH EXECUTION LAYER             │
                    └────────────────────────────────────────┘
```

---

### Diagrama 2: Fluxo de Resume Search (Multi-Query)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ INPUT: Resume Text (3000+ words)                                            │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Profile Extraction                                                  │
│                                                                             │
│  ProfileExtractor.extract(resume_text, source_type: :resume)               │
│                                                                             │
│  ┌────────────┐      ┌──────────────┐      ┌─────────────────┐           │
│  │ LLM Prompt │ ───► │ Gemini API   │ ───► │ JSON Response   │           │
│  │ (5000 chr) │      │ (0.2 temp)   │      │ confidence: 0.85│           │
│  └────────────┘      └──────────────┘      └─────────────────┘           │
│                               │                                             │
│                               │ Failure                                     │
│                               ▼                                             │
│                      ┌──────────────┐      ┌─────────────────┐           │
│                      │ Regex Parse  │ ───► │ confidence: 0.70│           │
│                      └──────────────┘      └─────────────────┘           │
│                               │                                             │
│                               │ Failure                                     │
│                               ▼                                             │
│                      ┌──────────────┐      ┌─────────────────┐           │
│                      │ Keyword      │ ───► │ confidence: 0.40│           │
│                      └──────────────┘      └─────────────────┘           │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         ExtractionResult {
           profile: { seniority, role, techs, skills, industry },
           confidence: 0.85,
           extraction_method: :llm,
           missing_fields: []
         }
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Multi-Query Generation                                             │
│                                                                             │
│  MultiQueryGenerator.generate(profile, context: :resume)                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ STRATEGY 1: Role-focused (weight: 0.3)                              │  │
│  │   → "senior desenvolvedor ruby"                                     │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │ STRATEGY 2: Tech-focused (weight: 0.25)                             │  │
│  │   → "Ruby Rails PostgreSQL Redis"                                   │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │ STRATEGY 3: Industry-focused (weight: 0.2)                          │  │
│  │   → "desenvolvedor ruby fintech liderança técnica"                  │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │ STRATEGY 4: Experience-focused (weight: 0.15)                       │  │
│  │   → "senior 8 anos desenvolvedor ruby"                              │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │ STRATEGY 5: Hybrid (weight: 0.1)                                    │  │
│  │   → "Ruby Rails desenvolvedor ruby"                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         MultiQueryResult {
           queries: [query1, query2, query3, query4, query5],
           weights: [0.3, 0.25, 0.2, 0.15, 0.1],
           strategy_used: :profile_based
         }
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: HyDE Document Generation (for each query)                          │
│                                                                             │
│  FOR EACH query in queries:                                                │
│    profile_mini = extract_profile_from_query(query)                        │
│    hyde_doc = HydeDocumentGenerator.generate(                              │
│      profile_mini,                                                          │
│      context: :resume,                                                      │
│      verbosity: :concise                                                    │
│    )                                                                        │
│                                                                             │
│  EXAMPLE HyDE Doc:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Profissional senior com 8 anos de experiência.                       │ │
│  │ Atuação como desenvolvedor ruby.                                     │ │
│  │ Tecnologias: Ruby, Rails, PostgreSQL, Redis.                         │ │
│  │ Competências: liderança técnica, SaaS.                               │ │
│  │ Setor: fintech.                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Multi-Embedding Search                                             │
│                                                                             │
│  FOR EACH (query, weight) in zip(queries, weights):                        │
│                                                                             │
│    ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐         │
│    │ HyDE Doc     │ ──► │ Embedding API   │ ──► │ vector[1536] │         │
│    │ (200 chars)  │     │ (text-embedding)│     │              │         │
│    └──────────────┘     └─────────────────┘     └──────┬───────┘         │
│                                                          │                  │
│                                                          ▼                  │
│                                            ┌─────────────────────────┐     │
│                                            │ EmbeddingCache.fetch()  │     │
│                                            │ (Redis cache)           │     │
│                                            └──────────┬──────────────┘     │
│                                                       │                     │
│                                                       ▼                     │
│                                            ┌─────────────────────────┐     │
│                                            │ pgvector cosine search  │     │
│                                            │ pool_size = weight*2    │     │
│                                            └──────────┬──────────────┘     │
│                                                       │                     │
│                                                       ▼                     │
│                                            [cand_1, cand_2, ...]           │
│                                                       │                     │
│                                                       ▼                     │
│    all_results << results.map { |r| r.merge(query_index: idx) }           │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         all_results = [
           {id: 1, distance: 0.15, query_index: 0},
           {id: 2, distance: 0.18, query_index: 0},
           {id: 1, distance: 0.12, query_index: 1},  # ← Duplicata!
           {id: 3, distance: 0.20, query_index: 1},
           {id: 1, distance: 0.14, query_index: 2},  # ← Duplicata!
           ...
         ]
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Deduplication + Multi-Query Boost                                  │
│                                                                             │
│  by_id = {}                                                                 │
│  FOR EACH result in all_results:                                           │
│    id = result[:id]                                                         │
│                                                                             │
│    IF by_id[id] exists:                                                    │
│      # Candidato apareceu em múltiplas queries! BOOST!                     │
│      by_id[id][:multi_query_boost] += 0.15                                 │
│      by_id[id][:query_hits] += 1                                           │
│      by_id[id][:distance] = MIN(by_id[id][:distance], result[:distance])  │
│    ELSE:                                                                    │
│      by_id[id] = result.merge(multi_query_boost: 1.0, query_hits: 1)      │
│                                                                             │
│  EXAMPLE:                                                                   │
│  Candidato ID=1 apareceu em 3 queries:                                     │
│    multi_query_boost = 1.0 + (0.15 * 2) = 1.30                            │
│    query_hits = 3                                                           │
│    distance = MIN(0.15, 0.12, 0.14) = 0.12                                │
│                                                                             │
│  Sort by: distance / multi_query_boost                                     │
│    → Candidato 1: 0.12 / 1.30 = 0.092 (rank 1)                            │
│    → Candidato 2: 0.18 / 1.00 = 0.180 (rank 2)                            │
│    → Candidato 3: 0.20 / 1.00 = 0.200 (rank 3)                            │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         deduplicated_results (sorted by adjusted distance)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Parallel Elasticsearch Search                                      │
│                                                                             │
│  keywords = build_keywords_from_profile(profile)                           │
│    → "senior desenvolvedor ruby Ruby Rails PostgreSQL liderança técnica"   │
│                                                                             │
│  es_results = ElasticsearchStrategy.search(keywords, pool_size)            │
│    → [{id: 2, score: 8.5}, {id: 1, score: 7.8}, {id: 4, score: 6.2}, ...] │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: Confidence-Based Fusion                                            │
│                                                                             │
│  strategy = determine_search_strategy(extraction)                          │
│    IF confidence >= 0.75:   :high_confidence                               │
│    ELIF confidence >= 0.50: :medium_confidence                             │
│    ELSE:                    :low_confidence                                │
│                                                                             │
│  weights = calculate_confidence_adjusted_weights(confidence, strategy)     │
│                                                                             │
│  WEIGHTS TABLE:                                                             │
│  ┌─────────────────┬─────────────────┬──────────────────┐                 │
│  │ Strategy        │ Elasticsearch   │ Embedding        │                 │
│  ├─────────────────┼─────────────────┼──────────────────┤                 │
│  │ high_confidence │ 35%             │ 65%              │ ← Confia semântica│
│  │ medium          │ 50%             │ 50%              │ ← Balanceado     │
│  │ low_confidence  │ 70%             │ 30%              │ ← Confia keywords│
│  └─────────────────┴─────────────────┴──────────────────┘                 │
│                                                                             │
│  fused = WeightedRankFusion.combine(                                       │
│    { elasticsearch: es_results, embedding: emb_results },                  │
│    weights: { elasticsearch: 0.35, embedding: 0.65 }                       │
│  )                                                                          │
│                                                                             │
│  RRF Formula (Reciprocal Rank Fusion):                                     │
│  ┌────────────────────────────────────────────────────────────┐           │
│  │ score(candidate) = Σ [ weight_i / (k + rank_i) ]          │           │
│  │                    i ∈ {elasticsearch, embedding}          │           │
│  │                                                            │           │
│  │ k = 60 (constant)                                          │           │
│  │ rank_i = position of candidate in source i                │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  EXAMPLE:                                                                   │
│  Candidate 1:                                                               │
│    ES rank = 2 → 0.35 / (60 + 2) = 0.00564                                │
│    Emb rank = 1 → 0.65 / (60 + 1) = 0.01066                               │
│    RRF score = 0.01630                                                     │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         fused_results (sorted by RRF score)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: Reranking with Quality Boosts                                      │
│                                                                             │
│  reranked = Reranker.apply(fused_results, limit: limit)                   │
│                                                                             │
│  FOR EACH candidate:                                                       │
│    base_boost = calculate_base_boost(candidate_data)                       │
│      → profile_completeness: +0.10                                         │
│      → has_contact_info: +0.05                                             │
│      → recent_activity: +0.08                                              │
│      → has_curriculum: +0.12                                               │
│      → ...                                                                  │
│                                                                             │
│    final_score = rrf_score * (1 + base_boost)                             │
│                                                                             │
│  EXAMPLE:                                                                   │
│    rrf_score = 0.01630                                                     │
│    base_boost = 0.25                                                       │
│    final_score = 0.01630 * 1.25 = 0.02038                                 │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Ranked Candidates                                                  │
│                                                                             │
│  Result {                                                                   │
│    candidates: [Candidate, Candidate, ...],                                │
│    metadata: {                                                              │
│      extraction_confidence: 0.85,                                          │
│      extraction_method: :llm,                                              │
│      missing_fields: [],                                                   │
│      queries_generated: 5,                                                 │
│      fusion_weights: { elasticsearch: 0.35, embedding: 0.65 }              │
│    },                                                                       │
│    search_meta_by_id: {                                                    │
│      123 => {                                                               │
│        source: "hybrid",                                                    │
│        score: 0.02038,                                                     │
│        contributions: { elasticsearch: 0.4, embedding: 0.6 },              │
│        boost: 0.25,                                                         │
│        boost_breakdown: { ... },                                           │
│        multi_query_hits: 3,                                                │
│        final_score: 0.02038                                                │
│      }                                                                      │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Diagrama 3: Fluxo de JD Search

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ INPUT: Job Description Text                                                │
│                                                                             │
│ "Buscamos desenvolvedor Ruby Senior com experiência em Rails e PostgreSQL. │
│  Requisitos: Ruby on Rails, PostgreSQL, Redis, 5+ anos de experiência.    │
│  Desejável: React, Docker, experiência em fintech."                        │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: JD Processing                                                      │
│                                                                             │
│  JobDescriptionProcessor.process(jd_text)                                  │
│                                                                             │
│  1. Detect document type:                                                  │
│     jd_score = count_matches(JD_INDICATORS)      → 5 matches              │
│     resume_score = count_matches(RESUME_INDICATORS) → 0 matches           │
│     → :job_description                                                     │
│                                                                             │
│  2. LLM Extraction:                                                         │
│     Prompt: "Extraia requisitos obrigatórios vs desejáveis..."            │
│     Response: {                                                             │
│       required_skills: ["Ruby on Rails", "PostgreSQL", "Redis"],          │
│       nice_to_have: ["React", "Docker"],                                   │
│       seniority_range: {min: :pleno, max: :senior},                       │
│       experience_range: {min: 5, max: 10}                                 │
│     }                                                                       │
│                                                                             │
│  3. Generate boost config:                                                 │
│     {                                                                       │
│       required_skill_match: {weight: 0.15, skills: [...]},                │
│       nice_to_have_match: {weight: 0.05, skills: [...]},                  │
│       seniority_match: {weight: 0.10, range: {...}},                      │
│       experience_match: {weight: 0.08, range: {...}}                      │
│     }                                                                       │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
         ProcessedJD {
           required_skills: ["Ruby on Rails", "PostgreSQL", "Redis"],
           nice_to_have_skills: ["React", "Docker"],
           seniority_range: {min: :pleno, max: :senior},
           role_titles: ["Desenvolvedor Ruby", "Engenheiro Backend"],
           industry_keywords: ["fintech"],
           experience_range: {min: 5, max: 10},
           boost_config: {...}
         }
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Elasticsearch Query (Prioritizing Required Skills)                 │
│                                                                             │
│  es_query = build_jd_elasticsearch_query(processed_jd)                     │
│                                                                             │
│  Query parts (in order of priority):                                       │
│    1. Required skills: "Ruby on Rails PostgreSQL Redis"                    │
│    2. Role title: "Desenvolvedor Ruby"                                     │
│    3. Nice-to-have (top 3): "React Docker"                                 │
│                                                                             │
│  Final query: "Ruby on Rails PostgreSQL Redis Desenvolvedor Ruby React"   │
│                                                                             │
│  es_results = ElasticsearchStrategy.search(es_query, pool_size: large)    │
│    → [{id: 5, score: 9.2}, {id: 8, score: 8.7}, ...]                      │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: HyDE Generation (Ideal Candidate Profile)                          │
│                                                                             │
│  profile_ideal = {                                                          │
│    "primary_role" => processed_jd.role_titles.first,                       │
│    "core_technologies" => processed_jd.required_skills,                    │
│    "transferable_skills" => processed_jd.nice_to_have_skills,              │
│    "seniority" => processed_jd.seniority_range[:min],                      │
│    "industry" => processed_jd.industry_keywords.first                      │
│  }                                                                          │
│                                                                             │
│  hyde_doc = HydeDocumentGenerator.generate(                                │
│    profile_ideal,                                                           │
│    context: :job_description,                                              │
│    verbosity: :standard                                                     │
│  )                                                                          │
│                                                                             │
│  GENERATED HyDE:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Candidato ideal para vaga de Desenvolvedor Ruby:                     │ │
│  │                                                                       │ │
│  │ REQUISITOS ATENDIDOS:                                                 │ │
│  │ - Experiência de 5 a 10 anos em Ruby on Rails, PostgreSQL, Redis    │ │
│  │ - Conhecimento sólido em Ruby on Rails, PostgreSQL, Redis           │ │
│  │ - Nível pleno com atuação em fintech                                 │ │
│  │                                                                       │ │
│  │ DIFERENCIAIS:                                                         │ │
│  │ - Experiência adicional em React, Docker                             │ │
│  │ - Capacidade de desenvolver soluções complexas e colaborar com time │ │
│  │                                                                       │ │
│  │ PERFIL COMPORTAMENTAL:                                                │ │
│  │ Profissional com perfil proativo, colaborativo e focado em          │ │
│  │ qualidade, adequado para ambiente regulado, com foco em segurança.  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Embedding Search                                                   │
│                                                                             │
│  embedding = EmbeddingCache.fetch(hyde_doc)                                │
│  emb_results = EmbeddingStrategy.search(embedding, pool_size)              │
│    → [{id: 8, distance: 0.11}, {id: 5, distance: 0.13}, ...]              │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Fusion (ES-Prioritized for JD)                                     │
│                                                                             │
│  weights = { elasticsearch: 0.60, embedding: 0.40 }                        │
│    ↑ ES tem mais peso porque JD precisa de match exato de requisitos      │
│                                                                             │
│  fused = WeightedRankFusion.combine(                                       │
│    { elasticsearch: es_results, embedding: emb_results },                  │
│    weights: weights                                                         │
│  )                                                                          │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Custom Reranking (Required Skills Boost)                           │
│                                                                             │
│  reranked = Reranker.apply(                                                │
│    fused_results,                                                           │
│    limit: limit,                                                            │
│    custom_boost_config: processed_jd.boost_config  ◄── CUSTOM!            │
│  )                                                                          │
│                                                                             │
│  FOR EACH candidate:                                                       │
│    base_boost = calculate_base_boost(data)                                 │
│    custom_boost = calculate_custom_boost(data, boost_config)               │
│                                                                             │
│    CUSTOM BOOST CALCULATION:                                               │
│    ┌────────────────────────────────────────────────────────────┐         │
│    │ Required skills matched: 3/3 → boost = 0.15 * (3/3) = 0.15 │         │
│    │ Nice-to-have matched: 1/2 → boost = 0.05 * (1/2) = 0.025   │         │
│    │ Seniority in range: pleno ∈ [pleno, senior] → boost = 0.10 │         │
│    │ Experience in range: 7 ∈ [5, 10] → boost = 0.08            │         │
│    │                                                             │         │
│    │ Total custom boost = 0.15 + 0.025 + 0.10 + 0.08 = 0.355   │         │
│    └────────────────────────────────────────────────────────────┘         │
│                                                                             │
│    total_boost = base_boost + custom_boost                                 │
│      = 0.20 + 0.355 = 0.555                                               │
│                                                                             │
│    final_score = rrf_score * (1 + total_boost)                            │
│      = 0.0145 * 1.555 = 0.0225                                            │
└────────────────────────────┬────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Candidates Ranked by JD Match                                      │
│                                                                             │
│  Result {                                                                   │
│    candidates: [...],                                                       │
│    metadata: {                                                              │
│      search_type: :job_description,                                        │
│      required_skills: ["Ruby on Rails", "PostgreSQL", "Redis"],           │
│      nice_to_have_skills: ["React", "Docker"],                             │
│      fusion_weights: { elasticsearch: 0.60, embedding: 0.40 }              │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes Técnicos Detalhados

### ProfileExtractor

**Código-chave:**

```ruby
def extract(text, source_type: :resume)
  return build_empty_result if text.blank?

  profile, method = extract_with_llm(text, source_type)

  profile = normalize_profile(profile)
  missing = find_missing_fields(profile)
  confidence = calculate_confidence(profile, method)

  ExtractionResult.new(
    profile: profile,
    confidence: confidence,
    extraction_method: method,
    missing_fields: missing
  )
end
```

**Fluxo de Fallback:**

```
extract_with_llm()
  ├─ @llm_client.chat(prompt) → Success → [:llm, profile]
  │
  ├─ LLM timeout/error → extract_structured(text) → [:structured, profile]
  │
  └─ Structured fails → extract_keyword_fallback(text) → [:keyword_fallback, profile]
```

**Confidence Formula:**

```ruby
confidence = (base * 0.4) + (coverage * 0.3) + (quality * 0.3)

# base = confidence_by_method[method]
#   :llm → 0.85
#   :structured → 0.70
#   :keyword_fallback → 0.40

# coverage = (required_present / required_total) * 0.7 +
#            (optional_present / optional_total) * 0.3

# quality = average of:
#   - tech_count >= 2 ? 1.0 : tech_count * 0.5
#   - role_words >= 2 ? 1.0 : 0.5
#   - valid_seniority ? 1.0 : 0.3
```

---

### MultiQueryGenerator

**Estratégias de Geração:**

```ruby
def build_queries_from_profile(profile, context)
  queries = []

  # 1. Role-focused
  queries << "#{profile['seniority']} #{profile['primary_role']}"

  # 2. Tech-focused
  queries << profile['core_technologies'].join(' ')

  # 3. Industry-focused
  queries << "#{profile['primary_role']} #{profile['industry']} #{profile['transferable_skills'].first}"

  # 4. Experience-focused
  queries << "#{profile['seniority']} #{profile['years_experience']} anos #{profile['primary_role']}"

  # 5. Hybrid
  queries << "#{profile['core_technologies'].first(2).join(' ')} #{profile['primary_role']}"

  queries.compact.uniq.first(5)
end
```

**Weight Normalization:**

```ruby
def calculate_weights(count)
  base_weights = [0.3, 0.25, 0.2, 0.15, 0.1]
  weights = base_weights.first(count)

  total = weights.sum
  weights.map { |w| (w / total).round(2) }
end

# Exemplo:
# count = 3 → weights = [0.3, 0.25, 0.2]
# total = 0.75
# normalized = [0.40, 0.33, 0.27]  # sum = 1.0
```

---

### Deduplication Algorithm

**Código completo:**

```ruby
def deduplicate_and_boost(results)
  by_id = {}

  results.each do |result|
    id = result[:id]

    if by_id[id]
      # Já existe - candidato apareceu em múltiplas queries
      by_id[id][:multi_query_boost] = (by_id[id][:multi_query_boost] || 1.0) + 0.15
      by_id[id][:query_hits] = (by_id[id][:query_hits] || 1) + 1

      # Mantém a MENOR distância (melhor score)
      by_id[id][:distance] = [by_id[id][:distance], result[:distance]].min
    else
      # Primeira aparição
      by_id[id] = result.merge(multi_query_boost: 1.0, query_hits: 1)
    end
  end

  # Re-rankear considerando boost
  by_id.values
    .sort_by { |r| r[:distance].to_f / r[:multi_query_boost] }
    .each_with_index
    .map { |r, idx| r.merge(rank: idx + 1) }
end
```

**Exemplo numérico:**

```
Input:
  Query 1: {id: 5, distance: 0.15}
  Query 2: {id: 5, distance: 0.12}  ← Duplicata
  Query 3: {id: 5, distance: 0.18}  ← Duplicata
  Query 1: {id: 7, distance: 0.10}
  Query 2: {id: 7, distance: 0.14}  ← Duplicata

Processing:
  Candidato 5:
    multi_query_boost = 1.0 + 0.15 + 0.15 = 1.30
    query_hits = 3
    distance = MIN(0.15, 0.12, 0.18) = 0.12
    adjusted_distance = 0.12 / 1.30 = 0.092

  Candidato 7:
    multi_query_boost = 1.0 + 0.15 = 1.15
    query_hits = 2
    distance = MIN(0.10, 0.14) = 0.10
    adjusted_distance = 0.10 / 1.15 = 0.087

Ranking:
  1. Candidato 7 (adjusted: 0.087)  ← Melhor!
  2. Candidato 5 (adjusted: 0.092)
```

---

### Weighted Rank Fusion (RRF)

**Fórmula:**

```
For each candidate c:
  RRF_score(c) = Σ [weight_s / (k + rank_s(c))]
                 s ∈ sources

Where:
  - k = 60 (constant, prevents division by zero and reduces impact of early ranks)
  - rank_s(c) = position of candidate c in source s (1-indexed)
  - weight_s = weight assigned to source s
```

**Exemplo de Cálculo:**

```ruby
# Candidate 42
# - Elasticsearch: rank 3, weight 0.35
# - Embedding: rank 1, weight 0.65

rrf_score = (0.35 / (60 + 3)) + (0.65 / (60 + 1))
          = (0.35 / 63) + (0.65 / 61)
          = 0.00556 + 0.01066
          = 0.01622

# Candidate 99
# - Elasticsearch: rank 1, weight 0.35
# - Embedding: rank 5, weight 0.65

rrf_score = (0.35 / (60 + 1)) + (0.65 / (60 + 5))
          = (0.35 / 61) + (0.65 / 65)
          = 0.00574 + 0.01000
          = 0.01574

# Ranking final:
# 1. Candidate 42: 0.01622
# 2. Candidate 99: 0.01574
```

**Por que RRF funciona melhor que score direto?**

1. **Normalização automática:** Scores de diferentes fontes são incomparáveis (ES: 0-100, Embedding: 0-1)
2. **Robustez a outliers:** Rank é mais estável que score absoluto
3. **Pesos configuráveis:** Fácil ajustar importância de cada fonte
4. **Propriedade de fusão:** Combina evidências de múltiplas fontes de forma principled

---

## 📊 Performance e Otimizações

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                     EMBEDDING CACHE                         │
│                                                             │
│  Key: SHA256(text + account_id)                            │
│  Value: [float × 1536]                                     │
│  TTL: 7 days                                                │
│  Storage: Redis                                             │
│                                                             │
│  Hit rate: ~75% (resumes similares, queries repetidas)     │
│  Miss penalty: ~200ms (API call)                            │
│  Hit benefit: ~2ms (Redis GET)                              │
│                                                             │
│  Economia estimada:                                         │
│    100 searches/day × 5 queries × 0.75 hit rate × 200ms    │
│    = 75,000ms saved = 1.25 minutes/day                     │
└─────────────────────────────────────────────────────────────┘
```

### Query Pool Sizes

```ruby
def effective_pool_size(limit)
  min_pool = (limit * 4).clamp(
    Configuration.min_pool_size,  # 40
    Configuration.max_pool_size   # 400
  )
  [Configuration.initial_pool_size, min_pool].max
end

# Exemplos:
# limit=10 → pool=40 (min)
# limit=50 → pool=200
# limit=100 → pool=400 (max)
```

**Por que pool = limit × 4?**

- RRF precisa de overlap entre fontes
- Filtros podem remover candidatos
- Queremos garantir `limit` resultados finais
- Trade-off: recall vs performance

### Latency Breakdown

```
Simple Search (~200ms):
  ├─ ES query: 80ms
  ├─ Embedding fetch (cached): 2ms
  ├─ Embedding search: 60ms
  ├─ Fusion: 5ms
  ├─ Reranking: 40ms
  └─ Load candidates: 13ms

Resume Search (~2500ms):
  ├─ Profile extraction (LLM): 1200ms  ◄── Bottleneck
  ├─ Multi-query generation: 50ms
  ├─ HyDE generation (5×): 200ms
  ├─ Embedding fetch (5×, partial cache): 400ms
  ├─ Embedding search (5×): 300ms
  ├─ Deduplication: 20ms
  ├─ ES query: 80ms
  ├─ Fusion: 8ms
  ├─ Reranking: 50ms
  └─ Load candidates: 15ms

JD Search (~2000ms):
  ├─ JD processing (LLM): 1100ms  ◄── Bottleneck
  ├─ HyDE generation: 180ms
  ├─ Embedding fetch (cached): 2ms
  ├─ Embedding search: 60ms
  ├─ ES query: 120ms
  ├─ Fusion: 6ms
  ├─ Reranking (custom): 60ms
  └─ Load candidates: 15ms
```

**Otimizações possíveis:**

1. **Parallel LLM calls** - Extraction + Query generation em paralelo
2. **Streaming LLM** - Processar chunks antes do fim
3. **Batch embedding** - 5 queries em 1 API call
4. **Async search** - ES + Embedding em paralelo (já implementado)

---

## 🧪 Testing Strategy

### Unit Tests

```ruby
# spec/services/candidates/search/profile_extractor_spec.rb
RSpec.describe Candidates::Search::ProfileExtractor do
  let(:extractor) { described_class.new }

  describe '#extract' do
    context 'with complete resume' do
      let(:resume) { File.read('spec/fixtures/resume_complete.txt') }

      it 'extracts with high confidence' do
        result = extractor.extract(resume)
        expect(result.confidence).to be >= 0.75
        expect(result.extraction_method).to eq(:llm)
      end
    end

    context 'with partial resume' do
      let(:resume) { 'Senior Ruby developer, 5 years experience' }

      it 'falls back to structured extraction' do
        result = extractor.extract(resume)
        expect(result.confidence).to be_between(0.50, 0.74)
        expect(result.extraction_method).to eq(:structured)
      end
    end

    context 'with minimal resume' do
      let(:resume) { 'Ruby developer' }

      it 'uses keyword fallback' do
        result = extractor.extract(resume)
        expect(result.confidence).to be < 0.50
        expect(result.extraction_method).to eq(:keyword_fallback)
      end
    end
  end
end
```

### Integration Tests

```ruby
# spec/services/candidates/search/hybrid_search_service_spec.rb
RSpec.describe Candidates::Search::HybridSearchService do
  let(:service) { described_class.new(account_id: 1, tenant: 'test') }

  describe '#search with resume' do
    let(:resume) { File.read('spec/fixtures/resume_senior_ruby.txt') }

    before do
      # Create test candidates
      create(:candidate, curriculum_text: 'Senior Ruby on Rails developer...')
      create(:candidate, curriculum_text: 'Python Django developer...')
    end

    it 'uses multi-query retrieval' do
      result = service.search(resume, limit: 10)

      expect(result.metadata[:queries_generated]).to be >= 3
      expect(result.metadata[:search_type]).to eq(:resume)
    end

    it 'adjusts weights based on confidence' do
      result = service.search(resume, limit: 10)

      weights = result.metadata[:fusion_weights]
      if result.metadata[:extraction_confidence] >= 0.75
        expect(weights[:embedding]).to be > weights[:elasticsearch]
      end
    end

    it 'applies multi-query boost' do
      result = service.search(resume, limit: 10)

      meta = result.search_meta_by_id[result.candidates.first.id]
      expect(meta[:multi_query_hits]).to be >= 1
    end
  end
end
```

---

**Versão:** 2.0  
**Última atualização:** 2026-02-01  
**Próxima revisão:** 2026-03-01
