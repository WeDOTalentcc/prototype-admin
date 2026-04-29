# frozen_string_literal: true

module Llm
  class RateLimitExceeded < StandardError
    attr_reader :limit_type, :details

    def initialize(limit_type:, details: {})
      @limit_type = limit_type
      @details = details
      super("LLM rate limit exceeded: #{limit_type}")
    end
  end

  class RateLimiter
    BURST_KEY_PREFIX = "llm:rpm"
    BURST_WINDOW = 60

    Result = Struct.new(:allowed, :reason, :usage, keyword_init: true) do
      def allowed? = allowed
    end

    def initialize(account_id:, user_id: nil, bypass: false)
      @account_id = account_id
      @user_id = user_id
      @bypass = bypass
    end

    def check!
      return true if bypass

      result = check
      return true if result.allowed?

      raise RateLimitExceeded.new(
        limit_type: result.reason,
        details: result.usage
      )
    end

    def check
      return Result.new(allowed: true, reason: nil, usage: {}) if bypass

      quota = find_or_create_quota
      @cached_usage = LlmQuotaUsage.current_for(account_id)

      return blocked_result("account_disabled", quota) unless quota.enabled?

      burst_check = check_burst(quota)
      return burst_check unless burst_check.allowed?

      cost_check = check_monthly_cost(quota)
      return cost_check unless cost_check.allowed?

      request_check = check_monthly_requests(quota)
      return request_check unless request_check.allowed?

      Result.new(allowed: true, reason: nil, usage: build_usage_data(quota))
    end

    def record_usage!(cost:, tokens:)
      return if bypass

      increment_burst_counter
      usage = LlmQuotaUsage.current_for(account_id)
      usage.increment_usage!(cost: cost, tokens: tokens)
      check_notification_threshold(usage)
    end

    def self.check!(account_id:, user_id: nil, bypass: false)
      new(account_id: account_id, user_id: user_id, bypass: bypass).check!
    end

    def self.check(account_id:, user_id: nil, bypass: false)
      new(account_id: account_id, user_id: user_id, bypass: bypass).check
    end

    private

    attr_reader :account_id, :user_id, :bypass

    def cached_usage
      @cached_usage ||= LlmQuotaUsage.current_for(account_id)
    end

    def find_or_create_quota
      LlmQuota.find_or_create_by!(account_id: account_id) do |quota|
        defaults = Llm::QuotaPlan.defaults_for(Llm::QuotaPlan::DEFAULT_PLAN)
        quota.plan = Llm::QuotaPlan::DEFAULT_PLAN
        quota.monthly_cost_limit_usd = defaults[:monthly_cost_limit_usd]
        quota.monthly_request_limit = defaults[:monthly_request_limit]
        quota.burst_rpm = defaults[:burst_rpm]
        quota.extra_budget_usd = 0.0
        quota.notify_at_percentage = 80
        quota.enabled = true
        quota.hard_limit = false
        quota.metadata = {}
      end
    end

    def check_burst(quota)
      current_rpm = current_burst_count
      return Result.new(allowed: true, reason: nil, usage: {}) if current_rpm < quota.burst_rpm

      Result.new(
        allowed: false,
        reason: "burst_rpm_exceeded",
        usage: {
          rpm_limit: quota.burst_rpm,
          rpm_current: current_rpm,
          retry_after_seconds: BURST_WINDOW
        }
      )
    end

    def check_monthly_cost(quota)
      usage = cached_usage
      effective_limit = quota.effective_monthly_limit

      return Result.new(allowed: true, reason: nil, usage: {}) if usage.total_cost_usd < effective_limit
      return Result.new(allowed: true, reason: nil, usage: {}) unless quota.hard_limit?

      Result.new(
        allowed: false,
        reason: "monthly_cost_exceeded",
        usage: {
          limit_usd: effective_limit.to_f,
          used_usd: usage.total_cost_usd.to_f,
          resets_at: next_month_reset.iso8601
        }
      )
    end

    def check_monthly_requests(quota)
      return Result.new(allowed: true, reason: nil, usage: {}) unless quota.monthly_request_limit

      usage = cached_usage
      return Result.new(allowed: true, reason: nil, usage: {}) if usage.total_requests < quota.monthly_request_limit

      Result.new(
        allowed: false,
        reason: "monthly_requests_exceeded",
        usage: {
          request_limit: quota.monthly_request_limit,
          requests_used: usage.total_requests,
          resets_at: next_month_reset.iso8601
        }
      )
    end

    def current_burst_count
      key = burst_key
      redis.zrangebyscore(key, Time.current.to_f - BURST_WINDOW, "+inf").size
    rescue Redis::BaseError => e
      Rails.logger.error "[Llm::RateLimiter] Redis error on burst check: #{e.message}"
      0
    end

    def increment_burst_counter
      key = burst_key
      now = Time.current.to_f
      redis.multi do |tx|
        tx.zadd(key, now, "#{now}:#{SecureRandom.hex(4)}")
        tx.zremrangebyscore(key, "-inf", now - BURST_WINDOW)
        tx.expire(key, BURST_WINDOW * 2)
      end
    rescue Redis::BaseError => e
      Rails.logger.error "[Llm::RateLimiter] Redis error on burst increment: #{e.message}"
    end

    def check_notification_threshold(usage)
      quota = LlmQuota.find_by(account_id: account_id)
      return unless quota

      percentage = ((usage.total_cost_usd / quota.effective_monthly_limit) * 100).round(2)
      return unless percentage >= quota.notify_at_percentage

      current_metadata = quota.metadata.is_a?(Hash) ? quota.metadata : {}
      already_notified = current_metadata.dig("notified_period") == usage.period
      return if already_notified

      quota.update!(metadata: current_metadata.merge(
        "notified_period" => usage.period,
        "notified_at" => Time.current.iso8601,
        "notified_percentage" => percentage
      ))

      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [Llm::RateLimiter] QUOTA ALERT"
      Rails.logger.warn "   Account: #{account_id}"
      Rails.logger.warn "   Usage: #{percentage}% (#{usage.total_cost_usd.to_f.round(4)} / #{quota.effective_monthly_limit.to_f.round(4)} USD)"
      Rails.logger.warn "   Period: #{usage.period}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue => e
      Rails.logger.error "[Llm::RateLimiter] Notification check error: #{e.message}"
    end

    def build_usage_data(quota)
      usage = cached_usage
      {
        limit_usd: quota.effective_monthly_limit.to_f,
        used_usd: usage.total_cost_usd.to_f,
        remaining_usd: [ quota.effective_monthly_limit - usage.total_cost_usd, 0 ].max.to_f,
        percentage: quota.effective_monthly_limit.zero? ? 0.0 : ((usage.total_cost_usd / quota.effective_monthly_limit) * 100).round(2),
        resets_at: next_month_reset.iso8601
      }
    end

    def blocked_result(reason, quota)
      Result.new(
        allowed: false,
        reason: reason,
        usage: build_usage_data(quota)
      )
    end

    def burst_key
      "#{BURST_KEY_PREFIX}:#{account_id}"
    end

    def next_month_reset
      Date.current.next_month.beginning_of_month.beginning_of_day
    end

    def redis
      @redis ||= Redis.new(url: ENV.fetch("REDIS_URL", "redis://localhost:6379/1"))
    end
  end
end
