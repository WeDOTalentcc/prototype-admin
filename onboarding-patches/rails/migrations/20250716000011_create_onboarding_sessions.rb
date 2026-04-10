# frozen_string_literal: true

class CreateOnboardingSessions < ActiveRecord::Migration[7.1]
  def change
    create_table :onboarding_sessions do |t|
      t.references :user, null: false, foreign_key: { on_delete: :cascade }
      t.references :account, null: false, foreign_key: { on_delete: :cascade }

      # State
      t.string :phase, limit: 30, null: false, default: "pending"
      t.string :channel, limit: 20 # whatsapp, email, web

      # WhatsApp tracking
      t.string :whatsapp_phone, limit: 20
      t.string :whatsapp_conversation_id

      # Timeline
      t.datetime :email_sent_at
      t.datetime :whatsapp_sent_at
      t.datetime :whatsapp_flow_completed_at
      t.datetime :magic_link_clicked_at
      t.datetime :tour_started_at
      t.datetime :tour_completed_at
      t.datetime :first_job_created_at
      t.datetime :completed_at

      # Data
      t.jsonb :onboarding_data, default: {}     # WhatsApp Flow responses
      t.jsonb :progress_steps, default: []       # Array of completed step IDs

      t.timestamps
    end

    add_index :onboarding_sessions, [:user_id, :phase]
    add_index :onboarding_sessions, :phase
  end
end
