class CreateLlmUsages < ActiveRecord::Migration[7.1]
  def change
    create_table :llm_usages do |t|
      t.references :user, null: false, foreign_key: false
      t.references :account, null: false, foreign_key: false
      t.string :model, null: false
      t.string :operation, null: false
      t.integer :input_tokens, null: false, default: 0
      t.integer :output_tokens, null: false, default: 0
      t.integer :total_tokens, null: false, default: 0
      t.decimal :cost_usd, precision: 12, scale: 8, null: false, default: 0.0
      t.decimal :latency_ms, precision: 10, scale: 2, null: false, default: 0.0
      t.boolean :success, null: false, default: true
      t.text :error_message
      t.jsonb :context, default: {}

      t.timestamps
    end

    add_index :llm_usages, :model
    add_index :llm_usages, :operation
    add_index :llm_usages, :success
    add_index :llm_usages, [ :account_id, :created_at ]
    add_index :llm_usages, [ :user_id, :created_at ]
    add_index :llm_usages, :created_at
    add_index :llm_usages, :context, using: :gin
  end
end
