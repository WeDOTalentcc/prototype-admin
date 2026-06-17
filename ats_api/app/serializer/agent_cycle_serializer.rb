# frozen_string_literal: true

class AgentCycleSerializer
  include JSONAPI::Serializer

  attributes :cycle_number, :status, :candidates_delivered, :candidates_total_found,
             :delivered_at, :reviewed_at, :expires_at, :created_at, :updated_at,
             :sourcing_id

  attribute :feedback_summary do |cycle|
    cycle.feedback_summary
  end

  attribute :expired do |cycle|
    cycle.expired?
  end

  attribute :execution_metadata do |cycle|
    cycle.execution_metadata || {}
  end

  belongs_to :background_agent
  belongs_to :sourcing
end
