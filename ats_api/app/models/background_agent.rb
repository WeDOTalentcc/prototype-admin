# frozen_string_literal: true

class BackgroundAgent < ApplicationRecord
  CALIBRATION_STATES = %w[pending learning calibrated].freeze
  MODES = %w[review auto_add].freeze
  STATUSES = %w[active paused stopped].freeze
  TARGET_TYPES = %w[Job List].freeze
  DEFAULT_SOURCES = ["local"].freeze
  CALIBRATION_THRESHOLD = 5

  belongs_to :job, optional: true
  belongs_to :list, optional: true
  belongs_to :user
  belongs_to :account

  has_many :agent_cycles, dependent: :destroy
  has_many :sourcings, through: :agent_cycles
  has_many :agent_feedbacks, dependent: :destroy
  has_many :background_agent_steps, dependent: :destroy

  validates :name, presence: true
  validates :status, inclusion: { in: STATUSES }
  validates :calibration_state, inclusion: { in: CALIBRATION_STATES }
  validates :mode, inclusion: { in: MODES }
  validates :target_type, inclusion: { in: TARGET_TYPES }
  validates :daily_limit, numericality: { greater_than: 0 }
  validates :min_score_threshold, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 100 }
  validate :must_have_target

  scope :active, -> { where(status: "active", is_deleted: false) }
  scope :paused, -> { where(status: "paused", is_deleted: false) }
  scope :runnable, -> { active.where("last_run_at IS NULL OR last_run_at < ?", Time.current.beginning_of_day) }
  scope :calibrated, -> { where(calibration_state: "calibrated") }
  scope :by_job, ->(job_id) { where(job_id: job_id) }
  scope :by_list, ->(list_id) { where(list_id: list_id) }
  scope :by_target_type, ->(type) { where(target_type: type) }

  def target
    target_type == "List" ? list : job
  end

  def target_name
    target_type == "List" ? list&.name : job&.title
  end

  def list_agent?
    target_type == "List"
  end

  def job_agent?
    target_type == "Job"
  end

  before_save :sync_sources_from_config

  def pause!
    update!(status: "paused", paused_at: Time.current)
  end

  def resume!
    update!(status: "active", paused_at: nil)
  end

  def stop!
    update!(status: "stopped", stopped_at: Time.current)
  end

  def calibrated?
    calibration_state == "calibrated"
  end

  def approval_rate
    return 0.0 if total_delivered.zero?
    (total_approved.to_f / total_delivered * 100).round(1)
  end

  def remaining_today
    delivered_today = agent_cycles
      .where("created_at >= ?", Time.current.beginning_of_day)
      .sum(:candidates_delivered)
    [daily_limit - delivered_today, 0].max
  end

  def should_auto_pause?
    return false if last_interaction_at.blank?
    last_interaction_at < auto_pause_days.days.ago
  end

  def current_cycle
    agent_cycles.where(status: "running").order(cycle_number: :desc).first
  end

  def next_cycle_number
    (agent_cycles.maximum(:cycle_number) || 0) + 1
  end

  SEARCH_HISTORY_LIMIT = 100

  def log_search_iteration!(iteration_data)
    current_history = (search_history || []).last(SEARCH_HISTORY_LIMIT - 1)
    current_history << iteration_data.merge(timestamp: Time.current.iso8601)
    update!(search_history: current_history)
  end

  private

  def must_have_target
    return if job_id.present? || list_id.present?

    errors.add(:base, "must have either job_id or list_id")
  end

  def sync_sources_from_config
    return unless search_iteration_config_changed?

    providers = search_iteration_config&.dig("enabled_providers")
    self.sources = providers if providers.present?
  end
end
