class ChangeNameDeletedQuestion < ActiveRecord::Migration[7.1]
  def change
    remove_column :questions, :deleted
    add_column :questions, :is_deleted, :boolean, default: false
  end
end
