class AddWorkosFieldsToAccounts < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :workos_organization_id, :string
    add_column :accounts, :workos_enabled, :boolean, default: false

    add_index :accounts, :workos_organization_id, unique: true
  end
end
