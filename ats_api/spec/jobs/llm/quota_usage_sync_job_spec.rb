# frozen_string_literal: true

require "rails_helper"

RSpec.describe Llm::QuotaUsageSyncJob, type: :job do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let!(:quota) { create(:llm_quota, account: account) }

  describe "#perform" do
    before do
      create(:llm_usage,
        account: account,
        user: user,
        cost_usd: 0.05,
        success: true,
        model: "gemini-2.5-flash",
        operation: "chat",
        created_at: Time.current
      )
      create(:llm_usage,
        account: account,
        user: user,
        cost_usd: 0.03,
        success: true,
        model: "gemini-2.5-flash",
        operation: "search",
        created_at: Time.current
      )
      create(:llm_usage,
        account: account,
        user: user,
        cost_usd: 0.10,
        success: false,
        model: "gemini-2.5-flash",
        operation: "chat",
        created_at: Time.current
      )
    end

    it "syncs usage snapshot from llm_usages" do
      described_class.new.perform

      usage = LlmQuotaUsage.current_for(account.id)
      expect(usage.total_cost_usd.to_f).to eq(0.08)
      expect(usage.total_requests).to eq(2)
      expect(usage.last_synced_at).to be_present
    end

    it "populates cost_by_model breakdown" do
      described_class.new.perform

      usage = LlmQuotaUsage.current_for(account.id)
      expect(usage.cost_by_model).to have_key("gemini-2.5-flash")
    end

    it "populates cost_by_operation breakdown" do
      described_class.new.perform

      usage = LlmQuotaUsage.current_for(account.id)
      expect(usage.cost_by_operation).to have_key("chat")
    end
  end
end
