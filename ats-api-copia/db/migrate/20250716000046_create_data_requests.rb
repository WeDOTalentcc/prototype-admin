# frozen_string_literal: true

class CreateDataRequests < ActiveRecord::Migration[7.1]
  def change
    create_table :data_request_templates, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :template_type, limit: 30
      t.boolean :is_active, default: true
      t.string :created_by
      t.timestamps
    end
    add_index :data_request_templates, :company_id

    create_table :data_request_fields, id: :uuid do |t|
      t.references :data_request_template, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :field_name, null: false, limit: 100
      t.string :field_type, limit: 30, default: "text"
      t.boolean :required, default: false
      t.jsonb :options, default: []
      t.integer :order, default: 0
      t.timestamps
    end

    create_table :data_requests, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :template_id
      t.string :job_id
      t.string :status, limit: 20, default: "pending"
      t.string :sent_via, limit: 20
      t.datetime :sent_at
      t.datetime :completed_at
      t.datetime :expires_at
      t.string :token, limit: 200
      t.timestamps
    end
    add_index :data_requests, :candidate_id
    add_index :data_requests, :token, unique: true

    create_table :data_request_responses, id: :uuid do |t|
      t.references :data_request, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :field_name, limit: 100
      t.text :value
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    create_table :data_request_configs, id: :uuid do |t|
      t.string :company_id, null: false
      t.jsonb :default_fields, default: []
      t.boolean :auto_send, default: false
      t.string :trigger_stage, limit: 100
      t.integer :expiry_days, default: 7
      t.timestamps
    end
    add_index :data_request_configs, :company_id, unique: true

    create_table :vacancy_data_request_configs, id: :uuid do |t|
      t.string :job_vacancy_id, null: false
      t.jsonb :fields, default: []
      t.boolean :auto_send, default: false
      t.string :trigger_stage, limit: 100
      t.timestamps
    end
    add_index :vacancy_data_request_configs, :job_vacancy_id, unique: true
  end
end
