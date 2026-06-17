# frozen_string_literal: true

class MeetingSerializer
  include JSONAPI::Serializer

  attributes :id, :subject, :provider, :status, :sub_status, :join_url, :location, :job_id, :apply_id, :start_time, :end_time, :settings

  attribute :sub_status_text do |meeting|
    meeting.sub_status_text
  end

  attribute :organizer_name do |meeting|
    meeting.organizer&.name
  end

  attribute :organizer_email do |meeting|
    meeting.organizer&.email
  end

  attribute :duration_minutes do |meeting|
    meeting.duration_minutes
  end

  attribute :is_active do |meeting|
    meeting.active?
  end

  attribute :created_at do |meeting|
    meeting.created_at.iso8601
  end

  attribute :updated_at do |meeting|
    meeting.updated_at.iso8601
  end
end
