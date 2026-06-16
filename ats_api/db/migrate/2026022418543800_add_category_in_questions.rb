class AddCategoryInQuestions < ActiveRecord::Migration[7.1]
  def change
    add_column :questions, :category, :string, default: nil, null: true unless column_exists?(:questions, :category)
  end
end
