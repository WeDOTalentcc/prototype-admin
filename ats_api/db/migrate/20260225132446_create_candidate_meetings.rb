# frozen_string_literal: true

class CreateCandidateMeetings < ActiveRecord::Migration[7.1]
  def change
    remove_column :applies, :meeting_id if column_exists?(:applies, :meeting_id)
    remove_column :applies, :calendar_event_id if column_exists?(:applies, :calendar_event_id)
    remove_index :applies, :meeting_id if index_exists?(:applies, :meeting_id)
    remove_index :applies, :calendar_event_id if index_exists?(:applies, :calendar_event_id)

    create_table :candidate_meetings do |t|
      t.bigint :account_id, null: false
      t.bigint :candidate_id, null: false
      t.bigint :apply_id
      t.bigint :meeting_id
      t.bigint :calendar_event_id

      t.timestamps
    end

    add_index :candidate_meetings, :candidate_id
    add_index :candidate_meetings, :apply_id
    add_index :candidate_meetings, :meeting_id
    add_index :candidate_meetings, :calendar_event_id
    add_index :candidate_meetings, [ :candidate_id, :account_id ]
  end
end
