# frozen_string_literal: true

class CreateMeetings < ActiveRecord::Migration[7.1]
  def change
    create_table :meetings, if_not_exists: true do |t|
      t.references :account, null: false, foreign_key: true
      t.references :organizer, null: false, foreign_key: { to_table: :users }

      t.string :provider, null: false
      t.string :external_id
      t.text :join_url

      t.string :subject, null: false
      t.datetime :start_time, null: false
      t.datetime :end_time, null: false

      t.jsonb :settings, default: {}
      t.jsonb :metadata, default: {}

      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :meetings, :provider, if_not_exists: true
    add_index :meetings, :external_id, if_not_exists: true
    add_index :meetings, :organizer_id, if_not_exists: true
    add_index :meetings, :start_time, if_not_exists: true
    add_index :meetings, [ :account_id, :is_deleted ], if_not_exists: true
  end
end
