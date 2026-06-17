# frozen_string_literal: true

class CreateSourcingAgentTables < ActiveRecord::Migration[7.1]
  def change
    create_table :sourcing_agents, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_id
      t.references :talent_pool, type: :uuid, foreign_key: { on_delete: :nullify }
      t.string :name, limit: 200
      t.string :status, limit: 20, default: "active"  # active, paused, completed, archived
      t.string :agent_type, limit: 30, default: "sourcing"  # sourcing, screening, outreach
      t.jsonb :search_strategy, default: {}
      t.jsonb :preferences, default: {}
      t.jsonb :outreach_config, default: {}
      t.integer :calibration_v, default: 0
      t.integer :profiles_viewed, default: 0
      t.integer :profiles_approved, default: 0
      t.integer :profiles_rejected, default: 0
      t.integer :emails_sent, default: 0
      t.string :created_by
      t.timestamps
    end

    add_index :sourcing_agents, :company_id
    add_index :sourcing_agents, :job_id
    add_index :sourcing_agents, [:company_id, :status]

    create_table :sourcing_agent_signals, id: :uuid do |t|
      t.references :sourcing_agent, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :candidate_id, null: false
      t.string :signal_type, limit: 20, null: false  # approve, reject, maybe, skip
      t.text :reason
      t.string :given_by                           # user_id or "system"
      t.float :match_score
      t.jsonb :match_criteria, default: {}
      t.timestamps
    end

    add_index :sourcing_agent_signals, [:sourcing_agent_id, :candidate_id], unique: true, name: "idx_agent_signals_unique"
    add_index :sourcing_agent_signals, :candidate_id
  end
end
