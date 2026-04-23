class AddBigFiveFieldsInBusiness < ActiveRecord::Migration[7.1]
  def change
    add_column :businesses, :openness, :integer, null: true if not column_exists?(:businesses, :openness)
    add_column :businesses, :conscientiousness, :integer, null: true if not column_exists?(:businesses, :conscientiousness)
    add_column :businesses, :extraversion, :integer, null: true if not column_exists?(:businesses, :extraversion)
    add_column :businesses, :agreeableness, :integer, null: true if not column_exists?(:businesses, :agreeableness)
    add_column :businesses, :stability, :integer, null: true if not column_exists?(:businesses, :stability)
  end
end
