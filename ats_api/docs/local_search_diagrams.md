# Local Search - Diagramas Visuais (Mermaid)

> **Diagramas em formato Mermaid**  
> Renderize estes diagramas no GitHub, GitLab, ou em ferramentas que suportam Mermaid  
> **Última atualização:** 2026-02-01

## 📊 Índice de Diagramas

1. [Fluxo Principal de Busca](#1-fluxo-principal-de-busca)
2. [Detecção de Tipo de Query](#2-detecção-de-tipo-de-query)
3. [Resume Search - Multi-Query Flow](#3-resume-search---multi-query-flow)
4. [Job Description Search Flow](#4-job-description-search-flow)
5. [Profile Extraction Flow](#5-profile-extraction-flow)
6. [Deduplication e Multi-Query Boost](#6-deduplication-e-multi-query-boost)
7. [Weighted Rank Fusion](#7-weighted-rank-fusion)
8. [Reranking com Boosts](#8-reranking-com-boosts)
9. [Arquitetura de Classes](#9-arquitetura-de-classes)
10. [Fluxo de Dados Completo](#10-fluxo-de-dados-completo)

---

## 1. Fluxo Principal de Busca

```mermaid
graph TD
    A[User Query] --> B[HybridSearchService]
    B --> C{SimpleQueryDetector}
    
    C -->|:simple| D[execute_simple_search]
    C -->|:complex| E[execute_complex_search]
    C -->|:resume| F[execute_resume_search]
    C -->|:job_description| G[execute_jd_search]
    
    D --> H[Elasticsearch Strategy]
    D --> I[Embedding Strategy]
    
    E --> J[QueryAnalyzer + LLM]
    E --> H
    E --> I
    
    F --> K[ProfileExtractor]
    F --> L[MultiQueryGenerator]
    F --> M[Multi-Embedding Search]
    
    G --> N[JobDescriptionProcessor]
    G --> H
    G --> I
    
    H --> O[WeightedRankFusion]
    I --> O
    M --> O
    
    O --> P[Reranker]
    P --> Q[Ranked Results]
    
    style F fill:#90EE90
    style G fill:#87CEEB
    style D fill:#FFE4B5
    style E fill:#FFE4B5
```

---

## 2. Detecção de Tipo de Query

```mermaid
flowchart TD
    A[Query Text] --> B{Blank or *?}
    B -->|Yes| C[:simple]
    B -->|No| D{Length > 200?}
    
    D -->|No| E{Has complex indicators?}
    E -->|Yes| F[:complex]
    E -->|No| C
    
    D -->|Yes| G{Count JD indicators}
    G --> H{Count Resume indicators}
    
    H --> I{JD score > Resume score<br/>and JD >= 2?}
    I -->|Yes| J[:job_description]
    I -->|No| K{Resume score >= 2<br/>and length > 500?}
    
    K -->|Yes| L[:resume]
    K -->|No| M{Has JD structure?<br/>requisitos + responsabilidades}
    
    M -->|Yes| J
    M -->|No| F
    
    style J fill:#87CEEB
    style L fill:#90EE90
    style C fill:#FFE4B5
    style F fill:#FFE4B5
```

---

## 3. Resume Search - Multi-Query Flow

```mermaid
sequenceDiagram
    participant U as User
    participant HS as HybridSearchService
    participant PE as ProfileExtractor
    participant MQG as MultiQueryGenerator
    participant HDG as HydeDocumentGenerator
    participant EC as EmbeddingCache
    participant ES as EmbeddingStrategy
    participant WRF as WeightedRankFusion
    participant R as Reranker
    
    U->>HS: search(resume_text)
    HS->>PE: extract(resume_text)
    
    PE->>PE: LLM extraction
    alt LLM Success
        PE-->>HS: profile (confidence: 0.85)
    else LLM Fail
        PE->>PE: Structured fallback
        PE-->>HS: profile (confidence: 0.70)
    end
    
    HS->>MQG: generate(profile)
    MQG-->>HS: 5 queries + weights
    
    loop For each query
        HS->>HDG: generate(query_profile)
        HDG-->>HS: hyde_doc
        HS->>EC: fetch(hyde_doc)
        EC-->>HS: embedding vector
        HS->>ES: search(embedding)
        ES-->>HS: candidates
    end
    
    HS->>HS: deduplicate_and_boost()
    Note over HS: +15% boost per<br/>additional query match
    
    HS->>WRF: combine(ES + Embedding)
    WRF-->>HS: fused_results
    
    HS->>R: apply(fused_results)
    R-->>HS: reranked_candidates
    
    HS-->>U: Result with metadata
```

---

## 4. Job Description Search Flow

```mermaid
sequenceDiagram
    participant U as User
    participant HS as HybridSearchService
    participant JDP as JobDescriptionProcessor
    participant HDG as HydeDocumentGenerator
    participant ESS as ElasticsearchStrategy
    participant EMS as EmbeddingStrategy
    participant WRF as WeightedRankFusion
    participant R as Reranker
    
    U->>HS: search(jd_text)
    HS->>JDP: process(jd_text)
    
    JDP->>JDP: detect_document_type()
    JDP->>JDP: LLM extraction
    JDP->>JDP: generate_boost_config()
    JDP-->>HS: ProcessedJD
    
    Note over JDP: required_skills: [Ruby, Rails]<br/>nice_to_have: [React]<br/>boost_config: {...}
    
    par Parallel Search
        HS->>ESS: search("Ruby Rails React")
        ESS-->>HS: es_results
    and
        HS->>HDG: generate(ideal_profile, context: :jd)
        HDG-->>HS: hyde_doc_ideal_candidate
        HS->>EMS: search(embedding)
        EMS-->>HS: emb_results
    end
    
    HS->>WRF: combine(ES: 60%, Emb: 40%)
    WRF-->>HS: fused_results
    
    HS->>R: apply(fused, custom_boost_config)
    Note over R: Boost +0.15 for<br/>required skills match
    R-->>HS: reranked_candidates
    
    HS-->>U: Result with JD metadata
```

---

## 5. Profile Extraction Flow

```mermaid
stateDiagram-v2
    [*] --> CheckInput
    
    CheckInput --> EmptyResult: text.blank?
    CheckInput --> LLMExtraction: text.present?
    
    LLMExtraction --> ValidateJSON: LLM response
    ValidateJSON --> HighConfidence: Valid & Complete
    ValidateJSON --> StructuredExtraction: Invalid/Incomplete
    
    StructuredExtraction --> RegexParsing
    RegexParsing --> MediumConfidence: Success
    RegexParsing --> KeywordFallback: Fail
    
    KeywordFallback --> LowConfidence
    
    HighConfidence --> CalculateMetrics
    MediumConfidence --> CalculateMetrics
    LowConfidence --> CalculateMetrics
    
    CalculateMetrics --> BuildResult
    EmptyResult --> BuildResult
    
    BuildResult --> [*]
    
    note right of HighConfidence
        confidence >= 0.75
        method: :llm
    end note
    
    note right of MediumConfidence
        confidence: 0.50-0.74
        method: :structured
    end note
    
    note right of LowConfidence
        confidence < 0.50
        method: :keyword_fallback
    end note
```

---

## 6. Deduplication e Multi-Query Boost

```mermaid
graph LR
    A[Query 1 Results] --> D[Deduplicator]
    B[Query 2 Results] --> D
    C[Query 3 Results] --> D
    
    D --> E{Candidate<br/>already seen?}
    
    E -->|No| F[Add to by_id<br/>boost = 1.0<br/>hits = 1]
    E -->|Yes| G[Increment boost<br/>+= 0.15<br/>hits += 1]
    
    F --> H[Keep best distance]
    G --> H
    
    H --> I[Sort by<br/>distance / boost]
    I --> J[Deduplicated Results]
    
    style G fill:#90EE90
    
    subgraph Example
        K[Cand 5: query 1<br/>distance: 0.15] --> L
        M[Cand 5: query 2<br/>distance: 0.12] --> L
        N[Cand 5: query 3<br/>distance: 0.18] --> L
        
        L[Final: Cand 5<br/>boost: 1.30<br/>hits: 3<br/>distance: 0.12<br/>adjusted: 0.092]
    end
```

---

## 7. Weighted Rank Fusion

```mermaid
graph TD
    A[Elasticsearch Results] --> C[RRF Calculator]
    B[Embedding Results] --> C
    
    C --> D{For each candidate}
    D --> E[Calculate ES contribution<br/>weight / 60 + rank]
    D --> F[Calculate Emb contribution<br/>weight / 60 + rank]
    
    E --> G[Sum contributions]
    F --> G
    
    G --> H[Sort by RRF score]
    H --> I[Fused Results]
    
    subgraph Formula
        J[RRF score = Σ weight_i / k + rank_i<br/>k = 60]
    end
    
    subgraph Example
        K[Candidate 42]
        K --> L[ES: rank 3, w=0.35<br/>0.35/63 = 0.00556]
        K --> M[Emb: rank 1, w=0.65<br/>0.65/61 = 0.01066]
        L --> N[Total: 0.01622]
        M --> N
    end
```

---

## 8. Reranking com Boosts

```mermaid
graph TD
    A[Fused Results<br/>RRF scores] --> B[Reranker]
    
    B --> C[Load candidate data]
    C --> D[Calculate base boost]
    C --> E[Calculate custom boost]
    
    D --> F[Base signals]
    F --> G[+0.10 profile_completeness]
    F --> H[+0.05 has_contact]
    F --> I[+0.12 has_curriculum]
    F --> J[+0.08 recent_activity]
    
    E --> K{Custom config<br/>provided?}
    K -->|No| L[custom_boost = 0]
    K -->|Yes| M[Custom signals]
    
    M --> N[+0.15 × required_match_ratio]
    M --> O[+0.05 × nice_to_have_ratio]
    M --> P[+0.10 seniority_in_range]
    M --> Q[+0.08 experience_in_range]
    
    G --> R[Total boost]
    H --> R
    I --> R
    J --> R
    L --> R
    N --> R
    O --> R
    P --> R
    Q --> R
    
    R --> S[Final score =<br/>RRF × 1 + boost]
    S --> T[Sort by final_score]
    T --> U[Reranked Results]
    
    style M fill:#87CEEB
    style K fill:#FFD700
```

---

## 9. Arquitetura de Classes

```mermaid
classDiagram
    class HybridSearchService {
        +account_id: Integer
        +tenant: String
        -es_strategy: ElasticsearchStrategy
        -emb_strategy: EmbeddingStrategy
        -profile_extractor: ProfileExtractor
        -multi_query_generator: MultiQueryGenerator
        -hyde_generator: HydeDocumentGenerator
        -jd_processor: JobDescriptionProcessor
        +search(query, filters, limit) Result
        -execute_simple_search()
        -execute_complex_search()
        -execute_resume_search()
        -execute_jd_search()
    }
    
    class ProfileExtractor {
        -llm_client: GeminiClient
        +extract(text, source_type) ExtractionResult
        -extract_with_llm()
        -extract_structured()
        -calculate_confidence()
    }
    
    class ExtractionResult {
        +profile: Hash
        +confidence: Float
        +extraction_method: Symbol
        +missing_fields: Array
    }
    
    class MultiQueryGenerator {
        -llm_client: GeminiClient
        +generate(profile, context) Result
        -build_queries_from_profile()
        -calculate_weights()
    }
    
    class MultiQueryResult {
        +queries: Array~String~
        +weights: Array~Float~
        +strategy_used: Symbol
    }
    
    class HydeDocumentGenerator {
        -llm_client: GeminiClient
        +generate(profile, context, verbosity) String
        -generate_for_resume()
        -generate_for_jd()
    }
    
    class JobDescriptionProcessor {
        -llm_client: GeminiClient
        +process(jd_text) ProcessedJD
        +detect_document_type(text) Symbol
        -extract_jd_structure()
        -generate_boost_config()
    }
    
    class ProcessedJD {
        +required_skills: Array
        +nice_to_have_skills: Array
        +seniority_range: Hash
        +role_titles: Array
        +boost_config: Hash
    }
    
    class SimpleQueryDetector {
        <<class>>
        +detect(query) Symbol
        +job_description?(query) Boolean
        +resume?(query) Boolean
    }
    
    class Reranker {
        <<class>>
        +apply(candidates, limit, custom_boost) Array
        -calculate_base_boost()
        -calculate_custom_boost()
        -combine_boosts()
    }
    
    class WeightedRankFusion {
        <<class>>
        +combine(sources, weights) Array
    }
    
    HybridSearchService --> ProfileExtractor
    HybridSearchService --> MultiQueryGenerator
    HybridSearchService --> HydeDocumentGenerator
    HybridSearchService --> JobDescriptionProcessor
    HybridSearchService --> SimpleQueryDetector
    HybridSearchService --> Reranker
    HybridSearchService --> WeightedRankFusion
    
    ProfileExtractor --> ExtractionResult
    MultiQueryGenerator --> MultiQueryResult
    JobDescriptionProcessor --> ProcessedJD
```

---

## 10. Fluxo de Dados Completo

```mermaid
flowchart TB
    subgraph Input Layer
        A1[Simple Query<br/>ruby senior]
        A2[Complex Query<br/>dev com 5 anos...]
        A3[Resume Text<br/>3000+ words]
        A4[JD Text<br/>Vaga para...]
    end
    
    A1 --> B[SimpleQueryDetector]
    A2 --> B
    A3 --> B
    A4 --> B
    
    B -->|:simple| C1[Simple Path]
    B -->|:complex| C2[Complex Path]
    B -->|:resume| C3[Resume Path]
    B -->|:job_description| C4[JD Path]
    
    subgraph Simple Path
        C1 --> D1[ES Search<br/>70% weight]
        C1 --> D2[Embedding Search<br/>30% weight]
    end
    
    subgraph Complex Path
        C2 --> E1[QueryAnalyzer<br/>LLM]
        E1 --> E2[HyDE Expansion]
        E2 --> E3[ES + Embedding<br/>50/50]
    end
    
    subgraph Resume Path - ENHANCED
        C3 --> F1[ProfileExtractor<br/>confidence scoring]
        F1 --> F2[MultiQueryGenerator<br/>3-5 queries]
        F2 --> F3[HydeDocGenerator<br/>rich templates]
        F3 --> F4[Multi-Embedding Search]
        F4 --> F5[Deduplication<br/>+15% per match]
        C3 --> F6[ES Search<br/>keywords from profile]
        F5 --> F7[Fusion<br/>confidence-adjusted weights]
        F6 --> F7
    end
    
    subgraph JD Path - NEW
        C4 --> G1[JDProcessor<br/>required vs nice-to-have]
        G1 --> G2[ES Search<br/>60% weight<br/>prioritize required]
        G1 --> G3[HyDE<br/>ideal candidate]
        G3 --> G4[Embedding Search<br/>40% weight]
        G2 --> G5[Fusion]
        G4 --> G5
        G5 --> G6[Reranker<br/>custom boost config]
    end
    
    D1 --> H[RRF Fusion]
    D2 --> H
    E3 --> H
    F7 --> H
    
    H --> I[Base Reranking]
    G6 --> J[Custom Reranking]
    
    I --> K[Final Results]
    J --> K
    
    K --> L[Result Object]
    
    subgraph Output
        L --> M1[candidates: Array]
        L --> M2[metadata: Hash]
        L --> M3[search_meta_by_id: Hash]
    end
    
    style C3 fill:#90EE90
    style C4 fill:#87CEEB
    style F5 fill:#FFD700
    style G6 fill:#FFD700
```

---

## Como Usar os Diagramas

### No GitHub/GitLab

Os diagramas Mermaid são renderizados automaticamente em arquivos `.md`:

1. Copie o código Mermaid
2. Cole em um arquivo `.md`
3. Commit e visualize no GitHub/GitLab

### Ferramentas Online

- **Mermaid Live Editor:** https://mermaid.live/
- **Draw.io (diagrams.net):** Importa Mermaid
- **VS Code:** Extensão "Markdown Preview Mermaid Support"

### Exportar como Imagem

```bash
# Usando mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Converter para PNG
mmdc -i diagram.mmd -o diagram.png

# Converter para SVG
mmdc -i diagram.mmd -o diagram.svg
```

---

## Legenda de Cores

| Cor | Significado |
|-----|-------------|
| 🟢 Verde (#90EE90) | Resume Search (Enhanced) |
| 🔵 Azul (#87CEEB) | JD Search (New) |
| 🟡 Amarelo (#FFE4B5) | Simple/Complex Search (Original) |
| 🟡 Dourado (#FFD700) | Componente crítico/boost |

---

**Versão:** 2.0  
**Formato:** Mermaid.js  
**Última atualização:** 2026-02-01
