class CreateLlmQuotas < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :llm_quotas, if_not_exists: true do |t|
        t.references :account, null: false, foreign_key: false
        t.string :plan, null: false, default: "starter"
        t.decimal :monthly_cost_limit_usd, precision: 10, scale: 4, null: false, default: 5.0
        t.integer :monthly_request_limit
        t.integer :burst_rpm, null: false, default: 30
        t.decimal :extra_budget_usd, precision: 10, scale: 4, null: false, default: 0.0
        t.datetime :extra_budget_expires_at
        t.boolean :enabled, null: false, default: true
        t.integer :notify_at_percentage, null: false, default: 80
        t.boolean :hard_limit, null: false, default: false
        t.jsonb :metadata, null: false, default: {}

        t.timestamps
      end

      add_index :llm_quotas, :account_id, unique: true, if_not_exists: true
      add_index :llm_quotas, :plan, if_not_exists: true
      add_index :llm_quotas, :enabled, if_not_exists: true
    end
  end
end
