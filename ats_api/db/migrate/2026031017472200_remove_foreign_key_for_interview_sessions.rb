class RemoveForeignKeyForInterviewSessions < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :interview_sessions, :users if foreign_key_exists?(:interview_sessions, :users)
    remove_foreign_key :interview_sessions, :accounts if foreign_key_exists?(:interview_sessions, :accounts)
  end
end
