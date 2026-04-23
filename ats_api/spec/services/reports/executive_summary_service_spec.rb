# frozen_string_literal: true

require "rails_helper"

RSpec.describe Reports::ExecutiveSummaryService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  let!(:job_active) { create(:job, user: user, account: account, is_active: true, is_deleted: false, created_at: 5.days.ago) }
  let!(:job_archived) { create(:job, user: user, account: account, is_active: false, is_archived: true, is_deleted: false, updated_at: 3.days.ago) }

  let!(:sp_hired) { create(:selective_process, job: job_active, account: account, status: :hired) }
  let!(:sp_rejected) { create(:selective_process, job: job_active, account: account, status: :rejected) }
  let!(:sp_screening) { create(:selective_process, job: job_active, account: account, status: :screening) }

  let!(:candidate1) { create(:candidate, account: account, source: "LinkedIn", created_at: 5.days.ago) }
  let!(:candidate2) { create(:candidate, account: account, source: "Referral", created_at: 10.days.ago) }

  let!(:apply_hired) { create(:apply, job: job_active, candidate: candidate1, selective_process: sp_hired, account: account, created_at: 5.days.ago) }
  let!(:apply_rejected) { create(:apply, job: job_active, candidate: candidate2, selective_process: sp_rejected, account: account, created_at: 10.days.ago) }

  let!(:interview_completed) do
    create(:calendar_event, :completed,
           organizer: user,
           event_type: "interview",
           start_time: 2.days.ago,
           end_time: 2.days.ago + 1.hour,
           is_deleted: false,
           is_cancelled: false,
           account: account)
  end

  let!(:interview_no_show) do
    create(:calendar_event, :no_show,
           organizer: user,
           event_type: "interview",
           start_time: 3.days.ago,
           end_time: 3.days.ago + 1.hour,
           is_deleted: false,
           is_cancelled: false,
           account: account)
  end

  let!(:evaluation) { create(:evaluation, user: user, job: job_active, account: account, is_deleted: false) }

  let!(:ec_completed) do
    create(:evaluation_candidate,
           evaluation: evaluation, candidate: candidate1,
           account: account, user: user, job: job_active,
           completed: true, score: 80, created_at: 5.days.ago)
  end

  let!(:ec_pending) do
    create(:evaluation_candidate,
           evaluation: evaluation, candidate: candidate2,
           account: account, user: user, job: job_active,
           completed: false, created_at: 5.days.ago)
  end

  let!(:llm_success) { create(:llm_usage, :chat, user: user, account: account, success: true, cost_usd: 0.05, total_tokens: 1000, created_at: 5.days.ago) }
  let!(:llm_failed) { create(:llm_usage, :chat, user: user, account: account, success: false, cost_usd: 0.0, total_tokens: 200, created_at: 5.days.ago) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe "#call" do
    subject(:result) { described_class.new(user: user, period: period, compare_previous: compare_previous).call }

    let(:period) { "month" }
    let(:compare_previous) { false }

    context "with default params" do
      it "returns success" do
        expect(result[:success]).to be true
      end

      it "includes period info" do
        expect(result[:data][:period]).to eq("month")
      end

      it "includes date range" do
        expect(result[:data][:date_range]).to include(:from, :to)
      end

      it "returns jobs stats" do
        jobs = result[:data][:current][:jobs]
        expect(jobs[:active_count]).to be >= 1
        expect(jobs[:created_count]).to be >= 1
        expect(jobs).to have_key(:closed_count)
        expect(jobs).to have_key(:avg_applies_per_job)
      end

      it "returns candidates stats" do
        candidates = result[:data][:current][:candidates]
        expect(candidates[:new_count]).to be >= 1
        expect(candidates[:by_source]).to be_a(Hash)
      end

      it "returns applies stats" do
        applies = result[:data][:current][:applies]
        expect(applies[:total_count]).to be >= 1
        expect(applies).to have_key(:hired_count)
        expect(applies).to have_key(:rejected_count)
        expect(applies).to have_key(:conversion_rate)
      end

      it "returns meetings stats" do
        meetings = result[:data][:current][:meetings]
        expect(meetings[:total_scheduled]).to be >= 2
        expect(meetings[:completed]).to be >= 1
        expect(meetings[:no_show]).to be >= 1
        expect(meetings).to have_key(:no_show_rate)
      end

      it "returns evaluations stats" do
        evals = result[:data][:current][:evaluations]
        expect(evals[:sent_count]).to be >= 2
        expect(evals[:completed_count]).to be >= 1
        expect(evals).to have_key(:response_rate)
        expect(evals).to have_key(:avg_score)
      end

      it "returns llm costs stats" do
        llm = result[:data][:current][:llm_costs]
        expect(llm[:total_requests]).to be >= 2
        expect(llm[:total_cost_usd]).to be > 0
        expect(llm[:total_tokens]).to be > 0
        expect(llm).to have_key(:success_rate)
      end

      it "includes meta" do
        expect(result[:meta][:computed_at]).to be_present
      end
    end

    context "with compare_previous" do
      let(:compare_previous) { true }

      it "returns previous period data" do
        expect(result[:data][:previous]).to be_a(Hash)
        expect(result[:data][:previous]).to have_key(:jobs)
      end

      it "returns trends" do
        trends = result[:data][:trends]
        expect(trends).to have_key(:jobs_created)
        expect(trends).to have_key(:new_candidates)
        expect(trends).to have_key(:total_applies)
        expect(trends).to have_key(:conversion_rate)
        expect(trends).to have_key(:meetings_scheduled)
        expect(trends).to have_key(:evaluations_completed)
        expect(trends).to have_key(:llm_cost)
      end

      it "calculates trend direction" do
        trend = result[:data][:trends][:jobs_created]
        expect(trend).to have_key(:change_pct)
        expect(trend[:direction]).to be_in(%w[up down stable])
      end

      it "includes previous date range" do
        expect(result[:data][:previous_date_range]).to include(:from, :to)
      end
    end

    context "with week period" do
      let(:period) { "week" }

      it "returns success with week range" do
        expect(result[:success]).to be true
        expect(result[:data][:period]).to eq("week")
      end
    end

    context "with quarter period" do
      let(:period) { "quarter" }

      it "returns success with quarter range" do
        expect(result[:success]).to be true
        expect(result[:data][:period]).to eq("quarter")
      end
    end

    context "with invalid period" do
      let(:period) { "invalid" }

      it "defaults to month" do
        expect(result[:success]).to be true
        expect(result[:data][:period]).to eq("month")
      end
    end

    context "with no test data in range" do
      let(:period) { "week" }

      before do
        Job.where(id: [ job_active.id, job_archived.id ]).update_all(created_at: 60.days.ago)
        Candidate.where(id: [ candidate1.id, candidate2.id ]).update_all(created_at: 60.days.ago)
        Apply.where(id: [ apply_hired.id, apply_rejected.id ]).update_all(created_at: 60.days.ago)
      end

      it "handles gracefully without test records in range" do
        expect(result[:success]).to be true
        expect(result[:data][:current]).to have_key(:jobs)
        expect(result[:data][:current]).to have_key(:candidates)
        expect(result[:data][:current]).to have_key(:applies)
      end
    end
  end
end
