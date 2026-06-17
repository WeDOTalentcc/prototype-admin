# frozen_string_literal: true

class CalendarEvent < ApplicationRecord
  include Searchable
  include TracksJobAnalytics

  PROVIDERS = {
    microsoft: "microsoft",
    google: "google"
  }.freeze

  EVENT_TYPES = {
    generic: "generic",
    interview: "interview",
    document_delivery: "document_delivery",
    feedback: "feedback",
    onboarding: "onboarding"
  }.freeze

  IMPORTANCE = %w[low normal high].freeze

  SUB_STATUSES = {
    invite_sent: "invite_sent",
    scheduled: "scheduled",
    confirmed: "confirmed",
    completed: "completed",
    no_show: "no_show"
  }.freeze

  SUB_STATUS_LABELS = {
    "invite_sent" => "Convite Enviado",
    "scheduled"   => "Agendada",
    "confirmed"   => "Confirmada",
    "completed"   => "Realizada",
    "no_show"     => "No-show"
  }.freeze

  RESPONSE_SYNC_FIELDS = %w[
    subject body organizer start end responseStatus isOrganizer
    isCancelled importance onlineMeetingUrl webLink iCalUId attendees id location
  ].join(",").freeze

  belongs_to :account
  belongs_to :organizer, class_name: "User"
  belongs_to :meeting, optional: true
  belongs_to :job, optional: true
  belongs_to :apply, optional: true

  has_many :attendees, class_name: "CalendarEventAttendee", dependent: :destroy

  validates :provider, presence: true, inclusion: { in: PROVIDERS.values }
  validates :title, presence: true
  validates :start_time, presence: true
  validates :end_time, presence: true
  validates :event_type, inclusion: { in: EVENT_TYPES.values }
  validates :importance, inclusion: { in: IMPORTANCE }
  validates :sub_status, inclusion: { in: SUB_STATUSES.values }, allow_nil: true
  validate :end_time_after_start_time

  scope :active, -> { where(is_deleted: false, is_cancelled: false) }
  scope :upcoming, -> { where("start_time > ?", Time.current).order(start_time: :asc) }
  scope :past, -> { where("end_time < ?", Time.current).order(start_time: :desc) }
  scope :by_provider, ->(provider) { where(provider: provider) }
  scope :by_type, ->(event_type) { where(event_type: event_type) }
  scope :in_range, ->(from, to) { where(start_time: from..to) }

  after_create_commit :schedule_post_interview_dispatch, if: :interview?
  after_update_commit :reschedule_post_interview_dispatch, if: :interview_rescheduled?
  after_update_commit :cancel_post_interview_dispatch, if: :interview_cancelled?

  def microsoft?
    provider == PROVIDERS[:microsoft]
  end

  def sub_status_text
    SUB_STATUS_LABELS[sub_status] || sub_status
  end

  def google?
    provider == PROVIDERS[:google]
  end

  def interview?
    event_type == EVENT_TYPES[:interview]
  end

  def active?
    !is_deleted && !is_cancelled
  end

  def soft_delete!
    update!(is_deleted: true)
  end

  def cancel!
    update!(is_cancelled: true)
  end

  def duration_minutes
    return 0 unless start_time && end_time
    ((end_time - start_time) / 60).round
  end

  def status
    return :deleted if is_deleted
    return :cancelled if is_cancelled
    return :in_progress if Time.current.between?(start_time, end_time)
    return :upcoming if start_time > Time.current
    :past
  end

  def has_online_meeting?
    meeting_id.present? || metadata&.dig("onlineMeetingUrl").present?
  end

  def join_url
    meeting&.join_url || metadata&.dig("onlineMeetingUrl")
  end

  def self.graph_fields
    RESPONSE_SYNC_FIELDS
  end

  def search_data
    {
      id: id,
      account_id: account_id,
      organizer_id: organizer_id,
      organizer_name: organizer&.name&.downcase,
      organizer_email: organizer&.email&.downcase,
      provider: provider,
      provider_text: provider_text,
      event_type: event_type,
      event_type_text: event_type_text,
      external_id: external_id,
      title: title&.downcase,
      description: description&.downcase,
      location: location&.downcase,
      importance: importance,
      start_time: start_time,
      end_time: end_time,
      timezone: timezone,
      duration_minutes: duration_minutes,
      status: status.to_s,
      is_all_day: is_all_day,
      is_cancelled: is_cancelled,
      is_deleted: is_deleted,
      has_online_meeting: has_online_meeting?,
      attendee_emails: attendees.pluck(:email),
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [ :title, :description, :location, :organizer_name, :organizer_email, :event_type_text ]
  end

  def self.agg_search_array(_params = {})
    {
      provider: { field: "provider", limit: 10 },
      provider_text: { field: "provider_text", limit: 10 },
      event_type: { field: "event_type", limit: 10 },
      event_type_text: { field: "event_type_text", limit: 10 },
      status: { field: "status", limit: 10 },
      importance: { field: "importance", limit: 5 },
      has_online_meeting: { field: "has_online_meeting", limit: 2 },
      organizer_name: { field: "organizer_name", limit: 50 }
    }
  end

  def provider_text
    case provider
    when PROVIDERS[:microsoft] then "Microsoft"
    when PROVIDERS[:google] then "Google"
    else provider
    end
  end

  def event_type_text
    case event_type
    when EVENT_TYPES[:interview] then "Interview"
    when EVENT_TYPES[:document_delivery] then "Document Delivery"
    when EVENT_TYPES[:feedback] then "Feedback"
    when EVENT_TYPES[:onboarding] then "Onboarding"
    else "Generic"
    end
  end

  private

  def schedule_post_interview_dispatch
    PostInterview::DispatchService.new(calendar_event: self).call
  rescue StandardError => e
    Rails.logger.error "❌ [CalendarEvent] Post-interview dispatch failed: #{e.message}"
  end

  def reschedule_post_interview_dispatch
    cancel_pending_dispatches
    PostInterview::DispatchService.new(calendar_event: self).call
  rescue StandardError => e
    Rails.logger.error "❌ [CalendarEvent] Post-interview reschedule failed: #{e.message}"
  end

  def cancel_post_interview_dispatch
    cancel_pending_dispatches
  end

  def cancel_pending_dispatches
    Dispatch
      .where(reference: self, status: :pending)
      .where("target_payload->>'trigger_event' = ?", PostInterview::DispatchService::TRIGGER_EVENT)
      .update_all(status: :failed)
  end

  def interview_rescheduled?
    interview? && saved_change_to_end_time? && !is_cancelled && !is_deleted
  end

  def interview_cancelled?
    interview? && (saved_change_to_is_cancelled? && is_cancelled || saved_change_to_is_deleted? && is_deleted)
  end

  def end_time_after_start_time
    return unless start_time && end_time
    errors.add(:end_time, "must be after start time") if end_time <= start_time
  end
end
