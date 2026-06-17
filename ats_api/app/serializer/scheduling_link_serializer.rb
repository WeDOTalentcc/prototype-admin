# frozen_string_literal: true

class SchedulingLinkSerializer
  include JSONAPI::Serializer

  attributes :id, :token, :status, :interview_type, :platform,
             :duration_minutes, :location, :subject, :message,
             :job_id, :apply_id, :candidate_id, :channels

  attribute :expires_at do |link|
    link.expires_at&.iso8601
  end

  attribute :booked_at do |link|
    link.booked_at&.iso8601
  end

  attribute :created_at do |link|
    link.created_at.iso8601
  end

  attribute :is_bookable do |link|
    link.bookable?
  end

  attribute :created_by_name do |link|
    link.created_by&.name
  end

  attribute :created_by_email do |link|
    link.created_by&.email
  end

  attribute :slots do |link|
    link.scheduling_slots.ordered.map do |slot|
      {
        id: slot.id,
        start_time: slot.start_time.iso8601,
        end_time: slot.end_time.iso8601,
        is_available: slot.is_available
      }
    end
  end

  attribute :meeting_id do |link|
    link.meeting_id
  end

  attribute :calendar_event_id do |link|
    link.calendar_event_id
  end

  attribute :public_url do |link|
    frontend = ENV.fetch("FRONT_URL", "http://localhost:3000")
    "#{frontend}/scheduling/#{link.account&.uid}/#{link.token}"
  end
end
