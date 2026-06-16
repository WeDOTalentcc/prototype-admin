class AddExternalIdToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :external_id, :string
    add_index :candidates, :external_id
  end
end
