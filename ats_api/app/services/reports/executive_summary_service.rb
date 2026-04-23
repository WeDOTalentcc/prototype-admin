# frozen_string_literal: true

module Reports
  class ExecutiveSummaryService
    VALID_PERIODS = %w[week month quarter].freeze

    def initialize(user:, period: "month", compare_previous: false)
      @user = user
      @period = VALID_PERIODS.include?(period) ? period : "month"
      @compare_previous = compare_previous
    end

    def call
      current_range = compute_range(@period)
      previous_range = compute_previous_range(current_range)

      current_data = build_period_data(current_range)

      result = {
        success: true,
        data: {
          period: @period,
          current: current_data,
          date_range: { from: current_range.first.to_s, to: current_range.last.to_s }
        },
        meta: { computed_at: Time.current.iso8601 }
      }

      if @compare_previous
        previous_data = build_period_data(previous_range)
        result[:data][:previous] = previous_data
        result[:data][:previous_date_range] = { from: previous_range.first.to_s, to: previous_range.last.to_s }
        result[:data][:trends] = compute_trends(current_data, previous_data)
      end

      result
    rescue StandardError => e
      Rails.logger.error "[Reports::ExecutiveSummaryService] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: e.message }
    end

    private

    attr_reader :user, :compare_previous

    def build_period_data(range)
      {
        jobs: jobs_stats(range),
        candidates: candidates_stats(range),
        applies: applies_stats(range),
        meetings: meetings_stats(range),
        evaluations: evaluations_stats(range),
        llm_costs: llm_stats(range)
      }
    end

    def jobs_stats(range)
      active = Job.where(is_deleted: false, is_active: true)
      created = Job.where(is_deleted: false, created_at: range)
      closed = Job.where(is_deleted: false, is_active: false, is_archived: true, updated_at: range)

      {
        active_count: active.count,
        created_count: created.count,
        closed_count: closed.count,
        avg_applies_per_job: active.count.positive? ?
          (Apply.where(is_deleted: false, job_id: active.select(:id)).count.to_f / active.count).round(1) : 0
      }
    end

    def candidates_stats(range)
      new_candidates = Candidate.where(is_deleted: false, created_at: range)
      sources = new_candidates.group(:source).count

      {
        new_count: new_candidates.count,
        by_source: sources.transform_keys { |k| k.presence || "unknown" }
      }
    end

    def applies_stats(range)
      scope = Apply.where(is_deleted: false, created_at: range)
      status_counts = scope.joins(:selective_process)
                           .group("selective_processes.status")
                           .count

      status_map = SelectiveProcess.statuses.invert

      hired = status_counts[SelectiveProcess.statuses["hired"]] || 0
      rejected = status_counts[SelectiveProcess.statuses["rejected"]] || 0
      total = scope.count

      {
        total_count: total,
        by_status: status_counts.transform_keys { |k| status_map[k] || k.to_s },
        hired_count: hired,
        rejected_count: rejected,
        conversion_rate: total.positive? ? ((hired.to_f / total) * 100).round(2) : 0.0
      }
    end

    def meetings_stats(range)
      scope = CalendarEvent.where(is_deleted: false, is_cancelled: false, event_type: "interview", start_time: range)
      total = scope.count
      completed = scope.where(sub_status: "completed").count
      no_show_count = scope.where(sub_status: "no_show").count

      {
        total_scheduled: total,
        completed: completed,
        no_show: no_show_count,
        no_show_rate: total.positive? ? ((no_show_count.to_f / total) * 100).round(2) : 0.0
      }
    end

    def evaluations_stats(range)
      sent = EvaluationCandidate.where(created_at: range)
      completed = sent.where(completed: true)
      scored = completed.where("score > 0")

      {
        sent_count: sent.count,
        completed_count: completed.count,
        response_rate: sent.count.positive? ? ((completed.count.to_f / sent.count) * 100).round(2) : 0.0,
        avg_score: scored.average(:score)&.to_f&.round(2)
      }
    end

    def llm_stats(range)
      scope = LlmUsage.where(account_id: user.account_id, created_at: range)

      {
        total_requests: scope.count,
        total_cost_usd: scope.sum(:cost_usd).to_f.round(6),
        total_tokens: scope.sum(:total_tokens).to_i,
        success_rate: scope.count.positive? ? ((scope.successful.count.to_f / scope.count) * 100).round(2) : 0.0
      }
    end

    def compute_trends(current, previous)
      {
        jobs_created: trend_value(current.dig(:jobs, :created_count), previous.dig(:jobs, :created_count)),
        new_candidates: trend_value(current.dig(:candidates, :new_count), previous.dig(:candidates, :new_count)),
        total_applies: trend_value(current.dig(:applies, :total_count), previous.dig(:applies, :total_count)),
        conversion_rate: trend_value(current.dig(:applies, :conversion_rate), previous.dig(:applies, :conversion_rate)),
        meetings_scheduled: trend_value(current.dig(:meetings, :total_scheduled), previous.dig(:meetings, :total_scheduled)),
        evaluations_completed: trend_value(current.dig(:evaluations, :completed_count), previous.dig(:evaluations, :completed_count)),
        llm_cost: trend_value(current.dig(:llm_costs, :total_cost_usd), previous.dig(:llm_costs, :total_cost_usd))
      }
    end

    def trend_value(current_val, previous_val)
      current_val = current_val.to_f
      previous_val = previous_val.to_f

      return { change_pct: 0.0, direction: "stable" } if previous_val.zero? && current_val.zero?
      return { change_pct: 100.0, direction: "up" } if previous_val.zero?

      change = ((current_val - previous_val) / previous_val * 100).round(2)
      direction = change.positive? ? "up" : (change.negative? ? "down" : "stable")
      { change_pct: change.abs, direction: direction }
    end

    def compute_range(period)
      case period
      when "week"
        7.days.ago.to_date.beginning_of_day..Time.current
      when "month"
        30.days.ago.to_date.beginning_of_day..Time.current
      when "quarter"
        90.days.ago.to_date.beginning_of_day..Time.current
      end
    end

    def compute_previous_range(current_range)
      duration = current_range.last - current_range.first
      previous_end = current_range.first - 1.second
      previous_start = previous_end - duration
      previous_start..previous_end
    end
  end
end
