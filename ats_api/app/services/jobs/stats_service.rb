# frozen_string_literal: true

module Jobs
  class StatsService
    def initialize(account_id:, start_date: nil, end_date: nil)
      @account_id = account_id
      @start_date = start_date&.to_date || 30.days.ago.to_date
      @end_date = end_date&.to_date || Date.current
    end

    def call
      result = {
        by_status: jobs_by_status,
        open_vs_closed: open_vs_closed,
        avg_days_to_close: avg_days_to_close,
        created_per_week: created_per_week,
        by_department: by_department,
        by_priority: by_priority,
        by_urgency: by_urgency,
        by_workplace_type: by_workplace_type,
        top_hiring_managers: top_hiring_managers,
        top_recruiters_by_speed: top_recruiters_by_speed,
        totals: totals,
        stale_jobs: stale_jobs,
        jobs_ranking: jobs_ranking,
        period: { start_date: start_date, end_date: end_date }
      }

      result
    end

    private

    attr_reader :account_id, :start_date, :end_date

    def base_scope
      Job.where(account_id: account_id, is_deleted: false)
    end

    def period_scope
      base_scope.where(created_at: start_date.beginning_of_day..end_date.end_of_day)
    end

    def jobs_by_status
      base_scope
        .joins("LEFT JOIN job_statuses ON job_statuses.id = jobs.job_status_id")
        .group("job_statuses.name", "job_statuses.color")
        .count
        .map { |(name, color), count| { status: name || "Sem status", color: color, count: count } }
    end

    def open_vs_closed
      closed_names = [ "Fechada (preenchida)", "Fechada (expirada)", "Cancelada", "Concluída" ]
      closed_ids = JobStatus.where(name: closed_names).pluck(:id)

      scope = period_scope
      total = scope.count
      closed = scope.where(job_status_id: closed_ids).count

      { open: total - closed, closed: closed, total: total }
    end

    def avg_days_to_close
      result = ActiveRecord::Base.connection.select_value(<<~SQL)
        SELECT AVG(EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0)
        FROM jobs j
        INNER JOIN activity_logs al ON al.reference_type = 'Job'
          AND al.reference_id = j.id
          AND al.action = 'update'
        INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
        WHERE j.account_id = #{account_id.to_i}
          AND j.is_deleted = false
          AND js.name IN ('Fechada (preenchida)', 'Fechada (expirada)', 'Concluída')
          AND j.created_at BETWEEN '#{start_date}' AND '#{end_date.end_of_day.iso8601}'
      SQL

      result&.to_f&.round(1)
    rescue StandardError
      nil
    end

    def created_per_week
      period_scope
        .group("DATE_TRUNC('week', jobs.created_at)")
        .order(Arel.sql("DATE_TRUNC('week', jobs.created_at)"))
        .count
        .map { |week, count| { week: week.to_date, count: count } }
    end

    def by_department
      base_scope
        .joins("LEFT JOIN departments ON departments.id = jobs.department_id")
        .group("departments.name")
        .order("count_all DESC")
        .limit(15)
        .count
        .map { |name, count| { department: name || "Sem departamento", count: count } }
    end

    def by_priority
      base_scope
        .group(:priority)
        .count
        .map do |priority, count|
          label = Job::PRIORITY.find { |p| p["id"] == priority }&.dig("name") || "Não informado"
          { priority: label, count: count }
        end
    end

    def by_urgency
      base_scope
        .group(:urgency_level)
        .count
        .map do |level, count|
          label = Job::URGENCY_LEVEL.find { |u| u["id"] == level }&.dig("name") || "Não informado"
          { urgency: label, count: count }
        end
    end

    def by_workplace_type
      base_scope
        .group(:workplace_type)
        .count
        .map do |wt, count|
          label = Job::WORKPLACE_TYPES.find { |w| w["id"].to_s == wt.to_s }&.dig("name") || "Não informado"
          { workplace_type: label, count: count }
        end
    end

    def top_hiring_managers
      base_scope
        .where.not(hiring_manager_id: nil)
        .joins("INNER JOIN users ON users.id = jobs.hiring_manager_id")
        .group("users.id", "users.name", "users.email")
        .order("count_all DESC")
        .limit(10)
        .count
        .map { |(id, name, email), count| { user_id: id, name: name, email: email, count: count } }
    end

    def totals
      scope = base_scope
      {
        total: scope.count,
        active: scope.where(is_active: true).count,
        archived: scope.where(is_archived: true).count,
        created_in_period: period_scope.count
      }
    end

    def stale_jobs(days_threshold: 30)
      rows = ActiveRecord::Base.connection.select_all(
        sanitized_stale_jobs_sql(days_threshold)
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

    def jobs_ranking(limit: 10)
      {
        most_applies: most_applies_ranking(limit),
        longest_open: longest_open_ranking(limit),
        fastest_closed: fastest_closed_ranking(limit)
      }
    end

    def top_recruiters_by_speed
      closed_names = [ "Fechada (preenchida)", "Concluída" ]
      closed_ids = JobStatus.where(name: closed_names).pluck(:id)
      return [] if closed_ids.empty?

      rows = ActiveRecord::Base.connection.select_all(
        sanitized_recruiters_by_speed_sql(closed_ids)
      )

      rows.map do |row|
        {
          user_id: row["user_id"],
          name: row["user_name"],
          jobs_closed: row["jobs_closed"],
          avg_days_to_close: row["avg_days_to_close"]&.to_f&.round(1)
        }
      end
    rescue StandardError
      []
    end

    def most_applies_ranking(limit)
      base_scope
        .where(is_active: true, is_archived: false)
        .joins("LEFT JOIN applies ON applies.job_id = jobs.id AND applies.is_deleted = false")
        .group("jobs.id", "jobs.title")
        .order(Arel.sql("COUNT(applies.id) DESC"))
        .limit(limit)
        .pluck("jobs.id", "jobs.title", Arel.sql("COUNT(applies.id)"))
        .map { |id, title, count| { job_id: id, title: title, applies_count: count } }
    end

    def longest_open_ranking(limit)
      base_scope
        .where(is_active: true, is_archived: false)
        .order(:created_at)
        .limit(limit)
        .pluck(:id, :title, :created_at)
        .map { |id, title, created| { job_id: id, title: title, days_open: ((Time.current - created) / 1.day).to_i } }
    end

    def fastest_closed_ranking(limit)
      closed_names = [ "Fechada (preenchida)", "Concluída" ]
      closed_ids = JobStatus.where(name: closed_names).pluck(:id)
      return [] if closed_ids.empty?

      rows = ActiveRecord::Base.connection.select_all(
        sanitized_fastest_closed_sql(closed_ids, limit)
      )

      rows.map do |row|
        {
          job_id: row["id"],
          title: row["title"],
          days_to_close: row["days_to_close"]&.to_f&.round(1)
        }
      end
    rescue StandardError
      []
    end

    def sanitized_stale_jobs_sql(days_threshold)
      ActiveRecord::Base.sanitize_sql_array([
        <<~SQL, account_id, days_threshold
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
    end

    def sanitized_recruiters_by_speed_sql(closed_ids)
      ActiveRecord::Base.sanitize_sql_array([
        <<~SQL, account_id, closed_ids, start_date, end_date.end_of_day
          SELECT
            ju.user_id,
            u.name AS user_name,
            COUNT(DISTINCT j.id) AS jobs_closed,
            AVG(EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0) AS avg_days_to_close
          FROM job_users ju
          INNER JOIN jobs j ON j.id = ju.job_id
          INNER JOIN users u ON u.id = ju.user_id
          INNER JOIN activity_logs al ON al.reference_type = 'Job'
            AND al.reference_id = j.id
            AND al.action = 'update'
          INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
          WHERE j.account_id = ?
            AND j.is_deleted = false
            AND js.id IN (?)
            AND j.created_at BETWEEN ? AND ?
          GROUP BY ju.user_id, u.name
          HAVING COUNT(DISTINCT j.id) >= 1
          ORDER BY avg_days_to_close ASC
          LIMIT 10
        SQL
      ])
    end

    def sanitized_fastest_closed_sql(closed_ids, limit)
      ActiveRecord::Base.sanitize_sql_array([
        <<~SQL, account_id, closed_ids, start_date, end_date.end_of_day, limit
          SELECT j.id, j.title,
            EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0 AS days_to_close
          FROM jobs j
          INNER JOIN activity_logs al ON al.reference_type = 'Job'
            AND al.reference_id = j.id
            AND al.action = 'update'
          INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
          WHERE j.account_id = ?
            AND j.is_deleted = false
            AND js.id IN (?)
            AND j.created_at BETWEEN ? AND ?
          ORDER BY days_to_close ASC
          LIMIT ?
        SQL
      ])
    end
  end
end
