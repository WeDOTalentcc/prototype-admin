# frozen_string_literal: true

require "rails_helper"

RSpec.describe LlmQuotaUsage, type: :model do
  describe "associations" do
    it { should belong_to(:account) }
  end

  describe "validations" do
    subject { create(:llm_quota_usage) }

    it { should validate_presence_of(:period) }
    it { should validate_numericality_of(:total_cost_usd).is_greater_than_or_equal_to(0) }
    it { should validate_numericality_of(:total_requests).is_greater_than_or_equal_to(0) }
    it { should validate_numericality_of(:total_tokens).is_greater_than_or_equal_to(0) }

    it "validates period format" do
      usage = build(:llm_quota_usage, period: "invalid")
      expect(usage).not_to be_valid
    end

    it "accepts valid period format" do
      usage = build(:llm_quota_usage, period: "2026-02")
      expect(usage).to be_valid
    end
  end

  describe ".current_for" do
    let(:account) { create(:account) }

    it "creates a new record for current month when none exists" do
      usage = LlmQuotaUsage.current_for(account.id)

      expect(usage).to be_persisted
      expect(usage.period).to eq(Date.current.strftime("%Y-%m"))
      expect(usage.total_cost_usd).to eq(0)
    end

    it "returns existing record for current month" do
      existing = create(:llm_quota_usage, account: account, total_cost_usd: 10.0)
      usage = LlmQuotaUsage.current_for(account.id)

      expect(usage.id).to eq(existing.id)
      expect(usage.total_cost_usd).to eq(10.0)
    end
  end

  describe "scopes" do
    let(:account) { create(:account) }

    before do
      create(:llm_quota_usage, account: account, period: Date.current.strftime("%Y-%m"))
      create(:llm_quota_usage, account: account, period: "2025-01")
    end

    describe ".for_period" do
      it "returns usages for the specified period" do
        results = LlmQuotaUsage.for_period(Date.current.strftime("%Y-%m")).where(account_id: account.id)
        expect(results.count).to eq(1)
      end
    end

    describe ".current_month" do
      it "returns usages for the current month" do
        results = LlmQuotaUsage.current_month.where(account_id: account.id)
        expect(results.count).to eq(1)
        expect(results.first.period).to eq(Date.current.strftime("%Y-%m"))
      end
    end
  end

  describe "#increment_usage!" do
    let(:usage) { create(:llm_quota_usage, total_cost_usd: 5.0, total_requests: 100, total_tokens: 50_000) }

    it "atomically increments cost, requests, and tokens" do
      usage.increment_usage!(cost: 0.05, tokens: 1500)

      expect(usage.total_cost_usd.to_f).to eq(5.05)
      expect(usage.total_requests).to eq(101)
      expect(usage.total_tokens).to eq(51_500)
    end
  end
end
