# frozen_string_literal: true

class CreateCalendarEventAttendees < ActiveRecord::Migration[7.1]
  def change
    create_table :calendar_event_attendees, if_not_exists: true do |t|
      t.references :calendar_event, null: false, foreign_key: true
      t.references :user, null: true, foreign_key: true

      t.string  :name
      t.string  :email, null: false
      t.string  :response_status, default: 'not_responded'
      t.datetime :responded_at
      t.boolean :is_organizer, default: false

      t.timestamps
    end

    add_index :calendar_event_attendees, :email, if_not_exists: true
    add_index :calendar_event_attendees, :response_status, if_not_exists: true
    add_index :calendar_event_attendees, [ :calendar_event_id, :email ], unique: true, if_not_exists: true
  end
end
