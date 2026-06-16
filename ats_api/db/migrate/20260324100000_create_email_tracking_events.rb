class CreateEmailTrackingEvents < ActiveRecord::Migration[7.1]
  def change
    create_table :email_tracking_events do |t|
      t.references :dispatch_message, null: false, index: true, foreign_key: true
      t.string :event_type, null: false
      t.timestamp :occurred_at, null: false
      t.text :user_agent
      t.string :ip_address
      t.text :url_clicked
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :email_tracking_events, [ :dispatch_message_id, :event_type ]
    add_index :email_tracking_events, :occurred_at
  end
end
