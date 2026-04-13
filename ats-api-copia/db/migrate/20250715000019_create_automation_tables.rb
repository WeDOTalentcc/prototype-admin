class CreateAutomationTables < ActiveRecord::Migration[7.1]
  def change
    create_table :recruitment_automations, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :name, limit: 255
      t.text :description
      t.string :trigger_event, limit: 100
      t.string :action_type, limit: 100
      t.jsonb :conditions, default: {}
      t.jsonb :action_config, default: {}
      t.boolean :is_active, default: true
      t.integer :execution_count, default: 0
      t.datetime :last_executed_at
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :recruitment_automations, :company_id

    create_table :recruitment_slas, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :stage_id, limit: 255
      t.string :stage_name, limit: 100
      t.integer :max_hours, null: false
      t.string :escalation_action, limit: 100
      t.string :escalation_target, limit: 255
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :recruitment_slas, :company_id
    add_index :recruitment_slas, [:company_id, :stage_id], unique: true

    create_table :sla_violations, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :sla_id, null: false
      t.string :candidate_id, limit: 255
      t.string :job_vacancy_id, limit: 255
      t.datetime :violation_date
      t.integer :hours_exceeded
      t.boolean :resolved, default: false
      t.datetime :resolved_at
      t.string :resolved_by, limit: 255
      t.text :resolution_notes
      t.timestamps
    end

    add_index :sla_violations, :sla_id
    add_index :sla_violations, :resolved
    add_foreign_key :sla_violations, :recruitment_slas, column: :sla_id
  end
end
