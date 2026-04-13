class CreateNotificationTables < ActiveRecord::Migration[7.1]
  def change
    create_table :notifications, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :user_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.string :notification_type, limit: 100
      t.string :title, limit: 500
      t.text :message
      t.string :status, limit: 50, default: "unread"
      t.string :priority, limit: 20, default: "normal"
      t.string :action_url, limit: 1000
      t.jsonb :metadata, default: {}
      t.datetime :read_at
      t.datetime :dismissed_at
      t.timestamps
    end

    add_index :notifications, :user_id
    add_index :notifications, :company_id
    add_index :notifications, :status
    add_index :notifications, :created_at

    create_table :chat_notifications, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :user_id, limit: 255, null: false
      t.string :conversation_id, limit: 255
      t.integer :unread_count, default: 0
      t.datetime :last_message_at
      t.timestamps
    end

    add_index :chat_notifications, [:user_id, :conversation_id], unique: true

    create_table :notification_policies, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :channel, limit: 50, null: false
      t.string :event_type, limit: 100, null: false
      t.boolean :is_enabled, default: true
      t.jsonb :config, default: {}
      t.timestamps
    end

    add_index :notification_policies, :company_id
    add_index :notification_policies, [:company_id, :channel, :event_type], unique: true, name: "idx_notif_policies_unique"
  end
end
