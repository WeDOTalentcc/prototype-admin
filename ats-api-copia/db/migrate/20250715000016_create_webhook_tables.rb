class CreateWebhookTables < ActiveRecord::Migration[7.1]
  def change
    create_table :webhooks, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :name, limit: 255
      t.text :description
      t.string :url, limit: 2000, null: false
      t.jsonb :events, default: []
      t.string :secret_key, limit: 255
      t.jsonb :headers, default: {}
      t.boolean :is_active, default: true
      t.integer :retry_count, default: 3
      t.integer :timeout_seconds, default: 30
      t.datetime :last_triggered_at
      t.datetime :last_success_at
      t.datetime :last_failure_at
      t.text :last_failure_reason
      t.integer :total_triggers, default: 0
      t.integer :total_successes, default: 0
      t.integer :total_failures, default: 0
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :webhooks, :company_id

    create_table :webhook_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :webhook_id, null: false
      t.string :event, limit: 100
      t.string :status, limit: 50
      t.integer :response_code
      t.text :response_body
      t.text :request_body
      t.integer :duration_ms
      t.text :error_message
      t.datetime :created_at, null: false
    end

    add_index :webhook_logs, :webhook_id
    add_index :webhook_logs, :created_at
    add_foreign_key :webhook_logs, :webhooks

    create_table :webhook_registrations, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :provider, limit: 100
      t.jsonb :config, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :webhook_registrations, :company_id

    create_table :webhook_delivery_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :webhook_id, null: false
      t.integer :attempt, default: 1
      t.string :status, limit: 50
      t.integer :duration_ms
      t.integer :response_code
      t.text :error_message
      t.datetime :created_at, null: false
    end

    add_index :webhook_delivery_logs, :webhook_id
    add_foreign_key :webhook_delivery_logs, :webhooks
  end
end
