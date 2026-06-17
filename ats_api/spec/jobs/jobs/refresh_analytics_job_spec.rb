# frozen_string_literal: true

require "rails_helper"

RSpec.describe Jobs::RefreshAnalyticsJob do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }

  describe "#perform" do
    it "computes and persists analytics for the given job" do
      create(:selective_process, job: job, account: account, name: "Funnel", position: 0, status: :web_submission)

      expect {
        described_class.new.perform(job.id, account.id)
      }.to change(JobAnalyticsSnapshot, :count).by(1)
    end

    it "updates existing snapshot on subsequent runs" do
      create(:selective_process, job: job, account: account, name: "Funnel", position: 0, status: :web_submission)

      described_class.new.perform(job.id, account.id)
      described_class.new.perform(job.id, account.id)

      expect(JobAnalyticsSnapshot.where(job_id: job.id).count).to eq(1)
    end

    it "does nothing when account is not found" do
      expect {
        described_class.new.perform(job.id, 0)
      }.not_to change(JobAnalyticsSnapshot, :count)
    end

    it "does nothing when job is not found" do
      expect {
        described_class.new.perform(0, account.id)
      }.not_to change(JobAnalyticsSnapshot, :count)
    end
  end

  describe ".enqueue" do
    it "schedules a job when no debounce lock exists" do
      Sidekiq.redis { |conn| conn.flushdb }

      expect(described_class).to receive(:perform_in).with(30, job.id, account.id)
      described_class.enqueue(job.id, account.id)
    end

    it "skips scheduling when debounce lock exists" do
      Sidekiq.redis { |conn| conn.set("job_analytics_refresh:#{job.id}", "1", ex: 30) }

      expect(described_class).not_to receive(:perform_in)
      described_class.enqueue(job.id, account.id)
    end
  end
end
