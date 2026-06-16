# frozen_string_literal: true

class CreateRecruitmentStages < ActiveRecord::Migration[7.1]
  def change
    create_table :recruitment_stages, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 100
      t.string :display_name, limit: 100
      t.string :stage_type, limit: 30, default: "custom"
      t.text :description
      t.string :color, limit: 7
      t.string :icon, limit: 50
      t.integer :order, default: 0
      t.boolean :is_active, default: true
      t.boolean :is_system, default: false
      t.boolean :is_initial, default: false
      t.boolean :is_final, default: false
      t.boolean :is_rejection, default: false
      t.boolean :is_hired, default: false
      t.integer :sla_hours
      t.jsonb :auto_advance_rules, default: {}
      t.string :default_channel, limit: 30
      t.jsonb :stage_metadata, default: {}
      t.string :created_by
      t.timestamps
    end

    add_index :recruitment_stages, :company_id
    add_index :recruitment_stages, [:company_id, :is_active]
    add_index :recruitment_stages, [:company_id, :order]
  end
end
