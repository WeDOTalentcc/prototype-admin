class RemoveForeignKeyFromUserPermissions < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :user_permissions, :users if foreign_key_exists?(:user_permissions, :users)
  end
end
