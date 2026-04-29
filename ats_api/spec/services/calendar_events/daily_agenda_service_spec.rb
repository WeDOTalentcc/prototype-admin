# frozen_string_literal: true

require "rails_helper"

RSpec.describe CalendarEvents::DailyAgendaService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let!(:candidate) { create(:candidate, account: account) }
  let!(:job) { create(:job, account: account, user: user, is_active: true) }
  let!(:sp) { create(:selective_process, job: job, account: account, name: "Funil", status: :web_submission) }
  let!(:apply) { create(:apply, job: job, candidate: candidate, selective_process: sp, account: account) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe "#call" do
    subject(:result) do
      described_class.new(account_id: account.id, params: params).call
    end

    context "with upcoming events" do
      let(:params) { {} }

      let!(:event) do
        create(:calendar_event, :interview,
               account: account, organizer: user,
               start_time: 1.hour.from_now, end_time: 2.hours.from_now,
               settings: { "apply_id" => apply.id.to_s, "candidate_id" => candidate.id.to_s, "job_id" => job.id.to_s })
      end

      it "returns grouped days" do
        expect(result.days).to be_an(Array)
        expect(result.days.first[:date]).to eq(Time.current.to_date.iso8601)
      end

      it "returns meta with total count" do
        expect(result.meta[:total]).to eq(1)
      end

      it "serializes event with all fields" do
        serialized = result.days.first[:events].first
        expect(serialized[:id]).to eq(event.id)
        expect(serialized[:title]).to eq(event.title)
        expect(serialized[:event_type]).to eq("interview")
        expect(serialized[:start_time]).to be_present
        expect(serialized[:end_time]).to be_present
      end

      it "enriches event with candidate info" do
        serialized = result.days.first[:events].first
        expect(serialized[:candidate][:id]).to eq(candidate.id)
        expect(serialized[:candidate][:name]).to eq(candidate.name)
      end

      it "enriches event with job info" do
        serialized = result.days.first[:events].first
        expect(serialized[:job][:id]).to eq(job.id)
        expect(serialized[:job][:title]).to eq(job.title)
      end
    end

    context "with has_feedback field" do
      let(:params) { {} }

      let!(:event) do
        create(:calendar_event, :interview,
               account: account, organizer: user,
               start_time: 1.hour.from_now, end_time: 2.hours.from_now,
               settings: { "apply_id" => apply.id.to_s, "candidate_id" => candidate.id.to_s })
      end

      context "when no feedback exists" do
        it "returns has_feedback as false" do
          serialized = result.days.first[:events].first
          expect(serialized[:has_feedback]).to be false
        end
      end

      context "when feedback exists for the apply" do
        before do
          create(:candidate_feedback, account: account, user: user, apply: apply, candidate: candidate, feedback_type: "like")
        end

        it "returns has_feedback as true" do
          serialized = result.days.first[:events].first
          expect(serialized[:has_feedback]).to be true
        end
      end

      context "when feedback exists for candidate without apply" do
        let!(:event_no_apply) do
          create(:calendar_event, :interview,
                 account: account, organizer: user,
                 start_time: 1.hour.from_now, end_time: 2.hours.from_now,
                 settings: { "candidate_id" => candidate.id.to_s })
        end

        before do
          create(:candidate_feedback, account: account, user: user, candidate: candidate, feedback_type: "dislike")
        end

        it "returns has_feedback as true via candidate lookup" do
          event_data = result.days.flat_map { |d| d[:events] }.find { |e| e[:id] == event_no_apply.id }
          expect(event_data[:has_feedback]).to be true
        end
      end
    end

    context "with history kind" do
      let(:params) { { kind: "history" } }

      let!(:past_event) do
        create(:calendar_event, :interview,
               account: account, organizer: user,
               start_time: 2.days.ago.change(hour: 10), end_time: 2.days.ago.change(hour: 11))
      end

      it "returns past events" do
        ids = result.days.flat_map { |d| d[:events] }.map { |e| e[:id] }
        expect(ids).to include(past_event.id)
      end
    end

    context "with event_type filter" do
      let(:params) { { event_type: "generic" } }

      let!(:interview_event) do
        create(:calendar_event, :interview, account: account, organizer: user,
               start_time: 1.hour.from_now, end_time: 2.hours.from_now)
      end

      let!(:generic_event) do
        create(:calendar_event, account: account, organizer: user,
               event_type: "generic",
               start_time: 1.hour.from_now, end_time: 2.hours.from_now)
      end

      it "filters by event type" do
        ids = result.days.flat_map { |d| d[:events] }.map { |e| e[:id] }
        expect(ids).to include(generic_event.id)
        expect(ids).not_to include(interview_event.id)
      end
    end

    context "with pagination" do
      let(:params) { { page: 1, per_page: 1 } }

      let!(:event1) do
        create(:calendar_event, account: account, organizer: user,
               start_time: 1.hour.from_now, end_time: 2.hours.from_now)
      end

      let!(:event2) do
        create(:calendar_event, account: account, organizer: user,
               start_time: 3.hours.from_now, end_time: 4.hours.from_now)
      end

      it "paginates results" do
        expect(result.days.flat_map { |d| d[:events] }.size).to eq(1)
        expect(result.meta[:total]).to eq(2)
      end
    end

    context "with search term" do
      let(:params) { { search: "specific" } }

      let!(:matching_event) do
        create(:calendar_event, account: account, organizer: user,
               title: "Specific interview topic",
               start_time: 1.hour.from_now, end_time: 2.hours.from_now)
      end

      let!(:non_matching_event) do
        create(:calendar_event, account: account, organizer: user,
               title: "Regular meeting",
               start_time: 1.hour.from_now, end_time: 2.hours.from_now)
      end

      it "filters by search term" do
        ids = result.days.flat_map { |d| d[:events] }.map { |e| e[:id] }
        expect(ids).to include(matching_event.id)
        expect(ids).not_to include(non_matching_event.id)
      end
    end
  end
end
