class RemoveAccountForeignKeyFromApplyStatus < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :apply_statuses, :accounts if foreign_key_exists?(:apply_statuses, :accounts)
    remove_foreign_key :apply_statuses, :users if foreign_key_exists?(:apply_statuses, :users)
  end
end
