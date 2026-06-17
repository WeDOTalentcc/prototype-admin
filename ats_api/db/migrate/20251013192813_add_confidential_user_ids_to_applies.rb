class AddConfidentialUserIdsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :confidential_user_ids, :integer, array: true, default: []
    add_index :applies, :confidential_user_ids, using: 'gin'
  end
end
