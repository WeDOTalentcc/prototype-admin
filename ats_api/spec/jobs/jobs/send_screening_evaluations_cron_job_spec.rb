# frozen_string_literal: true

require "rails_helper"

RSpec.describe Jobs::SendScreeningEvaluationsCronJob do
  let(:account) { create(:account, tenant: "public") }
  let(:user) { create(:user, account: account) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe "#perform" do
    it "enqueues SendScreeningEvaluationsJob for each job with is_screening_active" do
      job1 = create(:job, user: user, account: account, is_screening_active: true)
      job2 = create(:job, user: user, account: account, is_screening_active: true)
      create(:job, user: user, account: account, is_screening_active: false)

      allow(Account).to receive(:find_each).and_yield(account)

      expect(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async).with(job1.id, account.id)
      expect(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async).with(job2.id, account.id)

      described_class.new.perform
    end

    it "does not enqueue for deleted jobs" do
      create(:job, user: user, account: account, is_screening_active: true, is_deleted: true)

      allow(Account).to receive(:find_each).and_yield(account)

      expect(Jobs::SendScreeningEvaluationsJob).not_to receive(:perform_async)

      described_class.new.perform
    end

    it "does not enqueue for jobs with allowed_screenings_limit_date in the past" do
      job_within_window = create(:job, user: user, account: account, is_screening_active: true)
      job_past_limit = create(:job, user: user, account: account, is_screening_active: true,
                             allowed_screenings_limit_date: 1.hour.ago)

      allow(Account).to receive(:find_each).and_yield(account)

      expect(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async).with(job_within_window.id, account.id)
      expect(Jobs::SendScreeningEvaluationsJob).not_to receive(:perform_async).with(job_past_limit.id, anything)

      described_class.new.perform
    end

    it "skips accounts with blank tenant" do
      account.update_column(:tenant, nil)

      allow(Account).to receive(:find_each).and_yield(account)

      expect(Jobs::SendScreeningEvaluationsJob).not_to receive(:perform_async)

      described_class.new.perform
    end
  end
end
