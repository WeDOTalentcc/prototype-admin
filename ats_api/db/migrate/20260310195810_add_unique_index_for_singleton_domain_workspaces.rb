class AddUniqueIndexForSingletonDomainWorkspaces < ActiveRecord::Migration[7.1]
  def change
    add_index :workspaces, %i[user_id account_id domain],
              unique: true,
              where: "domain = 'lia_general' AND is_deleted = false",
              name: "idx_unique_lia_general_workspace"
  end
end
