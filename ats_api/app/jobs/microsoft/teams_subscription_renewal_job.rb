# frozen_string_literal: true

module Microsoft
  class TeamsSubscriptionRenewalJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform
      Rails.logger.info "🔄 [TeamsSubscriptionRenewalJob] Renewing expiring Teams subscriptions..."
      MicrosoftService::TeamsSubscriptionService.renew_all_expiring
      Rails.logger.info "🔄 [TeamsSubscriptionRenewalJob] Retrying failed Teams subscriptions..."
      MicrosoftService::TeamsSubscriptionService.retry_all_failed
      Rails.logger.info "✅ [TeamsSubscriptionRenewalJob] Renewal complete"
    rescue StandardError => e
      Rails.logger.error "❌ [TeamsSubscriptionRenewalJob] Error: #{e.message}"
    end
  end
end
