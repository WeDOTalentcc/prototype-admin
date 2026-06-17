class CreateAssessmentTables < ActiveRecord::Migration[7.1]
  def change
    create_table :big_five_questions, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.text :text, null: false
      t.text :text_en
      t.string :trait, limit: 50, null: false
      t.string :facet, limit: 50
      t.string :polarity, limit: 10, default: "positive"
      t.integer :scale_min, default: 1
      t.integer :scale_max, default: 5
      t.jsonb :scale_labels, default: {}
      t.string :category, limit: 100
      t.string :role_specific, array: true, default: []
      t.float :weight, default: 1.0
      t.boolean :is_active, default: true
      t.boolean :is_core, default: false
      t.boolean :ai_generated, default: false
      t.jsonb :validation_stats, default: {}
      t.integer :order
      t.timestamps
    end

    add_index :big_five_questions, :trait

    create_table :big_five_role_profiles, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :role_category, limit: 100
      t.string :seniority_level, limit: 50
      # Openness
      t.float :openness_min
      t.float :openness_max
      t.float :openness_ideal
      t.float :openness_weight, default: 1.0
      # Conscientiousness
      t.float :conscientiousness_min
      t.float :conscientiousness_max
      t.float :conscientiousness_ideal
      t.float :conscientiousness_weight, default: 1.0
      # Extroversion (fork uses extroversion, not extraversion)
      t.float :extroversion_min
      t.float :extroversion_max
      t.float :extroversion_ideal
      t.float :extroversion_weight, default: 1.0
      # Agreeableness
      t.float :agreeableness_min
      t.float :agreeableness_max
      t.float :agreeableness_ideal
      t.float :agreeableness_weight, default: 1.0
      # Neuroticism
      t.float :neuroticism_min
      t.float :neuroticism_max
      t.float :neuroticism_ideal
      t.float :neuroticism_weight, default: 1.0
      t.jsonb :facet_requirements, default: {}
      t.boolean :is_active, default: true
      t.boolean :is_template, default: false
      t.integer :usage_count, default: 0
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :big_five_role_profiles, :company_id

    create_table :technical_questions, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :title, limit: 500, null: false
      t.text :description
      t.string :question_type, limit: 50
      t.string :difficulty, limit: 20
      t.integer :estimated_time
      t.string :area, limit: 100
      t.string :tags, array: true, default: []
      t.jsonb :options, default: []
      t.jsonb :correct_answer, default: {}
      t.text :explanation
      t.text :code_template
      t.text :code_solution
      t.string :code_language, limit: 50
      t.jsonb :test_cases, default: []
      t.jsonb :rubric, default: {}
      t.boolean :ai_generated, default: false
      t.boolean :ai_correction_enabled, default: false
      t.boolean :is_active, default: true
      t.boolean :is_public, default: false
      t.integer :usage_count, default: 0
      t.float :avg_score
      t.float :avg_time
      t.uuid :company_id
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :technical_questions, :area
    add_index :technical_questions, :difficulty
    add_index :technical_questions, :company_id

    create_table :technical_test_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :area, limit: 100
      t.string :role_type, limit: 100
      t.string :seniority_level, limit: 50
      t.uuid :question_ids, array: true, default: []
      t.jsonb :question_config, default: {}
      t.integer :total_time
      t.float :passing_score
      t.text :instructions
      t.text :instructions_en
      t.boolean :randomize_questions, default: false
      t.boolean :randomize_options, default: false
      t.boolean :show_score, default: true
      t.boolean :proctoring_enabled, default: false
      t.boolean :webcam_required, default: false
      t.boolean :ai_correction_enabled, default: false
      t.text :ai_correction_prompt
      t.boolean :is_active, default: true
      t.boolean :is_public, default: false
      t.integer :usage_count, default: 0
      t.float :avg_score
      t.float :completion_rate
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :technical_test_templates, :company_id
    add_index :technical_test_templates, :area

    create_table :benefit_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :category, limit: 100
      t.boolean :is_popular, default: false
      t.boolean :is_active, default: true
      t.integer :order, default: 0
      t.timestamps
    end
  end
end
