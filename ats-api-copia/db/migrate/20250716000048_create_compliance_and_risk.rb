# frozen_string_literal: true

class CreateComplianceAndRisk < ActiveRecord::Migration[7.1]
  def change
    create_table :affirmative_audit_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id
      t.string :job_id
      t.string :action, limit: 50
      t.jsonb :details, default: {}
      t.string :performed_by
      t.timestamps
    end
    add_index :affirmative_audit_logs, :company_id

    create_table :compliance_audits, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :audit_type, limit: 50
      t.date :period_start
      t.date :period_end
      t.string :status, limit: 20, default: "in_progress"
      t.jsonb :findings, default: []
      t.jsonb :recommendations, default: []
      t.string :auditor
      t.datetime :completed_at
      t.timestamps
    end
    add_index :compliance_audits, :company_id

    create_table :compliance_control_library, id: :uuid do |t|
      t.string :code, null: false, limit: 50
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :framework, limit: 50
      t.string :category, limit: 50
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :compliance_control_library, :code, unique: true

    create_table :company_compliance_controls, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :control_code, limit: 50
      t.string :status, limit: 20, default: "not_started"
      t.string :responsible
      t.text :notes
      t.datetime :last_reviewed_at
      t.timestamps
    end
    add_index :company_compliance_controls, :company_id

    create_table :incident_reports, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :incident_type, limit: 50
      t.string :severity, limit: 20
      t.text :description
      t.string :reported_by
      t.string :status, limit: 20, default: "open"
      t.jsonb :timeline, default: []
      t.datetime :resolved_at
      t.timestamps
    end
    add_index :incident_reports, :company_id

    create_table :breach_notifications, id: :uuid do |t|
      t.string :company_id, null: false
      t.references :incident_report, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :notification_type, limit: 30
      t.string :recipient, limit: 200
      t.text :content
      t.datetime :sent_at
      t.string :status, limit: 20, default: "pending"
      t.timestamps
    end

    create_table :dpo_registry, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.string :email, limit: 200
      t.string :phone, limit: 20
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :dpo_registry, :company_id

    create_table :risk_entries, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :title, limit: 200
      t.text :description
      t.string :category, limit: 50
      t.string :likelihood, limit: 20
      t.string :impact, limit: 20
      t.string :risk_level, limit: 20
      t.string :status, limit: 20, default: "identified"
      t.string :owner
      t.timestamps
    end
    add_index :risk_entries, :company_id

    create_table :risk_treatments, id: :uuid do |t|
      t.references :risk_entry, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :treatment_type, limit: 30
      t.text :description
      t.string :status, limit: 20, default: "planned"
      t.string :responsible
      t.datetime :due_date
      t.timestamps
    end

    create_table :sod_roles, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :role_name, null: false, limit: 100
      t.text :description
      t.jsonb :permissions, default: []
      t.timestamps
    end
    add_index :sod_roles, :company_id

    create_table :sod_conflicts, id: :uuid do |t|
      t.string :role_a, limit: 100
      t.string :role_b, limit: 100
      t.text :reason
      t.string :severity, limit: 20
      t.boolean :is_active, default: true
      t.timestamps
    end

    create_table :sod_violations, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :role_a, limit: 100
      t.string :role_b, limit: 100
      t.string :status, limit: 20, default: "detected"
      t.text :resolution
      t.string :resolved_by
      t.datetime :resolved_at
      t.timestamps
    end
    add_index :sod_violations, :company_id
  end
end
