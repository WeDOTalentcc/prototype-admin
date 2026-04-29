class RemoveForeignKeyFromDispatch < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :dispatches, :users, column: :user_id, if_exists: true if foreign_key_exists?(:dispatches, :users, column: :user_id)
    remove_foreign_key :dispatches, :accounts, column: :account_id, if_exists: true if foreign_key_exists?(:dispatches, :accounts, column: :account_id)

    remove_foreign_key :dispatch_messages, :users, column: :user_id, if_exists: true if foreign_key_exists?(:dispatch_messages, :users, column: :user_id)
    remove_foreign_key :dispatch_messages, :accounts, column: :account_id, if_exists: true if foreign_key_exists?(:dispatch_messages, :accounts, column: :account_id)
  end
end
