class CreateEvaluationCandidate < ActiveRecord::Migration[7.1]
  def change
    create_table :evaluation_candidates do |t|
      t.string "candidate_uid"
      t.string "uid"
      t.datetime "date_expiration"
      t.datetime "date_view"
      t.boolean "completed", default: false
      t.boolean "is_deleted", default: false
      t.references "candidate", null: false, foreign_key: { to_table: :candidates }
      t.references "evaluation", null: false, foreign_key: { to_table: :evaluations }
      t.references "apply", foreign_key: { to_table: :applies }
      t.references "job", foreign_key: { to_table: :jobs }
      t.references "user", null: false, foreign_key: false
      t.references "account", null: false, foreign_key: false
      t.timestamps
    end
  end
end
