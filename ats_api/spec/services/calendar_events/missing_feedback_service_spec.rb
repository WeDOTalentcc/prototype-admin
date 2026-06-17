# frozen_string_literal: true

require "rails_helper"

RSpec.describe CalendarEvents::MissingFeedbackService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let!(:candidate1) { create(:candidate, account: account) }
  let!(:candidate2) { create(:candidate, account: account) }
  let!(:job) { create(:job, account: account, user: user, is_active: true) }
  let!(:sp) { create(:selective_process, job: job, account: account, name: "Funil", status: :web_submission) }
  let!(:apply1) { create(:apply, job: job, candidate: candidate1, selective_process: sp, account: account) }
  let!(:apply2) { create(:apply, job: job, candidate: candidate2, selective_process: sp, account: account) }

  let!(:past_interview1) do
    create(:calendar_event, :interview,
           account: account, organizer: user,
           start_time: 3.days.ago.change(hour: 10),
           end_time: 3.days.ago.change(hour: 11),
           settings: { "apply_id" => apply1.id.to_s, "candidate_id" => candidate1.id.to_s, "job_id" => job.id.to_s })
  end

  let!(:past_interview2) do
    create(:calendar_event, :interview,
           account: account, organizer: user,
           start_time: 5.days.ago.change(hour: 14),
           end_time: 5.days.ago.change(hour: 15),
           settings: { "apply_id" => apply2.id.to_s, "candidate_id" => candidate2.id.to_s, "job_id" => job.id.to_s })
  end

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe "#call" do
    subject(:result) do
      described_class.new(account_id: account.id, user_id: user.id, params: params).call
    end

    let(:params) { {} }

    context "when no feedback exists" do
      it "returns all past interviews" do
        expect(result.events.size).to eq(2)
      end

      it "returns meta with total count" do
        expect(result.meta[:total]).to eq(2)
      end

      it "enriches events with candidate info" do
        event = result.events.find { |e| e[:id] == past_interview1.id }
        expect(event[:candidate][:id]).to eq(candidate1.id)
        expect(event[:candidate][:name]).to eq(candidate1.name)
      end

      it "enriches events with job info" do
        event = result.events.find { |e| e[:id] == past_interview1.id }
        expect(event[:job][:id]).to eq(job.id)
      end

      it "includes days_since_interview" do
        event = result.events.first
        expect(event[:days_since_interview]).to be_a(Integer)
        expect(event[:days_since_interview]).to be >= 0
      end
    end

    context "when feedback exists for an apply" do
      before do
        create(:candidate_feedback, account: account, user: user, apply: apply1, candidate: candidate1, feedback_type: "like")
      end

      it "excludes events with feedback" do
        expect(result.events.size).to eq(1)
        expect(result.events.first[:id]).to eq(past_interview2.id)
      end
    end

    context "when event is in the future" do
      let!(:future_interview) do
        create(:calendar_event, :interview,
               account: account, organizer: user,
               start_time: 1.day.from_now, end_time: 1.day.from_now + 1.hour,
               settings: { "apply_id" => apply1.id.to_s })
      end

      it "excludes future events" do
        ids = result.events.map { |e| e[:id] }
        expect(ids).not_to include(future_interview.id)
      end
    end

    context "when event is cancelled" do
      before { past_interview1.update!(is_cancelled: true) }

      it "excludes cancelled events" do
        expect(result.events.size).to eq(1)
      end
    end

    context "with date filters" do
      let(:params) { { from: 4.days.ago.to_date.to_s, to: 2.days.ago.to_date.to_s } }

      it "filters by date range" do
        expect(result.events.size).to eq(1)
        expect(result.events.first[:id]).to eq(past_interview1.id)
      end
    end

    context "with job_id filter" do
      let(:other_job) { create(:job, account: account, user: user, is_active: true) }
      let(:other_sp) { create(:selective_process, job: other_job, account: account, name: "Funil", status: :web_submission) }
      let!(:other_apply) { create(:apply, job: other_job, candidate: candidate1, selective_process: other_sp, account: account) }
      let!(:other_interview) do
        create(:calendar_event, :interview,
               account: account, organizer: user,
               job_id: other_job.id,
               start_time: 2.days.ago.change(hour: 10),
               end_time: 2.days.ago.change(hour: 11),
               settings: { "apply_id" => other_apply.id.to_s, "job_id" => other_job.id.to_s })
      end

      let(:params) { { job_id: other_job.id } }

      it "filters by job" do
        expect(result.events.size).to eq(1)
        expect(result.events.first[:id]).to eq(other_interview.id)
      end
    end

    context "with pagination" do
      let(:params) { { page: 1, per_page: 1 } }

      it "paginates results" do
        expect(result.events.size).to eq(1)
        expect(result.meta[:total]).to eq(2)
        expect(result.meta[:page]).to eq(1)
        expect(result.meta[:per_page]).to eq(1)
      end
    end
  end
end
