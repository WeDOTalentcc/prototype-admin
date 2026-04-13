# frozen_string_literal: true

class CreateTriagemAndVoice < ActiveRecord::Migration[7.1]
  def change
    create_table :triagem_sessions, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :job_id
      t.string :channel, limit: 20, default: "web"
      t.string :status, limit: 20, default: "active"
      t.integer :current_question_idx, default: 0
      t.integer :total_questions, default: 0
      t.float :progress, default: 0.0
      t.float :final_score
      t.jsonb :scores, default: {}
      t.jsonb :session_data, default: {}
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end
    add_index :triagem_sessions, :candidate_id
    add_index :triagem_sessions, :company_id

    create_table :triagem_messages, id: :uuid do |t|
      t.references :triagem_session, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :sender, limit: 20
      t.text :content
      t.string :message_type, limit: 20, default: "text"
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    create_table :voice_screening_calls, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :job_id
      t.string :talent_pool_id
      t.string :channel, limit: 20, default: "web"
      t.string :status, limit: 20, default: "pending"
      t.string :twilio_call_sid, limit: 100
      t.integer :duration_seconds
      t.text :transcript
      t.jsonb :analysis, default: {}
      t.float :overall_score
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end
    add_index :voice_screening_calls, :candidate_id
    add_index :voice_screening_calls, :company_id

    create_table :voice_screening_analyses, id: :uuid do |t|
      t.references :voice_screening_call, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :analysis_type, limit: 30
      t.jsonb :results, default: {}
      t.float :score
      t.text :summary
      t.timestamps
    end
  end
end
