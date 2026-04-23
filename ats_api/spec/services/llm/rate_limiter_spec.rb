# frozen_string_literal: true

require "rails_helper"

RSpec.describe Llm::RateLimiter do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:redis) { Redis.new(url: ENV.fetch("REDIS_URL", "redis://localhost:6379/1")) }

  before do
    redis.del("llm:rpm:#{account.id}")
  end

  describe "#check" do
    context "when account has no quota" do
      before { LlmQuota.where(account_id: account.id).delete_all }

      it "auto-provisions a starter quota and allows" do
        result = described_class.check(account_id: account.id, user_id: user.id)

        expect(result).to be_allowed
        expect(LlmQuota.find_by(account_id: account.id)).to be_present
      end
    end

    context "when account is disabled" do
      before { create(:llm_quota, :disabled, account: account) }

      it "blocks with account_disabled reason" do
        result = described_class.check(account_id: account.id, user_id: user.id)

        expect(result).not_to be_allowed
        expect(result.reason).to eq("account_disabled")
      end
    end

    context "when monthly cost is exceeded with hard limit" do
      before do
        quota = create(:llm_quota, account: account, monthly_cost_limit_usd: 5.0)
        create(:llm_quota_usage,
          account: account,
          period: Date.current.strftime("%Y-%m"),
          total_cost_usd: 6.0
        )
      end

      it "blocks with monthly_cost_exceeded reason" do
        result = described_class.check(account_id: account.id, user_id: user.id)

        expect(result).not_to be_allowed
        expect(result.reason).to eq("monthly_cost_exceeded")
        expect(result.usage[:limit_usd]).to eq(5.0)
        expect(result.usage[:used_usd]).to eq(6.0)
      end
    end

    context "when monthly cost is exceeded with soft limit" do
      before do
        create(:llm_quota, :soft_limit, account: account, monthly_cost_limit_usd: 5.0)
        create(:llm_quota_usage,
          account: account,
          period: Date.current.strftime("%Y-%m"),
          total_cost_usd: 6.0
        )
      end

      it "allows with soft limit" do
        result = described_class.check(account_id: account.id, user_id: user.id)
        expect(result).to be_allowed
      end
    end

    context "when monthly requests are exceeded" do
      before do
        create(:llm_quota, account: account, monthly_request_limit: 100)
        create(:llm_quota_usage,
          account: account,
          period: Date.current.strftime("%Y-%m"),
          total_requests: 101
        )
      end

      it "blocks with monthly_requests_exceeded reason" do
        result = described_class.check(account_id: account.id, user_id: user.id)

        expect(result).not_to be_allowed
        expect(result.reason).to eq("monthly_requests_exceeded")
      end
    end

    context "when extra budget extends the limit" do
      before do
        create(:llm_quota,
          account: account,
          monthly_cost_limit_usd: 5.0,
          extra_budget_usd: 10.0,
          extra_budget_expires_at: 1.week.from_now
        )
        create(:llm_quota_usage,
          account: account,
          period: Date.current.strftime("%Y-%m"),
          total_cost_usd: 8.0
        )
      end

      it "allows because effective limit is 15.0" do
        result = described_class.check(account_id: account.id, user_id: user.id)
        expect(result).to be_allowed
      end
    end

    context "when burst RPM is exceeded" do
      let!(:quota) { create(:llm_quota, account: account, burst_rpm: 3) }

      before do
        4.times do |i|
          redis.zadd("llm:rpm:#{account.id}", Time.current.to_f, "#{Time.current.to_f}:#{i}")
        end
      end

      it "blocks with burst_rpm_exceeded reason" do
        result = described_class.check(account_id: account.id, user_id: user.id)

        expect(result).not_to be_allowed
        expect(result.reason).to eq("burst_rpm_exceeded")
        expect(result.usage[:rpm_limit]).to eq(3)
      end
    end

    context "when burst RPM is within limit" do
      let!(:quota) { create(:llm_quota, account: account, burst_rpm: 10) }

      before do
        2.times do |i|
          redis.zadd("llm:rpm:#{account.id}", Time.current.to_f, "#{Time.current.to_f}:#{i}")
        end
      end

      it "allows the request" do
        result = described_class.check(account_id: account.id, user_id: user.id)
        expect(result).to be_allowed
      end
    end

    context "when bypass is true" do
      before do
        create(:llm_quota, :disabled, account: account)
      end

      it "always allows" do
        result = described_class.check(account_id: account.id, bypass: true)
        expect(result).to be_allowed
      end
    end
  end

  describe "#check!" do
    context "when blocked" do
      before do
        create(:llm_quota, account: account, monthly_cost_limit_usd: 1.0)
        create(:llm_quota_usage,
          account: account,
          period: Date.current.strftime("%Y-%m"),
          total_cost_usd: 2.0
        )
      end

      it "raises RateLimitExceeded" do
        expect {
          described_class.check!(account_id: account.id, user_id: user.id)
        }.to raise_error(Llm::RateLimitExceeded) { |e|
          expect(e.limit_type).to eq("monthly_cost_exceeded")
        }
      end
    end
  end

  describe "#record_usage!" do
    let!(:quota) { create(:llm_quota, account: account) }

    it "increments the usage snapshot" do
      limiter = described_class.new(account_id: account.id)
      limiter.record_usage!(cost: 0.05, tokens: 1500)

      usage = LlmQuotaUsage.current_for(account.id)
      expect(usage.total_cost_usd.to_f).to eq(0.05)
      expect(usage.total_requests).to eq(1)
      expect(usage.total_tokens).to eq(1500)
    end

    it "skips when bypass is true" do
      limiter = described_class.new(account_id: account.id, bypass: true)
      limiter.record_usage!(cost: 0.05, tokens: 1500)

      usage = LlmQuotaUsage.current_for(account.id)
      expect(usage.total_cost_usd.to_f).to eq(0.0)
    end

    it "increments burst counter in Redis" do
      limiter = described_class.new(account_id: account.id)
      limiter.record_usage!(cost: 0.01, tokens: 100)

      count = redis.zrangebyscore("llm:rpm:#{account.id}", "-inf", "+inf").size
      expect(count).to eq(1)
    end

    it "triggers notification when threshold is reached" do
      quota.update!(notify_at_percentage: 50)
      usage = LlmQuotaUsage.current_for(account.id)
      usage.update!(total_cost_usd: 2.4)

      limiter = described_class.new(account_id: account.id)
      limiter.record_usage!(cost: 0.2, tokens: 100)

      quota.reload
      expect(quota.metadata["notified_period"]).to eq(Date.current.strftime("%Y-%m"))
      expect(quota.metadata["notified_percentage"].to_f).to be >= 50
    end

    it "does not re-notify for the same period" do
      quota.update!(
        notify_at_percentage: 50,
        metadata: { "notified_period" => Date.current.strftime("%Y-%m"), "notified_at" => Time.current.iso8601 }
      )
      usage = LlmQuotaUsage.current_for(account.id)
      usage.update!(total_cost_usd: 4.0)

      expect {
        limiter = described_class.new(account_id: account.id)
        limiter.record_usage!(cost: 0.1, tokens: 100)
      }.not_to change { quota.reload.metadata["notified_at"] }
    end
  end
end
