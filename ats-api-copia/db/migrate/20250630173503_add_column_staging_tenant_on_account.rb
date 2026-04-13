class AddColumnStagingTenantOnAccount < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :staging_tenant, :string

    add_index :accounts, :tenant
    add_index :accounts, :staging_tenant
  end
end
