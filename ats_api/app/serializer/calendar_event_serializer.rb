# frozen_string_literal: true

class CalendarEventSerializer
  include JSONAPI::Serializer

  attributes :id, :provider, :external_id, :external_uid, :title, :description, :location,
             :event_type, :importance, :start_time, :end_time, :timezone,
             :is_all_day, :is_cancelled, :is_deleted, :settings, :metadata, :meeting_id, :job_id, :apply_id, :sub_status

  attribute :sub_status_text do |event|
    event.sub_status_text
  end

  attribute :status do |event|
    event.status.to_s
  end

  attribute :provider_text do |event|
    event.provider_text
  end

  attribute :event_type_text do |event|
    event.event_type_text
  end

  attribute :organizer_id do |event|
    event.organizer_id
  end

  attribute :organizer_name do |event|
    event.organizer&.name
  end

  attribute :organizer_email do |event|
    event.organizer&.email
  end

  attribute :duration_minutes do |event|
    event.duration_minutes
  end

  attribute :has_online_meeting do |event|
    event.has_online_meeting?
  end

  attribute :join_url do |event|
    event.join_url
  end

  attribute :attendees do |event|
    event.attendees.map do |attendee|
      {
        id: attendee.id,
        email: attendee.email,
        name: attendee.name,
        response_status: attendee.response_status,
        is_organizer: attendee.is_organizer,
        responded_at: attendee.responded_at
      }
    end
  end

  attribute :created_at do |event|
    event.created_at.iso8601
  end

  attribute :updated_at do |event|
    event.updated_at.iso8601
  end
end
