class AddCostCenterToDepartments < ActiveRecord::Migration[7.1]
  def change
    add_column :departments, :cost_center, :string unless column_exists?(:departments, :cost_center)
  end
end
