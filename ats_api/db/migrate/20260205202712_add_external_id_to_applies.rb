class AddExternalIdToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :external_id, :string
  end
end
