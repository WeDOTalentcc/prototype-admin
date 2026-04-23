# frozen_string_literal: true

module EvaluationCandidates
  class StatsService
    def initialize(start_date: nil, end_date: nil)
      @start_date = start_date&.to_date || 30.days.ago.to_date
      @end_date = end_date&.to_date || Date.current
    end

    def call
      {
        totals: totals,
        completion_rate: completion_rate,
        avg_score: avg_score,
        avg_completion_time_hours: avg_completion_time_hours,
        score_distribution: score_distribution,
        by_classification: by_classification,
        screening_stats: screening_stats,
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s }
      }
    end

    private

    def base_scope
      EvaluationCandidate.where(is_deleted: false)
    end

    def period_scope
      base_scope.where(created_at: @start_date.beginning_of_day..@end_date.end_of_day)
    end

    def totals
      scope = period_scope
      total = scope.count
      completed = scope.where(completed: true).count
      pending = scope.where(completed: [ false, nil ]).where("date_expiration IS NULL OR date_expiration > ?", Time.current).count
      expired = scope.where(completed: [ false, nil ]).where("date_expiration <= ?", Time.current).count

      { total_sent: total, completed: completed, pending: pending, expired: expired }
    end

    def completion_rate
      scope = period_scope
      total = scope.count
      return 0.0 if total.zero?

      (scope.where(completed: true).count.to_f / total).round(3)
    end

    def avg_score
      period_scope.where(completed: true).where.not(score: nil).average(:score)&.round(2).to_f
    end

    def avg_completion_time_hours
      result = ActiveRecord::Base.connection.select_value(<<~SQL.squish)
        SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 3600.0)
        FROM evaluation_candidates
        WHERE completed = true
          AND is_deleted = false
          AND created_at BETWEEN '#{@start_date.beginning_of_day.iso8601}' AND '#{@end_date.end_of_day.iso8601}'
      SQL

      result&.to_f&.round(1)
    end

    def score_distribution
      ranges = { "0-1" => 0..1, "1-2" => 1..2, "2-3" => 2..3, "3-4" => 3..4, "4-5" => 4..5 }

      completed_scope = period_scope.where(completed: true).where.not(score: nil)

      ranges.transform_values do |range|
        completed_scope.where(score: range).count
      end
    end

    def by_classification
      period_scope
        .where(completed: true)
        .where.not(wsi_classification: nil)
        .group(:wsi_classification)
        .count
    end

    def screening_stats
      screening_scope = period_scope.where(is_screening: true)
      total = screening_scope.count
      passed = screening_scope.where(completed: true).where("score >= ?", 3.0).count

      {
        total_screening: total,
        pass_rate: total.zero? ? 0.0 : (passed.to_f / total).round(3),
        auto_advanced: passed
      }
    end
  end
end
