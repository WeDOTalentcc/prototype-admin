# frozen_string_literal: true

require "rails_helper"

RSpec.describe Jobs::AnalyticsService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account, published_date: 10.days.ago, application_deadline: 5.days.from_now) }

  let(:sp_funnel) { create(:selective_process, job: job, account: account, name: "Funnel", position: 0, status: :web_submission) }
  let(:sp_screening) { create(:selective_process, job: job, account: account, name: "Screening", position: 1, status: :screening) }
  let(:sp_interview) { create(:selective_process, job: job, account: account, name: "Interview", position: 2, status: :interview) }
  let(:sp_hired) { create(:selective_process, job: job, account: account, name: "Hired", position: 3, status: :hired) }
  let(:sp_rejected) { create(:selective_process, job: job, account: account, name: "Rejected", position: 4, status: :rejected) }

  subject(:service) { described_class.new(job: job, force_refresh: true) }

  before do
    allow(Rails.cache).to receive(:read).and_return(nil)
    allow(Rails.cache).to receive(:write)
  end

  describe "#call" do
    context "when job has no applies" do
      before do
        sp_funnel
        sp_screening
      end

      it "returns analytics with zero counts" do
        result = service.call

        expect(result[:overview][:total_applies]).to eq(0)
        expect(result[:funnel][:stages].size).to eq(2)
        expect(result[:funnel][:stages].all? { |s| s[:total_entered] == 0 }).to be true
        expect(result[:velocity][:applies_per_day]).to eq(0)
        expect(result[:quality][:avg_cv_match]).to be_nil
        expect(result[:engagement][:total_dispatches]).to eq(0)
        expect(result[:scheduling][:total_interviews_scheduled]).to eq(0)
        expect(result[:team_activity][:actions_by_user]).to be_empty
        expect(result[:computed_at]).to be_present
      end
    end

    context "when job has applies with stage transitions" do
      let(:candidate1) { create(:candidate, account_id: account.id) }
      let(:candidate2) { create(:candidate, account_id: account.id) }

      let!(:apply1) do
        create(:apply, candidate: candidate1, job: job, selective_process: sp_screening,
               account_id: account.id, cv_match: 75.0, total_score: 80.0, is_deleted: false)
      end

      let!(:apply2) do
        create(:apply, candidate: candidate2, job: job, selective_process: sp_funnel,
               account_id: account.id, cv_match: 50.0, total_score: 60.0, is_deleted: false)
      end

      before do
        sp_funnel
        sp_screening
        sp_interview
        sp_hired
        sp_rejected

        create(:apply_status, apply: apply1, selective_process: sp_funnel, user: user,
               account_id: account.id, status_name: "Funnel", created_at: 5.days.ago)
        create(:apply_status, apply: apply1, selective_process: sp_screening, user: user,
               account_id: account.id, status_name: "Screening", created_at: 3.days.ago)

        create(:apply_status, apply: apply2, selective_process: sp_funnel, user: user,
               account_id: account.id, status_name: "Funnel", created_at: 4.days.ago)
      end

      it "returns correct overview" do
        result = service.call

        expect(result[:overview][:total_applies]).to eq(2)
        expect(result[:overview][:active_applies]).to eq(2)
        expect(result[:overview][:days_since_published]).to eq(10)
        expect(result[:overview][:is_deadline_expired]).to be false
      end

      it "computes funnel with stage metrics" do
        result = service.call
        funnel = result[:funnel]

        expect(funnel[:stages]).to be_an(Array)
        expect(funnel[:stages].size).to eq(5)

        funnel_stage = funnel[:stages].find { |s| s[:name] == "Funnel" }
        expect(funnel_stage[:total_entered]).to be >= 1
      end

      it "computes stage time metrics from apply_statuses" do
        result = service.call
        funnel_stage = result[:funnel][:stages].find { |s| s[:name] == "Funnel" }

        expect(funnel_stage[:avg_time_in_stage_hours]).to be_a(Float).or(be_nil)
      end

      it "identifies bottleneck stage" do
        result = service.call
        expect(result[:funnel][:bottleneck_stage]).to be_a(String).or(be_nil)
      end

      it "computes quality metrics" do
        result = service.call
        quality = result[:quality]

        expect(quality[:avg_cv_match]).to be_a(Float)
        expect(quality[:avg_total_score]).to be_a(Float)
        expect(quality[:score_distribution]).to be_a(Hash)
        expect(quality[:score_distribution].keys).to contain_exactly("0-20", "21-40", "41-60", "61-80", "81-100")
      end

      it "computes velocity metrics" do
        result = service.call
        velocity = result[:velocity]

        expect(velocity[:applies_per_day]).to be_a(Float)
        expect(velocity[:applies_trend]).to be_an(Array)
      end

      it "persists snapshot to database" do
        expect { service.call }.to change(JobAnalyticsSnapshot, :count).by(1)
      end

      it "writes to cache" do
        service.call
        expect(Rails.cache).to have_received(:write).with(
          Jobs::AnalyticsService.cache_key(job.id),
          anything,
          expires_in: Jobs::AnalyticsService::CACHE_TTL
        )
      end
    end

    context "when cache has data and force_refresh is false" do
      let(:cached_data) { { overview: { total_applies: 42 }, computed_at: Time.current.iso8601 } }

      subject(:service) { described_class.new(job: job, force_refresh: false) }

      before do
        allow(Rails.cache).to receive(:read)
          .with(Jobs::AnalyticsService.cache_key(job.id))
          .and_return(cached_data)
      end

      it "returns cached data without recomputing" do
        result = service.call
        expect(result).to eq(cached_data)
      end
    end

    context "when job has team activity" do
      let(:candidate) { create(:candidate, account_id: account.id) }
      let!(:apply1) do
        create(:apply, candidate: candidate, job: job, selective_process: sp_funnel,
               account_id: account.id, is_deleted: false)
      end

      before do
        sp_funnel
        sp_screening

        create(:apply_status, apply: apply1, selective_process: sp_funnel, user: user,
               account_id: account.id, status_name: "Funnel", created_at: 2.days.ago)
        create(:apply_status, apply: apply1, selective_process: sp_screening, user: user,
               account_id: account.id, status_name: "Screening", created_at: 1.day.ago)
      end

      it "tracks actions by user" do
        result = service.call
        team = result[:team_activity]

        expect(team[:actions_by_user]).to be_an(Array)
        expect(team[:actions_by_user].first[:user_id]).to eq(user.id)
        expect(team[:actions_by_user].first[:applies_moved]).to be >= 1
      end
    end
  end
end
