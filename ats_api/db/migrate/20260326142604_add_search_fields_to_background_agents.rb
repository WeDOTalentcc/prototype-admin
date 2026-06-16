# frozen_string_literal: true

class AddSearchFieldsToBackgroundAgents < ActiveRecord::Migration[7.1]
  def change
    add_column :background_agents, :search_iteration_config, :jsonb, default: {}, null: false
    add_column :background_agents, :search_history, :jsonb, default: [], null: false
  end
end
