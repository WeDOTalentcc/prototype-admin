class ChangeMessage < ActiveRecord::Migration[7.1]
  def change
    change_column :messages, :content, :text
    add_column :messages, :metadata, :jsonb, default: {}
    add_index :messages, :parent_message_id
  end
end
