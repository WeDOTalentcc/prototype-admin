# frozen_string_literal: true

class CreateAiSuggestionsAndAdmin < ActiveRecord::Migration[7.1]
  def change
    create_table :ai_suggestions, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :suggestion_type, null: false, limit: 50  # candidate_match, jd_improvement, question, scheduling, outreach
      t.string :context_type, limit: 50                 # job, candidate, pipeline, campaign
      t.string :context_id
      t.text :suggestion_text
      t.jsonb :suggestion_data, default: {}
      t.float :confidence
      t.string :status, limit: 20, default: "pending"   # pending, accepted, rejected, expired
      t.datetime :accepted_at
      t.datetime :rejected_at
      t.text :rejection_reason
      t.timestamps
    end

    add_index :ai_suggestions, :company_id
    add_index :ai_suggestions, [:company_id, :suggestion_type]
    add_index :ai_suggestions, :status

    create_table :compliance_controls, id: :uuid do |t|
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50                     # data_protection, fairness, transparency, security
      t.string :regulation, limit: 50                   # lgpd, eu_ai_act, gdpr, sox
      t.string :severity, limit: 20, default: "medium"  # low, medium, high, critical
      t.jsonb :check_criteria, default: {}
      t.boolean :is_active, default: true
      t.boolean :is_system, default: true
      t.timestamps
    end

    add_index :compliance_controls, :category
    add_index :compliance_controls, :regulation

    create_table :compliance_health_check_items, id: :uuid do |t|
      t.string :company_id, null: false
      t.references :compliance_control, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :status, limit: 20, default: "pending"   # pending, passing, failing, not_applicable
      t.text :notes
      t.datetime :last_checked_at
      t.string :checked_by
      t.jsonb :evidence, default: {}
      t.timestamps
    end

    add_index :compliance_health_check_items, :company_id
    add_index :compliance_health_check_items, [:company_id, :status]

    create_table :admin_roles, id: :uuid do |t|
      t.string :name, null: false, limit: 100
      t.text :description
      t.jsonb :permissions, default: []
      t.boolean :is_system, default: false
      t.timestamps
    end

    add_index :admin_roles, :name, unique: true

    create_table :admin_user_roles, id: :uuid do |t|
      t.string :user_id, null: false
      t.references :admin_role, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :assigned_by
      t.timestamps
    end

    add_index :admin_user_roles, [:user_id, :admin_role_id], unique: true

    create_table :security_settings, id: :uuid do |t|
      t.string :company_id, null: false
      t.boolean :mfa_required, default: false
      t.boolean :sso_enforced, default: false
      t.integer :session_timeout_minutes, default: 480   # 8 hours
      t.integer :password_expiry_days, default: 90
      t.integer :max_login_attempts, default: 5
      t.jsonb :ip_whitelist, default: []
      t.jsonb :allowed_domains, default: []
      t.boolean :audit_logging_enabled, default: true
      t.jsonb :data_export_policy, default: {}
      t.timestamps
    end

    add_index :security_settings, :company_id, unique: true
  end
end
