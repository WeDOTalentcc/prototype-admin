class CreateSkillRelationship < ActiveRecord::Migration[7.1]
  def change
    create_table :skill_relationships do |t|
      t.integer "priority", default: 1, null: true
      t.integer "min_value", default: 0, null: true
      t.integer "max_value", default: 0, null: true
      t.text "description", null: true
      t.boolean "main", default: false, null: true
      t.integer "experience_time", default: 0, null: true
      t.integer "level_skill", default: 0, null: true
      t.string "reference_type", null: false
      t.integer "reference_id", null: false
      t.boolean "is_deleted", default: false, null: false
      t.references :skill, null: false, foreign_key: true
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
