class AddColumnTenantOnAccount < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :tenant, :string
  end
end
