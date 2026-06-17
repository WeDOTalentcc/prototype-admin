class AddScreeningFieldsForJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :use_whatsapp_channel, :boolean, default: false unless column_exists?(:jobs, :use_whatsapp_channel)
    add_column :jobs, :use_webchat_channel, :boolean, default: false unless column_exists?(:jobs, :use_website_channel)
    add_column :jobs, :use_call_channel, :boolean, default: false unless column_exists?(:jobs, :use_call_channel)
    add_column :jobs, :minimum_screening_score, :float, default: nil, null: true unless column_exists?(:jobs, :minimum_screening_score)
    add_column :jobs, :screening_timeout, :integer, default: nil, null: true unless column_exists?(:jobs, :screening_timeout)
    add_column :jobs, :screening_max_attempts, :integer, default: nil, null: true unless column_exists?(:jobs, :screening_max_attempts)
    add_column :jobs, :screening_approve_limit, :integer, default: nil, null: true unless column_exists?(:jobs, :screening_approve_limit)
    add_column :jobs, :interview_minimum_score, :float, default: nil, null: true unless column_exists?(:jobs, :interview_minimum_score)
    add_column :jobs, :has_automatic_interview, :boolean, default: false unless column_exists?(:jobs, :has_automatic_interview)
    add_column :jobs, :interview_calendar_type, :integer, default: nil, null: true unless column_exists?(:jobs, :calendar_type)
    add_column :jobs, :interview_hours_range, :string, default: nil, null: true unless column_exists?(:jobs, :interview_hours_range)
    add_column :jobs, :interview_duration, :integer, default: nil, null: true unless column_exists?(:jobs, :interview_duration)
  end
end
