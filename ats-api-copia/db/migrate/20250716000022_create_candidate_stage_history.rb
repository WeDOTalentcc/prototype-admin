# frozen_string_literal: true

class CreateCandidateStageHistory < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_stage_history, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :job_vacancy_id
      t.string :company_id, null: false
      t.string :from_stage, limit: 100
      t.string :to_stage, null: false, limit: 100
      t.string :from_sub_status, limit: 100
      t.string :to_sub_status, limit: 100
      t.string :moved_by
      t.string :moved_by_type, limit: 20, default: "user"  # user, system, agent
      t.text :reason
      t.jsonb :metadata, default: {}
      t.datetime :moved_at, null: false, default: -> { "CURRENT_TIMESTAMP" }
      t.timestamps
    end

    add_index :candidate_stage_history, :candidate_id
    add_index :candidate_stage_history, :job_vacancy_id
    add_index :candidate_stage_history, :company_id
    add_index :candidate_stage_history, [:candidate_id, :job_vacancy_id]
    add_index :candidate_stage_history, :moved_at
  end
end
