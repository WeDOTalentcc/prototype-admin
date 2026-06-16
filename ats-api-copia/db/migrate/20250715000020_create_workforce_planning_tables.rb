class CreateWorkforcePlanningTables < ActiveRecord::Migration[7.1]
  def change
    create_table :hiring_plans, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.uuid :department_id
      t.string :name, limit: 255
      t.text :description
      t.integer :year
      t.integer :quarter
      t.string :period, limit: 50
      t.integer :planned_hires, default: 0
      t.integer :actual_hires, default: 0
      t.float :budget
      t.float :budget_used, default: 0
      t.string :status, limit: 50, default: "draft"
      t.string :approved_by, limit: 255
      t.datetime :approved_at
      t.jsonb :metadata, default: {}
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :hiring_plans, :company_id
    add_index :hiring_plans, :department_id
    add_index :hiring_plans, :status

    create_table :planned_headcounts, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :hiring_plan_id, null: false
      t.string :role_title, limit: 255
      t.string :seniority, limit: 50
      t.integer :quantity, default: 1
      t.string :priority, limit: 20, default: "medium"
      t.text :justification
      t.string :status, limit: 50, default: "planned"
      t.float :estimated_salary
      t.string :currency, limit: 10, default: "BRL"
      t.date :target_start_date
      t.jsonb :requirements, default: {}
      t.timestamps
    end

    add_index :planned_headcounts, :hiring_plan_id
    add_foreign_key :planned_headcounts, :hiring_plans

    create_table :workforce_entries, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.uuid :department_id
      t.integer :current_headcount, default: 0
      t.integer :target_headcount, default: 0
      t.integer :gap, default: 0
      t.string :period, limit: 50
      t.integer :year
      t.jsonb :breakdown, default: {}
      t.timestamps
    end

    add_index :workforce_entries, :company_id
    add_index :workforce_entries, :department_id

    create_table :import_jobs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :source, limit: 100
      t.string :source_file, limit: 500
      t.string :status, limit: 50, default: "pending"
      t.integer :records_total, default: 0
      t.integer :records_imported, default: 0
      t.integer :records_failed, default: 0
      t.jsonb :errors, default: []
      t.jsonb :mapping, default: {}
      t.string :created_by, limit: 255
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end

    add_index :import_jobs, :company_id
    add_index :import_jobs, :status
  end
end
