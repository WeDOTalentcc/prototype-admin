class AddIsDeletedInCandidate < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :is_deleted, :boolean, default: false
  end
end
