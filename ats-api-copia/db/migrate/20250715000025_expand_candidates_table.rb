class ExpandCandidatesTable < ActiveRecord::Migration[7.1]
  def change
    # Campos que só o fork tem — expandir tabela Rails existente
    change_table :candidates do |t|
      # Diversity fields (ação afirmativa)
      t.string :diversity_race_ethnicity, limit: 50
      t.boolean :diversity_disability
      t.string :diversity_disability_type, limit: 100
      t.boolean :diversity_lgbtqia
      t.boolean :diversity_refugee
      t.boolean :diversity_age_50_plus
      t.boolean :diversity_indigenous
      t.jsonb :diversity_documents, default: {}
      t.datetime :diversity_self_declared_at
      t.datetime :diversity_document_deadline

      # Professional
      t.string :seniority_level, limit: 50
      t.integer :years_of_experience
      t.string :technical_skills, array: true, default: []
      t.string :soft_skills, array: true, default: []
      t.jsonb :languages, default: []
      t.string :certifications, array: true, default: []

      # External IDs for fork integration
      t.uuid :fork_uuid  # UUID from the fork system
    end

    add_index :candidates, :fork_uuid, unique: true, where: "fork_uuid IS NOT NULL"
    add_index :candidates, :seniority_level

    # Candidate experiences (nova tabela)
    create_table :candidate_experiences, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.bigint :candidate_id, null: false
      t.string :company_name, limit: 255, null: false
      t.string :company_linkedin_url, limit: 500
      t.string :company_domain, limit: 255
      t.string :title, limit: 255
      t.string :start_date, limit: 50
      t.string :end_date, limit: 50
      t.float :duration_years
      t.boolean :is_current, default: false
      t.text :description
      t.string :location, limit: 255
      t.string :industries, array: true, default: []
      t.string :company_size, limit: 50
      t.string :company_size_range, limit: 50
      t.string :technologies, array: true, default: []
      t.boolean :is_startup, default: false
      t.integer :company_founded_year
      t.float :company_annual_revenue
      t.string :funding_stage, limit: 50
      t.string :company_tags, array: true, default: []
      t.string :company_hq_city, limit: 100
      t.string :company_hq_state, limit: 100
      t.string :company_hq_country, limit: 100
      t.integer :sequence_order
      t.timestamps
    end

    add_index :candidate_experiences, :candidate_id
    add_index :candidate_experiences, :company_name
    add_foreign_key :candidate_experiences, :candidates

    # Candidate education (nova tabela)
    create_table :candidate_education, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.bigint :candidate_id, null: false
      t.string :institution, limit: 255, null: false
      t.string :degree, limit: 100
      t.string :field_of_study, limit: 255
      t.string :start_date, limit: 50
      t.string :end_date, limit: 50
      t.boolean :is_completed, default: false
      t.text :description
      t.string :gpa, limit: 20
      t.string :location, limit: 255
      t.string :institution_city, limit: 100
      t.string :institution_state, limit: 100
      t.string :institution_country, limit: 100
      t.integer :institution_ranking
      t.string :institution_tier, limit: 50
      t.integer :sequence_order
      t.timestamps
    end

    add_index :candidate_education, :candidate_id
    add_index :candidate_education, :institution
    add_foreign_key :candidate_education, :candidates

    # Candidate attachments (nova tabela)
    create_table :candidate_attachments, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.bigint :candidate_id, null: false
      t.string :file_name, limit: 255
      t.string :file_type, limit: 50
      t.string :file_url, limit: 1000
      t.integer :file_size
      t.string :category, limit: 50
      t.string :uploaded_by, limit: 255
      t.timestamps
    end

    add_index :candidate_attachments, :candidate_id
    add_foreign_key :candidate_attachments, :candidates
  end
end
