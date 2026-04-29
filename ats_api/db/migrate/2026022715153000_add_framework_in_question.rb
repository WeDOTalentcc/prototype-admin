class AddFrameworkInQuestion < ActiveRecord::Migration[7.1]
  def change
    add_column :questions, :framework, :string unless column_exists?(:questions, :framework)
  end
end
