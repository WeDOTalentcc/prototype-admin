class AddContentToDispatchMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :dispatch_messages, :subject, :string unless column_exists?(:dispatch_messages, :subject)
    add_column :dispatch_messages, :body, :text     unless column_exists?(:dispatch_messages, :body)
  end
end
