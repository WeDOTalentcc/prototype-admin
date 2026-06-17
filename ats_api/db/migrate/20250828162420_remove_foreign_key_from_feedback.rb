class RemoveForeignKeyFromFeedback < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :feedbacks, :accounts if foreign_key_exists?(:feedbacks, :accounts)
    remove_foreign_key :dispatches, :accounts if foreign_key_exists?(:dispatches, :accounts)
    remove_foreign_key :dispatches, :users if foreign_key_exists?(:dispatches, :users)
  end
end
