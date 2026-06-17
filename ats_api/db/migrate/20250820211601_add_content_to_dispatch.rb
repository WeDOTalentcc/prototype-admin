class AddContentToDispatch < ActiveRecord::Migration[7.1]
  def change
    add_column :dispatches, :subject, :string unless column_exists?(:dispatches, :subject)
    add_column :dispatches, :body, :text unless column_exists?(:dispatches, :body)
  end
end
