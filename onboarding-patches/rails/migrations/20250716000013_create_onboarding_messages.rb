# frozen_string_literal: true

class CreateOnboardingMessages < ActiveRecord::Migration[7.1]
  def change
    create_table :onboarding_messages do |t|
      t.references :onboarding_session, null: false, foreign_key: { on_delete: :cascade }

      t.string :channel, limit: 20, null: false    # whatsapp, email, web
      t.string :direction, limit: 10, null: false   # inbound, outbound
      t.text :content
      t.string :message_sid, limit: 100             # Twilio message SID
      t.jsonb :metadata, default: {}

      t.timestamps
    end

    add_index :onboarding_messages, [:onboarding_session_id, :channel]
    add_index :onboarding_messages, :message_sid
  end
end
