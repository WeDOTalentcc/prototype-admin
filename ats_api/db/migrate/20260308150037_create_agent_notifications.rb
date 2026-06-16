# frozen_string_literal: true

class CreateAgentNotifications < ActiveRecord::Migration[7.1]
  def change
    create_table :agent_notifications do |t|
      t.references :user, null: false, foreign_key: true
      t.string :notification_type, null: false
      t.string :channel, null: false, default: "web"
      t.string :status, null: false, default: "pending"
      t.text :content
      t.string :reference_type
      t.bigint :reference_id
      t.string :alert_key
      t.jsonb :metadata, default: {}
      t.datetime :sent_at
      t.datetime :read_at
      t.timestamps
    end

    add_index :agent_notifications, [ :user_id, :status ]
    add_index :agent_notifications, [ :user_id, :notification_type ]
    add_index :agent_notifications, :alert_key, unique: true
    add_index :agent_notifications, [ :reference_type, :reference_id ]
    add_index :agent_notifications, :sent_at
  end
end
