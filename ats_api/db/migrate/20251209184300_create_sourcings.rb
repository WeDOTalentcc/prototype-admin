class CreateSourcings < ActiveRecord::Migration[7.0]
  def change
    create_table :sourcings do |t|
      t.references :user, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true


      t.string :uid, null: false
      t.string :provider, default: 'pearch'
      t.string :external_id
      t.string :thread_id

      t.string :query, null: false
      t.jsonb :parameters, default: {}

      t.string :status
      t.float :duration
      t.integer :total_estimate
      t.boolean :total_estimate_is_lower_bound, default: false
      t.integer :results_count, default: 0

      t.integer :credits_used
      t.integer :credits_remaining

      t.datetime :searched_at
      t.text :notes
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :sourcings, :uid, unique: true
    add_index :sourcings, :external_id
    add_index :sourcings, :provider
    add_index :sourcings, :query
    add_index :sourcings, :status
    add_index :sourcings, :searched_at
    add_index :sourcings, [ :account_id, :created_at ]
    add_index :sourcings, [ :account_id, :is_deleted ]
  end
end
