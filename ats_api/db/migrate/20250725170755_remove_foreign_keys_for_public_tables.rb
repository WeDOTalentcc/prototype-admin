class RemoveForeignKeysForPublicTables < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :applies, :accounts, if_exists: true
    remove_foreign_key :candidates, :accounts, if_exists: true
    remove_foreign_key :selective_processes, :accounts, if_exists: true
    remove_foreign_key :workflow_templates, :users, if_exists: true
    remove_foreign_key :workflow_templates, :accounts, if_exists: true
  end
end
