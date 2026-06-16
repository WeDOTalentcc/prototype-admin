class AddSourcingConfigToAccounts < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :sourcing_config, :jsonb, default: {}, null: false
    add_index :accounts, :sourcing_config, using: :gin
  end
end
