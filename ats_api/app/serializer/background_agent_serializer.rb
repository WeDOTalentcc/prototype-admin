# frozen_string_literal: true

class BackgroundAgentSerializer
  include JSONAPI::Serializer

  attributes :name, :criteria_text, :calibration_state,
             :mode, :status, :daily_limit, :total_delivered, :total_approved,
             :total_rejected, :sources, :min_score_threshold, :auto_pause_days,
             :search_iteration_config, :target_type,
             :last_interaction_at, :last_run_at, :paused_at, :stopped_at,
             :created_at, :updated_at

  attribute :approval_rate do |agent|
    agent.approval_rate
  end

  attribute :remaining_today do |agent|
    agent.remaining_today
  end

  attribute :target_name do |agent|
    agent.target_name
  end

  attribute :current_cycle_number do |agent|
    agent.agent_cycles.loaded? ? agent.agent_cycles.select { |c| c.status == "running" }.max_by(&:cycle_number)&.cycle_number : agent.current_cycle&.cycle_number
  end

  attribute :cycles_count do |agent|
    agent.agent_cycles.loaded? ? agent.agent_cycles.size : agent.agent_cycles.count
  end

  belongs_to :job
  belongs_to :list
  belongs_to :user
end
