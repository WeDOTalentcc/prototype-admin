# frozen_string_literal: true

class CreateAtsStageMappings < ActiveRecord::Migration[7.1]
  def change
    create_table :ats_stage_mappings, id: :uuid do |t|
      t.references :ats_connection, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :external_stage_name, null: false, limit: 200
      t.string :external_stage_id, limit: 200
      t.references :recruitment_stage, type: :uuid, foreign_key: { on_delete: :nullify }
      t.string :direction, limit: 10, default: "both"  # import, export, both
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :ats_stage_mappings, [:ats_connection_id, :external_stage_id], unique: true, name: "idx_ats_stage_map_unique"
  end
end
