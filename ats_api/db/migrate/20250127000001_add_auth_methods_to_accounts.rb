class AddAuthMethodsToAccounts < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :auth_config, :jsonb, default: {}, null: false

    add_index :accounts, :auth_config, using: :gin
  end
end
