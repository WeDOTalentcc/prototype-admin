# frozen_string_literal: true

class CreateLowPriorityTables < ActiveRecord::Migration[7.1]
  def change
    # Candidate extensions
    create_table :candidate_hidden, id: :uuid do |t|
      t.string :user_id, null: false
      t.string :candidate_id, null: false
      t.string :company_id, null: false
      t.text :reason
      t.timestamps
    end
    add_index :candidate_hidden, [:user_id, :candidate_id], unique: true

    create_table :candidate_merge_audit, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :primary_candidate_id, null: false
      t.string :merged_candidate_id, null: false
      t.string :merged_by
      t.jsonb :fields_merged, default: {}
      t.jsonb :conflicts_resolved, default: {}
      t.timestamps
    end
    add_index :candidate_merge_audit, :company_id

    # Company extensions
    create_table :company_benefits, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50
      t.boolean :is_active, default: true
      t.integer :order, default: 0
      t.timestamps
    end
    add_index :company_benefits, :company_id

    create_table :company_culture_profiles, id: :uuid do |t|
      t.string :company_id, null: false
      t.jsonb :culture_dimensions, default: {}
      t.jsonb :work_environment, default: {}
      t.jsonb :leadership_style, default: {}
      t.jsonb :communication_style, default: {}
      t.float :overall_score
      t.datetime :last_analyzed_at
      t.string :analyzed_by, limit: 50, default: "system"
      t.timestamps
    end
    add_index :company_culture_profiles, :company_id, unique: true

    create_table :company_responsibilities, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :role_title, limit: 200
      t.string :seniority, limit: 50
      t.jsonb :responsibilities, default: []
      t.integer :frequency, default: 0
      t.string :source, limit: 30, default: "learned"
      t.timestamps
    end
    add_index :company_responsibilities, :company_id

    create_table :company_patterns, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :pattern_type, limit: 50
      t.jsonb :pattern_data, default: {}
      t.float :confidence
      t.integer :occurrences, default: 0
      t.datetime :last_seen_at
      t.timestamps
    end
    add_index :company_patterns, :company_id

    # Templates
    create_table :default_templates, id: :uuid do |t|
      t.string :template_type, null: false, limit: 50
      t.string :name, null: false, limit: 200
      t.text :content
      t.jsonb :template_data, default: {}
      t.string :locale, limit: 5, default: "pt-BR"
      t.boolean :is_active, default: true
      t.integer :order, default: 0
      t.timestamps
    end
    add_index :default_templates, [:template_type, :locale]

    # Teams extensions
    create_table :teams_notifications, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :notification_type, limit: 50
      t.text :message
      t.string :teams_message_id, limit: 200
      t.string :status, limit: 20, default: "sent"
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :teams_notifications, :company_id

    create_table :teams_action_audit_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :action, limit: 100
      t.string :context_type, limit: 50
      t.string :context_id
      t.jsonb :action_data, default: {}
      t.timestamps
    end
    add_index :teams_action_audit_logs, :company_id

    # SOX compliance
    create_table :sox_audit_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :control_id
      t.string :action, limit: 100
      t.string :performed_by
      t.jsonb :evidence, default: {}
      t.string :result, limit: 20
      t.timestamps
    end
    add_index :sox_audit_logs, :company_id

    create_table :sox_controls, id: :uuid do |t|
      t.string :control_id, null: false, limit: 50
      t.string :name, limit: 200
      t.text :description
      t.string :category, limit: 50
      t.string :frequency, limit: 20
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :sox_controls, :control_id, unique: true

    # Compliance extensions
    create_table :compliance_health_check_history, id: :uuid do |t|
      t.references :compliance_health_check_item, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :previous_status, limit: 20
      t.string :new_status, limit: 20
      t.string :changed_by
      t.text :notes
      t.timestamps
    end

    # Alert extensions
    create_table :alert_configs, id: :uuid do |t|
      t.string :company_id, null: false
      t.boolean :email_alerts, default: true
      t.boolean :whatsapp_alerts, default: false
      t.boolean :teams_alerts, default: false
      t.boolean :in_app_alerts, default: true
      t.jsonb :quiet_hours, default: {}
      t.string :timezone, limit: 50, default: "America/Sao_Paulo"
      t.timestamps
    end
    add_index :alert_configs, :company_id, unique: true

    create_table :alert_preferences, id: :uuid do |t|
      t.string :user_id, null: false
      t.string :company_id, null: false
      t.string :alert_type, limit: 50
      t.boolean :enabled, default: true
      t.jsonb :channels, default: ["bell"]
      t.timestamps
    end
    add_index :alert_preferences, [:user_id, :alert_type], unique: true

    # SaaS metrics
    create_table :client_saas_metrics, id: :uuid do |t|
      t.string :company_id, null: false
      t.date :period_date, null: false
      t.string :period_type, limit: 10, default: "monthly"
      t.integer :active_users, default: 0
      t.integer :jobs_created, default: 0
      t.integer :candidates_screened, default: 0
      t.integer :interviews_scheduled, default: 0
      t.integer :hires_made, default: 0
      t.float :avg_time_to_hire_days
      t.float :avg_cost_per_hire
      t.jsonb :feature_usage, default: {}
      t.timestamps
    end
    add_index :client_saas_metrics, [:company_id, :period_date], unique: true

    create_table :client_usage_metrics, id: :uuid do |t|
      t.string :company_id, null: false
      t.date :usage_date, null: false
      t.integer :api_calls, default: 0
      t.integer :ai_tokens_used, default: 0
      t.integer :emails_sent, default: 0
      t.integer :whatsapp_messages, default: 0
      t.integer :searches_performed, default: 0
      t.integer :reports_generated, default: 0
      t.jsonb :breakdown, default: {}
      t.timestamps
    end
    add_index :client_usage_metrics, [:company_id, :usage_date], unique: true

    create_table :client_health_metrics, id: :uuid do |t|
      t.string :company_id, null: false
      t.date :calculated_at, null: false
      t.float :health_score                           # 0-100
      t.float :adoption_score
      t.float :engagement_score
      t.float :satisfaction_score
      t.string :risk_level, limit: 20, default: "low" # low, medium, high, critical
      t.jsonb :signals, default: {}
      t.jsonb :recommendations, default: []
      t.timestamps
    end
    add_index :client_health_metrics, [:company_id, :calculated_at]

    create_table :payment_history, id: :uuid do |t|
      t.string :company_id, null: false
      t.references :invoice, type: :uuid, foreign_key: { on_delete: :nullify }
      t.decimal :amount, precision: 12, scale: 2, null: false
      t.string :currency, limit: 3, default: "BRL"
      t.string :status, limit: 20, default: "completed"
      t.string :payment_method, limit: 50
      t.string :external_transaction_id, limit: 200
      t.datetime :paid_at
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :payment_history, :company_id
    add_index :payment_history, :paid_at
  end
end
