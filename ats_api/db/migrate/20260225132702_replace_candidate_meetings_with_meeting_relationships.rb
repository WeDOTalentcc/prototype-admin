# frozen_string_literal: true

class ReplaceCandidateMeetingsWithMeetingRelationships < ActiveRecord::Migration[7.1]
  def change
    drop_table :candidate_meetings, if_exists: true

    create_table :meeting_relationships do |t|
      t.bigint  :account_id,      null: false
      t.string  :reference_type,  null: false
      t.bigint  :reference_id,    null: false
      t.bigint  :apply_id
      t.bigint  :meeting_id
      t.bigint  :calendar_event_id
      t.string  :role

      t.timestamps
    end

    add_index :meeting_relationships, [ :reference_type, :reference_id ]
    add_index :meeting_relationships, :meeting_id
    add_index :meeting_relationships, :calendar_event_id
    add_index :meeting_relationships, :apply_id
    add_index :meeting_relationships, :account_id
  end
end
