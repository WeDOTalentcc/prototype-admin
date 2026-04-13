class CreateAuditTables < ActiveRecord::Migration[7.1]
  def change
    create_table :audit_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255
      t.string :agent_name, limit: 255
      t.string :decision_type, limit: 100
      t.string :action, limit: 255
      t.string :candidate_id, limit: 255
      t.string :job_vacancy_id, limit: 255
      t.string :decision, limit: 100
      t.float :score
      t.float :confidence
      t.jsonb :reasoning, default: {}
      t.jsonb :criteria_used, default: {}
      t.jsonb :criteria_ignored, default: {}
      t.boolean :human_review_required, default: false
      t.string :human_reviewed_by, limit: 255
      t.datetime :human_reviewed_at
      t.string :human_override, limit: 255
      t.string :session_id, limit: 255
      t.string :agent_used, limit: 255
      t.text :input_text
      t.text :output_text
      t.jsonb :fairness_flags, default: {}
      t.datetime :retention_until
      t.datetime :created_at, null: false
    end

    add_index :audit_logs, :company_id
    add_index :audit_logs, :agent_name
    add_index :audit_logs, :decision_type
    add_index :audit_logs, :candidate_id
    add_index :audit_logs, :job_vacancy_id
    add_index :audit_logs, :session_id
    add_index :audit_logs, :created_at

    create_table :audit_retention_policies, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :log_type, limit: 100, null: false
      t.integer :retention_days, null: false
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :audit_retention_policies, :company_id

    create_table :admin_audit_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :admin_user_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.string :action, limit: 255, null: false
      t.string :target_type, limit: 100
      t.string :target_id, limit: 255
      t.jsonb :changes, default: {}
      t.string :ip_address, limit: 50
      t.string :user_agent, limit: 500
      t.datetime :created_at, null: false
    end

    add_index :admin_audit_logs, :admin_user_id
    add_index :admin_audit_logs, :company_id
    add_index :admin_audit_logs, :created_at
  end
end
