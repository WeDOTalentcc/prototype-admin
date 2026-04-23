# frozen_string_literal: true

module Sourcings
  class BulkStatsService
    def initialize(sourcing_ids:)
      @sourcing_ids = Array(sourcing_ids).compact.uniq.map(&:to_i)
    end

    def call
      return { success: false, error: "No sourcing IDs provided" } if @sourcing_ids.empty?

      sourcings = load_sourcings
      return { success: false, error: "No sourcings found" } if sourcings.empty?

      {
        success: true,
        data: build_stats(sourcings),
        meta: {
          requested_count: @sourcing_ids.size,
          found_count: sourcings.size,
          computed_at: Time.current.iso8601
        }
      }
    rescue StandardError => e
      Rails.logger.error "[Sourcings::BulkStatsService] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: e.message }
    end

    private

    attr_reader :sourcing_ids

    def load_sourcings
      Sourcing.where(id: @sourcing_ids, is_deleted: false)
    end

    def build_stats(sourcings)
      sourcings.each_with_object({}) do |sourcing, result|
        result[sourcing.id.to_s] = build_sourcing_stats(sourcing)
      rescue StandardError => e
        Rails.logger.error "[Sourcings::BulkStatsService] Failed for Sourcing##{sourcing.id}: #{e.message}"
        result[sourcing.id.to_s] = { error: e.message, sourcing_id: sourcing.id }
      end
    end

    def build_sourcing_stats(sourcing)
      profile_stats = sourcing.stats
      agg_stats = sourcing.aggregated_stats.presence || {}

      {
        sourcing_id: sourcing.id,
        uid: sourcing.uid,
        query: sourcing.query,
        provider: sourcing.provider,
        status: sourcing.status,
        searched_at: sourcing.searched_at&.iso8601,
        sourcing_stats: profile_stats,
        aggregated_stats: agg_stats,
        pool_info: build_pool_info(sourcing, profile_stats[:total]),
        import_stats: {
          total_imported: profile_stats[:imported]
        },
        score_distribution: agg_stats.dig("score_stats", "distribution") || {}
      }
    end

    def build_pool_info(sourcing, total_profiles)
      page_size = sourcing.parameters&.dig("page_size") || 30

      {
        total_profiles: total_profiles,
        total_pages: (total_profiles.to_f / page_size).ceil,
        current_page: sourcing.parameters&.dig("page") || 1,
        page_size: page_size
      }
    end
  end
end
