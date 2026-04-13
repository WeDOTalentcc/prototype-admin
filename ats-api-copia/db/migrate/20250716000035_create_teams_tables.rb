# frozen_string_literal: true

class CreateTeamsTables < ActiveRecord::Migration[7.1]
  def change
    create_table :teams_conversations, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :teams_channel_id, limit: 200
      t.string :teams_thread_id, limit: 200
      t.string :context_type, limit: 30                # candidate, job, campaign, general
      t.string :context_id
      t.string :title, limit: 200
      t.string :status, limit: 20, default: "active"
      t.jsonb :participants, default: []               # [{user_id, name, email}]
      t.datetime :last_message_at
      t.timestamps
    end

    add_index :teams_conversations, :company_id
    add_index :teams_conversations, :teams_thread_id

    create_table :teams_messages, id: :uuid do |t|
      t.references :teams_conversation, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :sender_id
      t.string :sender_name, limit: 200
      t.string :sender_type, limit: 20, default: "user"  # user, lia, system
      t.text :content
      t.string :teams_message_id, limit: 200
      t.jsonb :attachments, default: []
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :teams_messages, :teams_message_id
  end
end
