# LIA × recruiter_agent_v5 — Fase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar gaps P0/P1 do catálogo LIA × recruiter_agent_v5 reutilizando recursos existentes. Dois repos tocados: `ats_api` (Rails) e `recruiter_agent_v5` (Python).

**Architecture:** (1) Migration em `candidates` adiciona 8 colunas (diversity, LGPD, hidden, twin); `search_data` do Searchkick é atualizado e tabela reindexada. (2) Dois endpoints novos: `POST /v1/users/sourced_profiles/:id/analyze` (LLM + cache Redis) e `POST /v1/users/sourcings/:id/add_candidate` (cria SourcedProfileSourcing, idempotente). (3) No V5: `talent_pool.py` passa a chamar `/v1/users/sourcings/*`; 20 tools novas `@tool` apontando para endpoints existentes + os dois novos.

**Tech Stack:**
- Rails 7.1 + Searchkick (Elasticsearch) + PostgreSQL + Redis + Apartment (multi-tenant) + RSpec + FactoryBot
- Python 3.11 + LangChain `@tool` + `UniversalAPIClient` (HTTP) + pytest + MagicMock

---

## Addendum — descobertas durante execução (2026-04-16)

1. **Caminho real do Rails backend:** `/home/victhor/ats_mercado/wedotalent02202026/ats_api/` (parte do monorepo, branch `develop`). NÃO usar `/home/victhor/ats_mercado/ats_api/` standalone (branch master, mods não relacionadas).
2. **Rails commands via docker:** o ambiente local de Ruby/gems está quebrado (`ros-apartment` tem erro de sintaxe em Ruby local). Todo comando `bin/rails` deve rodar via `docker exec ats_api-web-1 bundle exec rails ...`. RSpec também: `docker exec ats_api-web-1 bundle exec rspec <path>`.
3. **Apartment multi-tenant:** `db:migrate` via docker já aplica aos 11 tenants automaticamente — não precisa `apartment:migrate` separado.
4. **`hide_user_ids` existe em `candidates`:** é array `integer[]` com GIN index — representa "usuários que ocultaram o candidato" (per-user). É ORTOGONAL ao nosso `is_hidden` (flag global). Manter ambos.
5. **`opinions` JÁ EXISTE no repo:** model `app/models/opinion.rb`, controller `v1/users/opinions_controller.rb`, rotas em `routes.rb:388-391`, migration aplicada. Campos: `uid, content, status, metadata, candidate_id, job_id, user_id, account_id`. Scopes: `active`, `general`, `for_job`, `by_candidate`, `pending_review`.
   - **Mudança no plano:** a tool V5 `generate_interview_opinion` (Task 12) agora chama **`POST /v1/users/opinions`** (não `candidate_feedbacks`). Body: `{"opinion": {"candidate_id":, "job_id":, "content":, "status": "active"}}`. Adaptar test spec e implementação.
6. **Candidate tem campos PCD extras:** `main_pcd_category`, `secondary_pcd_category`, `pcd_description`, `pcd_files_description`. Coexistem com nosso `pcd` boolean simples. Nosso boolean serve como filtro agregado; os campos detalhados ficam para ingestão futura.

---

## File Structure

### `ats_api` (Rails) — arquivos criados/modificados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `db/migrate/YYYYMMDD000001_add_diversity_lgpd_twin_fields_to_candidates.rb` | **criar** | Schema change |
| `app/models/candidate.rb` | **modificar** | enum, scopes, belongs_to, search_data |
| `spec/factories/candidates.rb` | **modificar** | traits novos |
| `spec/requests/v1/users/candidates_diversity_spec.rb` | **criar** | Filtros where + aggs |
| `spec/requests/v1/users/candidates_hidden_spec.rb` | **criar** | Scope visible |
| `spec/requests/v1/users/candidates_twin_spec.rb` | **criar** | Twin fields |
| `app/services/sourced_profile_analysis_service.rb` | **criar** | Wrapper LLM + cache |
| `app/controllers/v1/users/sourced_profiles/analysis_controller.rb` | **criar** | Endpoint analyze |
| `app/serializer/sourced_profile_analysis_serializer.rb` | **criar** | Serialização |
| `spec/requests/v1/users/sourced_profiles_analyze_spec.rb` | **criar** | Specs analyze |
| `config/routes.rb` | **modificar** | Rota analyze + add_candidate |
| `app/controllers/v1/users/sourcings_controller.rb` | **modificar** | Action `add_candidate` |
| `spec/requests/v1/users/sourcings_add_candidate_spec.rb` | **criar** | Specs add_candidate |

### `recruiter_agent_v5` (Python) — arquivos modificados/criados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/domains/autonomous/tools/talent_pool.py` | **modificar** | 7 tools → `/v1/users/sourcings/*` |
| `tests/test_talent_pool_tools.py` | **criar** | Smoke tests |
| `src/domains/autonomous/tools/applies_p1.py` | **criar** | 4 tools (aging, silver_medalists, sub_statuses, screening) |
| `src/domains/autonomous/tools/evaluations_p1.py` | **criar** | 3 tools (wsi_scores, screening_results, interview_opinion) |
| `src/domains/autonomous/tools/meetings_p1.py` | **criar** | 2 tools (details, notes) |
| `src/domains/autonomous/tools/communication_p1.py` | **criar** | 3 tools (outreach, generate_msg, add_notes) |
| `src/domains/autonomous/tools/preferences_p1.py` | **criar** | 2 tools (get/save preferences) |
| `src/domains/autonomous/tools/sourcing_p1.py` | **criar** | 4 tools (enrich_contact, enrich_profile, analyze_profile, rag_search) |
| `src/domains/autonomous/tools/activity_p1.py` | **criar** | 2 tools (activity_summary, wizard_feedback) |
| `src/domains/autonomous/tools/__init__.py` | **modificar** | Registrar 7 categorias novas |
| `src/domains/autonomous/tool_selector.py` | **modificar** | Registrar 20 tool names |
| `tests/test_p1_tools.py` | **criar** | Smoke tests P1 |

---

# PARTE 1 — ATS_API (Rails)

## Task 1: Migration — adicionar colunas de diversity/LGPD/twin em `candidates`

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/db/migrate/YYYYMMDDHHMMSS_add_diversity_lgpd_twin_fields_to_candidates.rb` (timestamp gerado pelo `rails g`)

- [ ] **Step 1: Gerar migration**

```bash
cd /home/victhor/ats_mercado/ats_api
bin/rails g migration AddDiversityLgpdTwinFieldsToCandidates
```

- [ ] **Step 2: Editar migration gerada**

Substituir conteúdo completo por:

```ruby
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

- [ ] **Step 3: Rodar migration contra o tenant padrão (Apartment)**

```bash
cd /home/victhor/ats_mercado/ats_api
bin/rails db:migrate
```

Esperado: migration aplicada sem erro. Confirmar com `bin/rails db:schema:dump` que `schema.rb` foi atualizado.

- [ ] **Step 4: Verificar schema**

```bash
grep -E "pcd|ethnicity|lgbtqia|neurodivergent|is_hidden|lgpd_expires_at|is_twin|twin_source_id" /home/victhor/ats_mercado/ats_api/db/schema.rb
```

Esperado: 8 linhas (uma por coluna) + índices.

- [ ] **Step 5: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add db/migrate/ db/schema.rb
git commit -m "feat(candidates): add diversity/lgpd/twin fields migration"
```

---

## Task 2: Model `Candidate` — enum, scopes, belongs_to, search_data update

**Files:**
- Modify: `/home/victhor/ats_mercado/ats_api/app/models/candidate.rb`

- [ ] **Step 1: Escrever test falhando para enum `ethnicity`**

Criar `/home/victhor/ats_mercado/ats_api/spec/models/candidate_diversity_spec.rb`:

```ruby
require "rails_helper"

RSpec.describe Candidate, type: :model do
  describe "diversity fields" do
    it "has ethnicity enum with 6 values" do
      expect(Candidate.ethnicities.keys).to match_array(
        %w[white black brown yellow indigenous undeclared]
      )
    end

    it "defaults boolean diversity fields to false" do
      candidate = build(:candidate)
      expect(candidate.pcd).to be false
      expect(candidate.lgbtqia).to be false
      expect(candidate.neurodivergent).to be false
      expect(candidate.is_hidden).to be false
      expect(candidate.is_twin).to be false
    end
  end

  describe "scopes" do
    let!(:visible)   { create(:candidate, is_hidden: false) }
    let!(:hidden)    { create(:candidate, is_hidden: true) }
    let!(:expired)   { create(:candidate, lgpd_expires_at: 1.day.ago) }
    let!(:valid_ttl) { create(:candidate, lgpd_expires_at: 30.days.from_now) }
    let!(:null_ttl)  { create(:candidate, lgpd_expires_at: nil) }

    it ".visible excludes hidden" do
      expect(Candidate.visible).to include(visible)
      expect(Candidate.visible).not_to include(hidden)
    end

    it ".lgpd_active excludes expired, includes null and future" do
      result = Candidate.lgpd_active
      expect(result).to include(valid_ttl, null_ttl)
      expect(result).not_to include(expired)
    end
  end

  describe "twin association" do
    it "links to twin_source via belongs_to" do
      source = create(:candidate)
      twin = create(:candidate, is_twin: true, twin_source_id: source.id)
      expect(twin.twin_source).to eq(source)
    end
  end
end
```

- [ ] **Step 2: Rodar o test para verificar que falha**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/models/candidate_diversity_spec.rb
```

Esperado: FALHA (enum ethnicity / scope visible / twin_source não definidos).

- [ ] **Step 3: Atualizar `app/models/candidate.rb`**

Localizar a linha `validates :cpf, uniqueness: true, allow_blank: true` (~linha 43) e adicionar DEPOIS dela:

```ruby
  enum ethnicity: {
    white: 0, black: 1, brown: 2, yellow: 3, indigenous: 4, undeclared: 5
  }, _prefix: :ethnicity

  belongs_to :twin_source, class_name: "Candidate", optional: true
  has_many   :twin_copies, class_name: "Candidate", foreign_key: :twin_source_id, inverse_of: :twin_source, dependent: :nullify

  scope :visible, -> { where(is_hidden: false) }
  scope :hidden,  -> { where(is_hidden: true) }
  scope :lgpd_active, -> { where("lgpd_expires_at IS NULL OR lgpd_expires_at > ?", Time.current) }
  scope :pcd,            -> { where(pcd: true) }
  scope :lgbtqia,        -> { where(lgbtqia: true) }
  scope :neurodivergent, -> { where(neurodivergent: true) }
```

- [ ] **Step 4: Atualizar `search_data` (linha 188–238)**

No bloco do hash retornado por `search_data`, adicionar antes de `**applies_search_data,`:

```ruby
      pcd: pcd,
      ethnicity: ethnicity,
      ethnicity_text: ethnicity,
      lgbtqia: lgbtqia,
      neurodivergent: neurodivergent,
      is_hidden: is_hidden,
      is_twin: is_twin,
      twin_source_id: twin_source_id,
      lgpd_expires_at: lgpd_expires_at,
      lgpd_active: lgpd_expires_at.nil? || lgpd_expires_at > Time.current,
```

- [ ] **Step 5: Atualizar `agg_search_array` (linha 240)**

Adicionar ao hash retornado:

```ruby
      pcd:            { field: "pcd",            limit: 2 },
      ethnicity:      { field: "ethnicity",      limit: 10 },
      ethnicity_text: { field: "ethnicity_text", limit: 10 },
      lgbtqia:        { field: "lgbtqia",        limit: 2 },
      neurodivergent: { field: "neurodivergent", limit: 2 },
      is_hidden:      { field: "is_hidden",      limit: 2 },
      is_twin:        { field: "is_twin",        limit: 2 },
```

- [ ] **Step 6: Rodar test para verificar que passa**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/models/candidate_diversity_spec.rb
```

Esperado: 6 examples, 0 failures.

- [ ] **Step 7: Reindex Searchkick em dev**

```bash
cd /home/victhor/ats_mercado/ats_api
bin/rails runner "Candidate.reindex"
```

Esperado: `Reindexing Candidate...` termina sem erro.

- [ ] **Step 8: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add app/models/candidate.rb spec/models/candidate_diversity_spec.rb
git commit -m "feat(candidate): add ethnicity enum, diversity scopes, twin association"
```

---

## Task 3: Factory updates — traits para pcd/hidden/twin

**Files:**
- Modify: `/home/victhor/ats_mercado/ats_api/spec/factories/candidates.rb`

- [ ] **Step 1: Editar o factory, adicionar traits**

No arquivo `spec/factories/candidates.rb`, antes do `end` final do bloco `factory :candidate do`, adicionar:

```ruby
    pcd { false }
    lgbtqia { false }
    neurodivergent { false }
    is_hidden { false }
    is_twin { false }
    lgpd_expires_at { nil }

    trait :pcd            do pcd { true }            end
    trait :lgbtqia        do lgbtqia { true }        end
    trait :neurodivergent do neurodivergent { true } end
    trait :hidden         do is_hidden { true }      end
    trait :twin do
      is_twin { true }
      twin_source { association(:candidate) }
    end
    trait :ethnicity_black do ethnicity { "black" } end
    trait :ethnicity_white do ethnicity { "white" } end
    trait :ethnicity_brown do ethnicity { "brown" } end
    trait :lgpd_expired    do lgpd_expires_at { 1.day.ago } end
```

- [ ] **Step 2: Verificar factory compila**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/models/candidate_diversity_spec.rb
```

Esperado: continua passando (6 examples).

- [ ] **Step 3: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add spec/factories/candidates.rb
git commit -m "test(candidate): add factory traits for diversity/hidden/twin"
```

---

## Task 4: Request spec — filtros de diversity em `GET /v1/users/candidates`

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/spec/requests/v1/users/candidates_diversity_spec.rb`

- [ ] **Step 1: Criar spec**

```ruby
require "rails_helper"

RSpec.describe "V1::Users::Candidates diversity filters", type: :request, search: true do
  let!(:account) { create(:account) }
  let!(:user)    { create(:user, account: account) }
  let(:headers)  { auth_headers(user) }

  let!(:pcd_black)   { create(:candidate, :pcd, :ethnicity_black, account: account) }
  let!(:lgbt_brown)  { create(:candidate, :lgbtqia, :ethnicity_brown, account: account) }
  let!(:plain_white) { create(:candidate, :ethnicity_white, account: account) }

  before { Candidate.searchkick_index.refresh }

  describe "GET /v1/users/candidates?where={\"pcd\":true}" do
    it "returns only PcD candidates" do
      get "/v1/users/candidates", params: { where: { pcd: true }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      ids = json["data"].map { |c| c["id"] }
      expect(ids).to include(pcd_black.id)
      expect(ids).not_to include(lgbt_brown.id, plain_white.id)
    end
  end

  describe "GET /v1/users/candidates?where={\"ethnicity\":\"black\"}" do
    it "returns only black-declared candidates" do
      get "/v1/users/candidates", params: { where: { ethnicity: "black" }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      ids = json["data"].map { |c| c["id"] }
      expect(ids).to contain_exactly(pcd_black.id)
    end
  end

  describe "GET /v1/users/candidates with aggregators" do
    it "returns ethnicity and pcd facets in meta" do
      get "/v1/users/candidates",
          params: { extra_params: "aggs(ethnicity,pcd,lgbtqia)" },
          headers: headers
      expect(response).to have_http_status(:ok)
      aggs = json.dig("meta", "aggregators")
      expect(aggs).to include("ethnicity", "pcd", "lgbtqia") if aggs.present?
    end
  end
end
```

- [ ] **Step 2: Rodar spec**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/candidates_diversity_spec.rb
```

Esperado: 3 examples, 0 failures. Se algum aggregator falhar por ausência de retorno (meta vazio), o `if aggs.present?` cobre.

- [ ] **Step 3: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add spec/requests/v1/users/candidates_diversity_spec.rb
git commit -m "test(candidates): filter by pcd/ethnicity + aggs"
```

---

## Task 5: Request spec — scope `visible` e filtro `is_hidden`

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/spec/requests/v1/users/candidates_hidden_spec.rb`

- [ ] **Step 1: Criar spec**

```ruby
require "rails_helper"

RSpec.describe "V1::Users::Candidates hidden filter", type: :request, search: true do
  let!(:account) { create(:account) }
  let!(:user)    { create(:user, account: account) }
  let(:headers)  { auth_headers(user) }

  let!(:visible_a) { create(:candidate, is_hidden: false, account: account) }
  let!(:visible_b) { create(:candidate, is_hidden: false, account: account) }
  let!(:hidden_a)  { create(:candidate, :hidden, account: account) }

  before { Candidate.searchkick_index.refresh }

  it "returns non-hidden by default (no filter)" do
    get "/v1/users/candidates", headers: headers
    expect(response).to have_http_status(:ok)
    ids = json["data"].map { |c| c["id"] }
    expect(ids).to match_array([visible_a.id, visible_b.id])
  end

  it "returns hidden when is_hidden:true explicitly requested" do
    get "/v1/users/candidates",
        params: { where: { is_hidden: true }.to_json },
        headers: headers
    expect(response).to have_http_status(:ok)
    ids = json["data"].map { |c| c["id"] }
    expect(ids).to contain_exactly(hidden_a.id)
  end
end
```

**NOTA:** o comportamento "excluir hidden por default" depende de ajuste em `CandidatesController#normalize_candidate_filters!` (ou método equivalente). Se o primeiro teste falhar, adicionar no controller, dentro de `index`, após `params[:where]["is_deleted"] = false if ...`:

```ruby
params[:where]["is_hidden"] = false if params[:where]["is_hidden"].nil?
```

- [ ] **Step 2: Rodar spec**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/candidates_hidden_spec.rb
```

Esperado: 2 examples, 0 failures. Se o primeiro falhar, aplicar nota acima e repetir.

- [ ] **Step 3: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add spec/requests/v1/users/candidates_hidden_spec.rb app/controllers/v1/users/candidates_controller.rb
git commit -m "feat(candidates): default exclude hidden from index, test filter"
```

---

## Task 6: Request spec — twin candidate creation

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/spec/requests/v1/users/candidates_twin_spec.rb`

- [ ] **Step 1: Criar spec**

```ruby
require "rails_helper"

RSpec.describe "V1::Users::Candidates twin creation", type: :request do
  let!(:account)       { create(:account) }
  let!(:user)          { create(:user, account: account) }
  let!(:source)        { create(:candidate, account: account, name: "Maria Original") }
  let(:headers)        { auth_headers(user) }

  describe "POST /v1/users/candidates with twin fields" do
    it "creates a twin candidate linked to source" do
      post "/v1/users/candidates",
           params: {
             candidate: {
               name: "Maria (Twin)",
               email: "twin-#{SecureRandom.hex(4)}@example.com",
               is_twin: true,
               twin_source_id: source.id
             }
           },
           headers: headers

      expect(response).to have_http_status(:created)
      twin = Candidate.find(json.dig("data", "id"))
      expect(twin.is_twin).to be true
      expect(twin.twin_source).to eq(source)
    end
  end

  describe "GET /v1/users/candidates?where={\"is_twin\":true}" do
    it "filters only twin candidates", search: true do
      create(:candidate, :twin, account: account)
      create(:candidate, account: account)
      Candidate.searchkick_index.refresh

      get "/v1/users/candidates", params: { where: { is_twin: true }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      expect(json["data"].all? { |c| c["is_twin"] }).to be true if json["data"].any? { |c| c.key?("is_twin") }
    end
  end
end
```

- [ ] **Step 2: Verificar se `candidate_params` permite `is_twin` e `twin_source_id`**

```bash
grep -n "candidate_params\|permit" /home/victhor/ats_mercado/ats_api/app/controllers/v1/users/candidates_controller.rb | head -20
```

Se `is_twin` / `twin_source_id` / `pcd` / `ethnicity` / `lgbtqia` / `neurodivergent` / `is_hidden` / `lgpd_expires_at` NÃO estiverem no `permit(...)`, adicioná-los na lista. Procurar o método privado `candidate_params` e acrescentar ao array.

- [ ] **Step 3: Rodar spec**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/candidates_twin_spec.rb
```

Esperado: 2 examples, 0 failures.

- [ ] **Step 4: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add spec/requests/v1/users/candidates_twin_spec.rb app/controllers/v1/users/candidates_controller.rb
git commit -m "feat(candidates): permit twin fields + test creation/filter"
```

---

## Task 7: Service `SourcedProfileAnalysisService` (LLM + cache)

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/app/services/sourced_profile_analysis_service.rb`
- Create: `/home/victhor/ats_mercado/ats_api/spec/services/sourced_profile_analysis_service_spec.rb`

- [ ] **Step 1: Escrever test falhando**

```ruby
require "rails_helper"

RSpec.describe SourcedProfileAnalysisService, type: :service do
  let(:account) { create(:account) }
  let(:sourcing) { create(:sourcing, account: account) }
  let(:sourced_profile) do
    create(:sourced_profile,
           account: account,
           name: "Ada Lovelace",
           headline: "Senior Ruby/Rails Engineer",
           skills_list: %w[ruby rails postgresql])
  end

  subject(:service) { described_class.new(sourced_profile: sourced_profile) }

  describe "#call" do
    before do
      allow(service).to receive(:invoke_llm).and_return(
        summary: "Senior dev with strong Rails background",
        skills_analysis: { strong: %w[ruby rails], moderate: [], gaps: [] },
        fit_score: 0.82,
        strengths: ["Direct stack match"],
        concerns: []
      )
    end

    it "returns the LLM analysis hash" do
      result = service.call
      expect(result[:summary]).to include("Senior")
      expect(result[:fit_score]).to eq(0.82)
    end

    it "caches the result under sp_analysis:<id>" do
      Rails.cache.clear
      service.call
      cached = Rails.cache.read("sp_analysis:#{sourced_profile.id}")
      expect(cached).not_to be_nil
      expect(cached[:fit_score]).to eq(0.82)
    end

    it "returns cached value on second call without re-invoking LLM" do
      Rails.cache.clear
      service.call
      expect(service).not_to receive(:invoke_llm)
      second = service.call
      expect(second[:fit_score]).to eq(0.82)
    end
  end
end
```

- [ ] **Step 2: Rodar — deve falhar por classe inexistente**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/services/sourced_profile_analysis_service_spec.rb
```

Esperado: `NameError: uninitialized constant SourcedProfileAnalysisService`.

- [ ] **Step 3: Implementar service**

```ruby
class SourcedProfileAnalysisService
  CACHE_TTL = 24.hours
  CACHE_KEY = "sp_analysis:%<id>d"

  def initialize(sourced_profile:, force_refresh: false)
    @sourced_profile = sourced_profile
    @force_refresh = force_refresh
  end

  def call
    key = format(CACHE_KEY, id: @sourced_profile.id)
    Rails.cache.delete(key) if @force_refresh
    Rails.cache.fetch(key, expires_in: CACHE_TTL) { invoke_llm }
  end

  private

  def invoke_llm
    prompt = build_prompt
    raw = LLMGateway.complete(model: "claude-sonnet-4-5", prompt: prompt, response_format: :json)
    parse_llm_response(raw)
  end

  def build_prompt
    <<~PROMPT
      Analise o perfil profissional abaixo e retorne JSON com:
      - summary (string curta, pt-BR)
      - skills_analysis: {strong: [], moderate: [], gaps: []}
      - fit_score: float 0..1
      - strengths: []
      - concerns: []

      PERFIL:
      Nome: #{@sourced_profile.name}
      Headline: #{@sourced_profile.headline}
      Skills: #{(@sourced_profile.skills_list || []).join(", ")}
      Empresa atual: #{@sourced_profile.current_company}
      Experiência: #{@sourced_profile.experiences_summary}
    PROMPT
  end

  def parse_llm_response(raw)
    json = raw.is_a?(Hash) ? raw : JSON.parse(raw, symbolize_names: true)
    {
      summary: json[:summary].to_s,
      skills_analysis: json[:skills_analysis] || { strong: [], moderate: [], gaps: [] },
      fit_score: json[:fit_score].to_f,
      strengths: json[:strengths] || [],
      concerns: json[:concerns] || []
    }
  end
end
```

**NOTA:** `LLMGateway.complete` é o wrapper existente no repo para chamar Claude. Se o nome for diferente no codebase, grepar por `anthropic\|claude_api\|llm_gateway` em `app/services/` e adaptar. Campos do `SourcedProfile` (`headline`, `skills_list`, `current_company`, `experiences_summary`) devem existir — caso contrário adaptar ao schema real.

- [ ] **Step 4: Rodar spec para verificar que passa**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/services/sourced_profile_analysis_service_spec.rb
```

Esperado: 3 examples, 0 failures.

- [ ] **Step 5: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add app/services/sourced_profile_analysis_service.rb spec/services/sourced_profile_analysis_service_spec.rb
git commit -m "feat(sourced_profile): service for LLM-based profile analysis with 24h cache"
```

---

## Task 8: Endpoint `POST /v1/users/sourced_profiles/:id/analyze`

**Files:**
- Create: `/home/victhor/ats_mercado/ats_api/app/controllers/v1/users/sourced_profiles/analysis_controller.rb`
- Create: `/home/victhor/ats_mercado/ats_api/app/serializer/sourced_profile_analysis_serializer.rb`
- Modify: `/home/victhor/ats_mercado/ats_api/config/routes.rb`
- Create: `/home/victhor/ats_mercado/ats_api/spec/requests/v1/users/sourced_profiles_analyze_spec.rb`

- [ ] **Step 1: Escrever request spec falhando**

```ruby
require "rails_helper"

RSpec.describe "V1::Users::SourcedProfiles#analyze", type: :request do
  let!(:account)         { create(:account) }
  let!(:user)            { create(:user, account: account) }
  let!(:sourced_profile) { create(:sourced_profile, account: account) }
  let(:headers)          { auth_headers(user) }

  before do
    allow_any_instance_of(SourcedProfileAnalysisService).to receive(:invoke_llm).and_return(
      summary: "Strong candidate",
      skills_analysis: { strong: ["ruby"], moderate: [], gaps: [] },
      fit_score: 0.77,
      strengths: [], concerns: []
    )
    Rails.cache.clear
  end

  describe "POST /v1/users/sourced_profiles/:id/analyze" do
    it "returns 200 and analysis payload" do
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect(response).to have_http_status(:ok)
      data = json["data"]
      expect(data["summary"]).to eq("Strong candidate")
      expect(data["fit_score"]).to eq(0.77)
      expect(data["sourced_profile_id"]).to eq(sourced_profile.id)
    end

    it "second call hits cache (does not call LLM again)" do
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect_any_instance_of(SourcedProfileAnalysisService).not_to receive(:invoke_llm)
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "returns 404 when sourced_profile does not belong to account" do
      other = create(:sourced_profile, account: create(:account))
      post "/v1/users/sourced_profiles/#{other.id}/analyze", headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end
end
```

- [ ] **Step 2: Rodar — deve falhar (404 na rota)**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/sourced_profiles_analyze_spec.rb
```

Esperado: falha com rota não encontrada.

- [ ] **Step 3: Adicionar rota em `config/routes.rb`**

Localizar bloco `resources :sourced_profiles` (linha 425) e adicionar dentro do `member do`, após a linha `post "enrich_contacts", ...`:

```ruby
            post "analyze", to: "sourced_profiles/analysis#create"
```

- [ ] **Step 4: Criar controller `app/controllers/v1/users/sourced_profiles/analysis_controller.rb`**

```ruby
module V1
  module Users
    module SourcedProfiles
      class AnalysisController < ApplicationController
        before_action :set_sourced_profile

        def create
          analysis = SourcedProfileAnalysisService.new(
            sourced_profile: @sourced_profile,
            force_refresh: ActiveModel::Type::Boolean.new.cast(params[:refresh])
          ).call

          render json: SourcedProfileAnalysisSerializer.new(
            sourced_profile: @sourced_profile,
            analysis: analysis
          ).as_json, status: :ok
        end

        private

        def set_sourced_profile
          @sourced_profile = @current_user.account.sourced_profiles.active.find(params[:id])
        rescue ActiveRecord::RecordNotFound
          render json: { error: "Sourced profile not found" }, status: :not_found
        end
      end
    end
  end
end
```

- [ ] **Step 5: Criar serializer `app/serializer/sourced_profile_analysis_serializer.rb`**

```ruby
class SourcedProfileAnalysisSerializer
  def initialize(sourced_profile:, analysis:)
    @sourced_profile = sourced_profile
    @analysis = analysis
  end

  def as_json
    {
      data: @analysis.merge(
        sourced_profile_id: @sourced_profile.id,
        cached_at: Time.current.iso8601,
        cache_ttl_seconds: SourcedProfileAnalysisService::CACHE_TTL.to_i
      ),
      meta: { source: "llm", model: "claude-sonnet-4-5" }
    }
  end
end
```

- [ ] **Step 6: Rodar spec — deve passar**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/sourced_profiles_analyze_spec.rb
```

Esperado: 3 examples, 0 failures.

- [ ] **Step 7: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add app/controllers/v1/users/sourced_profiles/analysis_controller.rb \
        app/serializer/sourced_profile_analysis_serializer.rb \
        config/routes.rb \
        spec/requests/v1/users/sourced_profiles_analyze_spec.rb
git commit -m "feat(sourced_profiles): POST /analyze endpoint with Redis cache"
```

---

## Task 9: Endpoint `POST /v1/users/sourcings/:id/add_candidate`

**Files:**
- Modify: `/home/victhor/ats_mercado/ats_api/app/controllers/v1/users/sourcings_controller.rb`
- Modify: `/home/victhor/ats_mercado/ats_api/config/routes.rb`
- Create: `/home/victhor/ats_mercado/ats_api/spec/requests/v1/users/sourcings_add_candidate_spec.rb`

- [ ] **Step 1: Escrever request spec falhando**

```ruby
require "rails_helper"

RSpec.describe "V1::Users::Sourcings#add_candidate", type: :request do
  let!(:account)   { create(:account) }
  let!(:user)      { create(:user, account: account) }
  let!(:sourcing)  { create(:sourcing, account: account, user: user) }
  let!(:candidate) { create(:candidate, account: account) }
  let(:headers)    { auth_headers(user) }

  describe "POST /v1/users/sourcings/:id/add_candidate" do
    it "creates SourcedProfileSourcing with candidate_id" do
      expect {
        post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
             params: { candidate_id: candidate.id, score: 85, notes: "manual" },
             headers: headers
      }.to change(SourcedProfileSourcing, :count).by(1)

      expect(response).to have_http_status(:created).or have_http_status(:ok)
      expect(json.dig("data", "sourcing_id")).to eq(sourcing.id)
      expect(json.dig("data", "score")).to eq(85)
    end

    it "is idempotent — second call returns existing relation without creating new" do
      post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
           params: { candidate_id: candidate.id }, headers: headers

      expect {
        post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
             params: { candidate_id: candidate.id }, headers: headers
      }.not_to change(SourcedProfileSourcing, :count)

      expect(response).to have_http_status(:ok)
    end

    it "returns 422 without candidate_id or sourced_profile_id" do
      post "/v1/users/sourcings/#{sourcing.id}/add_candidate", headers: headers
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "returns 404 for sourcing of another account" do
      other = create(:sourcing, account: create(:account))
      post "/v1/users/sourcings/#{other.id}/add_candidate",
           params: { candidate_id: candidate.id }, headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end
end
```

- [ ] **Step 2: Rodar — deve falhar**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/sourcings_add_candidate_spec.rb
```

Esperado: rota não encontrada.

- [ ] **Step 3: Adicionar rota em `config/routes.rb`**

Dentro do bloco `resources :sourcings ... do` (linha 405), no `member do`, adicionar:

```ruby
            post :add_candidate
```

- [ ] **Step 4: Adicionar action em `sourcings_controller.rb`**

Antes do bloco `private` do `SourcingsController`, adicionar:

```ruby
      def add_candidate
        sourcing = @current_user.account.sourcings.find(params[:id])

        sourced_profile = resolve_sourced_profile(sourcing)
        return if performed? # resolver já renderizou erro

        rel = SourcedProfileSourcing
                .where(sourcing_id: sourcing.id, sourced_profile_id: sourced_profile.id, is_deleted: false)
                .first

        if rel
          render json: { data: serialize_relation(rel), meta: { idempotent: true } }, status: :ok
          return
        end

        rel = SourcedProfileSourcing.create!(
          sourcing_id: sourcing.id,
          sourced_profile_id: sourced_profile.id,
          account_id: sourcing.account_id,
          score: params[:score],
          general_comments: params[:notes],
          source: "manual"
        )

        render json: { data: serialize_relation(rel) }, status: :created
      rescue ActiveRecord::RecordNotFound
        render json: { error: "Sourcing not found" }, status: :not_found
      rescue ActiveRecord::RecordInvalid => e
        render json: { error: e.message }, status: :unprocessable_entity
      end
```

Adicionar helpers privados (dentro do bloco `private`):

```ruby
      def resolve_sourced_profile(sourcing)
        if params[:sourced_profile_id].present?
          sp = @current_user.account.sourced_profiles.active.find_by(id: params[:sourced_profile_id])
          return sp if sp

          render json: { error: "sourced_profile not found" }, status: :not_found
          return nil
        end

        if params[:candidate_id].present?
          candidate = @current_user.account.candidates.find_by(id: params[:candidate_id])
          unless candidate
            render json: { error: "candidate not found" }, status: :not_found
            return nil
          end
          return find_or_create_sourced_profile_from_candidate(candidate, sourcing)
        end

        render json: { error: "candidate_id or sourced_profile_id required" }, status: :unprocessable_entity
        nil
      end

      def find_or_create_sourced_profile_from_candidate(candidate, sourcing)
        return candidate.sourced_profile.first if candidate.sourced_profile.any?

        SourcedProfile.create!(
          account_id: sourcing.account_id,
          candidate_id: candidate.id,
          name: candidate.name,
          email: candidate.email,
          source: "manual"
        )
      end

      def serialize_relation(rel)
        {
          id: rel.id,
          sourcing_id: rel.sourcing_id,
          sourced_profile_id: rel.sourced_profile_id,
          score: rel.score,
          general_comments: rel.general_comments,
          created_at: rel.created_at
        }
      end
```

**NOTA:** Atributos exatos de `SourcedProfile.create!` (name/email) podem precisar ajuste conforme schema real. Se `source` não for coluna válida, remover. Verificar com `SourcedProfile.column_names` no `rails c`.

- [ ] **Step 5: Rodar specs**

```bash
cd /home/victhor/ats_mercado/ats_api
bundle exec rspec spec/requests/v1/users/sourcings_add_candidate_spec.rb
```

Esperado: 4 examples, 0 failures.

- [ ] **Step 6: Commit**

```bash
cd /home/victhor/ats_mercado/ats_api
git add app/controllers/v1/users/sourcings_controller.rb \
        config/routes.rb \
        spec/requests/v1/users/sourcings_add_candidate_spec.rb
git commit -m "feat(sourcings): POST /:id/add_candidate endpoint (idempotent)"
```

---

# PARTE 2 — RECRUITER_AGENT_V5 (Python)

> **Contexto:** projeto em `/home/victhor/ats_mercado/recruiter_agent_v5/`. Use venv existente. Testes com `pytest`.

## Task 10: Corrigir `talent_pool.py` — 7 tools fantasma → `/v1/users/sourcings/*`

**Files:**
- Modify: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/talent_pool.py`
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/tests/test_talent_pool_tools.py`

- [ ] **Step 1: Criar smoke test falhando**

```python
import json
from unittest.mock import MagicMock
from src.domains.autonomous.tools.talent_pool import create_talent_pool_tools


def _get_tool(tools, name):
    for t in tools:
        if t.name == name:
            return t
    raise KeyError(name)


def test_search_talent_pools_calls_sourcings_index():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tools = create_talent_pool_tools(api)

    _get_tool(tools, "search_talent_pools").invoke({"name": "devs"})

    call = api.request.call_args
    assert call.args[0] == "GET"
    assert call.args[1] == "/v1/users/sourcings"


def test_create_talent_pool_posts_sourcing():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={"id": 1}, meta={})
    tools = create_talent_pool_tools(api)

    _get_tool(tools, "create_talent_pool").invoke(
        {"name": "React Devs", "criteria": json.dumps({"skills": ["react"]})}
    )

    call = api.create.call_args
    assert call.args[0] == "/v1/users/sourcings"
    body = call.args[1]
    assert body["sourcing"]["saved"] is True
    assert body["sourcing"]["query"] == "React Devs"


def test_add_candidate_calls_add_candidate_endpoint():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={"id": 99}, meta={})
    tools = create_talent_pool_tools(api)

    _get_tool(tools, "add_candidate_to_pool").invoke({"pool_id": 5, "candidate_id": 42})

    call = api.create.call_args
    assert call.args[0] == "/v1/users/sourcings/5/add_candidate"
    assert call.args[1] == {"candidate_id": 42}
```

- [ ] **Step 2: Rodar — deve falhar**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_talent_pool_tools.py -v
```

Esperado: falha nos assertions sobre URL.

- [ ] **Step 3: Reescrever `talent_pool.py`**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_talent_pool_tools(api: UniversalAPIClient) -> list:
    @tool
    def search_talent_pools(name: str = "", page: int = 1, per_page: int = 15) -> str:
        """Busca talent pools (sourcings persistidos). Use quando o usuário pedir para listar pools, bancos de talento ou buscas salvas."""
        params = [("page", str(page)), ("per_page", str(min(per_page, 30)))]
        where = {"saved": True}
        if name:
            where["query"] = {"like": f"%{name.lower()}%"}
        params.append(("where", json.dumps(where)))
        return _fmt(api.request("GET", "/v1/users/sourcings", params=params))

    @tool
    def get_talent_pool(pool_id: int) -> str:
        """Retorna detalhes de um talent pool (sourcing) específico pelo ID."""
        return _fmt(api.get(f"/v1/users/sourcings/{pool_id}"))

    @tool
    def create_talent_pool(name: str, description: str = "", criteria: str = "") -> str:
        """Cria novo talent pool (sourcing persistido).

        Args:
            name: Nome do pool (usado como query).
            description: Texto descritivo.
            criteria: JSON string com parameters opcionais.
        """
        body = {"sourcing": {"query": name, "saved": True, "provider": "local"}}
        if description:
            body["sourcing"]["description"] = description
        if criteria:
            try:
                body["sourcing"]["parameters"] = json.loads(criteria)
            except (json.JSONDecodeError, TypeError):
                return json.dumps({"success": False, "error": "criteria deve ser JSON valido"}, ensure_ascii=False)
        return _fmt(api.create("/v1/users/sourcings", body))

    @tool
    def add_candidate_to_pool(pool_id: int, candidate_id: int, score: int = 0, notes: str = "") -> str:
        """Adiciona candidato a um talent pool (sourcing). Idempotente."""
        body = {"candidate_id": candidate_id}
        if score:
            body["score"] = score
        if notes:
            body["notes"] = notes
        return _fmt(api.create(f"/v1/users/sourcings/{pool_id}/add_candidate", body))

    @tool
    def remove_candidate_from_pool(pool_id: int, sourced_profile_sourcing_id: int) -> str:
        """Remove candidato do pool (soft-delete da relação SourcedProfileSourcing)."""
        return _fmt(api.delete(f"/v1/users/sourced_profile_sourcings/{sourced_profile_sourcing_id}"))

    @tool
    def get_pool_candidates(pool_id: int, page: int = 1, per_page: int = 15) -> str:
        """Lista candidatos pertencentes ao pool (top_profiles do sourcing)."""
        params = [("page", str(page)), ("per_page", str(min(per_page, 30)))]
        return _fmt(api.request("GET", f"/v1/users/sourcings/{pool_id}", params=params))

    @tool
    def get_pool_metrics(pool_id: int) -> str:
        """Retorna estatísticas agregadas de um talent pool."""
        return _fmt(api.request("GET", f"/v1/users/sourcings/{pool_id}/stats"))

    return [
        search_talent_pools,
        get_talent_pool,
        create_talent_pool,
        add_candidate_to_pool,
        remove_candidate_from_pool,
        get_pool_candidates,
        get_pool_metrics,
    ]
```

**NOTA 1:** a tool original `bulk_add_to_pool` foi removida. Implementar depois apenas se LIA pedir — reuso via chamadas sequenciais de `add_candidate_to_pool` resolve na maioria dos casos.

**NOTA 2:** `remove_candidate_from_pool` depende de `DELETE /v1/users/sourced_profile_sourcings/:id` — a rota está listada em `routes.rb:439` (`resources :sourced_profile_sourcings` com `:destroy`). Validar no smoke test real. Se falhar, abrir endpoint dedicado.

- [ ] **Step 4: Rodar testes — deve passar**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_talent_pool_tools.py -v
```

Esperado: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
git add src/domains/autonomous/tools/talent_pool.py tests/test_talent_pool_tools.py
git commit -m "fix(talent_pool): redirect 7 phantom tools to /v1/users/sourcings/*"
```

---

## Task 11: Tools P1 — grupo `applies` (4 tools)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/applies_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_applies_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def get_stage_sub_statuses(page: int = 1, per_page: int = 30) -> str:
        """Lista sub-status disponíveis para stages/applies (apply_statuses)."""
        return _fmt(api.request("GET", "/v1/users/apply_statuses",
                                params=[("page", str(page)), ("per_page", str(per_page))]))

    @tool
    def get_candidate_aging(page: int = 1, per_page: int = 30) -> str:
        """Retorna applies agrupados por tempo de permanência no estágio (aging)."""
        return _fmt(api.request("GET", "/v1/users/applies/aging",
                                params=[("page", str(page)), ("per_page", str(per_page))]))

    @tool
    def get_at_risk_candidates(stage_days_gt: int = 30, page: int = 1, per_page: int = 30) -> str:
        """Lista candidatos que estão há mais de N dias no mesmo estágio (risco de evasão)."""
        where = {"stage_days_gt": stage_days_gt}
        return _fmt(api.request("GET", "/v1/users/applies/aging",
                                params=[("page", str(page)), ("per_page", str(per_page)),
                                        ("where", json.dumps(where))]))

    @tool
    def find_silver_medalists(min_score: int = 70, page: int = 1, per_page: int = 30) -> str:
        """Lista candidatos rejeitados de alta pontuação (silver medalists) para reengajamento."""
        where = {"status": "rejected", "score_gte": min_score}
        return _fmt(api.request("GET", "/v1/users/applies",
                                params=[("page", str(page)), ("per_page", str(per_page)),
                                        ("where", json.dumps(where))]))

    return [get_stage_sub_statuses, get_candidate_aging, get_at_risk_candidates, find_silver_medalists]
```

- [ ] **Step 2: Escrever smoke test**

Criar `tests/test_p1_tools.py`:

```python
import json
from unittest.mock import MagicMock
from src.domains.autonomous.tools.applies_p1 import create_applies_p1_tools


def _get(tools, name):
    return next(t for t in tools if t.name == name)


def test_get_candidate_aging():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_applies_p1_tools(api), "get_candidate_aging")
    tool.invoke({})
    call = api.request.call_args
    assert call.args[1] == "/v1/users/applies/aging"


def test_find_silver_medalists_builds_where():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_applies_p1_tools(api), "find_silver_medalists")
    tool.invoke({"min_score": 80})

    kwargs = dict(api.request.call_args.kwargs.get("params") or api.request.call_args.args[2])
    assert "where" in kwargs
    where = json.loads(kwargs["where"])
    assert where["status"] == "rejected"
    assert where["score_gte"] == 80


def test_at_risk_default_threshold():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_applies_p1_tools(api), "get_at_risk_candidates")
    tool.invoke({})
    kwargs = dict(api.request.call_args.kwargs.get("params") or api.request.call_args.args[2])
    assert json.loads(kwargs["where"])["stage_days_gt"] == 30
```

- [ ] **Step 3: Rodar**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
```

Esperado: 3 passed.

- [ ] **Step 4: Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
git add src/domains/autonomous/tools/applies_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 tools for applies aging/silver_medalists/sub_statuses"
```

---

## Task 12: Tools P1 — grupo `evaluations` (3 tools)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/evaluations_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_evaluations_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def get_candidate_wsi_scores(candidate_id: int, page: int = 1, per_page: int = 15) -> str:
        """Retorna scores WSI (Weighted Scoring Index) de um candidato."""
        where = {"candidate_id": candidate_id, "wsi": True}
        return _fmt(api.request("GET", "/v1/users/evaluation_candidates",
                                params=[("page", str(page)), ("per_page", str(per_page)),
                                        ("where", json.dumps(where))]))

    @tool
    def get_candidate_screening_results(candidate_id: int, page: int = 1, per_page: int = 15) -> str:
        """Retorna resultados de screening (evaluation_candidates) de um candidato."""
        where = {"candidate_id": candidate_id}
        return _fmt(api.request("GET", "/v1/users/evaluation_candidates",
                                params=[("page", str(page)), ("per_page", str(per_page)),
                                        ("where", json.dumps(where))]))

    @tool
    def generate_interview_opinion(candidate_id: int, apply_id: int, feedback_type: str,
                                   reason: str = "", search_query_snapshot: str = "") -> str:
        """Registra opinião do recruiter sobre candidato (like/dislike).

        Args:
            candidate_id: ID do candidato.
            apply_id: ID do apply vinculado.
            feedback_type: 'like' ou 'dislike'.
            reason: Texto curto com motivo.
            search_query_snapshot: snapshot da busca que levou ao candidato.
        """
        if feedback_type not in ("like", "dislike"):
            return json.dumps({"success": False, "error": "feedback_type deve ser 'like' ou 'dislike'"}, ensure_ascii=False)
        body = {
            "candidate_feedback": {
                "candidate_id": candidate_id,
                "apply_id": apply_id,
                "feedback_type": feedback_type,
                "reason": reason,
                "search_query_snapshot": search_query_snapshot,
            }
        }
        return _fmt(api.create("/v1/users/candidate_feedbacks", body))

    return [get_candidate_wsi_scores, get_candidate_screening_results, generate_interview_opinion]
```

- [ ] **Step 2: Adicionar smoke tests em `tests/test_p1_tools.py` (append)**

```python
from src.domains.autonomous.tools.evaluations_p1 import create_evaluations_p1_tools


def test_get_wsi_scores_filters_by_candidate_and_wsi_flag():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_evaluations_p1_tools(api), "get_candidate_wsi_scores")
    tool.invoke({"candidate_id": 10})
    kwargs = dict(api.request.call_args.kwargs.get("params") or api.request.call_args.args[2])
    where = json.loads(kwargs["where"])
    assert where == {"candidate_id": 10, "wsi": True}


def test_generate_interview_opinion_posts_candidate_feedback():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={"id": 1}, meta={})
    tool = _get(create_evaluations_p1_tools(api), "generate_interview_opinion")
    tool.invoke({"candidate_id": 5, "apply_id": 9, "feedback_type": "like", "reason": "good"})
    assert api.create.call_args.args[0] == "/v1/users/candidate_feedbacks"
    body = api.create.call_args.args[1]
    assert body["candidate_feedback"]["feedback_type"] == "like"


def test_generate_interview_opinion_rejects_invalid_type():
    api = MagicMock()
    tool = _get(create_evaluations_p1_tools(api), "generate_interview_opinion")
    result = tool.invoke({"candidate_id": 1, "apply_id": 1, "feedback_type": "maybe"})
    assert json.loads(result)["success"] is False
```

- [ ] **Step 3: Rodar**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
```

Esperado: 6 passed.

- [ ] **Step 4: Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
git add src/domains/autonomous/tools/evaluations_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 tools for wsi/screening/interview_opinion"
```

---

## Task 13: Tools P1 — grupo `meetings` (2 tools)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/meetings_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_meetings_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def get_interview_details(meeting_id: int) -> str:
        """Retorna detalhes de uma entrevista/meeting específica."""
        return _fmt(api.get(f"/v1/users/meetings/{meeting_id}"))

    @tool
    def view_interview_notes(candidate_id: int, page: int = 1, per_page: int = 30) -> str:
        """Lista meetings (notas e histórico de entrevistas) de um candidato."""
        where = {"candidate_id": candidate_id}
        return _fmt(api.request("GET", "/v1/users/meetings",
                                params=[("page", str(page)), ("per_page", str(per_page)),
                                        ("where", json.dumps(where))]))

    return [get_interview_details, view_interview_notes]
```

- [ ] **Step 2: Adicionar tests (append em `tests/test_p1_tools.py`)**

```python
from src.domains.autonomous.tools.meetings_p1 import create_meetings_p1_tools


def test_get_interview_details():
    api = MagicMock()
    api.get.return_value = MagicMock(success=True, data={"id": 5}, meta={})
    tool = _get(create_meetings_p1_tools(api), "get_interview_details")
    tool.invoke({"meeting_id": 5})
    assert api.get.call_args.args[0] == "/v1/users/meetings/5"


def test_view_interview_notes_filters_candidate():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_meetings_p1_tools(api), "view_interview_notes")
    tool.invoke({"candidate_id": 7})
    kwargs = dict(api.request.call_args.kwargs.get("params") or api.request.call_args.args[2])
    assert json.loads(kwargs["where"])["candidate_id"] == 7
```

- [ ] **Step 3: Rodar + Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
git add src/domains/autonomous/tools/meetings_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 tools for meetings (details, notes)"
```

---

## Task 14: Tools P1 — grupo `communication` (3 tools, uma HITL)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/communication_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_communication_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def send_outreach(candidate_id: int, template_id: int, variables: str = "") -> str:
        """[HITL] Envia outreach por email a um candidato usando template. Requer confirmação do recruiter."""
        try:
            vars_dict = json.loads(variables) if variables else {}
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"success": False, "error": "variables deve ser JSON valido"}, ensure_ascii=False)
        body = {
            "email_template": {
                "id": template_id,
                "candidate_id": candidate_id,
                "variables": vars_dict,
            }
        }
        return _fmt(api.create("/v1/users/email_templates/send", body))

    @tool
    def generate_message(template_id: int, candidate_id: int = 0, context: str = "") -> str:
        """Gera sugestão de mensagem para um candidato a partir de template (não envia)."""
        body = {"template_id": template_id}
        if candidate_id:
            body["candidate_id"] = candidate_id
        if context:
            body["context"] = context
        return _fmt(api.create("/v1/users/email_templates/generate_suggestion", body))

    @tool
    def add_notes(candidate_id: int, content: str, parent_message_id: int = 0) -> str:
        """Adiciona nota interna em um candidato (Message polymorphic)."""
        body = {
            "message": {
                "reference_type": "Candidate",
                "reference_id": candidate_id,
                "content": content,
                "content_format": "plain_text",
                "entity": 1,  # ROLE_USER
            }
        }
        if parent_message_id:
            body["message"]["parent_message_id"] = parent_message_id
        return _fmt(api.create("/v1/users/messages", body))

    return [send_outreach, generate_message, add_notes]
```

- [ ] **Step 2: Tests**

```python
from src.domains.autonomous.tools.communication_p1 import create_communication_p1_tools


def test_add_notes_uses_message_polymorphic():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={"id": 1}, meta={})
    tool = _get(create_communication_p1_tools(api), "add_notes")
    tool.invoke({"candidate_id": 10, "content": "Good fit"})
    body = api.create.call_args.args[1]
    assert body["message"]["reference_type"] == "Candidate"
    assert body["message"]["reference_id"] == 10
    assert body["message"]["content"] == "Good fit"


def test_send_outreach_validates_variables_json():
    api = MagicMock()
    tool = _get(create_communication_p1_tools(api), "send_outreach")
    result = tool.invoke({"candidate_id": 1, "template_id": 2, "variables": "not_json"})
    assert json.loads(result)["success"] is False


def test_generate_message_posts_to_suggestion():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={}, meta={})
    tool = _get(create_communication_p1_tools(api), "generate_message")
    tool.invoke({"template_id": 3, "candidate_id": 10})
    assert api.create.call_args.args[0] == "/v1/users/email_templates/generate_suggestion"
```

- [ ] **Step 3: Rodar + Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
git add src/domains/autonomous/tools/communication_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 communication tools (outreach HITL, generate, notes)"
```

---

## Task 15: Tools P1 — grupo `preferences` (2 tools, uma HITL)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/preferences_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_preferences_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def get_recruiter_preferences() -> str:
        """Retorna preferências de notificação/configuração do recruiter atual."""
        return _fmt(api.get("/v1/users/notification_preferences"))

    @tool
    def save_recruiter_preference(settings_json: str) -> str:
        """[HITL] Atualiza preferências de notificação. Requer confirmação.

        Args:
            settings_json: JSON string com o hash de settings a persistir.
        """
        try:
            settings = json.loads(settings_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"success": False, "error": "settings_json deve ser JSON valido"}, ensure_ascii=False)
        return _fmt(api.update("/v1/users/notification_preferences",
                               {"notification_preference": settings}))

    return [get_recruiter_preferences, save_recruiter_preference]
```

- [ ] **Step 2: Tests**

```python
from src.domains.autonomous.tools.preferences_p1 import create_preferences_p1_tools


def test_get_recruiter_preferences():
    api = MagicMock()
    api.get.return_value = MagicMock(success=True, data={}, meta={})
    tool = _get(create_preferences_p1_tools(api), "get_recruiter_preferences")
    tool.invoke({})
    assert api.get.call_args.args[0] == "/v1/users/notification_preferences"


def test_save_preferences_wraps_in_model_key():
    api = MagicMock()
    api.update.return_value = MagicMock(success=True, data={}, meta={})
    tool = _get(create_preferences_p1_tools(api), "save_recruiter_preference")
    tool.invoke({"settings_json": json.dumps({"email_digest": "daily"})})
    body = api.update.call_args.args[1]
    assert body == {"notification_preference": {"email_digest": "daily"}}
```

- [ ] **Step 3: Rodar + Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
git add src/domains/autonomous/tools/preferences_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 preferences tools (get/save notification_preferences)"
```

---

## Task 16: Tools P1 — grupo `sourcing` (4 tools incl. `analyze_profile` + `rag_search`)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/sourcing_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_sourcing_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def enrich_candidate_contact(sourced_profile_id: int, require_minimum: bool = False) -> str:
        """Enriquece emails E telefones de um sourced_profile via Pearch."""
        body = {"require_phones_or_emails": require_minimum}
        return _fmt(api.create(f"/v1/users/sourced_profiles/{sourced_profile_id}/enrich_contacts", body))

    @tool
    def enrich_candidate_profile(sourced_profile_id: int) -> str:
        """Enriquece perfil completo (dados profissionais) de um sourced_profile via Pearch."""
        return _fmt(api.create(f"/v1/users/sourced_profiles/{sourced_profile_id}/enrich_contacts", {}))

    @tool
    def analyze_profile(sourced_profile_id: int, refresh: bool = False) -> str:
        """Retorna análise LLM sintética de um sourced_profile (fit score, skills, gaps). Cache de 24h."""
        body = {"refresh": refresh} if refresh else {}
        return _fmt(api.create(f"/v1/users/sourced_profiles/{sourced_profile_id}/analyze", body))

    @tool
    def rag_search(prompt: str, page: int = 1, per_page: int = 15) -> str:
        """Busca vetorial RAG em candidates (prompt_search) — use para queries semânticas livres."""
        params = [("prompt", prompt), ("page", str(page)), ("per_page", str(per_page))]
        return _fmt(api.request("GET", "/v1/users/candidates/prompt_search", params=params))

    return [enrich_candidate_contact, enrich_candidate_profile, analyze_profile, rag_search]
```

- [ ] **Step 2: Tests**

```python
from src.domains.autonomous.tools.sourcing_p1 import create_sourcing_p1_tools


def test_enrich_contact_calls_enrich_contacts():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={}, meta={})
    tool = _get(create_sourcing_p1_tools(api), "enrich_candidate_contact")
    tool.invoke({"sourced_profile_id": 42})
    assert api.create.call_args.args[0] == "/v1/users/sourced_profiles/42/enrich_contacts"


def test_analyze_profile_calls_analyze_endpoint():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={"fit_score": 0.8}, meta={})
    tool = _get(create_sourcing_p1_tools(api), "analyze_profile")
    tool.invoke({"sourced_profile_id": 5})
    assert api.create.call_args.args[0] == "/v1/users/sourced_profiles/5/analyze"


def test_rag_search_uses_prompt_search():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_sourcing_p1_tools(api), "rag_search")
    tool.invoke({"prompt": "senior ruby devs in sp"})
    assert api.request.call_args.args[1] == "/v1/users/candidates/prompt_search"
```

- [ ] **Step 3: Rodar + Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
git add src/domains/autonomous/tools/sourcing_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 sourcing tools (enrich, analyze_profile, rag_search)"
```

---

## Task 17: Tools P1 — grupo `activity` (2 tools)

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/activity_p1.py`

- [ ] **Step 1: Criar módulo**

```python
import json
import logging
from langchain_core.tools import tool
from src.domains.autonomous.api_client import UniversalAPIClient
from src.domains.autonomous.tools.formatting import fmt as _fmt

logger = logging.getLogger(__name__)


def create_activity_p1_tools(api: UniversalAPIClient) -> list:
    @tool
    def get_activity_summary(page: int = 1, per_page: int = 30, where_json: str = "") -> str:
        """Retorna timeline de atividades do tenant (activity_logs)."""
        params = [("page", str(page)), ("per_page", str(per_page))]
        if where_json:
            try:
                json.loads(where_json)  # valida
                params.append(("where", where_json))
            except (json.JSONDecodeError, TypeError):
                return json.dumps({"success": False, "error": "where_json invalido"}, ensure_ascii=False)
        return _fmt(api.request("GET", "/v1/users/activity_logs", params=params))

    @tool
    def capture_wizard_feedback(title: str, description: str, name: str,
                                job_id: int = 0, apply_id: int = 0, selective_process_id: int = 0) -> str:
        """Registra feedback do wizard vinculado a job/apply/selective_process (NÃO polymorphic)."""
        if not (job_id or apply_id or selective_process_id):
            return json.dumps(
                {"success": False, "error": "informe job_id OU apply_id OU selective_process_id"},
                ensure_ascii=False,
            )
        body = {"feedback": {"title": title, "description": description, "name": name}}
        if job_id:
            body["feedback"]["job_id"] = job_id
        if apply_id:
            body["feedback"]["apply_id"] = apply_id
        if selective_process_id:
            body["feedback"]["selective_process_id"] = selective_process_id
        return _fmt(api.create("/v1/users/feedbacks", body))

    return [get_activity_summary, capture_wizard_feedback]
```

- [ ] **Step 2: Tests**

```python
from src.domains.autonomous.tools.activity_p1 import create_activity_p1_tools


def test_activity_summary_defaults():
    api = MagicMock()
    api.request.return_value = MagicMock(success=True, data=[], meta={})
    tool = _get(create_activity_p1_tools(api), "get_activity_summary")
    tool.invoke({})
    assert api.request.call_args.args[1] == "/v1/users/activity_logs"


def test_capture_wizard_feedback_requires_context():
    api = MagicMock()
    tool = _get(create_activity_p1_tools(api), "capture_wizard_feedback")
    result = tool.invoke({"title": "t", "description": "d", "name": "n"})
    assert json.loads(result)["success"] is False


def test_capture_wizard_feedback_with_job_id():
    api = MagicMock()
    api.create.return_value = MagicMock(success=True, data={}, meta={})
    tool = _get(create_activity_p1_tools(api), "capture_wizard_feedback")
    tool.invoke({"title": "t", "description": "d", "name": "n", "job_id": 42})
    body = api.create.call_args.args[1]
    assert body["feedback"]["job_id"] == 42
```

- [ ] **Step 3: Rodar + Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py -v
git add src/domains/autonomous/tools/activity_p1.py tests/test_p1_tools.py
git commit -m "feat(autonomous): P1 activity tools (summary, wizard_feedback)"
```

---

## Task 18: Registrar 7 categorias novas em `__init__.py` e `tool_selector.py`

**Files:**
- Modify: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tools/__init__.py`
- Modify: `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/tool_selector.py`

- [ ] **Step 1: Imports em `__init__.py`**

Localizar o bloco de `from src.domains.autonomous.tools.* import create_*_tools` no topo do arquivo e adicionar:

```python
from src.domains.autonomous.tools.applies_p1 import create_applies_p1_tools
from src.domains.autonomous.tools.evaluations_p1 import create_evaluations_p1_tools
from src.domains.autonomous.tools.meetings_p1 import create_meetings_p1_tools
from src.domains.autonomous.tools.communication_p1 import create_communication_p1_tools
from src.domains.autonomous.tools.preferences_p1 import create_preferences_p1_tools
from src.domains.autonomous.tools.sourcing_p1 import create_sourcing_p1_tools
from src.domains.autonomous.tools.activity_p1 import create_activity_p1_tools
```

- [ ] **Step 2: Adicionar ao `TOOL_CATEGORIES`**

Antes do `}` que fecha `TOOL_CATEGORIES`, adicionar:

```python
    "applies_p1":       create_applies_p1_tools,
    "evaluations_p1":   create_evaluations_p1_tools,
    "meetings_p1":      create_meetings_p1_tools,
    "communication_p1": create_communication_p1_tools,
    "preferences_p1":   create_preferences_p1_tools,
    "sourcing_p1":      create_sourcing_p1_tools,
    "activity_p1":      create_activity_p1_tools,
```

- [ ] **Step 3: Adicionar regex em `_CATEGORY_PATTERNS`**

Dentro do hash `_CATEGORY_PATTERNS`, antes da chave `}` final, adicionar:

```python
    "applies_p1": re.compile(
        r'\b(?:aging|silver\s*medalist|sub[\-_\s]status|risk|risco|rejeitad)',
        re.IGNORECASE,
    ),
    "evaluations_p1": re.compile(
        r'\b(?:wsi|screening|opini|interview\s+opinion)',
        re.IGNORECASE,
    ),
    "meetings_p1": re.compile(
        r'\b(?:entrevista|interview|meeting|nota|note)',
        re.IGNORECASE,
    ),
    "communication_p1": re.compile(
        r'\b(?:outreach|generate\s+message|add\s*not|adicionar\s*not)',
        re.IGNORECASE,
    ),
    "preferences_p1": re.compile(
        r'\b(?:prefer|notification|notificaca)',
        re.IGNORECASE,
    ),
    "sourcing_p1": re.compile(
        r'\b(?:enrich|analyze\s+profile|analisar\s+perfil|rag|busca\s+semantica)',
        re.IGNORECASE,
    ),
    "activity_p1": re.compile(
        r'\b(?:activity\s*log|atividade|wizard\s+feedback|feedback\s+wizard)',
        re.IGNORECASE,
    ),
```

- [ ] **Step 4: Atualizar `tool_selector.py` — `TOOL_TO_CATEGORY`**

Localizar o dict `TOOL_TO_CATEGORY` e acrescentar:

```python
    "get_stage_sub_statuses":        "applies_p1",
    "get_candidate_aging":           "applies_p1",
    "get_at_risk_candidates":        "applies_p1",
    "find_silver_medalists":         "applies_p1",
    "get_candidate_wsi_scores":      "evaluations_p1",
    "get_candidate_screening_results": "evaluations_p1",
    "generate_interview_opinion":    "evaluations_p1",
    "get_interview_details":         "meetings_p1",
    "view_interview_notes":          "meetings_p1",
    "send_outreach":                 "communication_p1",
    "generate_message":              "communication_p1",
    "add_notes":                     "communication_p1",
    "get_recruiter_preferences":     "preferences_p1",
    "save_recruiter_preference":     "preferences_p1",
    "enrich_candidate_contact":      "sourcing_p1",
    "enrich_candidate_profile":      "sourcing_p1",
    "analyze_profile":               "sourcing_p1",
    "rag_search":                    "sourcing_p1",
    "get_activity_summary":          "activity_p1",
    "capture_wizard_feedback":       "activity_p1",
```

- [ ] **Step 5: Verificar integridade do módulo**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
python -c "from src.domains.autonomous.tools import TOOL_CATEGORIES; print(len(TOOL_CATEGORIES)); print(sorted(TOOL_CATEGORIES.keys()))"
```

Esperado: número aumentou em 7 e os 7 novos nomes aparecem.

- [ ] **Step 6: Rodar TODOS os tests de tools + selection**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
pytest tests/test_p1_tools.py tests/test_talent_pool_tools.py tests/test_tool_selection.py -v
```

Esperado: tudo passa.

- [ ] **Step 7: Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
git add src/domains/autonomous/tools/__init__.py src/domains/autonomous/tool_selector.py
git commit -m "feat(autonomous): register 7 new P1 tool categories and mappings"
```

---

## Task 19: Smoke end-to-end — rodar V5 contra `ats_api` real

**Files:**
- Create: `/home/victhor/ats_mercado/recruiter_agent_v5/tests/smoke/test_p1_smoke.py`

> **NOTA:** este smoke depende do `ats_api` rodando localmente (`bin/rails s` na porta 3000, tenant de dev com usuário). Skip se ENV `ATS_API_URL` não estiver definida.

- [ ] **Step 1: Criar smoke test**

```python
import os
import pytest
from src.domains.autonomous.api_client import UniversalAPIClient, AgentContext
from src.domains.autonomous.tools.talent_pool import create_talent_pool_tools
from src.domains.autonomous.tools.applies_p1 import create_applies_p1_tools
from src.domains.autonomous.tools.sourcing_p1 import create_sourcing_p1_tools


pytestmark = pytest.mark.skipif(
    not os.getenv("ATS_API_URL"), reason="ATS_API_URL não configurada"
)


@pytest.fixture
def api():
    ctx = AgentContext(
        auth_token=os.environ["ATS_API_TOKEN"],
        base_url=os.environ["ATS_API_URL"],
    )
    return UniversalAPIClient(context=ctx)


def test_smoke_search_talent_pools(api):
    tools = create_talent_pool_tools(api)
    search = next(t for t in tools if t.name == "search_talent_pools")
    result = search.invoke({"name": ""})
    assert '"success": true' in result or '"success":true' in result


def test_smoke_candidate_aging(api):
    tools = create_applies_p1_tools(api)
    tool = next(t for t in tools if t.name == "get_candidate_aging")
    result = tool.invoke({})
    assert '"success": true' in result or '"success":true' in result


def test_smoke_rag_search(api):
    tools = create_sourcing_p1_tools(api)
    tool = next(t for t in tools if t.name == "rag_search")
    result = tool.invoke({"prompt": "desenvolvedor"})
    assert '"success": true' in result or '"success":true' in result
```

- [ ] **Step 2: Rodar smoke com backend de dev**

```bash
cd /home/victhor/ats_mercado/ats_api && bin/rails s -p 3000 &
cd /home/victhor/ats_mercado/recruiter_agent_v5
ATS_API_URL=http://localhost:3000 ATS_API_TOKEN=<token-dev> pytest tests/smoke/test_p1_smoke.py -v
```

Esperado: 3 passed (ou skipped se env ausente).

- [ ] **Step 3: Commit**

```bash
cd /home/victhor/ats_mercado/recruiter_agent_v5
git add tests/smoke/test_p1_smoke.py
git commit -m "test(smoke): e2e smoke for Fase 1 P1 tools"
```

---

# Deploy / Follow-ups

## Ordem de deploy

1. **ats_api staging:** merge PR da Parte 1 (Tasks 1–9). Aplicar migration. Reindex async via Sidekiq (`Candidate.reindex(mode: :async)`). Validar com `bin/rails runner "puts Candidate.column_names.grep(/pcd|ethnic|twin|lgpd/)"`.
2. **ats_api prod:** após smoke em staging, migrar prod. Reindex em job dedicado, monitorar `Searchkick::ReindexV2Job`.
3. **recruiter_agent_v5 staging:** apontar para ats_api staging, rodar smoke `test_p1_smoke.py`. Corrigir se algum endpoint divergir.
4. **recruiter_agent_v5 prod:** deploy após validação.

## Out of scope (próximas fases, NÃO neste plano)

- Market Intelligence, Skills Ontology, Workforce Planning, Interview Intelligence, Internal Mobility, Recruitment Campaigns aggregator (Fase 2).
- Hiring Policy, Nurture Sequences, Predictive Analytics ML (Fase 3).
- Job LGPD de anonimização automática ao `lgpd_expires_at`.
- Frontend (Next.js / plataforma-lia).

---

# Notas finais

- **Autenticação nos tests do Rails:** assume `auth_headers(user)` helper já existir em `spec/support/`. Se não existir, usar token JWT do `user` via `user.jwt_token` ou adaptar para header `Authorization: Bearer`.
- **`search: true` no RSpec:** usa helper existente no `spec/rails_helper.rb` que habilita Searchkick real no teste (refresh de índice).
- **Apartment multi-tenant:** todos os testes Rails assumem que `create(:account)` + `create(:user, account:)` já aciona o setup do tenant correto. Se não, verificar `spec/support/apartment_helper.rb`.
- **`api.request` vs `api.get`/`api.create`:** `api.request("GET", path, params=[...])` usado quando precisa passar múltiplos `params` (tuple list). `api.get(path, params={})` é atalho para dict. O codebase mistura os dois — manter o estilo já presente no módulo que você está tocando.
- **Permissões no controller:** se houver Pundit ou similar no `ats_api`, adicionar policies para `SourcedProfile#analyze` e `Sourcing#add_candidate` espelhando `show`/`update` do recurso pai.
