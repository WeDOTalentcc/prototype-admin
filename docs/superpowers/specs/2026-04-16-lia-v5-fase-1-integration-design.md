# Design: Integração LIA / recruiter_agent_v5 ↔ ats_api — Fase 1

**Data:** 2026-04-16
**Autor:** Victhor (conversa com Claude Code)
**Status:** Draft para aprovação

---

## 1. Objetivo

Fechar os gaps **P0 (endpoints fantasma)** e **P1 (tools que só precisam de `@tool` nova)** do catálogo LIA × recruiter_agent_v5, reutilizando ao máximo o que já existe no `ats_api`. Trabalho esperado: ~40h.

Fora de escopo: Fase 2/3 (Hiring Policy, Nurture, Skills Ontology, Predictive, Digital Twins completos, Diversity sourcing completo, Internal Mobility, Interview Intelligence, Workforce Planning, Market Intelligence, Recruitment Campaigns aggregator).

---

## 2. Mapeamento semântico confirmado

| Conceito LIA / V5 | Recurso ats_api | Observação |
|---|---|---|
| `talent_pool` | `Sourcing` | Busca persistida; membros = `SourcedProfileSourcing` |
| `talent_pool member` | `SourcedProfile` via `SourcedProfileSourcing` | junction table, suporta score e analysis |
| `opinion` (recruiter → candidato) | `CandidateFeedback` (já existe) | Tool V5 passa a chamar `POST /v1/users/candidate_feedbacks` |
| `profile_analysis` | **novo:** `POST /v1/users/sourced_profiles/:id/analyze` | síntese LLM com cache Redis |
| `capture_wizard_feedback` | `Feedback` (NÃO polymorphic) | usar FKs diretas: `job_id` ou `apply_id` |
| `digital_twin` | `Candidate` com `is_twin: true` + `twin_source_id` | reuso do model Candidate |

---

## 3. Trabalho no `ats_api` (Rails)

### 3.1. Migration — novos campos em `candidates`

```ruby
# db/migrate/YYYYMMDDHHMMSS_add_diversity_lgpd_twin_fields_to_candidates.rb
class AddDiversityLgpdTwinFieldsToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :pcd,             :boolean,  default: false, null: false
    add_column :candidates, :ethnicity,       :integer
    add_column :candidates, :lgbtqia,         :boolean,  default: false, null: false
    add_column :candidates, :neurodivergent,  :boolean,  default: false, null: false
    add_column :candidates, :is_hidden,       :boolean,  default: false, null: false
    add_column :candidates, :lgpd_expires_at, :datetime
    add_column :candidates, :is_twin,         :boolean,  default: false, null: false
    add_column :candidates, :twin_source_id,  :bigint

    add_index :candidates, :pcd
    add_index :candidates, :ethnicity
    add_index :candidates, :is_hidden
    add_index :candidates, :is_twin
    add_index :candidates, :twin_source_id
    add_index :candidates, :lgpd_expires_at
  end
end
```

### 3.2. Updates no model `Candidate`

- `enum ethnicity: { white: 0, black: 1, brown: 2, yellow: 3, indigenous: 4, undeclared: 5 }`
- `belongs_to :twin_source, class_name: "Candidate", optional: true`
- `scope :visible, -> { where(is_hidden: false) }`
- `scope :lgpd_active, -> { where("lgpd_expires_at IS NULL OR lgpd_expires_at > ?", Time.current) }`
- `search_data` (Searchkick): adicionar `pcd`, `ethnicity`, `lgbtqia`, `neurodivergent`, `is_hidden`, `is_twin`, `lgpd_expires_at`

### 3.3. Whitelist `SearchParams`

O concern atual (`app/controllers/concerns/search_params.rb`) normaliza qualquer chave de `where` sem whitelist fixo. Validar que os novos campos passam corretamente: boolean → boolean, integer → integer, datetime → range. Caso haja whitelist implícito, adicionar.

### 3.4. Novo endpoint — `POST /v1/users/sourced_profiles/:id/analyze`

**Objetivo:** entregar análise sintética do perfil via LLM, com cache de 24h.

**Request:**
```
POST /v1/users/sourced_profiles/:id/analyze
```

**Response (200):**
```json
{
  "data": {
    "sourced_profile_id": 123,
    "summary": "Dev sênior Ruby/Rails, 8 anos de experiência em fintech...",
    "skills_analysis": {
      "strong": ["Ruby", "Rails", "PostgreSQL"],
      "moderate": ["Kafka", "Kubernetes"],
      "gaps": ["React", "TypeScript"]
    },
    "fit_score": 0.82,
    "strengths": ["Experiência direta no stack", "Liderança técnica comprovada"],
    "concerns": ["Sem contato recente com front-end"],
    "cached_at": "2026-04-16T10:00:00Z",
    "cache_ttl_seconds": 86400
  },
  "meta": { "source": "llm", "model": "claude-sonnet-4-5" }
}
```

**Implementação:**
- Action `analyze` em `V1::Users::SourcedProfiles::ContactEnrichmentController` **OU** novo `V1::Users::SourcedProfiles::AnalysisController`. Preferência: **novo controller** para não misturar responsabilidades (enrichment vs análise).
- Rota: `resources :sourced_profiles { member { post :analyze, to: "sourced_profiles/analysis#create" } }`
- Serviço `SourcedProfileAnalysisService` chama Claude Sonnet 4.5, recebe `SourcedProfile`, retorna hash.
- Cache: `Rails.cache.fetch("sp_analysis:#{id}", expires_in: 24.hours) { service.call }`.
- Serializer: `SourcedProfileAnalysisSerializer`.

### 3.5. Novo endpoint — `POST /v1/users/sourcings/:id/add_candidate`

**Motivo:** o `SourcingsController` atual não permite adicionar candidato manualmente a um sourcing — só via busca Pearch/LinkedIn. A tool `add_candidate_to_pool` do V5 precisa disso.

**Request:**
```json
POST /v1/users/sourcings/:id/add_candidate
{
  "candidate_id": 456,
  "score": 85,
  "notes": "Indicação manual do recruiter"
}
```

Alternativa aceita: `sourced_profile_id` em vez de `candidate_id`.

**Comportamento:**
1. Se `candidate_id`: procurar/criar `SourcedProfile` associado (ou usar `candidate.sourced_profile_id`).
2. Criar `SourcedProfileSourcing(sourcing_id: :id, sourced_profile_id:, score:, general_comments: notes)`.
3. Retornar `SourcedProfileSourcingSerializer`.

**Idempotência:** se já existir relação com `is_deleted: false`, retornar 200 com o registro existente.

**Rota:**
```ruby
resources :sourcings do
  member do
    post :add_candidate
    # ...demais members existentes
  end
end
```

### 3.6. Request specs (RSpec)

Todos em `spec/requests/v1/users/`:

- `candidates_filter_diversity_spec.rb` — testa `where={pcd:true}`, `where={ethnicity:"black"}`, `aggs=ethnicity,pcd,lgbtqia`.
- `candidates_hidden_spec.rb` — testa scope `visible` e filtro `is_hidden`.
- `candidates_twin_spec.rb` — testa criação com `is_twin: true, twin_source_id: X`.
- `sourced_profiles_analyze_spec.rb` — testa análise + cache hit.
- `sourcings_add_candidate_spec.rb` — testa add + idempotência.
- `candidate_feedbacks_spec.rb` — smoke test para garantir payload que o V5 vai mandar (já existe controller; só validar contract).

### 3.7. Reindex Searchkick

Após migration aplicada em prod, rodar `Candidate.reindex` em background (job). Em dev/staging, síncrono.

---

## 4. Trabalho no `recruiter_agent_v5` (Python)

### 4.1. Corrigir `talent_pool.py` (7 tools fantasma → `/v1/users/sourcings/*`)

| Tool V5 | Endpoint final | Nota |
|---|---|---|
| `search_talent_pools` | `GET /v1/users/sourcings?where={saved:true}` | filtra persistidas |
| `create_talent_pool` | `POST /v1/users/sourcings` | passar `saved: true` |
| `get_talent_pool` | `GET /v1/users/sourcings/:id` | |
| `add_candidate_to_pool` | `POST /v1/users/sourcings/:id/add_candidate` | **endpoint novo** |
| `remove_from_pool` | `PUT /v1/users/sourcings/:id` com body excluindo — **ou** soft-delete da relação `sourced_profile_sourcing` (verificar se existe endpoint; se não, adicionar DELETE na seção 3.5) | confirmar na implementação |
| `get_pool_metrics` | `GET /v1/users/sourcings/:id/stats` | |
| `list_pool_members` | `GET /v1/users/sourcings/:id` (inclui top_profiles) **ou** novo collection | |

### 4.2. Adicionar 18 tools P1 no V5

Cada uma vira `@tool` no módulo apropriado (`autonomous/tools/` ou `domains/<domain>/tools/`). Chamam endpoints que já existem.

| # | Tool | Endpoint | Módulo V5 |
|---|---|---|---|
| 1 | `get_candidate_wsi_scores` | `GET /v1/users/evaluation_candidates?where={candidate_id:X,wsi:true}` | candidates |
| 2 | `get_candidate_screening_results` | `GET /v1/users/evaluation_candidates?where={candidate_id:X}` | candidates |
| 3 | `get_stage_sub_statuses` | `GET /v1/users/apply_statuses` | applies |
| 4 | `get_interview_details` | `GET /v1/users/meetings/:id` | meetings |
| 5 | `view_interview_notes` | `GET /v1/users/meetings?where={candidate_id:X}` | meetings |
| 6 | `get_candidate_aging` | `GET /v1/users/applies/aging` | applies |
| 7 | `get_at_risk_candidates` | `GET /v1/users/applies/aging?where={stage_days_gt:30}` | applies |
| 8 | `find_silver_medalists` | `GET /v1/users/applies?where={status:"rejected",score_gte:70}` | applies |
| 9 | `get_recruiter_preferences` | `GET /v1/users/notification_preferences` | user |
| 10 | `save_recruiter_preference` | `PUT /v1/users/notification_preferences` | user |
| 11 | `add_notes` | `POST /v1/users/messages` (polymorphic Candidate) | candidates |
| 12 | `send_outreach` | `POST /v1/users/email_templates/send` (HITL) | communication |
| 13 | `generate_message` | `POST /v1/users/email_templates/generate_suggestion` | communication |
| 14 | `enrich_candidate_contact` | `POST /v1/users/sourced_profiles/:id/enrich_emails` + `/enrich_phones` | sourcing |
| 15 | `enrich_candidate_profile` | `POST /v1/users/sourced_profiles/:id/enrich_contacts` | sourcing |
| 16 | `generate_interview_opinion` | `POST /v1/users/candidate_feedbacks` | evaluations |
| 17 | `get_activity_summary` | `GET /v1/users/activity_logs` | analytics |
| 18 | `capture_wizard_feedback` | `POST /v1/users/feedbacks` (com `job_id` ou `apply_id`, NÃO polymorphic) | wizard |

**Extra (consequência da Fase 1):**
- `analyze_profile` → `POST /v1/users/sourced_profiles/:id/analyze` (endpoint novo)
- `rag_search` → `GET /v1/users/candidates/prompt_search`

Total: **20 tools novas** + **7 corrigidas**.

### 4.3. Padrões obrigatórios em cada tool V5

- `@tool` com docstring em pt-BR: quando usar / quando NÃO usar.
- Args tipados + defaults.
- Chama via `api.search` / `api.get` / `api.create` / `api.update` (nunca `requests` direto).
- Retorno via `_fmt(...)` para compressão.
- Registrada em `TOOL_CATEGORIES` + regex em `_CATEGORY_PATTERNS` se categoria nova.
- Se ação write de alto impacto → `requires_confirmation=True` no `DomainAction`.
- Se toca dado sensível (reject / salário / diversity) → passa por FairnessGuard.
- Teste em `tests/test_<category>_domain.py` com mock do API client.

---

## 5. Ordem de execução sugerida

1. **PR 1 (Rails):** migration + model updates + Searchkick + whitelist + specs do Candidate. Reindex em staging.
2. **PR 2 (Rails):** endpoint `sourced_profiles/analyze` + service LLM + specs.
3. **PR 3 (Rails):** endpoint `sourcings/add_candidate` + specs.
4. **PR 4 (V5):** correção de `talent_pool.py` (7 tools fantasma).
5. **PR 5 (V5):** adição das 18 tools P1 novas + `analyze_profile` + `rag_search`.
6. **PR 6 (V5):** smoke tests por categoria.

Cada PR independente — V5 depende do ats_api para smoke; portanto ats_api primeiro em cada domínio (ex: PR 3 antes de talent_pool V5).

---

## 6. Testes (cobertura mínima)

**Rails (`spec/requests/v1/users/`):**
- 6 request specs novos (seção 3.6).
- Factory updates: `candidate` factory ganha traits `:pcd`, `:hidden`, `:twin`.

**Python (`tests/`):**
- Smoke test por tool nova — mock do client HTTP, valida URL + payload + parsing do response.
- Teste de `requires_confirmation` para tools HITL (`send_outreach`, `save_recruiter_preference`, `add_candidate_to_pool`).

---

## 7. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Reindex Candidate em produção (tabela grande) pode demorar | Rodar em Sidekiq background, monitorar com `Searchkick::ReindexV2Job` |
| LGPD — `lgpd_expires_at` precisa de job para anonimizar expirados | Fora do escopo da Fase 1; documentar como follow-up |
| Tool `remove_from_pool` pode exigir endpoint adicional (DELETE) | Confirmar na implementação; se sim, adicionar PR 3 extendido |
| Diversity fields precisam consentimento LGPD explícito na UI | Backend aceita valores; consentimento tratado no front (fora do escopo) |
| Cache Redis de analyze pode ficar stale após enrich | Invalidar em `SourcedProfile#after_update` se campos-chave mudarem |

---

## 8. Critérios de aceite

- [ ] Migration aplicada, `schema.rb` atualizado, reindex OK.
- [ ] `GET /v1/users/candidates?where={pcd:true}&aggs=ethnicity` retorna filtro + facets.
- [ ] `POST /v1/users/sourced_profiles/:id/analyze` retorna estrutura da seção 3.4; segundo request em <24h vem do cache.
- [ ] `POST /v1/users/sourcings/:id/add_candidate` cria `SourcedProfileSourcing` e é idempotente.
- [ ] 7 tools de `talent_pool.py` rodam ponta-a-ponta contra o `ats_api` real (smoke).
- [ ] 18+ tools P1 novas rodam ponta-a-ponta.
- [ ] Cobertura de specs ≥30% (gate do projeto).
- [ ] Nenhum teste existente quebrado.

---

## 9. Out of scope (próximas fases)

- **Fase 2:** Market Intelligence, Skills Ontology, Workforce Planning, Interview Intelligence, Internal Mobility, Recruitment Campaigns aggregator.
- **Fase 3:** Hiring Policy, Nurture Sequences, Predictive Analytics (ML).
- Frontend changes (Next.js / plataforma-lia).
- Job LGPD para anonimização automática ao `lgpd_expires_at`.
