class AddIsAdminInUser < ActiveRecord::Migration[7.1]
  def change
    if !column_exists?(:users, :is_admin)
      add_column :users, :is_admin, :boolean, default: false, null: false
    end
  end
end
