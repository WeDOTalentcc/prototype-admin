class AddColorToSelectiveProcesses < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :color, :string
  end
end
