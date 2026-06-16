# frozen_string_literal: true

class CreateCandidateLists < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_lists, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :list_type, limit: 30, default: "manual"  # manual, smart, import
      t.jsonb :filters, default: {}            # for smart lists
      t.integer :candidate_count, default: 0
      t.boolean :is_active, default: true
      t.string :created_by
      t.timestamps
    end

    add_index :candidate_lists, :company_id
    add_index :candidate_lists, [:company_id, :is_active]

    create_table :candidate_list_members, id: :uuid do |t|
      t.references :candidate_list, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :candidate_id, null: false
      t.string :added_by
      t.text :notes
      t.timestamps
    end

    add_index :candidate_list_members, [:candidate_list_id, :candidate_id], unique: true, name: "idx_list_members_unique"
    add_index :candidate_list_members, :candidate_id
  end
end
