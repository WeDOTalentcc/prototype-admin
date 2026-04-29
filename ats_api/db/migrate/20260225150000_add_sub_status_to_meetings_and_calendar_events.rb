# frozen_string_literal: true

class AddSubStatusToMeetingsAndCalendarEvents < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:meetings, :sub_status)
      add_column :meetings, :sub_status, :string, default: 'invite_sent', null: false
      add_index :meetings, :sub_status
    end

    unless column_exists?(:calendar_events, :sub_status)
      add_column :calendar_events, :sub_status, :string, default: 'invite_sent', null: false
      add_index :calendar_events, :sub_status
    end
  end
end
