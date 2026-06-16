class AddDomainToWorkspaces < ActiveRecord::Migration[7.1]
  def change
    add_column :workspaces, :domain, :string
    add_index :workspaces, [ :user_id, :account_id, :domain ], unique: true, where: "domain IS NOT NULL AND is_deleted = false", name: "index_workspaces_on_user_account_domain_unique"
  end
end
