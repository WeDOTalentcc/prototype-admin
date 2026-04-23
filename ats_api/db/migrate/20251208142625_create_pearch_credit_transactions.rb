class CreatePearchCreditTransactions < ActiveRecord::Migration[7.1]
  def change
    create_table :pearch_credit_transactions do |t|
      t.references :account, null: false, foreign_key: true, index: true
      t.string :transaction_type, null: false
      t.integer :amount, null: false
      t.integer :balance_before, null: false
      t.integer :balance_after, null: false
      t.text :reason
      t.jsonb :metadata, default: {}
      t.string :reference_id
      t.string :reference_type

      t.timestamps
    end

    add_index :pearch_credit_transactions, :transaction_type
    add_index :pearch_credit_transactions, :created_at
    add_index :pearch_credit_transactions, [ :account_id, :created_at ]
    add_index :pearch_credit_transactions, [ :reference_type, :reference_id ]
  end
end
