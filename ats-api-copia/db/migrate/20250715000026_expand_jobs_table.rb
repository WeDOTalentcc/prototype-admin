class ExpandJobsTable < ActiveRecord::Migration[7.1]
  def change
    change_table :jobs do |t|
      # Status & classification
      t.string :status, limit: 50, default: "active"
      t.string :department, limit: 100
      t.string :employment_type, limit: 50
      t.string :seniority_level, limit: 50
      t.string :priority, limit: 20
      t.integer :urgency_level

      # Requirements (JSON)
      t.jsonb :technical_requirements, default: []
      t.jsonb :behavioral_competencies, default: []
      t.jsonb :screening_questions, default: []
      t.jsonb :interview_stages, default: []
      t.jsonb :languages, default: []

      # Salary
      t.jsonb :salary_range, default: {}
      t.jsonb :bonus_range, default: {}
      t.string :benefits, array: true, default: []

      # Deadlines
      t.datetime :deadline_screening
      t.datetime :deadline_shortlist
      t.datetime :deadline_closing

      # Team structure
      t.string :manager, limit: 255
      t.string :manager_email, limit: 255
      t.string :recruiter, limit: 255
      t.string :recruiter_email, limit: 255
      t.string :created_by, limit: 255
      t.jsonb :organizational_structure, default: {}

      # Publishing
      t.boolean :published_linkedin, default: false
      t.boolean :published_website, default: false
      t.boolean :published_indeed, default: false
      t.string :linkedin_post_id, limit: 255
      t.string :indeed_job_id, limit: 255
      t.datetime :last_published_at

      # Affirmative action
      t.boolean :is_confidential, default: false
      t.boolean :is_affirmative, default: false
      t.string :affirmative_criteria_primary, limit: 50
      t.string :affirmative_criteria_secondary, limit: 50
      t.text :affirmative_description
      t.boolean :affirmative_document_required, default: false
      t.string :affirmative_document_types, array: true, default: []

      # Visibility
      t.string :visibility, limit: 50, default: "public"
      t.string :access_list, array: true, default: []
      t.string :masked_company_name, limit: 255
      t.boolean :exclude_from_sync, default: false
      t.string :public_slug, limit: 100

      # Budget
      t.float :budget
      t.float :budget_used, default: 0

      # Approval
      t.string :approval_status, limit: 50
      t.datetime :approval_requested_at
      t.string :approval_requested_by, limit: 255
      t.string :approved_by, limit: 255
      t.datetime :approved_at
      t.text :rejection_reason

      # WhatsApp template
      t.string :whatsapp_template_type, limit: 50

      # Tags
      t.string :tags, array: true, default: []

      # Fork integration
      t.uuid :fork_uuid
    end

    add_index :jobs, :status
    add_index :jobs, :department
    add_index :jobs, :seniority_level
    add_index :jobs, :visibility
    add_index :jobs, :public_slug, unique: true, where: "public_slug IS NOT NULL"
    add_index :jobs, :fork_uuid, unique: true, where: "fork_uuid IS NOT NULL"
  end
end
