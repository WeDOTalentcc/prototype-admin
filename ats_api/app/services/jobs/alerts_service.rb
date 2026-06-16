# frozen_string_literal: true

module Jobs
  class AlertsService
    def initialize(account_id:)
      @account_id = account_id
    end

    def call
      alerts = {
        deadline_expired: deadline_expired_jobs,
        deadline_soon: deadline_soon_jobs(days: 7),
        urgent_without_finalists: urgent_without_finalists,
        stale: stale_active_jobs(days: 30),
        no_applies: active_jobs_without_applies,
        chat_abandonment: chat_abandonment(hours: 4)
      }

      total = alerts.values.sum { |v| v.is_a?(Array) ? v.size : 0 }
      alerts[:summary] = { total_alerts: total }

      alerts
    end

    private

    def base_scope
      Job.where(account_id: @account_id, is_deleted: false, is_active: true, is_archived: false)
    end

    def deadline_expired_jobs
      base_scope
        .where("closing_deadline < ?", Date.current)
        .order(:closing_deadline)
        .limit(20)
        .pluck(:id, :title, :closing_deadline, :urgency_level)
        .map { |id, title, deadline, urgency| { job_id: id, title: title, closing_deadline: deadline, urgency_level: urgency } }
    end

    def deadline_soon_jobs(days:)
      base_scope
        .where(closing_deadline: Date.current..days.days.from_now.to_date)
        .order(:closing_deadline)
        .limit(20)
        .pluck(:id, :title, :closing_deadline)
        .map { |id, title, deadline| { job_id: id, title: title, closing_deadline: deadline, days_remaining: (deadline - Date.current).to_i } }
    end

    def urgent_without_finalists
      final_stage_ids = SelectiveProcess.where(status: [ :hired, :interview ]).pluck(:id)
      urgent_ids = base_scope.where("is_urgent = true OR urgency_level >= 4").pluck(:id)
      return [] if urgent_ids.empty?

      jobs_with_finalists = Apply
        .where(job_id: urgent_ids, selective_process_id: final_stage_ids, is_deleted: false)
        .distinct
        .pluck(:job_id)

      missing_ids = urgent_ids - jobs_with_finalists
      return [] if missing_ids.empty?

      base_scope
        .where(id: missing_ids)
        .limit(20)
        .pluck(:id, :title, :urgency_level)
        .map { |id, title, urgency| { job_id: id, title: title, urgency_level: urgency } }
    end

    def stale_active_jobs(days:)
      rows = ActiveRecord::Base.connection.select_all(
        ActiveRecord::Base.sanitize_sql_array([
          <<~SQL, @account_id, days
            SELECT j.id, j.title,
              COALESCE(
                (SELECT MAX(ast.created_at) FROM apply_statuses ast
                 INNER JOIN applies a ON a.id = ast.apply_id
                 WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
                j.created_at
              ) AS last_activity_at
            FROM jobs j
            WHERE j.account_id = ?
              AND j.is_deleted = false
              AND j.is_active = true
              AND j.is_archived = false
              AND COALESCE(
                (SELECT MAX(ast.created_at) FROM apply_statuses ast
                 INNER JOIN applies a ON a.id = ast.apply_id
                 WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
                j.created_at
              ) < NOW() - INTERVAL '1 day' * ?
            ORDER BY last_activity_at ASC
            LIMIT 20
          SQL
        ])
      )

      rows.map do |row|
        {
          job_id: row["id"],
          title: row["title"],
          last_activity_at: row["last_activity_at"],
          days_inactive: row["last_activity_at"] ? ((Time.current - row["last_activity_at"].to_time) / 1.day).to_i : nil
        }
      end
    rescue StandardError
      []
    end

    def chat_abandonment(hours:)
      EvaluationCandidate
        .where(completed: false)
        .where(declined_at: nil)
        .where.not(session_status: %w[closed timeout])
        .where("evaluation_candidates.updated_at < ?", hours.hours.ago)
        .joins(:candidate)
        .joins("INNER JOIN jobs ON evaluation_candidates.job_id = jobs.id")
        .where(jobs: { account_id: @account_id, is_deleted: false, is_active: true })
        .order("evaluation_candidates.updated_at ASC")
        .limit(20)
        .pluck(
          "evaluation_candidates.id",
          "candidates.name",
          "jobs.title",
          "evaluation_candidates.updated_at"
        )
        .map do |id, name, title, updated|
          {
            evaluation_candidate_id: id,
            candidate_name: name,
            job_title: title,
            last_activity_at: updated,
            hours_inactive: ((Time.current - updated) / 1.hour).round(1)
          }
        end
    rescue StandardError
      []
    end

    def active_jobs_without_applies
      base_scope
        .left_joins(:applies)
        .where(applies: { id: nil })
        .order(:created_at)
        .limit(20)
        .pluck(:id, :title, :created_at)
        .map { |id, title, created| { job_id: id, title: title, days_open: ((Time.current - created) / 1.day).to_i } }
    end
  end
end
