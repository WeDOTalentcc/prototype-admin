class CreateAtsIntegrationTables < ActiveRecord::Migration[7.1]
  def change
    create_table :integration_providers, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :name, limit: 100, null: false
      t.string :provider_type, limit: 50
      t.string :display_name, limit: 255
      t.text :description
      t.string :logo_url, limit: 500
      t.jsonb :config_schema, default: {}
      t.jsonb :supported_features, default: []
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :integration_providers, :name, unique: true

    create_table :integration_connections, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.uuid :provider_id, null: false
      t.string :status, limit: 50, default: "active"
      t.jsonb :credentials, default: {}
      t.jsonb :config, default: {}
      t.datetime :last_sync_at
      t.string :last_sync_status, limit: 50
      t.text :last_sync_error
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :integration_connections, :company_id
    add_index :integration_connections, :provider_id
    add_foreign_key :integration_connections, :integration_providers, column: :provider_id

    create_table :ats_connections, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :provider, limit: 100, null: false
      t.jsonb :credentials, default: {}
      t.string :status, limit: 50, default: "active"
      t.string :external_account_id, limit: 255
      t.jsonb :sync_config, default: {}
      t.datetime :last_sync_at
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :ats_connections, :company_id
    add_index :ats_connections, [:company_id, :provider], unique: true

    create_table :ats_sync_jobs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id, null: false
      t.string :direction, limit: 20
      t.string :entity_type, limit: 50
      t.string :status, limit: 50, default: "pending"
      t.integer :items_total, default: 0
      t.integer :items_synced, default: 0
      t.integer :items_failed, default: 0
      t.jsonb :errors, default: []
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end

    add_index :ats_sync_jobs, :connection_id
    add_foreign_key :ats_sync_jobs, :ats_connections, column: :connection_id

    create_table :ats_candidates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id, null: false
      t.string :external_id, limit: 255
      t.string :local_candidate_id, limit: 255
      t.string :sync_status, limit: 50, default: "synced"
      t.datetime :last_synced_at
      t.jsonb :external_data, default: {}
      t.timestamps
    end

    add_index :ats_candidates, :connection_id
    add_index :ats_candidates, [:connection_id, :external_id], unique: true

    create_table :ats_webhook_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id
      t.string :event, limit: 100
      t.jsonb :payload, default: {}
      t.boolean :processed, default: false
      t.text :error_message
      t.datetime :processed_at
      t.datetime :created_at, null: false
    end

    add_index :ats_webhook_logs, :connection_id
    add_index :ats_webhook_logs, :processed

    create_table :ats_job_mappings, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id, null: false
      t.string :external_job_id, limit: 255
      t.string :local_job_id, limit: 255
      t.string :sync_status, limit: 50, default: "synced"
      t.timestamps
    end

    add_index :ats_job_mappings, :connection_id
    add_index :ats_job_mappings, [:connection_id, :external_job_id], unique: true, name: "idx_ats_job_map_ext"

    create_table :integration_sync_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id, null: false
      t.string :direction, limit: 20
      t.string :entity_type, limit: 50
      t.integer :records_synced, default: 0
      t.integer :records_failed, default: 0
      t.jsonb :errors, default: []
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end

    add_index :integration_sync_logs, :connection_id

    create_table :integration_webhooks, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :connection_id, null: false
      t.string :url, limit: 2000
      t.jsonb :events, default: []
      t.boolean :is_active, default: true
      t.string :secret_key, limit: 255
      t.timestamps
    end

    add_index :integration_webhooks, :connection_id
  end
end
