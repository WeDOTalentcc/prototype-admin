# frozen_string_literal: true

class CreateJobVacancyTables < ActiveRecord::Migration[7.1]
  def change
    create_table :job_vacancies, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_id                                 # FK to jobs table (Rails)
      t.string :title, null: false, limit: 300
      t.text :description
      t.string :status, limit: 30, default: "draft"
      t.string :seniority_level, limit: 50
      t.string :department, limit: 100
      t.string :employment_type, limit: 30
      t.string :workplace_type, limit: 30
      t.string :city, limit: 100
      t.string :state, limit: 50
      t.string :country, limit: 50, default: "Brasil"
      t.jsonb :technical_requirements, default: []
      t.jsonb :behavioral_competencies, default: []
      t.jsonb :screening_questions, default: []
      t.string :screening_mode, limit: 20
      t.float :wsi_quality_score
      t.jsonb :salary_range, default: {}
      t.jsonb :benefits, default: []
      t.string :created_by
      t.string :fork_uuid
      t.timestamps
    end
    add_index :job_vacancies, :company_id
    add_index :job_vacancies, :job_id
    add_index :job_vacancies, :status
    add_index :job_vacancies, :fork_uuid, unique: true

    create_table :job_vacancy_interview_stages, id: :uuid do |t|
      t.references :job_vacancy, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :stage_name, null: false, limit: 100
      t.integer :order, default: 0
      t.string :interview_type, limit: 50
      t.integer :duration_minutes
      t.jsonb :config, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :job_vacancy_interview_stages, [:job_vacancy_id, :order]

    create_table :job_vacancy_templates, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.text :description
      t.jsonb :template_data, default: {}
      t.boolean :is_active, default: true
      t.string :created_by
      t.timestamps
    end
    add_index :job_vacancy_templates, :company_id

    create_table :job_vacancy_audit_logs, id: :uuid do |t|
      t.references :job_vacancy, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :action, limit: 50
      t.string :changed_by
      t.jsonb :changes_made, default: {}
      t.jsonb :previous_values, default: {}
      t.timestamps
    end
    add_index :job_vacancy_audit_logs, :job_vacancy_id

    create_table :job_drafts, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :title, limit: 300
      t.jsonb :draft_data, default: {}
      t.string :status, limit: 20, default: "draft"
      t.string :source, limit: 30
      t.timestamps
    end
    add_index :job_drafts, :company_id

    create_table :draft_field_history, id: :uuid do |t|
      t.references :job_draft, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :field_name, limit: 100
      t.text :old_value
      t.text :new_value
      t.string :changed_by
      t.timestamps
    end

    create_table :job_requirements, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_vacancy_id
      t.string :requirement_type, limit: 30
      t.string :name, limit: 200
      t.text :description
      t.float :weight, default: 1.0
      t.boolean :is_mandatory, default: false
      t.integer :order, default: 0
      t.timestamps
    end
    add_index :job_requirements, :job_vacancy_id

    create_table :vacancy_candidates, id: :uuid do |t|
      t.string :job_vacancy_id, null: false
      t.string :candidate_id, null: false
      t.string :status, limit: 30, default: "applied"
      t.float :match_score
      t.float :lia_score
      t.string :current_stage, limit: 100
      t.datetime :stage_entered_at
      t.jsonb :additional_data, default: {}
      t.string :source, limit: 50
      t.timestamps
    end
    add_index :vacancy_candidates, [:job_vacancy_id, :candidate_id], unique: true, name: "idx_vacancy_cand_unique"
    add_index :vacancy_candidates, :candidate_id
  end
end
