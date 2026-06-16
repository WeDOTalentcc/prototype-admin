# frozen_string_literal: true

class AgentNotification < ApplicationRecord
  NOTIFICATION_TYPES = %w[
    briefing
    alert_aging
    alert_deadline
    alert_no_show
    alert_evaluation
    alert_strong_fit
    alert_stale_job
    info
    success
    warning
    error
    action_required
    urgent
  ].freeze

  CATEGORIES = %w[pipeline productivity communication predictive system].freeze
  PRIORITIES = %w[low normal high urgent].freeze
  STATUSES = %w[pending sent delivered read failed].freeze
  CHANNELS = %w[web whatsapp teams].freeze

  belongs_to :user
  belongs_to :reference, polymorphic: true, optional: true

  validates :notification_type, presence: true
  validates :channel, presence: true, inclusion: { in: CHANNELS }
  validates :status, presence: true, inclusion: { in: STATUSES }
  validates :category, inclusion: { in: CATEGORIES }, allow_nil: true
  validates :priority, inclusion: { in: PRIORITIES }, allow_nil: true
  validates :alert_key, uniqueness: true, allow_nil: true

  scope :unread, -> { where(read_at: nil).where.not(status: "failed") }
  scope :by_type, ->(type) { where(notification_type: type) }
  scope :by_category, ->(category) { where(category: category) }
  scope :by_status, ->(status) { where(status: status) }
  scope :since, ->(time) { where("agent_notifications.created_at >= ?", time) }
  scope :recent_first, -> { order(created_at: :desc) }

  def read?
    read_at.present?
  end

  def mark_as_read!
    update!(read_at: Time.current, status: "read") unless read?
  end

  def mark_as_sent!
    update!(sent_at: Time.current, status: "sent")
  end

  def mark_as_failed!
    update!(status: "failed")
  end

  def related_job_id
    reference_id if reference_type == "Job"
  end

  def related_candidate_id
    reference_id if reference_type == "Candidate"
  end
end
