class RemoveSourcingForeignKeys < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :sourcings, :users if foreign_key_exists?(:sourcings, :users)
    remove_foreign_key :sourcings, :accounts if foreign_key_exists?(:sourcings, :accounts)
    remove_foreign_key :sourced_profiles, :accounts if foreign_key_exists?(:sourced_profiles, :accounts)
  end
end
