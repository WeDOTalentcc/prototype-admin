class CreateLgpdConsentTables < ActiveRecord::Migration[7.1]
  def change
    create_table :consent_records, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :candidate_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.string :consent_type, limit: 100, null: false
      t.string :status, limit: 50, default: "given"
      t.integer :version, default: 1
      t.datetime :given_at
      t.datetime :withdrawn_at
      t.datetime :expires_at
      t.string :ip_address, limit: 50
      t.string :user_agent, limit: 500
      t.string :source, limit: 100
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :consent_records, :candidate_id
    add_index :consent_records, :company_id
    add_index :consent_records, :consent_type
    add_index :consent_records, :status

    create_table :consent_versions, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :consent_type, limit: 100, null: false
      t.integer :version, null: false
      t.text :text_pt
      t.text :text_en
      t.boolean :is_active, default: true
      t.datetime :effective_from
      t.datetime :effective_until
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :consent_versions, [:consent_type, :version], unique: true

    create_table :consent_events, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :consent_id, null: false
      t.string :event_type, limit: 50, null: false
      t.jsonb :metadata, default: {}
      t.string :ip_address, limit: 50
      t.timestamps
    end

    add_index :consent_events, :consent_id
    add_foreign_key :consent_events, :consent_records, column: :consent_id

    create_table :data_subject_requests, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :candidate_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.string :request_type, limit: 50, null: false
      t.string :status, limit: 50, default: "pending"
      t.text :description
      t.datetime :deadline
      t.datetime :completed_at
      t.string :completed_by, limit: 255
      t.text :response_notes
      t.jsonb :request_data, default: {}
      t.jsonb :response_data, default: {}
      t.timestamps
    end

    add_index :data_subject_requests, :candidate_id
    add_index :data_subject_requests, :company_id
    add_index :data_subject_requests, :status

    create_table :automated_decision_explanations, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :candidate_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.string :decision_type, limit: 100
      t.string :decision, limit: 100
      t.text :explanation
      t.float :score
      t.float :confidence
      t.jsonb :factors, default: []
      t.jsonb :criteria_used, default: {}
      t.boolean :human_review_required, default: false
      t.string :reviewed_by, limit: 255
      t.datetime :reviewed_at
      t.timestamps
    end

    add_index :automated_decision_explanations, :candidate_id
    add_index :automated_decision_explanations, :company_id

    create_table :company_retention_policies, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :data_type, limit: 100, null: false
      t.integer :retention_days, null: false
      t.string :action, limit: 50, default: "anonymize"
      t.boolean :is_active, default: true
      t.text :description
      t.timestamps
    end

    add_index :company_retention_policies, :company_id
    add_index :company_retention_policies, [:company_id, :data_type], unique: true
  end
end
