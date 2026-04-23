class AddPinUserIdsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :pin_user_ids, :integer, array: true, default: []
    add_index :jobs, :pin_user_ids, using: 'gin'
  end
end
