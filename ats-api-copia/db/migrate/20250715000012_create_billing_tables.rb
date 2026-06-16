class CreateBillingTables < ActiveRecord::Migration[7.1]
  def change
    create_table :subscriptions, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :client_account_id, null: false
      t.string :plan_id, limit: 100
      t.string :plan_name, limit: 255
      t.string :status, limit: 50, default: "active"
      t.datetime :start_date
      t.datetime :end_date
      t.datetime :trial_end_date
      t.float :amount
      t.string :currency, limit: 10, default: "BRL"
      t.string :billing_cycle, limit: 20, default: "monthly"
      t.string :payment_provider, limit: 50
      t.string :external_subscription_id, limit: 255
      t.jsonb :features, default: {}
      t.jsonb :limits, default: {}
      t.boolean :auto_renew, default: true
      t.datetime :cancelled_at
      t.string :cancellation_reason, limit: 500
      t.timestamps
    end

    add_index :subscriptions, :client_account_id
    add_index :subscriptions, :status
    add_index :subscriptions, :external_subscription_id
    add_foreign_key :subscriptions, :client_accounts

    create_table :invoices, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :subscription_id
      t.uuid :client_account_id, null: false
      t.string :invoice_number, limit: 100
      t.string :status, limit: 50, default: "pending"
      t.float :subtotal
      t.float :tax
      t.float :total
      t.string :currency, limit: 10, default: "BRL"
      t.datetime :issue_date
      t.datetime :due_date
      t.datetime :paid_at
      t.string :payment_method, limit: 50
      t.string :pdf_url, limit: 500
      t.string :external_invoice_id, limit: 255
      t.jsonb :line_items, default: []
      t.text :notes
      t.timestamps
    end

    add_index :invoices, :subscription_id
    add_index :invoices, :client_account_id
    add_index :invoices, :status
    add_index :invoices, :invoice_number, unique: true
    add_foreign_key :invoices, :client_accounts

    create_table :payment_methods, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :client_account_id, null: false
      t.string :method_type, limit: 50
      t.string :provider, limit: 50
      t.string :last4, limit: 4
      t.string :brand, limit: 50
      t.integer :exp_month
      t.integer :exp_year
      t.string :holder_name, limit: 255
      t.string :external_id, limit: 255
      t.boolean :is_default, default: false
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :payment_methods, :client_account_id
    add_foreign_key :payment_methods, :client_accounts

    create_table :ai_consumption, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.integer :tokens_used
      t.float :cost
      t.string :provider, limit: 50
      t.string :model, limit: 100
      t.string :operation, limit: 100
      t.date :usage_date
      t.timestamps
    end

    add_index :ai_consumption, :company_id
    add_index :ai_consumption, :usage_date

    create_table :ai_credits_balance, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.integer :credits_remaining, default: 0
      t.integer :credits_monthly, default: 0
      t.integer :credits_used_this_period, default: 0
      t.datetime :reset_date
      t.datetime :last_updated_at
      t.timestamps
    end

    add_index :ai_credits_balance, :company_id, unique: true
  end
end
