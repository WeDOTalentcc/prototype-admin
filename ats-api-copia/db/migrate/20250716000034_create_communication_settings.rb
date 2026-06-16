# frozen_string_literal: true

class CreateCommunicationSettings < ActiveRecord::Migration[7.1]
  def change
    create_table :communication_settings, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :default_channel, limit: 20, default: "email"
      t.jsonb :channel_config, default: {}             # per-channel settings (smtp, twilio, teams)
      t.jsonb :business_hours, default: {}             # { mon: {start: "09:00", end: "18:00"}, ... }
      t.string :timezone, limit: 50, default: "America/Sao_Paulo"
      t.boolean :respect_business_hours, default: true
      t.boolean :auto_reply_enabled, default: false
      t.text :auto_reply_message
      t.jsonb :signature_config, default: {}
      t.boolean :tracking_enabled, default: true       # email open/click tracking
      t.string :whatsapp_number, limit: 20
      t.boolean :whatsapp_enabled, default: false
      t.string :teams_tenant_id, limit: 100
      t.boolean :teams_enabled, default: false
      t.timestamps
    end

    add_index :communication_settings, :company_id, unique: true

    create_table :communication_matrix_entries, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :event_type, null: false, limit: 100    # stage_changed, interview_scheduled, offer_sent, rejection
      t.string :channel, null: false, limit: 20        # email, whatsapp, sms, teams
      t.string :recipient_type, limit: 30, default: "candidate"  # candidate, recruiter, manager, team
      t.string :template_id
      t.boolean :is_active, default: true
      t.integer :delay_minutes, default: 0
      t.jsonb :conditions, default: {}
      t.timestamps
    end

    add_index :communication_matrix_entries, :company_id
    add_index :communication_matrix_entries, [:company_id, :event_type]
  end
end
