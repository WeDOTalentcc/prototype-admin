# frozen_string_literal: true

require "rails_helper"

RSpec.describe PostInterview::DispatchService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account) }
  let(:candidate) { create(:candidate, account: account, email: "candidate@example.com") }
  let(:apply) { create(:apply, candidate: candidate, job: job, account: account) }

  before do
    Apartment::Tenant.switch!(account.tenant)
  end

  describe "with CalendarEvent" do
    let(:calendar_event) do
      create(:calendar_event,
             organizer: user,
             account: account,
             event_type: "interview",
             job: job,
             apply: apply,
             start_time: 1.day.from_now,
             end_time: 1.day.from_now + 1.hour)
    end

    subject { described_class.new(calendar_event: calendar_event).call }

    context "when post-interview template exists" do
      let!(:template) { create(:email_template, :post_interview, account: account, user: user) }

      it "creates a Dispatch with scheduled_for based on end_time + delay" do
        expect { subject }.to change(Dispatch, :count).by(1)

        dispatch = Dispatch.last
        expected_time = calendar_event.end_time + template.delay_hours.hours
        expect(dispatch.scheduled_for).to be_within(1.second).of(expected_time)
        expect(dispatch.status).to eq("pending")
        expect(dispatch.channel_type).to eq("email")
        expect(dispatch.reference).to eq(calendar_event)
        expect(dispatch.target_payload["trigger_event"]).to eq("interview_ended")
        expect(dispatch.target_payload["automated"]).to be true
      end

      it "creates a DispatchMessage for the candidate" do
        expect { subject }.to change(DispatchMessage, :count).by(1)

        message = DispatchMessage.last
        expect(message.recipient).to eq(candidate)
        expect(message.recipient_address).to eq(candidate.email)
        expect(message.status).to eq("pending")
      end

      it "renders tags in subject and body" do
        subject

        dispatch = Dispatch.last
        expect(dispatch.subject).to include(job.title)
        expect(dispatch.body).to include(candidate.name)
        expect(dispatch.body).to include(job.title)
      end

      it "enqueues DispatchOrchestratorJob" do
        expect { subject }.to have_enqueued_job(DispatchOrchestratorJob)
      end

      it "cancels existing pending dispatch for same calendar_event" do
        old_dispatch = create(:dispatch,
                              account: account,
                              user: user,
                              reference: calendar_event,
                              status: :pending,
                              target_payload: { trigger_event: "interview_ended" })

        subject

        expect(old_dispatch.reload.status).to eq("failed")
        expect(Dispatch.pending.where(reference: calendar_event).count).to eq(1)
      end
    end

    context "when no post-interview template exists" do
      it "returns nil and creates no dispatch" do
        expect { subject }.not_to change(Dispatch, :count)
        expect(subject).to be_nil
      end
    end

    context "when candidate has no email" do
      let!(:template) { create(:email_template, :post_interview, account: account, user: user) }

      before { candidate.update_column(:email, nil) }

      it "returns nil and creates no dispatch" do
        expect { subject }.not_to change(Dispatch, :count)
      end
    end
  end

  describe "with InterviewSession" do
    let(:evaluation) { create(:evaluation, account: account, job: job, user: user) }
    let(:interview_session) do
      create(:interview_session,
             account: account,
             evaluation: evaluation,
             candidate: candidate,
             job: job,
             created_by: user,
             status: "completed")
    end

    subject { described_class.new(interview_session: interview_session).call }

    context "when post-interview template exists" do
      let!(:template) { create(:email_template, :post_interview, account: account, user: user) }

      it "creates a Dispatch with scheduled_for based on current time + delay" do
        freeze_time do
          subject

          dispatch = Dispatch.last
          expected_time = Time.current + template.delay_hours.hours
          expect(dispatch.scheduled_for).to be_within(1.second).of(expected_time)
          expect(dispatch.reference).to eq(interview_session)
        end
      end

      it "creates a DispatchMessage for the candidate" do
        expect { subject }.to change(DispatchMessage, :count).by(1)

        message = DispatchMessage.last
        expect(message.recipient).to eq(candidate)
      end
    end
  end
end
