class AddColorAndDescriptionInList < ActiveRecord::Migration[7.1]
  def change
    add_column :lists, :color, :string if !column_exists?(:lists, :color)
    add_column :lists, :description, :text if !column_exists?(:lists, :description)
    remove_foreign_key :lists, :accounts if foreign_key_exists?(:lists, :accounts)
    remove_foreign_key :lists, :users if foreign_key_exists?(:lists, :users)
    remove_foreign_key :list_relationships, :accounts if foreign_key_exists?(:list_relationships, :accounts)
    remove_foreign_key :list_relationships, :users if foreign_key_exists?(:list_relationships, :users)
  end
end
