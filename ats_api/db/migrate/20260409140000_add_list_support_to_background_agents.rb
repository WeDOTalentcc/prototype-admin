# frozen_string_literal: true

class AddListSupportToBackgroundAgents < ActiveRecord::Migration[7.0]
  def change
    change_column_null :background_agents, :job_id, true
    add_column :background_agents, :list_id, :bigint, null: true
    add_column :background_agents, :target_type, :string, default: "Job", null: false
    add_index :background_agents, :list_id
    add_index :background_agents, :target_type
  end
end
