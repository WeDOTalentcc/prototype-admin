# frozen_string_literal: true

class AgentFeedbackSerializer
  include JSONAPI::Serializer

  attributes :action, :reason, :created_at

  belongs_to :background_agent
  belongs_to :agent_cycle
  belongs_to :sourced_profile_sourcing
end
