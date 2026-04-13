# frozen_string_literal: true

class CreateAlertAndBiasTables < ActiveRecord::Migration[7.1]
  def change
    create_table :alerts, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id                                # target user (NULL = all)
      t.string :alert_type, null: false, limit: 50     # sla_breach, pipeline_stale, low_candidates, high_rejection, fairness_flag
      t.string :severity, limit: 20, default: "info"   # info, warning, critical
      t.string :title, null: false, limit: 200
      t.text :message
      t.string :status, limit: 20, default: "active"   # active, acknowledged, resolved, dismissed
      t.string :context_type, limit: 50                # job, candidate, campaign, pipeline
      t.string :context_id
      t.string :action_url, limit: 500
      t.jsonb :metadata, default: {}
      t.datetime :acknowledged_at
      t.datetime :resolved_at
      t.string :resolved_by
      t.timestamps
    end

    add_index :alerts, :company_id
    add_index :alerts, [:company_id, :status]
    add_index :alerts, [:user_id, :status]
    add_index :alerts, :alert_type

    create_table :alert_rules, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.string :alert_type, null: false, limit: 50
      t.string :severity, limit: 20, default: "warning"
      t.jsonb :conditions, default: {}                 # { metric: "time_in_stage", operator: ">", value: 72 }
      t.jsonb :notification_channels, default: ["bell"]  # bell, email, whatsapp, teams
      t.boolean :is_active, default: true
      t.integer :cooldown_minutes, default: 60         # don't re-fire within N minutes
      t.datetime :last_fired_at
      t.string :created_by
      t.timestamps
    end

    add_index :alert_rules, :company_id
    add_index :alert_rules, [:company_id, :is_active]

    create_table :bias_audit_reports, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :report_type, limit: 30, default: "periodic"  # periodic, triggered, manual
      t.date :period_start
      t.date :period_end
      t.jsonb :demographics_analyzed, default: {}
      t.jsonb :findings, default: []
      t.jsonb :recommendations, default: []
      t.float :overall_fairness_score
      t.integer :total_decisions_analyzed, default: 0
      t.integer :disparities_found, default: 0
      t.string :generated_by, limit: 50, default: "system"
      t.string :reviewed_by
      t.datetime :reviewed_at
      t.timestamps
    end

    add_index :bias_audit_reports, :company_id
    add_index :bias_audit_reports, [:company_id, :period_start]
  end
end
