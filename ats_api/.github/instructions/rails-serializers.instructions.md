---
applyTo: "app/serializer/**/*.rb,app/serializers/**/*.rb"
---

# Rails Serializers — WeDO Talent ATS

## Gem & Pattern

Uses `jsonapi-serializer` gem (`JSONAPI::Serializer`). Directory: `app/serializer/`.

Response format:

```json
{
  "data": [
    {
      "id": "123",
      "type": "job",
      "attributes": {
        "title": "Dev Full Stack",
        "is_active": true
      }
    }
  ],
  "meta": {
    "total": 50,
    "where": { "is_deleted": false }
  }
}
```

## Standard Structure

```ruby
# frozen_string_literal: true

class JobSerializer
  include JSONAPI::Serializer

  attributes :title, :description, :is_active, :is_archived, :is_urgent,
             :city, :state, :country, :published_date, :application_deadline,
             :closing_deadline, :created_at, :updated_at

  attribute :seniority_text do |job|
    Job::SENIORITY[job.seniority]
  end

  attribute :employment_type_text do |job|
    Job::EMPLOYMENT_TYPES[job.employment_type]
  end

  attribute :applies_count do |job|
    job.applies.where(is_deleted: false).size
  end

  attribute :applies_by_status_count do |job|
    job.applies.where(is_deleted: false).group(:selective_process_status).count
  end

  has_many :selective_processes
  belongs_to :user
  belongs_to :department
end
```

## Computed Attributes

Use block syntax for any derived/calculated data:

```ruby
attribute :seniority_text do |job|
  Job::SENIORITY[job.seniority]
end

attribute :job_status do |job|
  job.job_status&.name
end

attribute :job_status_color do |job|
  job.job_status&.color
end

attribute :url do |object|
  "/user/jobs/#{object.job_id}/applies/#{object.id}"
end
```

## Conditional Attributes

Use `params` hash from controller for context-dependent fields:

```ruby
attribute :pin do |job, params|
  next false unless params && params[:current_user]
  job.pin_user_ids&.include?(params[:current_user].id) || false
end

attribute :confidential do |job, params|
  next false unless params && params[:current_user]
  job.confidential_user_ids&.include?(params[:current_user].id) || false
end
```

Conditional includes:

```ruby
has_many :selective_processes, if: Proc.new { |_record, params|
  params && params[:include_selective_processes]
}
```

## Enum Text Variants

Always provide `_text` variant for enum fields:

```ruby
attribute :evaluation_candidate_status do |apply|
  apply.evaluation_candidate_status
end

attribute :selective_process_status do |apply|
  apply.selective_process&.status
end

attribute :selective_process_name do |apply|
  apply.selective_process&.name
end
```

## Associations

```ruby
has_many :selective_processes
belongs_to :user
belongs_to :department

attribute :meetings do |apply|
  apply.meeting_relationships.map do |mr|
    {
      id: mr.id,
      reference_type: mr.reference_type,
      join_url: mr.join_url,
      provider_text: mr.provider_text,
      sub_status: mr.sub_status
    }
  end
end
```

## Controller Usage

```ruby
render_success(@job, serializer: JobSerializer,
  serializer_params: {
    current_user: @current_user,
    include_selective_processes: true
  }
)

render_success(results[:records],
  serializer: CandidateSerializer,
  meta: { total: results[:total_count] },
  serializer_params: { includes: params[:includes] }
)
```

## Rules

- **Never expose sensitive data:** tokens, passwords, CPF, `ms_access_token`
- **Never use `.as_json`** — always use serializer
- **Provide `_text` variants** for all enums (seniority_text, status_text, etc.)
- **Use `params` for conditional logic** — never access global state
- **Computed fields** use block syntax, never methods
- **Keep serializers focused** — avoid heavy computations (pre-compute in service or model)

## Example: ApplySerializer

```ruby
class ApplySerializer
  include JSONAPI::Serializer

  attributes :id, :candidate_id, :job_id, :selective_process_id,
             :selective_process_name, :selective_process_status,
             :evaluation_candidate_status, :name, :email, :phone, :linkedin,
             :avatar_url, :cv_match, :total_score, :alerts, :sub_status,
             :source, :created_at, :updated_at, :external_id

  attribute :meetings do |apply|
    apply.meeting_relationships.map do |mr|
      { id: mr.id, join_url: mr.join_url, provider_text: mr.provider_text }
    end
  end

  attribute :pin do |apply, params|
    next false unless params && params[:current_user]
    apply.pin_user_ids&.include?(params[:current_user].id) || false
  end
end
```
