# frozen_string_literal: true

class AddColumnsToBackgroundAgentSteps < ActiveRecord::Migration[7.1]
  def change
    add_reference :background_agent_steps, :background_agent, null: false, foreign_key: true
    add_reference :background_agent_steps, :agent_cycle, foreign_key: true
    add_column :background_agent_steps, :step, :string, null: false
    add_column :background_agent_steps, :status, :string, null: false, default: "running"
    add_column :background_agent_steps, :message, :string
    add_column :background_agent_steps, :details, :jsonb, default: {}
    add_column :background_agent_steps, :iteration_number, :integer

    add_index :background_agent_steps, [ :background_agent_id, :created_at ], name: "idx_agent_steps_agent_created"
    add_index :background_agent_steps, [ :agent_cycle_id, :step ], name: "idx_agent_steps_cycle_step"
  end
end
