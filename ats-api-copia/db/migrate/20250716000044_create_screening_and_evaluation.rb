# frozen_string_literal: true

class CreateScreeningAndEvaluation < ActiveRecord::Migration[7.1]
  def change
    create_table :screening_questions, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_id
      t.string :stage_id
      t.text :question, null: false
      t.string :question_type, limit: 30, default: "text"
      t.jsonb :options, default: []
      t.string :ideal_answer, limit: 500
      t.float :weight, default: 1.0
      t.string :competency, limit: 100
      t.string :framework, limit: 30
      t.integer :bloom_level
      t.integer :dreyfus_level
      t.boolean :eliminatory, default: false
      t.boolean :is_active, default: true
      t.integer :order, default: 0
      t.timestamps
    end
    add_index :screening_questions, :company_id
    add_index :screening_questions, :job_id

    create_table :screening_question_sets, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.text :description
      t.string :set_type, limit: 30
      t.jsonb :question_ids, default: []
      t.boolean :is_active, default: true
      t.string :created_by
      t.timestamps
    end
    add_index :screening_question_sets, :company_id

    create_table :screening_tasks, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :job_id
      t.string :task_type, limit: 30
      t.string :status, limit: 20, default: "pending"
      t.jsonb :questions, default: []
      t.jsonb :answers, default: []
      t.jsonb :scores, default: {}
      t.float :final_score
      t.string :channel, limit: 20
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end
    add_index :screening_tasks, :candidate_id
    add_index :screening_tasks, :company_id

    create_table :company_screening_questions, id: :uuid do |t|
      t.string :company_id, null: false
      t.text :question, null: false
      t.string :category, limit: 50
      t.boolean :is_default, default: false
      t.integer :usage_count, default: 0
      t.timestamps
    end
    add_index :company_screening_questions, :company_id

    create_table :evaluation_criteria, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50
      t.float :weight, default: 1.0
      t.jsonb :rubric, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :evaluation_criteria, :company_id

    create_table :rubric_evaluations, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :job_id
      t.string :evaluator_id
      t.jsonb :scores, default: {}
      t.float :overall_score
      t.text :notes
      t.timestamps
    end
    add_index :rubric_evaluations, :candidate_id

    create_table :technical_tests, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :template_id
      t.string :job_id
      t.string :status, limit: 20, default: "pending"
      t.datetime :started_at
      t.datetime :completed_at
      t.integer :duration_seconds
      t.float :score
      t.jsonb :answers, default: []
      t.jsonb :ai_corrections, default: {}
      t.string :proctoring_status, limit: 20
      t.timestamps
    end
    add_index :technical_tests, :candidate_id
    add_index :technical_tests, :company_id

    create_table :test_results, id: :uuid do |t|
      t.references :technical_test, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :question_id
      t.text :answer
      t.float :score
      t.text :ai_feedback
      t.boolean :is_correct
      t.timestamps
    end
  end
end
