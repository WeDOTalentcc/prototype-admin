# frozen_string_literal: true

class CreateCreditAndBillingTables < ActiveRecord::Migration[7.1]
  def change
    create_table :credit_accounts, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :account_type, limit: 30, default: "ai"  # ai, sms, whatsapp
      t.decimal :balance, precision: 12, scale: 2, default: 0
      t.decimal :monthly_allowance, precision: 12, scale: 2, default: 0
      t.decimal :used_this_period, precision: 12, scale: 2, default: 0
      t.datetime :period_reset_at
      t.boolean :auto_recharge, default: false
      t.decimal :auto_recharge_amount, precision: 12, scale: 2
      t.decimal :auto_recharge_threshold, precision: 12, scale: 2
      t.timestamps
    end

    add_index :credit_accounts, [:company_id, :account_type], unique: true

    create_table :credit_transactions, id: :uuid do |t|
      t.references :credit_account, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :transaction_type, null: false, limit: 30  # debit, credit, refund, adjustment, recharge
      t.decimal :amount, precision: 12, scale: 2, null: false
      t.decimal :balance_after, precision: 12, scale: 2
      t.string :description, limit: 500
      t.string :reference_type, limit: 50               # ai_call, whatsapp_message, sms, screening
      t.string :reference_id
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :credit_transactions, :credit_account_id
    add_index :credit_transactions, :created_at
  end
end
