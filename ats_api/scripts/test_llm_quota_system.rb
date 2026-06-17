# frozen_string_literal: true

module LlmQuotaTest
  SEPARATOR = "━" * 60

  def self.run(account_id: nil)
    account = account_id ? Account.find(account_id) : Account.first
    user = User.where(account_id: account.id).first

    setup_current(user, account)
    sync_existing_usage(account)

    puts "\n#{SEPARATOR}"
    puts "🧪 LLM QUOTA SYSTEM - FULL TEST"
    puts "   Account: ##{account.id} (#{account.name})"
    puts "   User: ##{user.id} (#{user.email})"
    puts SEPARATOR

    original_state = snapshot_quota(account)

    results = []
    results << test_1_check_quota(account)
    results << test_2_llm_call_works(account)
    results << test_3_cost_limit_blocks(account)
    results << test_4_extra_budget_unblocks(account)
    results << test_5_burst_rpm(account)
    results << test_6_disable_account(account)
    results << test_7_bypass_flag(account)

    restore_state(account, original_state)

    print_summary(results)
  end

  private_class_method def self.setup_current(user, account)
    Current.user = user
    Current.account = account
  end

  private_class_method def self.sync_existing_usage(account)
    Llm::QuotaUsageSyncJob.new.perform
  end

  private_class_method def self.snapshot_quota(account)
    quota = account.llm_quota
    usage = LlmQuotaUsage.current_for(account.id)
    {
      plan: quota.plan,
      monthly_cost_limit_usd: quota.monthly_cost_limit_usd,
      monthly_request_limit: quota.monthly_request_limit,
      burst_rpm: quota.burst_rpm,
      hard_limit: quota.hard_limit,
      enabled: quota.enabled,
      extra_budget_usd: quota.extra_budget_usd,
      extra_budget_expires_at: quota.extra_budget_expires_at,
      metadata: quota.metadata,
      usage_cost: usage.total_cost_usd,
      usage_requests: usage.total_requests,
      usage_tokens: usage.total_tokens
    }
  end

  private_class_method def self.restore_state(account, state)
    puts "\n🔄 Restoring original state..."
    quota = account.llm_quota
    quota.update!(
      plan: state[:plan],
      monthly_cost_limit_usd: state[:monthly_cost_limit_usd],
      monthly_request_limit: state[:monthly_request_limit],
      burst_rpm: state[:burst_rpm],
      hard_limit: state[:hard_limit],
      enabled: state[:enabled],
      extra_budget_usd: state[:extra_budget_usd],
      extra_budget_expires_at: state[:extra_budget_expires_at],
      metadata: state[:metadata].is_a?(Hash) ? state[:metadata] : {}
    )
    usage = LlmQuotaUsage.current_for(account.id)
    usage.update!(
      total_cost_usd: state[:usage_cost],
      total_requests: state[:usage_requests],
      total_tokens: state[:usage_tokens]
    )
    clear_burst_redis(account.id)
    puts "✅ State restored\n"
  end

  private_class_method def self.clear_burst_redis(account_id)
    redis = Redis.new(url: ENV.fetch("REDIS_URL", "redis://localhost:6379/1"))
    redis.del("llm:rpm:#{account_id}")
  rescue => e
    puts "   ⚠️  Redis cleanup failed: #{e.message}"
  end

  private_class_method def self.test_1_check_quota(account)
    test("1. Check quota & usage") do
      quota = account.llm_quota
      usage = LlmQuotaUsage.current_for(account.id)

      puts "   Plan: #{quota.plan}"
      puts "   Limit: $#{quota.monthly_cost_limit_usd}"
      puts "   Used: $#{usage.total_cost_usd.to_f.round(6)}"
      puts "   Requests: #{usage.total_requests}"
      puts "   Usage: #{quota.usage_percentage}%"
      puts "   Remaining: $#{quota.cost_remaining.to_f.round(6)}"

      limiter = Llm::RateLimiter.new(account_id: account.id)
      result = limiter.check
      puts "   Rate limit check: #{result.allowed? ? '✅ ALLOWED' : '❌ BLOCKED'}"

      result.allowed?
    end
  end

  private_class_method def self.test_2_llm_call_works(account)
    test("2. Real LLM call (should work)") do
      quota = account.llm_quota
      quota.apply_plan!("pro")
      quota.update!(hard_limit: true)
      LlmQuotaUsage.current_for(account.id).update!(total_cost_usd: 0, total_requests: 0, total_tokens: 0)

      usage_before = LlmQuotaUsage.current_for(account.id).total_requests

      response = GeminiClient.new.chat(
        model: "gemini-2.0-flash",
        messages: [ { role: "user", content: "Reply with exactly: OK" } ],
        temperature: 0,
        max_tokens: 10,
        tracking: { operation: "quota_test.llm_call" }
      )

      content = response.dig("choices", 0, "message", "content")
      usage_after = LlmQuotaUsage.current_for(account.id).reload.total_requests

      puts "   Response: #{content.strip}"
      puts "   Requests before: #{usage_before} → after: #{usage_after}"
      puts "   Usage tracked: #{usage_after > usage_before ? '✅ YES' : '❌ NO'}"

      content.present? && usage_after > usage_before
    end
  end

  private_class_method def self.test_3_cost_limit_blocks(account)
    test("3. Cost limit blocks (hard_limit=true)") do
      quota = account.llm_quota
      quota.update!(monthly_cost_limit_usd: 0.001, hard_limit: true, extra_budget_usd: 0, extra_budget_expires_at: nil)
      LlmQuotaUsage.current_for(account.id).update!(total_cost_usd: 0.002)

      blocked = false
      begin
        GeminiClient.new.chat(
          model: "gemini-2.0-flash",
          messages: [ { role: "user", content: "Reply with: OK" } ],
          temperature: 0,
          max_tokens: 5,
          tracking: { operation: "quota_test.should_block" }
        )
        puts "   ❌ Call was NOT blocked (should have been)"
      rescue Llm::RateLimitExceeded => e
        blocked = true
        puts "   ✅ Blocked: #{e.limit_type}"
        puts "   Details: #{e.details}"
      end

      blocked
    end
  end

  private_class_method def self.test_4_extra_budget_unblocks(account)
    test("4. Extra budget unblocks") do
      quota = account.llm_quota
      quota.update!(monthly_cost_limit_usd: 0.001, hard_limit: true, extra_budget_usd: 0, extra_budget_expires_at: nil)
      LlmQuotaUsage.current_for(account.id).update!(total_cost_usd: 0.002)

      limiter = Llm::RateLimiter.new(account_id: account.id)
      before = limiter.check
      puts "   Before extra: #{before.allowed? ? 'ALLOWED' : 'BLOCKED'}"

      quota.grant_extra_budget!(amount: 1.0, expires_at: 1.hour.from_now, reason: "test")
      puts "   Effective limit: $#{quota.reload.effective_monthly_limit}"

      after = Llm::RateLimiter.new(account_id: account.id).check
      puts "   After extra: #{after.allowed? ? '✅ ALLOWED' : '❌ BLOCKED'}"

      response = GeminiClient.new.chat(
        model: "gemini-2.0-flash",
        messages: [ { role: "user", content: "Reply with: OK" } ],
        temperature: 0,
        max_tokens: 5,
        tracking: { operation: "quota_test.after_extra" }
      )
      content = response.dig("choices", 0, "message", "content")
      puts "   LLM response: #{content.strip}"

      !before.allowed? && after.allowed? && content.present?
    end
  end

  private_class_method def self.test_5_burst_rpm(account)
    test("5. Burst RPM limit") do
      quota = account.llm_quota
      quota.apply_plan!("pro")
      quota.update!(burst_rpm: 3, hard_limit: true)
      LlmQuotaUsage.current_for(account.id).update!(total_cost_usd: 0, total_requests: 0, total_tokens: 0)
      clear_burst_redis(account.id)

      limiter = Llm::RateLimiter.new(account_id: account.id)
      4.times { limiter.record_usage!(cost: 0.0001, tokens: 10) }

      result = Llm::RateLimiter.new(account_id: account.id).check
      puts "   After 4 requests (limit=3): #{result.allowed? ? '❌ ALLOWED' : '✅ BLOCKED'}"
      puts "   Reason: #{result.reason}"

      !result.allowed? && result.reason == "burst_rpm_exceeded"
    end
  end

  private_class_method def self.test_6_disable_account(account)
    test("6. Disabled quota blocks everything") do
      quota = account.llm_quota
      quota.update!(enabled: false)
      clear_burst_redis(account.id)

      result = Llm::RateLimiter.new(account_id: account.id).check
      puts "   Enabled=false: #{result.allowed? ? '❌ ALLOWED' : '✅ BLOCKED'}"
      puts "   Reason: #{result.reason}"

      quota.update!(enabled: true)
      !result.allowed? && result.reason == "account_disabled"
    end
  end

  private_class_method def self.test_7_bypass_flag(account)
    test("7. Bypass flag skips all checks") do
      quota = account.llm_quota
      quota.update!(enabled: false, hard_limit: true)

      result = Llm::RateLimiter.new(account_id: account.id, bypass: true).check
      puts "   Disabled + bypass: #{result.allowed? ? '✅ ALLOWED' : '❌ BLOCKED'}"

      quota.update!(enabled: true)
      result.allowed?
    end
  end

  private_class_method def self.test(name)
    puts "\n#{SEPARATOR}"
    puts "🧪 #{name}"
    puts SEPARATOR

    passed = yield
    puts passed ? "   ✅ PASSED" : "   ❌ FAILED"
    { name: name, passed: passed }
  rescue => e
    puts "   💥 ERROR: #{e.class} - #{e.message}"
    puts "   #{e.backtrace.first(3).join("\n   ")}"
    { name: name, passed: false }
  end

  private_class_method def self.print_summary(results)
    passed = results.count { |r| r[:passed] }
    total = results.size

    puts "\n#{SEPARATOR}"
    puts "📊 RESULTS: #{passed}/#{total} passed"
    puts SEPARATOR
    results.each do |r|
      puts "   #{r[:passed] ? '✅' : '❌'} #{r[:name]}"
    end
    puts SEPARATOR
    puts passed == total ? "🎉 ALL TESTS PASSED" : "⚠️  SOME TESTS FAILED"
    puts SEPARATOR
  end
end
