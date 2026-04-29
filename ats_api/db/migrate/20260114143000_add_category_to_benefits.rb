class AddCategoryToBenefits < ActiveRecord::Migration[7.1]
  def change
    add_column :benefits, :category, :string
    add_index :benefits, :category
  end
end
