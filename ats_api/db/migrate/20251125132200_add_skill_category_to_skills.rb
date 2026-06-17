class AddSkillCategoryToSkills < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:skills, :skill_category_id)
      add_reference :skills, :skill_category, foreign_key: true, null: true
      add_index :skills, :skill_category_id unless index_exists?(:skills, :skill_category_id)
    end
  end
end
