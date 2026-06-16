class CreateBehavioralSkills < ActiveRecord::Migration[7.1]
  def change
    unless table_exists?(:behavioral_skills)
      create_table :behavioral_skills do |t|
        t.string :name
        t.boolean :is_deleted, default: false
        t.references :account, null: false, foreign_key: false
        t.references :skill_category, null: true
        t.index :name, unique: true
        t.timestamps
      end
    end

    unless table_exists?(:behavioral_skill_relationships)
      create_table :behavioral_skill_relationships do |t|
        t.integer :priority
        t.integer :min_value
        t.integer :max_value
        t.text :description
        t.boolean :main
        t.integer :experience_time
        t.integer :level_skill
        t.string :reference_type
        t.integer :reference_id
        t.boolean :is_deleted, default: false
        t.references :behavioral_skill, null: false, foreign_key: true
        t.references :account, null: false, foreign_key: false
        t.references :user, null: true, foreign_key: false
        t.index :min_value
        t.index :max_value
        t.index :experience_time
        t.index :level_skill
        t.index :is_deleted
        t.timestamps
      end
    end
  end
end
