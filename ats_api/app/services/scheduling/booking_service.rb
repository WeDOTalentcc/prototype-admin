# frozen_string_literal: true

module Scheduling
  class BookingService
    Result = Struct.new(:success?, :data, :errors, keyword_init: true)

    def initialize(link:)
      @link = link
      @user = link.created_by
      @account = link.account
    end

    def book(slot_id:)
      return failure("Link is no longer available") unless link.bookable?

      slot = link.scheduling_slots.find_by(id: slot_id)
      return failure("Slot not found") unless slot
      return failure("Slot is no longer available") unless slot.available?
      return failure("Slot is in the past") if slot.start_time < Time.current

      ActiveRecord::Base.transaction do
        slot.mark_as_unavailable!

        meeting = create_meeting(slot)
        calendar_event = create_calendar_event(slot, meeting)

        link.update!(
          meeting_id: meeting.id,
          calendar_event_id: calendar_event&.id
        )
        link.mark_as_booked!(slot.start_time)

        mark_remaining_slots_unavailable

        schedule_notification(meeting)

        handle_phone_call_booking(slot) if phone_call_evaluation_candidate.present?

        success(
          link: link.reload,
          meeting: meeting,
          calendar_event: calendar_event,
          slot: slot
        )
      end
    rescue StandardError => e
      Rails.logger.error "❌ [BookingService] Booking failed: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      failure("Booking failed: #{e.message}")
    end

    private

    attr_reader :link, :user, :account

    def create_meeting(slot)
      MeetingService.create(
        user: user,
        subject: link.subject || "Interview",
        start_time: slot.start_time,
        end_time: slot.end_time,
        provider: determine_meeting_provider,
        location: link.location,
        sub_status: Meeting::SUB_STATUSES[:scheduled],
        job_id: link.job_id,
        apply_id: link.apply_id
      )
    rescue StandardError => e
      Rails.logger.error "❌ [BookingService] Meeting creation failed, creating local record: #{e.message}"
      Meeting.create!(
        account: account,
        organizer: user,
        subject: link.subject || "Interview",
        start_time: slot.start_time,
        end_time: slot.end_time,
        provider: Meeting::PROVIDERS[:presential],
        location: link.location,
        sub_status: Meeting::SUB_STATUSES[:scheduled],
        job_id: link.job_id,
        apply_id: link.apply_id
      )
    end

    def create_calendar_event(slot, meeting)
      attendees = build_attendees
      CalendarService.create(
        user: user,
        title: link.subject || "Interview",
        start_time: slot.start_time,
        end_time: slot.end_time,
        meeting_id: meeting.id,
        job_id: link.job_id,
        apply_id: link.apply_id,
        event_type: CalendarEvent::EVENT_TYPES[:interview],
        attendees: attendees,
        location: link.location,
        settings: { online_meeting: online_interview? }
      )
    rescue StandardError => e
      Rails.logger.error "❌ [BookingService] Calendar event creation failed: #{e.message}"
      nil
    end

    def determine_meeting_provider
      return link.platform if link.platform.present?
      return Meeting::PROVIDERS[:presential] if link.interview_type == "presential"

      nil
    end

    def online_interview?
      link.interview_type != "presential"
    end

    def build_attendees
      return [] unless link.candidate.present?

      candidate = link.candidate
      return [] if candidate.email.blank?

      [ { email: candidate.email, name: candidate.name } ]
    end

    def mark_remaining_slots_unavailable
      link.scheduling_slots.available.update_all(is_available: false)
    end

    def schedule_notification(meeting)
      Scheduling::BookingNotificationWorker.perform_async(
        link.id,
        meeting.id,
        account.id
      )
    rescue StandardError => e
      Rails.logger.error "❌ [BookingService] Failed to schedule notification: #{e.message}"
    end

    def success(data)
      Result.new(success?: true, data: data, errors: [])
    end

    def failure(message)
      Result.new(success?: false, data: nil, errors: [ message ])
    end

    def phone_call_evaluation_candidate
      @phone_call_evaluation_candidate ||= EvaluationCandidate.find_by(
        scheduling_link_id: link.id,
        evaluation_type: :phone_call
      )
    end

    def handle_phone_call_booking(slot)
      ec = phone_call_evaluation_candidate
      ec.update!(
        scheduled_at: slot.start_time,
        phone_call_status: "scheduled"
      )

      delay_seconds = [ (slot.start_time - Time.current).to_i, 0 ].max
      PhoneCallInterviews::TriggerCallJob.perform_in(
        delay_seconds,
        ec.id,
        account.id
      )
    rescue StandardError => e
      Rails.logger.error "❌ [BookingService] Phone call booking callback failed: #{e.message}"
    end
  end
end
