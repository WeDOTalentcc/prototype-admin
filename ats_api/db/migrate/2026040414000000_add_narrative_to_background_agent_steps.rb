# frozen_string_literal: true

class AddNarrativeToBackgroundAgentSteps < ActiveRecord::Migration[7.1]
  def change
    add_column :background_agent_steps, :narrative, :jsonb unless column_exists?(:background_agent_steps, :narrative)
  end
end
