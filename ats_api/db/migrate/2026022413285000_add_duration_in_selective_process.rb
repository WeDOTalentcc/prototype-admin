class AddDurationInSelectiveProcess < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :duration, :integer unless column_exists?(:selective_processes, :duration)
  end
end
