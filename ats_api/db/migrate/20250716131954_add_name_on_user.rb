class AddNameOnUser < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :name, :string, null: true, default: nil
  end
end
