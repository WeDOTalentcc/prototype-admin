class AddParentAndChildInSelectiveProcess < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :childrens, :integer, array: true, default: [] if !column_exists?(:selective_processes, :childrens)
    add_column :selective_processes, :position_x, :integer if !column_exists?(:selective_processes, :position_x)
    add_column :selective_processes, :position_y, :integer if !column_exists?(:selective_processes, :position_y)
  end
end
