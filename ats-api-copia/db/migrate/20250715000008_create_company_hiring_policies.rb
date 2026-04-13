class CreateCompanyHiringPolicies < ActiveRecord::Migration[7.1]
  def change
    create_table :company_hiring_policies, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.jsonb :pipeline_rules, default: {}
      t.jsonb :scheduling_rules, default: {}
      t.jsonb :communication_rules, default: {}
      t.jsonb :screening_rules, default: {}
      t.jsonb :automation_rules, default: {}
      t.jsonb :pipeline_templates, default: []
      t.jsonb :learned_patterns, default: {}
      t.jsonb :answered_questions, default: {}
      t.integer :setup_progress, default: 0
      t.datetime :setup_completed_at
      t.string :created_by, limit: 255
      t.string :updated_by, limit: 255
      t.timestamps
    end

    add_index :company_hiring_policies, :company_id, unique: true
  end
end
