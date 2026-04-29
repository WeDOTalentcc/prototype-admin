# Candidate Refinement System — Complete Technical Documentation

## Table of Contents
1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [API Entry Point](#3-api-entry-point)
4. [Complete Request Flow](#4-complete-request-flow)
5. [Phase 1 — Validation & Context Loading](#5-phase-1--validation--context-loading)
6. [Phase 2 — Feedback Persistence](#6-phase-2--feedback-persistence)
7. [Phase 3 — Vectorial Embedding Refinement](#7-phase-3--vectorial-embedding-refinement)
8. [Phase 4 — LLM Intent Extraction](#8-phase-4--llm-intent-extraction)
9. [Phase 5 — Hybrid Search (Vector + Elasticsearch + RRF)](#9-phase-5--hybrid-search-vector--elasticsearch--rrf)
10. [Phase 6 — Results Assembly & Response](#10-phase-6--results-assembly--response)
11. [Feedback Analyzer (Parallel)](#11-feedback-analyzer-parallel)
12. [Mathematical Formulas](#12-mathematical-formulas)
13. [Configuration Constants](#13-configuration-constants)
14. [Decision Tree Summary](#14-decision-tree-summary)
15. [Example: Real Scenario (Java → Ruby/Rails)](#15-example-real-scenario-java--rubyrails)
16. [API Response Schema](#16-api-response-schema)

---

## 1. Overview

The Candidate Refinement System allows recruiters to iteratively improve similarity search results by providing **like/dislike feedback** on candidates. Each refinement round:

1. Adjusts the search embedding vector towards liked and away from disliked candidates
2. Uses an LLM to extract the recruiter's **hidden intent** from dislike reasons
3. Runs a **hybrid search** combining vector similarity (pgvector) + text search (Elasticsearch)
4. Fuses results with **Reciprocal Rank Fusion (RRF)** with interleaving guarantees

The system solves a fundamental limitation of pure vector search: when a recruiter says "doesn't know Ruby" about a Java developer, the embedding shift alone cannot bridge the gap between Java and Ruby in the embedding space. The hybrid search uses Elasticsearch to find candidates matching both the base profile AND the desired skills.

---

## 2. Architecture

```
                          POST /v1/sourcings/:id/refinements
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │  RefinementsController   │
                          │  (parse params, auth)    │
                          └────────────┬────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │   RefinementService      │ ← Orchestrator
                          │   (call method)          │
                          └────────────┬────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
     ┌──────────────────┐  ┌─────────────────────┐  ┌──────────────┐
     │ EmbeddingRefine-  │  │ IntentBasedRefine-  │  │ Feedback-    │
     │ mentService       │  │ mentService         │  │ Analyzer-    │
     │ (α=0.3, β=0.2)   │  │ (γ=0.25, LLM)      │  │ Service      │
     └──────────┬───────┘  └─────────┬───────────┘  └──────────────┘
                │                    │
                │          ┌─────────┴─────────┐
                │          │                   │
                │          ▼                   ▼
                │   ┌─────────────┐   ┌──────────────┐
                │   │ GeminiClient│   │ Embeddings:: │
                │   │ (LLM chat)  │   │ Encoder      │
                │   └─────────────┘   └──────────────┘
                │
                ▼
     ┌──────────────────────────────────────────────┐
     │              hybrid_search                   │
     │  ┌──────────────┐    ┌──────────────────┐    │
     │  │ pgvector     │    │ TextSearchService │    │
     │  │ (60 results) │    │ (Elasticsearch)   │    │
     │  └──────┬───────┘    └────────┬─────────┘    │
     │         │                     │              │
     │         └─────────┬───────────┘              │
     │                   ▼                          │
     │         ┌──────────────────┐                 │
     │         │ RankFusionService│                 │
     │         │ (RRF + interleave)                │
     │         └──────────────────┘                 │
     └──────────────────────────────────────────────┘
```

### Files

| File | Responsibility |
|------|---------------|
| `app/controllers/v1/users/refinements_controller.rb` | HTTP entry point, param parsing |
| `app/services/candidates/similar_candidates/refinement_service.rb` | Main orchestrator (~650 lines) |
| `app/services/candidates/similar_candidates/embedding_refinement_service.rb` | Vectorial centroid adjustment |
| `app/services/candidates/similar_candidates/intent_based_refinement_service.rb` | LLM intent extraction + embedding blend |
| `app/services/candidates/similar_candidates/text_search_service.rb` | Elasticsearch search via Searchkick |
| `app/services/candidates/similar_candidates/rank_fusion_service.rb` | RRF algorithm with interleaving |
| `app/services/candidates/similar_candidates/feedback_analyzer_service.rb` | Feedback pattern analysis (LLM) |
| `app/services/gemini_client.rb` | Gemini API wrapper |
| `app/services/embeddings/encoder.rb` | Text → embedding vector |

---

## 3. API Entry Point

### Route

```
POST /v1/sourcings/:sourcing_id/refinements
```

Defined in `config/routes.rb`:
```ruby
resources :sourcings, only: [ :index, :show, :create, :update ] do
  resources :refinements, only: [ :create ]
end
```

### Request Body

```json
{
  "liked_candidate_ids": [123, 456],
  "disliked_feedbacks": [
    { "candidate_id": 789, "reason": "nao sabe ruby" },
    { "candidate_id": 101, "reason": "nao sabe rails" }
  ],
  "sources": ["local"],
  "limit": 20
}
```

### Controller

```ruby
# app/controllers/v1/users/refinements_controller.rb

def create
  service = Candidates::SimilarCandidates::RefinementService.new(
    account: @current_user.account,
    user: @current_user
  )

  result = service.call(
    sourcing: @sourcing,
    liked_candidate_ids: Array(params[:liked_candidate_ids]).map(&:to_i),
    disliked_feedbacks: parse_disliked_feedbacks,
    sources: Array(params[:sources] || ["local"]),
    limit: (params[:limit] || 20).to_i.clamp(1, 50)
  )

  render json: result, status: :ok
end
```

**What happens:** The controller authenticates the user, loads the sourcing, parses params, and delegates everything to `RefinementService#call`.

---

## 4. Complete Request Flow

The `RefinementService#call` method orchestrates the entire pipeline in this exact order:

```ruby
def call(sourcing:, liked_candidate_ids: [], disliked_feedbacks: [], sources: ["local"], limit: DEFAULT_LIMIT, use_intent_refinement: true)
  # 1. Validate inputs
  validate!(sourcing, liked_candidate_ids, disliked_feedbacks)

  # 2. Load sourcing context (base candidates, embeddings, threshold)
  context = load_sourcing_context(sourcing)

  # 3. Persist feedback to database
  save_feedbacks(sourcing, liked_candidate_ids, disliked_feedbacks, context[:job_id])

  # 4. Refine embedding (vectorial + intent)
  refinement_result = refine_embedding(...)

  # 5. Analyze feedback patterns (LLM, only if 2+ dislikes)
  feedback_analysis = analyze_feedback(...)

  # 6. Build exclude list
  all_exclude_ids = build_exclude_ids(...)

  # 7. Hybrid search (vector + text + RRF)
  new_results = hybrid_search(...)

  # 8. Recompute existing candidate similarities
  updated_existing = recompute_existing_similarities(...)

  # 9. Create sourced profiles for new results
  new_enriched = process_new_results(...)

  # 10. Update sourcing metadata
  update_sourcing_metadata(...)

  # 11. Build and return response
  build_response(...)
end
```

---

## 5. Phase 1 — Validation & Context Loading

### Validation (`validate!`)

The system validates three conditions before proceeding:

```ruby
def validate!(sourcing, liked_ids, disliked_feedbacks)
  # 1. Sourcing must be a similarity search
  unless sourcing.parameters&.dig("search_type") == "similarity"
    raise ArgumentError, "Sourcing #{sourcing.id} is not a similarity search"
  end

  # 2. At least one feedback required
  if liked_ids.empty? && disliked_feedbacks.empty?
    raise ArgumentError, "At least 1 like or 1 dislike is required"
  end

  # 3. All candidate IDs must belong to the sourcing
  sourcing_candidate_ids = SourcedProfileSourcing
    .where(sourcing_id: sourcing.id, is_deleted: false)
    .joins(:sourced_profile)
    .pluck("sourced_profiles.candidate_id")

  invalid = all_feedback_ids - sourcing_candidate_ids
  if invalid.any?
    raise ArgumentError, "Candidates #{invalid} do not belong to Sourcing #{sourcing.id}"
  end

  # 4. Every dislike must have a reason
  disliked_feedbacks.each do |df|
    if df[:reason].blank?
      raise ArgumentError, "Reason is required for dislike of candidate #{df[:candidate_id]}"
    end
  end
end
```

**When it fails:** Returns HTTP 422 with error message.

### Context Loading (`load_sourcing_context`)

Loads everything needed for the refinement:

```ruby
def load_sourcing_context(sourcing)
  base_candidate_ids = sourcing.parameters["base_candidate_ids"]
  threshold = sourcing.search_metadata&.dig("threshold") || 0.60
  base_candidates = Candidate.where(id: base_candidate_ids, account_id: @account.id)
  original_embedding = compute_centroid(base_candidate_ids)  # Average of base embeddings

  {
    base_candidate_ids: base_candidate_ids,
    base_candidates: base_candidates,
    job_id: sourcing.parameters["job_id"],
    threshold: threshold,
    original_embedding: original_embedding
  }
end
```

**What `compute_centroid` does:** Fetches the 768-dimensional embedding vectors for all base candidates from the `embeddings` table and averages them element-wise. This centroid represents the "center point" of the profile the recruiter is searching for.

```ruby
def compute_centroid(candidate_ids)
  vectors = Embedding
    .where(reference_type: "Candidate", reference_id: candidate_ids)
    .pluck(:embedding)

  return vectors.first if vectors.size == 1

  dims = vectors.first.size  # 768
  centroid = Array.new(dims, 0.0)
  vectors.each { |vec| vec.each_with_index { |v, i| centroid[i] += v } }
  centroid.map { |v| v / vectors.size }
end
```

---

## 6. Phase 2 — Feedback Persistence

Before any search happens, all feedback is saved to the `candidate_feedbacks` table:

```ruby
def save_feedbacks(sourcing, liked_ids, disliked_feedbacks, job_id)
  liked_ids.each { |id| create_feedback(sourcing:, candidate_id: id, feedback_type: "like", ...) }
  disliked_feedbacks.each { |df| create_feedback(sourcing:, candidate_id: df[:candidate_id], feedback_type: "dislike", reason: df[:reason], ...) }
end
```

**Upsert behavior:** If a feedback already exists for the same (sourcing, candidate, user), it updates instead of creating a duplicate. This allows a recruiter to change their mind (e.g., unlike a previously liked candidate).

```ruby
def create_feedback(sourcing:, candidate_id:, feedback_type:, reason:, job_id:)
  existing = CandidateFeedback.find_by(
    sourcing_id: sourcing.id,
    candidate_id: candidate_id,
    user_id: @user.id
  )

  if existing
    existing.update!(feedback_type: feedback_type, reason: reason)
  else
    CandidateFeedback.create!(
      sourcing_id: sourcing.id,
      candidate_id: candidate_id,
      feedback_type: feedback_type,
      reason: reason,
      candidate_score_snapshot: { ... },  # Snapshot for audit
      search_query_snapshot: { sourcing_query: sourcing.query, refinement: true }
    )
  end
end
```

---

## 7. Phase 3 — Vectorial Embedding Refinement

The `refine_embedding` method orchestrates two sub-services:

```ruby
def refine_embedding(original_centroid:, liked_ids:, disliked_ids:, disliked_feedbacks:, base_candidates:, use_intent: true)
  # Step 1: Vectorial adjustment (always runs)
  vectorial_service = EmbeddingRefinementService.new(original_centroid: original_centroid)
  vectorial_refined = vectorial_service.refine(liked_ids: liked_ids, disliked_ids: disliked_ids)

  # Step 2: Intent refinement (only if dislikes exist with reasons)
  return { embedding: vectorial_refined, intent_result: nil } unless use_intent && disliked_feedbacks.any?

  intent_service = IntentBasedRefinementService.new
  intent_result = intent_service.refine_with_intent(
    original_centroid: original_centroid,
    vectorial_refined: vectorial_refined,
    base_candidates: base_candidates,
    disliked_feedbacks: disliked_feedbacks,
    liked_candidates: liked_candidates
  )

  { embedding: intent_result.embedding, intent_result: intent_result }
end
```

### EmbeddingRefinementService

This service adjusts the original centroid vector by pulling it towards liked candidates and pushing it away from disliked candidates.

```ruby
# app/services/candidates/similar_candidates/embedding_refinement_service.rb

ALPHA = 0.3  # Attraction weight (likes)
BETA  = 0.2  # Repulsion weight (dislikes)
```

**Algorithm:**

1. Compute centroid of liked candidates' embeddings → `liked_centroid`
2. Compute centroid of disliked candidates' embeddings → `disliked_centroid`
3. Apply adjustments:

```ruby
def apply_vector_adjustment(vector, target_centroid, weight)
  adjusted = vector.dup
  @dims.times { |i| adjusted[i] += weight * (target_centroid[i] - @original[i]) }
  adjusted
end
```

**Formula:**

$$\vec{v}_{refined} = \vec{v}_{original} + \alpha \cdot (\vec{c}_{liked} - \vec{v}_{original}) - \beta \cdot (\vec{c}_{disliked} - \vec{v}_{original})$$

Where:
- $\alpha = 0.3$ — strength of attraction towards liked candidates
- $\beta = 0.2$ — strength of repulsion from disliked candidates
- $\vec{c}_{liked}$ — centroid of liked candidates' embeddings
- $\vec{c}_{disliked}$ — centroid of disliked candidates' embeddings

4. Normalize the result to unit magnitude:

```ruby
def normalize(vector)
  magnitude = Math.sqrt(vector.sum { |v| v**2 })
  return vector if magnitude.zero?
  vector.map { |v| v / magnitude }
end
```

**Result:** A 768-dimensional vector shifted towards what the recruiter likes and away from what they dislike. This is the `vectorial_refined` embedding.

---

## 8. Phase 4 — LLM Intent Extraction

The `IntentBasedRefinementService` uses a Gemini LLM to understand the recruiter's **hidden intent** behind dislike reasons. This is the most critical phase for bridging the gap between embedding spaces.

### When it runs

It runs only when there are disliked feedbacks with text reasons (not empty strings).

### Flow

```
disliked_feedbacks
       │
       ▼
build_extraction_prompt()  ← combines base candidates, dislikes, likes
       │
       ▼
call_llm()  ← Gemini 2.5 Flash, temperature=0.2, max_tokens=4096
       │
       ▼
parse_structured_response()
       │
       ├── description present + searchable → blend embedding
       │                                        │
       │                                        ▼
       │                              generate_embedding(description)
       │                                        │
       │                                        ▼
       │                              blend_embeddings(vectorial, intent)
       │                                        │
       │                                        ▼
       │                              IntentResult(skipped: false)
       │
       └── all not_searchable → IntentResult(skipped: true)
```

### The LLM Prompt

The system prompt classifies feedback into two categories:

**SEARCHABLE** — things that appear in resumes and can be used for search:
- Skills, programming languages, spoken languages, seniority level
- Leadership, domain expertise, tech stack, certifications

**NOT_SEARCHABLE** — things that can't be found in a resume:
- Salary, travel, work model (remote/PJ/CLT), cultural fit, availability

The critical instruction for contextualized search:

> The elasticsearch_query MUST combine the base profile (existing skills/role) with the desired improvements.
> Example: base is Java/Spring, dislike "não sabe ruby" → query MUST be "Java Spring Ruby Rails backend senior", NOT just "ruby rails".

### User Prompt

```ruby
def build_extraction_prompt(base_candidates:, disliked_feedbacks:, liked_candidates:)
  <<~PROMPT
    BASE CANDIDATES (recruiter started search with these):
    #{format_candidates(base_candidates)}

    REJECTED CANDIDATES (with reasons):
    #{format_disliked_feedbacks(disliked_feedbacks)}

    LIKED CANDIDATES:
    #{format_liked_candidates(liked_candidates)}

    Based on this feedback:
    1. Describe the IDEAL candidate combining the base profile with desired improvements.
    2. Generate an elasticsearch_query that combines base skills + desired skills.
    3. List must_have_skills and nice_to_have_skills.
    4. Classify each feedback as SEARCHABLE or NOT_SEARCHABLE.
    5. If ALL feedback is not_searchable, set description and query to "".
  PROMPT
end
```

### LLM Response (parsed JSON)

```json
{
  "ideal_candidate_description": "A Software Engineer with strong Java and Spring backend experience, who also possesses Ruby on Rails skills.",
  "elasticsearch_query": "Java Spring Ruby Rails backend API REST SQL AWS Python",
  "must_have_skills": ["ruby", "rails"],
  "nice_to_have_skills": ["java", "spring", "aws", "python"],
  "searchable_attributes": ["ruby", "rails"],
  "not_searchable_feedback": []
}
```

### Intent Embedding Blending

When the LLM returns a valid `ideal_candidate_description`, the system:

1. **Generates an embedding** from the description text using `Embeddings::Encoder` (Gemini embedding model, 768 dims)
2. **Blends** the vectorial-refined embedding with the intent embedding using weight $\gamma = 0.25$:

```ruby
def blend_embeddings(vectorial_refined, intent_embedding)
  vec_normalized = normalize(vectorial_refined)
  intent_normalized = normalize(intent_embedding)
  blended = blend_vectors(vec_normalized, intent_normalized)
  normalize(blended)
end

def blend_vectors(vec1, vec2)
  dims = vec1.size
  Array.new(dims) { |i| (1 - GAMMA) * vec1[i] + GAMMA * vec2[i] }
end
```

**Formula:**

$$\vec{v}_{final} = \text{normalize}\Big((1 - \gamma) \cdot \hat{v}_{vectorial} + \gamma \cdot \hat{v}_{intent}\Big)$$

Where $\gamma = 0.25$.

### IntentResult Struct

The output is an `IntentResult` struct containing everything downstream services need:

```ruby
IntentResult = Struct.new(
  :embedding,                # 768-dim blended vector
  :description,              # "A Software Engineer with Java + Ruby..."
  :elasticsearch_query,      # "Java Spring Ruby Rails backend..."
  :must_have_skills,         # ["ruby", "rails"]
  :nice_to_have_skills,      # ["java", "spring", "aws"]
  :searchable_attributes,    # ["ruby", "rails"]
  :not_searchable_feedback,  # [{"feedback": "pretensão alta", "type": "salary"}]
  :skipped,                  # false = intent was applied
  keyword_init: true
)
```

### When intent is skipped

Intent blending is **skipped** (returns `skipped: true`) in these cases:

| Condition | Why |
|-----------|-----|
| No disliked feedbacks | Nothing to extract intent from |
| LLM call fails | Graceful fallback to vectorial-only |
| All feedback is NOT_SEARCHABLE | e.g., "salary too high", "can't travel" — nothing to embed |
| Embedding generation fails | Fallback to vectorial-only |
| `ideal_candidate_description` is blank | No searchable signal found |

When skipped, the system uses the `vectorial_refined` embedding as-is.

---

## 9. Phase 5 — Hybrid Search (Vector + Elasticsearch + RRF)

This is where the magic happens. The system runs **two parallel search strategies** and fuses them.

### Hybrid Search Orchestration

```ruby
def hybrid_search(embedding:, intent_result:, exclude_ids:, limit:, threshold:)
  # Step 1: Vector search — always runs
  vector_pool = [limit * POOL_MULTIPLIER, MIN_POOL_SIZE].max  # min 60
  vector_results = search_with_refined_embedding(
    embedding: embedding,
    exclude_ids: exclude_ids,
    limit: vector_pool,
    threshold: threshold
  )

  # Step 2: Check if text search should run
  return vector_results.first(limit) unless should_run_text_search?(intent_result)

  # Step 3: Elasticsearch text search
  text_results = run_text_search(intent_result:, exclude_ids:, limit:)
  return vector_results.first(limit) if text_results.empty?

  # Step 4: Fuse with RRF
  fused = RankFusionService.new.fuse(
    vector_results: vector_results,
    text_results: text_results,
    limit: limit
  )

  fused.map { |r| { candidate_id: r[:candidate_id], similarity: r[:similarity], source: r[:source], rrf_score: r[:rrf_score] } }
end
```

### When text search runs

```ruby
def should_run_text_search?(intent_result)
  return false unless intent_result           # No intent = no text search
  return false if intent_result.skipped       # Intent was skipped = no text search
  intent_result.elasticsearch_query.present?  # Need a query to search
end
```

**Decision flow:**

```
intent_result nil? ─── YES ──→ vector-only search
        │ NO
        ▼
intent_result.skipped? ─── YES ──→ vector-only search
        │ NO
        ▼
elasticsearch_query blank? ─── YES ──→ vector-only search
        │ NO
        ▼
Run text search + RRF fusion
```

### Vector Search (pgvector)

Uses PostgreSQL's pgvector extension with cosine distance:

```ruby
def search_with_refined_embedding(embedding:, exclude_ids:, limit:, threshold:)
  pool_size = [limit * POOL_MULTIPLIER, MIN_POOL_SIZE].max  # 60

  results = Embedding
    .where(reference_type: "Candidate")
    .where.not(reference_id: exclude_ids)
    .nearest_neighbors(:embedding, embedding, distance: "cosine")
    .limit(pool_size)

  # Filter by tenant (multi-tenancy)
  tenant_ids = Candidate
    .where(account_id: @account.id, is_deleted: false)
    .where(id: results.map(&:reference_id))
    .pluck(:id).to_set

  results
    .select { |emb| tenant_ids.include?(emb.reference_id) }
    .map { |emb| { candidate_id: emb.reference_id, similarity: (1.0 - emb.neighbor_distance).clamp(0.0, 1.0) } }
    .select { |r| r[:similarity] >= threshold }
    .first(limit)
end
```

**Pool size:** Fetches `3x limit` or minimum 60 candidates from pgvector, then filters by tenant and threshold. This over-fetching ensures we have enough candidates after tenant filtering.

### Text Search (Elasticsearch via Searchkick)

```ruby
# app/services/candidates/similar_candidates/text_search_service.rb

DEFAULT_FIELDS = [
  "skills^10",              # Highest priority
  "role_name^8",            # Job title
  "curriculum_summary^7",   # Summary text
  "experiences_a^6",        # Experience descriptions
  "recent_roles^6",         # Recent job titles
  "current_company^4",      # Company name
  "all_companies^3"         # All past companies
].freeze

def search(query:, exclude_ids: [], must_have_skills: [], limit: DEFAULT_LIMIT)
  return [] if query.blank?

  options = {
    fields: DEFAULT_FIELDS,
    where: { account_id: @account_id, is_deleted: [false, nil], id: { not: exclude_ids } },
    limit: limit,
    operator: "or",
    misspellings: { below: 3 }
  }

  results = Candidate.search(query, **options)

  scored_results = results.map.with_index do |candidate, index|
    {
      candidate_id: candidate.id,
      similarity: compute_normalized_score(results, index),
      source: :text
    }
  end

  boost_must_have_skills(scored_results, must_have_skills)
end
```

**Key design decisions:**
- `operator: "or"` — matches candidates containing ANY of the terms (not all)
- `skills^10` — skills have highest boost factor
- `must_have_skills` boosting — after initial ES ranking, re-sorts to prioritize candidates who actually have the must-have skills

**Must-have boosting:**

```ruby
def boost_must_have_skills(results, must_have_skills)
  return results if must_have_skills.empty?

  results.each do |result|
    candidate = candidates[result[:candidate_id]]
    next unless candidate
    result[:must_have_match] = skill_match_ratio(candidate, must_have_skills)
  end

  # Sort by must_have match first, then ES score
  results.sort_by { |r| [-(r[:must_have_match] || 0), -(r[:similarity] || 0)] }
end
```

This ensures that a candidate with `ruby` AND `rails` (match ratio = 1.0) ranks above a candidate with only `java spring` (match ratio = 0.0), even if the latter has a higher ES text score.

### Reciprocal Rank Fusion (RRF)

```ruby
# app/services/candidates/similar_candidates/rank_fusion_service.rb

DEFAULT_K = 60
DEFAULT_VECTOR_WEIGHT = 0.6
DEFAULT_TEXT_WEIGHT = 0.4
MIN_TEXT_RATIO = 0.3
```

**Algorithm:**

For each candidate appearing in either result set:

$$score(d) = \sum_{i} \frac{w_i}{k + rank_i(d)}$$

Where:
- $k = 60$ (smoothing constant)
- $w_{vector} = 0.6$ (vector search weight)
- $w_{text} = 0.4$ (text search weight)
- $rank_i(d)$ = candidate's rank in source $i$ (1-indexed)

**Example scores:**

| Candidate | Vector Rank | Text Rank | RRF Score |
|-----------|-------------|-----------|-----------|
| Both (rank 1 + 1) | 1 | 1 | $\frac{0.6}{61} + \frac{0.4}{61} = 0.01639$ |
| Vector only (rank 1) | 1 | — | $\frac{0.6}{61} = 0.00984$ |
| Text only (rank 1) | — | 1 | $\frac{0.4}{61} = 0.00656$ |

Candidates appearing in **both** sources always rank highest.

### Interleaving Guarantee

Pure RRF with asymmetric weights (0.6 vs 0.4) would always rank vector-only above text-only when there's no overlap. To guarantee the recruiter sees text search results (which contain the skills they asked for), the system uses interleaving:

```ruby
def interleave(scored, limit)
  both, rest = scored.partition { |r| r[:source] == :both }
  text_only = rest.select { |r| r[:source] == :text }.sort_by { |r| -r[:rrf_score] }
  vector_only = rest.select { |r| r[:source] == :vector }.sort_by { |r| -r[:rrf_score] }

  both_sorted = both.sort_by { |r| -r[:rrf_score] }
  return (both_sorted + vector_only + text_only).first(limit) if text_only.empty?

  remaining = limit - both_sorted.size
  return both_sorted.first(limit) if remaining <= 0

  min_text = (remaining * MIN_TEXT_RATIO).ceil  # 30% of remaining slots
  text_slots = [min_text, text_only.size].min
  vector_slots = remaining - text_slots

  both_sorted
    .concat(vector_only.first(vector_slots))
    .concat(text_only.first(text_slots))
    .first(limit)
end
```

**Priority order:**
1. **:both** — candidates found in both sources (always first)
2. **:vector** — candidates from pgvector (70% of remaining slots)
3. **:text** — candidates from Elasticsearch (**guaranteed minimum 30%** of remaining slots)

**Example with limit=10:**

| Source | Slot Allocation |
|--------|----------------|
| Both (0 candidates) | 0 slots |
| Vector only | 7 slots (70% of 10) |
| Text only | 3 slots (30% of 10) |

This ensures the recruiter always sees text search candidates — the ones that actually have Ruby/Rails skills that pure vector search could never find.

---

## 10. Phase 6 — Results Assembly & Response

### Recompute Existing Similarities

All previously sourced candidates get their similarity scores recomputed against the new refined embedding:

```ruby
def recompute_existing_similarities(sourcing:, refined_embedding:, disliked_ids:)
  existing_sps = SourcedProfileSourcing
    .where(sourcing_id: sourcing.id, is_deleted: false)
    .joins(:sourced_profile).includes(:sourced_profile)

  existing_sps.filter_map do |sps|
    candidate_id = sps.sourced_profile.candidate_id
    next if disliked_ids.include?(candidate_id)

    embedding_record = Embedding.find_by(reference_type: "Candidate", reference_id: candidate_id)
    next unless embedding_record

    new_distance = cosine_distance(refined_embedding, embedding_record.embedding)
    new_similarity = (1.0 - new_distance).clamp(0.0, 1.0)
    new_similarity_pct = (new_similarity * 100).round(1)

    old_similarity_pct = sps.similarity_score
    if old_similarity_pct != new_similarity_pct
      sps.update_column(:similarity_score, new_similarity_pct)
      sps.update_column(:search_score, new_similarity)
    end

    {
      candidate_id: candidate_id,
      similarity_score: new_similarity_pct,
      previous_similarity_score: old_similarity_pct,
      score_changed: old_similarity_pct != new_similarity_pct,
      status: "existing"
    }
  end
end
```

**What this does:** As the embedding shifts, previously "good" candidates might now be less similar (they were similar to the disliked profile), while others might improve. The system re-ranks everything.

### Process New Results

Creates `SourcedProfile` and `SourcedProfileSourcing` records for every new candidate found:

```ruby
def process_new_results(results:, base_candidates:, sourcing:)
  results.filter_map do |result|
    candidate = candidates[result[:candidate_id]]
    next unless candidate

    profile = create_or_link_sourced_profile(candidate, sourcing, result[:similarity])
    shared = extract_shared_signals(base_candidates, candidate)

    {
      candidate_id: candidate.id,
      name: candidate.name,
      similarity_score: (result[:similarity] * 100).round(1),
      shared_signals: shared,  # Common terms between base and new candidate
      status: "new"
    }
  end
end
```

### Exclude IDs

The system excludes these candidates from appearing in results:

```ruby
def build_exclude_ids(context:, sourcing:, disliked_ids:)
  ids = context[:base_candidate_ids].dup     # Base candidates
  ids += disliked_ids                         # Disliked candidates

  if context[:job_id].present?
    ids += Apply.where(job_id: context[:job_id]).pluck(:candidate_id)  # Already applied
  end

  ids += SourcedProfileSourcing
    .where(sourcing_id: sourcing.id):
    .pluck("sourced_profiles.candidate_id")   # Already in sourcing

  ids.uniq
end
```

### Metadata Update

Each refinement round is tracked:

```ruby
def update_sourcing_metadata(sourcing:, new_count:, duration:, feedback_analysis:)
  refinements = current_meta["refinements"] || []

  refinements << {
    round: refinements.size + 1,
    timestamp: Time.current.iso8601,
    new_candidates_found: new_count,
    duration_ms: duration,
    feedback_analysis: feedback_analysis&.slice(:desired_profile, :rejection_patterns)
  }

  sourcing.update!(
    results_count: sourcing.results_count + new_count,
    search_metadata: current_meta.merge(
      "refinements" => refinements,
      "last_refined_at" => Time.current.iso8601,
      "total_refinement_rounds" => refinements.size
    )
  )
end
```

---

## 11. Feedback Analyzer (Parallel)

When there are 2+ dislikes, the `FeedbackAnalyzerService` runs an independent LLM call to analyze patterns. This is **not** part of the search pipeline — it provides supplementary information in the response.

```ruby
def analyze_feedback(context:, liked_ids:, disliked_feedbacks:)
  return nil if disliked_feedbacks.size < 2

  FeedbackAnalyzerService.new.analyze(
    base_candidates: context[:base_candidates],
    liked_candidates: Candidate.where(id: liked_ids),
    dislike_feedbacks: dislikes_with_candidates
  )
end
```

The analyzer uses a 3-second timeout and returns:

```json
{
  "desired_profile": "Backend engineer with Java + Ruby experience",
  "rejection_patterns": ["Lacks Ruby/Rails skills"],
  "positive_patterns": ["Strong Java/Spring background, AWS certified"],
  "explanation": "The recruiter wants Java developers who also know Ruby"
}
```

---

## 12. Mathematical Formulas

### Centroid Calculation

$$\vec{c} = \frac{1}{n} \sum_{i=1}^{n} \vec{e}_i$$

### Vectorial Refinement

$$\vec{v}_{refined} = \text{normalize}\Big(\vec{v}_{original} + 0.3 \cdot (\vec{c}_{liked} - \vec{v}_{original}) - 0.2 \cdot (\vec{c}_{disliked} - \vec{v}_{original})\Big)$$

### Intent Blending

$$\vec{v}_{final} = \text{normalize}\Big(0.75 \cdot \hat{v}_{vectorial} + 0.25 \cdot \hat{v}_{intent}\Big)$$

### Cosine Similarity

$$sim(\vec{a}, \vec{b}) = 1 - \frac{\vec{a} \cdot \vec{b}}{|\vec{a}| \cdot |\vec{b}|}$$

### RRF Score

$$RRF(d) = \frac{0.6}{60 + rank_{vector}(d)} + \frac{0.4}{60 + rank_{text}(d)}$$

### Normalization

$$\hat{v} = \frac{\vec{v}}{|\vec{v}|} = \frac{\vec{v}}{\sqrt{\sum_i v_i^2}}$$

---

## 13. Configuration Constants

| Constant | Value | Service | Purpose |
|----------|-------|---------|---------|
| `ALPHA` | 0.3 | EmbeddingRefinementService | Like attraction weight |
| `BETA` | 0.2 | EmbeddingRefinementService | Dislike repulsion weight |
| `GAMMA` | 0.25 | IntentBasedRefinementService | Intent blending weight |
| `DEFAULT_K` | 60 | RankFusionService | RRF smoothing constant |
| `DEFAULT_VECTOR_WEIGHT` | 0.6 | RankFusionService | Vector search weight in RRF |
| `DEFAULT_TEXT_WEIGHT` | 0.4 | RankFusionService | Text search weight in RRF |
| `MIN_TEXT_RATIO` | 0.3 | RankFusionService | Minimum text result guarantee |
| `POOL_MULTIPLIER` | 3 | RefinementService | Over-fetch factor for pgvector |
| `MIN_POOL_SIZE` | 60 | RefinementService | Minimum pgvector fetch count |
| `DEFAULT_THRESHOLD` | 0.60 | RefinementService | Minimum cosine similarity |
| `MAX_SKILLS_TO_EXTRACT` | 15 | IntentBasedRefinementService | Skills per candidate in prompt |
| `MAX_SKILLS_TO_SHOW` | 8 | IntentBasedRefinementService | Skills shown in prompt |
| `DEFAULT_LIMIT` | 20 | RefinementService | Default result limit |
| Embedding dimensions | 768 | Embeddings::Encoder | Gemini embedding size |
| LLM model | gemini-2.5-flash | IntentBasedRefinementService | For intent extraction |
| LLM temperature | 0.2 | IntentBasedRefinementService | Low for deterministic JSON |
| LLM max_tokens | 4096 | IntentBasedRefinementService | Accounts for thinking tokens |

---

## 14. Decision Tree Summary

```
Request arrives at POST /v1/sourcings/:id/refinements
│
├── Validate (search_type=similarity, feedback exists, candidates valid)
│   └── ❌ Fail → 422 Unprocessable Entity
│
├── Save feedbacks to DB (upsert)
│
├── VECTORIAL REFINEMENT (always runs)
│   └── centroid + α·(liked - original) - β·(disliked - original)
│
├── INTENT EXTRACTION (if dislikes with reasons exist)
│   ├── LLM classifies feedback → SEARCHABLE vs NOT_SEARCHABLE
│   ├── ALL not_searchable? → skip intent, use vectorial only
│   ├── Has searchable? → generate description → embed → blend with γ=0.25
│   └── Also extracts: elasticsearch_query, must_have_skills, nice_to_have_skills
│
├── HYBRID SEARCH
│   ├── Vector search (pgvector, pool=60, cosine distance) → always
│   ├── elasticsearch_query present?
│   │   ├── NO → return vector-only results
│   │   └── YES → Elasticsearch text search
│   │       └── RRF fusion (k=60, vec=0.6, txt=0.4)
│   │           └── Interleave: both first, then 70% vector / 30% text
│   └── Return top N candidates with source labels
│
├── Recompute existing candidate similarities against new embedding
├── Create SourcedProfile + SourcedProfileSourcing for new candidates
├── Update sourcing metadata (round count, timestamp, stats)
│
└── Return JSON response with all candidates, metadata, intent_analysis
```

---

## 15. Example: Real Scenario (Java → Ruby/Rails)

**Setup:** Sourcing #658, base candidates are Java/Spring developers.

**Request:**
```json
{
  "liked_candidate_ids": [101, 102, 103, 104],
  "disliked_feedbacks": [
    { "candidate_id": 201, "reason": "nao sabe ruby" },
    { "candidate_id": 202, "reason": "nao sabe rails" }
  ]
}
```

### Phase 3 — Vectorial Refinement
- Centroid shifts 0.38% towards liked Java devs, away from disliked
- **Problem:** Java and Ruby occupy distant embedding regions — 0.38% shift is negligible

### Phase 4 — Intent Extraction
- LLM output:
  ```json
  {
    "ideal_candidate_description": "A Software Engineer with strong Java and Spring backend experience, who also possesses Ruby on Rails skills.",
    "elasticsearch_query": "Java Spring Ruby Rails backend API REST SQL AWS Python",
    "must_have_skills": ["ruby", "rails"],
    "nice_to_have_skills": ["java", "spring", "aws", "python"],
    "searchable_attributes": ["ruby", "rails"]
  }
  ```
- Intent embedding generated from description
- Blended with γ=0.25 → centroid shifts 2.0% (5.3x amplification vs vectorial alone)

### Phase 5 — Hybrid Search

**Vector search (pgvector):** Returns 60 Java-adjacent devs. None have Ruby/Rails — the embedding space gap is too large.

**Text search (Elasticsearch):** Searches `"Java Spring Ruby Rails backend API REST SQL AWS Python"` → returns 15 candidates. 11 have both Ruby AND Rails. Boosted by `must_have_skills`.

**RRF Fusion with limit=10:**
- 0 candidates in both sources (no overlap — Java/Ruby embedding gap)
- 7 slots for vector results (70% of 10)
- 3 slots for text results (30% of 10, guaranteed by `MIN_TEXT_RATIO`)

### Results

| # | Candidate | Source | Ruby | Rails | Similarity |
|---|-----------|--------|------|-------|------------|
| 1 | Ramon Santos | text | ✓ | ✓ | 96.5% |
| 2 | Ronaldo Alves | text | ✓ | ✓ | 89.4% |
| 3 | Adriano Santos | vector | ✗ | ✗ | 86.5% |
| 4 | Fábio G. | vector | ✗ | ✗ | 86.9% |
| 5 | Victor Montibeller | vector | ✗ | ✗ | 86.7% |
| ... | ... | vector | ... | ... | ... |
| 8 | Lucas Siqueira | text | ✓ | ✓ | 77.6% |

**Before hybrid search:** 0% Ruby/Rails match in top 10 (pure vector).
**After hybrid search:** 3 candidates with 100% Ruby+Rails match surfaced via Elasticsearch.

---

## 16. API Response Schema

```json
{
  "sourcing_id": 658,
  "sourcing_uid": "abc-123",
  "search_type": "similarity_refined",
  "refinement_round": 1,

  "candidates": [
    {
      "candidate_id": 12345,
      "sourced_profile_id": 67890,
      "name": "Ramon Santos",
      "role_name": "Full Stack Developer",
      "current_company": "TechCo",
      "location": "São Paulo, SP",
      "similarity_score": 96.5,
      "shared_signals": ["java", "spring", "api", "rest"],
      "ai_score": null,
      "status": "new"
    },
    {
      "candidate_id": 11111,
      "sourced_profile_id": 22222,
      "name": "Fábio G.",
      "role_name": "Senior Java Developer",
      "similarity_score": 86.9,
      "previous_similarity_score": 85.7,
      "score_changed": true,
      "status": "existing"
    }
  ],

  "summary": {
    "total": 30,
    "existing_updated": 10,
    "new_found": 20,
    "scores_changed": 8
  },

  "feedback_analysis": {
    "desired_profile": "Backend engineer with Java + Ruby experience",
    "rejection_patterns": ["Lacks Ruby/Rails skills"],
    "positive_patterns": ["Strong Java/Spring background"],
    "explanation": "The recruiter wants Java developers who also know Ruby"
  },

  "intent_analysis": {
    "applied": true,
    "description": "A Software Engineer with strong Java and Spring backend experience, who also possesses Ruby on Rails skills.",
    "elasticsearch_query": "Java Spring Ruby Rails backend API REST SQL AWS Python",
    "must_have_skills": ["ruby", "rails"],
    "nice_to_have_skills": ["java", "spring", "aws", "python"],
    "searchable_attributes": ["ruby", "rails"],
    "not_searchable_feedback": [],
    "hybrid_search": true
  },

  "metadata": {
    "duration_ms": 1523.4,
    "embedding_model": "gemini-embedding-001",
    "refinement_method": "hybrid_rrf",
    "alpha": 0.3,
    "beta": 0.2,
    "gamma": 0.25
  }
}
```

### `refinement_method` Values

| Value | Meaning |
|-------|---------|
| `centroid_adjustment` | Only vectorial refinement (no intent) |
| `centroid_adjustment_with_intent` | Intent applied but no ES query generated (all not_searchable) |
| `hybrid_rrf` | Full hybrid search with vector + Elasticsearch + RRF |

### `status` Values for Candidates

| Value | Meaning |
|-------|---------|
| `new` | Candidate found in this refinement round |
| `existing` | Candidate was already in the sourcing, similarity recomputed |
