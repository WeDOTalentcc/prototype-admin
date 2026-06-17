# frozen_string_literal: true

class CreateBusinessRulesAndProcesses < ActiveRecord::Migration[7.1]
  def change
    create_table :business_rules, id: :uuid do |t|
      t.string :company_id
      t.string :rule_name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50          # hiring, screening, communication, compliance
      t.string :rule_type, limit: 30         # validation, automation, policy, guard
      t.jsonb :conditions, default: {}       # when to apply
      t.jsonb :actions, default: {}          # what to do
      t.integer :priority, default: 0
      t.boolean :is_active, default: true
      t.boolean :is_system, default: false
      t.string :created_by
      t.timestamps
    end
    add_index :business_rules, :company_id
    add_index :business_rules, [:company_id, :category]
    add_index :business_rules, [:company_id, :is_active]

    create_table :business_processes, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :process_name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50          # recruitment, onboarding, compliance, security
      t.string :owner
      t.string :status, limit: 20, default: "active"
      t.jsonb :steps, default: []
      t.jsonb :dependencies, default: []
      t.integer :review_frequency_days
      t.datetime :last_reviewed_at
      t.string :reviewed_by
      t.boolean :is_critical, default: false
      t.timestamps
    end
    add_index :business_processes, :company_id
    add_index :business_processes, [:company_id, :category]
  end
end
