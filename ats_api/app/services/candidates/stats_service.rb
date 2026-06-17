# frozen_string_literal: true

module Candidates
  class StatsService
    def initialize(start_date:, end_date:, source: nil)
      @start_date = start_date
      @end_date = end_date
      @source = source
    end

    def call
      {
        totals: calculate_totals,
        by_source: count_by_source,
        new_per_day: count_new_per_day,
        by_location: count_by_location,
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s }
      }
    end

    private

    def base_scope
      scope = Candidate.where(is_deleted: false)
      scope = scope.where(source: @source) if @source.present?
      scope
    end

    def period_scope
      base_scope.where(created_at: @start_date.beginning_of_day..@end_date.end_of_day)
    end

    def calculate_totals
      total = base_scope.count
      new_in_period = period_scope.count
      with_applies = base_scope.joins(:applies).where(applies: { is_deleted: false }).distinct.count

      {
        total: total,
        new_in_period: new_in_period,
        with_applies: with_applies,
        without_applies: total - with_applies
      }
    end

    def count_by_source
      raw = base_scope.group(:source).count
      total = raw.values.sum.to_f

      raw.map { |source, count|
        {
          source: source || "unknown",
          count: count,
          percentage: total.positive? ? (count / total * 100).round(1) : 0.0
        }
      }.sort_by { |h| -h[:count] }
    end

    def count_new_per_day
      period_scope
        .group("DATE(candidates.created_at)")
        .order(Arel.sql("DATE(candidates.created_at)"))
        .count
        .map { |date, count| { date: date.to_s, count: count } }
    end

    def count_by_location
      base_scope
        .where.not(city: [ nil, "" ])
        .group(:city, :state)
        .order(Arel.sql("COUNT(*) DESC"))
        .limit(20)
        .count
        .map { |(city, state), count| { city: city, state: state, count: count } }
    end
  end
end
