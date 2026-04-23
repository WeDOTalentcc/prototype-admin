---
applyTo: "app/models/**/*.rb"
---

# Rails Models — WeDO Talent ATS

## Block Ordering (mandatory)

```ruby
class ModelName < ApplicationRecord
  # 1. Includes/Concerns
  include HasActivityLog
  include Searchable

  # 2. Enums
  enum evaluation_candidate_status: { pending: 0, sent: 1, answered: 2 }

  # 3. Constants
  SENIORITY = ["Júnior", "Pleno", "Sênior", "Especialista"].freeze
  PER_PAGE_KANBAN = 10

  # 4. Associations
  belongs_to :user, optional: true
  belongs_to :account, optional: true
  has_many :applies, dependent: :destroy
  has_many :skill_relationships, as: :reference, dependent: :destroy
  has_many :skills, through: :skill_relationships
  has_one :embedding_record, class_name: "Embedding", as: :reference, dependent: :destroy

  # 5. Validations
  validates :name, presence: true
  validates :external_id, uniqueness: { scope: :account_id, allow_nil: true }

  # 6. Scopes
  scope :active, -> { where(is_active: true, is_deleted: false) }

  # 7. Callbacks
  after_create :set_default_status
  after_commit :sync_vector_after_commit, on: %i[create update]

  # 8. Class methods
  # 9. Instance methods
  # 10. Private methods
end
```

## Associations

Always specify `dependent:` — choose the appropriate strategy:

```ruby
# ✅ Correct
has_many :applies, dependent: :destroy
has_many :candidate_feedbacks, dependent: :nullify
has_many :job_users, dependent: :delete_all
belongs_to :department, optional: true

# ❌ Wrong — missing dependent
has_many :applies
```

For polymorphic associations:

```ruby
has_many :skill_relationships, as: :reference, dependent: :destroy
has_many :skills, through: :skill_relationships
has_one :embedding_record, class_name: "Embedding", as: :reference, dependent: :destroy
```

## Enums

Hash with explicit integers, never array:

```ruby
# ✅
enum evaluation_candidate_status: { pending: 0, sent: 1, answered: 2 }
enum chatbot_channel: { internal: 0, whatsapp: 1 }
enum notification_type: { per_candidate: 0, daily: 1, weekly: 2 }

# ❌ Never
enum :status, [:pending, :sent, :answered]
```

## Searchkick Integration

Every searchable model includes the `Searchable` concern which configures tenant-scoped index names automatically:

```ruby
class Candidate < ApplicationRecord
  include Searchable

  def search_data
    {
      name: name,
      email: email,
      role_name: role_name,
      current_company: current_company,
      city: city,
      state: state,
      source: source,
      skills: skills.pluck(:name),
      is_deleted: is_deleted,
      account_id: account_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
```

The `Searchable` concern handles:
- `searchkick index_name: -> { tenant_index_name }` — tenant-scoped ES indexes
- `search_default` class method for standardized querying
- Index name format: `{tenant}_{model_plural}_{env}`

## Soft Delete Pattern

Use `is_deleted` boolean field, never `acts_as_paranoid` or `discard`:

```ruby
scope :active, -> { where(is_deleted: false) }
scope :deleted, -> { where(is_deleted: true) }

def soft_delete!
  update!(is_deleted: true)
end
```

Always filter by `is_deleted: false` in queries and `search_data`.

## Concerns Available

| Concern | Purpose |
|---|---|
| `Searchable` | Searchkick with tenant-scoped indexes |
| `HasActivityLog` | Auto-logs create/update/destroy to ActivityLog |
| `AccountScopable` | Auto-assigns account_id from Current.user (in ApplicationRecord) |
| `UidGeneratable` | Generates UUID uid on create |
| `TracksJobAnalytics` | Enqueues analytics refresh on model changes |
| `RemunerableAttributes` | Shared salary/remuneration helpers |

Extract to a concern when behavior is shared by 2+ models.

## JSONB Fields

Use typed accessor methods or `store_accessor`:

```ruby
# ✅ Explicit accessor
def sourcing_config_max_results
  sourcing_config&.dig("max_results") || 50
end

# ✅ store_accessor for simple cases
store_accessor :settings, :theme, :language, :timezone
```

Never access raw hash directly in controllers or serializers.

## Callbacks

Use sparingly. Prefer services for complex side effects:

```ruby
# ✅ OK — simple data initialization
after_create :set_default_status, if: -> { account_id.present? }

# ✅ OK — async reindexing
after_commit :sync_vector_after_commit, on: %i[create update], unless: -> { Rails.env.test? }

# ❌ Don't — complex business logic in callback
after_create :send_welcome_email, :create_onboarding_tasks, :notify_slack
```

## Validations

```ruby
validates :title, presence: true
validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }, allow_blank: true
validates :cpf, uniqueness: true, allow_blank: true
validates :external_id, uniqueness: { scope: :account_id, allow_nil: true }
validate :custom_validation_method

private

def custom_validation_method
  return if valid_condition?
  errors.add(:field, "descriptive error message")
end
```

## Scopes

Must be chainable and return `ActiveRecord::Relation`:

```ruby
scope :active, -> { where(is_active: true, is_deleted: false) }
scope :by_department, ->(dept_id) { where(department_id: dept_id) }
scope :created_after, ->(date) { where("created_at >= ?", date) }
scope :with_applies, -> { joins(:applies).distinct }
```

## Preload Patterns

Define `include_base` or similar for common eager loading:

```ruby
scope :include_base, -> {
  includes(:user, :department, :job_status, :selective_processes, :skills)
}
```
