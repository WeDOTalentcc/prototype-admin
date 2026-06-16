class AddUserContextIdInMessage < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :user_context_id, :integer, null: true
    add_index :messages, :user_context_id
  end
end
