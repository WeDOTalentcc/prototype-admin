class RemoveForeignKeyFromMessage < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :messages, :users if foreign_key_exists?(:messages, :users)
    remove_foreign_key :messages, :accounts if foreign_key_exists?(:messages, :accounts)
  end
end
