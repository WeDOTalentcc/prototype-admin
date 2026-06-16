# frozen_string_literal: true

class CreateJourneyAndRecruitment < ActiveRecord::Migration[7.1]
  def change
    create_table :journey_blueprints, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :blueprint_type, limit: 30
      t.boolean :is_active, default: true
      t.boolean :is_template, default: false
      t.jsonb :config, default: {}
      t.string :created_by
      t.timestamps
    end
    add_index :journey_blueprints, :company_id

    create_table :journey_steps, id: :uuid do |t|
      t.references :journey_blueprint, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :name, limit: 200
      t.string :step_type, limit: 30
      t.integer :order, default: 0
      t.jsonb :config, default: {}
      t.jsonb :conditions, default: {}
      t.string :next_step_id
      t.timestamps
    end
    add_index :journey_steps, [:journey_blueprint_id, :order]

    create_table :journey_integrations, id: :uuid do |t|
      t.references :journey_blueprint, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :integration_type, limit: 50
      t.jsonb :config, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end

    create_table :recruitment_templates, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.jsonb :stages, default: []
      t.jsonb :automations, default: []
      t.boolean :is_active, default: true
      t.string :created_by
      t.timestamps
    end
    add_index :recruitment_templates, :company_id

    create_table :tasks, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :assigned_to
      t.string :created_by
      t.string :title, null: false, limit: 300
      t.text :description
      t.string :task_type, limit: 30
      t.string :status, limit: 20, default: "pending"
      t.string :priority, limit: 20, default: "medium"
      t.datetime :due_date
      t.string :related_type, limit: 50
      t.string :related_id
      t.jsonb :metadata, default: {}
      t.datetime :completed_at
      t.timestamps
    end
    add_index :tasks, :company_id
    add_index :tasks, :assigned_to
    add_index :tasks, :status

    create_table :task_templates, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :task_type, limit: 30
      t.jsonb :default_config, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :task_templates, :company_id
  end
end
