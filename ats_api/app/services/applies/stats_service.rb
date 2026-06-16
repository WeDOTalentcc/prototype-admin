# frozen_string_literal: true

module Applies
  class StatsService
    def initialize(start_date:, end_date:, job_id: nil, user_id: nil)
      @start_date = start_date
      @end_date = end_date
      @job_id = job_id
      @user_id = user_id
    end

    def call
      base = filtered_scope

      {
        by_status: count_by_status(base),
        by_source: count_by_source(base),
        by_period: count_by_period(base),
        conversion_rates: calculate_conversion_rates(base),
        totals: calculate_totals(base),
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s }
      }
    end

    private

    def filtered_scope
      scope = Apply.where(is_deleted: false)
      scope = scope.where(job_id: @job_id) if @job_id
      scope = scope.joins(:job).where(jobs: { user_id: @user_id }) if @user_id
      scope = scope.where(created_at: @start_date.beginning_of_day..@end_date.end_of_day)
      scope
    end

    def count_by_status(base)
      status_map = SelectiveProcess.statuses.invert

      base.joins(:selective_process)
          .group("selective_processes.status")
          .count
          .transform_keys { |k| status_map[k] || k.to_s }
    end

    def count_by_source(base)
      raw = base.joins(:candidate)
                .group("candidates.source")
                .count

      total = raw.values.sum.to_f

      raw.map { |source, count|
        {
          source: source || "unknown",
          count: count,
          percentage: total.positive? ? (count / total * 100).round(1) : 0.0
        }
      }.sort_by { |h| -h[:count] }
    end

    def count_by_period(base)
      base.group("DATE(applies.created_at)")
          .order(Arel.sql("DATE(applies.created_at)"))
          .count
          .map { |date, count| { date: date.to_s, count: count } }
    end

    def calculate_conversion_rates(base)
      counts = base.joins(:selective_process)
                   .group("selective_processes.status")
                   .count

      status_map = SelectiveProcess.statuses
      submission = counts[status_map["web_submission"]] || 0
      screening = counts[status_map["screening"]] || 0
      interview = counts[status_map["interview"]] || 0
      hired = counts[status_map["hired"]] || 0

      {
        submission_to_screening: safe_divide(screening, submission),
        screening_to_interview: safe_divide(interview, screening),
        interview_to_hired: safe_divide(hired, interview),
        overall: safe_divide(hired, submission)
      }
    end

    def calculate_totals(base)
      total = base.count

      rejected_count = base.joins(:selective_process)
                           .where(selective_processes: { status: :rejected })
                           .count

      hired_count = base.joins(:selective_process)
                        .where(selective_processes: { status: :hired })
                        .count

      active_count = total - rejected_count - hired_count

      avg_score = base.where.not(total_score: nil).average(:total_score)&.round(1) || 0.0

      {
        total: total,
        active: active_count,
        rejected: rejected_count,
        hired: hired_count,
        new_in_period: total,
        avg_score: avg_score
      }
    end

    def safe_divide(numerator, denominator)
      return 0.0 if denominator.zero?

      (numerator.to_f / denominator).round(3)
    end
  end
end
