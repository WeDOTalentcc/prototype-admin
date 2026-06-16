class AddHideUserIdsToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :hide_user_ids, :integer, default: [], array: true
    add_index :candidates, :hide_user_ids, using: :gin
  end
end
