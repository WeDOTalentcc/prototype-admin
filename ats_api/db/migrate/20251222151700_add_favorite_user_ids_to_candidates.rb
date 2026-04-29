class AddFavoriteUserIdsToCandidates < ActiveRecord::Migration[7.0]
  def change
    add_column :candidates, :favorite_user_ids, :integer, array: true, default: []
  end
end
