# frozen_string_literal: true

class CreateInterviewSessions < ActiveRecord::Migration[7.1]
  def change
    create_table :interview_sessions do |t|
      t.string     :token,                  null: false
      t.string     :status,                 null: false, default: "pending"
      t.references :account,                null: false, foreign_key: true
      t.references :evaluation,             null: false, foreign_key: true
      t.references :evaluation_candidate,   foreign_key: true
      t.references :apply,                  foreign_key: true
      t.references :candidate,              null: false, foreign_key: true
      t.references :job,                    null: false, foreign_key: true
      t.references :created_by,             foreign_key: { to_table: :users }

      t.string     :interview_type,         default: "voice"
      t.integer    :duration_minutes,       default: 30
      t.string     :language,               default: "pt-BR"
      t.jsonb      :questions_snapshot,      default: []
      t.jsonb      :job_context,            default: {}
      t.jsonb      :candidate_context,      default: {}

      t.jsonb      :transcript,             default: []
      t.jsonb      :report,                 default: {}
      t.float      :score
      t.string     :recommendation

      t.datetime   :started_at
      t.datetime   :completed_at
      t.datetime   :expires_at

      t.timestamps
    end

    add_index :interview_sessions, :token, unique: true
    add_index :interview_sessions, :status
    add_index :interview_sessions, %i[account_id candidate_id job_id]
  end
end
