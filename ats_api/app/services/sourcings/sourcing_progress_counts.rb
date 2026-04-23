# frozen_string_literal: true

module Sourcings
  module SourcingProgressCounts
    module_function

    def call(sourcing)
      return { processed: 0, total: 0, percentage: 0 } unless sourcing

      total_expected = SourcedProfileSourcing
        .where(sourcing_id: sourcing.id)
        .where(is_deleted: false)
        .count

      analyzed_count = SourcedProfileSourcing
        .where(sourcing_id: sourcing.id)
        .where(is_deleted: false)
        .where.not(analysis: nil)
        .count

      percentage = total_expected > 0 ? (analyzed_count.to_f / total_expected * 100).round(1) : 0

      { processed: analyzed_count, total: total_expected, percentage: percentage }
    end
  end
end
