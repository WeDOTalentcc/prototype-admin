# frozen_string_literal: true

class CreateFeatureFlags < ActiveRecord::Migration[7.1]
  def change
    create_table :feature_flags, id: :uuid do |t|
      t.string :company_id                         # NULL = global flag
      t.string :flag_name, null: false, limit: 100
      t.boolean :enabled, default: false
      t.integer :rollout_percentage, default: 0    # 0-100 for gradual rollout
      t.jsonb :metadata, default: {}               # conditions, user_ids, etc.
      t.text :description
      t.string :created_by
      t.timestamps
    end

    add_index :feature_flags, [:company_id, :flag_name], unique: true
    add_index :feature_flags, :flag_name
  end
end
