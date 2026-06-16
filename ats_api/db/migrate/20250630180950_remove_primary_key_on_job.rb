class RemovePrimaryKeyOnJob < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :jobs, :users
    remove_foreign_key :jobs, :accounts
  end
end
