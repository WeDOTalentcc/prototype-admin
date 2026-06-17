# frozen_string_literal: true

class Meeting < ApplicationRecord
  include Searchable

  PROVIDERS = {
    microsoft_teams: "microsoft_teams",
    google_meet: "google_meet",
    zoom: "zoom",
    presential: "presential"
  }.freeze

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

  belongs_to :account
  belongs_to :organizer, class_name: "User"
  belongs_to :job, optional: true
  belongs_to :apply, optional: true

  validates :provider, presence: true, inclusion: { in: PROVIDERS.values }
  validates :subject, presence: true
  validates :start_time, presence: true
  validates :end_time, presence: true
  validates :sub_status, inclusion: { in: SUB_STATUSES.values }, allow_nil: true
  validate :end_time_after_start_time

  scope :active, -> { where(is_deleted: false) }
  scope :deleted, -> { where(is_deleted: true) }
  scope :by_provider, ->(provider) { where(provider: provider) }
  scope :upcoming, -> { where("start_time > ?", Time.current).order(start_time: :asc) }
  scope :past, -> { where("end_time < ?", Time.current).order(start_time: :desc) }

  def microsoft_teams?
    provider == PROVIDERS[:microsoft_teams]
  end

  def presential?
    provider == PROVIDERS[:presential]
  end

  def sub_status_text
    SUB_STATUS_LABELS[sub_status] || sub_status
  end

  def google_meet?
    provider == PROVIDERS[:google_meet]
  end

  def zoom?
    provider == PROVIDERS[:zoom]
  end

  def active?
    !is_deleted
  end

  def soft_delete!
    update(is_deleted: true)
  end

  def restore!
    update(is_deleted: false)
  end

  def duration_minutes
    return 0 unless start_time && end_time
    ((end_time - start_time) / 60).round
  end

  def status
    return :cancelled if is_deleted
    return :in_progress if Time.current.between?(start_time, end_time)
    return :upcoming if start_time > Time.current
    :past
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
      external_id: external_id,
      join_url: join_url,
      subject: subject&.downcase,
      start_time: start_time,
      end_time: end_time,
      duration_minutes: duration_minutes,
      status: status.to_s,
      is_deleted: is_deleted,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [
      :subject,
      :organizer_name,
      :organizer_email,
      :provider_text,
      :external_id
    ]
  end

  def self.agg_search_array(_params = {})
    {
      provider: { field: "provider", limit: 10 },
      provider_text: { field: "provider_text", limit: 10 },
      status: { field: "status", limit: 10 },
      organizer_name: { field: "organizer_name", limit: 50 }
    }
  end

  def provider_text
    case provider
    when PROVIDERS[:microsoft_teams]
      "Microsoft Teams"
    when PROVIDERS[:google_meet]
      "Google Meet"
    when PROVIDERS[:zoom]
      "Zoom"
    when PROVIDERS[:presential]
      "Presencial"
    else
      provider
    end
  end

  private

  def end_time_after_start_time
    return unless start_time && end_time
    errors.add(:end_time, "must be after start time") if end_time <= start_time
  end
end
