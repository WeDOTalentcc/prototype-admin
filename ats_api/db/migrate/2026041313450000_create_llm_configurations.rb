# frozen_string_literal: true

class CreateLlmConfigurations < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists?("accounts")
      create_table :llm_configurations, if_not_exists: true do |t|
        t.references :account, null: false, foreign_key: false
        t.string :provider, null: false, default: "gemini"
        t.text :encrypted_api_key, null: false
        t.boolean :active, null: false, default: true
        t.jsonb :metadata, null: false, default: {}

        t.timestamps
      end

      add_index :llm_configurations, :account_id, unique: true, if_not_exists: true
      add_index :llm_configurations, :provider, if_not_exists: true
      add_index :llm_configurations, :active, if_not_exists: true
    end
  end
end
