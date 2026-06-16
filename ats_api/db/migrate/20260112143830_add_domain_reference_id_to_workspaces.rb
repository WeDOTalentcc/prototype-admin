class AddDomainReferenceIdToWorkspaces < ActiveRecord::Migration[7.1]
  def change
    remove_index :workspaces, name: "index_workspaces_on_user_account_domain_unique", if_exists: true
    add_column :workspaces, :domain_reference_id, :bigint
    add_index :workspaces, [ :user_id, :account_id, :domain, :domain_reference_id ],
              unique: true,
              where: "domain IS NOT NULL AND is_deleted = false",
              name: "index_workspaces_on_user_domain_reference_unique"
  end
end
