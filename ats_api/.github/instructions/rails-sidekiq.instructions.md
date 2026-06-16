---
applyTo: "app/jobs/**/*.rb,app/workers/**/*.rb"
---

# Sidekiq Jobs & Workers — WeDO Talent ATS

## Two Patterns in Use

### 1. ActiveJob-based (app/jobs/)

```ruby
# frozen_string_literal: true

class Jobs::EmbeddingSyncJob < ApplicationJob
  queue_as :default

  def perform(job_id, expected_updated_at, account_id)
    account = Account.find_by(id: account_id)
    return unless account

    Current.account = account

    Apartment::Tenant.switch(account.tenant) do
      job = Job.find_by(id: job_id)
      return unless job
      return if job.is_deleted?

      sync_embedding(job)
    end
  end

  private

  def sync_embedding(job)
    # ...
  end
end
```

### 2. Raw Sidekiq::Job (app/jobs/ and app/workers/)

```ruby
# frozen_string_literal: true

module Jobs
  class RefreshAnalyticsJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    DEBOUNCE_TTL = 30
    LOCK_PREFIX = "job_analytics_refresh"

    def self.enqueue(job_id, account_id)
      lock_key = "#{LOCK_PREFIX}:#{job_id}"
      locked = Sidekiq.redis { |conn| conn.set(lock_key, "1", nx: true, ex: DEBOUNCE_TTL) }
      return unless locked

      perform_in(DEBOUNCE_TTL, job_id, account_id)
    end

    def perform(job_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        job = Job.find_by(id: job_id)
        return unless job

        ::Jobs::AnalyticsService.new(job: job, force_refresh: true).call
      end
    rescue StandardError => e
      Rails.logger.error "[Jobs::RefreshAnalyticsJob] Error for Job##{job_id}: #{e.message}"
      raise
    ensure
      Sidekiq.redis { |conn| conn.del("#{LOCK_PREFIX}:#{job_id}") }
    end
  end
end
```

### Workers (Sidekiq::Worker — legacy alias)

```ruby
# frozen_string_literal: true

class MsGraphEmailWorker
  include Sidekiq::Worker

  sidekiq_options retry: 5, queue: :default

  def perform(message_id, user_id, options = {})
    user = User.find_by(id: user_id)
    account = user&.account
    Apartment::Tenant.switch!(account.tenant) if account

    message = DispatchMessage.find_by(id: message_id)
    return unless message && user

    process_message(message, user, options)
  rescue => error
    message&.update!(status: :failed, provider_response: { error: { class: error.class.name, message: error.message } })
    raise error
  end

  private

  def process_message(message, user, options)
    # ...
  end
end
```

## Queue Configuration (sidekiq.yml)

```yaml
:concurrency: 15
:queues:
  - [critical, 6]
  - [email_delivery, 4]
  - [sourcing_search, 6]
  - [default, 3]
  - [ai_analysis, 7]
  - [embeddings, 2]
  - [linkedin_enrichment, 2]
  - mailers
  - active_storage
  - low
  - ats_sync
```

## Rules

### MANDATORY: Tenant Switching

Every job that accesses tenant data MUST switch tenant:

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

Use `switch` (block form) instead of `switch!` when possible — it auto-restores the previous tenant.

### Pass IDs, Never Objects

```ruby
MyJob.perform_async(job.id, account.id)
MyJob.perform_later(job.id, account.id)
```

### Idempotency

Jobs should be safe to retry. Use `find_by` + `return unless` guard clauses. Use Redis locks for debouncing when needed.

### Error Handling

```ruby
rescue StandardError => e
  Rails.logger.error "[#{self.class.name}] Error: #{e.message}"
  Rails.logger.error e.backtrace.first(5).join("\n")
  raise
end
```

### sidekiq_options

```ruby
sidekiq_options queue: :default, retry: 3
sidekiq_options queue: :critical, retry: false
sidekiq_options queue: :low, retry: 2
sidekiq_options queue: :ai_analysis, retry: 3
sidekiq_options queue: :embeddings, retry: 2
sidekiq_options queue: :sourcing_search, retry: 3
```

### Rate Limiting / Backoff

For external API calls (Gemini, LinkedIn, MS Graph), implement exponential backoff:

```ruby
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 90

def call_with_retry(text)
  attempt = 0
  begin
    external_api_call(text)
  rescue => e
    attempt += 1
    if rate_limit_error?(e) && attempt <= MAX_RETRIES
      delay = [INITIAL_BACKOFF * (2**(attempt - 1)), MAX_BACKOFF].min
      sleep delay
      retry
    end
    raise e
  end
end
```

### WebSocket Broadcasting from Jobs

```ruby
ActionCable.server.broadcast(
  "sourcing_#{sourcing.id}",
  { event: "processing_started", sourcing_id: sourcing.id, status: sourcing.status, timestamp: Time.current.iso8601 }
)
```

### Naming Convention

- Jobs: `Module::VerbNounJob` (e.g., `Jobs::RefreshAnalyticsJob`)
- Workers: `VerbNounWorker` (e.g., `MsGraphEmailWorker`) — legacy, prefer Job for new code
