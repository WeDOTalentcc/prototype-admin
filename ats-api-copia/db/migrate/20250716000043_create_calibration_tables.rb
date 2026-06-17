# frozen_string_literal: true

class CreateCalibrationTables < ActiveRecord::Migration[7.1]
  def change
    create_table :calibration_sessions, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_id
      t.string :talent_pool_id
      t.string :created_by
      t.string :status, limit: 20, default: "active"
      t.integer :threshold, default: 3
      t.integer :approved_count, default: 0
      t.integer :rejected_count, default: 0
      t.jsonb :config, default: {}
      t.timestamps
    end
    add_index :calibration_sessions, :company_id

    create_table :calibration_feedback, id: :uuid do |t|
      t.references :calibration_session, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :candidate_id, null: false
      t.string :decision, limit: 20
      t.text :reason
      t.float :match_score
      t.jsonb :criteria, default: {}
      t.string :given_by
      t.timestamps
    end
    add_index :calibration_feedback, [:calibration_session_id, :candidate_id], unique: true, name: "idx_calib_fb_unique"

    create_table :calibration_events, id: :uuid do |t|
      t.references :calibration_session, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :event_type, limit: 30
      t.jsonb :event_data, default: {}
      t.string :triggered_by
      t.timestamps
    end

    create_table :calibration_weights, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :job_id
      t.jsonb :weights, default: {}
      t.integer :version, default: 1
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :calibration_weights, :company_id

    create_table :calibration_suggestions, id: :uuid do |t|
      t.references :calibration_session, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :suggestion_type, limit: 30
      t.text :suggestion_text
      t.jsonb :suggestion_data, default: {}
      t.float :confidence
      t.string :status, limit: 20, default: "pending"
      t.timestamps
    end
  end
end
