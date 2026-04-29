# frozen_string_literal: true

require "rails_helper"

RSpec.describe Llm::MonthlyQuotaSetupJob, type: :job do
  let(:account) { create(:account) }

  describe "#perform" do
    it "pre-creates quota usage records for enabled quotas" do
      create(:llm_quota, account: account, enabled: true)

      described_class.new.perform

      usage = LlmQuotaUsage.find_by(account_id: account.id, period: Time.current.strftime("%Y-%m"))
      expect(usage).to be_present
    end

    it "skips disabled quotas" do
      create(:llm_quota, :disabled, account: account)

      described_class.new.perform

      usage = LlmQuotaUsage.find_by(account_id: account.id, period: Time.current.strftime("%Y-%m"))
      expect(usage).to be_nil
    end

    it "does not duplicate existing records" do
      create(:llm_quota, account: account, enabled: true)
      LlmQuotaUsage.current_for(account.id)

      expect { described_class.new.perform }
        .not_to change { LlmQuotaUsage.where(account_id: account.id).count }
    end

    it "uses current month period" do
      create(:llm_quota, account: account, enabled: true)
      described_class.new.perform

      usage = LlmQuotaUsage.find_by(account_id: account.id)
      expect(usage.period).to eq(Time.current.strftime("%Y-%m"))
    end
  end
end
