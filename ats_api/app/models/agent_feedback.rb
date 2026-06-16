# frozen_string_literal: true

class AgentFeedback < ApplicationRecord
  ACTIONS = %w[approved rejected].freeze

  belongs_to :background_agent
  belongs_to :agent_cycle
  belongs_to :sourced_profile_sourcing

  validates :action, presence: true, inclusion: { in: ACTIONS }
  validates :sourced_profile_sourcing_id, uniqueness: { scope: :background_agent_id }

  scope :approved, -> { where(action: "approved") }
  scope :rejected, -> { where(action: "rejected") }
  scope :recent, -> { order(created_at: :desc) }
end
