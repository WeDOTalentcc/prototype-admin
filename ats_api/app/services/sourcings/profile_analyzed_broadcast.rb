# frozen_string_literal: true

module Sourcings
  class ProfileAnalyzedBroadcast
    def self.call(sourcing:, sourced_profile_sourcing:, progress: nil)
      sps = sourced_profile_sourcing
      return unless sps.is_a?(SourcedProfileSourcing)

      sps.reload

      serialized_profile = SourcedProfileSourcingSerializer.new(
        sps,
        params: { current_user: sourcing.user }
      ).serializable_hash[:data][:attributes]

      progress ||= Sourcings::SourcingProgressCounts.call(sourcing)

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profile_analyzed",
          profile: serialized_profile,
          processed: progress[:processed],
          total: progress[:total],
          percentage: progress[:percentage]
        }
      )

      Rails.logger.info "✅ [ProfileAnalyzedBroadcast] sourcing=#{sourcing.id} sps=#{sps.id} profile=#{sps.sourced_profile_id}"
    rescue => e
      Rails.logger.error "❌ [ProfileAnalyzedBroadcast] #{e.message}"
    end
  end
end
