class CreateCandidateFeedbackTable < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_feedbacks do |t|
      t.references :sourcing, null: true, foreign_key: true
      t.references :apply, null: true, foreign_key: true
      t.references :candidate, null: true, foreign_key: true
      t.references :user, null: false, foreign_key: false
      t.references :account, null: false, foreign_key: false
      t.references :job, null: true, foreign_key: true
      t.string :feedback_type, null: false
      t.jsonb :search_query_snapshot, default: {}
      t.jsonb :candidate_score_snapshot, default: {}
      t.boolean :is_deleted, default: false
      t.timestamps
    end

    add_index :candidate_feedbacks, :feedback_type
    add_index :candidate_feedbacks, [ :job_id, :is_deleted ]
    add_index :candidate_feedbacks, [ :account_id, :is_deleted ], name: 'idx_feedback_active'
    add_index :candidate_feedbacks, [ :sourcing_id, :is_deleted ]
    add_index :candidate_feedbacks, [ :apply_id, :is_deleted ]
    add_index :candidate_feedbacks, [ :feedback_type, :account_id, :is_deleted ]
  end
end
