# frozen_string_literal: true

class BackgroundAgentStep < ApplicationRecord
  STEPS = %w[plan load_context generate_queries search deduplicate evaluate reformulate paginate score select_batch search_similar search_pearch search_linkedin search_semantic deliver completed error].freeze
  STATUSES = %w[running done error].freeze

  belongs_to :background_agent
  belongs_to :agent_cycle, optional: true

  validates :step, presence: true, inclusion: { in: STEPS }
  validates :status, inclusion: { in: STATUSES }

  scope :by_cycle, ->(cycle_id) { where(agent_cycle_id: cycle_id) }
  scope :recent, -> { order(created_at: :desc) }
  scope :chronological, -> { order(created_at: :asc) }
end
