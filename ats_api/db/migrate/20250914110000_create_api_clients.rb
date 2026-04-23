class CreateApiClients < ActiveRecord::Migration[7.1]
  def change
    create_table :api_clients do |t|
      t.string :name, null: false
      t.string :client_id, null: false
      t.string :client_secret_hash, null: false
      t.references :account, null: false, foreign_key: true

      t.timestamps
    end

    add_index :api_clients, :client_id, unique: true
    add_index :api_clients, [ :account_id, :name ], unique: true
  end
end
