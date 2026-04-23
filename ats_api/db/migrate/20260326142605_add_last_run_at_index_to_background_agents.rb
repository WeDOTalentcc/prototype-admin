# frozen_string_literal: true

class AddLastRunAtIndexToBackgroundAgents < ActiveRecord::Migration[7.1]
  def change
    add_index :background_agents, :last_run_at, if_not_exists: true
    add_index :background_agents, [ :job_id ], if_not_exists: true
    add_index :background_agents, [ :user_id ], if_not_exists: true
  end
end
