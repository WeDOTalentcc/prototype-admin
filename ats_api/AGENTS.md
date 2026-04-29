# AGENTS.md — WeDO Talent ATS Backend

## Project Overview

**WeDO Talent** is a multi-tenant Applicant Tracking System (ATS) built as a **Rails 7.1 API-only** application. It manages recruitment workflows: jobs, candidates, applications, evaluations, interviews, sourcing, and AI-powered features (hybrid search, embeddings, LLM-based scoring).

## Tech Stack

| Component | Technology |
|---|---|
| Framework | Rails 7.1, API-only, Ruby 3.2+ |
| Database | PostgreSQL 15 with pgvector extension |
| Multi-tenancy | ros-apartment (schema-based isolation) |
| Search | Searchkick ~5.3 + Elasticsearch 8.x |
| Background Jobs | Sidekiq 7 + sidekiq-cron |
| Messaging | RabbitMQ (sneakers + bunny) |
| Auth | JWT (custom), WorkOS SSO |
| Authorization | Pundit |
| Serialization | jsonapi-serializer (JSON:API format) |
| LLM | Google Gemini (gemini-ai gem) |
| Embeddings | pgvector + neighbor gem (768-dim, gemini-embedding-001) |
| WebSockets | ActionCable |
| Caching | Redis |
| PDF | Prawn |
| Container | Docker + Docker Compose |

## Running the Project

```bash
make build        # Build Docker images
make up           # Start all services
make shell        # Open shell in web container
make console      # Rails console
make db-migrate   # Run migrations
make logs-web     # Tail web logs
make logs-sidekiq # Tail sidekiq logs
```

### Running Tests

```bash
docker compose exec web bundle exec rspec                        # All specs
docker compose exec web bundle exec rspec spec/models/           # Model specs
docker compose exec web bundle exec rspec spec/services/         # Service specs
docker compose exec web bundle exec rspec spec/requests/         # Request specs
docker compose exec web bundle exec rspec spec/path/to_spec.rb   # Single file
```

### Running Migrations

```bash
docker compose exec web bin/rails db:migrate          # Tenant migrations
docker compose exec web bin/rails db:migrate:public   # Public-only migrations
```

Generate migrations via Rails generator (ensures correct timestamp):

```bash
docker compose exec web bin/rails g migration AddColumnToTable column:type
```

## Architecture

### Directory Structure

```
app/
├── controllers/     # API controllers (V1::Users::*, V1::Services::*)
├── models/          # ActiveRecord models + concerns
├── services/        # Service objects (business logic)
├── serializer/      # JSONAPI::Serializer classes
├── jobs/            # Sidekiq/ActiveJob background jobs
├── workers/         # Legacy Sidekiq workers
├── policies/        # Pundit authorization policies
├── channels/        # ActionCable channels
├── mailers/         # ActionMailer classes
├── validators/      # Custom validators
├── middlewares/     # Rack middleware
├── lib/             # Shared libraries
└── helpers/         # View helpers
config/
├── routes.rb        # Main routes
├── sidekiq.yml      # Queue configuration
├── initializers/
│   └── apartment.rb # Multi-tenancy config
db/
├── migrate/         # Tenant migrations
├── migrate_public/  # Public schema migrations
└── schema.rb        # Current schema
spec/
├── models/          # Model specs
├── services/        # Service specs
├── requests/        # Controller/integration specs
├── jobs/            # Job specs
├── factories/       # FactoryBot factories
└── support/         # Test helpers
```

### Multi-Tenancy

Every `Account` has a `tenant` column mapping to a PostgreSQL schema. Tenant switching happens:

- **Automatically** in controllers via `Authenticable` concern (JWT → account → `Apartment::Tenant.switch!`)
- **Manually** in jobs via `Apartment::Tenant.switch(account.tenant) { ... }`

**Excluded models** (live in `public` schema): Account, User, Role, UserRole, Language, City, State, Country, Sector, ApiClient, RequestKey, WhatsappTenantMapping, LlmUsage, LlmQuota, LlmQuotaUsage.

### Request Flow

1. Request hits controller
2. `Authenticable#authorize_request` decodes JWT, finds account, switches tenant
3. `Current.user` and `Current.account` are set
4. Controller action executes (search via `SearchRenderer` or CRUD via `RenderDefault`)
5. Response serialized via `JSONAPI::Serializer`

### Controller Concerns

| Concern | Purpose |
|---|---|
| `Authenticable` | JWT auth, tenant switching, `Current` setup |
| `SearchRenderer` | `perform_search` → Searchkick integration |
| `SearchParams` | Parse `where`, `order`, `filter`, `page` params |
| `RenderDefault` | `render_success`, `render_error`, `render_not_found` |
| `Pinnable` | Pin/confidential user array management |
| `SparseFieldsets` | AI field presets for candidates/jobs |

### Model Concerns

| Concern | Purpose |
|---|---|
| `AccountScopable` | Auto-assigns `account_id` from `Current.user` |
| `Searchable` | Searchkick setup with tenant-scoped index names |
| `HasActivityLog` | After-commit activity logging |
| `TracksJobAnalytics` | Enqueues analytics refresh on commit |
| `UidGeneratable` | Auto-generates UUID on create |

## Coding Conventions

### Language

All code, tests, variables, and API responses MUST be in **English**.

### No Comments

Do not write comments. Use descriptive method and variable names. Exceptions: YARD docs for public APIs, WHY-not-WHAT explanations, TODO/FIXME.

### Style

- 2-space indentation, max 120 chars, `frozen_string_literal: true`
- `snake_case` for methods/variables, `CamelCase` for classes, `SCREAMING_CASE` for constants
- Early return (never nested if/else)
- Hash lookup over case/when
- `pluck` over `map`, `find_by` over `where.first`, `find_each` for batches

### Services

```ruby
module Namespace
  class VerbNounService
    def initialize(param:)
      @param = param
    end

    def call
      return error_result("Invalid") if invalid?
      success_result(execute)
    end

    private

    attr_reader :param
  end
end
```

Return `{ success: true/false, ... }` hashes.

### Controllers

```ruby
class V1::Users::ResourcesController < ApplicationController
  include SearchRenderer
  include SearchParams
  include Pinnable

  before_action :set_resource, only: [:show, :update, :destroy]

  def index
    perform_search(model: Resource, serializer: ResourceSerializer)
  end

  def show
    render_success(@resource, serializer: ResourceSerializer, status: :ok)
  end

  def create
    resource = Resource.new(resource_params)
    return render_error(resource, status: :unprocessable_entity) unless resource.save
    render_success(resource, serializer: ResourceSerializer, status: :created)
  end

  private

  def set_resource
    @resource = Resource.find(params[:id])
  end

  def resource_params
    params.require(:resource).permit(:field1, :field2)
  end
end
```

### Jobs

Always pass IDs. Always switch tenant. Always rescue with logging.

```ruby
class MyJob
  include Sidekiq::Job
  sidekiq_options queue: :default, retry: 3

  def perform(record_id, account_id)
    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch(account.tenant) do
      record = MyModel.find_by(id: record_id)
      return unless record
      do_work(record)
    end
  rescue StandardError => e
    Rails.logger.error "[#{self.class.name}] #{e.message}"
    raise
  end
end
```

## How to Add a New Feature

### New Model

1. Generate migration: `docker compose exec web bin/rails g migration CreateResources name:string account:references`
2. Create model in `app/models/resource.rb` — include `Searchable` if needed
3. Create factory in `spec/factories/resources.rb`
4. Create spec in `spec/models/resource_spec.rb`

### New CRUD Endpoint

1. Add route in `config/routes.rb` under the appropriate namespace
2. Create controller in `app/controllers/v1/users/resources_controller.rb`
3. Create serializer in `app/serializer/resource_serializer.rb`
4. Create service if business logic is complex
5. Create request spec in `spec/requests/v1/users/resources_spec.rb`

### New Background Job

1. Create job in `app/jobs/namespace/verb_noun_job.rb`
2. Include `Sidekiq::Job`, set `sidekiq_options`
3. Ensure `Apartment::Tenant.switch` in `perform`
4. Create spec in `spec/jobs/namespace/verb_noun_job_spec.rb`

## Environment Variables

Key variables (see `.env` for full list):

- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Redis for Sidekiq/caching
- `ELASTICSEARCH_URL` — Elasticsearch endpoint
- `GEMINI_API_KEY` — Google Gemini API key
- `GEMINI_CHAT_MODEL` — Chat model (default: `gemini-2.0-flash`)
- `GEMINI_FAST_MODEL` — Fast model for analysis
- `EMBEDDING_MODEL` — Embedding model (default: `gemini-embedding-001`)
- `WORKOS_API_KEY` — WorkOS SSO key
- `WORKOS_CLIENT_ID` — WorkOS client ID
