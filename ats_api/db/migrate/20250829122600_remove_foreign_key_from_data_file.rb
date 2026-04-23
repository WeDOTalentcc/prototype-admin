class RemoveForeignKeyFromDataFile < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :data_files, :accounts if foreign_key_exists?(:data_files, :accounts)
    remove_foreign_key :data_files, :users if foreign_key_exists?(:data_files, :users)
  end
end
