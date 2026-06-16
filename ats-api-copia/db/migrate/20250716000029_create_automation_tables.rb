# frozen_string_literal: true

class CreateAutomationTables < ActiveRecord::Migration[7.1]
  def change
    create_table :stage_automation_rules, id: :uuid do |t|
      t.string :company_id, null: false
      t.references :recruitment_stage, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :name, limit: 200
      t.string :trigger_type, null: false, limit: 50  # stage_enter, stage_exit, time_in_stage, score_threshold
      t.string :action_type, null: false, limit: 50   # advance_stage, send_email, send_whatsapp, create_task, notify
      t.jsonb :conditions, default: {}
      t.jsonb :action_config, default: {}
      t.boolean :is_active, default: true
      t.integer :execution_count, default: 0
      t.datetime :last_executed_at
      t.string :created_by
      t.timestamps
    end

    add_index :stage_automation_rules, :company_id
    add_index :stage_automation_rules, [:company_id, :is_active]

    create_table :automation_execution_logs, id: :uuid do |t|
      t.string :rule_id                            # stage_automation_rule or recruitment_automation
      t.string :rule_type, limit: 50               # stage_automation, communication_automation, recruitment_automation
      t.string :company_id, null: false
      t.string :candidate_id
      t.string :job_id
      t.string :action_taken, limit: 100
      t.string :result, limit: 20, default: "success"  # success, failed, skipped
      t.text :error_message
      t.jsonb :input_data, default: {}
      t.jsonb :output_data, default: {}
      t.integer :duration_ms
      t.datetime :executed_at, null: false, default: -> { "CURRENT_TIMESTAMP" }
      t.timestamps
    end

    add_index :automation_execution_logs, :company_id
    add_index :automation_execution_logs, :rule_id
    add_index :automation_execution_logs, :executed_at
    add_index :automation_execution_logs, [:company_id, :result]
  end
end
