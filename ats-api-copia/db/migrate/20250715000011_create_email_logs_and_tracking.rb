class CreateEmailLogsAndTracking < ActiveRecord::Migration[7.1]
  def change
    create_table :email_logs, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :template_id
      t.string :candidate_id, limit: 255
      t.string :recipient_email, limit: 255
      t.string :subject, limit: 500
      t.text :body_html
      t.text :body_text
      t.string :status, limit: 50, default: "pending"
      t.datetime :sent_at
      t.text :error_message
      t.jsonb :variables_used, default: {}
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :email_logs, :template_id
    add_index :email_logs, :candidate_id
    add_index :email_logs, :recipient_email
    add_index :email_logs, :status
    add_index :email_logs, :created_by

    create_table :email_tracking_events, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :email_log_id, null: false
      t.string :event_type, limit: 50, null: false
      t.datetime :event_at, null: false
      t.jsonb :metadata, default: {}
      t.string :ip_address, limit: 50
      t.string :user_agent, limit: 500
      t.timestamps
    end

    add_index :email_tracking_events, :email_log_id
    add_index :email_tracking_events, :event_type
    add_foreign_key :email_tracking_events, :email_logs

    create_table :recruitment_email_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255, null: false
      t.string :stage_name, limit: 100
      t.string :sub_status, limit: 100
      t.string :action_type, limit: 50
      t.uuid :template_id
      t.boolean :is_auto_send, default: false
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :recruitment_email_templates, :company_id
    add_index :recruitment_email_templates, [:company_id, :stage_name]
  end
end
