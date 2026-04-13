class ExpandSelectiveProcessesAndUsers < ActiveRecord::Migration[7.1]
  def change
    # Expand selective_processes (recruitment stages)
    change_table :selective_processes do |t|
      t.string :display_name, limit: 100
      t.text :description
      t.string :color, limit: 20
      t.string :icon, limit: 50
      t.string :stage_type, limit: 50, default: "active"
      t.boolean :is_initial, default: false
      t.boolean :is_final, default: false
      t.boolean :is_rejection, default: false
      t.boolean :is_hired, default: false
      t.jsonb :auto_advance_rules, default: {}
      t.integer :sla_hours
      t.boolean :is_active, default: true
      t.boolean :is_system, default: false
      t.string :stage_category, limit: 20, default: "custom"
      t.string :action_behavior, limit: 30, default: "passive"
      t.string :default_channel, limit: 30, default: "email"
      t.jsonb :stage_metadata, default: {}
      t.string :created_by, limit: 255
      t.string :company_id, limit: 255
    end

    add_index :selective_processes, :company_id, name: "idx_sp_company_id"
    add_index :selective_processes, :is_active, name: "idx_sp_is_active"

    # Expand users
    change_table :users do |t|
      t.string :name, limit: 255
      t.string :role, limit: 50
      t.jsonb :permissions, default: {}
      t.string :workos_user_id, limit: 255
      t.string :avatar_url, limit: 500
      t.datetime :last_login_at
      t.string :status, limit: 50, default: "active"
      t.uuid :fork_uuid
    end

    add_index :users, :workos_user_id, unique: true, where: "workos_user_id IS NOT NULL"
    add_index :users, :status, name: "idx_users_status"
    add_index :users, :fork_uuid, unique: true, where: "fork_uuid IS NOT NULL"

    # Expand applies
    change_table :applies do |t|
      t.string :source, limit: 100
      t.string :status, limit: 50, default: "active"
      t.float :lia_score
      t.float :match_percentage
      t.string :current_stage, limit: 100
      t.datetime :stage_entered_at
      t.jsonb :additional_data, default: {}
      t.uuid :fork_uuid
    end

    add_index :applies, :status, name: "idx_applies_status"
    add_index :applies, :fork_uuid, unique: true, where: "fork_uuid IS NOT NULL"
  end
end
