class CreateBenefits < ActiveRecord::Migration[7.1]
  def change
    create_table :benefits do |t|
      t.string :name, null: false
      t.boolean :is_deleted, default: false
      t.boolean :is_possible_extend_to_dependents, default: false, null: false
      t.boolean :is_per_day, default: false, null: false
      t.integer :days_of_month, default: 0, null: false
      t.boolean :enable_value_editing, default: true, null: false
      t.string :types, array: true, default: []
      t.timestamps
    end unless table_exists?(:benefits)

    add_index :benefits, :types, using: :gin unless index_exists?(:benefits, :types)
  end
end
