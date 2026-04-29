# frozen_string_literal: true

class AgentCycle < ApplicationRecord
  STATUSES = %w[running delivered reviewed expired cancelled].freeze

  belongs_to :background_agent
  belongs_to :sourcing

  has_many :agent_feedbacks, dependent: :destroy

  validates :cycle_number, presence: true, uniqueness: { scope: :background_agent_id }
  validates :status, inclusion: { in: STATUSES }

  scope :running, -> { where(status: "running") }
  scope :delivered, -> { where(status: "delivered") }
  scope :reviewed, -> { where(status: "reviewed") }
  scope :recent, -> { order(cycle_number: :desc) }

  def deliver!(candidates_count:, total_found:, execution_metadata: nil)
    attrs = {
      status: "delivered",
      candidates_delivered: candidates_count,
      candidates_total_found: total_found,
      delivered_at: Time.current,
      expires_at: 48.hours.from_now
    }
    attrs[:execution_metadata] = execution_metadata if execution_metadata.present?
    update!(attrs)
  end

  def mark_reviewed!
    update!(status: "reviewed", reviewed_at: Time.current)
  end

  def expired?
    expires_at.present? && expires_at < Time.current
  end

  def feedback_summary
    feedbacks = agent_feedbacks.loaded? ? agent_feedbacks.group_by(&:action).transform_values(&:size) : agent_feedbacks.group(:action).count
    approved = feedbacks["approved"] || 0
    rejected = feedbacks["rejected"] || 0
    {
      approved: approved,
      rejected: rejected,
      total: approved + rejected
    }
  end
end
