class RemoveForeignKeyFromEvaluation < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :evaluations, :accounts if foreign_key_exists?(:evaluations, :accounts)
    remove_foreign_key :evaluations, :users if foreign_key_exists?(:evaluations, :users)
  end
end
