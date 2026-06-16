# frozen_string_literal: true

class CreateCalendarEvents < ActiveRecord::Migration[7.1]
  def change
    create_table :calendar_events, if_not_exists: true do |t|
      t.references :account, null: false, foreign_key: true
      t.references :organizer, null: false, foreign_key: { to_table: :users }
      t.references :meeting, null: true, foreign_key: true

      t.string  :provider, null: false
      t.string  :external_id
      t.string  :external_uid

      t.string  :title, null: false
      t.text    :description
      t.string  :location
      t.string  :importance, default: 'normal'
      t.string  :event_type, null: false, default: 'generic'

      t.datetime :start_time, null: false
      t.datetime :end_time, null: false
      t.string   :timezone, default: 'America/Sao_Paulo'

      t.boolean :is_all_day, default: false
      t.boolean :is_cancelled, default: false
      t.boolean :is_deleted, default: false

      t.jsonb :settings, default: {}
      t.jsonb :metadata, default: {}

      t.timestamps
    end

    add_index :calendar_events, :provider, if_not_exists: true
    add_index :calendar_events, :external_id, if_not_exists: true
    add_index :calendar_events, :external_uid, if_not_exists: true
    add_index :calendar_events, :event_type, if_not_exists: true
    add_index :calendar_events, :start_time, if_not_exists: true
    add_index :calendar_events, [ :account_id, :is_deleted ], if_not_exists: true
    add_index :calendar_events, [ :organizer_id, :start_time ], if_not_exists: true
  end
end
