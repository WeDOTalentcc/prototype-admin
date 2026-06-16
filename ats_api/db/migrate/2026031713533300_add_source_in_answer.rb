class AddSourceInAnswer < ActiveRecord::Migration[7.1]
  def change
    add_column :answers, :source, :string unless column_exists?(:answers, :source)
  end
end
