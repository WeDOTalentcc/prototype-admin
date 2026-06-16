---
applyTo: "**/*search*.rb,**/*searchable*.rb,**/*searchkick*.rb,app/models/concerns/searchable.rb"
---

# Searchkick & Elasticsearch — WeDO Talent ATS

## Stack

- **searchkick ~> 5.3** with **Elasticsearch >= 8.x**
- Tenant-scoped indexes via `Searchable` concern
- `SearchService` builds search queries
- Controller concerns: `SearchRenderer`, `SearchParams`

## Searchable Concern (app/models/concerns/searchable.rb)

Every searchable model includes `Searchable`:

```ruby
# frozen_string_literal: true

module Searchable
  extend ActiveSupport::Concern

  included do
    searchkick index_name: -> { tenant_index_name }
  end

  module ClassMethods
    def tenant_index_name
      tenant = Apartment::Tenant.current
      tenant = "public" if Apartment.excluded_models.include?(model_name)
      [tenant, model_name.plural, Rails.env].join("_")
    end

    def search_fields
      [:id]
    end

    def agg_search_array(_params = {})
      {}
    end

    def comparison_search_terms
      []
    end

    def default_search_order
      { created_at: :desc }
    end

    def search_default(search_text, params = {}, page = 1, build_where_for_autocomplete = false, current_user_id = nil, include_aggregators = false)
      params ||= {}

      if column_names.include?("is_deleted")
        params[:where] = (params[:where] || {}).merge(is_deleted: [false, nil])
      end

      params[:order] ||= default_search_order

      fields_to_search = build_where_for_autocomplete ? false : (respond_to?(:search_fields) ? search_fields : [:id])

      force_aggregators = params.delete(:force_aggregators)
      should_include_aggs = force_aggregators || include_aggregators
      aggs_to_use = should_include_aggs && respond_to?(:agg_search_array) ? agg_search_array(params) : {}
      comparison_terms = respond_to?(:comparison_search_terms) ? comparison_search_terms : false

      search_options = {
        operator: "and",
        page: page || 1,
        limit: params[:limit] || 30,
        smart_aggs: true,
        body_options: { track_total_hits: true },
        aggs: aggs_to_use,
        fields: fields_to_search,
        current_user_id: current_user_id
      }.merge(params)

      SearchService.build(self, search_text, search_options, comparison_terms)
    end
  end
end
```

## Model search_data

Each model defines `search_data` returning a hash of indexed fields:

```ruby
class Job < ApplicationRecord
  include Searchable

  def search_data
    {
      title: title,
      description: description,
      external_id: external_id,
      is_active: is_active,
      is_deleted: is_deleted,
      confidential: confidential,
      published_date: published_date,
      city: city,
      state: state,
      country: country,
      department_id: department_id,
      user_id: user_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [:title, :external_id, :city, :state]
  end

  def self.default_search_order
    { created_at: :desc }
  end
end
```

## Index Naming

Format: `{tenant}_{model_plural}_{environment}`

Examples:
- `acme_jobs_production`
- `wedo_candidates_development`
- `public_users_test` (for excluded models)

## Controller Integration

### SearchRenderer Concern

```ruby
module SearchRenderer
  def perform_search(model:, serializer:, search_with_pin: false, compact: false)
    search_result = model.search_default(
      search_text,
      search_params_hash,
      page_param,
      false,
      @current_user&.id,
      include_aggregators?
    )
    render_search_results(search_result, serializer, compact)
  end
end
```

### SearchParams Concern

Parses `where`, `order`, `filter`, `page`, `per_page` from request params. Handles JSON parsing, boolean coercion, pin/confidential filtering.

### Usage in Controllers

```ruby
class V1::Users::JobsController < ApplicationController
  include SearchRenderer
  include SearchParams

  def index
    perform_search(model: Job, serializer: JobSerializer, search_with_pin: true)
  end
end
```

## Aggregations

```ruby
def self.agg_search_array(params = {})
  {
    employment_type: { where: params[:where]&.except(:employment_type) || {} },
    workplace_type: { where: params[:where]&.except(:workplace_type) || {} },
    city: { where: params[:where]&.except(:city) || {} },
    is_active: {}
  }
end
```

## Rules

- Always include `Searchable` (never raw `searchkick` call)
- Always define `search_data` for indexed fields
- Override `search_fields` with searchable text fields
- Override `default_search_order` when needed
- Soft-deleted records are auto-excluded via `is_deleted: [false, nil]`
- Reindex in tenant context: `Apartment::Tenant.switch(tenant) { Model.reindex }`
- Use `reindex(mode: :async)` in production for large datasets
- Use `callbacks: :async` for async index updates when available
- Never call `Model.search` directly in controllers — use `SearchRenderer#perform_search`
