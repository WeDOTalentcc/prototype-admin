# frozen_string_literal: true

class CreateCommunicationTables < ActiveRecord::Migration[7.1]
  def change
    # Communication history — log of ALL communication
    create_table :communication_history, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id
      t.string :user_id                        # recruiter who sent
      t.string :job_id
      t.string :channel, null: false, limit: 20  # email, whatsapp, phone, sms, chat, teams
      t.string :direction, limit: 10, null: false  # inbound, outbound
      t.string :subject, limit: 500
      t.text :content
      t.string :status, limit: 20, default: "sent"  # draft, sent, delivered, read, failed, bounced
      t.string :template_id
      t.string :external_id, limit: 200        # Twilio SID, email message-id, etc.
      t.jsonb :metadata, default: {}
      t.datetime :sent_at
      t.datetime :delivered_at
      t.datetime :read_at
      t.timestamps
    end

    add_index :communication_history, :company_id
    add_index :communication_history, :candidate_id
    add_index :communication_history, :channel
    add_index :communication_history, [:company_id, :candidate_id]
    add_index :communication_history, :sent_at

    # Communication automations
    create_table :communication_automations, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, null: false, limit: 200
      t.text :description
      t.string :trigger_event, null: false, limit: 100  # stage_changed, interview_scheduled, offer_sent
      t.string :channel, limit: 20, default: "email"
      t.string :template_id
      t.integer :delay_minutes, default: 0
      t.jsonb :conditions, default: {}
      t.jsonb :action_config, default: {}
      t.boolean :is_active, default: true
      t.integer :execution_count, default: 0
      t.datetime :last_executed_at
      t.string :created_by
      t.timestamps
    end

    add_index :communication_automations, :company_id
    add_index :communication_automations, [:company_id, :trigger_event]
  end
end
