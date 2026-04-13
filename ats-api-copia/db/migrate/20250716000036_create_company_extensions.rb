# frozen_string_literal: true

class CreateCompanyExtensions < ActiveRecord::Migration[7.1]
  def change
    create_table :department_members, id: :uuid do |t|
      t.references :department, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :user_id, null: false
      t.string :role, limit: 50, default: "member"     # member, manager, lead
      t.boolean :is_primary, default: false
      t.timestamps
    end

    add_index :department_members, [:department_id, :user_id], unique: true

    create_table :company_skills, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :skill_name, null: false, limit: 200
      t.string :category, limit: 50                    # technical, behavioral, language, tool
      t.integer :frequency, default: 0                 # how often used in JDs
      t.float :relevance_score                         # learned relevance
      t.jsonb :synonyms, default: []
      t.jsonb :related_skills, default: []
      t.boolean :is_verified, default: false
      t.string :source, limit: 30, default: "learned"  # learned, manual, import
      t.timestamps
    end

    add_index :company_skills, :company_id
    add_index :company_skills, [:company_id, :skill_name], unique: true

    create_table :global_search_settings, id: :uuid do |t|
      t.string :company_id, null: false
      t.boolean :semantic_search_enabled, default: true
      t.boolean :fuzzy_matching_enabled, default: true
      t.float :minimum_match_score, default: 0.5
      t.jsonb :boost_fields, default: {}               # {skills: 2.0, title: 1.5, experience: 1.0}
      t.jsonb :excluded_fields, default: []
      t.string :default_sort, limit: 50, default: "relevance"
      t.integer :results_per_page, default: 20
      t.jsonb :filters_config, default: {}
      t.timestamps
    end

    add_index :global_search_settings, :company_id, unique: true
  end
end
