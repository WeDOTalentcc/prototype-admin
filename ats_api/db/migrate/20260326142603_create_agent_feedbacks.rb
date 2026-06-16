# frozen_string_literal: true

class CreateAgentFeedbacks < ActiveRecord::Migration[7.1]
  def change
    create_table :agent_feedbacks do |t|
      t.references :background_agent, null: false, foreign_key: true
      t.references :agent_cycle, null: false, foreign_key: true
      t.references :sourced_profile_sourcing, null: false, foreign_key: true

      t.string :action, null: false
      t.text :reason

      t.timestamps
    end

    add_index :agent_feedbacks, [:background_agent_id, :sourced_profile_sourcing_id],
              unique: true, name: "idx_agent_feedbacks_agent_profile_unique"
    add_index :agent_feedbacks, :action
  end
end
