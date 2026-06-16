# frozen_string_literal: true

class AddIndexesForInsightsAgentEndpoints < ActiveRecord::Migration[7.1]
  def change
    add_index :applies, :created_at, where: "is_deleted = false",
              name: "idx_applies_created_at_not_deleted", if_not_exists: true

    add_index :apply_statuses, [ :apply_id, :created_at ],
              order: { created_at: :desc },
              name: "idx_apply_statuses_apply_id_created_at", if_not_exists: true

    add_index :apply_statuses, :created_at,
              order: { created_at: :desc },
              name: "idx_apply_statuses_created_at_desc", if_not_exists: true

    add_index :calendar_events, [ :start_time, :event_type ],
              where: "is_cancelled = false AND is_deleted = false",
              name: "idx_calendar_events_start_time_type_active", if_not_exists: true

    add_index :dispatch_messages, [ :recipient_type, :recipient_id ],
              name: "idx_dispatch_messages_recipient", if_not_exists: true

    add_index :evaluation_candidates, [ :candidate_id, :job_id ],
              name: "idx_evaluation_candidates_candidate_job", if_not_exists: true

    add_index :meetings, [ :start_time, :is_deleted ],
              name: "idx_meetings_start_time_not_deleted", if_not_exists: true
  end
end
