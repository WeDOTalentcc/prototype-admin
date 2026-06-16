class CreateIdealProfiles < ActiveRecord::Migration[7.1]
  def change
    create_table :ideal_profiles, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.uuid :department_id
      t.string :name, limit: 255
      t.text :description
      t.string :role_type, limit: 100
      t.string :seniority_level, limit: 50
      t.jsonb :technical_requirements, default: []
      t.jsonb :behavioral_requirements, default: []
      t.jsonb :experience_requirements, default: {}
      t.jsonb :education_requirements, default: {}
      t.jsonb :big_five_ideal, default: {}
      t.jsonb :evaluation_weights, default: {}
      t.string :mandatory_skills, array: true, default: []
      t.string :preferred_skills, array: true, default: []
      t.jsonb :languages, default: []
      t.float :salary_range_min
      t.float :salary_range_max
      t.jsonb :culture_fit_criteria, default: {}
      t.boolean :ai_generated, default: false
      t.datetime :ai_analysis_date
      t.float :ai_confidence
      t.boolean :validated, default: false
      t.string :validated_by, limit: 255
      t.datetime :validated_at
      t.boolean :is_active, default: true
      t.boolean :is_template, default: false
      t.integer :usage_count, default: 0
      t.float :success_rate
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :ideal_profiles, :company_id
    add_foreign_key :ideal_profiles, :company_profiles, column: :company_id
    add_foreign_key :ideal_profiles, :departments
  end
end
