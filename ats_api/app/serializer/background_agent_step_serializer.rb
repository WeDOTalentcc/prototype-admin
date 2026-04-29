# frozen_string_literal: true

class BackgroundAgentStepSerializer
  include JSONAPI::Serializer

  attributes :step, :status, :message, :details, :narrative, :iteration_number, :created_at

  belongs_to :background_agent
  belongs_to :agent_cycle
end
