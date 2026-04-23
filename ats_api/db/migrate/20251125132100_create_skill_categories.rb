class CreateSkillCategories < ActiveRecord::Migration[7.1]
  def change
    create_table :skill_categories do |t|
      t.string :name, null: false
      t.string :description
      t.string :icon
      t.string :color
      t.boolean :is_deleted, default: false
      t.timestamps
    end unless table_exists?(:skill_categories)

    add_index :skill_categories, :name, unique: true unless index_exists?(:skill_categories, :name)
  end
end
