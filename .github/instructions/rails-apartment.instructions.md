---
applyTo: "**/*.rb"
---

# Multi-Tenancy (ros-apartment) — WeDO Talent ATS

## Overview

This project uses **ros-apartment** (NOT the standard `apartment` gem) for PostgreSQL schema-based multi-tenancy. Each `Account` has a `tenant` column (string) that maps to a PostgreSQL schema.

## Configuration (config/initializers/apartment.rb)

```ruby
Apartment.configure do |config|
  config.persistent_schemas = %w[extensions]
  config.excluded_models = %w[
    Sector Account User Role UserRole Language City State Country
    ApiClient RequestKey WhatsappTenantMapping
    LlmUsage LlmQuota LlmQuotaUsage
  ]
  config.tenant_names = lambda { Account.pluck :tenant }
  config.default_tenant = "public"
end
```

## Key Concepts

### Excluded Models (Live in `public` Schema)

These models are shared across ALL tenants:

```
Account, User, Role, UserRole, Language, City, State, Country,
Sector, ApiClient, RequestKey, WhatsappTenantMapping,
LlmUsage, LlmQuota, LlmQuotaUsage
```

### Tenant-Scoped Models

Everything else (Job, Apply, Candidate, Evaluation, Department, Sourcing, etc.) lives in tenant-specific schemas.

### Persistent Schemas

`extensions` schema is always on the search_path so pgvector and other PostgreSQL extensions are accessible from all tenants.

## Tenant Switching

### In Controllers (Automatic)

The `Authenticable` concern handles tenant switching automatically on every authenticated request:

```ruby
module Authenticable
  def authorize_request
    # ... JWT decode ...
    account = Account.find(decoded[:account_id])
    Apartment::Tenant.switch!(account.tenant)
    Current.user = user
    Current.account = account
    @current_user = user
  end
end
```

### In Jobs/Workers (Manual — REQUIRED)

Every job accessing tenant data MUST switch tenant explicitly:

```ruby
def perform(record_id, account_id)
  account = Account.find_by(id: account_id)
  return unless account

  Apartment::Tenant.switch(account.tenant) do
    record = MyModel.find_by(id: record_id)
    return unless record

    do_work(record)
  end
end
```

**Block form** (`switch`) is preferred — it auto-restores the previous tenant. Use `switch!` only when the entire method operates in one tenant context.

### In Services

Services called from controllers inherit the tenant context. Services called from jobs must ensure tenant is set:

```ruby
Current.account = account
Apartment::Tenant.switch(account.tenant) do
  MyService.new(params).call
end
```

## AccountScopable Concern (app/models/concerns/account_scopable.rb)

Included in `ApplicationRecord`. Auto-assigns `account_id` from `Current.user`:

```ruby
module AccountScopable
  extend ActiveSupport::Concern

  included do
    belongs_to :account, optional: true
    before_validation :set_account_from_current_user, on: :create
  end

  private

  def set_account_from_current_user
    self.account_id ||= Current.user&.account_id
  end
end
```

## Current Thread-Local Storage

```ruby
Current.user     # Current authenticated user
Current.account  # Current account
```

Set in `Authenticable#authorize_request` for web requests. Must be set manually in background jobs.

## Migrations

### Tenant Migrations (db/migrate/)

Run on every tenant schema. Used for tenant-scoped tables (jobs, applies, candidates, etc.).

### Public Migrations (db/migrate_public/)

Run ONLY on the public schema. Used for excluded models (accounts, users, etc.).

### Running Migrations

```bash
docker compose exec web bin/rails db:migrate
docker compose exec web bin/rails db:migrate:public
```

### Creating Tenants

```ruby
Apartment::Tenant.create(account.tenant)
```

## Rules

- NEVER query tenant-scoped models without ensuring correct tenant is set
- ALWAYS use `Apartment::Tenant.switch` block form in jobs
- ALWAYS pass `account_id` to jobs (never rely on Current context)
- Excluded models are accessible from any tenant context
- Check `Apartment::Tenant.current` to verify active tenant
- Searchkick indexes are tenant-scoped: `{tenant}_{model}_{env}`
- `persistent_schemas = ["extensions"]` — pgvector lives here
- New tenant is created when `Account` is provisioned
