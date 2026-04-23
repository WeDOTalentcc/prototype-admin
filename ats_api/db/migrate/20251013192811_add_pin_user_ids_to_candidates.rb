class AddPinUserIdsToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :pin_user_ids, :integer, array: true, default: []
    add_index :candidates, :pin_user_ids, using: 'gin'
  end
end
