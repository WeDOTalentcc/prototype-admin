---
applyTo: "app/controllers/**/*.rb"
---

# Rails Controllers — WeDO Talent ATS

## Inheritance & Concerns

All API controllers inherit from `ApplicationController` which includes:
- `Authenticable` — JWT auth, tenant switching via `Apartment::Tenant.switch!`
- `SparseFieldsets` — AI presets for field filtering
- Controllers also include `SearchRenderer`, `SearchParams`, `RenderDefault`, `Pinnable` as needed

Namespace: `V1::Users::` for authenticated endpoints.

```ruby
# frozen_string_literal: true

module V1
  module Users
    class JobsController < ApplicationController
      include Pinnable

      before_action :set_job, only: %i[show update destroy]

      # actions...

      private

      def set_job
        @job = Job.include_base.where(is_deleted: false).find_by(id: params[:id])
        render_not_found("Job") unless @job
      end
    end
  end
end
```

## Rendering Responses

Use `RenderDefault` concern methods — never call `render json:` with raw model data:

```ruby
# ✅ Success with serializer
render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })

# ✅ Success with status
render_success(@job, serializer: JobSerializer, status: :created)

# ✅ Error
render_error(@job, status: :unprocessable_entity)

# ✅ Not found
render_not_found("Job")

# ✅ Simple error message
render_simple_error("Invalid parameters", status: :bad_request)

# ✅ Analytics/stats (plain JSON, not JSON:API)
render json: analytics_data, status: :ok

# ❌ Never
render json: @job.as_json
render json: { data: @job }
```

## Index Actions (Search)

Use `perform_search` from `SearchRenderer` — delegates to Searchkick:

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

`perform_search` handles:
- Full-text search via `search` param
- Structured filters via `where`/`filter` params (JSON)
- Ordering via `order` param
- Pagination: `page`, `per_page` (max 30)
- Compact mode: returns only specified fields
- Aggregations when `include_aggregators: true`

Response format (JSON:API):

```json
{
  "data": [{ "id": "1", "type": "job", "attributes": { ... } }],
  "meta": { "total": 50, "where": { "is_deleted": false } }
}
```

## Show Actions

```ruby
def show
  render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
end
```

## Create Actions

```ruby
def create
  @job = @current_user.jobs.build(job_params.merge(account_id: @current_user.account_id))

  if @job.save
    render_success(@job, serializer: JobSerializer, status: :created)
  else
    render_error(@job, status: :unprocessable_entity)
  end
end
```

For complex creation, delegate to a service:

```ruby
def create
  result = Jobs::CreateService.new(params: job_params, user: @current_user).call
  if result[:success]
    render_success(result[:job], serializer: JobSerializer, status: :created)
  else
    render json: { errors: [result[:error]] }, status: :unprocessable_entity
  end
end
```

## Update Actions

```ruby
def update
  if @job.update(job_params)
    render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
  else
    render_error(@job)
  end
end
```

## Destroy Actions

Prefer soft-delete over actual destroy:

```ruby
# ✅ Soft delete
def destroy
  @job.update!(is_deleted: true)
  render_success(@job, serializer: JobSerializer)
end

# Only when model truly uses destroy:
def destroy
  @job.destroy
  render_success(@job, serializer: JobSerializer)
end
```

## Custom Actions

Use service objects for business logic:

```ruby
def publish
  result = Jobs::PublishService.new(job: @job).publish
  if result[:success]
    render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user })
  else
    render json: { errors: [result[:error]] }, status: :unprocessable_entity
  end
end

def stats
  data = Jobs::StatsService.new(
    account_id: @current_user.account_id,
    start_date: params[:start_date],
    end_date: params[:end_date]
  ).call
  render json: data, status: :ok
end
```

## Strong Params

```ruby
private

def job_params
  params.require(:job).permit(
    :title, :description, :user_id, :department, :employment_type,
    :city, :state, :workplace_type, :salary_from, :salary_to,
    responsibilities: [],
    selective_processes_attributes: [:id, :name, :status, :position, :_destroy]
  )
end
```

## Pin & Confidential

Use `Pinnable` concern for pin/confidential user arrays:

```ruby
include Pinnable

# In update:
params_to_update = inject_pin_and_confidential(job_params, @job)

# In index:
new_params = search_with_pin_and_confidential
```

## Rules

- **Skinny controllers** — max 5-7 lines per action, delegate to services
- **Never query directly** — use Searchkick for lists, `find_by` for single records
- **Strong params** — always use `params.require().permit()`
- **before_action** for loading resources, auth, authorization
- **No business logic** — extract to service objects
- **Error handling** — centralized in `ApplicationController` via `rescue_from`
