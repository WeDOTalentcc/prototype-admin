# frozen_string_literal: true

module Productivity
  class ShowService
    def initialize(user:, start_date: nil, end_date: nil)
      @user = user
      @start_date = start_date&.to_date || 30.days.ago.to_date
      @end_date = end_date&.to_date || Date.current
    end

    def call
      {
        user_id: @user.id,
        user_name: @user.name,
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s },
        jobs: jobs_metrics,
        applies: applies_metrics,
        interviews: interviews_metrics,
        evaluations: evaluations_metrics
      }
    end

    private

    def jobs_metrics
      user_jobs = Job.where(user_id: @user.id, is_deleted: false)
      period_jobs = user_jobs.where(created_at: period_range)

      closed_statuses = JobStatus.where(name: [ "Fechada (preenchida)", "Concluída" ]).pluck(:id)
      closed_in_period = user_jobs.where(job_status_id: closed_statuses)
                                   .joins(:activity_logs)
                                   .where(activity_logs: { created_at: period_range })
                                   .distinct
                                   .count

      {
        active: user_jobs.where(is_active: true, is_archived: false).count,
        created_in_period: period_jobs.count,
        closed_in_period: closed_in_period,
        avg_days_to_close: avg_days_to_close
      }
    end

    def applies_metrics
      scope = Apply.joins(:job)
                   .where(jobs: { user_id: @user.id })
                   .where(is_deleted: false)
                   .where(created_at: period_range)

      hired = scope.joins(:selective_process)
                   .where(selective_processes: { status: :hired })
                   .count

      {
        total_received: scope.count,
        hired: hired
      }
    end

    def interviews_metrics
      scope = Meeting.where(organizer_id: @user.id, is_deleted: false)

      period_scope = scope.where(start_time: period_range)
      no_shows = period_scope.where(sub_status: "no_show").count
      upcoming = scope.where("start_time > ? AND start_time <= ?", Time.current, 7.days.from_now).count

      {
        conducted: period_scope.where(sub_status: "completed").count,
        no_shows: no_shows,
        upcoming_week: upcoming
      }
    end

    def evaluations_metrics
      candidate_ids = Apply.joins(:job)
                           .where(jobs: { user_id: @user.id })
                           .pluck(:candidate_id)

      return { sent: 0, completed: 0, pending: 0 } if candidate_ids.empty?

      scope = EvaluationCandidate.where(is_deleted: false)
                                  .where(candidate_id: candidate_ids)
                                  .where(created_at: period_range)

      total = scope.count
      completed = scope.where(completed: true).count

      {
        sent: total,
        completed: completed,
        pending: total - completed
      }
    end

    def avg_days_to_close
      result = ActiveRecord::Base.connection.select_value(<<~SQL.squish)
        SELECT AVG(EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0)
        FROM jobs j
        INNER JOIN activity_logs al ON al.reference_type = 'Job'
          AND al.reference_id = j.id
          AND al.action = 'update'
        INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
        WHERE j.user_id = #{@user.id.to_i}
          AND j.is_deleted = false
          AND js.name IN ('Fechada (preenchida)', 'Concluída')
          AND j.created_at BETWEEN '#{@start_date}' AND '#{@end_date.end_of_day.iso8601}'
      SQL

      result&.to_f&.round(1)
    rescue StandardError
      nil
    end

    def period_range
      @start_date.beginning_of_day..@end_date.end_of_day
    end
  end
end
