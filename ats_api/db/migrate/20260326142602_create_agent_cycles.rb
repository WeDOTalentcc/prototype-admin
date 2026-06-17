# frozen_string_literal: true

class CreateAgentCycles < ActiveRecord::Migration[7.1]
  def change
    create_table :agent_cycles do |t|
      t.references :background_agent, null: false, foreign_key: true
      t.references :sourcing, null: false, foreign_key: true

      t.integer :cycle_number, null: false
      t.string :status, null: false, default: "running"
      t.integer :candidates_delivered, default: 0, null: false
      t.integer :candidates_total_found, default: 0, null: false
      t.jsonb :execution_metadata, default: {}
      t.datetime :delivered_at
      t.datetime :reviewed_at
      t.datetime :expires_at

      t.timestamps
    end

    add_index :agent_cycles, [:background_agent_id, :status]
    add_index :agent_cycles, [:background_agent_id, :cycle_number], unique: true
  end
end
