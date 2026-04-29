---
applyTo: "app/services/**/*.rb"
---

# Rails Services — WeDO Talent ATS

## Standard Pattern

Services are namespaced under domain modules. Interface: `initialize(keyword_args:)` + `call`. Return hash with `success:` key or the result directly.

```ruby
# frozen_string_literal: true

module Jobs
  class PublishService
    def initialize(job:)
      @job = job
    end

    def call
      return error("Not ready for publication") unless ready_for_publication?

      update_job_status!
      success
    end

    private

    attr_reader :job

    def ready_for_publication?
      FieldRequirementChecker.new(job).is_ready_for_publication?
    end

    def update_job_status!
      active_status = JobStatus.find_by(name: "Ativa")
      attrs = { published_date: Time.current, is_active: true }
      attrs[:job_status_id] = active_status.id if active_status
      job.update!(attrs)
    end

    def success = { success: true, job: job }

    def error(message, **extra)
      { success: false, error: message }.merge(extra)
    end
  end
end
```

## Naming Convention

`VerbNounService` or just `VerbNoun` within a namespace:

```
Jobs::PublishService         — publishes a job
Jobs::CopyService            — copies/duplicates a job
Jobs::AnalyticsService       — computes analytics for a job
Jobs::StatsService           — aggregated stats across jobs
Jobs::AlertsService          — detects alerts/warnings
Candidates::ImportService    — imports candidates from external source
Evaluations::ScoreService    — scores evaluation responses
Sourcings::ExecuteService    — runs a sourcing search
```

## Service With Class Method Shortcut

When a service is called frequently, add a `.call` class method:

```ruby
module Candidates
  class ImportService
    def self.call(params:, user:)
      new(params: params, user: user).call
    end

    def initialize(params:, user:)
      @params = params
      @user = user
    end

    def call
      return error("Invalid data") unless valid?

      candidate = build_candidate
      candidate.save!
      candidate
    end

    private

    attr_reader :params, :user
  end
end
```

## Services With LLM (Gemini)

Every LLM call MUST create a `LlmUsage` record for cost tracking:

```ruby
module Evaluations
  class AiFeedbackService
    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      start_time = Time.current
      response = gemini_client.chat(
        model: model_name,
        messages: build_messages,
        temperature: 0.1,
        max_tokens: 1000,
        response_format: { type: "json_object" }
      )
      track_llm_usage!(response, start_time)
      parse_and_persist(response)
    rescue Faraday::TimeoutError => e
      Rails.logger.error "[#{self.class.name}] Timeout: #{e.message}"
      fallback_result
    rescue StandardError => e
      Rails.logger.error "[#{self.class.name}] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    end

    private

    attr_reader :evaluation_candidate

    def gemini_client
      @gemini_client ||= GeminiClient.new
    end

    def model_name
      ENV.fetch("GEMINI_FAST_MODEL", "gemini-2.0-flash")
    end

    def track_llm_usage!(response, start_time)
      LlmUsage.create!(
        model: model_name,
        operation: "evaluation_feedback",
        input_tokens: response.dig("usage", "input_tokens"),
        output_tokens: response.dig("usage", "output_tokens"),
        total_tokens: response.dig("usage", "total_tokens"),
        cost_usd: calculate_cost(response),
        latency_ms: ((Time.current - start_time) * 1000).round,
        success: true,
        context: {
          service: self.class.name,
          candidate_id: evaluation_candidate.candidate_id,
          job_id: evaluation_candidate.job_id
        }
      )
    end
  end
end
```

## Services With Caching

```ruby
module Jobs
  class AnalyticsService
    CACHE_PREFIX = "job_analytics"
    CACHE_TTL = 10.minutes

    def initialize(job:, force_refresh: false)
      @job = job
      @force_refresh = force_refresh
    end

    def call
      return cached_data unless @force_refresh || cached_data.nil?

      data = compute_analytics
      persist_snapshot(data)
      write_cache(data)
      data
    end

    private

    attr_reader :job

    def cached_data
      @cached_data ||= Rails.cache.read(cache_key)
    end

    def cache_key
      "#{CACHE_PREFIX}:#{job.id}"
    end

    def write_cache(data)
      Rails.cache.write(cache_key, data, expires_in: CACHE_TTL)
    end
  end
end
```

## Error Handling

```ruby
# ✅ Return structured result
def call
  return error("Job not found") unless load_job
  return error("User not found") unless load_user
  return error("Not authorized") unless authorized?

  process!
  success
rescue ActiveRecord::RecordInvalid => e
  error(e.record.errors.full_messages.join(", "))
rescue StandardError => e
  Rails.logger.error "[#{self.class.name}] Unexpected error: #{e.message}"
  Rails.logger.error e.backtrace.first(5).join("\n")
  raise
end

# ❌ Never let exceptions leak without logging
def call
  process!
rescue => e
  nil  # swallowing errors silently
end
```

## Rules

- One service = one responsibility (SRP)
- Early return for validation/guard clauses
- Private `attr_reader` for instance variables
- Handle errors internally with structured returns
- Never `puts`/`p` — use `Rails.logger`
- For long operations: extract to Sidekiq job
- For LLM calls: always track via `LlmUsage`, add timeout, provide fallback
- Use `ENV.fetch("KEY", "default")` for configuration
- Use `Time.current` not `Time.now`
