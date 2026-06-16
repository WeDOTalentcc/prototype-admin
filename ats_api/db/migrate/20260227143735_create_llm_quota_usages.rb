class CreateLlmQuotaUsages < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :llm_quota_usages, if_not_exists: true do |t|
        t.references :account, null: false, foreign_key: false
        t.string :period, null: false
        t.decimal :total_cost_usd, precision: 12, scale: 8, null: false, default: 0.0
        t.integer :total_requests, null: false, default: 0
        t.integer :total_tokens, null: false, default: 0
        t.jsonb :cost_by_operation, null: false, default: {}
        t.jsonb :cost_by_model, null: false, default: {}
        t.datetime :last_synced_at

        t.timestamps
      end

      add_index :llm_quota_usages, [ :account_id, :period ], unique: true, if_not_exists: true
      add_index :llm_quota_usages, :period, if_not_exists: true
    end
  end
end
