class AddConfidentialUserIdsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :confidential_user_ids, :integer, array: true, default: []
    add_index :jobs, :confidential_user_ids, using: 'gin'
  end
end
