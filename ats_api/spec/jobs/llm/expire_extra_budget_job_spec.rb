# frozen_string_literal: true

require "rails_helper"

RSpec.describe Llm::ExpireExtraBudgetJob, type: :job do
  describe "#perform" do
    it "zeros out expired extra budgets" do
      quota = create(:llm_quota, :with_expired_extra)

      described_class.new.perform

      quota.reload
      expect(quota.extra_budget_usd).to eq(0)
      expect(quota.extra_budget_expires_at).to be_nil
    end

    it "preserves active extra budgets" do
      quota = create(:llm_quota, :with_extra_budget)

      described_class.new.perform

      quota.reload
      expect(quota.extra_budget_usd).to be > 0
    end

    it "only targets quotas with positive extra budget" do
      quota_no_extra = create(:llm_quota)

      expect { described_class.new.perform }.not_to raise_error
    end
  end
end
