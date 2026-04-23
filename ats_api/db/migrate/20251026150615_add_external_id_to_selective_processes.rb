class AddExternalIdToSelectiveProcesses < ActiveRecord::Migration[7.1]
  def change
    add_column :selective_processes, :external_id, :string
    add_index :selective_processes, :external_id
  end
end
