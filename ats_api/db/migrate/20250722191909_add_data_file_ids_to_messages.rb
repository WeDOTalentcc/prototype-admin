class AddDataFileIdsToMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :data_file_ids, :integer, array: true, default: []
  end
end
