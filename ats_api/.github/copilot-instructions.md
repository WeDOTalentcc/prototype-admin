# GitHub Copilot Instructions — WeDO Talent ATS

## Project Overview

Multi-tenant ATS (Applicant Tracking System) with integrated AI. API-only Ruby on Rails serving a Vue/Nuxt frontend.

**Stack:** Ruby 3.2+ (YJIT) / Rails 7.1 API-only / PostgreSQL 15+ / Elasticsearch 8.x (Searchkick) / Sidekiq 7 / Redis / Google Gemini (LLM) / pgvector (embeddings)

**Multi-tenancy:** `ros-apartment` gem — one PostgreSQL schema per tenant. Tenant resolved from JWT in `Authenticable` concern → `Apartment::Tenant.switch!`. Global models (public schema): `Account`, `User`, `ApiClient`, `Role`, `Language`, `City`, `State`, `Country`, `LlmUsage`, `LlmQuota`.

**Frontend:** Vue 3 / Nuxt (separate repo) — never generate views, HTML, or frontend code.

---

## Critical: English-Only Code

EVERYTHING in English: class names, method names, variable names, migration columns, test descriptions, error messages, API field names. **Never use Portuguese in code.**

---

## No Code Comments

Do not write comments. If code needs comments, refactor it to be self-explanatory.

**Exceptions:** YARD docs for public APIs, complex algorithms (WHY not WHAT), TODO/FIXME markers.

---

## Ruby Style

```ruby
# frozen_string_literal: true at top of every .rb file
# 2 spaces indent, max 120 chars, UTF-8
# snake_case: methods/vars/files | CamelCase: classes | SCREAMING_SNAKE: constants
# Predicates: valid? | Dangerous: save! | Never: get_/set_/is_
```

### Early Return — Always

```ruby
# ✅
def process(user)
  return if user.blank?
  return unless user.active?

  do_work(user)
end

# ❌ Never nested if/else
```

### Hash Over Case/Switch

```ruby
HANDLERS = {
  create: ->(params) { CreateService.call(params) },
  update: ->(params) { UpdateService.call(params) }
}.freeze

def handle(action, params)
  HANDLERS.fetch(action) { raise ArgumentError, "Unknown action: #{action}" }.call(params)
end
```

### Collections

```ruby
items.map(&:name)                          # &:symbol when possible
items.select(&:active?).map(&:name)        # chain over each + push
users.each { |u| process(u) }             # { } single-line
data.each do |item|                        # do/end multi-line
  validate(item)
  save(item)
end
```

---

## Controllers

Inherit from `ApplicationController` (which includes `Authenticable`, `SparseFieldsets`). Controllers under `V1::Users::` namespace.

### Rendering

Use `RenderDefault` concern methods:

```ruby
render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
render_success(@job, serializer: JobSerializer, status: :created)
render_error(@job, status: :unprocessable_entity)
render_not_found("Job")
render_simple_error("Invalid params", status: :bad_request)
```

### Search/Index Actions

Use `SearchRenderer` concern — `perform_search` delegates to Searchkick:

```ruby
def index
  new_params = search_with_pin_and_confidential
  new_params[:where][:is_deleted] = false unless new_params[:where].key?(:is_deleted)

  perform_search(
    model: Job,
    serializer: JobSerializer,
    search_with_pin: new_params,
    compact: params[:compact]&.split(",") || []
  )
end
```

### Resource Loading

```ruby
before_action :set_job, only: %i[show update destroy]

private

def set_job
  @job = Job.include_base.where(is_deleted: false).find_by(id: params[:id])
  render_not_found("Job") unless @job
end
```

### Strong Params

```ruby
def job_params
  params.require(:job).permit(:title, :description, :user_id, :department, responsibilities: [])
end
```

### Rules

- Skinny controllers — delegate logic to services
- Never do queries directly in controller
- Analytics/stats endpoints return plain JSON (not JSON:API)
- Soft-delete: set `is_deleted: true`, never `destroy` (except when the model truly uses `destroy`)
- Use `before_action` for auth, resource loading, authorization

---

## Models

### Block Ordering

```
includes/concerns → enums → constants → associations → validations → scopes → callbacks → class methods → instance methods → private
```

### Associations

Always specify `dependent:`:

```ruby
has_many :applies, dependent: :destroy
has_many :skill_relationships, as: :reference, dependent: :destroy
has_many :skills, through: :skill_relationships
belongs_to :user, optional: true
belongs_to :account, optional: true
has_one :embedding_record, class_name: "Embedding", as: :reference, dependent: :destroy
```

### Enums

Hash with explicit integers, never array:

```ruby
# ✅
enum evaluation_candidate_status: { pending: 0, sent: 1, answered: 2 }

# ❌
enum :status, [:pending, :sent, :answered]
```

### Concerns Used

- `Searchable` — adds Searchkick with tenant-scoped index names
- `HasActivityLog` — auto-logs create/update/destroy to `ActivityLog`
- `AccountScopable` — auto-assigns `account_id` from `Current.user`
- `UidGeneratable` — generates UUID `uid` on create
- `TracksJobAnalytics` — enqueues analytics refresh on changes
- `RemunerableAttributes` — shared salary/remuneration helpers

### Searchkick Integration

Every searchable model includes `Searchable` concern and defines `search_data`:

```ruby
class Candidate < ApplicationRecord
  include Searchable

  def search_data
    {
      name: name,
      email: email,
      role_name: role_name,
      city: city,
      source: source,
      skills: skills.pluck(:name),
      is_deleted: is_deleted,
      created_at: created_at
    }
  end
end
```

### Rules

- Never use `default_scope`
- Soft-delete via `is_deleted` boolean + named scope
- For jsonb: use `store_accessor` or typed accessor methods
- Callbacks: use sparingly, prefer services for side effects
- Validations with presence, uniqueness, numericality

---

## Services

Namespaced under module matching domain. Interface: `initialize(keyword_args:)` + `call`. Return hash with `success:` key.

```ruby
module Jobs
  class PublishService
    def initialize(job:)
      @job = job
    end

    def call
      return error("Not ready") unless ready?

      job.update!(published_date: Time.current, is_active: true)
      success
    end

    private

    attr_reader :job

    def success = { success: true, job: job }
    def error(message) = { success: false, error: message }
  end
end
```

### Services with LLM

Track every LLM call via `LlmUsage`:

```ruby
module Evaluations
  class ScoreCandidateService
    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      start_time = Time.current
      response = GeminiClient.new.chat(model: model_name, messages: build_messages, temperature: 0.1)
      track_llm_usage!(response, start_time)
      parse_and_persist_score(response)
    rescue Faraday::TimeoutError => e
      Rails.logger.error "[#{self.class.name}] Timeout: #{e.message}"
      fallback_score
    end

    private

    def track_llm_usage!(response, start_time)
      LlmUsage.create!(
        model: model_name,
        operation: "evaluation",
        input_tokens: response.dig("usage", "input_tokens"),
        output_tokens: response.dig("usage", "output_tokens"),
        cost_usd: calculate_cost(response),
        latency_ms: ((Time.current - start_time) * 1000).round,
        success: true,
        context: { service: self.class.name, candidate_id: @evaluation_candidate.candidate_id }
      )
    end
  end
end
```

### Rules

- One service = one responsibility (SRP)
- Handle errors internally — never let exceptions leak unhandled
- For long operations: extract to Sidekiq job that calls the service
- Naming: `VerbNounService` (e.g., `PublishService`, `CopyService`, `AnalyticsService`)
- Use `ENV.fetch("KEY", "default")` for env vars

---

## Serializers

`jsonapi-serializer` gem (`JSONAPI::Serializer`):

```ruby
class JobSerializer
  include JSONAPI::Serializer

  attributes :title, :description, :is_active, :city, :state, :published_date, :closing_deadline

  attribute :seniority_text do |job|
    Job::SENIORITY[job.seniority]
  end

  attribute :applies_count do |job|
    job.applies.where(is_deleted: false).size
  end

  attribute :pin do |job, params|
    next false unless params && params[:current_user]
    job.pin_user_ids&.include?(params[:current_user].id) || false
  end

  has_many :selective_processes
  belongs_to :user
  belongs_to :department
end
```

### Rules

- Never include sensitive data (tokens, passwords, CPF, salary in list views)
- Computed fields use block syntax
- Include `_text` variants for enums
- Use `params` hash for conditional attributes (e.g., admin-only fields)
- Always use serializer, never `model.as_json`

---

## Background Jobs (Sidekiq)

```ruby
module Jobs
  class RefreshAnalyticsJob
    include Sidekiq::Job

    sidekiq_options queue: :analytics, retry: 3

    def perform(job_id, account_id)
      account = Account.find(account_id)
      Apartment::Tenant.switch!(account.tenant) do
        job = Job.find(job_id)
        Jobs::AnalyticsService.new(job: job, force_refresh: true).call
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn "[#{self.class.name}] Record not found, skipping: #{e.message}"
    end
  end
end
```

### Rules

- ALWAYS `Apartment::Tenant.switch!` inside perform — tenant is NOT automatic in jobs
- Pass tenant/account_id as argument — never rely on `Current.user`
- Pass simple IDs, never Ruby objects (serialization)
- Idempotent — running twice must not cause duplicates
- `sidekiq_options` with explicit queue and retry
- For LLM jobs: add timeout + circuit breaker + fallback
- Queues: `default`, `mailers`, `analytics`, `llm`, `indexing`, `critical`

---

## Elasticsearch (Searchkick)

### Model Configuration

The `Searchable` concern auto-configures tenant-scoped index names:

```ruby
# Index name format: {tenant}_{model_plural}_{env}
# e.g., acme_corp_jobs_production
```

### Querying

Done via `SearchRenderer` concern in controllers. The `search_default` class method handles:
- Full-text search (`search` param or `"*"`)
- Structured filters (`where` param)
- Ordering (`order` param)
- Pagination (`page`, `per_page` max 30)
- Aggregations (`aggs` param)

### Rules

- Never `Model.reindex` inside a request — use `reindex_async` or Sidekiq job
- `search_data` method defines what gets indexed
- Data may have 1-2s delay (async reindex)
- For tests: stub `Model.search` or use `Searchkick.disable_callbacks`

---

## Multi-tenancy (Apartment)

### How It Works

1. JWT token → `Authenticable` concern decodes → finds `User` or `Account`
2. `Apartment::Tenant.switch!(account.tenant)` — all subsequent queries hit that schema
3. Each tenant has its own tables, Elasticsearch indexes, and embeddings

### Rules

- **Controllers:** Tenant switching is automatic via `Authenticable` concern
- **Sidekiq jobs:** MUST manually `Apartment::Tenant.switch!` with account.tenant
- **Rake tasks:** Iterate with `Apartment::Tenant.each { |t| ... }`
- **Never** access tenant data without proper switch — security violation
- **Global models** (Account, User, ApiClient, etc.) live in public schema
- `Apartment::Tenant.current` returns current schema name

---

## Testing (RSpec)

```ruby
RSpec.describe Jobs::PublishService do
  subject(:result) { described_class.new(job: job).call }

  let(:job) { create(:job, is_active: false) }

  context "when job is ready for publication" do
    before { allow_any_instance_of(Jobs::FieldRequirementChecker).to receive(:is_ready_for_publication?).and_return(true) }

    it "publishes the job" do
      expect(result[:success]).to be true
      expect(job.reload.is_active).to be true
    end
  end

  context "when job is not ready" do
    it "returns error" do
      expect(result[:success]).to be false
      expect(result[:error]).to be_present
    end
  end
end
```

### Rules

- `let` for lazy setup, `let!` only when eager needed
- `described_class` to reference tested class
- `context "when ..."` for scenarios
- `build_stubbed` for unit tests, `create` for integration
- `shared_examples` for common behaviors
- Multi-tenancy: `before { Apartment::Tenant.switch!(account.tenant) }`
- Stub Searchkick when not testing search
- VCR cassettes for external APIs (Gemini, Microsoft Graph)

---

## Logging

```ruby
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "🔄 [ClassName] Processing started"
Rails.logger.info "   Detail: #{value}"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

Emojis: 🔄 Processing | ✅ Success | ❌ Error | ⏳ Waiting | 🧠 LLM/AI | 🔍 Search | 🚀 Start

---

## Security (LGPD)

- Never log PII: `candidate.email`, `mobile_phone`, `cpf`, `current_salary`, `clt_expectation`
- Masking in logs: `joao****@email.com`
- Respect `confidential_user_ids` for confidential candidates
- Never expose tokens (`ms_access_token`, JWT) in responses or logs
- Use `Rails.application.credentials` for secrets, never hardcode

---

## Performance

- `pluck(:id)` over `map(&:id)` when only IDs needed
- `find_each` for batch iteration, never `.all.each`
- `includes`/`preload` to prevent N+1
- `select()` when not all columns needed
- Fragment caching with Redis for slowly-changing data
- `JobAnalyticsSnapshot` — cached metrics with 10min TTL
- Never `Model.reindex` in request — use async job
- Use `Time.current` not `Time.now` (timezone-aware)

---

## Anti-patterns — NEVER Do

- ❌ `Model.all` without filter
- ❌ N+1 queries — use `includes`/`preload`/`eager_load`
- ❌ Business logic in controller — extract to service
- ❌ `default_scope` — use named scopes
- ❌ `where("name = '#{input}'")` — SQL injection! Use `where(name: input)`
- ❌ Heavy callbacks — use services or jobs
- ❌ `update_all`/`delete_all` without WHERE clause
- ❌ `sleep()` anywhere — use Sidekiq scheduled jobs
- ❌ HTTP calls without timeout
- ❌ `puts`/`p` for debug — use `Rails.logger`
- ❌ Hardcoded secrets — use credentials
- ❌ Generic `rescue => e` without logging or re-raise
- ❌ Tenant data access without `Apartment::Tenant.switch!` in jobs
- ❌ `Model.reindex` inside request flow
- ❌ `Time.now` — use `Time.current`
- ❌ Enum as array: `enum :status, [:a, :b]` — use hash with explicit integers
- ❌ `model.as_json` — use serializer

---

## Naming Conventions

- **Services:** `VerbNounService` → `PublishService`, `CopyService`, `AnalyticsService`
- **Jobs:** `VerbNounJob` → `RefreshAnalyticsJob`, `ProcessCandidateJob`
- **Strategies:** `NounStrategy` → `ElasticsearchStrategy`, `EmbeddingStrategy`
- **Concerns:** `Adjective` or `HasNoun` → `Searchable`, `HasActivityLog`, `Pinnable`

---

## Git Commits

```
<type>(<scope>): <short description>

Types: feat | fix | refactor | perf | test | docs | chore
```

---

## Migrations

Always use `docker compose exec app rails g migration` to generate (avoids timestamp conflicts). Migrations run in ALL tenant schemas automatically via Apartment.
