# frozen_string_literal: true

require 'rails_helper'

RSpec.describe LlmUsage, type: :model do
  describe 'associations' do
    it { should belong_to(:user) }
    it { should belong_to(:account) }
  end

  describe 'validations' do
    it { should validate_presence_of(:model) }
    it { should validate_presence_of(:operation) }
    it { should validate_numericality_of(:cost_usd).is_greater_than_or_equal_to(0) }
    it { should validate_numericality_of(:latency_ms).is_greater_than_or_equal_to(0) }
  end

  describe 'scopes' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }

    before do
      create(:llm_usage, account: account, user: user, success: true, cost_usd: 0.05)
      create(:llm_usage, account: account, user: user, success: false, cost_usd: 0.0)
      create(:llm_usage, account: account, user: user, success: true, cost_usd: 0.03)
    end

    it 'filters successful usages' do
      expect(LlmUsage.successful.count).to eq(2)
    end

    it 'filters failed usages' do
      expect(LlmUsage.failed.count).to eq(1)
    end

    it 'filters by account' do
      expect(LlmUsage.by_account(account.id).count).to eq(3)
    end

    it 'orders by recent' do
      recent = LlmUsage.recent.first
      expect(recent.created_at).to be >= 1.minute.ago
    end
  end

  describe '.total_cost_by_account' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }

    before do
      create(:llm_usage, account: account, user: user, cost_usd: 0.05, success: true)
      create(:llm_usage, account: account, user: user, cost_usd: 0.03, success: true)
      create(:llm_usage, account: account, user: user, cost_usd: 0.10, success: false)
    end

    it 'sums only successful costs' do
      total = LlmUsage.total_cost_by_account(account.id)
      expect(total).to eq(0.08)
    end
  end

  describe '.usage_stats_by_model' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }

    before do
      create(:llm_usage,
        account: account,
        user: user,
        model: "gemini-2.5-flash",
        input_tokens: 1000,
        output_tokens: 500,
        total_tokens: 1500,
        cost_usd: 0.05,
        latency_ms: 250.0,
        success: true
      )
      create(:llm_usage,
        account: account,
        user: user,
        model: "gemini-2.5-flash",
        input_tokens: 2000,
        output_tokens: 1000,
        total_tokens: 3000,
        cost_usd: 0.10,
        latency_ms: 300.0,
        success: true
      )
    end

    it 'aggregates stats by model' do
      stats = LlmUsage.usage_stats_by_model(account.id)
      gemini_stats = stats.find { |s| s.model == "gemini-2.5-flash" }

      expect(gemini_stats.request_count).to eq(2)
      expect(gemini_stats.total_input_tokens).to eq(3000)
      expect(gemini_stats.total_output_tokens).to eq(1500)
      expect(gemini_stats.total_cost).to eq(0.15)
      expect(gemini_stats.avg_latency_ms).to eq(275.0)
    end
  end
end
