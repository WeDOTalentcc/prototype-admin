class AddCostPerProfileToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :cost_per_profile, :float
  end
end
