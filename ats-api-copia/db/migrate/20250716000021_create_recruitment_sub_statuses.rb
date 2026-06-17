# frozen_string_literal: true

class CreateRecruitmentSubStatuses < ActiveRecord::Migration[7.1]
  def change
    create_table :recruitment_sub_statuses, id: :uuid do |t|
      t.references :recruitment_stage, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :name, null: false, limit: 100
      t.string :color, limit: 7
      t.string :icon, limit: 50
      t.integer :order, default: 0
      t.boolean :is_active, default: true
      t.boolean :is_system, default: false
      t.timestamps
    end

    add_index :recruitment_sub_statuses, [:recruitment_stage_id, :order]
  end
end
