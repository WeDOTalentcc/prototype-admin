# frozen_string_literal: true

class CreateBackgroundAgents < ActiveRecord::Migration[7.1]
  def change
    create_table :background_agents do |t|
      t.references :job, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true

      t.string :name, null: false
      t.text :criteria_text
      t.jsonb :criteria_structured, default: {}
      t.string :calibration_state, null: false, default: "pending"
      t.integer :consecutive_approvals, default: 0, null: false
      t.jsonb :extracted_preferences, default: {}
      t.string :mode, null: false, default: "review"
      t.string :status, null: false, default: "active"
      t.integer :daily_limit, default: 25, null: false
      t.integer :total_delivered, default: 0, null: false
      t.integer :total_approved, default: 0, null: false
      t.integer :total_rejected, default: 0, null: false
      t.integer :auto_pause_days, default: 4, null: false
      t.string :sources, array: true, default: ["local"]
      t.float :min_score_threshold, default: 70.0, null: false
      t.datetime :last_interaction_at
      t.datetime :last_run_at
      t.jsonb :last_run_metadata, default: {}
      t.jsonb :diversity_queries, default: []
      t.datetime :paused_at
      t.datetime :stopped_at
      t.boolean :is_deleted, default: false, null: false

      t.timestamps
    end

    add_index :background_agents, :status
    add_index :background_agents, :calibration_state
    add_index :background_agents, [:status, :calibration_state]
  end
end
