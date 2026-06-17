# frozen_string_literal: true

class AddApplyIdToMeetingsAndCalendarEvents < ActiveRecord::Migration[7.1]
  def change
    add_column :meetings, :apply_id, :bigint unless column_exists?(:meetings, :apply_id)
    add_column :calendar_events, :apply_id, :bigint unless column_exists?(:calendar_events, :apply_id)

    add_index :meetings, :apply_id, if_not_exists: true
    add_index :calendar_events, :apply_id, if_not_exists: true
  end
end
