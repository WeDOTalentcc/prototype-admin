# frozen_string_literal: true

class CreateCandidateExtensions < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_jobs, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :job_id, null: false
      t.string :company_id, null: false
      t.string :status, limit: 30, default: "applied"
      t.datetime :applied_at
      t.string :source, limit: 50
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :candidate_jobs, [:candidate_id, :job_id], unique: true
    add_index :candidate_jobs, :company_id

    create_table :candidate_feedbacks, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :company_id, null: false
      t.string :job_id
      t.string :given_by
      t.string :feedback_type, limit: 30
      t.integer :rating
      t.text :comment
      t.string :stage, limit: 100
      t.jsonb :criteria_scores, default: {}
      t.timestamps
    end
    add_index :candidate_feedbacks, :candidate_id
    add_index :candidate_feedbacks, :company_id

    create_table :candidate_searches, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.text :query
      t.jsonb :filters, default: {}
      t.integer :results_count, default: 0
      t.jsonb :results_metadata, default: {}
      t.timestamps
    end
    add_index :candidate_searches, :company_id

    create_table :candidate_affirmative_documents, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :company_id, null: false
      t.string :document_type, limit: 50
      t.string :file_url, limit: 500
      t.string :file_name, limit: 200
      t.string :status, limit: 20, default: "pending"
      t.datetime :verified_at
      t.string :verified_by
      t.timestamps
    end
    add_index :candidate_affirmative_documents, :candidate_id

    create_table :viewed_candidates, id: :uuid do |t|
      t.string :user_id, null: false
      t.string :candidate_id, null: false
      t.string :company_id, null: false
      t.string :context_type, limit: 30
      t.string :context_id
      t.timestamps
    end
    add_index :viewed_candidates, [:user_id, :candidate_id]
    add_index :viewed_candidates, :company_id

    create_table :credits_usage, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :action_type, limit: 50
      t.integer :credits_used, default: 1
      t.string :candidate_id
      t.string :job_id
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :credits_usage, :company_id
    add_index :credits_usage, :created_at
  end
end
