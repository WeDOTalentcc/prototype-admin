class CreateAuditLogs < ActiveRecord::Migration[7.1]
  def change
    create_table :audit_logs do |t|
      t.references :user, null: true, foreign_key: true
      t.references :account, null: true, foreign_key: true
      t.string :action, null: false
      t.string :resource_type
      t.integer :resource_id
      t.jsonb :metadata, default: {}
      t.string :ip_address
      t.string :user_agent
      t.string :workos_event_id

      t.timestamps
    end

    add_index :audit_logs, [ :user_id, :created_at ]
    add_index :audit_logs, [ :account_id, :created_at ]
    add_index :audit_logs, [ :resource_type, :resource_id ]
    add_index :audit_logs, :workos_event_id, unique: true
  end
end
