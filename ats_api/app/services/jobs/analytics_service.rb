# frozen_string_literal: true

module Jobs
  class AnalyticsService
    CACHE_PREFIX = "job_analytics"
    CACHE_TTL = 10.minutes

    SCORE_RANGES = {
      "0-20" => 0..20,
      "21-40" => 21..40,
      "41-60" => 41..60,
      "61-80" => 61..80,
      "81-100" => 81..100
    }.freeze

    def self.cache_key(job_id)
      "#{CACHE_PREFIX}:#{job_id}"
    end

    def initialize(job:, force_refresh: false)
      @job = job
      @force_refresh = force_refresh
    end

    def call
      return cached_data unless @force_refresh || cached_data.nil?

      data = compute_analytics
      persist_snapshot(data)
      write_cache(data)
      data
    end

    private

    attr_reader :job

    def cached_data
      @cached_data ||= Rails.cache.read(cache_key)
    end

    def cache_key
      self.class.cache_key(job.id)
    end

    def write_cache(data)
      Rails.cache.write(cache_key, data, expires_in: CACHE_TTL)
    end

    def persist_snapshot(data)
      snapshot = JobAnalyticsSnapshot.find_or_initialize_by(job_id: job.id)
      snapshot.update!(snapshot_data: data, computed_at: Time.current, version: (snapshot.version || 0) + 1)
    rescue StandardError => e
      Rails.logger.error "[Jobs::AnalyticsService] Failed to persist snapshot for Job##{job.id}: #{e.message}"
    end

    def compute_analytics
      applies_scope = active_applies
      apply_ids = applies_scope.pluck(:id)

      {
        overview: build_overview(applies_scope),
        funnel: build_funnel(apply_ids),
        velocity: build_velocity(apply_ids, applies_scope),
        quality: build_quality(apply_ids, applies_scope),
        sources: build_sources(applies_scope),
        engagement: build_engagement(apply_ids),
        scheduling: build_scheduling(apply_ids),
        team_activity: build_team_activity(apply_ids),
        computed_at: Time.current.iso8601
      }
    end

    def active_applies
      job.applies.where(is_deleted: false)
    end

    def selective_processes
      @selective_processes ||= job.selective_processes.where(is_deleted: false).order(:position)
    end

    def build_overview(applies_scope)
      total = applies_scope.count

      {
        total_applies: total,
        active_applies: total,
        days_since_published: days_since(job.published_date),
        days_since_created: days_since(job.created_at),
        days_until_deadline: days_until(job.application_deadline),
        is_deadline_expired: job.application_deadline.present? && job.application_deadline < Time.current,
        is_active: job.is_active,
        is_archived: job.is_archived
      }
    end

    def build_funnel(apply_ids)
      sp_list = selective_processes.to_a

      if apply_ids.empty?
        stages = sp_list.map { |sp| format_stage(sp, {}) }
        return { stages: stages, overall_conversion_rate: 0, bottleneck_stage: nil, avg_total_pipeline_days: nil }
      end

      transitions = load_transitions(apply_ids)
      stage_metrics = compute_stage_metrics(transitions)
      sp_list = selective_processes.to_a

      stages = sp_list.map { |sp| format_stage(sp, stage_metrics) }

      first_stage_entered = stages.first&.dig(:total_entered) || 0
      last_stage_count = stages.select { |s| s[:status] == "hired" }.sum { |s| s[:current_count] }

      bottleneck = find_bottleneck(stages)

      pipeline_days = compute_avg_pipeline_days(transitions)

      {
        stages: stages,
        overall_conversion_rate: safe_percentage(last_stage_count, first_stage_entered),
        bottleneck_stage: bottleneck,
        avg_total_pipeline_days: pipeline_days
      }
    end

    def build_velocity(apply_ids, applies_scope)
      return empty_velocity if apply_ids.empty?

      first_actions = first_action_times(apply_ids)
      avg_first_action = average_hours(first_actions)

      stage_arrival = stage_arrival_times(apply_ids)

      total_days = applies_scope.exists? ? ((Time.current - applies_scope.minimum(:created_at)) / 1.day).ceil : 1
      total_days = [ total_days, 1 ].max

      trend = compute_weekly_trend(applies_scope)

      {
        avg_time_to_first_action_hours: avg_first_action,
        avg_time_to_screening_hours: stage_arrival[:screening],
        avg_time_to_interview_hours: stage_arrival[:interview],
        applies_per_day: (applies_scope.count.to_f / total_days).round(2),
        applies_trend: trend
      }
    end

    def build_quality(apply_ids, applies_scope)
      return empty_quality if apply_ids.empty?

      cv_matches = applies_scope.where("cv_match > 0").pluck(:cv_match)
      total_scores = applies_scope.where("total_score > 0").pluck(:total_score)

      score_distribution = build_score_distribution(cv_matches)

      eval_stats = compute_evaluation_stats(apply_ids)

      status_breakdown = applies_scope
        .group(:selective_process_status)
        .count

      {
        avg_cv_match: safe_average(cv_matches),
        avg_total_score: safe_average(total_scores),
        score_distribution: score_distribution,
        evaluation_stats: eval_stats,
        status_breakdown: status_breakdown
      }
    end

    def build_sources(applies_scope)
      source_data = applies_scope
        .joins(:candidate)
        .group("candidates.source")
        .count

      total = source_data.values.sum
      by_source = source_data.map do |source, count|
        { source: source.presence || "direct", count: count, percentage: safe_percentage(count, total) }
      end.sort_by { |s| -s[:count] }

      {
        by_source: by_source,
        by_career_page: {
          career_page_name: job.career_page_name,
          count: applies_scope.count
        }
      }
    end

    def build_engagement(apply_ids)
      return empty_engagement if apply_ids.empty?

      dispatches = Dispatch.where(reference_type: "Job", reference_id: job.id)
      dispatch_count = dispatches.count
      dispatch_by_channel = dispatches.group(:channel_type).count

      message_count = Message.where(apply_id: apply_ids, is_deleted: false).count
      candidates_with_messages = Message.where(apply_id: apply_ids, is_deleted: false)
        .distinct.count(:apply_id)
      avg_messages = apply_ids.size.positive? ? (message_count.to_f / apply_ids.size).round(2) : 0

      feedbacks = CandidateFeedback.where(job_id: job.id, is_deleted: false)
      feedback_by_type = feedbacks.group(:feedback_type).count

      {
        total_dispatches: dispatch_count,
        dispatch_breakdown: dispatch_by_channel,
        total_messages: message_count,
        avg_messages_per_candidate: avg_messages,
        candidates_with_feedback: feedbacks.distinct.count(:candidate_id),
        feedback_breakdown: feedback_by_type
      }
    end

    def build_scheduling(apply_ids)
      return empty_scheduling if apply_ids.empty?

      events = CalendarEvent.where(job_id: job.id, is_deleted: false)
      total = events.count

      {
        total_interviews_scheduled: total,
        interviews_completed: events.where(sub_status: "completed").count,
        interviews_cancelled: events.where(is_cancelled: true).count,
        interviews_pending: events.where(sub_status: %w[invite_sent scheduled confirmed]).where(is_cancelled: false).count,
        sub_status_breakdown: events.group(:sub_status).count,
        no_show_count: events.where(sub_status: "no_show").count
      }
    end

    def build_team_activity(apply_ids)
      return empty_team_activity if apply_ids.empty?

      status_actions = ApplyStatus
        .where(apply_id: apply_ids, is_deleted: false)
        .where.not(user_id: nil)
        .group(:user_id)
        .count

      user_ids = status_actions.keys
      users = User.where(id: user_ids).index_by(&:id)

      last_actions = ApplyStatus
        .where(apply_id: apply_ids, is_deleted: false)
        .where(user_id: user_ids)
        .group(:user_id)
        .maximum(:created_at)

      evaluations_by_user = EvaluationCandidate
        .where(job_id: job.id)
        .where.not(user_id: nil)
        .group(:user_id)
        .count

      actions_by_user = user_ids.map do |uid|
        user = users[uid]
        {
          user_id: uid,
          user_name: user&.name || "Unknown",
          applies_moved: status_actions[uid] || 0,
          evaluations_done: evaluations_by_user[uid] || 0,
          last_action_at: last_actions[uid]&.iso8601
        }
      end.sort_by { |u| -u[:applies_moved] }

      inactive_count = Apply
        .where(id: apply_ids)
        .where("applies.updated_at < ?", 7.days.ago)
        .count

      {
        actions_by_user: actions_by_user,
        inactive_applies_7d: inactive_count
      }
    end

    def load_transitions(apply_ids)
      ApplyStatus
        .where(apply_id: apply_ids, is_deleted: false)
        .joins("INNER JOIN selective_processes ON selective_processes.id = apply_statuses.selective_process_id")
        .select(
          "apply_statuses.apply_id",
          "apply_statuses.selective_process_id",
          "apply_statuses.created_at",
          "selective_processes.name AS stage_name",
          "selective_processes.position AS stage_position",
          "selective_processes.status AS stage_status"
        )
        .order("apply_statuses.apply_id, apply_statuses.created_at")
    end

    def compute_stage_metrics(transitions)
      metrics = Hash.new { |h, k| h[k] = { times: [], entered: 0, exited: 0 } }
      current_stage_counts = active_applies.group(:selective_process_id).count

      by_apply = transitions.group_by(&:apply_id)

      by_apply.each_value do |statuses|
        statuses.each_cons(2) do |current, nxt|
          duration_hours = (nxt.created_at - current.created_at) / 1.hour
          metrics[current.selective_process_id][:times] << duration_hours
          metrics[current.selective_process_id][:exited] += 1
        end

        statuses.each do |s|
          metrics[s.selective_process_id][:entered] += 1
        end
      end

      metrics.each_key do |sp_id|
        metrics[sp_id][:current_count] = current_stage_counts[sp_id] || 0
      end

      metrics
    end

    def format_stage(sp, stage_metrics)
      m = stage_metrics.fetch(sp.id, { times: [], entered: 0, exited: 0, current_count: 0 })
      times = m[:times] || []
      entered = m[:entered] || 0
      exited = m[:exited] || 0
      current = m[:current_count] || 0

      {
        selective_process_id: sp.id,
        name: sp.name,
        position: sp.position,
        status: sp.status,
        color: sp.color,
        current_count: current,
        total_entered: entered,
        total_exited: exited,
        conversion_rate: entered.positive? ? safe_percentage(exited, entered) : 0,
        avg_time_in_stage_hours: safe_average(times),
        median_time_in_stage_hours: percentile(times, 50),
        min_time_in_stage_hours: times.any? ? times.min.round(2) : nil,
        max_time_in_stage_hours: times.any? ? times.max.round(2) : nil
      }
    end

    def find_bottleneck(stages)
      advancing_stages = stages.reject { |s| s[:status].to_s.in?(%w[rejected hired]) }
      return nil if advancing_stages.empty?

      bottleneck = advancing_stages.min_by { |s| s[:conversion_rate] }
      bottleneck[:name]
    end

    def compute_avg_pipeline_days(transitions)
      by_apply = transitions.group_by(&:apply_id)
      return nil if by_apply.empty?

      durations = by_apply.map do |_apply_id, statuses|
        next nil if statuses.size < 2

        (statuses.last.created_at - statuses.first.created_at) / 1.day
      end.compact

      return nil if durations.empty?

      (durations.sum / durations.size).round(2)
    end

    def first_action_times(apply_ids)
      rows = ActiveRecord::Base.connection.select_all(<<~SQL)
        SELECT
          a.id AS apply_id,
          EXTRACT(EPOCH FROM (MIN(ast.created_at) - a.created_at)) / 3600.0 AS hours_to_first_action
        FROM applies a
        INNER JOIN apply_statuses ast ON ast.apply_id = a.id AND ast.is_deleted = false
        WHERE a.id IN (#{sanitize_ids(apply_ids)})
        GROUP BY a.id
        HAVING COUNT(ast.id) > 1
      SQL

      rows.map { |r| r["hours_to_first_action"].to_f }
    end

    def stage_arrival_times(apply_ids)
      rows = ActiveRecord::Base.connection.select_all(<<~SQL)
        SELECT
          sp.status AS stage_status,
          AVG(EXTRACT(EPOCH FROM (ast.created_at - a.created_at)) / 3600.0) AS avg_hours
        FROM apply_statuses ast
        INNER JOIN applies a ON a.id = ast.apply_id
        INNER JOIN selective_processes sp ON sp.id = ast.selective_process_id
        WHERE ast.apply_id IN (#{sanitize_ids(apply_ids)})
          AND ast.is_deleted = false
          AND sp.status IN (1, 2)
        GROUP BY sp.status
      SQL

      result = { screening: nil, interview: nil }
      rows.each do |r|
        case r["stage_status"].to_i
        when 1 then result[:screening] = r["avg_hours"].to_f.round(2)
        when 2 then result[:interview] = r["avg_hours"].to_f.round(2)
        end
      end
      result
    end

    def compute_evaluation_stats(apply_ids)
      evals = EvaluationCandidate.where(job_id: job.id)

      total = evals.count
      completed = evals.where(completed: true).count
      pending = evals.where(completed: false).count
      scores = evals.where("score > 0").pluck(:score)

      screening = evals.where(is_screening: true)
      screening_scores = screening.where("score > 0").pluck(:score)
      screening_total = screening.count
      screening_passed = screening.where("score >= ?", job.minimum_screening_score || 0).where(completed: true).count

      {
        total_evaluated: total,
        avg_score: safe_average(scores),
        completed_count: completed,
        pending_count: pending,
        screening_stats: {
          total: screening_total,
          avg_score: safe_average(screening_scores),
          pass_rate: safe_percentage(screening_passed, screening_total)
        }
      }
    end

    def build_score_distribution(scores)
      distribution = SCORE_RANGES.transform_values { 0 }
      scores.each do |score|
        range_key = SCORE_RANGES.find { |_, range| range.cover?(score.to_f.round) }&.first
        distribution[range_key] += 1 if range_key
      end
      distribution
    end

    def sanitize_ids(ids)
      ids.map(&:to_i).join(",")
    end

    def compute_weekly_trend(applies_scope)
      rows = applies_scope
        .where("applies.created_at >= ?", 12.weeks.ago)
        .group("DATE_TRUNC('week', applies.created_at)")
        .order(Arel.sql("DATE_TRUNC('week', applies.created_at)"))
        .count

      rows.map { |period, count| { period: period.to_date.to_s, count: count } }
    end

    def safe_average(values)
      return nil if values.blank?

      (values.sum.to_f / values.size).round(2)
    end

    def safe_percentage(numerator, denominator)
      return 0.0 if denominator.nil? || denominator.zero?

      ((numerator.to_f / denominator) * 100).round(2)
    end

    def average_hours(values)
      return nil if values.blank?

      (values.sum / values.size).round(2)
    end

    def percentile(values, pct)
      return nil if values.blank?

      sorted = values.sort
      k = ((pct / 100.0) * (sorted.size - 1)).round
      sorted[k]&.round(2)
    end

    def days_since(date)
      return nil unless date

      ((Time.current - date.to_time) / 1.day).to_i
    end

    def days_until(date)
      return nil unless date

      ((date.to_time - Time.current) / 1.day).to_i
    end

    def empty_funnel
      { stages: [], overall_conversion_rate: 0, bottleneck_stage: nil, avg_total_pipeline_days: nil }
    end

    def empty_velocity
      { avg_time_to_first_action_hours: nil, avg_time_to_screening_hours: nil,
        avg_time_to_interview_hours: nil, applies_per_day: 0, applies_trend: [] }
    end

    def empty_quality
      { avg_cv_match: nil, avg_total_score: nil, score_distribution: SCORE_RANGES.transform_values { 0 },
        evaluation_stats: { total_evaluated: 0, avg_score: nil, completed_count: 0, pending_count: 0,
                            screening_stats: { total: 0, avg_score: nil, pass_rate: 0 } },
        status_breakdown: {} }
    end

    def empty_engagement
      { total_dispatches: 0, dispatch_breakdown: {}, total_messages: 0,
        avg_messages_per_candidate: 0, candidates_with_feedback: 0, feedback_breakdown: {} }
    end

    def empty_scheduling
      { total_interviews_scheduled: 0, interviews_completed: 0, interviews_cancelled: 0,
        interviews_pending: 0, sub_status_breakdown: {}, no_show_count: 0 }
    end

    def empty_team_activity
      { actions_by_user: [], inactive_applies_7d: 0 }
    end
  end
end
