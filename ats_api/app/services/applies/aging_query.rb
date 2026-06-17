# frozen_string_literal: true

module Applies
  class AgingQuery
    SEVERITY_THRESHOLDS = {
      critical: 5,
      warning: 3,
      attention: 2
    }.freeze

    def initialize(days: 3, status: nil, job_id: nil)
      @days = days
      @status = status
      @job_id = job_id
    end

    def call
      scope = build_scope
      scope = scope.where(selective_processes: { status: @status }) if @status.present?
      scope = scope.where(applies: { job_id: @job_id }) if @job_id.present?
      scope
    end

    def severity_counts
      base = build_base_scope
      base = base.where(selective_processes: { status: @status }) if @status.present?
      base = base.where(applies: { job_id: @job_id }) if @job_id.present?

      {
        critical: base.where("EXTRACT(DAY FROM NOW() - COALESCE(last_status.last_activity_at, applies.created_at)) >= ?", SEVERITY_THRESHOLDS[:critical]).count,
        warning: base.where("EXTRACT(DAY FROM NOW() - COALESCE(last_status.last_activity_at, applies.created_at)) BETWEEN ? AND ?", SEVERITY_THRESHOLDS[:warning], SEVERITY_THRESHOLDS[:critical] - 1).count,
        attention: base.where("EXTRACT(DAY FROM NOW() - COALESCE(last_status.last_activity_at, applies.created_at)) BETWEEN ? AND ?", SEVERITY_THRESHOLDS[:attention], SEVERITY_THRESHOLDS[:warning] - 1).count
      }
    end

    def stage_counts
      base = build_base_scope
      base = base.where(selective_processes: { status: @status }) if @status.present?
      base = base.where(applies: { job_id: @job_id }) if @job_id.present?

      status_map = SelectiveProcess.statuses.invert

      base.group("selective_processes.status")
          .count
          .transform_keys { |k| status_map[k] || k.to_s }
    end

    private

    def lateral_join_sql
      <<~SQL
        LEFT JOIN LATERAL (
          SELECT MAX(apply_statuses.created_at) as last_activity_at
          FROM apply_statuses
          WHERE apply_statuses.apply_id = applies.id
        ) last_status ON true
      SQL
    end

    def build_base_scope
      Apply.joins(:selective_process, :candidate, :job)
           .joins(lateral_join_sql)
           .where(applies: { is_deleted: false })
           .where.not(selective_processes: { status: [ :rejected, :hired ] })
           .where("COALESCE(last_status.last_activity_at, applies.created_at) < ?", @days.days.ago)
    end

    def build_scope
      build_base_scope
        .select(
          "applies.id",
          "applies.candidate_id",
          "applies.job_id",
          "applies.selective_process_id",
          "applies.cv_match",
          "applies.total_score",
          "applies.created_at",
          "candidates.name as candidate_name",
          "candidates.email as candidate_email",
          "jobs.title as job_title",
          "jobs.user_id as recruiter_id",
          "selective_processes.name as stage_name",
          "selective_processes.status as stage_status",
          "COALESCE(last_status.last_activity_at, applies.created_at) as last_activity_at",
          "EXTRACT(DAY FROM NOW() - COALESCE(last_status.last_activity_at, applies.created_at))::integer as days_in_stage"
        )
        .order(Arel.sql("days_in_stage DESC"))
    end
  end
end
