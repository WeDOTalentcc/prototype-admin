# frozen_string_literal: true

require "rails_helper"

RSpec.describe Scheduling::BookingService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:candidate) { create(:candidate, account: account, email: "candidate@test.com") }
  let(:link) { create(:scheduling_link, account: account, created_by: user, candidate: candidate, subject: "Technical Interview") }
  let(:slot) do
    create(:scheduling_slot,
      scheduling_link: link,
      start_time: 1.day.from_now.beginning_of_day + 10.hours,
      end_time: 1.day.from_now.beginning_of_day + 11.hours
    )
  end

  subject(:service) { described_class.new(link: link) }

  let(:meeting) do
    Meeting.create!(
      account: account,
      organizer: user,
      subject: "Technical Interview",
      start_time: 1.day.from_now.beginning_of_day + 10.hours,
      end_time: 1.day.from_now.beginning_of_day + 11.hours,
      provider: Meeting::PROVIDERS[:presential]
    )
  end

  let(:calendar_event) do
    CalendarEvent.create!(
      account: account,
      organizer: user,
      title: "Technical Interview",
      start_time: 1.day.from_now.beginning_of_day + 10.hours,
      end_time: 1.day.from_now.beginning_of_day + 11.hours,
      event_type: CalendarEvent::EVENT_TYPES[:interview],
      provider: CalendarEvent::PROVIDERS[:microsoft],
      importance: "normal",
      meeting: meeting
    )
  end

  before do
    allow(MeetingService).to receive(:create).and_return(meeting)
    allow(CalendarService).to receive(:create).and_return(calendar_event)
    allow(Scheduling::BookingNotificationWorker).to receive(:perform_async)
  end

  describe "#book" do
    context "when booking succeeds" do
      it "returns a successful result" do
        result = service.book(slot_id: slot.id)
        expect(result.success?).to be true
      end

      it "marks the slot as unavailable" do
        service.book(slot_id: slot.id)
        expect(slot.reload.is_available).to be false
      end

      it "marks the link as booked" do
        service.book(slot_id: slot.id)
        expect(link.reload.status).to eq("booked")
      end

      it "creates a meeting via MeetingService" do
        service.book(slot_id: slot.id)
        expect(MeetingService).to have_received(:create).with(
          hash_including(
            user: user,
            subject: "Technical Interview",
            start_time: slot.start_time,
            end_time: slot.end_time
          )
        )
      end

      it "creates a calendar event via CalendarService" do
        service.book(slot_id: slot.id)
        expect(CalendarService).to have_received(:create).with(
          hash_including(
            user: user,
            title: "Technical Interview",
            start_time: slot.start_time,
            end_time: slot.end_time
          )
        )
      end

      it "schedules a notification worker" do
        service.book(slot_id: slot.id)
        expect(Scheduling::BookingNotificationWorker).to have_received(:perform_async)
      end

      it "marks remaining slots as unavailable" do
        other_slot = create(:scheduling_slot,
          scheduling_link: link,
          start_time: 1.day.from_now.beginning_of_day + 14.hours,
          end_time: 1.day.from_now.beginning_of_day + 15.hours
        )

        service.book(slot_id: slot.id)
        expect(other_slot.reload.is_available).to be false
      end
    end

    context "when link is not bookable" do
      let(:link) { create(:scheduling_link, :booked, account: account, created_by: user) }

      it "returns failure" do
        result = service.book(slot_id: slot.id)
        expect(result.success?).to be false
        expect(result.errors).to include("Link is no longer available")
      end
    end

    context "when slot is not found" do
      it "returns failure" do
        result = service.book(slot_id: 99999)
        expect(result.success?).to be false
        expect(result.errors).to include("Slot not found")
      end
    end

    context "when slot is unavailable" do
      let(:slot) { create(:scheduling_slot, :unavailable, scheduling_link: link) }

      it "returns failure" do
        result = service.book(slot_id: slot.id)
        expect(result.success?).to be false
        expect(result.errors).to include("Slot is no longer available")
      end
    end

    context "when slot is in the past" do
      let(:slot) { create(:scheduling_slot, :past, scheduling_link: link) }

      it "returns failure" do
        result = service.book(slot_id: slot.id)
        expect(result.success?).to be false
        expect(result.errors).to include("Slot is in the past")
      end
    end

    context "when meeting creation fails completely" do
      before do
        allow(MeetingService).to receive(:create).and_raise(StandardError, "Provider failed")
      end

      it "falls back to creating a local meeting record" do
        result = service.book(slot_id: slot.id)
        expect(result.success?).to be true
        expect(link.reload.meeting_id).to be_present
      end
    end

    context "when link is associated with a phone_call evaluation candidate" do
      let!(:evaluation) { create(:evaluation, account: account) }
      let!(:ec) do
        create(:evaluation_candidate,
          account: account,
          user: user,
          evaluation: evaluation,
          candidate: candidate,
          job: create(:job, account: account),
          evaluation_type: :phone_call,
          phone_call_status: "pending_schedule",
          scheduling_link: link
        )
      end

      before do
        allow(PhoneCallInterviews::TriggerCallJob).to receive(:perform_in)
      end

      it "updates evaluation candidate scheduled_at" do
        service.book(slot_id: slot.id)
        expect(ec.reload.scheduled_at).to eq(slot.start_time)
      end

      it "updates phone_call_status to scheduled" do
        service.book(slot_id: slot.id)
        expect(ec.reload.phone_call_status).to eq("scheduled")
      end

      it "schedules TriggerCallJob" do
        service.book(slot_id: slot.id)
        expect(PhoneCallInterviews::TriggerCallJob).to have_received(:perform_in)
          .with(anything, ec.id, account.id)
      end
    end
  end
end
