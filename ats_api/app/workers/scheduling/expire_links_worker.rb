# frozen_string_literal: true

module Scheduling
  class ExpireLinksWorker
    include Sidekiq::Worker

    sidekiq_options queue: :default, retry: 1

    def perform
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "⏳ [ExpireLinksWorker] Checking for expired scheduling links"

      expired_count = expire_by_date
      Rails.logger.info "✅ [ExpireLinksWorker] Expired #{expired_count} links"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue StandardError => e
      Rails.logger.error "❌ [ExpireLinksWorker] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    end

    private

    def expire_by_date
      links = SchedulingLink.active.where("expires_at IS NOT NULL AND expires_at < ?", Time.current)

      links.find_each do |link|
        link.mark_as_expired!
      end

      links.count
    end
  end
end
