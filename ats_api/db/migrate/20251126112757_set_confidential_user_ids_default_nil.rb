class SetConfidentialUserIdsDefaultNil < ActiveRecord::Migration[7.1]
  def change
    change_column :jobs, :confidential_user_ids, :integer, array: true, default: nil, null: true
    change_column :applies, :confidential_user_ids, :integer, array: true, default: nil, null: true
    change_column :candidates, :confidential_user_ids, :integer, array: true, default: nil, null: true
  end
end
