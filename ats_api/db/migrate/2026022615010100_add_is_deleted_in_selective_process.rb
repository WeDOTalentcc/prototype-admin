class AddIsDeletedInSelectiveProcess < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :is_deleted, :boolean, default: false unless column_exists?(:selective_processes, :is_deleted)
  end
end
