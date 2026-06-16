class CreateInterviewSchedulingTables < ActiveRecord::Migration[7.1]
  def change
    create_table :interviews, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255
      t.string :title, limit: 255
      t.text :description
      t.string :interview_type, limit: 50
      t.string :interview_mode, limit: 50, default: "video"
      t.string :candidate_id, limit: 255
      t.string :candidate_name, limit: 255
      t.string :candidate_email, limit: 255
      t.string :interviewer_name, limit: 255
      t.string :interviewer_email, limit: 255
      t.jsonb :additional_interviewers, default: []
      t.datetime :start_time
      t.datetime :end_time
      t.string :timezone, limit: 100, default: "America/Sao_Paulo"
      t.integer :duration_minutes
      t.string :location, limit: 500
      t.string :meeting_url, limit: 1000
      t.string :meeting_platform, limit: 50
      t.string :meeting_id, limit: 255
      t.string :graph_event_id, limit: 255
      t.string :graph_calendar_id, limit: 255
      t.string :graph_organizer_email, limit: 255
      t.boolean :is_synced_to_calendar, default: false
      t.text :calendar_sync_error
      t.datetime :last_synced_at
      t.string :google_event_id, limit: 255
      t.string :google_meet_link, limit: 500
      t.string :status, limit: 50, default: "scheduled"
      t.string :confirmation_status, limit: 50, default: "pending"
      t.boolean :reminder_sent, default: false
      t.datetime :reminder_sent_at
      t.boolean :confirmation_request_sent, default: false
      t.datetime :confirmation_request_sent_at
      t.string :job_vacancy_id, limit: 255
      t.string :job_title, limit: 255
      t.string :application_stage, limit: 100
      t.jsonb :feedback, default: {}
      t.text :interviewer_notes
      t.string :recording_url, limit: 1000
      t.jsonb :lia_preparation_notes, default: {}
      t.jsonb :lia_suggested_questions, default: []
      t.string :created_by, limit: 255
      t.datetime :cancelled_at
      t.text :cancellation_reason
      t.timestamps
    end

    add_index :interviews, :company_id
    add_index :interviews, :candidate_id
    add_index :interviews, :status
    add_index :interviews, :graph_event_id
    add_index :interviews, :google_event_id
    add_index :interviews, :start_time

    create_table :interview_feedbacks, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :interview_id, null: false
      t.string :interviewer_id, limit: 255
      t.string :interviewer_name, limit: 255
      t.jsonb :ratings, default: {}
      t.text :notes
      t.string :recommendation, limit: 50
      t.float :overall_score
      t.boolean :is_submitted, default: false
      t.timestamps
    end

    add_index :interview_feedbacks, :interview_id
    add_foreign_key :interview_feedbacks, :interviews

    create_table :interview_notes, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :interview_id, null: false
      t.string :author_id, limit: 255
      t.string :author_name, limit: 255
      t.text :content
      t.boolean :is_private, default: false
      t.timestamps
    end

    add_index :interview_notes, :interview_id
    add_foreign_key :interview_notes, :interviews

    create_table :calendar_availability, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :user_id, limit: 255, null: false
      t.string :company_id, limit: 255
      t.integer :day_of_week
      t.time :start_time
      t.time :end_time
      t.string :timezone, limit: 100, default: "America/Sao_Paulo"
      t.boolean :is_active, default: true
      t.timestamps
    end

    add_index :calendar_availability, :user_id

    create_table :self_scheduling_links, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :interview_id
      t.string :token, limit: 255, null: false
      t.datetime :expires_at
      t.jsonb :available_slots, default: []
      t.string :status, limit: 50, default: "active"
      t.datetime :selected_at
      t.timestamps
    end

    add_index :self_scheduling_links, :token, unique: true

    create_table :reschedule_history, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :interview_id, null: false
      t.datetime :old_start_time
      t.datetime :new_start_time
      t.text :reason
      t.string :initiated_by, limit: 255
      t.timestamps
    end

    add_index :reschedule_history, :interview_id
    add_foreign_key :reschedule_history, :interviews

    create_table :interview_reminders, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :interview_id, null: false
      t.string :reminder_type, limit: 50
      t.string :channel, limit: 50, default: "email"
      t.datetime :send_at
      t.datetime :sent_at
      t.string :status, limit: 50, default: "pending"
      t.timestamps
    end

    add_index :interview_reminders, :interview_id
    add_foreign_key :interview_reminders, :interviews
  end
end
