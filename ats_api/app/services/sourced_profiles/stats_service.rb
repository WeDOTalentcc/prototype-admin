# frozen_string_literal: true

module SourcedProfiles
  class StatsService
    def initialize(start_date: nil, end_date: nil)
      @start_date = start_date&.to_date || 30.days.ago.to_date
      @end_date = end_date&.to_date || Date.current
    end

    def call
      {
        totals: totals,
        conversion_funnel: conversion_funnel,
        by_provider: by_provider,
        by_status: by_status,
        credits: credits_summary,
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s }
      }
    end

    private

    def base_scope
      SourcedProfile.active.where(created_at: @start_date.beginning_of_day..@end_date.end_of_day)
    end

    def totals
      scope = base_scope
      total = scope.count
      imported = scope.imported.count
      with_applies = imported_candidate_ids_with_applies
      hired = hired_count

      {
        total_sourced: total,
        imported_to_candidates: imported,
        with_applies: with_applies,
        hired: hired
      }
    end

    def conversion_funnel
      scope = base_scope
      total = scope.count
      imported = scope.imported.count
      applies = imported_candidate_ids_with_applies
      hired = hired_count

      {
        sourced_to_imported: safe_divide(imported, total),
        imported_to_applied: safe_divide(applies, imported),
        applied_to_hired: safe_divide(hired, applies)
      }
    end

    def by_provider
      SourcedProfileSourcing.where(is_deleted: false)
        .joins(:sourcing, :sourced_profile)
        .where(sourced_profiles: { is_deleted: false })
        .where(sourced_profiles: { created_at: @start_date.beginning_of_day..@end_date.end_of_day })
        .group("sourcings.provider")
        .select(
          "sourcings.provider",
          "COUNT(DISTINCT sourced_profile_sourcings.sourced_profile_id) as profile_count",
          "COUNT(DISTINCT CASE WHEN sourced_profiles.candidate_id IS NOT NULL THEN sourced_profiles.id END) as imported_count"
        )
        .map do |row|
          {
            provider: row.provider,
            count: row.profile_count,
            imported: row.imported_count
          }
        end
    end

    def by_status
      base_scope.group(:status).count
    end

    def credits_summary
      sourcings = Sourcing.where(is_deleted: false)
                          .where(created_at: @start_date.beginning_of_day..@end_date.end_of_day)

      total_used = sourcings.sum(:credits_used)
      hired = hired_count

      {
        total_consumed: total_used,
        avg_cost_per_hire: hired.zero? ? 0 : (total_used.to_f / hired).round(2)
      }
    end

    def imported_candidate_ids_with_applies
      candidate_ids = base_scope.imported.pluck(:candidate_id)
      return 0 if candidate_ids.empty?

      Apply.where(is_deleted: false, candidate_id: candidate_ids).distinct.count(:candidate_id)
    end

    def hired_count
      candidate_ids = base_scope.imported.pluck(:candidate_id)
      return 0 if candidate_ids.empty?

      Apply.joins(:selective_process)
           .where(is_deleted: false, candidate_id: candidate_ids)
           .where(selective_processes: { status: :hired })
           .distinct
           .count(:candidate_id)
    end

    def safe_divide(numerator, denominator)
      return 0.0 if denominator.zero?

      (numerator.to_f / denominator).round(3)
    end
  end
end
