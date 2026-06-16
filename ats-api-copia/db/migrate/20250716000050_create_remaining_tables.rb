# frozen_string_literal: true

class CreateRemainingTables < ActiveRecord::Migration[7.1]
  def change
    # Activity feed
    create_table :activity_feed, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :activity_type, limit: 50
      t.string :entity_type, limit: 50
      t.string :entity_id
      t.text :description
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :activity_feed, :company_id
    add_index :activity_feed, [:company_id, :created_at]

    # Conversations (chat)
    create_table :conversations, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id, null: false
      t.string :title, limit: 300
      t.string :context_type, limit: 50
      t.string :context_id
      t.string :status, limit: 20, default: "active"
      t.jsonb :metadata, default: {}
      t.datetime :last_message_at
      t.timestamps
    end
    add_index :conversations, :user_id
    add_index :conversations, :company_id

    # Background jobs
    create_table :background_jobs, id: :uuid do |t|
      t.string :company_id
      t.string :job_type, limit: 50
      t.string :status, limit: 20, default: "pending"
      t.jsonb :payload, default: {}
      t.jsonb :result, default: {}
      t.text :error_message
      t.integer :attempts, default: 0
      t.datetime :started_at
      t.datetime :completed_at
      t.timestamps
    end
    add_index :background_jobs, :status

    # Approvers (for approval workflows)
    create_table :approvers, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id, null: false
      t.string :approval_type, limit: 50
      t.integer :level, default: 1
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :approvers, [:company_id, :approval_type]

    # Skills catalogs
    create_table :behavioral_competencies_catalog, id: :uuid do |t|
      t.string :company_id
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :category, limit: 50
      t.string :trait_big_five, limit: 30
      t.boolean :is_system, default: false
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :behavioral_competencies_catalog, :company_id

    create_table :company_skills_catalog, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :skill_name, null: false, limit: 200
      t.string :category, limit: 50
      t.jsonb :metadata, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :company_skills_catalog, :company_id

    create_table :client_skill_catalogs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.jsonb :skills, default: []
      t.string :source, limit: 30
      t.timestamps
    end
    add_index :client_skill_catalogs, :company_id

    create_table :client_test_configs, id: :uuid do |t|
      t.string :company_id, null: false
      t.jsonb :config, default: {}
      t.boolean :ai_correction_enabled, default: true
      t.boolean :proctoring_enabled, default: false
      t.timestamps
    end
    add_index :client_test_configs, :company_id, unique: true

    # Company calendar
    create_table :company_calendar_credentials, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :provider, limit: 30
      t.jsonb :credentials, default: {}
      t.string :status, limit: 20, default: "active"
      t.datetime :last_synced_at
      t.timestamps
    end
    add_index :company_calendar_credentials, :company_id

    # Culture analysis
    create_table :culture_analysis_jobs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :status, limit: 20, default: "pending"
      t.jsonb :results, default: {}
      t.datetime :completed_at
      t.timestamps
    end
    add_index :culture_analysis_jobs, :company_id

    # WorkOS SSO
    create_table :company_workos_config, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :organization_id, limit: 200
      t.jsonb :config, default: {}
      t.boolean :sso_enabled, default: false
      t.boolean :directory_sync_enabled, default: false
      t.timestamps
    end
    add_index :company_workos_config, :company_id, unique: true

    create_table :workos_groups, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :workos_group_id, limit: 200
      t.string :name, limit: 200
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :workos_groups, :workos_group_id, unique: true

    create_table :workos_group_memberships, id: :uuid do |t|
      t.references :workos_group, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :user_id, null: false
      t.timestamps
    end
    add_index :workos_group_memberships, [:workos_group_id, :user_id], unique: true, name: "idx_workos_membership_unique"

    create_table :workos_group_role_mappings, id: :uuid do |t|
      t.references :workos_group, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :role_name, limit: 100
      t.jsonb :permissions, default: []
      t.timestamps
    end

    create_table :sso_audit_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :action, limit: 50
      t.string :provider, limit: 30
      t.jsonb :details, default: {}
      t.string :ip_address, limit: 45
      t.timestamps
    end
    add_index :sso_audit_logs, :company_id

    # Imported JDs
    create_table :imported_job_descriptions, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :source, limit: 50
      t.text :raw_content
      t.jsonb :parsed_data, default: {}
      t.string :status, limit: 20, default: "pending"
      t.string :job_id
      t.timestamps
    end
    add_index :imported_job_descriptions, :company_id

    create_table :import_batches, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :batch_type, limit: 30
      t.string :source, limit: 50
      t.integer :total_records, default: 0
      t.integer :imported, default: 0
      t.integer :failed, default: 0
      t.string :status, limit: 20, default: "pending"
      t.jsonb :errors, default: []
      t.string :created_by
      t.timestamps
    end
    add_index :import_batches, :company_id

    # Escalation
    create_table :escalation_rules, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :trigger_type, limit: 50
      t.jsonb :conditions, default: {}
      t.string :action, limit: 50
      t.string :target_user_id
      t.integer :delay_minutes, default: 0
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :escalation_rules, :company_id

    create_table :escalation_logs, id: :uuid do |t|
      t.references :escalation_rule, type: :uuid, foreign_key: { on_delete: :nullify }
      t.string :company_id, null: false
      t.string :entity_type, limit: 50
      t.string :entity_id
      t.string :action_taken, limit: 50
      t.string :target_user
      t.timestamps
    end
    add_index :escalation_logs, :company_id

    # Global & platform policies
    create_table :global_policies, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :policy_type, limit: 50
      t.jsonb :rules, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :global_policies, :company_id

    create_table :platform_global_policies, id: :uuid do |t|
      t.string :policy_type, limit: 50
      t.string :name, limit: 200
      t.jsonb :rules, default: {}
      t.boolean :is_active, default: true
      t.timestamps
    end

    create_table :platform_policy_audit_logs, id: :uuid do |t|
      t.string :policy_id
      t.string :action, limit: 50
      t.string :performed_by
      t.jsonb :changes, default: {}
      t.timestamps
    end

    # Rate limiting
    create_table :rate_limit_rules, id: :uuid do |t|
      t.string :company_id
      t.string :rule_name, limit: 100
      t.string :resource, limit: 100
      t.integer :max_requests
      t.integer :window_seconds
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :rate_limit_rules, :company_id

    # Trust center
    create_table :trust_center_settings, id: :uuid do |t|
      t.string :company_id, null: false
      t.boolean :is_public, default: false
      t.jsonb :config, default: {}
      t.string :custom_domain, limit: 200
      t.timestamps
    end
    add_index :trust_center_settings, :company_id, unique: true

    create_table :trust_center_subprocessors, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.string :purpose, limit: 300
      t.string :location, limit: 100
      t.string :data_types, limit: 300
      t.boolean :is_active, default: true
      t.timestamps
    end
    add_index :trust_center_subprocessors, :company_id

    create_table :trust_center_resources, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :title, limit: 200
      t.text :content
      t.string :resource_type, limit: 50
      t.string :file_url, limit: 500
      t.boolean :is_public, default: true
      t.timestamps
    end
    add_index :trust_center_resources, :company_id

    create_table :trust_center_updates, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :title, limit: 200
      t.text :content
      t.string :update_type, limit: 30
      t.datetime :published_at
      t.timestamps
    end
    add_index :trust_center_updates, :company_id

    # Data access logs
    create_table :data_access_logs, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :user_id
      t.string :resource_type, limit: 50
      t.string :resource_id
      t.string :action, limit: 30
      t.string :ip_address, limit: 45
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    add_index :data_access_logs, :company_id
    add_index :data_access_logs, :created_at
  end
end
