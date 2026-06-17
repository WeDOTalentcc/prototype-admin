# frozen_string_literal: true

class AddJobIdToMeetingsAndCalendarEvents < ActiveRecord::Migration[7.1]
  def change
    add_column :meetings, :job_id, :bigint unless column_exists?(:meetings, :job_id)
    add_column :calendar_events, :job_id, :bigint unless column_exists?(:calendar_events, :job_id)

    add_index :meetings, :job_id, if_not_exists: true
    add_index :calendar_events, :job_id, if_not_exists: true
  end
end
