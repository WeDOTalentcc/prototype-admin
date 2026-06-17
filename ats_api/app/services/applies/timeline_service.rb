# frozen_string_literal: true

module Applies
  class TimelineService
    def initialize(apply:)
      @apply = apply
    end

    def call
      events = []
      events << creation_event
      events.concat(stage_change_events)
      events.concat(evaluation_events)
      events.concat(interview_events)
      events.concat(dispatch_events)

      {
        apply_id: @apply.id,
        candidate_name: @apply.candidate.name,
        job_title: @apply.job.title,
        current_stage: @apply.selective_process&.name,
        created_at: @apply.created_at,
        timeline: events.sort_by { |e| e[:timestamp] },
        summary: build_summary(events)
      }
    end

    private

    def creation_event
      {
        timestamp: @apply.created_at,
        type: "apply_created",
        description: "Candidatura recebida via #{@apply.candidate.source || 'sistema'}",
        actor: "system"
      }
    end

    def stage_change_events
      @apply.apply_statuses
            .joins(:selective_process)
            .joins("LEFT JOIN users ON apply_statuses.user_id = users.id")
            .select(
              "apply_statuses.created_at",
              "selective_processes.name as stage_name",
              "selective_processes.status as stage_status",
              "users.name as actor_name"
            )
            .order("apply_statuses.created_at ASC")
            .map { |as| format_stage_change(as) }
    end

    def evaluation_events
      EvaluationCandidate.where(apply_id: @apply.id)
                         .joins(:evaluation)
                         .joins("LEFT JOIN users ON evaluation_candidates.user_id = users.id")
                         .select(
                           "evaluation_candidates.created_at",
                           "evaluation_candidates.updated_at",
                           "evaluation_candidates.completed",
                           "evaluation_candidates.score",
                           "evaluation_candidates.wsi_classification",
                           "evaluations.name as evaluation_name",
                           "users.name as actor_name"
                         )
                         .flat_map { |ec| format_evaluation(ec) }
    end

    def interview_events
      CalendarEvent.where(apply_id: @apply.id, event_type: "interview")
                   .where(is_deleted: false, is_cancelled: false)
                   .joins("LEFT JOIN users ON calendar_events.organizer_id = users.id")
                   .select(
                     "calendar_events.start_time",
                     "calendar_events.provider",
                     "calendar_events.sub_status",
                     "calendar_events.title",
                     "users.name as organizer_name"
                   )
                   .order(:start_time)
                   .map { |ce| format_interview(ce) }
    end

    def dispatch_events
      DispatchMessage.joins(:dispatch)
                     .where(recipient_type: "Candidate", recipient_id: @apply.candidate_id)
                     .select(
                       "dispatches.channel_type",
                       "dispatches.subject",
                       "dispatch_messages.status",
                       "dispatch_messages.sent_at",
                       "dispatch_messages.opened_at"
                     )
                     .order("dispatch_messages.sent_at ASC NULLS LAST")
                     .map { |dm| format_dispatch(dm) }
    end

    def format_stage_change(record)
      {
        timestamp: record.created_at,
        type: "stage_change",
        to: record.stage_name,
        stage_status: record.stage_status,
        actor: record.actor_name || "system"
      }
    end

    def format_evaluation(record)
      events = [ {
        timestamp: record.created_at,
        type: "evaluation_sent",
        evaluation: record.evaluation_name,
        actor: record.actor_name || "system"
      } ]

      if record.completed
        events << {
          timestamp: record.updated_at,
          type: "evaluation_completed",
          evaluation: record.evaluation_name,
          score: record.score&.to_f,
          classification: record.wsi_classification
        }
      end

      events
    end

    def format_interview(record)
      {
        timestamp: record.start_time,
        type: "interview_scheduled",
        title: record.title,
        provider: record.provider,
        sub_status: record.sub_status,
        interviewer: record.organizer_name
      }
    end

    def format_dispatch(record)
      {
        timestamp: record.sent_at || record.created_at,
        type: "dispatch_sent",
        channel: record.channel_type,
        subject: record.subject,
        status: record.status
      }
    end

    def build_summary(events)
      {
        days_in_pipeline: ((Time.current - @apply.created_at) / 1.day).round,
        stages_visited: events.count { |e| e[:type] == "stage_change" } + 1,
        evaluations_completed: events.count { |e| e[:type] == "evaluation_completed" },
        interviews_scheduled: events.count { |e| e[:type] == "interview_scheduled" }
      }
    end
  end
end
