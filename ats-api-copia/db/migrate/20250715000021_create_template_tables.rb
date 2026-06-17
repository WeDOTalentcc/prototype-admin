class CreateTemplateTables < ActiveRecord::Migration[7.1]
  def change
    create_table :template_categories, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :name, limit: 255, null: false
      t.uuid :parent_id
      t.text :description
      t.integer :order, default: 0
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :template_categories, :parent_id

    create_table :job_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id
      t.uuid :parent_template_id
      t.uuid :category_id
      t.string :category, limit: 50
      t.string :subcategory, limit: 50
      t.string :title, limit: 200, null: false
      t.string :title_normalized, limit: 200
      t.string :title_alternatives, array: true, default: []
      t.string :seniority, limit: 20
      t.text :default_description
      t.text :default_responsibilities
      t.text :default_requirements
      t.text :default_nice_to_have
      t.string :default_education, array: true, default: []
      t.string :default_certifications, array: true, default: []
      t.string :default_languages, array: true, default: []
      t.jsonb :default_skills, default: []
      t.jsonb :default_behavioral, default: []
      t.integer :salary_range_min
      t.integer :salary_range_max
      t.string :salary_currency, limit: 3, default: "BRL"
      t.string :work_model, limit: 20, default: "hybrid"
      t.string :employment_type, limit: 20, default: "clt"
      t.integer :experience_years_min
      t.integer :experience_years_max
      t.boolean :is_system, default: false
      t.boolean :is_active, default: true
      t.integer :usage_count, default: 0
      t.datetime :last_used_at
      t.float :popularity_score
      t.float :quality_score
      t.jsonb :template_metadata, default: {}
      t.uuid :created_by
      t.timestamps
    end

    add_index :job_templates, :company_id
    add_index :job_templates, :category
    add_index :job_templates, :title
    add_index :job_templates, :is_system
    add_index :job_templates, :is_active

    create_table :pipeline_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id
      t.string :name, limit: 255, null: false
      t.text :description
      t.jsonb :stages, default: []
      t.boolean :is_system, default: false
      t.boolean :is_active, default: true
      t.integer :usage_count, default: 0
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :pipeline_templates, :company_id

    create_table :template_usage_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :template_id, null: false
      t.string :template_type, limit: 50
      t.string :used_by, limit: 255
      t.string :vacancy_id, limit: 255
      t.string :company_id, limit: 255
      t.datetime :created_at, null: false
    end

    add_index :template_usage_logs, :template_id
    add_index :template_usage_logs, :company_id
  end
end
