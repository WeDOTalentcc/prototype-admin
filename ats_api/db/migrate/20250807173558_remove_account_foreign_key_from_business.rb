class RemoveAccountForeignKeyFromBusiness < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :businesses, :accounts if foreign_key_exists?(:businesses, :accounts)
  end
end
