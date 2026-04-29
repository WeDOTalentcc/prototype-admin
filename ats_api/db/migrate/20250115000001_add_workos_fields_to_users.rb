class AddWorkosFieldsToUsers < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :workos_user_id, :string
    add_column :users, :workos_organization_id, :string
    add_column :users, :workos_access_token, :text
    add_column :users, :workos_refresh_token, :text
    add_column :users, :workos_expires_at, :datetime

    add_index :users, :workos_user_id, unique: true
    add_index :users, :workos_organization_id
  end
end
