# frozen_string_literal: true

class CreateComplianceTables < ActiveRecord::Migration[7.1]
  def change
    # LGPD consents (separate from candidate consent_records)
    create_table :lgpd_consents, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id                            # recruiter user
      t.string :candidate_id                       # or candidate
      t.string :consent_type, null: false, limit: 50  # data_processing, screening, communication, onboarding
      t.string :channel, limit: 20                 # web, whatsapp, email, api
      t.boolean :consented, null: false
      t.string :version, limit: 20                 # consent text version
      t.string :ip_address, limit: 45
      t.string :user_agent, limit: 500
      t.datetime :consented_at, null: false
      t.datetime :withdrawn_at
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :lgpd_consents, :company_id
    add_index :lgpd_consents, :candidate_id
    add_index :lgpd_consents, :user_id
    add_index :lgpd_consents, [:company_id, :consent_type]

    # Fairness audit log
    create_table :fairness_audit_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :action, null: false, limit: 100    # jd_enrichment, screening, evaluation, communication
      t.text :content_checked                       # what was checked
      t.string :result, limit: 20, null: false      # passed, blocked, warning
      t.jsonb :flags_found, default: []             # bias flags detected
      t.jsonb :corrections_applied, default: []     # corrections made
      t.string :agent_used, limit: 100
      t.string :session_id
      t.string :job_id
      t.string :candidate_id
      t.datetime :checked_at, null: false, default: -> { "CURRENT_TIMESTAMP" }
      t.timestamps
    end

    add_index :fairness_audit_logs, :company_id
    add_index :fairness_audit_logs, :result
    add_index :fairness_audit_logs, :checked_at
    add_index :fairness_audit_logs, [:company_id, :action]

    # Bias audit snapshots (periodic reports)
    create_table :bias_audit_snapshots, id: :uuid do |t|
      t.string :company_id, null: false
      t.date :snapshot_date, null: false
      t.string :period, limit: 20, default: "monthly"  # weekly, monthly, quarterly
      t.jsonb :metrics, default: {}                # diversity stats, bias detection rates, etc.
      t.jsonb :recommendations, default: []
      t.integer :total_evaluations, default: 0
      t.integer :flags_detected, default: 0
      t.integer :blocks_applied, default: 0
      t.float :fairness_score                      # 0-100
      t.string :generated_by, limit: 50, default: "system"
      t.timestamps
    end

    add_index :bias_audit_snapshots, :company_id
    add_index :bias_audit_snapshots, [:company_id, :snapshot_date], unique: true
  end
end
