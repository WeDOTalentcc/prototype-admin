# frozen_string_literal: true

module Candidates
  class CommunicationsService
    def initialize(candidate:)
      @candidate = candidate
    end

    def call
      communications = []
      communications.concat(fetch_dispatches)
      communications.concat(fetch_evaluations)
      communications.concat(fetch_interviews)
      communications.concat(fetch_pipeline_changes)

      sorted = communications.sort_by { |c| c[:date] || Time.at(0) }.reverse

      {
        candidate_id: @candidate.id,
        candidate_name: @candidate.name,
        communications: sorted,
        summary: build_summary(sorted)
      }
    end

    private

    def fetch_dispatches
      DispatchMessage.joins(:dispatch)
                     .where(recipient_type: "Candidate", recipient_id: @candidate.id)
                     .select(
                       "dispatches.channel_type",
                       "dispatches.subject",
                       "dispatch_messages.status",
                       "dispatch_messages.sent_at",
                       "dispatch_messages.opened_at",
                       "dispatch_messages.created_at"
                     )
                     .order("dispatch_messages.created_at DESC")
                     .map do |dm|
                       {
                         type: "dispatch",
                         channel: dm.channel_type,
                         subject: dm.subject,
                         status: dm.status,
                         direction: "outbound",
                         sent_at: dm.sent_at,
                         opened_at: dm.opened_at,
                         date: dm.sent_at || dm.created_at
                       }
                     end
    end

    def fetch_evaluations
      EvaluationCandidate.where(candidate_id: @candidate.id)
                         .joins(:evaluation)
                         .select(
                           "evaluations.name as evaluation_name",
                           "evaluation_candidates.completed",
                           "evaluation_candidates.created_at",
                           "evaluation_candidates.updated_at"
                         )
                         .order("evaluation_candidates.created_at DESC")
                         .map do |ec|
                           {
                             type: "evaluation_sent",
                             evaluation_name: ec.evaluation_name,
                             status: ec.completed ? "completed" : "pending",
                             direction: "outbound",
                             sent_at: ec.created_at,
                             completed_at: ec.completed ? ec.updated_at : nil,
                             date: ec.created_at
                           }
                         end
    end

    def fetch_interviews
      candidate_apply_ids = Apply.where(candidate_id: @candidate.id, is_deleted: false).pluck(:id)
      return [] if candidate_apply_ids.empty?

      CalendarEvent.where(apply_id: candidate_apply_ids, event_type: "interview")
                   .where(is_deleted: false, is_cancelled: false)
                   .select(:start_time, :provider, :sub_status, :title)
                   .order(start_time: :desc)
                   .map do |ce|
                     {
                       type: "interview",
                       title: ce.title,
                       provider: ce.provider,
                       status: ce.sub_status || "scheduled",
                       scheduled_at: ce.start_time,
                       date: ce.start_time
                     }
                   end
    end

    def fetch_pipeline_changes
      apply_ids = Apply.where(candidate_id: @candidate.id, is_deleted: false).pluck(:id)
      return [] if apply_ids.empty?

      ApplyStatus.where(apply_id: apply_ids)
                 .joins(:selective_process)
                 .joins("LEFT JOIN users ON apply_statuses.user_id = users.id")
                 .select(
                   "selective_processes.name as stage_name",
                   "users.name as changed_by",
                   "apply_statuses.created_at"
                 )
                 .order("apply_statuses.created_at DESC")
                 .map do |as|
                   {
                     type: "pipeline_change",
                     to_stage: as.stage_name,
                     changed_by: as.try(:changed_by),
                     changed_at: as.created_at,
                     date: as.created_at
                   }
                 end
    end

    def build_summary(communications)
      outbound = communications.select { |c| c[:direction] == "outbound" }
      inbound = communications.select { |c| c[:type] == "evaluation_sent" && c[:status] == "completed" }

      last_outbound = outbound.first
      last_inbound = inbound.first

      {
        total_communications: communications.size,
        last_outbound_at: last_outbound&.dig(:sent_at),
        last_inbound_at: last_inbound&.dig(:completed_at),
        days_since_last_contact: last_outbound ? ((Time.current - (last_outbound[:date] || Time.current)) / 1.day).round : nil
      }
    end
  end
end
