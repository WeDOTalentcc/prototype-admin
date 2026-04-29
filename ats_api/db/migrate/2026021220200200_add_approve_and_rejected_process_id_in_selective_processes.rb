class AddApproveAndRejectedProcessIdInSelectiveProcesses < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :approved_process_id, :integer if not column_exists?(:selective_processes, :approved_process_id)
    add_column :selective_processes, :rejected_process_id, :integer if not column_exists?(:selective_processes, :rejected_process_id)
  end
end
