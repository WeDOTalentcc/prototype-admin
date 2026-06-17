class RemoveForeignKeysToAccountRelatedToMeeting < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :meetings, :accounts if foreign_key_exists?(:meetings, :accounts)
    remove_foreign_key :meetings, :users, column: :organizer_id if foreign_key_exists?(:meetings, :users, column: :organizer_id)
    remove_foreign_key :meeting_relationships, :accounts if foreign_key_exists?(:meeting_relationships, :accounts)
    remove_foreign_key :cached_availabilities, :users if foreign_key_exists?(:cached_availabilities, :users)
    remove_foreign_key :calendar_events, :accounts if foreign_key_exists?(:calendar_events, :accounts)
    remove_foreign_key :calendar_events, :users, column: :organizer_id if foreign_key_exists?(:calendar_events, :users, column: :organizer_id)
    remove_foreign_key :calendar_event_attendees, :users if foreign_key_exists?(:calendar_event_attendees, :users)
    remove_foreign_key :scheduling_links, :accounts if foreign_key_exists?(:scheduling_links, :accounts)
    remove_foreign_key :scheduling_links, :users, column: :created_by_id if foreign_key_exists?(:scheduling_links, :users, column: :created_by_id)
  end
end
