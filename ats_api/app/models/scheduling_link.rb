# frozen_string_literal: true

class SchedulingLink < ApplicationRecord
  STATUSES = {
    active: "active",
    booked: "booked",
    expired: "expired",
    cancelled: "cancelled"
  }.freeze

  INTERVIEW_TYPES = {
    technical: "technical",
    behavioral: "behavioral",
    cultural_fit: "cultural_fit",
    case_study: "case_study",
    online: "online",
    presential: "presential"
  }.freeze

  PLATFORMS = {
    teams: "teams",
    microsoft_teams: "microsoft_teams",
    google_meet: "google_meet",
    zoom: "zoom"
  }.freeze

  belongs_to :account
  belongs_to :created_by, class_name: "User"
  belongs_to :apply, optional: true
  belongs_to :candidate, optional: true
  belongs_to :job, optional: true
  belongs_to :meeting, optional: true
  belongs_to :calendar_event, optional: true

  has_many :scheduling_slots, dependent: :destroy

  validates :token, presence: true, uniqueness: true
  validates :status, presence: true, inclusion: { in: STATUSES.values }
  validates :duration_minutes, presence: true, inclusion: { in: SchedulingSetting::VALID_DURATIONS }
  validates :interview_type, inclusion: { in: INTERVIEW_TYPES.values }, allow_nil: true
  validates :platform, inclusion: { in: PLATFORMS.values }, allow_nil: true

  before_validation :generate_token, on: :create

  scope :active, -> { where(status: STATUSES[:active]) }
  scope :booked, -> { where(status: STATUSES[:booked]) }
  scope :expired, -> { where(status: STATUSES[:expired]) }
  scope :not_expired, -> { where.not(status: STATUSES[:expired]) }

  def active?
    status == STATUSES[:active]
  end

  def booked?
    status == STATUSES[:booked]
  end

  def expired?
    return true if expires_at.present? && expires_at < Time.current

    status == STATUSES[:expired]
  end

  def bookable?
    active? && !expired?
  end

  def mark_as_booked!(slot_time)
    update!(status: STATUSES[:booked], booked_at: slot_time)
  end

  def mark_as_expired!
    update!(status: STATUSES[:expired])
  end

  private

  def generate_token
    self.token ||= SecureRandom.urlsafe_base64(32)
  end
end
