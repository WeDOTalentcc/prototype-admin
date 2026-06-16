class AddPinUserIdsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :pin_user_ids, :integer, array: true, default: []
    add_index :applies, :pin_user_ids, using: 'gin'
  end
end
