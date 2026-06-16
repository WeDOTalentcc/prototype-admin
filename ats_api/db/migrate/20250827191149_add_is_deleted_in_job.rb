class AddIsDeletedInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :is_deleted, :boolean, default: false, null: false
  end
end
