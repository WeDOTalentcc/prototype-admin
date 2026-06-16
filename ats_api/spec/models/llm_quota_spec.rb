# frozen_string_literal: true

require "rails_helper"

RSpec.describe LlmQuota, type: :model do
  describe "associations" do
    it { should belong_to(:account) }
  end

  describe "validations" do
    subject { create(:llm_quota) }

    it { should validate_presence_of(:plan) }
    it { should validate_inclusion_of(:plan).in_array(%w[starter pro enterprise custom]) }
    it { should validate_presence_of(:monthly_cost_limit_usd) }
    it { should validate_numericality_of(:monthly_cost_limit_usd).is_greater_than_or_equal_to(0) }
    it { should validate_numericality_of(:burst_rpm).is_greater_than(0) }
    it { should validate_numericality_of(:extra_budget_usd).is_greater_than_or_equal_to(0) }
    it { should validate_uniqueness_of(:account_id) }
  end

  describe "#effective_monthly_limit" do
    let(:quota) { create(:llm_quota, monthly_cost_limit_usd: 25.0, extra_budget_usd: 0.0) }

    it "returns monthly limit when no extra budget" do
      expect(quota.effective_monthly_limit).to eq(25.0)
    end

    it "includes active extra budget" do
      quota.update!(extra_budget_usd: 10.0, extra_budget_expires_at: 1.week.from_now)
      expect(quota.effective_monthly_limit).to eq(35.0)
    end

    it "excludes expired extra budget" do
      quota.update!(extra_budget_usd: 10.0, extra_budget_expires_at: 1.day.ago)
      expect(quota.effective_monthly_limit).to eq(25.0)
    end
  end

  describe "#usage_percentage" do
    let(:account) { create(:account) }
    let(:quota) { create(:llm_quota, account: account, monthly_cost_limit_usd: 100.0) }

    before do
      create(:llm_quota_usage,
        account: account,
        period: Date.current.strftime("%Y-%m"),
        total_cost_usd: 50.0
      )
    end

    it "calculates percentage correctly" do
      expect(quota.usage_percentage).to eq(50.0)
    end
  end

  describe "#cost_remaining" do
    let(:account) { create(:account) }
    let(:quota) { create(:llm_quota, account: account, monthly_cost_limit_usd: 100.0) }

    it "returns the difference between limit and usage" do
      create(:llm_quota_usage, account: account, period: Date.current.strftime("%Y-%m"), total_cost_usd: 40.0)
      expect(quota.cost_remaining).to eq(60.0)
    end

    it "returns zero when usage exceeds limit" do
      create(:llm_quota_usage, account: account, period: Date.current.strftime("%Y-%m"), total_cost_usd: 150.0)
      expect(quota.cost_remaining).to eq(0)
    end
  end

  describe "#requests_remaining" do
    let(:account) { create(:account) }
    let(:quota) { create(:llm_quota, account: account, monthly_request_limit: 1000) }

    it "returns remaining requests" do
      create(:llm_quota_usage, account: account, period: Date.current.strftime("%Y-%m"), total_requests: 300)
      expect(quota.requests_remaining).to eq(700)
    end

    it "returns zero when requests exceed limit" do
      create(:llm_quota_usage, account: account, period: Date.current.strftime("%Y-%m"), total_requests: 1500)
      expect(quota.requests_remaining).to eq(0)
    end

    it "returns nil when monthly_request_limit is nil" do
      quota.update!(monthly_request_limit: nil)
      expect(quota.requests_remaining).to be_nil
    end
  end

  describe "#extra_budget_expired?" do
    let(:quota) { create(:llm_quota) }

    it "returns false when no expiration set" do
      expect(quota.extra_budget_expired?).to be false
    end

    it "returns false when expiration is in the future" do
      quota.update!(extra_budget_usd: 5.0, extra_budget_expires_at: 1.week.from_now)
      expect(quota.extra_budget_expired?).to be false
    end

    it "returns true when expiration is in the past" do
      quota.update!(extra_budget_usd: 5.0, extra_budget_expires_at: 1.day.ago)
      expect(quota.extra_budget_expired?).to be true
    end
  end

  describe "#active_extra_budget" do
    let(:quota) { create(:llm_quota, extra_budget_usd: 10.0) }

    it "returns extra budget when no expiration" do
      expect(quota.active_extra_budget).to eq(10.0)
    end

    it "returns zero when extra_budget_usd is zero" do
      quota.update!(extra_budget_usd: 0.0)
      expect(quota.active_extra_budget).to eq(0.0)
    end

    it "returns zero when expired" do
      quota.update!(extra_budget_expires_at: 1.day.ago)
      expect(quota.active_extra_budget).to eq(0.0)
    end

    it "returns extra budget when not expired" do
      quota.update!(extra_budget_expires_at: 1.week.from_now)
      expect(quota.active_extra_budget).to eq(10.0)
    end
  end

  describe "#grant_extra_budget!" do
    let(:quota) { create(:llm_quota, extra_budget_usd: 0.0) }

    it "adds extra budget cumulatively" do
      quota.grant_extra_budget!(amount: 10.0, expires_at: 1.month.from_now, reason: "Test")

      expect(quota.extra_budget_usd).to eq(10.0)
      expect(quota.extra_budget_expires_at).to be_present
      expect(quota.metadata["last_extra_reason"]).to eq("Test")
    end

    it "stacks extra budget amounts" do
      quota.grant_extra_budget!(amount: 5.0, reason: "First")
      quota.grant_extra_budget!(amount: 3.0, reason: "Second")

      expect(quota.extra_budget_usd).to eq(8.0)
      expect(quota.metadata["last_extra_reason"]).to eq("Second")
    end

    it "handles metadata stored as string" do
      quota.update_column(:metadata, "{}")
      quota.reload
      expect { quota.grant_extra_budget!(amount: 5.0, reason: "Fix") }.not_to raise_error
      expect(quota.extra_budget_usd).to eq(5.0)
    end
  end

  describe "#apply_plan!" do
    let(:quota) { create(:llm_quota, plan: "starter") }

    it "updates to pro plan defaults" do
      quota.apply_plan!("pro")

      expect(quota.plan).to eq("pro")
      expect(quota.monthly_cost_limit_usd).to eq(25.0)
      expect(quota.burst_rpm).to eq(50)
    end

    it "updates to enterprise plan defaults" do
      quota.apply_plan!("enterprise")

      expect(quota.plan).to eq("enterprise")
      expect(quota.monthly_cost_limit_usd).to eq(100.0)
      expect(quota.monthly_request_limit).to eq(100_000)
      expect(quota.burst_rpm).to eq(100)
    end
  end
end
