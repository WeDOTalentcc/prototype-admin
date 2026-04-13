# frozen_string_literal: true

class CreateWhatsappTables < ActiveRecord::Migration[7.1]
  def change
    create_table :whatsapp_conversations, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id
      t.string :user_id                          # recruiter, if internal chat
      t.string :phone_number, null: false, limit: 20
      t.string :twilio_conversation_sid, limit: 100
      t.string :status, limit: 20, default: "active"  # active, closed, expired
      t.string :context_type, limit: 30          # screening, onboarding, outreach, support
      t.string :context_id                       # job_id, session_id, etc.
      t.datetime :last_message_at
      t.datetime :expires_at                     # 24h window
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :whatsapp_conversations, :company_id
    add_index :whatsapp_conversations, :candidate_id
    add_index :whatsapp_conversations, :phone_number
    add_index :whatsapp_conversations, :status
    add_index :whatsapp_conversations, [:company_id, :phone_number]

    create_table :whatsapp_messages, id: :uuid do |t|
      t.references :whatsapp_conversation, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :direction, limit: 10, null: false  # inbound, outbound
      t.string :message_type, limit: 20, default: "text"  # text, template, image, audio, document, interactive, flow
      t.text :content
      t.string :message_sid, limit: 100          # Twilio message SID
      t.string :template_name, limit: 100
      t.jsonb :template_variables, default: {}
      t.string :status, limit: 20, default: "sent"  # queued, sent, delivered, read, failed
      t.jsonb :metadata, default: {}
      t.datetime :sent_at
      t.datetime :delivered_at
      t.datetime :read_at
      t.timestamps
    end

    add_index :whatsapp_messages, :message_sid
    add_index :whatsapp_messages, [:whatsapp_conversation_id, :created_at]
  end
end
