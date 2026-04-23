class AddSelectiveProcessStatusInApply < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :selective_process_status, :string if !column_exists?(:applies, :selective_process_status)
  end
end
