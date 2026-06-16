# frozen_string_literal: true

module Microsoft
  class TeamsSubscriptionFullResetJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 1

    def perform
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🚀 [TeamsSubscriptionFullResetJob] Starting full subscription reset"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      stats = { recreated: 0, failed: 0, skipped: 0 }

      Account.pluck(:tenant).each do |tenant|
        Apartment::Tenant.switch(tenant) do
          next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)

          reset_tenant_subscriptions(tenant, stats)
        end
      end

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [TeamsSubscriptionFullResetJob] Reset complete"
      Rails.logger.info "   ✅ Recreated: #{stats[:recreated]}"
      Rails.logger.info "   ❌ Failed: #{stats[:failed]}"
      Rails.logger.info "   ⏭️  Skipped (no token): #{stats[:skipped]}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue StandardError => e
      Rails.logger.error "❌ [TeamsSubscriptionFullResetJob] Error: #{e.message}"
      raise
    end

    private

    def reset_tenant_subscriptions(tenant, stats)
      subscriptions = TeamsChatSubscription.all.to_a
      return if subscriptions.empty?

      Rails.logger.info "🔄 [TeamsSubscriptionFullResetJob] Tenant: #{tenant} (#{subscriptions.size} subscriptions)"

      subscriptions.each do |subscription|
        lia_user = User.find_by(id: subscription.lia_user_id)

        unless lia_user&.ms_access_token.present?
          stats[:skipped] += 1
          Rails.logger.warn "   ⏭️  #{subscription.chat_id.first(30)}: No valid token for lia_user_id=#{subscription.lia_user_id}"
          next
        end

        reset_single_subscription(subscription, lia_user, tenant, stats)
      end
    end

    def reset_single_subscription(subscription, lia_user, tenant, stats)
      delete_from_microsoft(subscription, lia_user) if subscription.subscription_id.present?

      subscription.update!(subscription_id: nil, status: "expired", subscription_expires_at: nil)

      MicrosoftService::TeamsSubscriptionService.new(lia_user, subscription.chat_id).call

      subscription.reload

      if subscription.subscription_active?
        stats[:recreated] += 1
        Rails.logger.info "   ✅ #{subscription.chat_id.first(30)}: Active (expires: #{subscription.subscription_expires_at})"
      else
        stats[:failed] += 1
        Rails.logger.warn "   ❌ #{subscription.chat_id.first(30)}: Failed (status: #{subscription.status})"
      end
    rescue StandardError => e
      stats[:failed] += 1
      Rails.logger.error "   ❌ #{tenant}/#{subscription.chat_id.first(30)}: #{e.message}"
    end

    def delete_from_microsoft(subscription, lia_user)
      MicrosoftService::Api.delete("/subscriptions/#{subscription.subscription_id}", lia_user)
    rescue StandardError => e
      Rails.logger.warn "   ⚠️  Failed to delete #{subscription.subscription_id} from MS: #{e.message}"
    end
  end
end
